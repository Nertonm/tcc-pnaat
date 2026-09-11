#!/usr/bin/env python3
"""Valida os pares gerados e monta o dataset de treino (defective) + relatorio.

Reusa o gate do validar_pares.py (schema, bbox, mascara, isolamento). So copia o que PASS.
O que falha vai para o relatorio e para --rejeitados (opcional).

Uso:
  python montar_dataset.py [--gerados DIR] [--origem DIR] [--dest DIR] [--report PATH]
                           [--tol 12] [--max-outside 0.002] [--dry-run] [--strict]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

TCC_HOME = os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat"))
BASE_DATASETS = Path(TCC_HOME) / "datasets"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validar_pares import IMG_EXT, validate_pair  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gerados", type=Path, default=BASE_DATASETS / "pnaat" / "gerados")
    ap.add_argument("--origem", type=Path, default=BASE_DATASETS / "pnaat" / "origem")
    ap.add_argument("--dest", type=Path, default=BASE_DATASETS / "pnaat" / "dataset" / "defective")
    ap.add_argument("--report", type=Path,
                    default=BASE_DATASETS / "pnaat" / "revisao" / "relatorio_dataset.json")
    ap.add_argument("--tol", type=int, default=12)
    ap.add_argument("--max-outside", type=float, default=0.002)
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 se houve qualquer FAIL")
    args = ap.parse_args()

    imgs = sorted(p for p in args.gerados.rglob("*")
                  if p.is_file() and p.suffix.lower() in IMG_EXT and not p.stem.endswith("_mask"))
    results, aprovados, rejeitados = [], [], []
    for p in imgs:
        r = validate_pair(p, args.origem, args.tol, args.max_outside, schema_only=False, margin=args.margin)
        results.append(r)
        (aprovados if r["status"] == "PASS" else rejeitados).append(r)

    copiados = 0
    if not args.dry_run:
        for r in aprovados:
            src = args.gerados / r["arquivo"] if (args.gerados / r["arquivo"]).exists() else next(
                (q for q in imgs if q.name == r["arquivo"]), None)
            if src is None:
                continue
            cls = json.loads(src.with_suffix(".json").read_text()).get("classe", "outros")
            d = args.dest / cls
            d.mkdir(parents=True, exist_ok=True)
            for extra in (src, src.with_suffix(".json"), src.with_name(src.stem + "_mask.png")):
                if extra.exists():
                    shutil.copy(extra, d / extra.name)
            copiados += 1

    por_classe = Counter(json.loads((args.gerados / r["arquivo"]).with_suffix(".json").read_text()).get("classe", "?")
                         for r in aprovados if (args.gerados / r["arquivo"]).exists())
    rel = {
        "total": len(results), "aprovados": len(aprovados), "rejeitados": len(rejeitados),
        "copiados": copiados, "dry_run": args.dry_run, "por_classe": dict(por_classe),
        "rejeitados_detalhe": rejeitados,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(rel, ensure_ascii=False, indent=1))

    print(f"total={len(results)} aprovados={len(aprovados)} rejeitados={len(rejeitados)} copiados={copiados}")
    if por_classe:
        print("por classe:", dict(por_classe))
    for r in rejeitados:
        print(f"  REJEITADO {r['arquivo']}: {'; '.join(r['problemas'])}")
    print("relatorio:", args.report)
    return 1 if (args.strict and rejeitados) else 0


if __name__ == "__main__":
    sys.exit(main())