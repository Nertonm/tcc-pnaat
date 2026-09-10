"""PoC-01: trigger de presenca + janela de captura multi-view.

Logica executa no ESP32 (MicroPython) e em desktop para CI. O sensor E18-D80NK e
IR difuso com saida digital NPN NO: LOW = objeto dentro do alcance (active low).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

E18_D80NK_ACTIVE_LOW = True


def present_from_sensor(level: int, active_low: bool = E18_D80NK_ACTIVE_LOW) -> bool:
    """Converte o nivel logico do E18-D80NK em 'presente (objeto dentro do alcance)'.

    E18-D80NK: saida LOW indica deteccao (ativo em nivel baixo).
    """
    if level not in (0, 1):
        raise ValueError("nivel logico deve ser 0 ou 1")
    return (level == 0) if active_low else (level == 1)


@dataclass(frozen=True)
class CaptureRun:
    item_window_id: str
    views: tuple[str, ...]


class PresenceTrigger:
    """Debounce de presenca + abertura/fechamento da janela de captura multi-view."""

    def __init__(
        self,
        views: tuple[str, ...] = ("topo", "lateral1", "lateral2"),
        stable_reads: int = 5,
        miss_reads: int = 5,
    ) -> None:
        if stable_reads < 1 or miss_reads < 1:
            raise ValueError("stable_reads e miss_reads devem ser >= 1")
        self._views = tuple(views)
        self._stable_reads = stable_reads
        self._miss_reads = miss_reads
        self._hits = 0
        self._misses = 0
        self._open = False
        self._counter = 0

    def update(self, present: bool) -> Optional[CaptureRun]:
        """Alimenta com a presenca ja convertida (LOW = presente). Retorna a abertura so na borda de subida."""
        if present:
            self._hits += 1
            self._misses = 0
            if not self._open and self._hits >= self._stable_reads:
                self._open = True
                self._counter += 1
                return CaptureRun(item_window_id=f"w-{self._counter}", views=self._views)
        else:
            self._misses += 1
            self._hits = 0
            if self._open and self._misses >= self._miss_reads:
                self._open = False
        return None

    @property
    def is_open(self) -> bool:
        return self._open