"""--conferir do gerador de contrato: le o arquivo e reprova o que o consumidor recusaria."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "treino"))

import gera_contrato_preproc as gerador  # noqa: E402


def _insumos(tmp_path: Path) -> dict:
    peso = tmp_path / "v9b-lateral.pt"
    peso.write_bytes(b"peso-de-teste")
    sha = hashlib.sha256(peso.read_bytes()).hexdigest()
    meta = tmp_path / "model-meta.json"
    meta.write_text(json.dumps({"classes": ["normal", "tampa_ausente"], "args": {"imgsz": 480}}))
    roi = tmp_path / "roi.json"
    roi.write_text(json.dumps({"cameras": {
        "csi": {"roi_normalizada": {"x": .1, "y": .2, "w": .5, "h": .6}},
        "usb": {"roi_normalizada": {"x": .0, "y": .1, "w": .7, "h": .8}},
    }}))
    calibracao = tmp_path / "calibracao-val.json"
    calibracao.write_text(json.dumps({
        "imgsz": 480, "peso": str(peso),
        "limiares_escolhidos_na_val": {
            "normal": {"conf": .4, "f1_val": .9},
            "tampa_ausente": {"conf": .2, "f1_val": .8},
        },
    }))
    return {"peso": peso, "meta": meta, "roi": roi, "calibracao": calibracao, "sha": sha}


def _contrato(tmp_path: Path) -> Path:
    insumos = _insumos(tmp_path)
    saida = tmp_path / "preprocessamento.json"
    codigo = gerador.main([
        "--peso", str(insumos["peso"]), "--metadados", str(insumos["meta"]),
        "--roi", str(insumos["roi"]), "--calibracao", str(insumos["calibracao"]),
        "--vistas", "csi=lateral1,usb=lateral2", "--rotacao", "csi=0,usb=90",
        "--saida", str(saida),
    ])
    assert codigo == 0, "geracao deveria passar"
    assert saida.is_file()
    assert json.loads(saida.read_text())["modelo"]["sha256"] == insumos["sha"]
    return saida


def test_conferir_aceita_contrato_gerado(tmp_path, capsys):
    saida = _contrato(tmp_path)
    assert gerador.main(["--conferir", "--saida", str(saida)]) == 0
    texto = capsys.readouterr().out
    assert "contrato confere" in texto and "imgsz: 480" in texto


def test_conferir_recusa_roi_alterada_a_mao(tmp_path, capsys):
    """ROI e campo da impressao digital: mexer sem recalcular tem de ser recusado."""
    saida = _contrato(tmp_path)
    dado = json.loads(saida.read_text())
    dado["roi_por_camera"]["csi"]["w"] = 0.9
    saida.write_text(json.dumps(dado))
    assert gerador.main(["--conferir", "--saida", str(saida)]) == 2
    assert "BLOQUEADO" in capsys.readouterr().err


def test_conferir_recusa_limiar_sem_fonte(tmp_path, capsys):
    """Limiar dito calibrado sem fonte e recusado (guarda estrutural que existe hoje).

    NOTA de limite declarado: o VALOR do limiar nao entra na impressao digital, entao editar o
    numero mantendo `fonte` e `calibrado` passa. Esta lacuna esta registrada no README do produto.
    """
    saida = _contrato(tmp_path)
    dado = json.loads(saida.read_text())
    dado["limiares_por_imgsz"]["480"].pop("fonte")
    saida.write_text(json.dumps(dado))
    assert gerador.main(["--conferir", "--saida", str(saida)]) == 2
    assert "BLOQUEADO" in capsys.readouterr().err


def test_gerar_sem_calibracao_e_recusado_pelo_consumidor(tmp_path, capsys):
    """Limiar provisorio nao vira contrato: o validador do consumidor recusa na geracao."""
    saida = _insumos(tmp_path)
    assert gerador.main([
        "--peso", str(saida["peso"]), "--metadados", str(saida["meta"]),
        "--roi", str(saida["roi"]), "--vistas", "csi=lateral1,usb=lateral2",
        "--rotacao", "csi=0,usb=90", "--saida", str(tmp_path / "sem-calibracao.json"),
    ]) == 2
    assert "calibrado" in capsys.readouterr().err


def test_gerar_sem_insumos_obrigatorios_e_erro(tmp_path):
    with pytest.raises(SystemExit):
        gerador.main(["--saida", str(tmp_path / "x.json")])
