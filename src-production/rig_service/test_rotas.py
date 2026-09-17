#!/usr/bin/env python3
"""Teste ponta a ponta das rotas HTTP do site, com camera FALSA e imagens controladas.

Sobe o servidor real (mesmo Handler) numa porta livre, aponta DADOS para um diretorio temporario
(nenhum risco para os dados de producao) e percorre o fluxo: fundo -> referencia -> analise, mais os
caminhos de erro. Sai != 0 se qualquer passo divergir.

    python3 test_rotas.py
"""
from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

import app as appmod
import visao

FALHAS: list[str] = []
OK = 0


def chk(nome: str, cond: bool, detalhe: str = ""):
    global OK
    if cond:
        OK += 1
    else:
        FALHAS.append(f"{nome} | {detalhe}")


def cena(com_garrafa: bool, h=480, w=640) -> bytes:
    """Cena sintetica REALISTA: fundo com textura/ruido (parede), borda de bancada e a garrafa.

    Fundo liso demais faz a nitidez ir a zero e o gate de foco disparar antes do motivo real
    (foi o que aconteceu na primeira versao deste teste) -- cena de teste tambem precisa ser crivel.
    """
    rng = np.random.default_rng(5)
    a = np.full((h, w, 3), 200, np.float32)
    a += rng.normal(0, 7.0, a.shape)                 # textura/ruido de sensor
    a[int(h * 0.75):, :] -= 35                       # bancada um pouco mais escura
    a[int(h * 0.75):int(h * 0.75) + 3, :] -= 40      # quina da bancada (estrutura)
    a = np.clip(a, 0, 255).astype(np.uint8)
    if com_garrafa:
        cx, topo, base = w // 2, int(h * 0.15), int(h * 0.92)
        a[topo:base, cx - 40:cx + 40] = 60                     # corpo
        a[topo:topo + 60, cx - 30:cx + 30] = 60                # ombro/gargalo
        a[topo - 40:topo, cx - 45:cx + 45] = 45                # tampa
    buf = BytesIO()
    Image.fromarray(a).save(buf, format="JPEG", quality=92)
    return buf.getvalue()


