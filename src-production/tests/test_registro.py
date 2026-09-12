"""Testes do registro: idempotencia, conflito, regra D-04 e invariantes do proprio banco.

Cada teste falha se a regra for desfeita — inclusive quando a "resposta errada" seria gravar.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest

from dominio import Classe, Dominio, Evento, Medida, Papel, Qualidade, Vista
from registro import (ConflitoDeItem, EventoInvalido, Registro, estado_da_classe,
                      papel_da_linha, qualidade_registro, status_final)

AGORA = datetime(2026, 9, 12, 23, 40, tzinfo=timezone.utc)


def _medida(vista, dominio, classe, conf=0.95, qualidade=Qualidade.OK):
    return Medida(vista=vista, dominio=dominio, classe=classe, confianca=conf,
                  qualidade=qualidade)


def _evento(item_id="i-001", medidas=None, vistas=None, classe=Classe.NORMAL) -> Evento:
    if medidas is None:
        medidas = (
            _medida(Vista.LATERAL1, Dominio.TAMPA, classe),
            _medida(Vista.LATERAL2, Dominio.TAMPA, classe),
            _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
            _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
        )
    return Evento(item_id=item_id, capturado_em=AGORA, equipamento="pi5-rig", localizacao="bancada",
                  vistas=vistas or (Vista.TOPO,), medidas=medidas, status=classe)


@pytest.fixture()
def reg(tmp_path):
    r = Registro.abrir(tmp_path / "hub.db")
    yield r
    r.fechar()


# ---------------------------------------------------------------- mapeamentos

def test_estado_da_classe():
    assert estado_da_classe(Classe.NORMAL) == "ok"
    assert estado_da_classe(Classe.TAMPA_AUSENTE) == "defeito"
    assert estado_da_classe(Classe.DEFORMIDADE) == "defeito"
    assert estado_da_classe(Classe.INCONCLUSIVO) == "inconclusivo"


def test_papel_do_topo_nunca_decide():
    m = _medida(Vista.TOPO, Dominio.CORPO, Classe.NORMAL)
    assert papel_da_linha(Vista.TOPO, m) is Papel.AUXILIAR
    assert papel_da_linha(Vista.LATERAL1, m) is Papel.DECIDE
    inconclusiva = _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.INCONCLUSIVO, conf=0.0)
    assert papel_da_linha(Vista.LATERAL2, inconclusiva) is Papel.FALLBACK


def test_status_final_prioriza_defeito_e_protege_inconclusivo():
    assert status_final({Dominio.TAMPA: "ok", Dominio.CORPO: "ok"}, False) == "ok"
    assert status_final({Dominio.TAMPA: "defeito", Dominio.CORPO: "ok"}, False) == "defeito"
    assert status_final({Dominio.TAMPA: "ok", Dominio.CORPO: "inconclusivo"}, False) == "inconclusivo"
    assert status_final({Dominio.TAMPA: "ok", Dominio.CORPO: "ok"}, True) == "inconclusivo"


def test_qualidade_do_registro():
    assert qualidade_registro(2) == "completo"
    assert qualidade_registro(1) == "parcial_1_vista_faltante"
    assert qualidade_registro(0) == "evidencia_insuficiente"


# ---------------------------------------------------------------- esquema

def test_catalogo_de_referencia_aponta_para_as_laterais(reg):
    linhas = {r["codigo"]: r for r in reg._cx.execute(
        "SELECT codigo, classe, dominio, severidade, vista_esperada FROM taxonomia_defeito")}
    assert len(linhas) == 5
    for codigo in ("TAMPA_AUSENTE", "TAMPA_MAL_ROSQUEADA"):
        assert linhas[codigo]["vista_esperada"] == "lateral1,lateral2"   # D-23/D-30
        assert linhas[codigo]["dominio"] == "tampa"
    assert linhas["CORPO_DEFORMADO_SEVERO"]["classe"] == "deformidade"
    assert linhas["CORPO_DEFORMADO_SEVERO"]["severidade"] == "critico"
    assert linhas["CORPO_DEFORMADO_LEVE"]["severidade"] == "minor"
    assert linhas["ERRO_PROCESSAMENTO"]["classe"] is None               # categoria tecnica


def test_banco_recusa_topo_decidindo(reg):
    reg._cx.execute("INSERT INTO item (item_id, timestamp_trigger) VALUES ('x', 't')")
    with pytest.raises(sqlite3.IntegrityError):
        reg._cx.execute(
            "INSERT INTO inspecao_vista (item_id, vista, dominio, papel) VALUES ('x','topo','tampa','decide')")


def test_banco_recusa_decidir_sem_dominio(reg):
    reg._cx.execute("INSERT INTO item (item_id, timestamp_trigger) VALUES ('y', 't')")
    with pytest.raises(sqlite3.IntegrityError):
        reg._cx.execute(
            "INSERT INTO inspecao_vista (item_id, vista, papel) VALUES ('y','lateral1','decide')")


# ---------------------------------------------------------------- escrita

def test_round_trip_item_completo(reg):
    assert reg.registrar(_evento()) == "inserido"
    g = reg.ler("i-001")
    assert g.status_tampa == "ok" and g.status_corpo == "ok" and g.status_final == "ok"
    assert g.qualidade_registro == "completo"
    assert [l.papel for l in g.vistas if l.vista is Vista.TOPO] == [Papel.AUXILIAR]


def test_reenvio_da_mesma_evidencia_nao_duplica(reg):
    e = _evento()
    assert reg.registrar(e) == "inserido"
    assert reg.registrar(e) == "repetido"
    assert reg.contar() == 1
    assert reg._cx.execute("SELECT COUNT(*) FROM inspecao_vista").fetchone()[0] == 5


def test_evidencia_divergente_no_mesmo_item_da_conflito(reg):
    reg.registrar(_evento())
    outra = _evento(medidas=(
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
        _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
    ))
    with pytest.raises(ConflitoDeItem):
        reg.registrar(outra)
    assert reg.ler("i-001").status_tampa == "ok"      # nada foi sobrescrito
    assert reg.contar() == 1


def test_defeito_em_um_dominio_reprova_e_marca_discordancia(reg):
    medidas = (
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.TAMPA_MAL_ROSQUEADA),
        _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.NORMAL),
        _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
        _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
    )
    reg.registrar(_evento(medidas=medidas))
    g = reg.ler("i-001")
    assert g.status_tampa == "defeito" and g.status_final == "defeito"
    assert reg._cx.execute("SELECT discordancia_lateral FROM item WHERE item_id='i-001'").fetchone()[0] == 1


def test_vista_lateral_faltante_vira_inconclusivo(reg):
    medidas = (_medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),)
    reg.registrar(_evento(medidas=medidas))
    g = reg.ler("i-001")
    assert g.status_final == "inconclusivo"
    assert g.qualidade_registro == "parcial_1_vista_faltante"
    assert g.motivo_inconclusivo == "vista_lateral_ausente"


def test_evento_sem_identidade_e_recusado(reg):
    with pytest.raises(EventoInvalido):
        reg.registrar(Evento(item_id="  ", capturado_em=AGORA, equipamento="pi5", localizacao="b",
                             vistas=(Vista.LATERAL1,), medidas=(), status=Classe.NORMAL))


def test_vista_sem_medida_grava_inconclusivo_e_nao_aprova(reg):
    """Capturada e nao decidida nao e evidencia de nada (D-04)."""
    reg.registrar(Evento(item_id="i-002", capturado_em=AGORA, equipamento="pi5", localizacao="b",
                         vistas=(Vista.LATERAL1,), medidas=(), status=Classe.NORMAL))
    g = reg.ler("i-002")
    assert g.status_final == "inconclusivo"
    assert g.qualidade_registro == "evidencia_insuficiente"
    assert [(l.vista, l.papel, l.status) for l in g.vistas] == [(Vista.LATERAL1, Papel.AUXILIAR, "inconclusivo")]


def test_codigo_do_catalogo_e_gravado_quando_o_mapa_e_1_para_1(reg):
    medidas = (
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
        _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
    )
    reg.registrar(_evento(medidas=medidas))
    codigos = [r[0] for r in reg._cx.execute(
        "SELECT codigo_defeito FROM inspecao_vista WHERE item_id='i-001' AND vista LIKE 'lateral%'")]
    assert codigos == ["TAMPA_AUSENTE", "TAMPA_AUSENTE"]
