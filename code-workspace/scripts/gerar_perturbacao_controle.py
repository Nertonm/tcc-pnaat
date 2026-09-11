#!/usr/bin/env python3
"""Gera uma perturbacao de CONTROLE numa frame real (nao e defeito real nem par de dataset).

Serve para provar, no video da PoC, que a tecnologia central REAGE a uma anomalia conhecida:
o chao de verdade (regiao afetada) fica registrado, o que permite comparar com o mapa do modelo.

    python3 scripts/gerar_perturbacao_controle.py --origem <frame.jpg> [--tipo oclusao|risco]
                                                 [--dest DIR] [--seed N]

Saidas em <dest>: <stem>_controle_<tipo>.jpg, <stem>_controle_<tipo>_mask.png e .json com
proveniencia (sha256 da origem, regiao em bbox, ferramenta, seed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def oclusao(img: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Mancha escura de bordas suaves no corpo (2/3 inferiores): simula amassado/oclusao."""
    h, w = img.shape[:2]
    cx = int(w * rng.uniform(0.35, 0.65))
    cy = int(h * rng.uniform(0.60, 0.80))
    r = int(min(w, h) * rng.uniform(0.06, 0.09))
    mask = np.zeros((h, w), np.float32)
    cv2.circle(mask, (cx, cy), r, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), r * 0.45)
    fator = 1.0 - 0.55 * mask[..., None]
    out = np.clip(img.astype(np.float32) * fator, 0, 255).astype(np.uint8)
    return out, (cx - r, cy - r, 2 * r, 2 * r)


def risco(img: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Risco claro fino e comprido no corpo: simula arranhão."""
    h, w = img.shape[:2]
    x0 = int(w * rng.uniform(0.30, 0.45))
    y0 = int(h * rng.uniform(0.55, 0.75))
    x1 = int(min(w - 1, x0 + w * rng.uniform(0.20, 0.30)))
    y1 = int(min(h - 1, y0 + h * rng.uniform(0.05, 0.12)))
    out = img.copy()
    cv2.line(out, (x0, y0), (x1, y1), (245, 245, 245), 2, cv2.LINE_AA)
    return out, (x0, y0, x1 - x0, y1 - y0)


GERADORES = {"oclusao": oclusao, "risco": risco}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origem", type=Path, required=True)
    ap.add_argument("--tipo", choices=sorted(GERADORES), default="oclusao")
    ap.add_argument("--dest", type=Path, default=Path("controle"))
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    if not args.origem.is_file():
        print("origem inexistente:", args.origem)
        return 2
    img = cv2.imread(str(args.origem))
    if img is None:
        print("nao consegui ler a imagem:", args.origem)
        return 2

    rng = np.random.default_rng(args.seed)
    perturbada, bbox = GERADORES[args.tipo](img, rng)
    args.dest.mkdir(parents=True, exist_ok=True)
    stem = f"{args.origem.stem}_controle_{args.tipo}"
    destino = args.dest / f"{stem}.jpg"
    cv2.imwrite(str(destino), perturbada, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

    mask = np.zeros(img.shape[:2], np.uint8)
    x, y, w, h = bbox
    mask[max(0, y): y + h, max(0, x): x + w] = 255
    cv2.imwrite(str(args.dest / f"{stem}_mask.png"), mask)

    meta = {
        "origem": str(args.origem),
        "origem_sha256": _sha256(args.origem),
        "perturbacao": args.tipo,
        "bbox_xywh": [int(v) for v in bbox],
        "seed": args.seed,
        "ferramenta": "gerar_perturbacao_controle.py",
        "aviso": "CONTROLE: nao e defeito real nem par sintetico do dataset; serve para provar "
                 "que o pipeline reage a uma anomalia conhecida.",
    }
    (args.dest / f"{stem}.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(f"CONTROLE gerado: {destino}")
    print(f"  regiao afetada (xywh): {bbox}  | mascara: {stem}_mask.png")
    print(f"  aviso: {meta['aviso']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
