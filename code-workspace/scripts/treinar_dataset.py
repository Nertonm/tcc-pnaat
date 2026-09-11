#!/usr/bin/env python3
"""Treina/avalia um modelo one-class no NOSSO dataset (normal vs defective).

Estrutura esperada (padrao anomalib Folder):
  <root>/normal/*      (imagens OK)  -> treino
  <root>/defective/*   (imagens com defeito; opcionalmente tambem _mask.png) -> teste

Uso (usar o venv com anomalib: <TCC_HOME>/github/.venv/bin/python):
  python treinar_dataset.py [--root DIR] [--model patchcore|padim|efficientad] [--epochs N]
                            [--exigir-defeitos] [--amostras-stats N]

Sem imagens de defeito o treino one-class continua valido (PatchCore/PaDiM aprendem so com
normais): o script avisa, pula o teste (nao ha AUROC sem anomalia) e deriva o limiar de score
a partir da distribuicao das proprias normais, gravando resultados/modelo_info.json.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

TCC_HOME = os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat"))
BASE_DATASETS = Path(TCC_HOME) / "datasets"

from anomalib.data import Folder
from anomalib.engine import Engine
from anomalib.models import EfficientAd, Padim, Patchcore

MODELS = {"patchcore": (Patchcore, 1), "padim": (Padim, 1), "efficientad": (EfficientAd, 20)}


def _ckpt_mais_novo(raiz: Path) -> Path | None:
    arquivos = sorted(raiz.rglob("*.ckpt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return arquivos[0] if arquivos else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=BASE_DATASETS / "pnaat" / "dataset")
    ap.add_argument("--model", choices=sorted(MODELS), default="patchcore")
    ap.add_argument("--epochs", type=int, default=0, help="0 = usa o default do modelo")
    ap.add_argument("--exigir-defeitos", action="store_true",
                    help="aborta se nao houver imagens de defeito (comportamento antigo)")
    ap.add_argument("--amostras-stats", type=int, default=20,
                    help="quantas normais usar para derivar o limiar de score (0 = todas)")
    args = ap.parse_args()

    normais = sorted((args.root / "normal").glob("*.jpg")) + sorted((args.root / "normal").glob("*.png"))
    defect = sorted((args.root / "defective").glob("*")) if (args.root / "defective").exists() else []
    print(f"dataset: normal={len(normais)} defective={len(defect)}")
    if not normais:
        print("ERRO: nenhuma imagem normal em", args.root / "normal")
        return 2
    if not defect and args.exigir_defeitos:
        print("SEM defeitos: abortado por --exigir-defeitos.")
        return 2
    if not defect:
        print("AVISO: sem defeito no dataset. Treino one-class apenas com normais; "
              "AUROC/matriz de confusao ficam PENDENTES ate existir defeito.")

    cls, default_epochs = MODELS[args.model]
    epochs = args.epochs or default_epochs
    if defect:
        dm = Folder(name="pnaat", root=args.root, normal_dir="normal", abnormal_dir="defective")
    else:
        # anomalib exige a pasta de anormais apenas para montar o split; em one-class puro
        # treinamos so com normais e validamos por holdout do proprio conjunto normal.
        dm = Folder(name="pnaat", root=args.root, normal_dir="normal",
                    val_split_mode="from_train", val_split_ratio=0.2)
    dm.setup()
    raiz_resultados = args.root.parent / "resultados"
    eng = Engine(max_epochs=epochs, accelerator="auto", devices=1, enable_progress_bar=False,
                 default_root_dir=str(raiz_resultados))
    model = cls()
    eng.fit(model=model, datamodule=dm)
    print("FIT ok")

    if defect:
        res = eng.test(model=model, datamodule=dm)
        m = res[0] if isinstance(res, (list, tuple)) and res else res
        print("METRICAS", args.model, json.dumps(m, default=str))
    else:
        print("teste pulado: sem anomalias de referencia")

    ckpt = _ckpt_mais_novo(raiz_resultados)
    info: dict = {"modelo": args.model, "epochs": epochs, "n_normal": len(normais),
                  "n_defective": len(defect), "checkpoint": str(ckpt) if ckpt else None,
                  "raiz_resultados": str(raiz_resultados)}

    if ckpt and args.amostras_stats:
        amostras = normais if args.amostras_stats <= 0 else normais[: args.amostras_stats]
        try:
            import numpy as np

            preds = eng.predict(model=model, data_path=str(args.root / "normal"),
                                ckpt_path=str(ckpt))
            scores = []
            for p in preds:
                s = getattr(p, "pred_score", None)
                if s is None:
                    continue
                scores.append(float(np.asarray(s).ravel()[0]))
            if scores:
                arr = np.asarray(scores, dtype=float)
                limiar = float(arr.mean() + 3.0 * arr.std(ddof=1))
                info["score_normais"] = {
                    "n": int(arr.size),
                    "media": float(arr.mean()),
                    "desvio": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
                    "min": float(arr.min()),
                    "max": float(arr.max()),
                }
                info["limiar_3sigma"] = limiar
                print(f"score normais: media={arr.mean():.4f} desvio={arr.std(ddof=1):.4f} "
                      f"limiar(3sigma)={limiar:.4f}")
        except Exception as e:  # nao falha o treino por causa das estatisticas
            info["erro_stats"] = str(e)[:300]
            print("aviso: estatisticas de score nao calculadas:", e)

    destino = raiz_resultados / "modelo_info.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(info, indent=1, default=str))
    print("modelo_info:", destino)
    print("checkpoint:", ckpt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
