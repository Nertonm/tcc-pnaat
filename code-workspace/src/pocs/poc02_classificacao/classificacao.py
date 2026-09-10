"""PoC-02: harness de avaliacao do classificador de tampas (RNF-02)."""
from __future__ import annotations

from collections import Counter
from typing import Sequence


def avaliar(previsto: Sequence[str], verdade: Sequence[str], limiar: float = 0.95) -> dict:
    if len(previsto) != len(verdade):
        raise ValueError("previsto e verdade devem ter o mesmo tamanho")
    total = len(previsto)
    if total == 0:
        raise ValueError("sem amostras para avaliar")
    acertos = sum(1 for p, v in zip(previsto, verdade) if p == v)
    acuracia = acertos / total
    matriz = Counter((v, p) for v, p in zip(verdade, previsto))
    return {
        "n": total,
        "acuracia": round(acuracia, 4),
        "aprova_rnf02": acuracia >= limiar,
        "limiar": limiar,
        "matriz_confusao": {f"{v}->{p}": c for (v, p), c in matriz.items()},
    }
