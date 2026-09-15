"""Testes da correcao do operador no registro (P1/D-30).

Regras que estes testes protegem:
  * a correcao e TRILHA: nao sobrescreve `item.status_final` (o que o classificador decidiu permanece);
  * quem decide o veredito e o operador, e o veredito tem vocabulario fechado (ok|defeito);
  * a decisao efetiva e a ULTIMA correcao, e o registro diz quem e quando;
  * correcao sem autor, sobre item inexistente ou repetindo o que ja vale e RECUSADA com motivo.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dominio import Classe, Dominio, Evento, Medida, Qualidade, Vista
from registro import EventoInvalido, Registro

T0 = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)


def _medida(vista, dominio, classe, conf=0.9):
    return Medida(vista=vista, dominio=dominio, classe=classe, confianca=conf, qualidade=Qualidade.OK)


@pytest.fixture()
def reg(tmp_path):
    r = Registro.abrir(tmp_path / "hub.db")
    r._cx.execute("INSERT INTO lote (lote_id, data_inicio) VALUES ('L1','2026-09-15')")
    # i-dfe: defeito; i-inc: inconclusivo (uma lateral so)
    r.registrar(Evento(item_id="i-dfe", capturado_em=T0, equipamento="rig", localizacao="bancada-b",
                       vistas=(Vista.TOPO,),
                       medidas=(_medida(Vista.LATERAL1, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
                                _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
                                _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
                                _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL)),
                       status=Classe.TAMPA_AUSENTE))
    r.registrar(Evento(item_id="i-inc", capturado_em=T0 + timedelta(seconds=5), equipamento="rig",
                       localizacao="bancada-b", vistas=(Vista.TOPO,),
                       medidas=(_medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),),
                       status=Classe.NORMAL))
    r._cx.execute("UPDATE item SET lote_id='L1'")
    r._cx.commit()
    yield r
    r.fechar()


def _status(reg, item_id):
    return reg._cx.execute("SELECT status_final FROM item WHERE item_id = ?", (item_id,)).fetchone()[0]


def test_o_registro_abre_em_wal(reg):
    """WAL e o que permite o rig gravar enquanto a API le/escreve (era o defeito do lock)."""
    assert reg._cx.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_correcao_grava_e_a_leitura_de_volta_confirma(reg):
    gravado = reg.corrigir("i-inc", "ok", "operador-1")
    assert gravado["decisao_original"] == "inconclusivo"
    assert gravado["decisao_corrigida"] == "ok"
    assert gravado["corrigido_por"] == "operador-1"
    assert gravado["timestamp"]
    vigente = reg.correcao_vigente("i-inc")
    assert vigente is not None and vigente["id"] == gravado["id"]
    assert vigente["decisao_corrigida"] == "ok"


def test_correcao_nao_sobrescreve_o_status_do_registro(reg):
    """O que o classificador decidiu permanece: corrigir nao e reescrever o fato."""
    antes = _status(reg, "i-dfe")
    reg.corrigir("i-dfe", "ok", "operador-2")
    assert _status(reg, "i-dfe") == antes == "defeito"
    assert reg.correcao_vigente("i-dfe")["decisao_corrigida"] == "ok"


def test_a_segunda_correcao_parte_da_primeira(reg):
    reg.corrigir("i-inc", "ok", "operador-1")
    segunda = reg.corrigir("i-inc", "defeito", "operador-2")
    assert segunda["decisao_original"] == "ok"
    assert reg.correcao_vigente("i-inc")["decisao_corrigida"] == "defeito"


def test_correcao_recusa_item_inexistente(reg):
    with pytest.raises(EventoInvalido, match="inexistente"):
        reg.corrigir("i-nao-existe", "ok", "operador-1")


def test_correcao_recusa_decisao_fora_do_vocabulario(reg):
    for ruim in ("tampa_ausente", "NORMAL", "", "inconclusivo"):
        with pytest.raises(EventoInvalido):
            reg.corrigir("i-inc", ruim, "operador-1")


def test_correcao_recusa_autor_ausente_ou_improvavel(reg):
    for ruim in ("", "   ", "a" * 65, "operador\x07com sino"):
        with pytest.raises(EventoInvalido, match="operador"):
            reg.corrigir("i-inc", "ok", ruim)


def test_espaco_em_excesso_no_nome_e_normalizado(reg):
    """Nome com espacos/quebras e normalizado na gravacao — nao e erro, e higiene de trilha."""
    gravado = reg.corrigir("i-inc", "ok", "  operador\n  da   bancada  ")
    assert gravado["corrigido_por"] == "operador da bancada"


def test_correcao_repetida_e_recusada(reg):
    reg.corrigir("i-inc", "ok", "operador-1")
    with pytest.raises(EventoInvalido, match="ja esta"):
        reg.corrigir("i-inc", "ok", "operador-2")
    # e corrigir de volta ao que o registro ja diz tambem nao acrescenta trilha
    with pytest.raises(EventoInvalido, match="ja esta"):
        reg.corrigir("i-dfe", "defeito", "operador-1")


def test_operador_e_normalizado_e_o_historico_preserva_a_ordem(reg):
    reg.corrigir("i-inc", "ok", "  operador   com espacos  ")
    assert reg.correcao_vigente("i-inc")["corrigido_por"] == "operador com espacos"
    reg.corrigir("i-inc", "defeito", "operador-2")
    historico = reg._cx.execute(
        "SELECT decisao_corrigida, corrigido_por FROM correcao_operador WHERE item_id='i-inc' ORDER BY id"
    ).fetchall()
    assert [(l[0], l[1]) for l in historico] == [("ok", "operador com espacos"), ("defeito", "operador-2")]
