"""Testes da avaliacao da PoC-02: IC (Wilson/Clopper-Pearson), recall/FP por classe, fontes separadas e anotacao.

Cada teste assere um numero calculado a mao, nao o que o codigo devolve.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import avaliar_poc02 as av  # noqa: E402


# ---------------------------------------------------------------- IC

def test_wilson_lb_quando_k_igual_n():
    # forma fechada: k=n -> LB = n/(n+z^2)
    n = 10
    esperado = n / (n + av.Z95 ** 2)
    assert av.wilson(n, n, "lb") == pytest.approx(esperado, rel=1e-9)
    assert av.wilson(n, n, "lb") == pytest.approx(0.7225, abs=5e-4)


def test_wilson_ub_quando_k_zero():
    n = 20
    esperado = (av.Z95 ** 2) / (n + av.Z95 ** 2)
    assert av.wilson(0, n, "ub") == pytest.approx(esperado, rel=1e-9)


def test_wilson_sem_itens():
    assert av.wilson(0, 0, "lb") == 0.0
    assert av.wilson(5, 0, "ub") == 0.0


def test_clopper_pearson_k_igual_n():
    # k=n -> LB = (alpha/2)^(1/n); para n=73: 0.025^(1/73) = 0.95072
    cp = av.clopper_pearson(73, 73, "lb")
    if cp is None:
        pytest.skip("scipy indisponivel")
    assert cp == pytest.approx(0.95072, abs=5e-5)


# ---------------------------------------------------------------- metricas

def _fixture(tmp_path: Path):
    """proprio: ausente 73/73 (LB95 0,9507), mal_rosqueada 55/56, normal 5/6; publico: 4/5."""
    itens = []
    preds = {}
    for i in range(6):
        iid = "n%02d" % i
        itens.append((iid, "proprio", "normal", "/tmp/x.jpg"))
        preds[iid] = {"classe": "normal" if i < 5 else "tampa_ausente", "confianca": 0.9,
                      "medidas": {"tilt_graus": 1.2, "arco_graus": 352.0}, "motivos": []}
    for i in range(73):
        iid = "a%02d" % i
        itens.append((iid, "proprio", "tampa_ausente", "/tmp/x.jpg"))
        preds[iid] = {"classe": "tampa_ausente", "confianca": 0.95,
                      "medidas": {"arco_graus": 351.0}, "motivos": []}
    for i in range(56):
        iid = "m%02d" % i
        itens.append((iid, "proprio", "tampa_mal_rosqueada", "/tmp/x.jpg"))
        preds[iid] = {"classe": "tampa_mal_rosqueada" if i < 55 else "inconclusivo", "confianca": 0.8,
                      "medidas": {"tilt_graus": 6.5}, "motivos": ["angulo_zona_cinzenta"] if i >= 55 else []}
    for i in range(5):                       # outra fonte: nunca agregada
        iid = "p%02d" % i
        itens.append((iid, "publico:ds_x", "tampa_ausente", "/tmp/x.jpg"))
        preds[iid] = {"classe": "tampa_ausente" if i < 4 else "inconclusivo", "confianca": 0.7,
                      "medidas": {}, "motivos": []}

    man = tmp_path / "manifest.csv"
    man.write_text("item_id,fonte,classe_verdade,arquivo\n" +
                   "\n".join("%s,%s,%s,%s" % it for it in itens) + "\n")
    pr = tmp_path / "pred.json"
    pr.write_text(json.dumps(preds))
    return av.carregar(man, pr)


def test_recall_e_fp_por_classe(tmp_path):
    itens = _fixture(tmp_path)
    b = av.bloco(itens, "proprio")
    assert b["n"] == 135

    aus = b["por_classe"]["tampa_ausente"]
    assert aus["n"] == 73 and aus["acertos"] == 73
    assert aus["recall"] == pytest.approx(1.0)
    assert aus["recall_lb95"] == pytest.approx(0.9507, abs=0.001)
    assert aus["negativos"] == 62 and aus["fp"] == 1          # o normal previsto como ausente
    assert aus["fp_taxa"] == pytest.approx(1 / 62)

    mal = b["por_classe"]["tampa_mal_rosqueada"]
    assert mal["n"] == 56 and mal["acertos"] == 55
    assert mal["recall"] == pytest.approx(55 / 56)
    assert mal["recall_lb95"] == pytest.approx(0.9056, abs=0.002)
    assert mal["fp"] == 0

    nor = b["por_classe"]["normal"]
    assert nor["n"] == 6 and nor["acertos"] == 5


def test_inconclusivo_e_classe_propria_e_conta_como_erro(tmp_path):
    itens = _fixture(tmp_path)
    b = av.bloco(itens, "proprio")
    assert b["inconclusivo_n"] == 1
    assert b["inconclusivo_taxa"] == pytest.approx(1 / 135)
    assert b["por_classe"]["tampa_mal_rosqueada"]["acertos"] == 55   # o inconclusivo NAO conta acerto
    assert b["escalonados"] == 1


def test_fontes_nao_sao_agregadas(tmp_path):
    itens = _fixture(tmp_path)
    proprio = av.bloco(itens, "proprio")
    publico = av.bloco(itens, "publico:ds_x")
    assert publico["n"] == 5
    assert publico["por_classe"]["tampa_ausente"]["n"] == 5
    assert publico["por_classe"]["tampa_ausente"]["recall"] == pytest.approx(4 / 5)
    # se houvesse agregacao, o recall de ausente de 'proprio' mudaria
    assert proprio["por_classe"]["tampa_ausente"]["n"] == 73


def test_veredito_go_nas_duas_classes(tmp_path):
    b = av.bloco(_fixture(tmp_path), "proprio")
    v = {x["classe"]: x["veredito"] for x in av.vereditos(b)}
    assert v["tampa_ausente"] == "GO"
    assert v["tampa_mal_rosqueada"] == "GO"


def test_veredito_no_go_quando_lb_abaixo_do_alvo(tmp_path):
    itens = _fixture(tmp_path)
    itens["m00"]["pred"] = "normal"          # derruba o recall de mal_rosqueada
    b = av.bloco(itens, "proprio")
    mal = [x for x in av.vereditos(b) if x["classe"] == "tampa_mal_rosqueada"][0]
    assert mal["recall_lb95"] < 0.90
    assert mal["veredito"] == "NO_GO"


def test_nao_decidivel_quando_inconclusivo_acima_de_10pct(tmp_path):
    itens = _fixture(tmp_path)
    for iid in list(itens)[:20]:
        if "pred" in itens[iid]:
            itens[iid]["pred"] = "inconclusivo"
    b = av.bloco(itens, "proprio")
    v = [x for x in av.vereditos(b) if x["veredito"] == "NAO_DECIDIVEL"]
    assert any("inconclusivo" in x["motivo"] for x in v)


# ---------------------------------------------------------------- anotacao

def test_anotacao_gera_png_legivel(tmp_path):
    cv2 = pytest.importorskip("cv2")
    import numpy as np
    img = tmp_path / "item.jpg"
    cv2.imwrite(str(img), np.full((120, 200, 3), 200, dtype="uint8"))
    info = {"arquivo": str(img), "pred": "tampa_mal_rosqueada", "verdade": "tampa_mal_rosqueada",
            "confianca": 0.88,
            "medidas": {"tilt_graus": 7.1, "arco_graus": 330.0}, "motivos": ["angulo_zona_cinzenta"]}
    saida = av.anotar("it-0001", info, tmp_path / "anotados")
    assert saida and Path(saida).exists()
    lido = cv2.imread(saida)
    assert lido is not None and lido.shape[0] == 120 and Path(saida).stat().st_size > 500


def test_anotacao_sem_arquivo_nao_quebra(tmp_path):
    assert av.anotar("it-9", {"pred": "normal", "verdade": "normal", "arquivo": ""}, tmp_path) is None


def test_relatorio_nao_quebra_sem_negativos(tmp_path, capsys):
    """Regressao: conjunto em que nao ha negativos de uma classe (todas as amostras sao 'normal')."""
    man = tmp_path / "m.csv"
    man.write_text("item_id,fonte,classe_verdade,arquivo\nit1,proprio,normal,/tmp/x.jpg\n")
    pr = tmp_path / "p.json"
    pr.write_text(json.dumps({"it1": {"classe": "normal", "confianca": 0.9, "medidas": {}, "motivos": []}}))
    rc = av.main(["--manifest", str(man), "--predicoes", str(pr)])
    saida = capsys.readouterr().out
    assert rc == 0
    assert "FP=-" in saida and "neg=0" in saida
