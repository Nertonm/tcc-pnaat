"""Testes do classificador do artefato (reproducao da receita medida).

O fixture monta um artefato de matematica CONHECIDA (PCA = identidade, padronizacao = identidade,
logits = 3x), para que a expectativa de cada teste possa ser calculada a mao:

    e = [a, 0, 0, 0]  ->  logits = [3a, 0, 0]  ->  p0 = exp(3a) / (exp(3a) + 2)

    a = 1.0  ->  p0 = 0.909...  < 0.95  -> INCONCLUSIVO (roteia para o fallback)
    a = 1.5  ->  p0 = 0.978... >= 0.95  -> decide
"""

from __future__ import annotations

import json

import numpy as np
import pytest
from classificador import ErroDeClassificacao
from classificador_artefato import (
    ARTEFATO_PADRAO,
    ClassificadorDoArtefato,
    Procedencia,
    construir_embutidor,
)
from dominio import Classe, Dominio, Qualidade, Vista

NOMES = ("normal", "tampa_ausente", "defeito_tampa")

#: fixture de matematica conhecida: PCA e padronizacao IDENTIDADE, para as expectativas poderem ser
#: calculadas a mao nos testes de comportamento (roteamento por limiar, classe do argmax).
D, K = 4, 4

#: fixture NAO degenerado: e o que o teste de fidelidade usa. Com transformacao identidade, remover a
#: PCA ou a padronizacao do port nao muda numero nenhum; o teste passaria com o port mutado (foi o que
#: aconteceu na primeira rodada de mutacao). Fidelidade so se prova com transformacao que age.
D_REAL, K_REAL = 6, 4


