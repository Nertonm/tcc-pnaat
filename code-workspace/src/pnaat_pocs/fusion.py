"""PoC-04: fusao deterministica por votacao entre vistas.

Regra: classe com maioria estrita vence; empate ou discordancia sem maioria vira
ANALISE_HUMANA (não coberta pela regra, permanece para opiniao humana).
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

from .events import DefectClass, ViewResult


def fuse_views(results: Sequence[ViewResult]) -> tuple[DefectClass, float]:
    if not results:
        raise ValueError("sem resultados para fundir")

    votes = Counter(v.defect for v in results)
    top = votes.most_common()
    first = top[0][1]

    # maioria estrita: o topo tem mais votos que os demais somados
    total = sum(votes.values())
    if len(top) == 1:
        return top[0][0], _agg_confidence(results, top[0][0])

    # empate no topo => analise humana
    if top[0][1] == top[1][1]:
        return DefectClass.ANALISE_HUMANA, max(v.confidence for v in results)

    if first * 2 > total:
        return top[0][0], _agg_confidence(results, top[0][0])

    return DefectClass.ANALISE_HUMANA, max(v.confidence for v in results)


def _agg_confidence(results: Sequence[ViewResult], defect: DefectClass) -> float:
    votes = [v.confidence for v in results if v.defect == defect]
    return round(max(votes), 4) if votes else 0.0
