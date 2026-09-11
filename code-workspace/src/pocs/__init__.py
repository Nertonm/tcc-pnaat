"""pocs: nucleo de codigo das PoCs do Cenario 1 (inspecao de envase)."""
from .events import CLASSES_DE_DEFEITO, DefectClass, Dominio, ObservationEvent, Qualidade, ViewResult
from .poc01_trigger import CaptureRun, PresenceTrigger
from .poc04_fusao import ConfiguracaoFusao, Fusao, fundir, papel
from .poc05_registro import LocalRegistry
from .poc06_resiliencia import retry_until_persist
from .poc07_dashboard import bootstrap_events, recorrencia, summarize
from .pocfinal import concluir_ensaio, executar_ensaio

__all__ = [
    "CLASSES_DE_DEFEITO", "DefectClass", "Dominio", "ObservationEvent", "Qualidade", "ViewResult",
    "CaptureRun", "PresenceTrigger",
    "ConfiguracaoFusao", "Fusao", "fundir", "papel",
    "LocalRegistry", "retry_until_persist",
    "bootstrap_events", "recorrencia", "summarize",
    "concluir_ensaio", "executar_ensaio",
]
