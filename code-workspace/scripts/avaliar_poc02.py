"""Avaliacao da PoC-02 (classificacao de tampa): metrica por classe, IC e imagem anotada.

Decisoes vigentes (docs/DECISIONS.md, D-23..D-28):
  D-23  a decisao da tampa roda nas DUAS vistas laterais; a vista de topo e um check dimensional
        independente que so pode ESCALONAR (nunca aprovar sozinha).
  D-25  recall por classe com IC (Wilson, e Clopper-Pearson quando scipy existe) + FP separado de FN,
        e IMAGEM ANOTADA por item mostrando o que discriminou.
  D-26  amostras de fronteira entram no conjunto; `inconclusivo` e classe propria na matriz.
  D-27  composicao de referencias e datasets com procedencia por numero: metricas NUNCA agregadas
        entre fontes (cada `fonte` tem seu proprio bloco).

Uso:
  python scripts/avaliar_poc02.py --manifest manifest.csv --predicoes predicoes.json [--anotar DIR]
  manifest.csv: item_id,fonte,classe_verdade,arquivo[,vista]
  predicoes.json: {"it-0001": {"classe": "...", "confianca": 0.91, "medidas": {...}, "motivos": [...]}}
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

CLASSES = ("normal", "tampa_ausente", "tampa_mal_rosqueada", "inconclusivo")
Z95 = 1.959963984540054

# Metas do nucleo (docs/requisitos.md: RNF-02 acuracia por classe; RNF-03 FP)
ALVOS = {"tampa_ausente": 0.95, "tampa_mal_rosqueada": 0.90, "normal": None}
LIMITES_FP = {"tampa_ausente": 0.02}
LIMITE_FP_PADRAO = 0.05

CORES = {"normal": (60, 160, 60), "tampa_ausente": (30, 30, 220),
         "tampa_mal_rosqueada": (0, 140, 255), "inconclusivo": (140, 140, 140)}


def wilson(k: int, n: int, limite: str = "lb", z: float = Z95) -> float:
    """Intervalo de Wilson. limite='lb' (inferior) ou 'ub' (superior). n=0 -> 0.0."""
    if n <= 0:
        return 0.0
    p = k / n
    z2 = z * z
    centro = p + z2 / (2 * n)
    meia = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    if limite == "lb":
        return max(0.0, (centro - meia) / (1 + z2 / n))
    return min(1.0, (centro + meia) / (1 + z2 / n))


def clopper_pearson(k: int, n: int, limite: str = "lb", alpha: float = 0.05) -> float | None:
    """Clopper-Pearson exato, se scipy estiver disponivel; senao None."""
    try:
        from scipy.stats import beta
    except Exception:
        return None
    if n <= 0:
        return 0.0
    if limite == "lb":
        return 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    return 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))


def carregar(manifest: Path, predicoes: Path):
    itens = {}
    with manifest.open(newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            itens[linha["item_id"]] = {
                "fonte": linha.get("fonte") or "proprio",
                "verdade": linha["classe_verdade"],
                "arquivo": linha.get("arquivo") or "",
            }
    pred = json.loads(predicoes.read_text(encoding="utf-8"))
    for k, v in pred.items():
        if k in itens:
            itens[k]["pred"] = v.get("classe", "inconclusivo")
            itens[k]["confianca"] = v.get("confianca")
            itens[k]["medidas"] = v.get("medidas") or {}
            itens[k]["motivos"] = v.get("motivos") or []
    return itens


def bloco(itens: dict, fonte: str) -> dict:
    """Metricas de UMA fonte. Nunca agrega fontes diferentes (D-27)."""
    sel = {k: v for k, v in itens.items() if v["fonte"] == fonte and "pred" in v}
    matriz = Counter()
    for v in sel.values():
        matriz[(v["verdade"], v["pred"])] += 1
    por_classe = {}
    for c in CLASSES:
        if c == "inconclusivo":
            continue
        total = sum(1 for v in sel.values() if v["verdade"] == c)
        acertos = sum(1 for v in sel.values() if v["verdade"] == c and v["pred"] == c)
        negativos = sum(1 for v in sel.values() if v["verdade"] != c)
        fp = sum(1 for v in sel.values() if v["verdade"] != c and v["pred"] == c)
        por_classe[c] = {
            "n": total, "acertos": acertos,
            "recall": (acertos / total) if total else None,
            "recall_lb95": wilson(acertos, total, "lb") if total else None,
            "recall_cp95_lb": clopper_pearson(acertos, total, "lb") if total else None,
            "negativos": negativos, "fp": fp,
            "fp_taxa": (fp / negativos) if negativos else None,
            "fp_ub95": wilson(fp, negativos, "ub") if negativos else None,
        }
    n = len(sel)
    inconclusivos = sum(1 for v in sel.values() if v["pred"] == "inconclusivo")
    return {"fonte": fonte, "n": n, "matriz": {f"{a}->{b}": q for (a, b), q in sorted(matriz.items())},
            "por_classe": por_classe, "inconclusivo_n": inconclusivos,
            "inconclusivo_taxa": (inconclusivos / n) if n else None,
            "escalonados": sum(1 for v in sel.values() if v["motivos"])}


def vereditos(b: dict) -> list[dict]:
    """Go/no-go ligado ao RNF-02/RNF-03, pelo limite INFERIOR do IC (metodo exigido)."""
    saida = []
    for c, alvo in ALVOS.items():
        if alvo is None:
            continue
        d = b["por_classe"][c]
        lim_fp = LIMITES_FP.get(c, LIMITE_FP_PADRAO)
        if not d["n"]:
            saida.append({"classe": c, "veredito": "NAO_DECIDIVEL", "motivo": "sem itens desta classe"})
            continue
        lb = d["recall_lb95"]
        fp = d["fp_taxa"]
        ok = lb is not None and lb >= alvo and fp is not None and fp <= lim_fp
        saida.append({"classe": c, "veredito": "GO" if ok else "NO_GO",
                      "recall": d["recall"], "recall_lb95": lb, "alvo": alvo,
                      "fp_taxa": fp, "limite_fp": lim_fp, "n": d["n"],
                      "motivo": "limite inferior do IC atende" if ok else "limite inferior do IC abaixo do alvo ou FP acima"})
    if b["inconclusivo_taxa"] and b["inconclusivo_taxa"] > 0.10:
        saida.append({"classe": "-", "veredito": "NAO_DECIDIVEL",
                      "motivo": "inconclusivo em %.1f%% dos itens (>10%%)" % (100 * b["inconclusivo_taxa"])})
    return saida


def anotar(item_id: str, info: dict, destino: Path) -> str | None:
    """Escreve a imagem anotada do item: o que discriminou a decisao (D-25)."""
    try:
        import cv2
        import numpy as np
    except Exception:
        return None
    arq = info.get("arquivo")
    if not arq or not Path(arq).exists():
        return None
    img = cv2.imread(arq)
    if img is None:
        return None
    cor = CORES.get(info["pred"], (200, 200, 200))
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w - 1, h - 1), cor, 8)
    p = info.get("pred", "?")
    linhas = ["item: %s" % item_id, "previsto: %s | verdade: %s" % (p, info.get("verdade")),
              "confianca: %s" % (info.get("confianca") if info.get("confianca") is not None else "-")]
    for k, v in (info.get("medidas") or {}).items():
        try:
            linhas.append("%s: %.3f" % (k, float(v)))
        except (TypeError, ValueError):
            linhas.append("%s: %s" % (k, v))
    if info.get("motivos"):
        linhas.append("motivos: " + ", ".join(str(m) for m in info["motivos"])[:60])
    y = 24
    for linha in linhas[:7]:
        cv2.putText(img, linha, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, linha, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        y += 24
    destino.mkdir(parents=True, exist_ok=True)
    saida = destino / ("%s_anotado.png" % item_id)
    cv2.imwrite(str(saida), img)
    return str(saida)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Avaliacao da PoC-02 (por classe, com IC e FP)")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--predicoes", required=True)
    ap.add_argument("--anotar", default=None, help="diretorio para as imagens anotadas")
    ap.add_argument("--limiares", default=None, help="JSON dos limiares usados (vai para o relatorio)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    itens = carregar(Path(a.manifest), Path(a.predicoes))
    fontes = sorted({v["fonte"] for v in itens.values()})
    relatorio = {"fontes": [], "limiares": json.loads(Path(a.limiares).read_text()) if a.limiares
                 and Path(a.limiares).exists() else None,
                 "imagens_anotadas": []}

    for f in fontes:
        b = bloco(itens, f)
        b["vereditos"] = vereditos(b)
        relatorio["fontes"].append(b)

    if a.anotar:
        destino = Path(a.anotar)
        for k, v in itens.items():
            if "pred" in v:
                p = anotar(k, v, destino)
                if p:
                    relatorio["imagens_anotadas"].append(p)

    if a.json:
        print(json.dumps(relatorio, indent=1, ensure_ascii=False))
    else:
        for b in relatorio["fontes"]:
            print("== fonte: %s | n=%d | inconclusivo=%.1f%% | escalonados=%d" % (
                b["fonte"], b["n"], 100 * (b["inconclusivo_taxa"] or 0), b["escalonados"]))
            for c, d in b["por_classe"].items():
                if not d["n"]:
                    print("   %-20s n=0" % c)
                    continue
                print("   %-20s n=%-4d recall=%s LB95=%s CP95=%s | neg=%-4d FP=%s UB95=%s" % (
                    c, d["n"],
                    "%.3f" % d["recall"] if d["recall"] is not None else "-",
                    "%.3f" % d["recall_lb95"] if d["recall_lb95"] is not None else "-",
                    "%.3f" % d["recall_cp95_lb"] if d["recall_cp95_lb"] is not None else "-",
                    d["negativos"],
                    "%.3f" % d["fp_taxa"] if d["fp_taxa"] is not None else "-",
                    "%.3f" % d["fp_ub95"] if d["fp_ub95"] is not None else "-"))
            for v in b["vereditos"]:
                print("   -> %-18s %s (%s)" % (v["classe"], v["veredito"], v["motivo"]))
        if relatorio["imagens_anotadas"]:
            print("imagens anotadas: %d" % len(relatorio["imagens_anotadas"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
