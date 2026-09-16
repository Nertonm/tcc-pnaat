from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
TRABALHO = ROOT / "dataset" / "TRABALHO"
REQUIRED_FILES = (
    "monta_v0_detector.py",
    "treina_v0_detector.py",
    "atualiza_meta_lateral.py",
)
pytestmark = pytest.mark.skipif(
    not all((TRABALHO / nome).is_file() for nome in REQUIRED_FILES),
    reason="contrato v0 requer os scripts do dataset em dataset/TRABALHO",
)


def _montador():
    spec = importlib.util.spec_from_file_location(
        "monta_v0_detector", TRABALHO / "monta_v0_detector.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_montador_lateral_emite_vocabulario_canonico():
    module = _montador()
    assert module.CLASSES == ["normal", "tampa_ausente", "defeito_tampa"]
    assert all(
        label in module.CLASSES
        for mapping in module.FONTES.values()
        for label in mapping.values()
    )


def test_metadata_v0_declara_mesmas_classes_do_montador():
    esperado = "['normal','tampa_ausente','defeito_tampa']"
    for nome in ("treina_v0_detector.py", "atualiza_meta_lateral.py"):
        assert esperado in (TRABALHO / nome).read_text(), nome
