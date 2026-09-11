from pocs.events import DefectClass, Dominio, ObservationEvent, ViewResult
from pocs.poc06_resiliencia import retry_until_persist


def _ev(eid):
    return ObservationEvent(
        event_id=eid, item_id="i", esteira_id="est-b", node_id="n01", location="l1",
        recorded_at="2026-09-09T10:00:00+00:00",
        views=(ViewResult("topo", Dominio.DIMENSAO, DefectClass.NORMAL, 0.9),),
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
    assert res["persisted"] is True and res["attempts"] == 2 and res["alert"] is False


def test_esgotamento_gera_alerta():
    res = retry_until_persist(lambda ev: "error", _ev("a"), max_retries=2)
    assert res["persisted"] is False and res["alert"] is True and res["quality"] == "falha"
