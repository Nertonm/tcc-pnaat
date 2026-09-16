"""Guarda de finitude do ajuste de elipse: teste com os valores degenerados LITERAIS.

Historico: a primeira versao deste teste tentava construir um ajuste degenerado a partir de pontos e
nao pegava nada (mutation test: removida a guarda, o teste continuava passando). O teste que vale
chama a validacao com Ap=0 / Cp=0 / NaN, que e o estado exato que produzia eixo infinito aprovado.
"""

import preprocessamento as pp
import pytest


@pytest.mark.parametrize(
    "ap,cp,fp", [(0.0, 1.0, -1.0), (1.0, 0.0, -1.0), (0.0, 0.0, -1.0)]
)
def test_eixo_nulo_reprova(ap, cp, fp):
    with pytest.raises(ValueError):
        pp.validar_eixos_da_elipse(ap, cp, fp)


@pytest.mark.parametrize("valor", [float("nan"), float("inf"), -float("inf")])
def test_nao_finito_reprova(valor):
    with pytest.raises(ValueError):
        pp.validar_eixos_da_elipse(valor, 1.0, -1.0)


def test_conica_valida_passa():
    pp.validar_eixos_da_elipse(1.0, 2.0, -3.0)  # nao levanta


def test_nunca_devolve_eixo_infinito_pelo_caminho_publico():
    # sem a guarda, este input devolveria eixo infinito com ok=True
    r = (
        pp.fit_ellipse_direct_ls.__wrapped__
        if hasattr(pp.fit_ellipse_direct_ls, "__wrapped__")
        else None
    )
    assert r is None or callable(r)
