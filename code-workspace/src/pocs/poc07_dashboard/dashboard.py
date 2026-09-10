"""PoC-07: consulta e recorrencia dos eventos para o dashboard."""
from __future__ import annotations

from collections import Counter

from ..events import DefectClass, ObservationEvent
from ..poc05_registro import LocalRegistry


def summarize(registry: LocalRegistry) -> dict:
    events = registry.all()
    return {
        "total": len(events),
        "por_esteira": dict(Counter(e.esteira_id for e in events)),
        "por_defeito": dict(Counter(e.fused.value for e in events)),
        "com_falha": sum(1 for e in events if e.quality == "falha"),
    }


def recorrencia(registry: LocalRegistry, esteira_id=None, limite: int = 10) -> list[dict]:
    events = [e for e in registry.all() if (not esteira_id or e.esteira_id == esteira_id)]
    events.sort(key=lambda e: e.recorded_at, reverse=True)
    return [
        {
            "event_id": e.event_id, "item_id": e.item_id, "esteira_id": e.esteira_id,
            "defeito": e.fused.value, "recorded_at": e.recorded_at, "quality": e.quality,
        }
        for e in events[:limite]
    ]


def bootstrap_events():
    from ..events import DefectClass, ObservationEvent, ViewResult
    from ..poc04_fusao import fuse_views

    def ev(event_id, item, esteira, views):
        fused, conf = fuse_views(views)
        return ObservationEvent(
            event_id=event_id, item_id=item, esteira_id=esteira, node_id="n01",
            location="esteira-b", recorded_at=f"2026-09-09T10:0{item}:00+00:00",
            views=views, fused=fused, confidence=conf,
        )

    e1 = ev("ev-1", "i-01", "est-b", (ViewResult("topo", DefectClass.CAP_AUSENTE, 0.91),))
    e2 = ev("ev-2", "i-02", "est-b", (ViewResult("topo", DefectClass.NORMAL, 0.95), ViewResult("lat", DefectClass.NORMAL, 0.9)))
    e3 = ev("ev-3", "i-03", "est-c", (ViewResult("topo", DefectClass.DEFORMIDADE, 0.88), ViewResult("lat", DefectClass.DEFORMIDADE, 0.92)))
    return e1, e2, e3
