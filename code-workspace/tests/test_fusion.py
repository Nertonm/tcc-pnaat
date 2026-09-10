from pnaat_pocs.events import DefectClass, ViewResult
from pnaat_pocs.poc04_fusao import fuse_views


def test_majoria_estrita_vence():
    res = fuse_views([ViewResult("v1", DefectClass.CAP_AUSENTE, 0.9), ViewResult("v2", DefectClass.CAP_AUSENTE, 0.85)])
    assert res[0] == DefectClass.CAP_AUSENTE
    assert res[1] == 0.9


def test_vista_unica_ok():
    res = fuse_views([ViewResult("v1", DefectClass.DEFORMIDADE, 0.93)])
    assert res[0] == DefectClass.DEFORMIDADE
    assert res[1] == 0.93


def test_empate_vira_analise_humana():
    res = fuse_views([ViewResult("v1", DefectClass.CAP_AUSENTE, 0.8), ViewResult("v2", DefectClass.CAP_MAL_ROSQUEADA, 0.9)])
    assert res[0] == DefectClass.ANALISE_HUMANA


def test_sem_maioria_estrita_analise_humana():
    res = fuse_views([
        ViewResult("v1", DefectClass.CAP_AUSENTE, 0.9),
        ViewResult("v2", DefectClass.NORMAL, 0.9),
        ViewResult("v3", DefectClass.DEFORMIDADE, 0.9),
    ])
    assert res[0] == DefectClass.ANALISE_HUMANA


def test_sem_resultados_erro():
    import pytest
    with pytest.raises(ValueError):
        fuse_views([])
