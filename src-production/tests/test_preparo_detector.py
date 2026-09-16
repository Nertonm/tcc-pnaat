"""Pre-processamento do detector: a regra unica de recorte, rotacao e leitura de contrato.

O que estes testes protegem, e por que:

  * `retangulo_de_recorte` e a UNICA regra de recorte do projeto (treino e inferencia). O teste fixa
    a formula e mostra o caso em que a formula "obvia" (`floor((x+w)*L)`) da 1 px de diferenca;
  * `orientar` gira no sentido horario, e a convencao esta fixada por valor, nao por comentario;
  * orientacao de entrada ambigua e ERRO: sem `orientacao_entrada` nao existe default;
  * contrato sem limiar calibrado no `imgsz` de treino nao decide (o consumidor precisa pedir);
  * fingerprint conferido: arquivo editado a mao nao entra.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

import ajudantes_pacote as aj
from dominio import Vista
from preparo_detector import (ErroDePreparo, ContratoDePreprocessamento, orientar,
                              recorte_normalizado, retangulo_de_recorte)


# --------------------------------------------------------------------------- recorte

def test_retangulo_usa_piso_por_componente():
    assert retangulo_de_recorte((1000, 1000), {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.25}) == \
        (100, 200, 400, 450)


def test_retangulo_difere_da_formula_ingenua():
    """`floor(x*L) + floor(w*L)` != `floor((x+w)*L)`: a diferenca de 1 px existe e e fixada aqui."""
    roi = {"x": 0.15, "y": 0.0, "w": 0.75, "h": 1.0}
    largura = 10
    x1, _, x2, _ = retangulo_de_recorte((largura, 10), roi)
    assert (x1, x2) == (1, 8)
    assert x2 != int((roi["x"] + roi["w"]) * largura)      # a formula ingenua daria 9
    assert x2 - x1 == int(roi["w"] * largura)


@pytest.mark.parametrize("roi", [
    {"x": -0.01, "y": 0.0, "w": 0.5, "h": 0.5},
    {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.5},
    {"x": 0.6, "y": 0.0, "w": 0.5, "h": 0.5},
    {"x": float("nan"), "y": 0.0, "w": 0.5, "h": 0.5},
    {"x": 0.0, "y": 0.0, "w": 0.5},
])
def test_roi_invalida_falha(roi):
    with pytest.raises(ErroDePreparo):
        retangulo_de_recorte((100, 100), roi)


@pytest.mark.parametrize("tamanho", [(0, 10), (-1, 10), (10,)])
def test_tamanho_invalido_falha(tamanho):
    with pytest.raises(ErroDePreparo):
        retangulo_de_recorte(tamanho, {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5})


def test_recorte_devolve_a_regiao_e_nao_copia_o_quadro():
    quadro = np.arange(4 * 6 * 3, dtype=np.uint8).reshape(4, 6, 3)
    recorte = recorte_normalizado(quadro, {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5})
    assert recorte.shape == (2, 3, 3)
    assert np.array_equal(recorte, quadro[2:4, 3:6])


@pytest.mark.parametrize("quadro", [
    np.zeros((4, 4), dtype=np.uint8),                       # sem canal
    np.zeros((4, 4, 4), dtype=np.uint8),                    # 4 canais
    np.zeros((4, 4, 3), dtype=np.float32),                  # nao e BGR de 8 bits
    np.zeros((0, 4, 3), dtype=np.uint8),                    # vazio
    [[0, 0, 0]],                                            # nem ndarray
])
def test_quadro_invalido_falha(quadro):
    with pytest.raises(ErroDePreparo):
        recorte_normalizado(quadro, {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})


# --------------------------------------------------------------------------- rotacao

def test_rotacao_e_no_sentido_horario():
    quadro = np.arange(6, dtype=np.uint8).reshape(2, 3)
    quadro = np.repeat(quadro[:, :, None], 3, axis=2)          # a rotacao e definida para BGR
    assert orientar(quadro, 0) is quadro
    esperado_90 = np.array([[3, 0], [4, 1], [5, 2]], dtype=np.uint8)[:, :, None].repeat(3, axis=2)
    esperado_180 = np.array([[5, 4, 3], [2, 1, 0]], dtype=np.uint8)[:, :, None].repeat(3, axis=2)
    esperado_270 = np.array([[2, 5], [1, 4], [0, 3]], dtype=np.uint8)[:, :, None].repeat(3, axis=2)
    assert np.array_equal(orientar(quadro, 90), esperado_90)
    assert np.array_equal(orientar(quadro, 180), esperado_180)
    assert np.array_equal(orientar(quadro, 270), esperado_270)


def test_rotacao_horaria_de_90_leva_a_coluna_da_esquerda_para_o_topo():
    """Convencao explicita, sem ambiguidade: esquerda vira topo no giro de 90 (horario)."""
    quadro = np.zeros((4, 3, 3), dtype=np.uint8)
    quadro[:, 0] = 7
    girado = orientar(quadro, 90)
    assert girado.shape == (3, 4, 3)
    assert np.all(girado[0] == 7)


def test_rotacao_invalida_falha():
    with pytest.raises(ErroDePreparo):
        orientar(np.zeros((2, 2, 3), dtype=np.uint8), 45)


# --------------------------------------------------------------------------- contrato

def _contrato(**kwargs) -> ContratoDePreprocessamento:
    dado = aj.contrato(peso_sha256="a" * 64, **kwargs)
    return ContratoDePreprocessamento(dado, "memoria/preprocessamento.json")


def test_contrato_valido_expoe_cameras_e_vistas():
    contrato = _contrato()
    assert contrato.cameras() == ("csi", "usb")
    assert contrato.vista_da_camera("usb") is Vista.LATERAL2
    assert contrato.roi_da_camera("csi") == {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}
    assert contrato.limiares(480)["tampa_ausente"] == 0.15
    assert contrato.calibrado_no_imgsz_de_treino() is True


def test_camera_desconhecida_falha():
    with pytest.raises(ErroDePreparo):
        _contrato().roi_da_camera("espcam")


def test_imgsz_sem_limiar_falha():
    with pytest.raises(ErroDePreparo):
        _contrato().limiares(416)


def test_fingerprint_editado_a_mao_e_recusado():
    dado = aj.contrato()
    dado["imgsz_treino"] = 320
    with pytest.raises(ErroDePreparo):
        ContratoDePreprocessamento(dado, "memoria/preprocessamento.json")


def test_fingerprint_pega_edicao_que_o_resto_da_validacao_aceita():
    """ROI editada a mao passa por toda validacao de campo e TEM de morrer no fingerprint."""
    dado = aj.contrato()
    dado["roi_por_camera"]["csi"] = {"x": 0.0, "y": 0.0, "w": 0.4, "h": 0.5}
    with pytest.raises(ErroDePreparo, match="fingerprint"):
        ContratoDePreprocessamento(dado, "memoria/preprocessamento.json")
    # e o mesmo contrato com o fingerprint recalculado abre: a guarda e o fingerprint, so ele
    dado["fingerprint"] = aj.fingerprint_do_contrato(dado)
    assert ContratoDePreprocessamento(dado, "memoria/preprocessamento.json").roi_da_camera(
        "csi")["w"] == 0.4


@pytest.mark.parametrize("campo,valor", [
    ("orientacao_entrada", "tanto_faz"),
    ("orientacao_entrada", None),
    ("letterbox", False),
    ("imgsz_treino", 0),
    ("classes", ["normal", "normal"]),
])
def test_contrato_com_campo_invalido_falha(campo, valor):
    dado = aj.contrato(peso_sha256="a" * 64)
    dado[campo] = valor
    dado["fingerprint"] = aj.fingerprint_do_contrato(dado)
    with pytest.raises(ErroDePreparo):
        ContratoDePreprocessamento(dado, "memoria/preprocessamento.json")


def test_cameras_divergentes_entre_roi_e_rotacao_falham():
    dado = aj.contrato(peso_sha256="a" * 64)
    dado["rotacao_graus"] = {"csi": 0}
    dado["fingerprint"] = aj.fingerprint_do_contrato(dado)
    with pytest.raises(ErroDePreparo):
        ContratoDePreprocessamento(dado, "memoria/preprocessamento.json")


def test_limiar_calibrado_sem_fonte_falha():
    dado = aj.contrato(peso_sha256="a" * 64)
    del dado["limiares_por_imgsz"]["480"]["fonte"]
    dado["fingerprint"] = aj.fingerprint_do_contrato(dado)
    with pytest.raises(ErroDePreparo):
        ContratoDePreprocessamento(dado, "memoria/preprocessamento.json")


def test_limiar_nao_calibrado_nao_abre_nem_com_pedido():
    """Nao existe caminho provisorio em producao: contrato sem calibracao nao abre."""
    dado = aj.contrato(calibrado=False)
    with pytest.raises(ErroDePreparo, match="nao esta calibrado"):
        ContratoDePreprocessamento(dado, "memoria/preprocessamento.json")
    import inspect
    assinatura = inspect.signature(ContratoDePreprocessamento.abrir)
    assert 'permitir_nao_calibrado' not in assinatura.parameters, (
        'a porta do provisorio voltou: nenhuma flag pode contornar a calibracao')


def test_abrir_de_arquivo_inexistente_falha(tmp_path):
    with pytest.raises(ErroDePreparo):
        ContratoDePreprocessamento.abrir(tmp_path / "nao-existe.json")


# --------------------------------------------------------------------------- preparo

def test_preparo_com_quadro_ja_orientado_nao_rotaciona():
    contrato = _contrato(rotacao_usb=90, orientacao_entrada="quadro_ja_orientado")
    quadro = np.arange(8 * 8 * 3, dtype=np.uint8).reshape(8, 8, 3)
    preparo = contrato.preparar(quadro, "usb")
    assert preparo.rotacao_aplicada == 0
    assert preparo.retangulo == (2, 0, 6, 4)
    assert np.array_equal(preparo.recorte, quadro[0:4, 2:6])


def test_preparo_com_quadro_a_rotacionar_rotaciona_antes_de_recortar():
    contrato = _contrato(rotacao_usb=90, orientacao_entrada="rotacionar_no_consumo")
    quadro = np.arange(8 * 8 * 3, dtype=np.uint8).reshape(8, 8, 3)
    preparo = contrato.preparar(quadro, "usb")
    assert preparo.rotacao_aplicada == 90
    rotacionado = np.ascontiguousarray(np.rot90(quadro, k=-1))
    assert preparo.retangulo == (2, 0, 6, 4)
    assert np.array_equal(preparo.recorte, rotacionado[0:4, 2:6])
    assert not np.array_equal(rotacionado[0:4, 2:6], quadro[0:4, 2:6])


def test_json_do_contrato_da_volta_no_disco(tmp_path):
    dado = aj.contrato(peso_sha256="b" * 64)
    caminho = tmp_path / "preprocessamento.json"
    caminho.write_text(json.dumps(dado, ensure_ascii=False, indent=1))
    contrato = ContratoDePreprocessamento.abrir(caminho)
    assert contrato.versao == 1
    assert contrato.fingerprint_calculado() == dado["fingerprint"]
