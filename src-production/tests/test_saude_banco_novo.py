"""Banco novo nao pode derrubar /api/health (achado P2-1 do relatorio de auditoria).

O sintoma antigo: `SELECT COUNT(*) FROM item` num banco sem esquema levantava sqlite3.OperationalError
e a rota devolvia 503 `banco_indisponivel` -- o MESMO erro de um banco corrompido, escondendo a causa.
Agora a rota abre pelo caminho canonico (registro.py), que cria o esquema, e declara o estado.
"""

from pathlib import Path

from api import _rota_health


def _ctx(tmp_path: Path) -> dict:
    return {
        "db": tmp_path / "novo.db",
        "porta_real": 0,
        "evidencias": tmp_path,
        "site": tmp_path,
    }


def test_banco_novo_responde_com_esquema_criado(tmp_path):
    saude = _rota_health(_ctx(tmp_path))
    assert saude["banco"]["esquema"]["aberto"] is True, saude["banco"]["esquema"]
    assert saude["banco"]["itens"] == 0
    assert saude["banco"]["existe"] is True


def test_servico_do_banco_declara_esquema(tmp_path):
    saude = _rota_health(_ctx(tmp_path))
    banco = next(s for s in saude["servicos"] if s["nome"] == "Banco do registro")
    assert banco["estado"] == "ok", banco


def test_banco_corrompido_levanta_para_a_guarda_responder_503(tmp_path):
    """Banco ilegivel NAO pode virar 200: a rota levanta e a guarda da API responde 503.

    O que nao pode acontecer -- e era o achado -- e o banco NOVO cair no mesmo erro do corrompido.
    """
    import sqlite3

    import pytest

    ruim = tmp_path / "ruim.db"
    ruim.write_bytes(b"nao e sqlite")
    with pytest.raises(sqlite3.DatabaseError):
        _rota_health(_ctx(tmp_path) | {"db": ruim})
