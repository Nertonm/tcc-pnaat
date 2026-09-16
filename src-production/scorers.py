"""Scorers plugaveis para o harness de avaliacao (avaliacao_ood.py).

Cada funcao recebe o caminho de UMA imagem e devolve:
  - float            -> probabilidade de defeito (AUROC de imagem)
  - list[box]        -> caixas em pixel [x1, y1, x2, y2] (recall por IoU / FPR)

Configuracao por ambiente (nada de caminho fixo no codigo):
  PNAAT_PESOS        pesos do modelo (default: v0-lateral-detector best.pt)
  PNAAT_CONF         confianca minima (default 0.05; mesma do relatorio de baseline)
  PNAAT_IMGSZ        tamanho de inferencia (default 320; igual ao treino)
  PNAAT_CLASSE_BOA   nome da classe considerada "sem defeito" (default normal)
"""

from __future__ import annotations

import os
from pathlib import Path

PESOS = os.environ.get(
    "PNAAT_PESOS",
    str(Path(os.environ.get("PNAAT_MODELOS_DIR") or Path.home() / "pnaat-modelos") / "v0-lateral-detector/runs/v0-lateral-yolov8n/weights/best.pt"),
)
CONF = float(os.environ.get("PNAAT_CONF", "0.05"))
IMGSZ = int(os.environ.get("PNAAT_IMGSZ", "320"))
CLASSE_BOA = os.environ.get("PNAAT_CLASSE_BOA", "normal")

_modelo = None


def modelo():
    global _modelo
    if _modelo is None:
        from ultralytics import YOLO

        _modelo = YOLO(PESOS)
    return _modelo


def _predicao(caminho: str):
    r = modelo().predict(caminho, imgsz=IMGSZ, conf=CONF, verbose=False)[0]
    nomes = r.names or {}
    caixas = []
    if r.boxes is not None and len(r.boxes) > 0:
        xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy().astype(int)
        for (x1, y1, x2, y2), c, k in zip(xyxy, confs, classes):
            caixas.append(
                {
                    "box": (float(x1), float(y1), float(x2), float(y2)),
                    "conf": float(c),
                    "classe": nomes.get(int(k), str(k)),
                }
            )
    return caixas


def v0_caixas(caminho: str):
    """Caixas de QUALQUER classe (uso: recall generico contra a verdade da fonte)."""
    return [c["box"] for c in _predicao(caminho)]


def v0_caixas_defeito(caminho: str):
    """Caixas de classe != 'normal'; alarme de defeito (uso: FPR em imagens good)."""
    return [c["box"] for c in _predicao(caminho) if c["classe"] != CLASSE_BOA]


def v0_alarme(caminho: str) -> float:
    """Confianca maxima entre as classes de defeito (0.0 se nao houver alarme)."""
    altas = [c["conf"] for c in _predicao(caminho) if c["classe"] != CLASSE_BOA]
    return max(altas) if altas else 0.0
