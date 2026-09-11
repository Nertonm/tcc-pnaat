"""Rascunho da PoC-03 (versao que roda): medir o corpo nas nossas frames reais e montar a banda normal.

Ideia da PoC: a forma do corpo e mensuravel contra uma referencia, e um desvio e detectavel.
Aqui: silhueta por Otsu no quadro inteiro, perfil de largura por linha, perfil de referencia = mediana
das 81 frames, e desvio medio de forma por frame. Depois, mede as duas perturbacoes de controle
(oclusao e risco) para ver se caem fora da banda. Nao e deformidade real: e controle.

Uso: python rascunho.py
Saida: ~/tcc-pnaat/resultados_poc03/{medidas.json, banda.json} + resumo no terminal
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path.home() / "tcc-pnaat"
ORIGEM = RAIZ / "datasets/pnaat/origem"
CONTROLE = RAIZ / "datasets/pnaat/controle"
OUT = RAIZ / "resultados_poc03"
ROI = (40, 20, 600, 460)   # corte grosso do quadro (x1, y1, x2, y2): tira as bordas
LIMIAR_MIN_AREA = 4000


def silhueta(caminho: Path):
    """Contorno do corpo + perfil de largura por linha (relativo ao topo do contorno)."""
    im = cv2.imread(str(caminho))
    if im is None:
        return None
    x1, y1, x2, y2 = ROI
    g = cv2.cvtColor(im[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (7, 7), 0)
    _, binaria = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contornos, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return None
    c = max(contornos, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < LIMIAR_MIN_AREA:
        return None
    bx, by, bw, bh = cv2.boundingRect(c)
    mascara = np.zeros_like(binaria)
    cv2.drawContours(mascara, [c], -1, 255, -1)
    larguras = [int((mascara[by + r, bx:bx + bw] > 0).sum()) for r in range(bh)]
    return {"arquivo": caminho.name, "area": float(area), "largura_bbox": int(bw), "altura_bbox": int(bh),
            "aspecto": float(bw / bh), "larguras": larguras,
            "largura_media": float(np.mean([l for l in larguras if l > 0])),
            "tenengrad": float(cv2.Laplacian(g, cv2.CV_64F).var())}


def perfil_referencia(medidas):
    """Perfil de largura mediano entre as frames normais, reamostrado em 100 pontos."""
    n = 100
    perfis = []
    for m in medidas:
        l = np.array(m["larguras"], dtype="float32")
        if len(l) < 10:
            continue
        x_old = np.linspace(0, 1, len(l))
        perfis.append(np.interp(np.linspace(0, 1, n), x_old, l))
    return np.median(np.stack(perfis), axis=0) if perfis else None


def desvio_forma(m, ref):
    l = np.array(m["larguras"], dtype="float32")
    x_old = np.linspace(0, 1, len(l))
    perfil = np.interp(np.linspace(0, 1, len(ref)), x_old, l)
    base = max(ref.mean(), 1.0)
    return float(np.mean(np.abs(perfil - ref)) / base)


def banda(valores):
    v = sorted(valores)
    if len(v) < 5:
        return {}
    return {"n": len(v), "media": float(np.mean(v)), "desvio": float(np.std(v, ddof=1)),
            "min": v[0], "p2_5": float(np.percentile(v, 2.5)), "p97_5": float(np.percentile(v, 97.5)),
            "max": v[-1]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = sorted(ORIGEM.glob("*.jpg"))
    print("frames normais: %d" % len(frames))
    medidas = [m for m in (silhueta(f) for f in frames) if m]
    print("silhuetas medidas: %d (perdas: %d)" % (len(medidas), len(frames) - len(medidas)))
    if len(medidas) < 5:
        print("poucas silhuetas: ajuste a ROI ou o limiar de area")
        return
    ref = perfil_referencia(medidas)
    for m in medidas:
        m["desvio_forma"] = desvio_forma(m, ref)
    b = {"desvio_forma": banda([m["desvio_forma"] for m in medidas]),
         "largura_media": banda([m["largura_media"] for m in medidas]),
         "aspecto": banda([m["aspecto"] for m in medidas]),
         "area": banda([m["area"] for m in medidas]),
         "tenengrad": banda([m["tenengrad"] for m in medidas])}
    print("\n=== banda normal (81 frames, uma vista) ===")
    for k, v in b.items():
        if v:
            print("  %-14s media=%.3f desvio=%.3f  p2.5=%.3f p97.5=%.3f  min=%.3f max=%.3f"
                  % (k, v["media"], v["desvio"], v["p2_5"], v["p97_5"], v["min"], v["max"]))

    print("\n=== perturbacoes de controle (nao sao deformidade real) ===")
    ctl = []
    for f in sorted(CONTROLE.glob("*.jpg")):
        m = silhueta(f)
        if not m:
            print("  %-42s silhueta nao medida" % f.name)
            continue
        m["desvio_forma"] = desvio_forma(m, ref)
        fora = not (b["desvio_forma"]["p2_5"] <= m["desvio_forma"] <= b["desvio_forma"]["p97_5"])
        print("  %-42s desvio_forma=%.4f  %s" % (f.name, m["desvio_forma"],
                                                 "FORA da banda" if fora else "dentro da banda"))
        ctl.append({k: m[k] for k in ("arquivo", "desvio_forma", "area", "aspecto", "tenengrad")})

    (OUT / "medidas.json").write_text(json.dumps(
        [{k: v for k, v in m.items() if k != "larguras"} for m in medidas], indent=1, ensure_ascii=False))
    (OUT / "banda.json").write_text(json.dumps({"banda": b, "controle": ctl}, indent=1, ensure_ascii=False))
    print("\nsalvo em %s" % OUT)


if __name__ == "__main__":
    main()
