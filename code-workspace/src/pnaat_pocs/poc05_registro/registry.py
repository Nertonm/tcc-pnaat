"""PoC-05: registro local sem perda nem duplicacao."""
from __future__ import annotations

from typing import Optional, Sequence

from ..events import DefectClass, ObservationEvent


class LocalRegistry:
    def __init__(self) -> None:
        self._store: dict[str, ObservationEvent] = {}

    def upsert(self, event: ObservationEvent) -> str:
        # idempotente: reenvio do mesmo event_id não duplica
        if event.event_id in self._store:
            return "exists"
        self._store[event.event_id] = event
        return "stored"

    def get(self, event_id: str) -> Optional[ObservationEvent]:
        return self._store.get(event_id)

    @property
    def size(self) -> int:
        return len(self._store)

    def reconcile(self, expected_ids: set[str]) -> dict:
        missing = sorted(expected_ids - set(self._store))
        return {"missing": missing, "stored": self.size}

    def query(
        self,
        esteira_id: Optional[str] = None,
        defect: Optional[DefectClass] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> list[ObservationEvent]:
        out = []
        for ev in self._store.values():
            if esteira_id and ev.esteira_id != esteira_id:
                continue
            if defect and ev.fused != defect:
                continue
            if start and ev.recorded_at < start:
                continue
            if end and ev.recorded_at > end:
                continue
            out.append(ev)
        return out

    def all(self) -> Sequence[ObservationEvent]:
        return tuple(self._store.values())
