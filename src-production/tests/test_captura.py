"""Testes da captura: identidade, tres vistas, alinhamento e janela temporal (fail-closed).

As imagens sao sinteticas e deterministicas: um quadro com um retangulo claro em posicao conhecida.
Deslocar o item e deslocar o retangulo. O tempo de captura e o mtime do arquivo, entao o teste
escreve a imagem e AJUSTA o mtime — sem isso a janela nao tem o que medir.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import cv2
import numpy as np
import pytest

from captura import (MOTIVO_FORA_DA_JANELA, MOTIVO_JANELA_NAO_DECLARADA, VISTAS_ESPERADAS, Alinhamento,
                     ErroDeCaptura, FonteDeDiretorio, ItemCapturado, VerificadorPorTemplate,
                     VistaCapturada)
from dominio import Vista

AGORA = datetime(2026, 9, 13, 3, 0, tzinfo=timezone.utc)
LARGURA, ALTURA = 320, 240
CAIXA = (120, 80, 80, 60)          # x, y, w, h do retangulo de referencia
#: onde o template foi recortado no quadro de referencia (canto superior esquerdo)
POSICAO_REF = (CAIXA[0] - 10, CAIXA[1] - 10)


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


def _escrever(pasta, vista: Vista, imagem, quando: datetime = AGORA) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{vista.value}.jpg"
    cv2.imwrite(str(caminho), imagem)
    ts = quando.timestamp()
    os.utime(caminho, (ts, ts))


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


# ---------------------------------------------------------------- janela temporal (RF-01.2)

def test_vista_dentro_da_janela_e_utilizavel(tmp_path, template):
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF), janela_s=1.0)
    _escrever(tmp_path / "i-1", Vista.LATERAL1, _quadro(), AGORA + timedelta(milliseconds=300))
    item = fonte.capturar("i-1", AGORA)
    assert [v.vista for v in item.vistas_utilizaveis] == [Vista.LATERAL1]
    assert item.vistas[0].motivo_da_janela is None
    assert item.fora_da_janela == ()
    assert item.faltantes == (Vista.TOPO, Vista.LATERAL2)


def test_vista_fora_da_janela_conta_como_faltante(tmp_path, template):
    """Contrato da interface: camera fora da janela e identificada como faltante."""
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF), janela_s=1.0)
    _escrever(tmp_path / "i-1", Vista.LATERAL1, _quadro())                                  # na hora
    _escrever(tmp_path / "i-1", Vista.LATERAL2, _quadro(), AGORA + timedelta(seconds=5))     # atrasada
    item = fonte.capturar("i-1", AGORA)
    assert [v.vista for v in item.vistas_utilizaveis] == [Vista.LATERAL1]
    assert [v.vista for v in item.fora_da_janela] == [Vista.LATERAL2]
    assert item.vistas[1].motivo_da_janela == MOTIVO_FORA_DA_JANELA
    assert Vista.LATERAL2 in item.faltantes                   # fora da janela nao entra como evidencia


def test_atraso_tambem_conta_quando_a_vista_vem_adiantada(tmp_path, template):
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF), janela_s=1.0)
    _escrever(tmp_path / "i-1", Vista.LATERAL1, _quadro(), AGORA - timedelta(seconds=4))
    item = fonte.capturar("i-1", AGORA)
    assert item.vistas[0].no_janela is False
    assert item.vistas[0].motivo_da_janela == MOTIVO_FORA_DA_JANELA


def test_sem_janela_declarada_nada_e_utilizavel(tmp_path, template):
    """Rig sem janela declarada nao tem associacao temporal verificada: nao aprova por omissao."""
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF))
    for v in VISTAS_ESPERADAS:
        _escrever(tmp_path / "i-1", v, _quadro())
    item = fonte.capturar("i-1", AGORA)
    assert item.vistas_utilizaveis == ()
    assert {v.motivo_da_janela for v in item.vistas} == {MOTIVO_JANELA_NAO_DECLARADA}
    assert {v.vista for v in item.nao_verificadas} == set(VISTAS_ESPERADAS)
    assert item.fora_da_janela == ()            # nao declarada nao e "divergencia medida"
    assert item.faltantes == VISTAS_ESPERADAS


def test_item_montado_a_mao_sem_janela_declarada_nao_e_utilizavel():
    """Vista sem verificacao de janela nao vira evidencia, mesmo com alinhamento ok."""
    v = VistaCapturada(vista=Vista.LATERAL1, imagem="x.jpg", capturado_em=AGORA,
                       alinhamento=Alinhamento.OK)
    item = ItemCapturado(item_id="i-1", trigger_em=AGORA, vistas=(v,))
    assert item.vistas_utilizaveis == ()
    assert [x.vista for x in item.nao_verificadas] == [Vista.LATERAL1]
    assert item.faltantes == VISTAS_ESPERADAS


# ---------------------------------------------------------------- montagem do item

def test_sem_verificador_nada_e_utilizavel(tmp_path):
    fonte = FonteDeDiretorio(tmp_path, janela_s=1.0)
    for v in VISTAS_ESPERADAS:
        _escrever(tmp_path / "i-1", v, _quadro())
    item = fonte.capturar("i-1", AGORA)
    assert len(item.vistas) == 3
    assert all(v.alinhamento is Alinhamento.NAO_VERIFICADO for v in item.vistas)
    assert item.vistas_utilizaveis == ()


def test_com_verificador_so_o_alinhado_e_utilizavel(tmp_path, template):
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF), janela_s=5.0)
    _escrever(tmp_path / "i-1", Vista.LATERAL1, _quadro())
    _escrever(tmp_path / "i-1", Vista.LATERAL2, _quadro(dx=70))
    _escrever(tmp_path / "i-1", Vista.TOPO, _quadro())
    item = fonte.capturar("i-1", AGORA)
    assert {v.vista for v in item.vistas_utilizaveis} == {Vista.LATERAL1, Vista.TOPO}
    fora = [v for v in item.vistas if v.alinhamento is Alinhamento.FORA_DA_TOLERANCIA]
    assert [v.vista for v in fora] == [Vista.LATERAL2]


def test_vista_ausente_e_estado_e_nao_erro(tmp_path, template):
    fonte = FonteDeDiretorio(tmp_path, verificador=VerificadorPorTemplate(template, POSICAO_REF), janela_s=5.0)
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
