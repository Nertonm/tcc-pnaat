"""pocs: nucleo de codigo das PoCs do Cenário 1 (inspecao de envase)."""
from .events import DefectClass, ObservationEvent, ViewResult
from .poc01_trigger import CaptureRun, PresenceTrigger
from .poc04_fusao import fuse_views
from .poc05_registro import LocalRegistry
from .poc06_resiliencia import retry_until_persist
from .poc07_dashboard import bootstrap_events, recorrencia, summarize
from .pocfinal import concluir_ensaio, executar_ensaio

__all__ = [
    "DefectClass", "ObservationEvent", "ViewResult",
    "CaptureRun", "PresenceTrigger",
    "fuse_views", "LocalRegistry", "retry_until_persist",
    "bootstrap_events", "recorrencia", "summarize",
    "concluir_ensaio", "executar_ensaio",
]
