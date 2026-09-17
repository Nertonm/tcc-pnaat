"""--pacote do exportador: read-back do pacote gravado, sem exportar."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1] / "treino"
sys.path.insert(0, str(PIPELINE))

import pacote_entrega  # noqa: E402

CLASSES = ["normal", "tampa_ausente"]


def _insumos(tmp_path: Path):
    peso = tmp_path / "v9b-lateral.pt"
    peso.write_bytes(b"peso-do-pacote")
    sha = hashlib.sha256(peso.read_bytes()).hexdigest()
    contrato = tmp_path / "preprocessamento.json"
    contrato.write_text(json.dumps({
        "nome": "pnaat-preprocessamento", "versao": 1, "letterbox": True,
        "classes": CLASSES, "imgsz_treino": 480,
        "roi_por_camera": {"csi": {"x": .1, "y": .0, "w": .5, "h": .6},
                           "usb": {"x": .0, "y": .0, "w": .6, "h": .5}},
        "rotacao_graus": {"csi": 0, "usb": 90},
        "limiares_por_imgsz": {"480": {"calibrado": True, "fonte": "calibracao-val.json",
                                       "normal": .4, "tampa_ausente": .2}},
        "modelo": {"arquivo": peso.name, "sha256": sha},
    }))
    metadados = tmp_path / "model-meta.json"
    metadados.write_text(json.dumps({
        "peso_sha256": sha, "classes": CLASSES, "args": {"imgsz": 480},
        "metricas_val": {"metrics/mAP50(B)": .9},
    }))
    return peso, contrato, metadados, tmp_path / "pacote"


def test_conferir_pacote_gravado_e_tamper(tmp_path, capsys):
    peso, contrato, metadados, saida = _insumos(tmp_path)
    pacote_entrega.export_bundle(peso, contrato, metadados, saida, apply=True)
    assert pacote_entrega.main(["--pacote", str(saida)]) == 0
    assert "pacote confere" in capsys.readouterr().out

    (saida / peso.name).write_bytes(b"peso-trocado")
    assert pacote_entrega.main(["--pacote", str(saida)]) == 2
    assert "BLOQUEADO" in capsys.readouterr().err


def test_exportar_sem_insumos_e_erro(tmp_path):
    import pytest

    with pytest.raises(SystemExit):
        pacote_entrega.main(["--saida", str(tmp_path / "x")])