class CameraFalsa:
    """Substitui a camera real nos testes: devolve o JPEG que o teste mandar."""

    def __init__(self):
        self.frame = cena(False)
        self.erro = None

    def ultimo(self):
        return self.frame, 1.0

    def esperar_frame(self, timeout=6.0):
        del timeout                      # a camera falsa sempre tem frame pronto
        return self.frame

    def parar(self):
        pass


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def pega(base_url: str, rota: str):
    try:
        with urllib.request.urlopen(base_url + rota, timeout=15) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pnaat-rotas-"))
    # isola os dados: producao intocada
    visao.DADOS = tmp
    appmod.DADOS = tmp
    appmod.HISTORICO = tmp / "historico.jsonl"
    appmod._cam = CameraFalsa()

    port = porta_livre()
    srv = ThreadingHTTPServer(("127.0.0.1", port), appmod.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}"

    fundo_jpg, item_jpg = cena(False), cena(True)

    st, ct, corpo = pega(url, "/")
    chk("GET / devolve a pagina", st == 200 and b"Inspe" in corpo, f"{st} {ct}")

    st, _, corpo = pega(url, "/estado")
    e = json.loads(corpo)
    chk("GET /estado: camera ok e sem calibracao", st == 200 and e["camera"] == "ok"
        and e["tem_fundo"] is False and e["tem_referencia"] is False, str(e)[:120])
    chk("GET /estado expoe a ROI", isinstance(e.get("roi"), list) and len(e["roi"]) == 4)

    st, ct, corpo = pega(url, "/frame.jpg")
    chk("GET /frame.jpg devolve JPEG", st == 200 and ct == "image/jpeg" and corpo[:3] == b"\xff\xd8\xff")

    st, _, corpo = pega(url, "/capturar?alvo=analise")
    chk("analise antes do fundo e recusada com motivo", json.loads(corpo)["ok"] is False
        and "fundo" in json.loads(corpo).get("erro", ""), corpo[:120])

    appmod._cam.frame = fundo_jpg
    st, _, corpo = pega(url, "/capturar?alvo=fundo")
    chk("captura do fundo funciona", json.loads(corpo).get("ok") is True, corpo[:120])
    chk("fundo.npy e um NPY valido (nao JSON por cima)",
        (tmp / "fundo.npy").read_bytes()[:6] == b"\x93NUMPY", str((tmp / "fundo.npy").read_bytes()[:8]))

    appmod._cam.frame = item_jpg
    st, _, corpo = pega(url, "/capturar?alvo=referencia")
    r = json.loads(corpo)
    chk("captura da referencia funciona", r.get("ok") is True, corpo[:160])
    chk("mascara da referencia foi salva", (tmp / "referencia_mascara.png").exists())

    st, _, corpo = pega(url, "/estado")
    e2 = json.loads(corpo) if st == 200 else {}
    chk("GET /estado depois da referencia (nao pode estourar com ndarray)",
        st == 200 and e2.get("tem_referencia") is True, f"status={st}")

    st, _, corpo = pega(url, "/capturar?alvo=analise")
    v = json.loads(corpo)["veredito"]
    chk("MESMA imagem da referencia -> OK (sem falso defeito)", v["veredito"] == "ok", str(v))

    st, _, corpo = pega(url, "/estado")
    chk("GET /estado depois da analise devolve ultimo veredito",
        st == 200 and (json.loads(corpo).get("ultimo") or {}).get("veredito") == "ok",
        f"status={st}")

    appmod._cam.frame = fundo_jpg          # a garrafa sai de cena
    st, _, corpo = pega(url, "/capturar?alvo=analise")
    v = json.loads(corpo)["veredito"]
    chk("sem garrafa -> sem_garrafa (nunca defeito)", v["veredito"] == "sem_garrafa", str(v))

    st, _, corpo = pega(url, "/limiar?iou_ok=0.96")
    chk("limiar conhecido e aplicado", json.loads(corpo)["ok"] is True)
    st, _, corpo = pega(url, "/limiar?chave_errada=1")
    r = json.loads(corpo)
    chk("limiar desconhecido e reportado (nao finge sucesso)",
        r["ok"] is False and "chave_errada" in r["ignorados"], str(r)[:120])

    st, _, corpo = pega(url, "/roi?x0=0.5&y0=0.5&x1=0.51&y1=0.51")
    chk("ROI invalida e recusada", json.loads(corpo)["ok"] is False, corpo[:100])
    st, _, corpo = pega(url, "/roi?x0=0.1&y0=0.05&x1=0.9&y1=0.95")
    chk("ROI valida e aceita", json.loads(corpo)["ok"] is True, corpo[:100])

    # REGRESSAO do bug relatado: ROI apertada no objeto nao pode gerar "cena mudou" em cena parada
    appmod._cam.frame = item_jpg          # a garrafa volta para a frente da camera
    mask = visao.carregar_mascara()
    if mask is not None and mask.any():
        ys, xs = np.nonzero(mask)
        h, w = mask.shape
        pega(url, f"/roi?x0={xs.min() / w:.4f}&y0={ys.min() / h:.4f}"
                 f"&x1={(xs.max() + 1) / w:.4f}&y1={(ys.max() + 1) / h:.4f}")
        st, _, corpo = pega(url, "/capturar?alvo=analise")
        v = json.loads(corpo)["veredito"]
        chk("ROI colada no objeto NAO produz 'cena mudou' (cena parada)",
            v["veredito"] != "cena_mudou", str(v)[:160])
        chk("recusa por ROI apertada diz o que fazer (cita a janela/ROI)",
            v["veredito"] == "ok" or any("ROI" in m or "janela" in m for m in v.get("motivos", [])),
            str(v)[:160])
        st, _, corpo_r = pega(url, "/roi?x0=0&y0=0&x1=1&y1=1")
        _, _, corpo_e = pega(url, "/estado")
        roi_apos = (json.loads(corpo_e) or {}).get("roi")
        st, _, corpo = pega(url, "/capturar?alvo=analise")
        v2 = json.loads(corpo).get("veredito", {})
        chk("voltando a ROI do quadro inteiro segue OK", v2.get("veredito") == "ok",
            f"roi_reset={json.loads(corpo_r)} roi_agora={roi_apos} veredito={v2}")

    st, _, corpo = pega(url, "/historico")
    h = json.loads(corpo)
    chk("historico registra as analises", st == 200 and len(h["itens"]) >= 2, str(h)[:120])

    st, _, corpo = pega(url, "/zerar")
    chk("zerar limpa a calibracao", json.loads(corpo)["ok"] is True and not (tmp / "referencia.json").exists())

    st, _, _ = pega(url, "/rota_que_nao_existe")
    chk("rota desconhecida -> 404", st == 404, str(st))

    st, _, _ = pega(url, "/capturar?alvo=invalido")
    chk("alvo invalido -> 400", st == 400, str(st))

    srv.shutdown()
    print(f"teste das rotas: {OK} ok, {len(FALHAS)} falha(s)   (dados isolados em {tmp})")
    for f in FALHAS:
        print("  FALHA:", f)
    return 1 if FALHAS else 0


if __name__ == "__main__":
    sys.exit(main())
