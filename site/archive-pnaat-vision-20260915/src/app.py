#!/usr/bin/env python3
"""Site da garrafa: câmera do Pi -> veredito (OK / qual defeito).

Uma unica dona da camera (rpicam-vid em MJPEG). O navegador ve o quadro ao vivo e os botoes
capturam o fundo, a referencia OK e analisam a garrafa. Sem Flask, sem OpenCV, sem instalacao.

    python3 app.py [--porta 8090] [--largura 1296] [--altura 972]
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import json
import os
import subprocess
import threading
from pathlib import Path
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageDraw

import visao

DIR = visao.DIR
DADOS = visao.DADOS
HISTORICO = DADOS / "historico.jsonl"
_cam: visao.Camera | None = None
_trava = threading.Lock()
_ultimo: dict = {"veredito": None}
ESP_CAM_FRAME_URL = "http://127.0.0.1:8094/frame.jpg"
USB_CAMERA_DEVICE = "/dev/video8"


def _usb_device() -> str:
    """Acha a webcam pelo nome do driver; o número /dev/videoN muda entre boots."""
    for nome in sorted(Path('/sys/class/video4linux').glob('video*/name')):
        try:
            texto = nome.read_text().strip().lower()
        except OSError:
            continue
        if 'webcam' in texto or 'usb camera' in texto or 'generalplus' in texto:
            return '/dev/' + nome.parent.name
    return USB_CAMERA_DEVICE
SERIES_DIR = Path("/home/nerton/pnaat-dataset") / "series-3-cameras"
ROTACAO_USB = 90    # webcam montada girada: 90 graus anti-horario corrige
ROTACAO_ESP = 180   # sensor do ESP-CAM montado invertido
TRIGGER_DIR = DADOS / "triggers"
PREVIEW_DIR = Path("/dev/shm/pnaat-dataset-preview")

# Modelo neural local: o site continua dono da camera; este worker consulta a API
# em :8093 e publica a ultima imagem anotada sem disputar /dev/video.
MODELO_API = os.getenv("PNAAT_MODEL_API", "http://127.0.0.1:8093")
MODELOS_VISTA = {"lateral": "v0-lateral.pt", "topo": "v0-top.pt"}
MODELO_NOME = os.getenv("PNAAT_MODEL_NAME", MODELOS_VISTA["lateral"])
MODELO_VISTA = "topo" if MODELO_NOME == MODELOS_VISTA["topo"] else "lateral"
MODELO_CONF = float(os.getenv("PNAAT_MODEL_CONF", "0.25"))
_modelo_lock = threading.Lock()
_modelo = {"status": "inicializando", "vista": MODELO_VISTA, "modelo": MODELO_NOME, "deteccoes": [],
           "inference_ms": None, "atualizado_em": None, "jpeg": None, "veredito": None, "erro": None}
_modelo_thread: threading.Thread | None = None


def _anotar(jpeg: bytes, med: dict, res: dict) -> bytes:
    """Desenha o que o sistema viu: caixa da silhueta, faixa do topo e o veredito."""
    from io import BytesIO
    im = Image.open(BytesIO(jpeg)).convert("RGB")
    d = ImageDraw.Draw(im)
    cor = {"ok": (60, 122, 87), "defeito": (140, 59, 46)}.get(res.get("veredito"), (22, 58, 95))
    roi_px = visao.roi_px(im.size[::-1], visao.roi_atual())
    d.rectangle([roi_px[0], roi_px[1], roi_px[2], roi_px[3]], outline=(22, 58, 95), width=1)
    d.text((roi_px[0] + 4, roi_px[1] + 4), "ROI do rig", fill=(22, 58, 95))
    if med.get("ok"):
        x0, y0, x1, y1 = med["bbox"]
        d.rectangle([x0, y0, x1, y1], outline=cor, width=3)
        topo = y0 + max(3, int(0.15 * med["altura_px"]))
        d.line([(x0, topo), (x1, topo)], fill=cor, width=2)
        d.text((max(4, x0), max(4, y0 - 16)), f"tilt {med['tilt_tampa_graus']:.1f} graus", fill=cor)
    texto = f"{res.get('veredito', '?').upper()}  {res.get('classe', '')}".strip()
    d.rectangle([0, im.height - 26, im.width, im.height], fill=(255, 255, 255))
    d.text((8, im.height - 19), texto, fill=cor)
    saida = BytesIO()
    im.save(saida, format="JPEG", quality=85)
    return saida.getvalue()


def _jpeg_valido(data: bytes) -> bool:
    return data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")


def _modelo_com_box(jpeg: bytes, deteccoes: list[dict]) -> bytes:
    """Desenha as boxes retornadas pelo detector sobre o frame que ele recebeu."""
    from io import BytesIO
    im = Image.open(BytesIO(jpeg)).convert("RGB")
    d = ImageDraw.Draw(im)
    for det in deteccoes:
        box = det.get("bbox") or []
        if len(box) != 4:
            continue
        x1, y1, x2, y2 = (int(float(v)) for v in box)
        label = "%s %.2f" % (det.get("label", "?"), float(det.get("confidence", 0)))
        d.rectangle((x1, y1, x2, y2), outline=(220, 75, 35), width=4)
        d.rectangle((x1, max(0, y1 - 22), x1 + max(90, len(label) * 9), y1), fill=(220, 75, 35))
        d.text((x1 + 3, max(0, y1 - 19)), label, fill=(255, 255, 255))
    if not deteccoes:
        d.rectangle((0, 0, 250, 28), fill=(40, 40, 40))
        d.text((7, 7), "modelo: sem deteccao", fill=(255, 210, 80))
    out = BytesIO()
    im.save(out, format="JPEG", quality=88)
    return out.getvalue()


def _rodar_modelo(jpeg: bytes) -> None:
    """Uma inferencia no worker; falha vira estado visivel, nunca excecao silenciosa."""
    from urllib.request import Request, urlopen
    with _modelo_lock:
        nome_modelo = _modelo.get("modelo", MODELO_NOME)
    payload = json.dumps({"image_base64": base64.b64encode(jpeg).decode("ascii"),
                          "model_name": nome_modelo, "confidence": MODELO_CONF}).encode()
    req = Request(MODELO_API + "/predict", data=payload,
                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=8) as resp:
            dados = json.loads(resp.read().decode())
        deteccoes = dados.get("detections") or []
        anotada = _modelo_com_box(jpeg, deteccoes)
        with _modelo_lock:
            _modelo.update({"status": "ok" if deteccoes else "sem_deteccao",
                            "modelo": dados.get("model_used", nome_modelo),
                            "deteccoes": deteccoes, "inference_ms": dados.get("inference_ms"),
                            "atualizado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "jpeg": anotada, "erro": None})
    except Exception as exc:
        with _modelo_lock:
            _modelo.update({"status": "erro", "deteccoes": [], "inference_ms": None,
                            "atualizado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "erro": "%s: %s" % (type(exc).__name__, str(exc)[:180])})


def _modelo_veredito() -> dict:
    with _modelo_lock:
        deteccoes = list(_modelo.get("deteccoes") or [])
        nome = _modelo.get("modelo", MODELO_NOME)
    if not deteccoes:
        return {"veredito": "inconclusivo", "classe": "inconclusivo", "confianca": None,
                "motivos": [f"{nome}: nenhuma tampa detectada; nao assumir normal"]}
    melhor = max(deteccoes, key=lambda d: float(d.get("confidence", 0)))
    label = melhor.get("label", "")
    mapa = {"normal": ("ok", "normal"), "tampa_presente": ("ok", "normal"),
            "tampa_ausente": ("defeito", "tampa_ausente"),
            "tampa_alterada": ("defeito", "defeito_tampa"),
            "tampa_mal_rosqueada": ("defeito", "defeito_tampa")}
    ver, classe = mapa.get(label, ("inconclusivo", "inconclusivo"))
    return {"veredito": ver, "classe": classe, "confianca": melhor.get("confidence"),
            "motivos": [f"{nome}: {label} (confianca {float(melhor.get('confidence', 0)):.2f})"]}


def _modelo_analisar_agora(jpeg: bytes) -> dict:
    _rodar_modelo(jpeg)
    res = _modelo_veredito()
    with _modelo_lock:
        _modelo["veredito"] = res
        estado = {k: v for k, v in _modelo.items() if k != "jpeg"}
    return {"ok": True, "acao": "analise neural", "veredito": res, "modelo": estado}


def _modelo_loop() -> None:
    ultimo_ts = 0.0
    while True:
        try:
            jpeg, ts = _cam.ultimo() if _cam is not None else (None, 0.0)
            if jpeg and ts > ultimo_ts:
                ultimo_ts = ts
                _rodar_modelo(jpeg)
            time.sleep(1.5)
        except Exception as exc:
            with _modelo_lock:
                _modelo.update({"status": "erro", "erro": "%s: %s" % (type(exc).__name__, str(exc)[:180])})
            time.sleep(2.0)


def _capturar_usb(destino: Path) -> None:
    """Pega uma foto da webcam USB sem manter outro processo da camera."""
    temporario = destino.with_suffix(".tmp.jpg")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "v4l2",
           "-input_format", "mjpeg", "-video_size", "1280x720", "-i",
           _usb_device(), "-frames:v", "1", "-q:v", "2", "-y", str(temporario)]
    try:
        subprocess.run(cmd, check=True, timeout=12)
        data = temporario.read_bytes()
        if not _jpeg_valido(data):
            raise RuntimeError("webcam USB entregou JPEG invalido")
        _gravar_orientado(destino, data, ROTACAO_USB)
    finally:
        temporario.unlink(missing_ok=True)


def _gravar_atomico(destino: Path, data: bytes) -> None:
    """Grava bytes no armazenamento persistente sem deixar arquivo parcial."""
    temporario = destino.with_name(destino.name + ".tmp")
    with temporario.open("wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(temporario, destino)
    dirfd = os.open(str(destino.parent), os.O_DIRECTORY)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)


def _gravar_orientado(destino: Path, data: bytes, graus: int) -> None:
    """Grava o JPEG já na orientação final (a câmera é montada girada)."""
    if not graus:
        _gravar_atomico(destino, data)
        return
    with Image.open(BytesIO(data)) as im:
        girada = im.rotate(graus, expand=True)
        buf = BytesIO()
        girada.save(buf, format='JPEG', quality=95, subsampling=0)
    _gravar_atomico(destino, buf.getvalue())


def _capturar_esp_novo(destino: Path) -> None:
    """Solicita frame novo ao bridge antes de salvar a vista ESP-CAM."""
    from urllib.request import Request, urlopen
    with urlopen("http://127.0.0.1:8094/status", timeout=5) as resp:
        antes = json.loads(resp.read().decode())["frames_ok"]
    with urlopen(Request("http://127.0.0.1:8094/capture", method="POST"), timeout=5):
        pass
    limite = time.time() + 45
    while time.time() < limite:
        with urlopen("http://127.0.0.1:8094/status", timeout=5) as resp:
            atual = json.loads(resp.read().decode())
        if atual.get("frames_ok", 0) > antes:
            _capturar_esp(destino)
            return
        time.sleep(0.2)
    raise RuntimeError("ESP-CAM nao entregou frame novo para o dataset")


def _capturar_esp(destino: Path) -> None:
    """Busca o ultimo JPEG real da ESP-CAM pela ponte do Gaspar."""
    from urllib.request import Request, urlopen
    req = Request(ESP_CAM_FRAME_URL, headers={"Cache-Control": "no-cache"})
    with urlopen(req, timeout=10) as resp:
        data = resp.read()
    if not _jpeg_valido(data):
        raise RuntimeError("ESP-CAM entregou resposta que nao e JPEG")
    _gravar_orientado(destino, data, ROTACAO_ESP)


def registrar_foto_trigger(trigger_n: int, trigger_em: float) -> dict:
    """Salva somente a foto produzida pela ESP-CAM por este trigger."""
    if _cam is None:
        return {"ok": False, "erro": "camera CSI nao iniciada"}
    inicio = time.time()
    destino = TRIGGER_DIR / (time.strftime("%Y%m%d-%H%M%S") + "-%03d" % int(inicio * 1000 % 1000))
    destino.mkdir(parents=True, exist_ok=False)
    try:
        # A bridge so chama este endpoint depois de validar BEGIN/CHUNK/END;
        # /frame.jpg agora e' exatamente o frame deste trigger.
        from urllib.request import Request, urlopen
        with urlopen(Request("http://127.0.0.1:8094/frame.jpg"), timeout=8) as resp:
            jpeg = resp.read()
        if not _jpeg_valido(jpeg):
            raise RuntimeError("frame da ESP-CAM invalido")
        p = destino / "espcam-trigger.jpg"; _gravar_orientado(p, jpeg, ROTACAO_ESP)
        fim = time.time()
        manifest = {"trigger_n": trigger_n, "trigger_em": trigger_em,
                    "capturado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "foto": {"camera": "espcam", "nome": p.name, "bytes": len(jpeg)},
                    "delay_trigger_ate_foto_ms": round((fim-trigger_em)*1000)}
        (destino / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")
        resultado = {"ok": True, "acao": "foto do trigger salva", "trigger_n": trigger_n,
                     "serie": destino.name, "delay_trigger_ate_foto_ms": manifest["delay_trigger_ate_foto_ms"],
                     "foto": {"camera":"espcam", "nome":p.name, "bytes":len(jpeg),
                              "url":"/triggers/%s/%s" % (destino.name,p.name)}}
        with _trava: _ultimo["ultima_trigger"] = resultado
        return resultado
    except Exception as exc:
        return {"ok": False, "erro": str(exc), "trigger_n": trigger_n}


def _resultado_tripla(serie: str, diretorio: Path, fotos: list[dict], acao: str, persistida: bool) -> dict:
    return {"ok": True, "acao": acao, "serie": serie, "diretorio": str(diretorio),
            "persistida": persistida,
            "fotos": [{**f, "url": ("/series-3-cameras" if persistida else "/dataset-preview") + "/%s/%s" % (serie, f["nome"])} for f in fotos]}


def capturar_preview_dataset() -> dict:
    """Captura as tres fontes em RAM para validacao visual; ainda nao salva dataset."""
    if _cam is None:
        return {"ok": False, "erro": "camera CSI nao iniciada"}
    serie = time.strftime("%Y%m%d-%H%M%S") + ("-%03d" % int(time.time()*1000 % 1000))
    destino = PREVIEW_DIR / serie
    destino.mkdir(parents=True, exist_ok=False)
    fotos=[]
    try:
        csi, _ = _cam.ultimo()
        if not csi or not _jpeg_valido(csi): raise RuntimeError("camera CSI nao entregou JPEG")
        p=destino/"acerola-csi.jpg"; _gravar_atomico(p,csi); fotos.append({"camera":"acerola-csi","nome":p.name,"bytes":len(csi)})
        p=destino/"acerola-usb.jpg"; _capturar_usb(p); fotos.append({"camera":"acerola-usb","nome":p.name,"bytes":p.stat().st_size})
        p=destino/"espcam.jpg"; _capturar_esp_novo(p); fotos.append({"camera":"espcam","nome":p.name,"bytes":p.stat().st_size})
        _gravar_atomico(destino/"preview.json", json.dumps({"serie":serie,"fotos":fotos,"capturado_em":time.strftime("%Y-%m-%d %H:%M:%S")},indent=2).encode())
        r=_resultado_tripla(serie,destino,fotos,"preview das 3 cameras pronta — valide antes de salvar",False)
        with _trava: _ultimo["preview_dataset"]=r
        return r
    except Exception as exc:
        return {"ok":False,"erro":str(exc),"serie":serie,"fotos_parciais":fotos}


def salvar_preview_dataset() -> dict:
    """Promove a preview exibida, depois da validacao humana, ao dataset persistente."""
    with _trava: prev=dict(_ultimo.get("preview_dataset") or {})
    if not prev.get("ok") or not prev.get("serie"):
        return {"ok":False,"erro":"capture e valide uma preview primeiro"}
    origem=PREVIEW_DIR/prev["serie"]
    fotos=prev.get("fotos",[])
    if len(fotos)!=3 or not all((origem/f["nome"]).is_file() for f in fotos):
        return {"ok":False,"erro":"preview incompleta ou expirada; recapture"}
    destino=SERIES_DIR/prev["serie"]
    if destino.exists(): return {"ok":False,"erro":"serie ja existe"}
    destino.mkdir(parents=True)
    try:
        novas=[]
        for f in fotos:
            data=(origem/f["nome"]).read_bytes(); alvo=destino/f["nome"]; _gravar_atomico(alvo,data)
            novas.append({"camera":f["camera"],"nome":f["nome"],"bytes":len(data)})
        manifest={"serie":prev["serie"],"capturado_em":time.strftime("%Y-%m-%d %H:%M:%S"),"validado_e_salvo":True,"fontes":novas}
        _gravar_atomico(destino/"manifest.json",(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n").encode())
        r=_resultado_tripla(prev["serie"],destino,novas,"dataset validado e salvo",True)
        with _trava:
            _ultimo["ultima_tripla"] = r
            _ultimo.pop("preview_dataset", None)
        return r
    except Exception as exc:
        return {"ok":False,"erro":str(exc)}


def capturar_tres_cameras(trigger_n=None, trigger_em=None) -> dict:
    """Salva uma foto de cada fonte na mesma serie identificada."""
    if _cam is None:
        return {"ok": False, "erro": "camera CSI nao iniciada"}
    inicio = time.time()
    serie = time.strftime("%Y%m%d-%H%M%S") + ("-%03d" % int(inicio * 1000 % 1000))
    destino = SERIES_DIR / serie
    destino.mkdir(parents=True, exist_ok=False)
    fotos = []
    try:
        csi, _ = _cam.ultimo()
        if not csi or not _jpeg_valido(csi):
            raise RuntimeError("camera CSI nao entregou JPEG")
        p = destino / "acerola-csi.jpg"; _gravar_atomico(p, csi)
        fotos.append({"camera": "acerola-csi", "nome": p.name, "bytes": len(csi)})

        p = destino / "acerola-usb.jpg"; _capturar_usb(p)
        fotos.append({"camera": "acerola-usb", "nome": p.name, "bytes": p.stat().st_size})

        p = destino / "espcam.jpg"; _capturar_esp_novo(p)
        fotos.append({"camera": "espcam", "nome": p.name, "bytes": p.stat().st_size})

        fim = time.time()
        manifest = {"serie": serie, "capturado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "trigger_n": trigger_n, "trigger_em": trigger_em,
                    "captura_inicio_epoch": inicio, "captura_fim_epoch": fim,
                    "delay_trigger_ate_fim_ms": round((fim - trigger_em) * 1000) if trigger_em else None,
                    "fontes": fotos}
        _gravar_atomico(destino / "manifest.json",
                        (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode())
        resultado = {"ok": True, "acao": "3 cameras capturadas", "serie": serie,
                "diretorio": str(destino), "trigger_n": trigger_n,
                "delay_trigger_ate_fim_ms": manifest["delay_trigger_ate_fim_ms"], "fotos": [
                    {**f, "url": "/series-3-cameras/%s/%s" % (serie, f["nome"])} for f in fotos]}
        with _trava:
            _ultimo["ultima_tripla"] = resultado
        return resultado
    except Exception as exc:
        return {"ok": False, "erro": str(exc), "serie": serie, "fotos_parciais": fotos}


def capturar_tres_fotos(intervalo=0.5) -> dict:
    """Captura 3 frames distintos e preserva a serie em disco.

    O timestamp do frame precisa mudar entre fotos; assim o endpoint nao finge
    ter capturado tres imagens quando o produtor ainda nao entregou a proxima.
    """
    if _cam is None:
        return {"ok": False, "erro": "camera nao iniciada"}
    serie_id = time.strftime("%Y%m%d-%H%M%S") + ("-%03d" % int(time.time() * 1000 % 1000))
    destino = DADOS / "series" / serie_id
    destino.mkdir(parents=True, exist_ok=False)
    fotos = []
    ultimo_ts = 0.0
    try:
        for indice in range(1, 4):
            limite = time.time() + 6.0
            jpeg = None
            while time.time() < limite:
                candidato, ts = _cam.ultimo()
                if candidato and ts > ultimo_ts:
                    jpeg, ultimo_ts = candidato, ts
                    break
                time.sleep(0.03)
            if jpeg is None:
                raise RuntimeError("camera nao entregou um frame novo para a foto %02d" % indice)
            nome = "foto-%02d.jpg" % indice
            caminho = destino / nome
            caminho.write_bytes(jpeg)
            fotos.append({"nome": nome, "bytes": len(jpeg),
                          "url": "/series/%s/%s" % (serie_id, nome)})
            if indice < 3:
                time.sleep(intervalo)
        (destino / "manifest.json").write_text(json.dumps({
            "serie": serie_id, "fotos": fotos, "intervalo_s": intervalo,
            "capturado_em": time.strftime("%Y-%m-%d %H:%M:%S")
        }, indent=2, ensure_ascii=False) + "\n")
        return {"ok": True, "acao": "3 fotos capturadas", "serie": serie_id,
                "diretorio": str(destino), "fotos": fotos}
    except Exception as exc:
        return {"ok": False, "erro": str(exc), "serie": serie_id,
                "fotos_parciais": fotos}


def acao(alvo: str) -> dict:
    """Executa uma acao de captura/analise e devolve o resultado."""
    global _ultimo
    jpeg = _cam.esperar_frame() if _cam else None
    if not jpeg:
        return {"ok": False, "erro": "sem frame da camera",
                "detalhe": (_cam.erro if _cam else "camera nao iniciada")}

    with _trava:
        img = visao.imagem(jpeg)
        lim = visao.limiares()

        if alvo == "fundo":
            visao.salvar_frame(jpeg, "fundo.jpg")
            _salvar_fundo(img)          # unico gravador de fundo.npy (antes havia um write perdido)
            return {"ok": True, "acao": "fundo capturado",
                    "nota": "cena sem garrafa registrada como fundo"}

        fundo = _carregar_fundo()
        if fundo is None:
            return {"ok": False, "erro": "capture o fundo primeiro (cena sem garrafa)"}

        mascara_ref = visao.carregar_mascara()

        if alvo == "referencia":
            # sonda de cena = borda do quadro (a referencia ainda NAO existe: usar a mascara antiga
            # aqui acusaria "cena mudou" numa recaptura legitima)
            med = visao.medir(img, fundo, lim, None, None)
            motivo = med.get("motivo")
            if motivo == "cena_diferente_do_fundo":
                return {"ok": False, "erro": "a imagem nao bate com o fundo salvo",
                        "detalhe": "recapture o fundo com a camera na mesma posicao"}
            if not med.get("ok"):
                return {"ok": False, "erro": "sem silhueta de garrafa no quadro",
                        "detalhe": motivo}
            if med["frac_altura_quadro"] < lim["altura_min_frac"]:
                return {"ok": False, "erro": "garrafa pequena demais no quadro",
                        "detalhe": f"{med['frac_altura_quadro']*100:.0f}% da altura do quadro"}
            caixa, motivo_caixa = visao.descobrir_objeto(img, fundo, lim)
            tema = f"garrafa em x{caixa[0]*100:.0f}-{caixa[2]*100:.0f}% y{caixa[1]*100:.0f}-{caixa[3]*100:.0f}%" \
                if caixa else f"caixa nao localizada ({motivo_caixa})"
            if med.get("mascara") is not None:
                visao.salvar_mascara(med["mascara"])
            visao.salvar_frame(jpeg, "referencia.jpg")
            med = {**med, "schema_metricas": visao.SCHEMA_METRICAS}
            (DADOS / "referencia.json").write_text(json.dumps(_persistivel(med), indent=1))
            res = {"veredito": "referencia", "classe": "normal",
                   "motivos": [f"referencia gravada (nitidez {med['nitidez']:.0f}, "
                               f"brilho {med['brilho']:.0f}) - estes passam a ser os padroes de comparacao",
                               f"silhueta salva para comparacao ({tema})"]}
            _ultimo = {**(_sem_perfil(med) or {}), **res}
            return {"ok": True, "acao": "referencia capturada", "medidas": _sem_perfil(med),
                    "veredito": res}

        med = visao.medir(img, fundo, lim, None, mascara_ref)
        ref = _carregar_json("referencia.json")
        if ref is not None and ref.get("schema_metricas") != visao.SCHEMA_METRICAS:
            return {"ok": False, "erro": "referencia antiga (metricas mudaram)",
                    "detalhe": "capture a garrafa boa novamente para regravar a referencia"}
        res = visao.decidir(med, ref, lim, visao.metricas_frame(img), mascara_ref)
        visao.salvar_frame(jpeg, "ultima.jpg")
        (DADOS / "ultima_anotada.jpg").write_bytes(_anotar(jpeg, med, res))
        linha = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), **res,
                 "medidas": _sem_perfil(med)}
        with HISTORICO.open("a") as fh:
            fh.write(json.dumps(linha, ensure_ascii=False) + "\n")
        _ultimo = {**(_sem_perfil(med) or {}), **res}
        return {"ok": True, "acao": "analise", "veredito": res,
                "medidas": _sem_perfil(med), "referencia": _sem_perfil(ref) if ref else None}


def _sem_perfil(m: dict | None) -> dict | None:
    """Versao enxuta para RESPOSTA HTTP: sem perfil grande e sem a mascara binaria."""
    if not m:
        return None
    return {k: v for k, v in m.items() if k not in ("perfil", "mascara")}


def _persistivel(m: dict | None) -> dict | None:
    """Versao para ARQUIVO: mantem o perfil (a decisao de fallback usa), tira o ndarray.

    Sem isto a gravacao da referencia estourava `TypeError: Object of type ndarray is not JSON
    serializable` e a captura da referencia respondia 500 -- o fluxo morria no passo 2.
    """
    if not m:
        return None
    return {k: v for k, v in m.items() if k != "mascara"}


def _salvar_fundo(img):
    import numpy as np
    np.save(DADOS / "fundo.npy", img.astype("int16"))


def _carregar_fundo():
    import numpy as np
    arq = DADOS / "fundo.npy"
    if not arq.exists():
        return None
    try:
        a = np.load(arq)
        return a if a.ndim == 3 else None
    except Exception:
        return None


def _carregar_json(nome):
    arq = DADOS / nome
    if not arq.exists():
        return None
    try:
        return json.loads(arq.read_text())
    except Exception:
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = "pnaat-visao/1.0"

    def log_message(self, fmt, *args):
        pass

    def _html(self, corpo: bytes, tipo="text/html; charset=utf-8", cache=False):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        if not cache:
            self.send_header("Cache-Control", "no-store, max-age=0")
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, obj, codigo=200):
        corpo = json.dumps(obj, ensure_ascii=False, indent=1).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)

        if u.path in ("/", "/index.html"):
            return self._html((DIR / "index.html").read_bytes())

        if u.path == "/stream.mjpg":
            # Uma unica fonte: Camera._ler ja e' dona do rpicam-vid e guarda o
            # ultimo JPEG. Cada cliente recebe os frames novos sem disputar /dev/video.
            if _cam is None:
                return self._json({"erro": "camera nao iniciada"}, 503)
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            ultimo_ts = 0.0
            try:
                while True:
                    jpeg, ts = _cam.ultimo()
                    if not jpeg or ts <= ultimo_ts:
                        time.sleep(0.03)
                        continue
                    ultimo_ts = ts
                    parte = (b"--frame\r\n"
                             b"Content-Type: image/jpeg\r\n"
                             b"Content-Length: " + str(len(jpeg)).encode("ascii") +
                             b"\r\n\r\n" + jpeg + b"\r\n")
                    self.wfile.write(parte)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            return

        if u.path == "/capturar-preview-dataset":
            return self._json(capturar_preview_dataset())

        if u.path == "/salvar-preview-dataset":
            return self._json(salvar_preview_dataset())

        if u.path.startswith("/dataset-preview/"):
            partes=u.path.split("/")
            if len(partes)!=4 or partes[3] not in ("acerola-csi.jpg","acerola-usb.jpg","espcam.jpg"):
                return self._json({"erro":"preview invalida"},400)
            alvo=(PREVIEW_DIR/partes[2]/partes[3]).resolve(); raiz=PREVIEW_DIR.resolve()
            if raiz not in alvo.parents or not alvo.is_file(): return self._json({"erro":"preview ausente"},404)
            return self._html(alvo.read_bytes(),"image/jpeg")

        if u.path == "/dataset-series":
            itens = []
            if SERIES_DIR.is_dir():
                for destino in sorted((x for x in SERIES_DIR.iterdir() if x.is_dir()), reverse=True)[:30]:
                    try:
                        manifest = json.loads((destino / "manifest.json").read_text())
                        fontes = manifest.get("fontes", [])
                        if len(fontes) != 3 or not all((destino / f.get("nome", "")).is_file() for f in fontes):
                            continue
                        itens.append({"serie": destino.name, "capturado_em": manifest.get("capturado_em"),
                                      "trigger_n": manifest.get("trigger_n"),
                                      "fotos": [{**f, "url": "/series-3-cameras/%s/%s" % (destino.name, f["nome"])} for f in fontes]})
                    except (OSError, ValueError, TypeError, KeyError):
                        continue
            return self._json({"series": itens})

        if u.path.startswith("/series-3-cameras/"):
            partes = u.path.split("/")
            if len(partes) != 4 or any(not p or p in (".", "..") for p in partes[2:]):
                return self._json({"erro": "caminho invalido"}, 400)
            serie, nome = partes[2], partes[3]
            permitidos = ("acerola-csi.jpg", "acerola-usb.jpg", "espcam.jpg", "manifest.json")
            if not serie.replace("-", "").isdigit() or nome not in permitidos:
                return self._json({"erro": "arquivo invalido"}, 400)
            alvo = (SERIES_DIR / serie / nome).resolve()
            raiz = SERIES_DIR.resolve()
            if raiz not in alvo.parents or not alvo.is_file():
                return self._json({"erro": "arquivo ausente"}, 404)
            tipo = "application/json; charset=utf-8" if nome.endswith(".json") else "image/jpeg"
            return self._html(alvo.read_bytes(), tipo)

        if u.path == "/teste-trigger-3-cameras":
            # teste de bancada: mesma rota do sensor no bridge, sem salvar um
            # JPEG antigo. O callback do frame validado grava a serie depois.
            from urllib.request import Request, urlopen
            import urllib.error
            ref = int(time.time() * 1000) % 1000000000
            try:
                req = Request("http://127.0.0.1:8094/simular?n=%d" % ref, method="POST")
                with urlopen(req, timeout=5) as resp:
                    corpo = resp.read(256).decode("utf-8", "replace")
                return self._json({"ok": True, "acao": "trigger de teste enviado", "trigger_n": ref,
                                   "resposta": corpo.strip()})
            except (OSError, urllib.error.URLError) as exc:
                return self._json({"ok": False, "erro": "bridge do trigger indisponivel", "detalhe": str(exc)}, 503)

        if u.path == "/testar-delay":
            from urllib.request import Request, urlopen
            try:
                with urlopen(Request("http://127.0.0.1:8094/teste-delay", method="POST"), timeout=35) as resp:
                    resposta = resp.read(256).decode("utf-8", "replace")
                return self._json({"ok": True, "acao": "teste de delay concluido",
                                   "testado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                                   "resposta": resposta.strip()})
            except OSError as exc:
                return self._json({"ok": False, "erro": "bridge indisponivel", "detalhe": str(exc)}, 503)

        if u.path == "/configurar-delay":
            raw = (q.get("ms") or [""])[0]
            try:
                ms = int(raw)
                if not 0 <= ms <= 30000:
                    raise ValueError
            except ValueError:
                return self._json({"ok": False, "erro": "delay invalido (0..30000 ms)"}, 400)
            from urllib.request import Request, urlopen
            try:
                req = Request("http://127.0.0.1:8094/delay?ms=%d" % ms, method="POST")
                with urlopen(req, timeout=5) as resp:
                    resposta = resp.read(256).decode("utf-8", "replace")
                return self._json({"ok": True, "delay_ms": ms,
                                   "salvo_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                                   "resposta": resposta.strip()})
            except OSError as exc:
                return self._json({"ok": False, "erro": "bridge indisponivel", "detalhe": str(exc)}, 503)

        if u.path == "/configurar-delay":
            raw = (q.get("ms") or [""])[0]
            try:
                ms = int(raw)
                if not 0 <= ms <= 30000:
                    raise ValueError
            except ValueError:
                return self._json({"ok": False, "erro": "delay invalido (0..30000 ms)"}, 400)
            from urllib.request import Request, urlopen
            try:
                req = Request("http://127.0.0.1:8094/delay?ms=%d" % ms, method="POST")
                with urlopen(req, timeout=5) as resp:
                    resposta = resp.read(256).decode("utf-8", "replace")
                return self._json({"ok": True, "delay_ms": ms, "resposta": resposta.strip()})
            except OSError as exc:
                return self._json({"ok": False, "erro": "bridge indisponivel", "detalhe": str(exc)}, 503)

        if u.path == "/capturar-trigger":
            try:
                raw_n = (q.get("trigger_n") or [""])[0].strip()
                raw_em = (q.get("trigger_em") or [""])[0].strip()
                if not raw_n or not raw_em:
                    raise ValueError("trigger_n e trigger_em obrigatorios")
                trigger_n, trigger_em = int(raw_n), float(raw_em)
                if trigger_n < 1 or trigger_em <= 0:
                    raise ValueError("trigger fora da faixa")
            except (ValueError, AttributeError):
                return self._json({"ok": False, "erro": "trigger invalido"}, 400)
            return self._json(registrar_foto_trigger(trigger_n, trigger_em))

        if u.path == "/capturar-3-cameras":
            try:
                raw_n = (q.get("trigger_n") or [""])[0].strip()
                raw_em = (q.get("trigger_em") or [""])[0].strip()
                trigger_n = int(raw_n) if raw_n else None
                trigger_em = float(raw_em) if raw_em else None
                if trigger_n is not None and trigger_n < 1:
                    raise ValueError("trigger_n deve ser >= 1")
                if trigger_em is not None and trigger_em <= 0:
                    raise ValueError("trigger_em deve ser > 0")
            except (ValueError, AttributeError):
                return self._json({"ok": False, "erro": "trigger invalido"}, 400)
            # dataset manual: captura uma imagem de cada fonte; nao e' o fluxo do trigger.
            # capturar_tres_cameras publica _ultimo sob _trava; nao adquirir o
            # mesmo Lock aqui (Lock nao e reentrante: antes a resposta travava).
            return self._json(capturar_tres_cameras(trigger_n, trigger_em))

        if u.path.startswith("/series/"):
            partes = u.path.split("/")
            if len(partes) != 4 or any(not p or p in (".", "..") for p in partes[2:]):
                return self._json({"erro": "caminho invalido"}, 400)
            serie, nome = partes[2], partes[3]
            if not serie.replace("-", "").isdigit() or nome not in ("foto-01.jpg", "foto-02.jpg", "foto-03.jpg", "manifest.json"):
                return self._json({"erro": "arquivo invalido"}, 400)
            alvo = (DADOS / "series" / serie / nome).resolve()
            raiz = (DADOS / "series").resolve()
            if raiz not in alvo.parents or not alvo.is_file():
                return self._json({"erro": "arquivo ausente"}, 404)
            tipo = "application/json; charset=utf-8" if nome.endswith(".json") else "image/jpeg"
            return self._html(alvo.read_bytes(), tipo)

        if u.path == "/capturar-tres":
            return self._json(capturar_tres_fotos())

        if u.path == "/modelo/analisar":
            jpeg = _cam.esperar_frame() if _cam else None
            if not jpeg:
                return self._json({"ok": False, "erro": "sem frame da camera"}, 503)
            return self._json(_modelo_analisar_agora(jpeg))

        if u.path == "/modelo":
            vista = (q.get("vista", [""])[0] or "").strip().lower()
            if vista not in MODELOS_VISTA:
                return self._json({"ok": False, "erro": "vista invalida (lateral ou topo)"}, 400)
            with _modelo_lock:
                _modelo.update({"vista": vista, "modelo": MODELOS_VISTA[vista], "status": "aguardando",
                                "deteccoes": [], "veredito": None, "erro": None})
            return self._json({"ok": True, "vista": vista, "modelo": MODELOS_VISTA[vista]})

        if u.path == "/modelo.jpg":
            with _modelo_lock:
                jpeg_modelo = _modelo.get("jpeg")
            if not jpeg_modelo:
                return self._json({"erro": "modelo ainda sem frame"}, 503)
            return self._html(jpeg_modelo, "image/jpeg")

        if u.path == "/frame.jpg":
            jpeg, _ = _cam.ultimo()
            if not jpeg:
                return self._json({"erro": "sem frame"}, 503)
            return self._html(jpeg, "image/jpeg")

        if u.path in ("/ultima_anotada.jpg", "/fundo.jpg", "/referencia.jpg"):
            arq = DADOS / u.path.lstrip("/")
            if not arq.exists():
                return self._json({"erro": "arquivo ausente"}, 404)
            return self._html(arq.read_bytes(), "image/jpeg")

        if u.path == "/estado":
            ult = visao.limiares()
            n = sum(1 for _ in HISTORICO.open()) if HISTORICO.exists() else 0
            with _modelo_lock:
                modelo_estado = {k: v for k, v in _modelo.items() if k != "jpeg"}
            return self._json({
                "camera": "ok" if (_cam and _cam.ultimo()[0]) else "sem_frame",
                "erro_camera": _cam.erro if _cam else "nao iniciada",
                "tem_fundo": (DADOS / "fundo.npy").exists(),
                "tem_referencia": (DADOS / "referencia.json").exists(),
                "referencia": _sem_perfil(_carregar_json("referencia.json")),
                "referencia_ok": ((_carregar_json("referencia.json") or {})
                                  .get("schema_metricas") == visao.SCHEMA_METRICAS),
                "analises": n,
                "limiares": ult,
                "roi": list(visao.roi_atual()),
                "ultimo": _ultimo,
                "modelo": modelo_estado,
            })

        if u.path == "/capturar":
            alvo = (q.get("alvo", ["analise"])[0] or "analise").lower()
            if alvo not in ("fundo", "referencia", "analise"):
                return self._json({"ok": False, "erro": "alvo invalido"}, 400)
            return self._json(acao(alvo))

        if u.path == "/roi":
            try:
                nova = visao.salvar_roi(q.get("x0", [0.2])[0], q.get("y0", [0.04])[0],
                                        q.get("x1", [0.8])[0], q.get("y1", [0.96])[0])
            except (ValueError, TypeError) as exc:
                return self._json({"ok": False, "erro": str(exc)}, 400)
            return self._json({"ok": True, "roi": nova})

        if u.path == "/limiar":
            novos = {k: v[0] for k, v in q.items() if k != "t"}
            resultado = visao.salvar_limiares(novos)
            ignorados = resultado.pop("_ignorados", {})
            return self._json({"ok": not ignorados, "limiares": resultado, "ignorados": ignorados})

        if u.path == "/historico":
            linhas = []
            if HISTORICO.exists():
                for linha in HISTORICO.read_text().splitlines()[-25:]:
                    with contextlib.suppress(Exception):
                        linhas.append(json.loads(linha))
            return self._json({"itens": list(reversed(linhas))})

        if u.path == "/zerar":
            for nome in ("fundo.npy", "fundo.jpg", "referencia.json", "referencia.jpg",
                         "ultima.jpg", "ultima_anotada.jpg", "historico.jsonl"):
                (DADOS / nome).unlink(missing_ok=True)
            _ultimo.clear()
            _ultimo.update({"veredito": None})
            return self._json({"ok": True, "acao": "calibracao zerada"})

        return self._json({"erro": "rota desconhecida"}, 404)


def restaurar_ultima_serie() -> None:
    """Carrega a ultima serie valida do armazenamento persistente."""
    if not SERIES_DIR.is_dir():
        return
    for destino in sorted((x for x in SERIES_DIR.iterdir() if x.is_dir()), reverse=True):
        manifest = destino / "manifest.json"
        try:
            dados = json.loads(manifest.read_text())
            fontes = dados.get("fontes", [])
            if len(fontes) != 3 or not all((destino / f.get("nome", "")).is_file() for f in fontes):
                continue
            resultado = {"ok": True, "acao": "ultima serie persistida", "serie": destino.name,
                         "diretorio": str(destino), "persistida": True, "trigger_n": dados.get("trigger_n"),
                         "delay_trigger_ate_fim_ms": dados.get("delay_trigger_ate_fim_ms"),
                         "fotos": [{**f, "url": "/series-3-cameras/%s/%s" % (destino.name, f["nome"])}
                                   for f in fontes]}
            _ultimo["ultima_tripla"] = resultado
            return
        except (OSError, ValueError, TypeError, KeyError):
            continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--porta", type=int, default=8090)
    ap.add_argument("--largura", type=int, default=1296)
    ap.add_argument("--altura", type=int, default=972)
    ap.add_argument("--fps", type=int, default=12)
    a = ap.parse_args()

    global _cam
    _cam = visao.Camera(largura=a.largura, altura=a.altura, fps=a.fps)
    _cam.iniciar()
    restaurar_ultima_serie()
    global _modelo_thread
    _modelo_thread = threading.Thread(target=_modelo_loop, name="modelo-v0", daemon=True)
    _modelo_thread.start()
    print(f"camera: {a.largura}x{a.altura} @ {a.fps}fps (mjpeg)")
    print(f"modelo neural: {MODELO_NOME} via {MODELO_API}")
    print(f"site: http://0.0.0.0:{a.porta}/")
    srv = ThreadingHTTPServer(("0.0.0.0", a.porta), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _cam.parar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
