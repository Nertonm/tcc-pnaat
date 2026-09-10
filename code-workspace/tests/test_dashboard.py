from pnaat_pocs.dashboard import bootstrap_events, recorrencia, summarize
from pnaat_pocs.events import DefectClass
from pnaat_pocs.registry import LocalRegistry


def test_summarize_agrega_por_esteira_defeito():
    r = LocalRegistry()
    for ev in bootstrap_events():
        r.upsert(ev)
    s = summarize(r)
    assert s["total"] == 3
    assert s["por_esteira"]["est-b"] == 2
    assert DefectClass.DEFORMIDADE.value in s["por_defeito"]


def test_recorrencia_mais_recente_primeiro():
    r = LocalRegistry()
    for ev in bootstrap_events():
        r.upsert(ev)
    out = recorrencia(r)
    assert out[0]["recorded_at"] >= out[-1]["recorded_at"]
