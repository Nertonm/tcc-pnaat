"""Testes da politica da tampa (PoC-02): gatilho de fallback e assimetria da fusao com o auxiliar.

Cada teste corresponde a uma regra do contrato: inclusive as que garantem que o fallback NAO e
acionado quando a geometria ja decidiu com folga (custo) e que o auxiliar nao cancela reprovacao.
"""
from __future__ import annotations

from pocs.poc02_classificacao.politica_tampa import (
    AUSENTE,
    INCONCLUSIVO,
    MAL_ROSQUEADA,
    NORMAL,
    GeometriaTampa,
    Limiares,
    aplicar_auxiliar,
    decidir,
)

LIM = Limiares()


def _geo(**kw) -> GeometriaTampa:
    base = dict(contorno_ok=True, arco_visivel_graus=340.0, tilt_graus=0.5,
                altura_cupula_px=12.0, cnr=25.0, especular=0.005, inliers=140)
    base.update(kw)
    return GeometriaTampa(**base)


def test_tampa_bem_rosqueada_aprova_sem_escalar():
    d = decidir(_geo())
    assert d.classe == NORMAL and d.escalar is False


def test_tampa_ausente_reprova_sem_escalar():
    d = decidir(_geo(altura_cupula_px=1.0))
    assert d.classe == AUSENTE and d.escalar is False


def test_tilt_alto_reprova_sem_escalar():
    d = decidir(_geo(tilt_graus=6.5))
    assert d.classe == MAL_ROSQUEADA and d.escalar is False


def test_zona_cinzenta_do_angulo_escala_para_a_outra_vista():
    d = decidir(_geo(tilt_graus=2.8))
    assert d.classe == INCONCLUSIVO and d.escalar is True
    assert "angulo_zona_cinzenta" in d.motivos


def test_arco_insuficiente_escala_mesmo_com_angulo_pequeno():
    """Oclusao e o gargalo medido: com pouco arco, o angulo nao merece confianca -> outra vista."""
    d = decidir(_geo(arco_visivel_graus=250.0, tilt_graus=0.4))
    assert d.escalar is True and "arco_insuficiente" in d.motivos


def test_captura_degradada_vira_inconclusivo_e_escala():
    d = decidir(_geo(cnr=6.0))
    assert d.classe == INCONCLUSIVO and d.escalar is True
    assert "captura_degradada" in d.motivos


def test_sem_contorno_escala():
    d = decidir(_geo(contorno_ok=False))
    assert d.classe == INCONCLUSIVO and "sem_geometria" in d.motivos


def test_auxiliar_nao_cancela_reprovacao_da_geometria():
    base = decidir(_geo(tilt_graus=6.0))                     # geometria reprovou
    fused = aplicar_auxiliar(base, {"classe": NORMAL})        # auxiliar diz normal: NAO cancela
    assert fused.classe == MAL_ROSQUEADA and fused.origem == "geometria"


def test_auxiliar_conclui_quando_geometria_ficou_inconclusiva():
    base = decidir(_geo(tilt_graus=2.5))                     # zona cinzenta -> escalou
    fused = aplicar_auxiliar(base, {"classe": MAL_ROSQUEADA})
    assert fused.classe == MAL_ROSQUEADA and fused.origem == "auxiliar"


def test_auxiliar_pode_reprovar_quando_geometria_aprovou_e_escalou():
    base = decidir(_geo(arco_visivel_graus=260.0, tilt_graus=0.3))   # aprovou normal, mas escalou
    assert base.classe == NORMAL and base.escalar is True
    fused = aplicar_auxiliar(base, {"classe": AUSENTE})
    assert fused.classe == AUSENTE and "auxiliar_reprovou" in fused.motivos


def test_auxiliar_inconclusivo_nao_vira_aprovacao():
    base = decidir(_geo(tilt_graus=2.5))
    fused = aplicar_auxiliar(base, {"classe": INCONCLUSIVO})
    assert fused.classe == INCONCLUSIVO


def test_sem_auxiliar_mantem_decisao_base():
    base = decidir(_geo(tilt_graus=2.5))
    assert aplicar_auxiliar(base, None) is base


def test_auxiliar_sem_classe_mantem_inconclusivo():
    base = decidir(_geo(arco_visivel_graus=200.0, tilt_graus=0.2))
    fused = aplicar_auxiliar(base, {})
    assert fused.classe == INCONCLUSIVO
