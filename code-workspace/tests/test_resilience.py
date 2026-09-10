from pnaat_pocs.events import DefectClass, ObservationEvent, ViewResult
from pnaat_pocs.resilience import retry_until_persist


def _ev(eid):
    return ObservationEvent(
        event_id=eid, item_id="i", esteira_id="est-b", node_id="n01", location="l1",
        recorded_at="2026-09-09T10:00:00+00:00",
        views=(ViewResult("topo", DefectClass.NORMAL, 0.9),),
        fused=DefectClass.NORMAL, confidence=0.9,
    )


def test_retry_conta_tentativas_ate_sucesso():
    calls = {"n": 0}

    def flaky(ev):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("indisponivel")
        return "stored"

    res = retry_until_persist(flaky, _ev("a"), max_retries=3)
    assert res["persisted"] is True
    assert res["attempts"] == 2
    assert res["alert"] is False
    assert res["quality"] == "ok"


def test_esgotamento_gera_alerta():
    def always_fail(ev):
        return "error"

    res = retry_until_persist(always_fail, _ev("a"), max_retries=2)
    assert res["persisted"] is False
    assert res["attempts"] == 3
    assert res["alert"] is True
    assert res["quality"] == "falha"
