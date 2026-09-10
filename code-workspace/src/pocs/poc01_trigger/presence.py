"""PoC-01: trigger de presenca + janela de captura multi-view."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CaptureRun:
    item_window_id: str
    views: tuple[str, ...]


class PresenceTrigger:
    def __init__(self, views: tuple[str, ...] = ("topo", "lateral1", "lateral2"), debounce: int = 2) -> None:
        if debounce < 1:
            raise ValueError("debounce deve ser >= 1")
        self._views = tuple(views)
        self._debounce = debounce
        self._hits = 0
        self._misses = 0
        self._open = False
        self._counter = 0

    def update(self, detected: bool) -> Optional[CaptureRun]:
        if detected:
            self._hits += 1
            self._misses = 0
            if not self._open and self._hits >= self._debounce:
                self._open = True
                self._counter += 1
                return CaptureRun(item_window_id=f"w-{self._counter}", views=self._views)
        else:
            self._misses += 1
            self._hits = 0
            if self._open and self._misses >= self._debounce:
                self._open = False
        return None

    @property
    def is_open(self) -> bool:
        return self._open
