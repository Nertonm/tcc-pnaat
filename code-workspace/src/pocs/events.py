"""Modelos de dominio das PoCs: evento de observacao por item."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DefectClass(str, Enum):
    NORMAL = "normal"
    CAP_AUSENTE = "cap_ausente"
    CAP_MAL_ROSQUEADA = "cap_mal_rosqueada"
    DEFORMIDADE = "deformidade"
    ANALISE_HUMANA = "analise_humana"


@dataclass(frozen=True)
class ViewResult:
    view_id: str
    defect: DefectClass
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar em [0,1]")


@dataclass(frozen=True)
class ObservationEvent:
    event_id: str
    item_id: str
    esteira_id: str
    node_id: str
    location: str
    recorded_at: str  # ISO8601 com fuso
    views: tuple[ViewResult, ...]
    fused: DefectClass
    confidence: float
    quality: str = "ok"  # ok | parcial | falha

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar em [0,1]")
        if not self.views:
            raise ValueError("evento sem vistas")
