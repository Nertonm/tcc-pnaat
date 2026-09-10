from pocs.poc03_deformidade import calibrar, dentro_tolerancia, medir


def test_calibracao_e_medida():
    fator = calibrar(100.0, 25.0)
    assert abs(medir(40.0, fator) - 10.0) < 1e-3


def test_tolerancia_rnf14():
    assert dentro_tolerancia(10.2, 10.0, 0.5) is True
    assert dentro_tolerancia(10.6, 10.0, 0.5) is False


def test_pixels_zero_erro():
    import pytest
    with pytest.raises(ValueError):
        calibrar(0.0, 1.0)
