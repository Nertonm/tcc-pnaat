#!/usr/bin/env python3
"""PoC-02 (demo integrada): mede a tampa, decide normal/ausente/mal rosqueada e registra evidencia.

Fecha a lacuna apontada na revisao: nenhum script executava a politica da PoC-02.

Metodo (conforme a decisao aprovada):
  1. GEOMETRIA primaria: no recorte da tampa mede a elipse do anel (tilt), a altura da cupula
     relativa ao recorte e a fracao escura dentro do anel (boca aberta).
  2. Limiares CALIBRADOS na banda das imagens normais de referencia (nao ha valor arbitrario).
  3. FALLBACK: se a geometria escalona (nao atinge limiar / sem contorno), o classificador leve
     (MobileNetV3 + regressao logistica, treinado no corpus publico) decide.
  4. FUSAO ASSIMETRICA (politica_tampa.aplicar_auxiliar): o auxiliar NUNCA cancela reprovacao da
     geometria; evidencia insuficiente vira INCONCLUSIVO, nunca aprovacao silenciosa.
  5. Evidencia: imagem anotada (contorno/elipse + medida que discriminou) + JSON por item.

Uso:
    python demo.py --referencia DIR --padrao 'frame_*.jpg' --salvar-ref ref.json [--roi x1,y1,x2,y2]
    python demo.py --ref ref.json --imagem FOTO --saida OUT
    python demo.py --ref ref.json --avaliar DIR --saida OUT
    python demo.py --ref ref.json --imagem FOTO --classificador corpus   # usa o auxiliar aprendido
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src" / "pocs"))

from poc02_classificacao.politica_tampa import (  # noqa: E402
    GeometriaTampa, Limiares, aplicar_auxiliar, decidir,
)
from poc02_classificacao.medir_tampa import medir_tampa  # noqa: E402

ROI_PADRAO = (0.30, 0.00, 0.70, 0.28)      # x1,y1,x2,y2 relativos: topo central (rig)
VERSAO = "poc02-demo-1"
CLASSES = ("normal", "tampa_ausente", "tampa_mal_rosqueada")
CORES = {"normal": (230, 140, 70), "tampa_ausente": (60, 60, 235),
         "tampa_mal_rosqueada": (60, 200, 240), "inconclusivo": (200, 200, 60)}


def wilson(k, n, z=1.959963984540054):
    import math
    if n <= 0:
        return 0.0
    p, z2 = k / n, z * z
    c = p + z2 / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, (c - m) / (1 + z2 / n))


# ------------------------------------------------------------------ localizacao por detector

_DET = {"modelo": None, "caminho": None}


def carregar_detector(caminho: Path):
    """Carrega o detector de tampa (YOLO treinado no corpus publico com caixa no nivel da tampa)."""
    if _DET["modelo"] is not None and _DET["caminho"] == str(caminho):
        return _DET["modelo"]
    from ultralytics import YOLO
    _DET["modelo"] = YOLO(str(caminho))
    _DET["caminho"] = str(caminho)
    return _DET["modelo"]


def localizar(caminho: Path, detector: Path, conf=0.25, margem=0.08):
    """Devolve a caixa da tampa detectada (independente do enquadramento) + estado + confianca."""
    try:
        modelo = carregar_detector(detector)
        r = modelo.predict(str(caminho), conf=conf, verbose=False)[0]
    except Exception as e:  # noqa: BLE001
        return {"erro": "%s: %s" % (type(e).__name__, str(e)[:100])}
    if r.boxes is None or len(r.boxes) == 0:
        return None
    i = int(r.boxes.conf.argmax())
    x1, y1, x2, y2 = [float(v) for v in r.boxes.xyxy[i].tolist()]
    cls = str(r.names[int(r.boxes.cls[i])])
    cf = float(r.boxes.conf[i])
    im = cv2.imread(str(caminho))
    h, w = im.shape[:2]
    mx, my = (x2 - x1) * margem, (y2 - y1) * margem
    caixa = [max(0, int(x1 - mx)), max(0, int(y1 - my)), min(w, int(x2 + mx)), min(h, int(y2 + my))]
    return {"caixa": caixa, "classe_detectada": cls, "confianca": cf}


def roi_de_caixa(caminho: Path, caixa):
    """Converte a caixa detectada em ROI relativa (x1,y1,x2,y2 em fracao) -- agnostico ao enquadramento."""
    im = cv2.imread(str(caminho))
    h, w = im.shape[:2]
    return (caixa[0] / w, caixa[1] / h, caixa[2] / w, caixa[3] / h)


# ------------------------------------------------------------------ ancora COCO (sem treino)

_COCO = {"modelo": None}
FRACAO_TOPO_OBJETO = 0.28


def carregar_coco():
    """YOLO pre-treinado em COCO: detecta 'bottle' em qualquer enquadramento (sem treino, sem anotacao)."""
    if _COCO["modelo"] is None:
        from ultralytics import YOLO
        _COCO["modelo"] = YOLO("yolov8n.pt")
    return _COCO["modelo"]


def localizar_objeto(caminho: Path, conf=0.15, imgsz=960, fracao_topo=FRACAO_TOPO_OBJETO):
    """Caixa da garrafa pelo COCO + ROI da tampa = faixa superior do objeto (relativa)."""
    try:
        modelo = carregar_coco()
        r = modelo.predict(str(caminho), conf=conf, imgsz=imgsz, verbose=False)[0]
    except Exception as e:  # noqa: BLE001
        return {"erro": "%s: %s" % (type(e).__name__, str(e)[:100])}
    if r.boxes is None or len(r.boxes) == 0:
        return None
    idx = [i for i in range(len(r.boxes)) if str(r.names[int(r.boxes.cls[i])]) == "bottle"]
    if not idx:
        return None
    i = max(idx, key=lambda j: float(r.boxes.conf[j]))
    x1, y1, x2, y2 = [int(v) for v in r.boxes.xyxy[i].tolist()]
    y_topo = int(y1 + (y2 - y1) * fracao_topo)
    im = cv2.imread(str(caminho))
    h, w = im.shape[:2]
    caixa_objeto = [max(0, x1), max(0, y1), min(w, x2), min(h, y2)]
    caixa = [max(0, x1), max(0, y1), min(w, x2), min(h, y_topo)]
    return {"caixa": caixa, "caixa_objeto": caixa_objeto, "classe_detectada": "bottle",
            "confianca": float(r.boxes.conf[i]), "fracao_topo": fracao_topo}


def achar_caixa(caminho: Path, detector=None, ancora=None):
    """Escolhe a ancora de localizacao: 'coco' (sem treino) | modelo treinado | None (ROI fixa)."""
    if ancora == "coco":
        return localizar_objeto(caminho)
    if detector is not None:
        return localizar(caminho, detector)
    return None


def medir_item(caminho: Path, roi=ROI_PADRAO) -> dict | None:
    """Mede o item na ROI informada: devolve as features geometricas + o geom para a politica."""
    im = cv2.imread(str(caminho))
    if im is None:
        return None
    h, w = im.shape[:2]
    x1, y1, x2, y2 = int(w * roi[0]), int(h * roi[1]), int(w * roi[2]), int(h * roi[3])
    tampa = im[y1:y2, x1:x2]
    if tampa.size == 0:
        return None
    corpo = im[y2:, :]
    m = medir_tampa(tampa, corpo if corpo.size else None)
    # fracao escura dentro do anel (boca aberta) e altura relativa ao recorte
    g = cv2.cvtColor(tampa, cv2.COLOR_BGR2GRAY)
    boca = 0.0
    if m["contorno_ok"]:
        bordas = cv2.Canny(cv2.GaussianBlur(g, (3, 3), 0), 60, 160)
        cnts, _ = cv2.findContours(bordas, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            mask = np.zeros_like(g)
            cv2.drawContours(mask, [c], -1, 255, -1)
            dentro = mask > 0
            if dentro.sum():
                boca = float(((g < 90) & dentro).sum()) / float(dentro.sum())
    altura_rel = float(m["altura_cupula_px"]) / max(1, tampa.shape[0]) if m["contorno_ok"] else 0.0
    return {"arquivo": caminho.name, "contorno_ok": m["contorno_ok"], "motivo_medicao": m.get("motivo"),
            "tilt": float(m["tilt_graus"]), "arco": float(m["arco_visivel_graus"]),
            "altura_px": float(m["altura_cupula_px"]), "altura_rel": altura_rel,
            "cnr": float(m["cnr"]), "especular": float(m["especular"]), "inliers": int(m["inliers"]),
            "boca_escura": boca, "roi": list(roi), "caixa_roi": [x1, y1, x2, y2]}


# ------------------------------------------------------------------ calibracao

def calibrar(diretorio: Path, padrao: str, roi, saida: Path, detector=None, ancora=None) -> dict:
    feats, det = [], []
    for f in sorted(diretorio.glob(padrao)):
        roi_f = roi
        loc = achar_caixa(f, detector, ancora)
        if loc is None and (detector is not None or ancora is not None):
            det.append(f.name)
            continue
        if loc and "caixa" in loc:
            roi_f = roi_de_caixa(f, loc["caixa"])
            det.append(loc["classe_detectada"])
        m = medir_item(f, roi_f)
        if m and m["contorno_ok"]:
            m["roi_relativa"] = list(roi_f)
            if loc:
                m["detectado"] = loc.get("classe_detectada")
            feats.append(m)
    if len(feats) < 5:
        raise SystemExit("referencia insuficiente: %d itens validos" % len(feats))
    def banda(campo):
        v = [x[campo] for x in feats]
        return {"p2_5": float(np.percentile(v, 2.5)), "p50": float(np.median(v)),
                "p97_5": float(np.percentile(v, 97.5)), "min": float(min(v)), "max": float(max(v))}
    dados = {"versao": VERSAO, "origem": str(diretorio), "padrao": padrao, "roi": list(roi),
             "origem_detector": str(detector) if detector else None,
             "origem_ancora": "coco" if ancora else ("detector" if detector else "fixa"),
             "n": len(feats), "falhas": len(list(diretorio.glob(padrao))) - len(feats),
             "altura_rel": banda("altura_rel"), "tilt": banda("tilt"), "boca_escura": banda("boca_escura"),
             "cnr": banda("cnr"), "arco": banda("arco")}
    # limiares: ausente = altura abaixo do p2.5 das normais OU boca escura acima do p97.5
    dados["t_ausente_altura"] = dados["altura_rel"]["p2_5"]
    dados["t_boca"] = dados["boca_escura"]["p97_5"]
    dados["t_tilt"] = dados["tilt"]["p97_5"]
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=1))
    print("referencia: %d itens | altura_rel p2.5=%.3f p50=%.3f | boca p97.5=%.3f | tilt p97.5=%.1f"
          % (len(feats), dados["t_ausente_altura"], dados["altura_rel"]["p50"], dados["t_boca"], dados["t_tilt"]))
    print("salva em %s" % saida)
    return dados


# ------------------------------------------------------------------ auxiliar aprendido

_AUX = {"modelo": None, "clf": None}


def carregar_auxiliar(corpus: Path, cache: Path):
    if _AUX["clf"] is not None:
        return _AUX
    import joblib
    if cache.exists():
        _AUX.update(joblib.load(cache))
        return _AUX
    import torch
    from sklearn.linear_model import LogisticRegression
    from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small
    pesos = MobileNet_V3_Small_Weights.DEFAULT
    modelo = mobilenet_v3_small(weights=pesos)
    modelo.classifier = torch.nn.Identity()
    modelo.eval()
    prep = pesos.transforms()
    X, y = [], []
    for d in sorted(p for p in corpus.iterdir() if p.is_dir()):
        for f in sorted(d.glob("*.jpg")):
            im = cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2RGB)
            with torch.no_grad():
                X.append(modelo(prep(torch.from_numpy(im).permute(2, 0, 1)).unsqueeze(0)).numpy()[0])
            y.append(d.name)
    clf = LogisticRegression(max_iter=1000).fit(np.stack(X), y)
    joblib.dump({"modelo": modelo, "clf": clf, "prep": prep}, cache)
    _AUX.update({"modelo": modelo, "clf": clf, "prep": prep})
    return _AUX


def inferir_auxiliar(im_bgr, corpus: Path, cache: Path) -> dict | None:
    try:
        a = carregar_auxiliar(corpus, cache)
    except Exception as e:  # noqa: BLE001
        return {"erro": "%s: %s" % (type(e).__name__, str(e)[:80])}
    import torch
    rgb = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2RGB)
    with torch.no_grad():
        f = a["modelo"](a["prep"](torch.from_numpy(rgb).permute(2, 0, 1)).unsqueeze(0)).numpy()[0]
    proba = a["clf"].predict_proba([f])[0]
    idx = int(np.argmax(proba))
    return {"classe": str(a["clf"].classes_[idx]), "confianca": float(proba[idx])}


# ------------------------------------------------------------------ decisao

def decidir_item(m: dict, ref: dict, aux: dict | None) -> dict:
    geo = GeometriaTampa(contorno_ok=bool(m["contorno_ok"]), arco_visivel_graus=m["arco"],
                         tilt_graus=m["tilt"], altura_cupula_px=m["altura_px"],
                         cnr=m["cnr"], especular=m["especular"], inliers=m["inliers"])
    base = decidir(geo, Limiares())
    # regra calibrada da demo (substitui os limiares provisorios quando a referencia existe)
    if m["contorno_ok"]:
        if m["altura_rel"] < ref["t_ausente_altura"] or m["boca_escura"] > ref["t_boca"]:
            base_classe, base_motivo, escalar = "tampa_ausente", "ausente_calibrado", False
        elif m["tilt"] > ref["t_tilt"]:
            base_classe, base_motivo, escalar = "tampa_mal_rosqueada", "tilt_acima_banda", False
        else:
            base_classe, base_motivo, escalar = "normal", "dentro_da_banda", False
        from poc02_classificacao.politica_tampa import Decisao
        base = Decisao(base_classe, escalar=escalar, motivos=(base_motivo,), origem="geometria")
    final = aplicar_auxiliar(base, aux) if aux else base
    return {"classe": final.classe, "origem": final.origem, "escalou": bool(base.escalar),
            "motivos": list(final.motivos), "geom_base": base.classe, "auxiliar": aux}


def anotar(caminho: Path, m: dict, ref: dict, d: dict, destino: Path) -> Path:
    im = cv2.imread(str(caminho))
    cor = CORES.get(d["classe"], (200, 200, 200))
    x1, y1, x2, y2 = m["caixa_roi"]
    cv2.rectangle(im, (x1, y1), (x2, y2), cor, 2)
    if m["contorno_ok"]:
        g = cv2.cvtColor(im[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        bordas = cv2.Canny(cv2.GaussianBlur(g, (3, 3), 0), 60, 160)
        cnts, _ = cv2.findContours(bordas, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        if cnts:
            c = max(cnts, key=cv2.contourArea).copy()
            c[:, 0, 0] += x1
            c[:, 0, 1] += y1
            cv2.drawContours(im, [c], -1, cor, 1)
    faixa = np.full((40, im.shape[1], 3), 24, np.uint8)
    txt = "%s | %s | altura_rel=%.3f boca=%.2f tilt=%.1f" % (
        d["classe"].upper(), d["origem"], m["altura_rel"], m["boca_escura"], m["tilt"])
    cv2.putText(faixa, txt, (8, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 1)
    cv2.putText(faixa, "motivos: %s | limiares: altura<%.3f boca>%.3f tilt>%.1f" % (
        ",".join(d["motivos"])[:60], ref["t_ausente_altura"], ref["t_boca"], ref["t_tilt"]),
        (8, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
    destino.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino), np.vstack([faixa, im]))
    return destino


def avaliar_item(caminho: Path, ref: dict, corpus: Path | None, cache: Path, saida: Path | None,
                 detector: Path | None = None, ancora: str | None = None) -> dict:
    roi_rel = tuple(ref["roi"])
    loc = achar_caixa(caminho, detector, ancora)
    if (detector is not None or ancora is not None) and (not loc or "caixa" not in loc):
        return {"arquivo": caminho.name, "classe": "inconclusivo", "motivo": "nao_localizado",
                "origem": "ancora", "motivos": ["nao_localizado"], "medidas": {}}
    if loc and "caixa" in loc:
        roi_rel = roi_de_caixa(caminho, loc["caixa"])
    m = medir_item(caminho, roi_rel)
    if m is None:
        return {"arquivo": caminho.name, "classe": "inconclusivo", "motivo": "imagem_ilegivel"}
    aux = None
    if corpus is not None:
        im = cv2.imread(str(caminho))
        if loc is not None and "caixa" in loc:
            x1, y1, x2, y2 = loc["caixa"]
            roi_img = im[y1:y2, x1:x2]
        else:
            h = im.shape[0]
            roi_img = im[: int(h * 0.35), :]
        aux = inferir_auxiliar(cv2.resize(roi_img, (224, 224)), corpus, cache)
    d = decidir_item(m, ref, aux)
    r = {"arquivo": caminho.name, **d, "medidas": {k: m[k] for k in
         ("altura_rel", "boca_escura", "tilt", "arco", "cnr", "contorno_ok")}}
    if loc is not None:
        r["detector"] = {"caixa": loc.get("caixa"), "classe": loc.get("classe_detectada"),
                         "confianca": loc.get("confianca"), "erro": loc.get("erro")}
        r["roi_relativa"] = list(roi_rel)
    if saida is not None:
        r["anotada"] = str(anotar(caminho, m, ref, d, saida / ("%s_anotada.png" % caminho.stem)))
        (saida / ("%s_resultado.json" % caminho.stem)).write_text(json.dumps(r, ensure_ascii=False, indent=1))
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--referencia", type=Path)
    ap.add_argument("--padrao", default="frame_*.jpg")
    ap.add_argument("--roi", default=",".join(str(v) for v in ROI_PADRAO))
    ap.add_argument("--salvar-ref", type=Path, default=Path("poc02_ref.json"))
    ap.add_argument("--ref", type=Path)
    ap.add_argument("--imagem", type=Path)
    ap.add_argument("--avaliar", type=Path, help="diretorio com imagens (padrao *.jpg)")
    ap.add_argument("--padrao-avaliar", default="*.jpg")
    ap.add_argument("--classificador", type=Path, help="diretorio do corpus publico de recortes (auxiliar)")
    ap.add_argument("--detector", type=Path, help="modelo YOLO da tampa: ROI detectada (agnostico ao enquadramento)")
    ap.add_argument("--ancora", choices=["coco"], help="ancora sem treino: 'coco' acha a garrafa e usa a faixa superior como ROI")
    ap.add_argument("--cache", type=Path, default=Path("/tmp/poc02_aux.joblib"))
    ap.add_argument("--saida", type=Path, default=Path("poc02_saida"))
    a = ap.parse_args()
    roi = tuple(float(v) for v in a.roi.split(","))

    if a.referencia:
        calibrar(a.referencia, a.padrao, roi, a.salvar_ref, detector=a.detector, ancora=a.ancora)
        return 0
    caminho_ref = a.ref or a.salvar_ref
    if not caminho_ref.exists():
        raise SystemExit("referencia ausente (%s): rode --referencia DIR" % caminho_ref)
    ref = json.loads(caminho_ref.read_text())
    roi = tuple(ref["roi"])
    modo_atual = "coco" if a.ancora else ("detector" if a.detector else "fixa")
    if ref.get("origem_ancora") != modo_atual:
        print("aviso: referencia calibrada em modo '%s' e a execucao usa '%s' -- medidas nao comparaveis."
              % (ref.get("origem_ancora"), modo_atual))

    if a.imagem:
        r = avaliar_item(a.imagem, ref, a.classificador, a.cache, a.saida, detector=a.detector, ancora=a.ancora)
        print(" %s -> %s (origem=%s, motivos=%s)" % (r["arquivo"], r["classe"].upper(),
                                                     r.get("origem"), ",".join(r.get("motivos", []))))
        if "anotada" in r:
            print(" anotada: %s" % r["anotada"])
        return 0

    if a.avaliar:
        fotos = sorted(a.avaliar.glob(a.padrao_avaliar))
        if not fotos:
            raise SystemExit("nenhuma imagem em %s" % a.avaliar)
        saida = a.saida / a.avaliar.name
        linhas = [avaliar_item(f, ref, a.classificador, a.cache, saida, detector=a.detector) for f in fotos]
        print("%-38s %-18s %-10s %8s" % ("arquivo", "classe", "geom_base", "altura_rel"))
        for r in linhas:
            alt = r["medidas"].get("altura_rel") if r.get("medidas") else None
            print("%-38s %-18s %-10s %8s" % (r["arquivo"], r["classe"], r.get("geom_base", "-"),
                                             ("%.3f" % alt) if alt is not None else "-"))
        cont = {}
        for r in linhas:
            cont[r["classe"]] = cont.get(r["classe"], 0) + 1
        print("\nresumo: %s (n=%d)" % (cont, len(linhas)))
        resumo = a.saida / ("resumo_%s.json" % a.avaliar.name)
        resumo.parent.mkdir(parents=True, exist_ok=True)
        resumo.write_text(json.dumps({"ref": str(caminho_ref), "resultados": linhas, "contagem": cont},
                                     ensure_ascii=False, indent=1))
        print("resumo: %s" % resumo)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
