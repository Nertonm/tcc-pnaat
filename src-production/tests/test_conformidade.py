"""Testes da conformidade por dominio: uma asserção por regra da D-04/D-29.

Regra sem teste e promessa. As regras 1 a 6 do modulo estao todas aqui, incluindo os caminhos em que
a resposta "esperada" seria uma aprovacao; que e onde um bug passaria despercebido.
"""

from __future__ import annotations

import pytest
from conformidade import (
    MOTIVO_CHECK_AUSENTE,
    MOTIVO_CHECK_ESCALONADO,
    MOTIVO_CHECK_VIOLADO,
    MOTIVO_RIG_INCOMPLETO,
    ConfiguracaoDoRig,
    ErroDeConformidade,
    avaliar_conformidade,
)
from dominio import Classe, Dominio, Medida, Qualidade, Vista


def _m(vista, dominio, classe, conf=0.9, q=Qualidade.OK):
    return Medida(
        vista=vista, dominio=dominio, classe=classe, confianca=conf, qualidade=q
    )


def _par(dominio, c1, c2, q1=Qualidade.OK, q2=Qualidade.OK, conf1=0.9, conf2=0.9):
    return (
        _m(Vista.LATERAL1, dominio, c1, conf1, q1),
        _m(Vista.LATERAL2, dominio, c2, conf2, q2),
    )


TOPO_OK = _m(Vista.TOPO, Dominio.TAMPA, Classe.NORMAL)


def _completo(tampa, corpo, topo=TOPO_OK, conf_tampa=(0.9, 0.9), conf_corpo=(0.9, 0.9)):
    return (
        _par(Dominio.TAMPA, *tampa, conf1=conf_tampa[0], conf2=conf_tampa[1])
        + _par(Dominio.CORPO, *corpo, conf1=conf_corpo[0], conf2=conf_corpo[1])
        + (topo,)
    )


def _por_dominio(r):
    return {d.dominio: d for d in r.por_dominio}


# ---------------------------------------------------------------- regra 3: aprovacao


def test_aprovacao_exige_todos_os_dominios_normais_e_check_presente():
    r = avaliar_conformidade(
        _completo((Classe.NORMAL, Classe.NORMAL), (Classe.NORMAL, Classe.NORMAL))
    )
    assert r.status == "ok" and not r.discordancia_lateral and not r.check_escalonado
    assert {d.dominio: d.status for d in r.por_dominio} == {
        Dominio.TAMPA: "ok",
        Dominio.CORPO: "ok",
    }


def test_dominio_sem_medida_bloqueia_aprovacao():
    medidas = _par(Dominio.TAMPA, Classe.NORMAL, Classe.NORMAL) + (TOPO_OK,)
    r = avaliar_conformidade(medidas)
    assert r.status == "inconclusivo"
    assert _por_dominio(r)[Dominio.CORPO].motivos == ("dominio_nao_medido_corpo",)


