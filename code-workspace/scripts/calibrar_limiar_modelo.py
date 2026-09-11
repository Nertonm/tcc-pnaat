#!/usr/bin/env python3
"""Calibra o limiar do modelo usando o sinal CRU (maximo do mapa de anomalia) nas normais.

Por que: em anomalib 2.6.1 o `pred_score` retornado satura (0 ou 1) porque passa por
normalizacao com os limites do conjunto: nao serve como medida comparavel entre itens nem
entre execucoes. O `anomaly_map` cru (maximo) e uma distancia comparavel: medimos a distribuicao
nas NORMais e derivamos o limiar.

    python3 scripts/calibrar_limiar_modelo.py [--amostras 0] [--percentil 99]

Atualiza datasets/pnaat/resultados/modelo_info.json com:
    score_bruto_normais {n, media, desvio, min, max, p99}
    limiar_bruto (max(p99, media + 3*desvio))
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

TCC_HOME = Path(os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat")))
BASE = Path(os.environ.get("PNAAT_DATASETS", str(TCC_HOME / "datasets" / "pnaat")))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--amostras", type=int, default=0, help="0 = todas as normais")
    ap.add_argument("--percentil", type=float, default=99.0)
    ap.add_argument("--pasta", type=Path, default=None, help="pasta de imagens (default: normal/)")
    args = ap.parse_args()

    from anomalib.engine import Engine
    from anomalib.models import Padim, Patchcore

    info_path = BASE / "resultados" / "modelo_info.json"
    if not info_path.exists():
        print("modelo_info.json ausente: treine primeiro")
        return 2
    info = json.loads(info_path.read_text())
    ckpt = info.get("checkpoint")
    if not ckpt or not Path(ckpt).exists():
        print("checkpoint ausente:", ckpt)
        return 2

    pasta = args.pasta or (BASE / "dataset" / "normal")
    imgs = sorted(pasta.glob("*.jpg")) + sorted(pasta.glob("*.png"))
    if args.amostras > 0:
        imgs = imgs[: args.amostras]
    if not imgs:
        print("sem imagens em", pasta)
        return 2

    modelo_cls = {"patchcore": Patchcore, "padim": Padim}[info.get("modelo", "patchcore")]
    eng = Engine(accelerator="auto", devices=1, enable_progress_bar=False,
                 default_root_dir=str(BASE / "resultados"))
    preds = eng.predict(model=modelo_cls(), data_path=str(pasta), ckpt_path=ckpt)

    scores: dict[str, float] = {}
    for lote in preds:
        mapas = getattr(lote, "anomaly_map", None)
        for i, caminho in enumerate(list(lote.image_path)):
            m = np.asarray(mapas)[i].squeeze().astype(np.float64)
            scores[Path(str(caminho)).name] = float(m.max())

    arr = np.asarray(list(scores.values()), dtype=float)
    p99 = float(np.percentile(arr, args.percentil))
    limiar = float(max(p99, arr.mean() + 3.0 * arr.std(ddof=1)))
    info["score_bruto_normais"] = {
        "n": int(arr.size), "media": float(arr.mean()),
        "desvio": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        "min": float(arr.min()), "max": float(arr.max()), "p99": p99,
        "sinal": "maximo do anomaly_map (cru)",
    }
    info["limiar_bruto"] = limiar
    info_path.write_text(json.dumps(info, indent=1, default=str))

    print(f"normais medidas: {arr.size} (pasta {pasta})")
    print(f"map.max: media={arr.mean():.4f} desvio={arr.std(ddof=1):.4f} "
          f"min={arr.min():.4f} max={arr.max():.4f} p99={p99:.4f}")
    print(f"LIMIAR BRUTO = {limiar:.4f}")
    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:5]
    print("maiores (normais):", [(n, round(v, 4)) for n, v in top])
    print("modelo_info atualizado:", info_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
