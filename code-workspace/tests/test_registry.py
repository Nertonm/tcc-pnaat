from pnaat_pocs.events import DefectClass, ObservationEvent, ViewResult
from pnaat_pocs.poc05_registro import LocalRegistry


def _ev(eid):
    return ObservationEvent(
        event_id=eid, item_id="i", esteira_id="est-b", node_id="n01", location="l1",
        recorded_at="2026-09-09T10:00:00+00:00",
        views=(ViewResult("topo", DefectClass.NORMAL, 0.9),),
        fused=DefectClass.NORMAL, confidence=0.9,
    )


def test_upsert_idempotente_nao_duplica():
    r = LocalRegistry()
    assert r.upsert(_ev("a")) == "stored"
    assert r.upsert(_ev("a")) == "exists"
    assert r.size == 1


def test_reconcile_detecta_perda():
    r = LocalRegistry()
    r.upsert(_ev("a"))
    r.upsert(_ev("b"))
    assert r.reconcile({"a", "b", "c"}) == {"missing": ["c"], "stored": 2}


def test_query_por_defeito_e_esteira():
    r = LocalRegistry()
    r.upsert(_ev("a"))
    assert r.query(esteira_id="est-b") and not r.query(esteira_id="est-x")
