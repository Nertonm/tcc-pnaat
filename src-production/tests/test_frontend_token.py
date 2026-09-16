"""Ponte pytest -> node: o contrato de token do frontend entra no gate, nao fica so manual.

O canario real vive em `site/tests/test-token.cjs` (roda com `node`). Aqui so o disparamos e
exigimos exit 0; sem node instalado o teste e pulado com motivo declarado, nunca "passa".
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
CANARIO = RAIZ / "site" / "tests" / "test-token.cjs"
NODE = shutil.which("node")


@pytest.mark.skipif(
    NODE is None, reason="node ausente: canario de frontend nao roda aqui"
)
def test_token_do_frontend_vem_do_fragmento_e_vira_header():
    resultado = subprocess.run(
        [NODE, str(CANARIO)],
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
        timeout=60,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "PASS" in resultado.stdout
