from pocs.poc02_classificacao import avaliar


def test_gate_rnf02_aprovado():
    prev = ["normal"] * 95 + ["tampa_ausente"] * 2 + ["tampa_mal_rosqueada"] * 3
    verd = ["normal"] * 95 + ["tampa_ausente"] * 2 + ["tampa_mal_rosqueada"] * 3
    assert avaliar(prev, verd, limiar=0.95)["aprova_rnf02"] is True


def test_confusao_reprova():
    res = avaliar(["normal"] * 90 + ["tampa_ausente"] * 10, ["normal"] * 100, limiar=0.95)
    assert res["aprova_rnf02"] is False
    assert res["matriz_confusao"].get("normal->tampa_ausente", 0) == 10


def test_tamanho_divergente_erro():
    import pytest
    with pytest.raises(ValueError):
        avaliar(["a"], ["a", "b"])
