#!/usr/bin/env python3
"""Valida os pares (imagem editada + JSON [+ mascara]) do dataset sintetico.

Checa, por par:
  1. existe o JSON correspondente e o schema minimo;
  2. classe valida e bbox dentro da imagem;
  3. `arquivo_saida` bate com o nome do arquivo;
  4. mascara (se houver) tem o mesmo tamanho e fica dentro do bbox;
  5. ISOLAMENTO: comparando com a foto original, as diferencas ficam dentro do bbox;
  6. duplicatas (sha256) e balanceamento por classe.

Saida: relatorio no stdout + opcional --json-out. Exit 0 = tudo PASS; 1 = algum FAIL.

Uso:
  python validar_pares.py --pares DIR --origem DIR [--tol 12] [--max-outside 0.01] [--json-out rep.json]
  python validar_pares.py --pares DIR --schema-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image
import numpy as np

CLASSES = {"tampa_ausente", "tampa_mal_rosqueada", "deformidade"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(65536), b""):
            h.update(blk)
    return h.hexdigest()


def find_original(name: str, classe: str, origem: Path | None) -> Path | None:
    if origem is None:
        return None
    cand = [name, name.replace(f"{classe}_", "", 1)]
    for c in cand:
        p = origem / c
        if p.exists():
            return p
    return None


def validate_pair(img_path: Path, origem: Path | None, tol: int, max_outside: float, schema_only: bool) -> dict:
    res = {"arquivo": img_path.name, "status": "PASS", "problemas": []}

    def fail(msg: str) -> None:
        res["status"] = "FAIL"
        res["problemas"].append(msg)

    json_path = img_path.with_suffix(".json")
    if not json_path.exists():
        fail("JSON ausente")
        return res
    try:
        meta = json.loads(json_path.read_text())
    except Exception as e:  # noqa: BLE001
        fail(f"JSON invalido: {e}")
        return res

    for k in ("classe", "regiao", "arquivo_saida"):
        if k not in meta:
            fail(f"campo obrigatorio ausente: {k}")
    if res["problemas"]:
        return res

    if meta["classe"] not in CLASSES:
        fail(f"classe invalida: {meta['classe']}")
    if meta["arquivo_saida"] != img_path.name:
        fail(f"arquivo_saida ({meta['arquivo_saida']}) != arquivo real ({img_path.name})")

    try:
        im = Image.open(img_path)
        im.load()
        W, H = im.size
    except Exception as e:  # noqa: BLE001
        fail(f"imagem invalida: {e}")
        return res

    reg = meta["regiao"]
    if not (isinstance(reg, (list, tuple)) and len(reg) == 4 and all(isinstance(v, (int, float)) for v in reg)):
        fail("regiao deve ser [x,y,w,h]")
        return res
    x, y, w, h = (int(v) for v in reg)
    if w <= 0 or h <= 0:
        fail("regiao com w/h <= 0")
    if x < 0 or y < 0 or x + w > W or y + h > H:
        fail(f"regiao fora da imagem {W}x{H}: {reg}")

    # mascara opcional
    mask_path = img_path.with_name(img_path.stem + "_mask.png")
    if mask_path.exists():
        m = np.array(Image.open(mask_path).convert("L"))
        if m.shape != (H, W):
            fail(f"mascara {m.shape} != imagem {(H, W)}")
        else:
            ys, xs = np.where(m > 127)
            if xs.size and (xs.min() < x or ys.min() < y or xs.max() > x + w - 1 or ys.max() > y + h - 1):
                fail("mascara tem pixels fora do bbox declarado")

    if not schema_only:
        orig_p = None
        if meta.get("arquivo_original") and origem is not None:
            cand = origem / meta["arquivo_original"]
            if cand.exists():
                orig_p = cand
            else:
                fail(f"arquivo_original nao existe em origem/: {meta['arquivo_original']}")
        if orig_p is None and not res["problemas"]:
            orig_p = find_original(img_path.name, meta["classe"], origem)
        if orig_p is None and not res["problemas"]:
            fail("original nao encontrado (informe arquivo_original ou --origem com o nome certo)")
        if orig_p is not None:
            o = Image.open(orig_p).convert("RGB")
            e = Image.open(img_path).convert("RGB")
            if o.size != e.size:
                fail(f"tamanho original {o.size} != editada {e.size}")
            else:
                a = np.asarray(o, dtype=np.int16)
                b = np.asarray(e, dtype=np.int16)
                changed = (np.abs(a - b).max(axis=2) > tol)
                out = changed.copy()
                out[y:y + h, x:x + w] = False
                ratio = float(out.sum()) / float(changed.size)
                res["diff_fora_bbox"] = round(ratio, 6)
                if ratio > max_outside:
                    fail(f"edicao nao isolada: {ratio:.4%} dos pixels mudaram fora do bbox (limite {max_outside:.2%})")

    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", required=True, type=Path)
    ap.add_argument("--origem", type=Path, default=None)
    ap.add_argument("--tol", type=int, default=12)
    ap.add_argument("--max-outside", type=float, default=0.002)
    ap.add_argument("--schema-only", action="store_true")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    imgs = sorted(p for p in args.pares.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXT
                  and not p.stem.endswith("_mask"))
    if not imgs:
        print(f"nenhuma imagem em {args.pares}")
        return 1

    resultados = [validate_pair(p, args.origem, args.tol, args.max_outside, args.schema_only) for p in imgs]
    fails = [r for r in resultados if r["status"] == "FAIL"]
    classes = Counter(r["arquivo"].split("_")[0] for r in resultados)
    hashes = Counter(sha256(p) for p in imgs)
    dups = [h for h, c in hashes.items() if c > 1]

    print(f"total={len(resultados)} PASS={len(resultados)-len(fails)} FAIL={len(fails)}")
    for r in resultados:
        if "diff_fora_bbox" in r:
            print(f"  {r['status']} {r['arquivo']}: diff_fora_bbox={r['diff_fora_bbox']:.4%}")
    for r in fails:
        print(f"  FAIL {r['arquivo']}: {'; '.join(r['problemas'])}")
    print("por classe (prefixo):", dict(classes))
    if dups:
        print(f"duplicatas (sha256 repetido): {len(dups)}")

    if args.json_out:
        args.json_out.write_text(json.dumps(
            {"total": len(resultados), "fails": fails, "classes": dict(classes), "duplicatas": len(dups)},
            ensure_ascii=False, indent=1))

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())