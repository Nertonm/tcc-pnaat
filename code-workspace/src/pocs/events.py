"""Modelos de dominio das PoCs: evento de observacao por item.

Vocabulario canonico das classes (D-28) e dominio da medida (D-04/D-23).
A decisao do item e POR DOMINIO: nenhuma vista cancela o defeito detectado em outro dominio.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DefectClass(str, Enum):
    """Vocabulario canonico das classes (D-28). Nome divergente e legado."""

    NORMAL = "normal"
    TAMPA_AUSENTE = "tampa_ausente"
    TAMPA_MAL_ROSQUEADA = "tampa_mal_rosqueada"
    DEFORMIDADE = "deformidade"
    INCONCLUSIVO = "inconclusivo"


class Dominio(str, Enum):
    """Dominio a que uma medida se refere (D-04)."""

    TAMPA = "tampa"
    CORPO = "corpo"
    DIMENSAO = "dimensao"  # check dimensional independente da vista de topo (D-23)


class Qualidade(str, Enum):
    """Qualidade da medida (nao e a confianca do classificador)."""

    OK = "ok"
    INSUFICIENTE = "insuficiente"  # a medida existe, mas nao atende ao criterio de captura
    AUSENTE = "ausente"  # esta vista nao produziu medida para este dominio


#: Classes de defeito admissiveis por dominio: trava de coerencia dominio x classe.
CLASSES_DE_DEFEITO: dict[Dominio, tuple[DefectClass, ...]] = {
    Dominio.TAMPA: (DefectClass.TAMPA_AUSENTE, DefectClass.TAMPA_MAL_ROSQUEADA),
    Dominio.CORPO: (DefectClass.DEFORMIDADE,),
    Dominio.DIMENSAO: (),  # o check dimensional nao classifica defeito: ele veta/escala
}


@dataclass(frozen=True)
class ViewResult:
    """UMA medida de UMA vista, no dominio a que ela se refere.

    Uma vista lateral mede dois dominios (tampa e corpo) e por isso emite DOIS ViewResult.
    `escalona`/`motivo` atendem ao check dimensional (D-23), que nao classifica nem aprova:
    apenas veta/escala o item.
    """

    view_id: str
    dominio: Dominio
    defect: DefectClass
    confidence: float
    qualidade: Qualidade = Qualidade.OK
    escalona: bool = False
    motivo: str | None = None

    def __post_init__(self) -> None:
        if not self.view_id:
            raise ValueError("view_id obrigatorio")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar em [0,1]")
        if self.defect in (DefectClass.NORMAL, DefectClass.INCONCLUSIVO):
            return
        if self.defect not in CLASSES_DE_DEFEITO[self.dominio]:
            raise ValueError(
                f"classe {self.defect.value} nao pertence ao dominio {self.dominio.value}"
            )


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
    fusao: dict | None = None  # resultado por dominio do PoC-04 (status_tampa/status_corpo/...)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar em [0,1]")
        if not self.views:
            raise ValueError("evento sem vistas")
