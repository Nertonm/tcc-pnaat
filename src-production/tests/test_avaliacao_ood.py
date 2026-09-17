"""Testes do harness OOD (MVTec); a métrica tem de responder e reprovar quando deve.

Cobrem: AUROC unitário (separação, empate, inversão), oracle no corpus sintético,
teste de mutação com o oracle invertido e detecção de modo (imagem vs mapa).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from avaliacao_ood import auroc, avalia, iou


def _mvtec_sintetico(base: Path) -> Path:
    for cat in ("bottle", "carpet"):
        for d in ("good", "broken_large"):
            (base / cat / "test" / d).mkdir(parents=True, exist_ok=True)
        (base / cat / "ground_truth" / "broken_large").mkdir(
            parents=True, exist_ok=True
        )
        for i in range(3):
            Image.new("RGB", (32, 32), "white").save(
                base / cat / "test" / "good" / f"{i:03d}.png"
            )
            Image.new("RGB", (32, 32), "gray").save(
                base / cat / "test" / "broken_large" / f"{i:03d}.png"
            )
            m = Image.new("L", (32, 32), 0)
            for x in range(4, 12):
                for y in range(4, 12):
                    m.putpixel((x, y), 255)
            m.save(base / cat / "ground_truth" / "broken_large" / f"{i:03d}_mask.png")
    return base


def test_auroc_unitario():
    assert auroc([1.0, 1.0], [0.0, 0.0]) == pytest.approx(1.0)
    assert auroc([0.5, 0.5], [0.5, 0.5]) == pytest.approx(0.5)
    assert auroc([0.0], [1.0]) == pytest.approx(0.0)


def test_iou_basico():
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == pytest.approx(1.0)
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == pytest.approx(0.0)


def test_iou_min_para_detectar(tmp_path):
    base = _mvtec_sintetico(tmp_path / "mvtec")
    caixa_gt = (4, 4, 12, 12)  # caixa da máscara sintética
    def scorer(caminho):
        return [] if "good" in caminho else [caixa_gt]
    rel = avalia(base, ("bottle",), scorer, "teste-caixa", 0.3, 4)
    assert rel["categorias"]["bottle"]["recall_defeito"] == pytest.approx(1.0)
    assert rel["categorias"]["bottle"]["fpr_good"] == pytest.approx(0.0)


def _avalia_baseline(base: Path, nome: str, seed: int = 7):
    from avaliacao_ood import _baseline_por_imagem

    def scorer(caminho):
        return _baseline_por_imagem(nome, seed, base, str(caminho))
    return avalia(base, ("bottle", "carpet"), scorer, nome, 0.3, 4)


def test_oracle_imagem_separa_perfeito(tmp_path):
    base = _mvtec_sintetico(tmp_path / "mvtec")
    rel = _avalia_baseline(base, "oracle")
    assert rel["categorias"]["bottle"]["auroc_imagem"] == pytest.approx(1.0)
    assert rel["categorias"]["carpet"]["auroc_imagem"] == pytest.approx(1.0)


def test_mutacao_oracle_invertido_zera(tmp_path):
    """Se a métrica fosse carimbo, o oracle invertido também daria 1.0."""
    base = _mvtec_sintetico(tmp_path / "mvtec")
    rel = _avalia_baseline(base, "oracle-invertido")
    assert rel["categorias"]["bottle"]["auroc_imagem"] == pytest.approx(0.0)


def test_baseline_aleatorio_nao_e_perfeito(tmp_path):
    base = _mvtec_sintetico(tmp_path / "mvtec")
    rel = _avalia_baseline(base, "aleatorio")
    valor = rel["categorias"]["bottle"]["auroc_imagem"]
    assert 0.0 < valor < 1.0


def test_modo_mapa_usa_mascara(tmp_path):
    base = _mvtec_sintetico(tmp_path / "mvtec")
    rel = _avalia_baseline(base, "oracle-mapa")
    assert rel["categorias"]["bottle"]["modo"] == "mapa"
    assert rel["categorias"]["bottle"]["auroc_pixel"] == pytest.approx(1.0)
    assert rel["categorias"]["bottle"]["mascaras_usadas"] == 3
