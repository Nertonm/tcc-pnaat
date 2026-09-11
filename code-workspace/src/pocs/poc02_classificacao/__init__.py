"""PoC-02: classificacao de tampa (harness de metrica + politica de decisao)."""
from .classificacao import avaliar
from .politica_tampa import (
    AUSENTE,
    INCONCLUSIVO,
    MAL_ROSQUEADA,
    NORMAL,
    Decisao,
    GeometriaTampa,
    Limiares,
    aplicar_auxiliar,
    decidir,
)
__all__ = ["avaliar", "decidir", "aplicar_auxiliar", "GeometriaTampa", "Limiares",
           "Decisao", "NORMAL", "AUSENTE", "MAL_ROSQUEADA", "INCONCLUSIVO"]
