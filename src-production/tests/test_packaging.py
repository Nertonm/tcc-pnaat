"""Contrato de empacotamento: o metadata tem de cobrir o que o runtime importa.

Historico: `py-modules` listava 13 nomes enquanto a arvore tinha 21 modulos de runtime
(classificador_artefato, ingerir_serie, mapeamento_rig, preprocessamento, scorers...). Uma
instalacao limpa esquecia justamente o caminho de inferencia, e a falta so aparecia em producao.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_py_modules_cobre_todos_os_modulos_da_raiz():
    dados = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declarados = set(dados["tool"]["setuptools"]["py-modules"])
    reais = {p.stem for p in ROOT.glob("*.py")}
    assert declarados == reais, {
        "faltando_no_metadata": sorted(reais - declarados),
        "declarado_sem_arquivo": sorted(declarados - reais),
    }


def test_servicos_entram_no_sdist():
    """O site e servido do checkout: o sdist precisa leva-lo, nao so os .py."""
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "recursive-include site *" in manifest


def test_site_tem_os_assets_de_entrada():
    """O site e servido direto do checkout: os assets de entrada precisam existir no fonte."""
    assert (ROOT / "site" / "index.html").is_file()
    assert (ROOT / "site" / "js" / "api.js").is_file()
    assert (ROOT / "site" / "css" / "style.css").is_file()
