from pocs.poc05_registro import LocalRegistry
from pocs.poc07_dashboard import bootstrap_events, recorrencia, summarize


def test_summarize_agrega():
    r = LocalRegistry()
    for ev in bootstrap_events():
        r.upsert(ev)
    s = summarize(r)
    assert s["total"] == 3 and s["por_esteira"]["est-b"] == 2


def test_recorrencia_mais_recente_primeiro():
    r = LocalRegistry()
    for ev in bootstrap_events():
        r.upsert(ev)
    out = recorrencia(r)
    assert out[0]["recorded_at"] >= out[-1]["recorded_at"]
