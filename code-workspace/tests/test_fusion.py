"""PoC-04: protocolo da fusao por dominio (D-04, emenda D-23).

Cada teste isola UMA pergunta do protocolo: o defeito sobrevive a discordancia? a vista de topo
pode aprovar? evidencia insuficiente vira aprovacao? a origem e a discordancia ficam registradas?
"""
import pytest

from pocs.events import DefectClass, Dominio, Qualidade, ViewResult
from pocs.poc04_fusao import ConfiguracaoFusao, fundir

T = DefectClass.TAMPA_AUSENTE
M = DefectClass.TAMPA_MAL_ROSQUEADA
D = DefectClass.DEFORMIDADE
N = DefectClass.NORMAL
I = DefectClass.INCONCLUSIVO
CFG_RIG_COMPLETO = ConfiguracaoFusao(rig_id="rig-2laterais-topo")


def normal_dois_lados(**kw):
    """Fixtures de item NORMAL com as duas vistas laterais e o check dimensional."""
    return [
        ViewResult("lateral1", Dominio.TAMPA, N, 0.9),
        ViewResult("lateral2", Dominio.TAMPA, N, 0.9),
        ViewResult("lateral1", Dominio.CORPO, N, 0.9),
        ViewResult("lateral2", Dominio.CORPO, N, 0.9),
        ViewResult("topo", Dominio.DIMENSAO, N, 0.95),
    ]


def test_item_normal_completo_aprova():
    f = fundir(normal_dois_lados(), CFG_RIG_COMPLETO)
    assert f.classe == N
    assert (f.status_tampa, f.status_corpo) == ("ok", "ok")
    assert f.qualidade_registro == "completo"
    assert f.discordancia_lateral is False and f.escalonado is False
    assert f.confidence == 0.9


def test_defeito_nao_e_cancelado_pela_maioria():
    """O caso que a votacao global apagava: 1 vista reprova tampa, as outras 'aprovam'."""
    views = normal_dois_lados()
    views[0] = ViewResult("lateral1", Dominio.TAMPA, M, 0.8)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe == M
    assert f.status_tampa == "defeito" and f.classe_tampa == M
    assert f.discordancia_lateral is True
    assert any(m.startswith("discordancia_tampa") for m in f.motivos)


def test_dominio_corpo_reprova_com_tampa_ok():
    views = normal_dois_lados()
    views[2] = ViewResult("lateral1", Dominio.CORPO, D, 0.85)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert (f.classe, f.status_corpo, f.classe_corpo) == (D, "defeito", D)
    assert f.status_tampa == "ok"  # um dominio nao contamina o outro


def test_dois_dominios_com_defeito_preserva_os_dois():
    views = normal_dois_lados()
    views[0] = ViewResult("lateral1", Dominio.TAMPA, T, 0.7)
    views[3] = ViewResult("lateral2", Dominio.CORPO, D, 0.7)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe == T  # precedencia declarada: tampa antes de corpo
    assert f.classe_tampa == T and f.classe_corpo == D


def test_ausente_tem_precedencia_sobre_mal_rosqueada():
    views = normal_dois_lados()
    views[0] = ViewResult("lateral1", Dominio.TAMPA, M, 0.95)
    views[1] = ViewResult("lateral2", Dominio.TAMPA, T, 0.6)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe_tampa == T
    assert any("classes_divergentes_tampa" in m for m in f.motivos)


def test_top_check_nao_aprova_sozinho():
    """Topo sozinho nao tem evidencia decisoria: inconclusivo, nunca aprovacao."""
    f = fundir([ViewResult("topo", Dominio.DIMENSAO, N, 0.99)],
               ConfiguracaoFusao(checagem_obrigatoria=False))
    assert f.classe == I
    assert f.qualidade_registro == "parcial_1_vista_faltante"
    assert any(m.startswith("sem_vista_decisoria") for m in f.motivos)


def test_top_check_nao_cancela_defeito():
    views = normal_dois_lados()
    views[0] = ViewResult("lateral1", Dominio.TAMPA, M, 0.8)
    f = fundir(views, CFG_RIG_COMPLETO)  # topo continua normal
    assert f.classe == M


def test_top_check_violado_escalona_mesmo_com_dominios_ok():
    views = normal_dois_lados()
    views[4] = ViewResult("topo", Dominio.DIMENSAO, N, 0.9, escalona=True, motivo="dimensao_violada")
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe == I and f.escalonado is True
    assert "dimensao_violada" in f.motivos


def test_check_dimensional_ausente_nao_aprova():
    views = [v for v in normal_dois_lados() if v.view_id != "topo"]
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe == I and f.escalonado is True
    assert "check_dimensional_ausente" in f.motivos


