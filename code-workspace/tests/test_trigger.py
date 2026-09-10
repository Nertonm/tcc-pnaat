from pocs.poc01_trigger import CaptureRun, PresenceTrigger


def test_abre_janela_apos_debounce():
    t = PresenceTrigger(debounce=2)
    assert t.update(True) is None
    run = t.update(True)
    assert isinstance(run, CaptureRun) and len(run.views) == 3 and t.is_open is True


def test_pulso_isolado_nao_abre():
    t = PresenceTrigger(debounce=2)
    t.update(True); t.update(False)
    assert t.is_open is False


def test_fecha_apos_debounce_de_ausencia():
    t = PresenceTrigger(debounce=2)
    t.update(True); t.update(True)
    t.update(False); assert t.is_open is True
    t.update(False); assert t.is_open is False
