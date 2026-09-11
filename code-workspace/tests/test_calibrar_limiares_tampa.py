"""Testes da calibracao de limiar (D-24): separacao, sobreposicao, amostra insuficiente, determinismo."""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import calibrar_limiares_tampa as cl  # noqa: E402


def _gauss(media, desvio, n, seed):
    r = random.Random(seed)
    return [media + r.gauss(0, desvio) for _ in range(n)]


def test_classes_separadas_dao_sensibilidade_e_especificidade_1():
    normal = _gauss(1.5, 0.3, 40, 1)
    defeito = _gauss(7.0, 0.5, 40, 2)
    r = cl.calibrar(defeito, normal, n_min=20)
    assert r["status"] == "CALIBRADO"
    assert r["sensibilidade"] == 1.0 and r["especificidade"] == 1.0
    assert r["youden"] == pytest.approx(1.0)
    assert r["sobreposicao"] is False and r["zona_cinzenta"] is None
    assert max(normal) < r["limiar"] < min(defeito)


def test_classes_sobrepostas_revelam_zona_cinzenta():
    normal = _gauss(3.0, 1.2, 60, 3)
    defeito = _gauss(4.5, 1.2, 60, 4)
    r = cl.calibrar(defeito, normal, n_min=20)
    assert r["status"] == "CALIBRADO"
    assert r["youden"] < 1.0
    assert r["sobreposicao"] is True and r["zona_cinzenta"] is not None
    assert r["zona_cinzenta"][0] < r["zona_cinzenta"][1]


def test_amostra_insuficiente_nao_emite_limiar():
    r = cl.calibrar([8.0] * 5, [1.0] * 5, n_min=20)
    assert r["status"] == "AMOSTRA_INSUFICIENTE"
    assert "limiar" not in r
    assert r["faltam"] == 30


def test_determinismo_mesma_entrada_mesmo_limiar():
    normal = _gauss(2.0, 1.0, 30, 5)
    defeito = _gauss(5.0, 1.0, 30, 6)
    a = cl.calibrar(defeito, normal, n_min=20)["limiar"]
    b = cl.calibrar(list(reversed(defeito)), list(reversed(normal)), n_min=20)["limiar"]
    assert a == b


def test_direcao_menor_e_pior_inverte_a_regra():
    normal = [1.0 + i * 0.01 for i in range(30)]
    defeito = [-5.0 - i * 0.01 for i in range(30)]
    r = cl.calibrar(defeito, normal, n_min=20, maior_e_pior=False)
    assert r["status"] == "CALIBRADO"
    assert "=>" in r["regra"] and "<=" in r["regra"]


def test_estatisticas_basicas():
    e = cl.estat([1.0, 2.0, 3.0, 4.0])
    assert e["n"] == 4 and e["min"] == 1.0 and e["max"] == 4.0
    assert e["media"] == pytest.approx(2.5)
    assert e["p2_5"] <= e["media"] <= e["p97_5"]


def _escreve(tmp_path: Path, normal, defeito):
    p = tmp_path / "m.csv"
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "classe", "tilt_graus"])
        for i, v in enumerate(normal):
            w.writerow(["n%02d" % i, "normal", "%.4f" % v])
        for i, v in enumerate(defeito):
            w.writerow(["d%02d" % i, "mal_rosqueada", "%.4f" % v])
    return p


def test_main_grava_json_com_procedencia(tmp_path, capsys):
    p = _escreve(tmp_path, _gauss(1.5, 0.3, 25, 7), _gauss(7.0, 0.4, 25, 8))
    saida = tmp_path / "limiares.json"
    rc = cl.main(["--medicoes", str(p), "--coluna", "tilt_graus", "--saida", str(saida)])
    capsys.readouterr()
    assert rc == 0 and saida.exists()
    d = json.loads(saida.read_text())
    assert d["medida"] == "tilt_graus" and d["n_defeito"] == 25 and d["n_normal"] == 25
    assert len(d["sha256_entrada"]) == 64 and d["procedencia"].startswith("calibracao empirica")


def test_main_retorna_2_e_nao_grava_com_amostra_insuficiente(tmp_path, capsys):
    p = _escreve(tmp_path, [1.0, 1.2, 1.4], [7.0, 7.2, 7.4])
    saida = tmp_path / "limiares.json"
    rc = cl.main(["--medicoes", str(p), "--coluna", "tilt_graus", "--saida", str(saida), "--n-min", "20"])
    capsys.readouterr()
    assert rc == 2
    assert not saida.exists()
