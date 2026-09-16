"""Testes da identidade: formato, unicidade entre reinicios e atomicidade da reserva.

O teste central aqui e o do reboot: se a sequencia morasse em memoria, o segundo processo comecaria
em 1 e dois itens distintos receberiam o mesmo `item_id`; o que o RF-01.2 proibe.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from dominio import Classe, Dominio, Evento, Medida, Vista
from identidade import (
    FORMATO,
    ErroDeIdentidade,
    SequenciaDeItens,
    decompor,
    montar,
    validar_lote,
)
from registro import Registro

AGORA = datetime(2026, 9, 13, 2, 0, tzinfo=timezone.utc)


def _evento(item_id: str) -> Evento:
    return Evento(
        item_id=item_id,
        capturado_em=AGORA,
        equipamento="pi5-rig",
        localizacao="bancada-b",
        vistas=(Vista.TOPO,),
        status=Classe.NORMAL,
        medidas=(
            Medida(
                vista=Vista.LATERAL1,
                dominio=Dominio.TAMPA,
                classe=Classe.NORMAL,
                confianca=0.9,
            ),
            Medida(
                vista=Vista.LATERAL2,
                dominio=Dominio.TAMPA,
                classe=Classe.NORMAL,
                confianca=0.9,
            ),
        ),
    )


# ---------------------------------------------------------------- formato


def test_formato_e_ida_e_volta():
    assert montar("L1", 123) == "L1-000123"
    assert decompor("L1-000123") == ("L1", 123)
    assert FORMATO.format(lote="TURNO_A", sequencia=1) == "TURNO_A-000001"


def test_lote_invalido_e_recusado():
    for ruim in ("", "com espaco", "com-hifen", "acentuação", "x" * 33):
        with pytest.raises(ErroDeIdentidade):
            validar_lote(ruim)


def test_item_id_fora_do_formato_e_recusado():
    for ruim in ("L1-1", "L1-0000001", "000123", "L1-abcdef", "l1_000123"):
        with pytest.raises(ErroDeIdentidade):
            decompor(ruim)


def test_sequencia_comeca_em_1():
    with pytest.raises(ErroDeIdentidade):
        montar("L1", 0)


# ---------------------------------------------------------------- geracao ancorada no banco


def test_proxima_exige_transacao(tmp_path):
    reg = Registro.abrir(tmp_path / "hub.db")
    seq = SequenciaDeItens(reg._cx)
    with pytest.raises(ErroDeIdentidade):
        seq.proxima("L1")  # fora de transacao nao reserva
    reg.fechar()


def test_primeiro_item_do_lote_e_o_um(tmp_path):
    reg = Registro.abrir(tmp_path / "hub.db")
    with SequenciaDeItens(reg._cx).reservar("L1") as item_id:
        assert item_id == "L1-000001"
        reg.registrar(_evento(item_id))
    with SequenciaDeItens(reg._cx).reservar("L1") as item_id:
        assert item_id == "L1-000002"
        reg.registrar(_evento(item_id))
    assert reg.contar() == 2
    reg.fechar()


def test_reboot_nao_reinicia_a_sequencia(tmp_path):
    """O caso que a revisao apontou: contador em memoria faria colisao depois de reiniciar."""
    cam = tmp_path / "hub.db"
    reg = Registro.abrir(cam)
    with SequenciaDeItens(reg._cx).reservar("L1") as item_id:
        reg.registrar(_evento(item_id))
    reg.fechar()  # "processo morreu"

    reg2 = Registro.abrir(cam)  # "processo subiu de novo"
    with SequenciaDeItens(reg2._cx).reservar("L1") as item_id:
        assert item_id == "L1-000002"  # nao volta para 1
        reg2.registrar(_evento(item_id))
    assert sorted(
        r["item_id"] for r in reg2._cx.execute("SELECT item_id FROM item")
    ) == ["L1-000001", "L1-000002"]
    reg2.fechar()


def test_lotes_diferentes_tem_sequencias_independentes(tmp_path):
    reg = Registro.abrir(tmp_path / "hub.db")
    seq = SequenciaDeItens(reg._cx)
    with seq.reservar("L1") as i1:
        reg.registrar(_evento(i1))
    with seq.reservar("L2") as i2:
        reg.registrar(_evento(i2))
    assert (i1, i2) == ("L1-000001", "L2-000001")
    reg.fechar()


def test_falha_dentro_da_reserva_nao_grava_e_libera_o_numero(tmp_path):
    reg = Registro.abrir(tmp_path / "hub.db")
    seq = SequenciaDeItens(reg._cx)
    with pytest.raises(RuntimeError), seq.reservar("L1") as item_id:
        assert item_id == "L1-000001"
        raise RuntimeError("falhou no meio da execucao")
    assert reg.contar() == 0
    with seq.reservar("L1") as item_id:  # o numero pode ser reusado: nada foi gravado
        assert item_id == "L1-000001"
        reg.registrar(_evento(item_id))
    reg.fechar()


def test_id_fora_do_formato_nao_quebra_a_sequencia(tmp_path):
    reg = Registro.abrir(tmp_path / "hub.db")
    reg.registrar(_evento("registro-antigo-sem-formato"))
    with SequenciaDeItens(reg._cx).reservar("L1") as item_id:
        assert item_id == "L1-000001"
    reg.fechar()
