"""PoC-Final: conjectura integrada (trigger -> fusao -> registro -> dashboard)."""
from __future__ import annotations

from typing import Optional

from ..events import ObservationEvent
from ..poc05_registro import LocalRegistry
from ..poc07_dashboard import recorrencia, summarize


def concluir_ensaio(registry: LocalRegistry, eventos: list[ObservationEvent]) -> dict:
    for ev in eventos:
        registry.upsert(ev)
    return summarize(registry)


def executar_ensaio(eventos: list[ObservationEvent], esteira_id: Optional[str] = None) -> dict:
    registry = LocalRegistry()
    resumo = concluir_ensaio(registry, eventos)
    resumo["recorrencia"] = recorrencia(registry, esteira_id=esteira_id)
    return resumo
