import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from presence import CaptureRun, PresenceTrigger, present_from_sensor


def test_abre_janela_apos_debounce():
    t = PresenceTrigger(views=("topo", "lateral1", "lateral2"), stable_reads=2, miss_reads=2)
    assert t.update(True) is None
    run = t.update(True)
    assert isinstance(run, CaptureRun)
    assert len(run.views) == 3          # multi-view
    assert t.is_open is True


def test_pulso_isolado_nao_abre():
    t = PresenceTrigger(stable_reads=2)
    t.update(True)
    t.update(False)                     # ruido: volta a 0 antes de estabilizar
    assert t.is_open is False


def test_fecha_apos_debounce_de_ausencia():
    t = PresenceTrigger(stable_reads=2, miss_reads=2)
    t.update(True)
    t.update(True)                      # abre
    t.update(False)
    assert t.is_open is True            # ainda aberto (1 miss)
    t.update(False)                     # estabiliza ausencia
    assert t.is_open is False


def test_present_from_sensor_active_low():
    assert present_from_sensor(0) is True    # LOW = objeto presente
    assert present_from_sensor(1) is False   # HIGH = ausente
    assert present_from_sensor(1, active_low=False) is True


def test_present_from_sensor_nivel_invalido():
    import pytest
    with pytest.raises(ValueError):
        present_from_sensor(2)