def test_vista_unica_nao_aprova_o_dominio():
    medidas = (
        _m(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),
        _m(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
        _m(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
        TOPO_OK,
    )
    r = avaliar_conformidade(medidas)
    assert r.status == "inconclusivo"
    tampa = _por_dominio(r)[Dominio.TAMPA]
    assert (
        tampa.status == "inconclusivo" and "vistas_insuficientes_tampa" in tampa.motivos
    )


def test_qualidade_insuficiente_nao_vira_normal():
    r = avaliar_conformidade(
        _completo(
            (Classe.NORMAL, Classe.NORMAL),
            (Classe.NORMAL, Classe.NORMAL),
            topo=_m(Vista.TOPO, Dominio.TAMPA, Classe.NORMAL, q=Qualidade.INSUFICIENTE),
        )
    )
    assert r.status == "inconclusivo" and r.check_escalonado
    assert MOTIVO_CHECK_ESCALONADO in r.motivos


# ---------------------------------------------------------------- regra 2 e 4: defeito e discordancia


def test_defeito_em_uma_vista_reprova_e_marca_discordancia():
    r = avaliar_conformidade(
        _completo((Classe.DEFEITO_TAMPA, Classe.NORMAL), (Classe.NORMAL, Classe.NORMAL))
    )
    assert r.status == "defeito" and r.discordancia_lateral
    tampa = _por_dominio(r)[Dominio.TAMPA]
    assert tampa.classe is Classe.DEFEITO_TAMPA
    assert "classes_divergentes_tampa" in tampa.motivos
    assert tampa.origem == (
        (Vista.LATERAL1, Classe.DEFEITO_TAMPA),
        (Vista.LATERAL2, Classe.NORMAL),
    )


def test_defeito_nos_dois_dominios_reprova():
    r = avaliar_conformidade(
        _completo(
            (Classe.TAMPA_AUSENTE, Classe.TAMPA_AUSENTE),
            (Classe.DEFORMIDADE, Classe.DEFORMIDADE),
        )
    )
    assert r.status == "defeito"
    assert {d.dominio: d.classe for d in r.por_dominio} == {
        Dominio.TAMPA: Classe.TAMPA_AUSENTE,
        Dominio.CORPO: Classe.DEFORMIDADE,
    }


def test_precedencia_vence_a_confianca():
    """tampa_ausente precede defeito_tampa, mesmo com confianca menor."""
    r = avaliar_conformidade(
        _completo(
            (Classe.DEFEITO_TAMPA, Classe.TAMPA_AUSENTE),
            (Classe.NORMAL, Classe.NORMAL),
            conf_tampa=(0.99, 0.70),
        )
    )
    assert _por_dominio(r)[Dominio.TAMPA].classe is Classe.TAMPA_AUSENTE


def test_mesma_classe_com_confiancas_diferentes():
    r = avaliar_conformidade(
        _completo(
            (Classe.TAMPA_AUSENTE, Classe.TAMPA_AUSENTE),
            (Classe.NORMAL, Classe.NORMAL),
            conf_tampa=(0.60, 0.98),
        )
    )
    tampa = _por_dominio(r)[Dominio.TAMPA]
    assert tampa.classe is Classe.TAMPA_AUSENTE
    assert tampa.origem == (
        (Vista.LATERAL1, Classe.TAMPA_AUSENTE),
        (Vista.LATERAL2, Classe.TAMPA_AUSENTE),
    )
    assert not r.discordancia_lateral


def test_inconclusivo_em_uma_vista_nao_aprova():
    r = avaliar_conformidade(
        _completo((Classe.NORMAL, Classe.INCONCLUSIVO), (Classe.NORMAL, Classe.NORMAL))
    )
    assert r.status == "inconclusivo"
    assert "classes_divergentes_tampa" in _por_dominio(r)[Dominio.TAMPA].motivos


# ---------------------------------------------------------------- regra 5: o check nao decide


def test_topo_nao_cancela_defeito_das_laterais():
    medidas = _completo(
        (Classe.TAMPA_AUSENTE, Classe.TAMPA_AUSENTE), (Classe.NORMAL, Classe.NORMAL)
    )
    r = avaliar_conformidade(medidas, check_escalonado=False)
    assert r.status == "defeito"  # check ok nao salva o item


def test_check_escalonado_leva_a_inconclusivo_e_registra_motivo():
    r = avaliar_conformidade(
        _completo((Classe.NORMAL, Classe.NORMAL), (Classe.NORMAL, Classe.NORMAL)),
        check_escalonado=True,
    )
    assert r.status == "inconclusivo" and r.check_escalonado
    assert MOTIVO_CHECK_VIOLADO in r.motivos
    assert r.check_origem == ((Vista.TOPO, Classe.NORMAL),)


def test_check_obrigatorio_ausente_nao_aprova():
    medidas = _par(Dominio.TAMPA, Classe.NORMAL, Classe.NORMAL) + _par(
        Dominio.CORPO, Classe.NORMAL, Classe.NORMAL
    )
    r = avaliar_conformidade(medidas)
    assert r.status == "inconclusivo" and MOTIVO_CHECK_AUSENTE in r.motivos


# ---------------------------------------------------------------- regra 1: rig declarado


def test_vista_fora_do_rig_declarado_e_erro():
    medidas = _completo((Classe.NORMAL, Classe.NORMAL), (Classe.NORMAL, Classe.NORMAL))
    with pytest.raises(ErroDeConformidade):
        avaliar_conformidade(
            medidas + (_m(Vista.TOPO, Dominio.CORPO, Classe.NORMAL),),
            config=ConfiguracaoDoRig(
                vista_check=Vista.TOPO, vistas_decisorias=(Vista.LATERAL1,)
            ),
        )


def test_configuracao_menor_nao_aprova():
    """Rig reduzido (uma vista decisoria): o dado satisfaz a configuracao, mas NAO aprova (D-29)."""
    medidas = (
        _m(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),
        _m(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
        TOPO_OK,
    )
    r = avaliar_conformidade(
        medidas, config=ConfiguracaoDoRig(vistas_decisorias=(Vista.LATERAL1,))
    )
    assert r.status == "inconclusivo" and MOTIVO_RIG_INCOMPLETO in r.motivos


def test_dominio_nao_declarado_bloqueia():
    r = avaliar_conformidade(
        _completo((Classe.NORMAL, Classe.NORMAL), (Classe.NORMAL, Classe.NORMAL)),
        config=ConfiguracaoDoRig(dominios_medidos=frozenset({Dominio.TAMPA})),
    )
    assert r.status == "inconclusivo"
    assert _por_dominio(r)[Dominio.CORPO].motivos == ("dominio_nao_declarado_corpo",)
