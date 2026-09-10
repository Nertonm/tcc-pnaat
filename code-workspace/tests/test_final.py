from pocs.poc05_registro import LocalRegistry
from pocs.poc07_dashboard import bootstrap_events
from pocs.pocfinal import concluir_ensaio, executar_ensaio


def test_ensaio_registra_e_resume():
    resumo = executar_ensaio(list(bootstrap_events()))
    assert resumo["total"] == 3
    assert resumo["recorrencia"][0]["recorded_at"] >= resumo["recorrencia"][-1]["recorded_at"]


def test_concluir_ensaio_idempotente():
    r = LocalRegistry()
    evs = list(bootstrap_events())
    concluir_ensaio(r, evs)
    concluir_ensaio(r, evs)
    assert r.size == 3
