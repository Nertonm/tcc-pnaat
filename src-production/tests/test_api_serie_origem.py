"""A serie publicada no site tem de dizer DE ONDE veio o trigger.

Sem `trigger_n` e `origem_trigger` o operador nao consegue distinguir captura do sensor
fisico de teste de bancada — foi exatamente a confusao que travou a bancada hoje.
"""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace

import api


def _serie_valida(tmp_path: Path, nome: str, extra: dict) -> Path:
    destino = tmp_path / nome
    destino.mkdir()
    manifest = {"serie": nome, "fontes": [], **extra}
    (destino / "manifest.json").write_text(json.dumps(manifest))
    return destino


def test_series_publicam_trigger_n_e_origem(monkeypatch, tmp_path):
    _serie_valida(tmp_path, "20260915-183824-267",
                  {"trigger_n": 1, "origem_trigger": "fisico"})
    monkeypatch.setattr(api, "SERIES_DIR", tmp_path)
    series = api._series_locais(limite=5)
    assert series[0]["trigger_n"] == 1
    assert series[0]["origem_trigger"] == "fisico"


def test_serie_sem_manifesto_nao_inventa_origem(monkeypatch, tmp_path):
    (tmp_path / "20260915-180000-000").mkdir()
    monkeypatch.setattr(api, "SERIES_DIR", tmp_path)
    s = api._series_locais(limite=5)[0]
    assert s["trigger_n"] is None and s["origem_trigger"] is None
    assert s["completa"] is False
