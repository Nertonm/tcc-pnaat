"""PoC-07: consulta e recorrencia dos eventos para o dashboard."""
from __future__ import annotations

from collections import Counter

from ..events import DefectClass, Dominio, ObservationEvent, ViewResult
from ..poc04_fusao import ConfiguracaoFusao, fundir
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
            "fusao": e.fusao,
        }
        for e in events[:limite]
    ]


def bootstrap_events():
    """Eventos de exemplo, decididos pela MESMA fusao por dominio do PoC-04 (nada hardcoded)."""
    cfg = ConfiguracaoFusao(rig_id="bootstrap-2laterais-topo")

    def ev(event_id, item, esteira, views):
        fusao = fundir(views, cfg)
        return ObservationEvent(
            event_id=event_id, item_id=item, esteira_id=esteira, node_id="n01",
            location="esteira-b", recorded_at=f"2026-09-09T10:0{event_id[-1]}:00+00:00",
            views=views, fused=fusao.classe, confidence=fusao.confidence, fusao=fusao.como_dict(),
        )

    normal_tampa = [ViewResult("lateral1", Dominio.TAMPA, DefectClass.NORMAL, 0.9),
                    ViewResult("lateral2", Dominio.TAMPA, DefectClass.NORMAL, 0.9)]
    normal_corpo = [ViewResult("lateral1", Dominio.CORPO, DefectClass.NORMAL, 0.9),
                    ViewResult("lateral2", Dominio.CORPO, DefectClass.NORMAL, 0.9)]
    check = [ViewResult("topo", Dominio.DIMENSAO, DefectClass.NORMAL, 0.95)]

    # ev-1: tampa ausente em UMA lateral -> o defeito sobrevive a discordancia (nao ha maioria global)
    e1 = ev("ev-1", "i-01", "est-b",
            [ViewResult("lateral1", Dominio.TAMPA, DefectClass.TAMPA_AUSENTE, 0.91),
             ViewResult("lateral2", Dominio.TAMPA, DefectClass.NORMAL, 0.88),
             *normal_corpo, *check])
    # ev-2: item normal completo
    e2 = ev("ev-2", "i-02", "est-b", [*normal_tampa, *normal_corpo, *check])
    # ev-3: deformidade nos dois dominios laterais (corpo)
    e3 = ev("ev-3", "i-03", "est-c",
            [*normal_tampa,
             ViewResult("lateral1", Dominio.CORPO, DefectClass.DEFORMIDADE, 0.88),
             ViewResult("lateral2", Dominio.CORPO, DefectClass.DEFORMIDADE, 0.92),
             *check])
    return e1, e2, e3
