"""Contrato do ACK de baud: valor corrompido NAO pode trocar a taxa do host.

Caso real (2026-09-15 18:45): bytes se perderam na transicao de taxa e a linha chegou como
`BAUD_ACK ok=1 de=921600 para=46TASKS_READY`. O regex `para=(\\d+)` casou "46" e o host
trocou o UART para 46 baud; enlace morto (frames_ok=0, camera=desconhecido) sem nenhum
erro visivel no painel. O contrato do firmware e uma taxa de 4 a 7 digitos.

O alvo aqui e o PARSER, nao o enlace: `serial` entra como stub para o modulo carregar em
qualquer runner (a suite roda onde pyserial nao esta instalado).
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path

PONTE = (
    Path(__file__).resolve().parents[1]
    / "firmware"
    / "esp32cam-test"
    / "esp32cam_site.py"
)


def _stub_serial() -> None:
    if "serial" in sys.modules:
        return
    falso = types.ModuleType("serial")

    class Serial:
        def __init__(self, *a, **k) -> None:
            pass

    falso.Serial = Serial
    falso.SerialException = OSError
    sys.modules["serial"] = falso


def _carrega():
    sentinel = object()
    anterior = sys.modules.get("serial", sentinel)
    _stub_serial()
    try:
        loader = importlib.machinery.SourceFileLoader("ponte_baud", str(PONTE))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        modulo = importlib.util.module_from_spec(spec)
        loader.exec_module(modulo)
        return modulo
    finally:
        if anterior is sentinel:
            sys.modules.pop("serial", None)
        else:
            sys.modules["serial"] = anterior


def test_ack_normal_casa_e_extrai_a_taxa():
    m = _carrega()
    r = m.BAUD_ACK_RE.search("BAUD_ACK ok=1 de=921600 para=460800")
    assert r is not None and r.group(2) == "460800"


def test_ack_corrompido_nao_casa():
    """A linha que derrubou o enlace: se casar, o host troca para 46 baud."""
    m = _carrega()
    assert m.BAUD_ACK_RE.search("BAUD_ACK ok=1 de=921600 para=46TASKS_READY") is None


def test_ack_truncado_nao_casa():
    m = _carrega()
    assert m.BAUD_ACK_RE.search("BAUD_ACK ok=1 de=921600 para=46") is None


def test_baud_ativo_normal_casa_e_truncado_nao():
    m = _carrega()
    assert m.BAUD_ATIVO_RE.search("BAUD_ATIVO 460800") is not None
    assert m.BAUD_ATIVO_RE.search("BAUD_ATIVO 46") is None