def _artefato(
    caminho,
    *,
    limiar=0.95,
    nomes=NOMES,
    vintage="teste-1",
    aviso="PROTOTIPO de teste",
    coef=None,
    sem_chave=None,
    sem_metadado=False,
    sem_vintage=False,
    tipo="torchvision",
):
    dados = {
        "mu0": np.zeros(D, dtype=np.float32),
        "P": np.eye(D, K, dtype=np.float32),
        "classes": np.array(nomes, dtype=f"<U{max(len(n) for n in nomes)}"),
        "coef": np.array(
            coef
            if coef is not None
            else [[3.0, 0.0, 0.0, 0.0], [0.0, 3.0, 0.0, 0.0], [0.0, 0.0, 3.0, 0.0]],
            dtype=np.float32,
        ),
        "intercept": np.zeros(len(nomes), dtype=np.float32),
        "mu_nosso": np.zeros(K, dtype=np.float32),
        "sd_nosso": np.ones(K, dtype=np.float32),
        "mu_apoio": np.ones(K, dtype=np.float32),
        "sd_apoio": np.full(K, 2.0, dtype=np.float32),
    }
    if sem_chave:
        dados.pop(sem_chave)
    np.savez(caminho, **dados)
    if sem_metadado:
        return caminho
    meta = {
        "vintage": vintage,
        "extrator": "mobilenetv3s",
        "limiar_abstencao": limiar,
        "classes": list(nomes),
        "avaliacao": {"n": 43, "recall_medio": 0.85},
        "aviso": aviso,
        "config_extrator": {
            "tipo": tipo,
            "fn": "mobilenet_v3_small",
            "pesos": "IMAGENET1K_V1",
            "size": 224,
            "corta": "classifier",
        },
    }
    if sem_vintage:
        meta.pop("vintage")
    caminho.with_suffix(".json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    return caminho


@pytest.fixture
def artefato(tmp_path):
    return _artefato(tmp_path / "modelo-inferencia.npz")


def _artefato_nao_degenerado(caminho, *, limiar=0.95):
    """Artefato cujas transformacoes MUDAM o vetor (PCA cheia, padronizacao com media/sd != 0/1)."""
    rng = np.random.default_rng(11)
    np.savez(
        caminho,
        mu0=rng.normal(size=D_REAL).astype(np.float32),
        P=rng.normal(size=(D_REAL, K_REAL)).astype(np.float32),
        classes=np.array(NOMES, dtype="<U13"),
        coef=rng.normal(size=(len(NOMES), K_REAL)).astype(np.float32),
        intercept=rng.normal(size=len(NOMES)).astype(np.float32),
        mu_nosso=rng.normal(size=K_REAL).astype(np.float32),
        sd_nosso=(1.0 + rng.random(K_REAL)).astype(np.float32),
        mu_apoio=rng.normal(size=K_REAL).astype(np.float32),
        sd_apoio=(1.0 + rng.random(K_REAL)).astype(np.float32),
    )
    caminho.with_suffix(".json").write_text(
        json.dumps(
            {
                "vintage": "teste-nao-degenerado",
                "extrator": "mobilenetv3s",
                "limiar_abstencao": limiar,
                "aviso": "PROTOTIPO de teste",
                "config_extrator": {
                    "tipo": "torchvision",
                    "fn": "mobilenet_v3_small",
                    "pesos": "IMAGENET1K_V1",
                    "size": 224,
                    "corta": "classifier",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return caminho


@pytest.fixture
def artefato_realista(tmp_path):
    return _artefato_nao_degenerado(tmp_path / "modelo-inferencia.npz")


def _embutidor(*vetores):
    """Embutidor de teste: devolve os vetores na ordem das chamadas (conta quantas houve)."""
    chamadas: list[int] = []
    fila = list(vetores)

    def embutir(_recorte):
        chamadas.append(1)
        return np.asarray(fila[min(len(chamadas), len(fila)) - 1], dtype=np.float64)

    embutir.chamadas = chamadas  # type: ignore[attr-defined]
    return embutir


def _imagem():
    return np.zeros((8, 8, 3), dtype=np.uint8)


# ------------------------------------------------------------------ fidelidade da matematica


def test_probabilidades_reproduzem_a_logreg_do_sklearn(artefato_realista):
    """A receita portada tem de bater com `predict_proba` do consumidor do artefato (o servico)."""
    sklearn = pytest.importorskip("sklearn.linear_model")
    artefato = artefato_realista
    cls = ClassificadorDoArtefato.abrir(
        artefato, embutidor=_embutidor(np.zeros(D_REAL))
    )
    with np.load(artefato, allow_pickle=False) as a:
        clf = sklearn.LogisticRegression()
        clf.classes_ = a["classes"]
        clf.coef_ = np.asarray(a["coef"], dtype=np.float64)
        clf.intercept_ = np.asarray(a["intercept"], dtype=np.float64)
        clf.n_features_in_ = clf.coef_.shape[1]
        mu0 = np.asarray(a["mu0"], dtype=np.float64)
        P = np.asarray(a["P"], dtype=np.float64)
        mu_fonte = np.asarray(a["mu_nosso"], dtype=np.float64)
        sd_fonte = np.asarray(a["sd_nosso"], dtype=np.float64)

    rng = np.random.default_rng(7)
    for embedding in rng.normal(size=(6, D_REAL)) * 2.0:
        # referencia independente: PCA -> padronizacao por fonte, como o servico faz
        z = (embedding - mu0) @ P
        z = (z - mu_fonte) / sd_fonte

        # GUARDA DO PROPRIO TESTE: se as transformacoes fossem no-op, este teste passaria com o port
        # mutado. Sem esta linha, o oraculo seria insensivel ao que ele diz provar.
        assert not np.allclose(z, embedding[:K], atol=1e-6), (
            "fixture degenerado: PCA/padronizacao nao mudam o vetor, o teste nao prova o port"
        )
        esperado = clf.predict_proba(z.reshape(1, -1))[0]
        obtido = cls.probabilidades(embedding)
        assert np.allclose(obtido, esperado, atol=1e-12), (obtido, esperado)


def test_a_padronizacao_usa_a_fonte_declarada(artefato, tmp_path):
    """Fonte diferente = estatistica diferente: se a escolha da fonte nao muda nada, ela e decorativa."""
    outra = _artefato(tmp_path / "outro.npz")
    with np.load(outra, allow_pickle=False) as a:
        dados = {chave: a[chave] for chave in a.files}
    dados["mu_nosso"] = np.array([5.0, 0.0, 0.0, 0.0], dtype=np.float32)
    dados["sd_nosso"] = np.array([2.0, 1.0, 1.0, 1.0], dtype=np.float32)
    np.savez(outra, **dados)

    embedding = np.array([1.0, 0.0, 0.0, 0.0])
    padrao = ClassificadorDoArtefato.abrir(artefato, embutidor=_embutidor(embedding))
    deslocado = ClassificadorDoArtefato.abrir(outra, embutidor=_embutidor(embedding))
    assert not np.allclose(
        padrao.probabilidades(embedding), deslocado.probabilidades(embedding)
    )


# ------------------------------------------------------------------ o limiar vem do artefato


def test_limiar_do_metadado_manda_no_roteamento(tmp_path):
    apertado = ClassificadorDoArtefato.abrir(
        _artefato(tmp_path / "a.npz", limiar=0.95),
        embutidor=_embutidor(np.array([1.0, 0.0, 0.0, 0.0])),
    )
    medida = apertado.prever(_imagem(), Dominio.TAMPA, Vista.LATERAL1)
    assert medida.classe is Classe.INCONCLUSIVO
    assert medida.qualidade is Qualidade.INSUFICIENTE
    assert not medida.conclusiva
    assert medida.confianca == pytest.approx(0.9094, abs=1e-3)

    folgado = ClassificadorDoArtefato.abrir(
        _artefato(tmp_path / "b.npz", limiar=0.0),
        embutidor=_embutidor(np.array([1.0, 0.0, 0.0, 0.0])),
    )
    decidida = folgado.prever(_imagem(), Dominio.TAMPA, Vista.LATERAL1)
    assert decidida.classe is Classe.NORMAL
    assert decidida.qualidade is Qualidade.OK
    assert decidida.conclusiva


def test_confianca_acima_do_limiar_decide_a_classe_do_argmax(artefato):
    cls = ClassificadorDoArtefato.abrir(
        artefato, embutidor=_embutidor(np.array([0.0, 0.0, 1.5, 0.0]))
    )
    medida = cls.prever(_imagem(), Dominio.TAMPA, Vista.TOPO)
    assert medida.classe is Classe.DEFEITO_TAMPA
    assert medida.conclusiva
    assert medida.vista is Vista.TOPO
    assert medida.dominio is Dominio.TAMPA


# ------------------------------------------------------------------ fail-closed


def test_corpo_devolve_none_e_nao_embute_nada(artefato):
    embutidor = _embutidor(np.zeros(D))
    cls = ClassificadorDoArtefato.abrir(artefato, embutidor=embutidor)
    assert cls.prever(_imagem(), Dominio.CORPO, Vista.LATERAL1) is None
    assert embutidor.chamadas == [], (
        "sem modelo do corpo nada pode ser extraido da imagem"
    )


def test_recorte_que_nao_e_imagem_e_erro(artefato):
    cls = ClassificadorDoArtefato.abrir(artefato, embutidor=_embutidor(np.zeros(D)))
    for ruim in (
        "/tmp/x.jpg",
        None,
        np.zeros((8, 8), dtype=np.uint8),
        np.zeros((0, 8, 3), dtype=np.uint8),
    ):
        with pytest.raises(ErroDeClassificacao):
            cls.prever(ruim, Dominio.TAMPA, Vista.LATERAL1)


def test_dominio_ou_vista_fora_do_tipo_e_erro(artefato):
    cls = ClassificadorDoArtefato.abrir(artefato, embutidor=_embutidor(np.zeros(D)))
    with pytest.raises(ErroDeClassificacao):
        cls.prever(_imagem(), "tampa", Vista.LATERAL1)
    with pytest.raises(ErroDeClassificacao):
        cls.prever(_imagem(), Dominio.TAMPA, "lateral1")


def test_classe_fora_do_dominio_da_tampa_e_erro(tmp_path):
    caminho = _artefato(tmp_path / "c.npz", nomes=("normal", "gato", "cachorro"))
    with pytest.raises(ErroDeClassificacao, match="gato"):
        ClassificadorDoArtefato.abrir(caminho, embutidor=_embutidor(np.zeros(D)))


def test_embedding_com_dimensao_errada_e_erro(artefato):
    cls = ClassificadorDoArtefato.abrir(artefato, embutidor=_embutidor(np.zeros(D)))
    with pytest.raises(ErroDeClassificacao, match="dimens"):
        cls.probabilidades(np.zeros(D + 1))


def test_fonte_sem_estatistica_no_artefato_e_erro(artefato):
    with pytest.raises(ErroDeClassificacao, match="publico"):
        ClassificadorDoArtefato.abrir(
            artefato, fonte="publico", embutidor=_embutidor(np.zeros(D))
        )


def test_artefato_sem_metadado_e_erro(tmp_path):
    caminho = _artefato(tmp_path / "d.npz", sem_metadado=True)
    with pytest.raises(ErroDeClassificacao, match="sem metadado"):
        ClassificadorDoArtefato.abrir(caminho, embutidor=_embutidor(np.zeros(D)))


def test_metadado_sem_vintage_e_erro(tmp_path):
    caminho = _artefato(tmp_path / "e.npz", sem_vintage=True)
    with pytest.raises(ErroDeClassificacao, match="vintage"):
        ClassificadorDoArtefato.abrir(caminho, embutidor=_embutidor(np.zeros(D)))


def test_npz_sem_chave_da_receita_e_erro(tmp_path):
    caminho = _artefato(tmp_path / "f.npz", sem_chave="coef")
    with pytest.raises(ErroDeClassificacao, match="coef"):
        ClassificadorDoArtefato.abrir(caminho, embutidor=_embutidor(np.zeros(D)))


def test_extrator_declarado_desconhecido_e_erro(tmp_path):
    caminho = _artefato(tmp_path / "g.npz", tipo="magia")
    with pytest.raises(ErroDeClassificacao, match="magia"):
        ClassificadorDoArtefato.abrir(caminho)


def test_artefato_inexistente_e_erro(tmp_path):
    with pytest.raises(ErroDeClassificacao, match="nao existe"):
        ClassificadorDoArtefato.abrir(tmp_path / "nada.npz")


# ------------------------------------------------------------------ procedencia e rastro


def test_procedencia_e_rastro_do_artefato(artefato):
    cls = ClassificadorDoArtefato.abrir(
        artefato, embutidor=_embutidor(np.array([1.0, 0.0, 0.0, 0.0]))
    )
    p = cls.procedencia
    assert isinstance(p, Procedencia)
    assert p.vintage == "teste-1" and p.extrator == "mobilenetv3s"
    assert p.limiar_de_abstencao == 0.95 and p.classes == NOMES
    assert len(p.sha256) == 64 and p.fonte_das_estatisticas == "nosso"
    assert "teste-1" in cls.identificacao and p.sha256[:12] in cls.identificacao
    assert "limiar=0.95" in cls.identificacao
    assert p.aviso == "PROTOTIPO de teste"
    assert "vintage='teste-1'" in p.linha() and "aviso=" in p.linha()


def test_limitacao_declarada_viaja_na_medida_como_provisoria(artefato):
    cls = ClassificadorDoArtefato.abrir(
        artefato, embutidor=_embutidor(np.array([1.0, 0.0, 0.0, 0.0]))
    )
    medida = cls.prever(_imagem(), Dominio.TAMPA, Vista.LATERAL1)
    limitacao = [
        e
        for e in medida.evidencias
        if e.grandeza == "limitacao_declarada_pelo_artefato"
    ]
    assert len(limitacao) == 1
    assert limitacao[0].provisorio() is True
    assert limitacao[0].metodo == "PROTOTIPO de teste"
    limiar = [
        e for e in medida.evidencias if e.grandeza == "limiar_de_confianca_do_fallback"
    ][0]
    assert limiar.provisorio() is False and limiar.fonte.endswith("#limiar_abstencao")
    probabilidade = [
        e for e in medida.evidencias if e.grandeza == "probabilidade_da_classe_decidida"
    ][0]
    assert probabilidade.valor == pytest.approx(medida.confianca)


def test_construir_embutidor_recusa_config_incompleta():
    with pytest.raises(ErroDeClassificacao):
        construir_embutidor({"tipo": "hub"})
    with pytest.raises(ErroDeClassificacao):
        construir_embutidor({"tipo": "torchvision"})
    with pytest.raises(ErroDeClassificacao):
        construir_embutidor({})


# ------------------------------------------------------------------ a cadeia usa o artefato


def test_a_cadeia_registra_a_evidencia_do_modelo(tmp_path, artefato):
    """A ligacao que a tranche entrega: `executar` com o classificador do artefato grava o rastro.

    Embutidor injetado de proposito: o que se prova aqui e a LIGACAO (medida -> Decisor -> registro),
    nao o torch. O embedding real e exercitado no canario (`canario_modelo_artefato.py --cadeia`).
    """
    import sqlite3
    from datetime import UTC, datetime

    import cv2
    from captura import Alinhamento, ItemCapturado, VistaCapturada
    from orquestracao import IdentidadeDoRig, executar
    from registro import Registro

    cls = ClassificadorDoArtefato.abrir(
        artefato, embutidor=_embutidor(np.array([1.5, 0.0, 0.0, 0.0]))
    )
    imagem = tmp_path / "lateral1.jpg"
    cv2.imwrite(str(imagem), np.zeros((32, 32, 3), dtype=np.uint8))
    agora = datetime.now(UTC)
    item = ItemCapturado(
        item_id="T-1",
        trigger_em=agora,
        vistas=(
            VistaCapturada(
                vista=Vista.LATERAL1,
                imagem=imagem,
                capturado_em=agora,
                alinhamento=Alinhamento.OK,
                no_janela=True,
                motivo_da_janela="janela declarada pelo teste",
            ),
        ),
    )
    banco = tmp_path / "t.db"
    registro = Registro.abrir(str(banco))
    try:
        executar(
            item,
            cls,
            registro,
            IdentidadeDoRig("bancada", "teste"),
            roi=(0.0, 0.0, 1.0, 1.0),
        )
    finally:
        registro.fechar()

    linhas = list(
        sqlite3.connect(str(banco)).execute(
            "select grandeza, origem, papel, metodo from evidencia"
        )
    )
    do_modelo = [linha for linha in linhas if linha[1] == "classificador"]
    assert do_modelo, f"nenhuma evidencia do classificador no registro: {linhas}"
    metodos = {linha[3] for linha in do_modelo}
    assert any("teste-1" in metodo for metodo in metodos), metodos
    grandeza = {linha[0] for linha in do_modelo}
    assert "probabilidade_da_classe_decidida" in grandeza
    assert any(
        linha[0] == "limitacao_declarada_pelo_artefato" for linha in do_modelo
    ), "a limitacao declarada pelo artefato nao chegou ao registro"


def test_fabrica_prefere_o_artefato_e_declara_quando_nao_ha_modelo(tmp_path, artefato):
    """`main` nao pode escolher modelo em silencio: ou o artefato abre, ou o motivo aparece."""
    from orquestracao import SemModelo, criar_classificador

    escolhido, motivo = criar_classificador(artefato, embutidor=_embutidor(np.zeros(D)))
    assert isinstance(escolhido, ClassificadorDoArtefato)
    assert "teste-1" in motivo and "limiar=0.95" in motivo

    nenhum, motivo = criar_classificador(None)
    assert isinstance(nenhum, SemModelo)
    assert motivo.strip()

    quebrado, motivo = criar_classificador(tmp_path / "nao-existe.npz")
    assert isinstance(quebrado, SemModelo)
    assert "nao existe" in motivo


# ------------------------------------------------------------------ o artefato real do repo

real = pytest.mark.skipif(
    not ARTEFATO_PADRAO.is_file(), reason=f"artefato real ausente: {ARTEFATO_PADRAO}"
)


@real
def test_artefato_real_abre_com_a_procedencia_declarada():
    """Estrutural (sem torch): abre o artefato do repo e confere o que ele declara sobre si."""
    cls = ClassificadorDoArtefato.abrir()
    p = cls.procedencia
    assert p.vintage.startswith("pet-infer"), p.vintage
    assert p.extrator == "dinov2_vits14"
    assert p.limiar_de_abstencao == pytest.approx(0.95)
    assert set(p.classes) == {"normal", "tampa_ausente", "defeito_tampa"}
    assert p.config_extrator.get("tipo") == "hub"
    assert p.aviso and "NAO VALIDADO" in p.aviso.upper().replace("Ã", "A").replace(
        "Ó", "O"
    )
    assert cls.probabilidades(np.zeros(384)).shape == (3,)
