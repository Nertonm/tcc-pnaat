"""Identidade do item: formato e geracao do `item_id` (DAT-01, RF-06, RF-01.2).

Decisao implementada (revisao de 2026-09-12): `item_id` = `lote-sequencia`, com a sequencia
monotonica **por lote** e o timestamp do trigger como atributo; nao dentro da chave. O motivo de
nao embutir data/hora no id: o schema ja guarda `timestamp_trigger` e a tendencia por hora consulta
ele; duplicar a data na chave quebraria ordenacao e ocuparia espaco sem ganho.

A sequencia NAO vive em memoria: ela e derivada do que ja esta gravado (`MAX(sequencia)` do lote).
Assim um reboot nao reinicia o contador; e reiniciar em 1 faria dois itens distintos receberem o
mesmo `item_id`, o que o criterio de reprovacao do RF-01.2 proibe explicitamente.

Contrato de uso (fail-closed): `proxima()` exige transacao aberta; `reservar()` abre a transacao,
cede o id e so confirma no fim do bloco com sucesso. Reservar e gravar tem de ser a mesma transacao,
senao dois escritores podem escolher o mesmo numero.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

#: formato canonico: <lote>-<sequencia de 6 digitos>
FORMATO = "{lote}-{sequencia:06d}"
RE_ITEM_ID = re.compile(r"^(?P<lote>[A-Za-z0-9_]{1,32})-(?P<sequencia>[0-9]{6})$")


class ErroDeIdentidade(Exception):
    """Identidade invalida ou uso indevido do gerador."""


def validar_lote(lote: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]{1,32}", lote or ""):
        raise ErroDeIdentidade(
            f"lote invalido: {lote!r} (use letras, digitos e _ ate 32)"
        )
    return lote


def montar(lote: str, sequencia: int) -> str:
    validar_lote(lote)
    if sequencia < 1:
        raise ErroDeIdentidade(f"sequencia comeca em 1, recebido {sequencia}")
    return FORMATO.format(lote=lote, sequencia=sequencia)


def decompor(item_id: str) -> tuple[str, int]:
    m = RE_ITEM_ID.fullmatch(item_id or "")
    if not m:
        raise ErroDeIdentidade(f"item_id fora do formato {FORMATO!r}: {item_id!r}")
    return m.group("lote"), int(m.group("sequencia"))


class SequenciaDeItens:
    """Gerador de identidade ancorado no banco: a sequencia sai do que ja foi gravado."""

    def __init__(self, conexao: sqlite3.Connection):
        self._cx = conexao

    def proxima(self, lote: str) -> str:
        """Proximo id do lote. Exige transacao aberta; reserva e gravacao sao a mesma unidade."""
        validar_lote(lote)
        if not self._cx.in_transaction:
            raise ErroDeIdentidade(
                "proxima() exige transacao aberta (use reservar() ou BEGIN IMMEDIATE): reservar o "
                "numero fora da transacao que grava o item permite dois itens com o mesmo item_id"
            )
        return self._proximo_do_lote(lote)

    @contextmanager
    def reservar(self, lote: str) -> Iterator[str]:
        """Cede o proximo id dentro de uma transacao. Confirma so se o bloco sair sem excecao."""
        validar_lote(lote)
        self._cx.execute("BEGIN IMMEDIATE")
        try:
            yield self._proximo_do_lote(lote)
            self._cx.commit()
        except BaseException:
            self._cx.rollback()
            raise

    # ---------------------------------------------------------------- interno

    def _proximo_do_lote(self, lote: str) -> str:
        vistas: list[int] = []
        for (item_id,) in self._cx.execute(
            "SELECT item_id FROM item WHERE item_id LIKE ?", (f"{lote}-%",)
        ):
            try:
                lote_lido, sequencia = decompor(item_id)
            except ErroDeIdentidade:
                continue  # id fora do formato nao conta para a sequencia
            if lote_lido == lote:
                vistas.append(sequencia)
        return montar(lote, (max(vistas) + 1) if vistas else 1)
