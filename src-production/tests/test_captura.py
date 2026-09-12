"""Testes da captura: identidade, tres vistas e verificacao de alinhamento fail-closed.

As imagens sao sinteticas e deterministicas: um quadro com um retangulo claro em posicao conhecida.
Deslocar o item e deslocar o retangulo.
"""
from __future__ import annotations

from datetime import datetime, timezone

import cv2
import numpy as np
import pytest

from captura import (VISTAS_ESPERADAS, Alinhamento, ErroDeCaptura, FonteDeDiretorio,
                     ItemCapturado, VerificadorPorTemplate, VistaCapturada)
from dominio import Vista

AGORA = datetime(2026, 9, 13, 0, 10, tzinfo=timezone.utc)
LARGURA, ALTURA = 320, 240
CAIXA = (120, 80, 80, 60)          # x, y, w, h do retangulo de referencia


def _quadro(dx: int = 0, dy: int = 0) -> np.ndarray:
    im = np.full((ALTURA, LARGURA), 40, dtype=np.uint8)
    x, y, w, h = CAIXA
    im[y + dy:y + h + dy, x + dx:x + w + dx] = 220
    cv2.circle(im, (60 + dx, 180 + dy), 18, 160, -1)      # marca assimetrica
    return im


@pytest.fixture()
def template() -> np.ndarray:
    x, y, w, h = CAIXA
    return _quadro()[y - 10:y + h + 10, x - 10:x + w + 10]


#: onde o template foi recortado no quadro de referencia (canto superior esquerdo)
POSICAO_REF = (CAIXA[0] - 10, CAIXA[1] - 10)


def _escrever(pasta, vista: Vista, imagem) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(pasta / f"{vista.value}.jpg"), imagem)


# ---------------------------------------------------------------- alinhamento

def test_template_aprova_o_enquadramento_de_referencia(template):
    alinhamento, deslocamento = VerificadorPorTemplate(template, POSICAO_REF).verificar(_quadro())
    assert alinhamento is Alinhamento.OK
    assert deslocamento == pytest.approx(0.0, abs=1.0)


def test_item_deslocado_sai_fora_da_tolerancia(template):
    """O score continua alto (o padrao esta la); quem reprova e o deslocamento."""
    alinhamento, deslocamento = VerificadorPorTemplate(template, POSICAO_REF).verificar(_quadro(dx=60, dy=25))
    assert alinhamento is Alinhamento.FORA_DA_TOLERANCIA
    assert deslocamento == pytest.approx((60 ** 2 + 25 ** 2) ** 0.5, abs=2.0)


def test_deslocamento_dentro_da_tolerancia_aprova(template):
    alinhamento, deslocamento = VerificadorPorTemplate(template, POSICAO_REF, tolerancia_px=10).verificar(_quadro(dx=6))
    assert alinhamento is Alinhamento.OK and deslocamento == pytest.approx(6.0, abs=1.5)


def test_gabarito_ausente_e_fora_da_tolerancia(template):
    alinhamento, deslocamento = VerificadorPorTemplate(template, POSICAO_REF).verificar(np.full((ALTURA, LARGURA), 40, np.uint8))
    assert alinhamento is Alinhamento.FORA_DA_TOLERANCIA and deslocamento == float("inf")


def test_template_maior_que_a_imagem_e_erro_explicito():
    grande = np.zeros((500, 500), dtype=np.uint8)
    with pytest.raises(ErroDeCaptura):
        VerificadorPorTemplate(grande, (0, 0)).verificar(_quadro())


# ---------------------------------------------------------------- montagem do item

def test_sem_verificador_nada_e_utilizavel(tmp_path):
    """Rig sem template = conjunto nao calibrado: nao se aprova por omissao."""
    for v in VISTAS_ESPERADAS:
        _escrever(tmp_path / "i-1", v, _quadro())
    item = FonteDeDiretorio(tmp_path).capturar("i-1", AGORA)
    assert len(item.vistas) == 3
    assert all(v.alinhamento is Alinhamento.NAO_VERIFICADO for v in item.vistas)
    assert item.vistas_utilizaveis == ()
    assert item.faltantes == ()


def test_com_verificador_so_o_alinhado_e_utilizavel(tmp_path, template):
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF))
    _escrever(tmp_path / "i-1", Vista.LATERAL1, _quadro())
    _escrever(tmp_path / "i-1", Vista.LATERAL2, _quadro(dx=70))
    _escrever(tmp_path / "i-1", Vista.TOPO, _quadro())
    item = fonte.capturar("i-1", AGORA)
    ok = {v.vista for v in item.vistas_utilizaveis}
    assert ok == {Vista.LATERAL1, Vista.TOPO}
    fora = [v for v in item.vistas if v.alinhamento is Alinhamento.FORA_DA_TOLERANCIA]
    assert [v.vista for v in fora] == [Vista.LATERAL2]


def test_vista_ausente_e_estado_e_nao_erro(tmp_path, template):
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF))
    _escrever(tmp_path / "i-2", Vista.LATERAL1, _quadro())
    item = fonte.capturar("i-2", AGORA)
    assert [v.vista for v in item.vistas] == [Vista.LATERAL1]
    assert item.faltantes == (Vista.TOPO, Vista.LATERAL2)


def test_item_sem_identidade_e_recusado(tmp_path):
    with pytest.raises(ErroDeCaptura):
        FonteDeDiretorio(tmp_path).capturar("   ", AGORA)


def test_item_sem_pasta_e_recusado(tmp_path):
    with pytest.raises(ErroDeCaptura):
        FonteDeDiretorio(tmp_path).capturar("i-inexistente", AGORA)


def test_pasta_sem_imagem_e_recusada(tmp_path):
    (tmp_path / "i-3").mkdir()
    with pytest.raises(ErroDeCaptura):
        FonteDeDiretorio(tmp_path).capturar("i-3", AGORA)


def test_vista_repetida_e_recusada():
    v = VistaCapturada(vista=Vista.TOPO, imagem="x.jpg", capturado_em=AGORA,
                       alinhamento=Alinhamento.OK)
    with pytest.raises(ErroDeCaptura):
        ItemCapturado(item_id="i-1", trigger_em=AGORA, vistas=(v, v))


def test_trigger_sem_fuso_e_recusado():
    with pytest.raises(ErroDeCaptura):
        ItemCapturado(item_id="i-1", trigger_em=datetime(2026, 9, 13),
                      vistas=(VistaCapturada(vista=Vista.TOPO, imagem="x.jpg", capturado_em=AGORA,
                                             alinhamento=Alinhamento.OK),))
