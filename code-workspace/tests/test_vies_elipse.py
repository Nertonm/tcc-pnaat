"""Regressao do vies do ajuste de elipse (ver docs/reference/medicao-vies-elipse-geometria.md).

Fixamos os numeros medidos para que qualquer mudanca no ajuste ou na amostragem apareca como
falha, em vez de passar despercebida. Teste de caracterizacao: a falha aqui e informacao.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_HARNESS = RAIZ / "scripts" / "medir_vies_elipse.py"


def _carregar_harness():
    spec = importlib.util.spec_from_file_location("medir_vies_elipse", CAMINHO_HARNESS)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def harness():
    return _carregar_harness()


def test_sem_ruido_e_contorno_completo_nao_tem_vies(harness):
    r = harness.medir(
        a=22.9, b=21.0, ang=30.0, sigma=0.0, arco=(0.0, 360.0),
        trials=20, seed=7, usar_ransac=False,
    )
    assert r["n"] == 20
    assert abs(r["bias_a_px"]) < 0.01
    assert abs(r["bias_b_px"]) < 0.01
    assert abs(r["bias_ang_deg"]) < 0.01


def test_vies_algebrico_segue_pequeno_com_ruido_de_borda(harness):
    """Viés medido: ~0,038 px em sigma=1 px e ~0,149 px em sigma=2 px (contorno completo)."""
    r1 = harness.medir(22.9, 21.0, 30.0, 1.0, (0.0, 360.0), 60, 1234, False)
    assert 0.0 < r1["bias_a_px"] < 0.1, r1
    r2 = harness.medir(22.9, 21.0, 30.0, 2.0, (0.0, 360.0), 60, 1234, False)
    assert r2["bias_a_px"] < 0.25, r2


def test_oclusao_degrada_o_angulo_muito_mais_que_o_vies(harness):
    """Caracterizacao do gargalo real: com 270 graus visiveis o erro angular explode."""
    completo = harness.medir(22.9, 21.0, 30.0, 1.0, (0.0, 360.0), 60, 1234, False)
    ocluido = harness.medir(22.9, 21.0, 30.0, 1.0, (0.0, 270.0), 60, 1234, False)
    assert completo["bias_ang_deg"] < 2.0
    assert ocluido["bias_ang_deg"] > 2.5, ocluido
    # o vies de semi-eixo continua pequeno nos dois casos -> oclusao nao e problema de semi-eixo
    assert abs(ocluido["bias_a_px"]) < 0.15


def test_ransac_nao_recupera_arco_ausente(harness):
    """RANSAC rejeita outlier; nao reconstroi contorno que nao existe."""
    sem = harness.medir(22.9, 21.0, 30.0, 1.0, (0.0, 270.0), 40, 99, False)
    com = harness.medir(22.9, 21.0, 30.0, 1.0, (0.0, 270.0), 40, 99, True)
    assert sem["bias_ang_deg"] > 2.5
    assert com["bias_ang_deg"] > 2.5


def test_escala_do_rig_atual_e_o_limite_fisico(harness):
    """1 px = 0,611 mm nas frames atuais -> 0,5 mm exige subpixel (0,82 px)."""
    escala = harness.ESCALA_PADRAO_MM_PX
    assert 0.55 < escala < 0.70
    assert 0.5 / escala < 1.0
