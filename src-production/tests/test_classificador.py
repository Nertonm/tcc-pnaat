"""Testes do classificador da tampa: rotulo, contrato do Protocol, fail-closed e identificacao.

Nenhum teste aqui carrega torch. Extrator e cabeca entram por injecao, entao o contrato e exercitado
com dublês deterministas: o modulo TEM de ser importavel (e passavel nos testes) numa maquina sem a
stack de inferencia, e um teste em subprocesso prova isso. A medicao real no conjunto (YOLO +
MobileNetV3 + validacao cruzada) roda FORA dos testes, com o venv que tem a stack.

O que cada bloco protege:
  - `CORPO` devolve `None` e nao toca no extrator: nao existe modelo do corpo, e `None` e o que aciona
    o fallback da D-30 (inconclusivo + humana), nunca uma aprovacao inventada;
  - a medida sai com a VISTA e o DOMINIO consultados (o `Decisor` recusa `ErroDeDecisao` se mentir);
  - classe fora do dominio da tampa e recusada na cabeca e na `Medida` (D-28);
  - recorte e IMAGEM: caminho de arquivo, lista ou vazio e erro (hipotese H-1 da portagem);
  - rotulo por prefixo do nome, com origem sem rotulo sendo erro (nao vira `normal` por omissao);
  - a identificacao declarada e a receita, componente por componente.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import classificador as modulo
import numpy as np
import pytest
from classificador import (
    CONFIANCA_DA_DETECCAO,
    DOBRAS,
    FRACAO_DO_TOPO,
    IDENTIFICACAO,
    LADO_DA_ENTRADA,
    PREFIXO_DAS_CAPTURAS_DO_RIG,
    REFERENCIA_MEDIDA,
    ROTULOS_POR_PREFIXO,
    SEMENTE,
    TAMANHO_DA_DETECCAO,
    VERSAO,
    Amostra,
    ClassificadorDeTampa,
    ErroDeClassificacao,
    ResultadoDaValidacao,
    comparar_com_a_referencia,
    conjunto_rotulado,
    distribuicao,
    medir_por_validacao_cruzada,
    recorte_da_tampa,
    rotulo_do_nome,
    wilson,
)
from decisao import Decisor
from dominio import VOCABULARIO, Classe, Dominio, Medida, Papel, Qualidade, Vista

#: recorte BGR minimo: o classificador so ve pixels (nunca abre arquivo)
RECORTE = np.zeros((13, 50, 3), dtype=np.uint8)


# ---------------------------------------------------------------- dublês deterministicos


class _ExtratorFalso:
    """Extrator declarado: devolve sempre o mesmo vetor e CONTA as chamadas (o corpo nao pode medir)."""

    identificacao = "extrator-falso"

    def __init__(self) -> None:
        self.chamadas = 0

    def embedding(self, recorte):
        self.chamadas += 1
        return np.zeros(4, dtype=float)


class _CabecaFalsa:
    """Cabeca determinista: devolve as probabilidades declaradas, na ordem do sklearn (sorted)."""

    def __init__(self, probabilidades: dict[str, float]) -> None:
        self._por_classe = dict(probabilidades)
        self.classes_ = np.array(sorted(self._por_classe))

    def predict_proba(self, X):
        return np.array([[self._por_classe[nome] for nome in self.classes_]])


def _classificador(
    probabilidades: dict[str, float] | None = None, *, limiar: float = 0.0
) -> tuple[ClassificadorDeTampa, _ExtratorFalso]:
    extrator = _ExtratorFalso()
    cabeca = _CabecaFalsa(
        probabilidades or {"normal": 0.05, "tampa_ausente": 0.90, "defeito_tampa": 0.05}
    )
    return ClassificadorDeTampa(extrator, cabeca, limiar_de_confianca=limiar), extrator


# ---------------------------------------------------------------- dominio do corpo: None (D-30)


def test_corpo_nao_tem_modelo_e_devolve_none():
    classificador, extrator = _classificador()
    assert classificador.prever(RECORTE, Dominio.CORPO, Vista.LATERAL1) is None
    assert extrator.chamadas == 0  # nao se mede o que nao existe modelo para decidir


def test_corpo_cai_no_fallback_do_decisor_e_nunca_aprova():
    classificador, _ = _classificador()
    resultado = Decisor(classificador).decidir(RECORTE, Dominio.CORPO, Vista.LATERAL1)
    assert resultado.papel is Papel.FALLBACK
    assert resultado.classe is Classe.INCONCLUSIVO and resultado.escalona
    assert not resultado.aprovado
    assert resultado.motivo == "classificador_indisponivel"


# ---------------------------------------------------------------- medida com a origem consultada


@pytest.mark.parametrize("vista", [Vista.LATERAL1, Vista.LATERAL2])
def test_medida_sai_com_a_vista_e_o_dominio_consultados(vista):
    classificador, _ = _classificador()
    medida = classificador.prever(RECORTE, Dominio.TAMPA, vista)
    assert medida.vista is vista and medida.dominio is Dominio.TAMPA
    assert medida.classe is Classe.TAMPA_AUSENTE and medida.confianca == pytest.approx(
        0.90
    )
    assert medida.conclusiva


@pytest.mark.parametrize("vista", [Vista.LATERAL1, Vista.LATERAL2])
def test_decisor_aceita_a_medida_e_decide(vista):
    """Passar pelo `Decisor` e o teste que importa: e ele que recusa medida que minta sobre a origem."""
    classificador, _ = _classificador()
    resultado = Decisor(classificador).decidir(RECORTE, Dominio.TAMPA, vista)
    assert resultado.papel is Papel.DECIDE and resultado.vista is vista
    assert resultado.classe is Classe.TAMPA_AUSENTE and not resultado.escalona


@pytest.mark.parametrize(
    "probabilidades, esperada",
    [
        ({"normal": 0.91, "tampa_ausente": 0.05, "defeito_tampa": 0.04}, Classe.NORMAL),
        (
            {"normal": 0.05, "tampa_ausente": 0.91, "defeito_tampa": 0.04},
            Classe.TAMPA_AUSENTE,
        ),
        (
            {"normal": 0.05, "tampa_ausente": 0.04, "defeito_tampa": 0.91},
            Classe.DEFEITO_TAMPA,
        ),
    ],
)
def test_argmax_mapeia_probabilidade_em_classe_do_conjunto(probabilidades, esperada):
    classificador, _ = _classificador(probabilidades)
    medida = classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert medida.classe is esperada
    assert medida.confianca == pytest.approx(0.91)


def test_recorte_que_nao_e_imagem_nao_vira_medida():
    """Hipotese H-1: o recorte chega pronto. Caminho de arquivo (ou lista) e erro, nao conveniencia."""
    classificador, extrator = _classificador()
    for entrada in (
        Path("frame_0000.jpg"),
        "frame_0000.jpg",
        b"frame_0000.jpg",
        ["recorte"],
    ):
        with pytest.raises(ErroDeClassificacao):
            classificador.prever(entrada, Dominio.TAMPA, Vista.LATERAL1)
    assert extrator.chamadas == 0


def test_dominio_ou_vista_fora_do_tipo_e_erro():
    classificador, extrator = _classificador()
    with pytest.raises(ErroDeClassificacao):
        classificador.prever(
            RECORTE, "tampa", Vista.LATERAL1
        )  # str no lugar de Dominio
    with pytest.raises(ErroDeClassificacao):
        classificador.prever(
            RECORTE, Dominio.TAMPA, "lateral1"
        )  # str no lugar de Vista
    assert extrator.chamadas == 0


# ---------------------------------------------------------------- classe fora do dominio (D-28)


def test_cabeca_com_classe_de_outro_dominio_e_recusada():
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDeTampa(
            _ExtratorFalso(), _CabecaFalsa({"normal": 0.5, "deformidade": 0.5})
        )


def test_cabeca_com_classe_desconhecida_e_recusada():
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDeTampa(
            _ExtratorFalso(), _CabecaFalsa({"normal": 0.5, "tampinha": 0.5})
        )


def test_medida_recusa_classe_de_outro_dominio():
    with pytest.raises(ValueError):
        Medida(
            vista=Vista.LATERAL1,
            dominio=Dominio.TAMPA,
            classe=Classe.DEFORMIDADE,
            confianca=0.9,
        )


def test_mapeamento_so_produz_classe_do_dominio_da_tampa():
    assert tuple(prefixo for prefixo, _ in ROTULOS_POR_PREFIXO) == (
        "tampa_ausente",
        "tampa_mal_rosqueada",
        "deformidade",
        "frame_",
    )
    for prefixo, classe in ROTULOS_POR_PREFIXO:
        assert classe in VOCABULARIO[Dominio.TAMPA], prefixo
        assert classe is not Classe.DEFORMIDADE, (
            prefixo
        )  # deformidade e do corpo, nao da tampa


# ---------------------------------------------------------------- rotulo por nome de arquivo


@pytest.mark.parametrize(
    "nome, esperada",
    [
        ("tampa_ausente_frame000.jpg", Classe.TAMPA_AUSENTE),
        ("tampa_ausente_frame014.jpg", Classe.TAMPA_AUSENTE),
        ("tampa_mal_rosqueada_frame0.jpg", Classe.DEFEITO_TAMPA),
        ("tampa_mal_rosqueada_frame19.jpg", Classe.DEFEITO_TAMPA),
        (
            "deformidade_frame_0000.jpg",
            Classe.NORMAL,
        ),  # tampa boa: o corpo e que esta deformado
        ("deformidade_frame_0008.jpg", Classe.NORMAL),
        ("frame_0000.jpg", Classe.NORMAL),  # captura do rig, garrafa normal
        ("frame_0080.jpg", Classe.NORMAL),
    ],
)
def test_rotulo_por_prefixo_do_nome(nome, esperada):
    assert rotulo_do_nome(nome) is esperada


@pytest.mark.parametrize(
    "nome",
    ["garrafa_0001.jpg", "normal_0000.jpg", "0000.jpg", "", "TAMPA_AUSENTE_1.jpg"],
)
def test_nome_sem_rotulo_declarado_e_erro(nome):
    """Rotulo novo nao vira `normal` por omissao: isso envenenaria o treino em silencio."""
    with pytest.raises(ErroDeClassificacao):
        rotulo_do_nome(nome)


def test_conjunto_rotulado_le_a_pasta_e_respeita_o_ignorar(tmp_path):
    nomes = [
        "tampa_ausente_frame000.jpg",
        "tampa_ausente_frame001.jpg",
        "tampa_mal_rosqueada_frame0.jpg",
        "deformidade_frame_0000.jpg",
        "frame_0000.jpg",
    ]
    for nome in nomes:
        (tmp_path / nome).write_bytes(b"nao precisa ser imagem: o rotulo vem do nome")

    completo = conjunto_rotulado(tmp_path)
    assert len(completo) == 5
    assert distribuicao(completo) == (
        (Classe.NORMAL, 2),
        (Classe.TAMPA_AUSENTE, 2),
        (Classe.DEFEITO_TAMPA, 1),
    )

    sem_rig = conjunto_rotulado(tmp_path, ignorar=(PREFIXO_DAS_CAPTURAS_DO_RIG,))
    assert len(sem_rig) == 4
    assert not any(
        item.arquivo.name.startswith(PREFIXO_DAS_CAPTURAS_DO_RIG) for item in sem_rig
    )


def test_conjunto_ausente_ou_vazio_e_erro(tmp_path):
    with pytest.raises(ErroDeClassificacao):
        conjunto_rotulado(tmp_path / "nao-existe")
    with pytest.raises(ErroDeClassificacao):
        conjunto_rotulado(tmp_path)  # pasta vazia nao treina nada


# ---------------------------------------------------------------- recorte da tampa (22% do topo)


def test_recorte_da_tampa_pega_a_faixa_do_topo():
    """Os numeros sao LITERAIS: a fracao e o protocolo medido, nao uma conveniencia do modulo.

    Se a constante mudar, este teste falha; foi assim que uma versao anterior (que calculava o
    esperado com a propria constante) passou com a fracao errada, que e o mesmo que nao testar.
    """
    assert FRACAO_DO_TOPO == pytest.approx(0.22)
    quadro = np.arange(100 * 80 * 3, dtype=np.uint8).reshape(100, 80, 3)
    recorte = recorte_da_tampa(quadro, (10, 20, 60, 80))
    assert recorte.shape == (13, 50, 3)  # int(20 + 60 * 0.22) = 33 -> 13 linhas
    assert np.array_equal(recorte, quadro[20:33, 10:60])
    # truncado, nao arredondado: 10 + 80 * 0.22 = 27,6 -> 27 (round daria 28, e o protocolo medido
    # truncava). Caixa escolhida por isso: e o unico jeito de separar `int` de `round`.
    outro = recorte_da_tampa(quadro, (10, 10, 60, 90))
    assert outro.shape == (17, 50, 3)
    assert np.array_equal(outro, quadro[10:27, 10:60])


@pytest.mark.parametrize(
    "caixa", [(10, 20, 10, 80), (10, 20, 60, 20), (10, 20, 90, 80), (-5, 20, 60, 80)]
)
def test_caixa_degenerada_ou_fora_do_quadro_e_erro(caixa):
    quadro = np.zeros((100, 80, 3), dtype=np.uint8)
    with pytest.raises(ErroDeClassificacao):
        recorte_da_tampa(quadro, caixa)


def test_quadro_que_nao_e_imagem_bgr_e_erro():
    with pytest.raises(ErroDeClassificacao):
        recorte_da_tampa(np.zeros((100, 80), dtype=np.uint8), (10, 20, 60, 80))


def test_detector_recusa_quadro_que_nao_e_imagem():
    """Antes de qualquer uso do YOLO: sem fonte, ele cai num asset empacotado e responde outra imagem.

    Construido por `__new__` (sem carregar peso) de proposito: a validacao de entrada tem de acontecer
    ANTES de qualquer coisa que precise do detector, e este teste roda sem torch.
    """
    import classificador as modulo_detector

    detector = modulo_detector.DetectorDeGarrafa.__new__(
        modulo_detector.DetectorDeGarrafa
    )
    for entrada in (
        None,
        "frame_0000.jpg",
        np.zeros((10, 10), dtype=np.uint8),
        np.zeros((10, 10, 4)),
    ):
        with pytest.raises(ErroDeClassificacao):
            detector.caixa(entrada)


# ---------------------------------------------------------------- limiar declarado (D-30 item i)


def test_limiar_alto_roteia_para_o_fallback_em_vez_de_decidir():
    classificador, _ = _classificador(limiar=0.95)
    medida = classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert medida.classe is Classe.INCONCLUSIVO
    assert medida.qualidade is Qualidade.INSUFICIENTE and not medida.conclusiva
    resultado = Decisor(classificador).decidir(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert (
        resultado.papel is Papel.FALLBACK
        and resultado.escalona
        and not resultado.aprovado
    )
    assert resultado.motivo.startswith("classificador_inconclusivo")


def test_limiar_fora_do_intervalo_e_erro():
    for limiar in (-0.1, 1.1):
        with pytest.raises(ErroDeClassificacao):
            ClassificadorDeTampa(
                _ExtratorFalso(),
                _CabecaFalsa({"normal": 1.0}),
                limiar_de_confianca=limiar,
            )


def test_limiar_roteador_entra_como_evidencia_provisoria():
    """D-24: o limiar que dispara o fallback ainda nao tem fonte (D-30 item (i)); e declarado assim."""
    classificador, _ = _classificador(limiar=0.95)
    medida = classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    limiar = next(
        e for e in medida.evidencias if e.grandeza == "limiar_de_confianca_do_fallback"
    )
    assert limiar.provisorio() is True and limiar.papel is Papel.FALLBACK
    probabilidade = next(
        e for e in medida.evidencias if e.grandeza.startswith("probabilidade")
    )
    assert (
        probabilidade.provisorio() is False
        and probabilidade.fonte == "docs/DECISIONS.md:452"
    )
    assert probabilidade.valor == pytest.approx(0.90)


# ---------------------------------------------------------------- numero de referencia e protocolo


def test_wilson_bate_com_o_limite_de_referencia():
    assert wilson(43, 44) == pytest.approx(0.882, abs=5e-4)
    assert wilson(0, 0) == 0.0
    assert wilson(44, 44) > 0.9


def test_referencia_declarada_e_a_do_documento():
    assert REFERENCIA_MEDIDA.n == 44 and REFERENCIA_MEDIDA.acertos == 43
    assert REFERENCIA_MEDIDA.acuracia == pytest.approx(0.977, abs=5e-4)
    assert REFERENCIA_MEDIDA.lb95 == pytest.approx(0.882, abs=5e-4)
    assert REFERENCIA_MEDIDA.maioria == pytest.approx(0.455, abs=5e-4)
    assert REFERENCIA_MEDIDA.ganho == pytest.approx(0.523, abs=5e-4)
    assert REFERENCIA_MEDIDA.fonte == "docs/DECISIONS.md:452"
    assert sum(d.n for d in REFERENCIA_MEDIDA.por_classe) == 44
    assert sum(d.acertos for d in REFERENCIA_MEDIDA.por_classe) == 43


def test_validacao_cruzada_usa_o_protocolo_declarado():
    """Protocolo: estratificado, embaralhado, semente fixa e escala reajustada dentro de cada dobra."""
    pytest.importorskip("sklearn")
    rng = np.random.default_rng(0)
    centros = {
        "normal": [0.0, 0.0, 0.0],
        "tampa_ausente": [6.0, 0.0, 0.0],
        "defeito_tampa": [0.0, 6.0, 0.0],
    }
    amostras = [
        Amostra(
            origem=f"{nome}-{i}",
            classe=Classe(nome),
            embedding=np.asarray(centro) + rng.normal(0, 0.2, 3),
        )
        for nome, centro in centros.items()
        for i in range(15)
    ]
    resultado = medir_por_validacao_cruzada(amostras, fonte="teste")
    assert (resultado.dobras, resultado.semente) == (
        5,
        7,
    )  # protocolo declarado, literal
    assert resultado.n == 45 and resultado.acertos == 45
    assert resultado.acuracia == pytest.approx(1.0)
    assert resultado.maioria == pytest.approx(15 / 45)
    assert resultado.ganho == pytest.approx(1 - 15 / 45)
    assert sum(d.n for d in resultado.por_classe) == 45
    assert all(d.recall == pytest.approx(1.0) for d in resultado.por_classe)


def test_validacao_cruzada_sem_itens_ou_com_uma_classe_e_erro():
    pytest.importorskip("sklearn")
    with pytest.raises(ErroDeClassificacao):
        medir_por_validacao_cruzada([])
    so_normal = [
        Amostra(origem=f"a-{i}", classe=Classe.NORMAL, embedding=np.zeros(3))
        for i in range(4)
    ]
    with pytest.raises(ErroDeClassificacao):
        medir_por_validacao_cruzada(so_normal)


def test_comparacao_com_a_referencia_nao_maquia_diferenca():
    igual, motivo = comparar_com_a_referencia(REFERENCIA_MEDIDA)
    assert igual and "igual a referencia" in motivo
    outro_conjunto = ResultadoDaValidacao(
        n=125,
        acertos=120,
        acuracia=0.960,
        lb95=0.910,
        maioria=0.720,
        ganho=0.240,
        por_classe=(),
        dobras=5,
        semente=7,
        fonte=None,
    )
    igual, motivo = comparar_com_a_referencia(outro_conjunto)
    assert not igual and "nao comparavel" in motivo
    pior = ResultadoDaValidacao(
        n=44,
        acertos=40,
        acuracia=0.909,
        lb95=0.790,
        maioria=0.455,
        ganho=0.455,
        por_classe=(),
        dobras=5,
        semente=7,
        fonte=None,
    )
    igual, motivo = comparar_com_a_referencia(pior)
    assert not igual and "0.909" in motivo and "40/44" in motivo


# ---------------------------------------------------------------- identificacao declarada

RECEITA_DECLARADA = (
    "medida-cnn-recorte-1"
    "|extrator=mobilenet_v3_small(imagenet-default,congelado,classifier=Identity)"
    "|cabeca=logistic-regression(C=0.5,max_iter=3000)+StandardScaler"
    "|deteccao=yolov8n.pt(classe=bottle,conf=0.15,imgsz=960)"
    "|recorte=22%-do-topo-do-box"
    "|entrada=224px"
    "|validacao=5dobras-semente7"
)


def test_identificacao_declara_a_receita_inteira():
    """A identificacao e a RECEITA do artefato, escrita por extenso: muda-la e mudar o artefato.

    Comparada com a string LITERAL (e nao com uma montada a partir das mesmas constantes): uma
    identificacao derivada das constantes concordaria consigo mesma em qualquer valor, e o numero
    medido passaria a nao ter receita nenhuma atrelada. As constantes entram aqui como gate separado.
    """
    assert isinstance(ClassificadorDeTampa.identificacao, str)
    assert ClassificadorDeTampa.identificacao == RECEITA_DECLARADA
    assert IDENTIFICACAO == RECEITA_DECLARADA and VERSAO == "medida-cnn-recorte-1"
    assert FRACAO_DO_TOPO == pytest.approx(0.22) and LADO_DA_ENTRADA == 224
    assert CONFIANCA_DA_DETECCAO == pytest.approx(0.15) and TAMANHO_DA_DETECCAO == 960
    assert (DOBRAS, SEMENTE) == (5, 7)
    assert (modulo.C_DA_REGULARIZACAO, modulo.MAX_ITERACOES) == (0.5, 3000)
    assert (
        modulo.EXTRATOR == "mobilenet_v3_small"
        and modulo.PESOS_DO_EXTRATOR == "imagenet-default"
    )
    assert (
        Path(modulo.PESOS_DA_DETECCAO).name == "yolov8n.pt"
        and modulo.CLASSE_DA_CAIXA == "bottle"
    )
    assert (
        "sem-modelo" not in IDENTIFICACAO
    )  # nao se confunde com o classificador declarado ausente


def test_assinatura_do_protocolo_do_decisor():
    """O `Decisor` chama `prever(recorte, dominio, vista)`: a assinatura e contrato, nao conveniencia."""
    import inspect

    parametros = list(inspect.signature(ClassificadorDeTampa.prever).parameters)
    assert parametros == ["self", "recorte", "dominio", "vista"]
    assert isinstance(ClassificadorDeTampa.identificacao, str)


def test_modulo_importa_sem_torch():
    """Prova da requisito 2: importar `classificador` nao carrega torch/torchvision/cv2/sklearn."""
    codigo = (
        "import sys; import classificador; "
        "proibidos = [m for m in ('torch', 'torchvision', 'ultralytics', 'cv2', 'sklearn', 'numpy') "
        "if m in sys.modules]; "
        "assert not proibidos, proibidos; "
        "print(classificador.IDENTIFICACAO)"
    )
    processo = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=str(Path(modulo.__file__).parent),
        capture_output=True,
        text=True,
        check=False,
    )
    assert processo.returncode == 0, processo.stderr
    assert processo.stdout.strip() == IDENTIFICACAO