def test_uma_lateral_nao_aprova_dominio_que_exige_duas():
    f = fundir([ViewResult("lateral1", Dominio.TAMPA, N, 0.9),
                ViewResult("lateral1", Dominio.CORPO, N, 0.9)], CFG_RIG_COMPLETO)
    assert f.classe == I
    assert f.qualidade_registro == "parcial_1_vista_faltante"
    assert any(m.startswith("vista_decisoria_ausente_tampa") for m in f.motivos)


def test_configuracao_declarada_de_uma_vista_mede_so_o_corpo():
    """O rig declara o que mede: o corpo fica ok, mas o item nao pode ser aprovado sem a tampa."""
    cfg = ConfiguracaoFusao(rig_id="bancada-1-vista", vistas_decisoria_por_dominio=1,
                            checagem_obrigatoria=False, dominios_medidos=(Dominio.CORPO,))
    f = fundir([ViewResult("lateral1", Dominio.CORPO, N, 0.9)], cfg)
    assert f.status_corpo == "ok"
    assert f.status_tampa == "inconclusivo"
    assert f.classe == I
    assert any(m == "dominio_nao_medido_tampa" for m in f.motivos)


def test_defeito_vs_defeito_de_outra_classe_tambem_e_discordancia():
    views = normal_dois_lados()
    views[0] = ViewResult("lateral1", Dominio.TAMPA, M, 0.95)
    views[1] = ViewResult("lateral2", Dominio.TAMPA, T, 0.60)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.discordancia_lateral is True
    assert any(m.startswith("discordancia_tampa") for m in f.motivos)
    assert any(m.startswith("classes_divergentes_tampa") for m in f.motivos)


def test_dominio_nao_medido_impede_aprovacao():
    """Declarar o rig como 'so corpo' nao pode virar aprovacao silenciosa do item."""
    cfg = ConfiguracaoFusao(rig_id="bancada-1-vista", vistas_decisoria_por_dominio=1,
                            checagem_obrigatoria=False, dominios_medidos=(Dominio.CORPO,))
    f = fundir([ViewResult("lateral1", Dominio.CORPO, N, 0.9)], cfg)
    assert f.classe == I
    assert f.qualidade_registro != "completo"


def test_evidencia_insuficiente_nao_vira_aprovacao():
    views = normal_dois_lados()
    views[1] = ViewResult("lateral2", Dominio.TAMPA, N, 0.9, qualidade=Qualidade.INSUFICIENTE)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe == I
    assert f.qualidade_registro == "evidencia_insuficiente"
    assert any(m.startswith("evidencia_insuficiente_tampa") for m in f.motivos)


def test_inconclusivo_de_vista_nao_vira_aprovacao():
    views = normal_dois_lados()
    views[1] = ViewResult("lateral2", Dominio.TAMPA, I, 0.5)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe == I


def test_defeito_sobrevive_a_evidencia_insuficiente_no_mesmo_dominio():
    """Conservador de proposito: defeito manda o item para analise humana, nao para aprovacao."""
    views = normal_dois_lados()
    views[0] = ViewResult("lateral1", Dominio.TAMPA, M, 0.6, qualidade=Qualidade.INSUFICIENTE)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert f.classe == M and f.status_tampa == "defeito"


def test_origem_e_preservada_por_vista():
    views = normal_dois_lados()
    views[2] = ViewResult("lateral1", Dominio.CORPO, D, 0.85)
    f = fundir(views, CFG_RIG_COMPLETO)
    assert ("lateral1", "corpo", "deformidade") in f.origens
    assert len(f.origens) == len(views)


def test_vista_desconhecida_e_recusada():
    with pytest.raises(ValueError):
        fundir([ViewResult("camera-3", Dominio.CORPO, N, 0.9)])


def test_medicao_duplicada_e_recusada():
    v = ViewResult("lateral1", Dominio.CORPO, N, 0.9)
    with pytest.raises(ValueError):
        fundir([v, v])


def test_classe_incoerente_com_dominio_e_recusada():
    with pytest.raises(ValueError):
        ViewResult("lateral1", Dominio.CORPO, M, 0.9)


def test_sem_vistas_erro():
    with pytest.raises(ValueError):
        fundir([])


def test_como_dict_usa_vocabulario_do_schema():
    f = fundir(normal_dois_lados(), CFG_RIG_COMPLETO)
    d = f.como_dict()
    assert d["classe"] == "normal" and d["status_tampa"] == "ok"
    assert d["discordancia_lateral"] == 0 and d["qualidade_registro"] == "completo"
