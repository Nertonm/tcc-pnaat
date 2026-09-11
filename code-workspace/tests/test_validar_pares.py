"""Testes do gate validar_pares (guarda contra regressao do validador)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image, ImageDraw  # noqa: E402

VALID = Path(__file__).resolve().parents[1] / "scripts" / "validar_pares.py"


@pytest.fixture(scope="module")
def val():
    spec = importlib.util.spec_from_file_location("validar_pares", VALID)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validar_pares"] = mod
    spec.loader.exec_module(mod)
    return mod


def _pair(tmp: Path, nome="deformidade_frame_0000.png", box=(100, 100, 40, 40),
          extra=None, meta=None, size=(200, 200)):
    (tmp / "origem").mkdir(parents=True, exist_ok=True)
    (tmp / "pares").mkdir(parents=True, exist_ok=True)
    orig = Image.new("RGB", size, (30, 30, 30))
    d = ImageDraw.Draw(orig)
    d.rectangle([0, 0, 20, 20], fill=(200, 200, 200))
    orig.save(tmp / "origem" / "frame_0000.png")
    im = orig.copy()
    dd = ImageDraw.Draw(im)
    x, y, w, h = box
    dd.rectangle([x, y, x + w, y + h], fill=(0, 0, 0))
    if extra:
        dd.rectangle(list(extra), fill=(255, 0, 0))
    p = tmp / "pares" / nome
    im.save(p)
    m = {"classe": "deformidade", "regiao": list(box), "arquivo_saida": nome,
         "arquivo_original": "frame_0000.png", "descricao": "t"}
    if meta is not False and meta is not None:
        m.update(meta)
    if meta is not False:
        p.with_suffix(".json").write_text(json.dumps(m))
    return p


def test_par_valido_passa(val, tmp_path):
    p = _pair(tmp_path)
    r = val.validate_pair(p, tmp_path / "origem", 12, 0.002, schema_only=False)
    assert r["status"] == "PASS"


def test_mudanca_fora_do_bbox_falha(val, tmp_path):
    p = _pair(tmp_path, extra=(170, 170, 190, 190))
    r = val.validate_pair(p, tmp_path / "origem", 12, 0.002, schema_only=False)
    assert r["status"] == "FAIL"
    assert any("isolada" in x for x in r["problemas"])


def test_sem_arquivo_original_falha(val, tmp_path):
    p = _pair(tmp_path, meta={"arquivo_original": "nao_existe.png"})
    r = val.validate_pair(p, tmp_path / "origem", 12, 0.002, schema_only=False)
    assert r["status"] == "FAIL"
    assert any("arquivo_original" in x for x in r["problemas"])


def test_bbox_fora_da_imagem_falha(val, tmp_path):
    p = _pair(tmp_path, box=(180, 180, 60, 60))
    r = val.validate_pair(p, tmp_path / "origem", 12, 0.002, schema_only=False)
    assert r["status"] == "FAIL"
    assert any("fora da imagem" in x for x in r["problemas"])


def test_arquivo_saida_divergente_falha(val, tmp_path):
    p = _pair(tmp_path, meta={"arquivo_saida": "outro.png"})
    r = val.validate_pair(p, tmp_path / "origem", 12, 0.002, schema_only=False)
    assert r["status"] == "FAIL"


def test_json_ausente_falha(val, tmp_path):
    p = _pair(tmp_path, meta=False)
    r = val.validate_pair(p, tmp_path / "origem", 12, 0.002, schema_only=False)
    assert r["status"] == "FAIL"
    assert any("JSON ausente" in x for x in r["problemas"])