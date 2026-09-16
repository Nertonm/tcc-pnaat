from __future__ import annotations

from datetime import UTC, datetime

import cv2
import numpy as np
import pytest
from decisao import Decisor, ErroDeDecisao
from dominio import (
    Classe,
    Dominio,
    Evento,
    Evidencia,
    Medida,
    Origem,
    Papel,
    Qualidade,
    Vista,
)
from orquestracao import ErroDeOrquestracao, SemModelo, recorte_da_vista
from registro import ConflitoDeItem, ReferenciaDaEvidencia, Registro

AGORA = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)


def _evento_com_medidas(*, qualidade=Qualidade.OK, evidencias=()):
    medidas = tuple(
        Medida(
            vista=vista,
            dominio=dominio,
            classe=Classe.NORMAL,
            confianca=0.9,
            qualidade=qualidade,
            evidencias=evidencias,
        )
        for vista in (Vista.LATERAL1, Vista.LATERAL2)
        for dominio in (Dominio.TAMPA, Dominio.CORPO)
    )
    return Evento(
        item_id="i-reg",
        capturado_em=AGORA,
        equipamento="pi5",
        localizacao="bancada",
        vistas=(Vista.LATERAL1, Vista.LATERAL2),
        medidas=medidas,
        status=Classe.NORMAL,
    )


def test_sem_modelo_honra_o_protocolo_de_vista():
    assert SemModelo().prever(None, Dominio.TAMPA, Vista.LATERAL1) is None


def test_qualidade_insuficiente_nao_vira_aprovacao(reg):
    evento = _evento_com_medidas(qualidade=Qualidade.INSUFICIENTE)
    reg.registrar(evento)
    gravado = reg.ler(evento.item_id)
    assert gravado is not None
    assert gravado.status_final == "inconclusivo"


def test_registro_faz_rollback_se_gravacao_de_evidencia_falhar(tmp_path, monkeypatch):
    reg = Registro.abrir(tmp_path / "hub.db")
    evidencia = Evidencia(
        grandeza="x",
        valor=1.0,
        unidade="px",
        origem=Origem.GEOMETRIA,
        papel=Papel.AUXILIAR,
        metodo="teste",
    )
    evento = _evento_com_medidas(evidencias=(evidencia,))

    def falha(*args, **kwargs):
        raise RuntimeError("falha injetada")

    monkeypatch.setattr(reg, "_gravar_evidencias", falha)
    try:
        with pytest.raises(RuntimeError, match="falha injetada"):
            reg.registrar(evento)
        assert reg.contar() == 0
        assert reg._cx.execute("SELECT COUNT(*) FROM inspecao_vista").fetchone()[0] == 0
    finally:
        reg.fechar()


class _GeometriaComPapelInvalido:
    identificacao = "geo-invalida"

    def medir(self, recorte):
        return (
            Evidencia(
                grandeza="x",
                valor=1.0,
                unidade="px",
                origem=Origem.CLASSIFICADOR,
                papel=Papel.DECIDE,
                metodo="teste",
            ),
        )


def test_geometria_decisoria_e_rejeitada():
    with pytest.raises(ErroDeDecisao, match="geometria.*auxiliar"):
        Decisor(SemModelo(), _GeometriaComPapelInvalido()).decidir(
            None, Dominio.TAMPA, Vista.LATERAL1
        )


def test_replay_com_referencia_alterada_vira_conflito(tmp_path):
    reg = Registro.abrir(tmp_path / "hub.db")
    evento = _evento_com_medidas()
    referencias_a = tuple(
        ReferenciaDaEvidencia(vista=v, caminho=f"a/{v.value}.jpg", sha256="a" * 64)
        for v in evento.vistas
    )
    referencias_b = tuple(
        ReferenciaDaEvidencia(vista=v, caminho=f"b/{v.value}.jpg", sha256="b" * 64)
        for v in evento.vistas
    )
    try:
        assert reg.registrar(evento, referencias=referencias_a) == "inserido"
        with pytest.raises(ConflitoDeItem):
            reg.registrar(evento, referencias=referencias_b)
        assert {
            x["sha256_evidencia"]
            for x in reg._cx.execute(
                "SELECT DISTINCT sha256_evidencia FROM inspecao_vista"
            )
        } == {"a" * 64}
    finally:
        reg.fechar()


@pytest.mark.parametrize(
    "roi",
    [
        (-0.1, 0.0, 1.0, 1.0),
        (0.0, 0.0, 1.1, 1.0),
        (0.0, 0.0, 0.0, 1.0),
        (0.0, float("nan"), 1.0, 1.0),
    ],
)
def test_roi_invalida_e_rejeitada_sem_clamp(tmp_path, roi):
    imagem = tmp_path / "frame.jpg"
    cv2.imwrite(str(imagem), np.zeros((20, 30, 3), dtype=np.uint8))
    with pytest.raises(ErroDeOrquestracao):
        recorte_da_vista(imagem, roi)


@pytest.fixture
def reg(tmp_path):
    registro = Registro.abrir(tmp_path / "hub.db")
    yield registro
    registro.fechar()
