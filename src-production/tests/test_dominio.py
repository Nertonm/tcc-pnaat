"""Invariantes do dominio e da regra de decisao (D-04, D-24, D-28, D-30).

Cada teste aqui falha se a regra for desfeita — inclusive os caminhos em que a resposta "esperada"
seria uma aprovacao.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from decisao import Decisor
from dominio import (Classe, Dominio, Evidencia, Medida, Origem, Papel, Qualidade, Vista)


# ---------------------------------------------------------------- vocabulario por dominio (D-28)

def test_classe_de_outro_dominio_e_recusada():
    with pytest.raises(ValueError):
        Medida(vista=Vista.LATERAL1, dominio=Dominio.TAMPA, classe=Classe.DEFORMIDADE, confianca=0.9)


def test_confianca_fora_do_intervalo_e_recusada():
    with pytest.raises(ValueError):
        Medida(vista=Vista.TOPO, dominio=Dominio.CORPO, classe=Classe.NORMAL, confianca=1.4)


def test_medida_inconclusiva_nao_e_conclusiva():
    m = Medida(vista=Vista.LATERAL1, dominio=Dominio.TAMPA, classe=Classe.INCONCLUSIVO, confianca=0.0)
    assert not m.conclusiva


# ---------------------------------------------------------------- evidencia (D-24)

def test_evidencia_sem_fonte_e_provisoria():
    e = Evidencia(grandeza="tilt_graus", valor=2.0, unidade="grau", origem=Origem.GEOMETRIA,
                  papel=Papel.AUXILIAR, metodo="elipse-ls-v1")
    assert e.provisorio() is True
    com_fonte = Evidencia(grandeza="arco_visivel_graus", valor=300.0, unidade="grau",
                          origem=Origem.GEOMETRIA, papel=Papel.AUXILIAR, metodo="elipse-ls-v1",
                          fonte="docs/reference/medicao-vies-elipse-geometria.md:12")
    assert com_fonte.provisorio() is False


# ---------------------------------------------------------------- decisao (D-30)

class _ClassificadorFixo:
    identificacao = "fake"

    def __init__(self, medida):
        self._medida = medida

    def prever(self, recorte, dominio):
        return self._medida


class _GeometriaFalsa:
    identificacao = "geo-fake"

    def __init__(self, valor=3.0):
        self._valor = valor

    def medir(self, recorte):
        return (Evidencia(grandeza="tilt_graus", valor=self._valor, unidade="grau",
                          origem=Origem.GEOMETRIA, papel=Papel.AUXILIAR, metodo="fake"),)


def test_classificador_conclusivo_decide_e_nao_escala():
    medida = Medida(vista=Vista.LATERAL1, dominio=Dominio.TAMPA, classe=Classe.NORMAL, confianca=0.97)
    r = Decisor(_ClassificadorFixo(medida), _GeometriaFalsa()).decidir(None, Dominio.TAMPA, Vista.LATERAL1)
    assert r.papel is Papel.DECIDE and r.classe is Classe.NORMAL
    assert not r.escalona and r.aprovado
    assert any(e.papel is Papel.AUXILIAR for e in r.evidencias)      # geometria fica como rastro


def test_fallback_sem_classificador_nunca_aprova():
    r = Decisor(_ClassificadorFixo(None), _GeometriaFalsa(valor=0.1)).decidir(
        None, Dominio.TAMPA, Vista.LATERAL1)
    assert r.papel is Papel.FALLBACK
    assert r.classe is Classe.INCONCLUSIVO and r.escalona and not r.aprovado
    assert r.motivo == "classificador_indisponivel"


def test_classificador_inconclusivo_vira_fallback_e_escala():
    medida = Medida(vista=Vista.LATERAL1, dominio=Dominio.TAMPA, classe=Classe.INCONCLUSIVO,
                    confianca=0.0, qualidade=Qualidade.INSUFICIENTE)
    r = Decisor(_ClassificadorFixo(medida), _GeometriaFalsa()).decidir(None, Dominio.TAMPA, Vista.LATERAL1)
    assert r.papel is Papel.FALLBACK and r.escalona and not r.aprovado


def test_evento_exige_fuso_e_vista():
    from dominio import Evento
    with pytest.raises(ValueError):
        Evento(item_id="i-1", capturado_em=datetime(2026, 9, 12), equipamento="pi5",
               localizacao="bancada", vistas=(Vista.LATERAL1,), medidas=(), status=Classe.NORMAL)
    with pytest.raises(ValueError):
        Evento(item_id="i-1", capturado_em=datetime.now().astimezone(), equipamento="pi5",
               localizacao="bancada", vistas=(), medidas=(), status=Classe.NORMAL)
