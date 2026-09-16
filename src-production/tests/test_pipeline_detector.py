"""Cadeia com pacote de detector: captura -> preparo do contrato -> decisao -> registro.

O que estes testes provam, e o que NAO provam:

  * provam que o recorte de cada vista vem do CONTRATO por camera (ROI por camera, rotacao declarada)
    e que a decisao passa pelo `Decisor` e chega ao registro com a identidade do pacote;
  * provam que a montagem da cadeia e a mesma (`executar`), sem caminho paralelo;
  * NAO provam desempenho do detector: o modelo aqui e falso e deterministico. Numero de deteccao so
    sai de peso real em dado real (ver `make smoke-detector` e o k-fold do pipeline de treino).
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import pytest

import ajudantes_pacote as aj
from dominio import Classe, Dominio, Vista
from orquestracao import IdentidadeDoRig, abrir_pacote_de_visao, executar
from registro import Registro

IDENTIDADE = IdentidadeDoRig(equipamento="rig-teste", localizacao="bancada-teste")
ITEM = "lote-teste-0001"


def _imagem(caminho: Path, valor: int, altura: int, largura: int) -> Path:
    quadro = np.full((altura, largura, 3), valor, dtype=np.uint8)
    assert cv2.imwrite(str(caminho), quadro)
    return caminho


def _captura(raiz: Path, *, altura1: int = 100, largura1: int = 200,
             altura2: int = 120, largura2: int = 80) -> Path:
    pasta = raiz / ITEM
    pasta.mkdir(parents=True, exist_ok=True)
    _imagem(pasta / "lateral1.jpg", 30, altura1, largura1)
    _imagem(pasta / "lateral2.jpg", 200, altura2, largura2)
    _imagem(pasta / "topo.jpg", 60, 64, 64)
    return raiz


def _pacote_decisivo(tmp_path: Path, **contrato_kwargs) -> Path:
    """Pacote cujo modelo falso decide pelo brilho do recorte: 30 -> normal, 200 -> tampa_ausente."""
    parametros = {"roi_csi": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
                  "roi_usb": {"x": 0.25, "y": 0.0, "w": 0.5, "h": 0.5}}
    parametros.update(contrato_kwargs)
    dados = aj.contrato(**parametros)
    return aj.pacote(tmp_path / "pacote", contrato_dados=dados)


def _classificador_e_preparo(pacote: Path, modelo: aj.ModeloFalso):
    return abrir_pacote_de_visao(pacote, carregador=aj.carregador(modelo))


def _item(raiz_da_captura: Path):
    from captura import FonteDeDiretorio

    return FonteDeDiretorio(raiz_da_captura, verificador=aj.VerificadorFalso(),
                            janela_s=3600.0).capturar(ITEM, datetime.now(UTC))


def test_cadeia_do_pacote_recorta_por_camera_e_registra(tmp_path):
    pacote = _pacote_decisivo(tmp_path)
    modelo = aj.ModeloFalso(por_media=[(lambda media: media >= 128, [(1, 0.90)])],
                            caixas=[(0, 0.90)])
    classificador, motivo, preparo = _classificador_e_preparo(pacote, modelo)
    assert "detector.pt" in motivo

    captura = _captura(tmp_path / "captura")
    item = _item(captura)
    registro = Registro.abrir(tmp_path / "hub.db")
    try:
        resultado = executar(item, classificador, registro, IDENTIDADE, preparo=preparo)
    finally:
        registro.fechar()

    # recorte POR CAMERA, do contrato: a vista lateral1 e a camera csi, a lateral2 e a usb
    formas = {c["shape"] for c in modelo.chamadas}
    assert formas == {(50, 100, 3), (60, 40, 3)}
    # 30 -> normal; 200 -> tampa_ausente; defeito em QUALQUER vista reprova (D-04/D-29)
    por_vista = {(m.vista, m.dominio): m.classe for m in resultado.medidas}
    assert por_vista[(Vista.LATERAL1, Dominio.TAMPA)] is Classe.NORMAL
    assert por_vista[(Vista.LATERAL2, Dominio.TAMPA)] is Classe.TAMPA_AUSENTE
    assert por_vista[(Vista.LATERAL1, Dominio.CORPO)] is Classe.INCONCLUSIVO
    assert resultado.status == "defeito"
    assert resultado.aprovado is False
    assert any("pacote:detector.pt" in e.metodo for m in resultado.medidas for e in m.evidencias)


def test_rota_do_contrato_nao_rotaciona_quadro_ja_orientado(tmp_path):
    pacote = _pacote_decisivo(tmp_path, orientacao_entrada="quadro_ja_orientado", rotacao_usb=0)
    modelo = aj.ModeloFalso(caixas=[(0, 0.90)])
    classificador, _, preparo = _classificador_e_preparo(pacote, modelo)
    _rodar(tmp_path, classificador, preparo)
    assert {c["shape"] for c in modelo.chamadas} == {(50, 100, 3), (60, 40, 3)}


def test_rota_do_contrato_rotaciona_quando_o_quadro_vem_cru(tmp_path):
    """Quadro cru de 120x80 com `usb=90`: rotacionado vira 80x120 e a ROI {w:0.5,h:0.25} da (20,60)."""
    roi_usb = {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.25}
    pacote = _pacote_decisivo(tmp_path / "cru", orientacao_entrada="rotacionar_no_consumo",
                              rotacao_usb=90, roi_usb=roi_usb)
    modelo_cru = aj.ModeloFalso(caixas=[(0, 0.90)])
    classificador_cru, _, preparo_cru = _classificador_e_preparo(pacote, modelo_cru)
    _rodar(tmp_path, classificador_cru, preparo_cru, nome_db="cru.db", nome_captura="captura")
    assert (20, 60, 3) in {c["shape"] for c in modelo_cru.chamadas}

    pacote_orientado = _pacote_decisivo(tmp_path / "orientado",
                                        orientacao_entrada="quadro_ja_orientado",
                                        rotacao_usb=0, roi_usb=roi_usb)
    modelo_orientado = aj.ModeloFalso(caixas=[(0, 0.90)])
    classificador, _, preparo = _classificador_e_preparo(pacote_orientado, modelo_orientado)
    _rodar(tmp_path, classificador, preparo, nome_db="orientado.db", nome_captura="captura")
    assert (30, 40, 3) in {c["shape"] for c in modelo_orientado.chamadas}


def test_item_sem_defeito_nem_assim_aprova_sem_modelo_de_corpo(tmp_path):
    """Aprovacao exige o rig completo (D-04/D-29): sem modelo de CORPO, o item fica inconclusivo.

    O detector deste pacote so cobre a tampa. Nenhum defeito aparece e ainda assim o item NAO e
    aprovado: aprovar por ausencia de evidencia e o erro que a cadeia existe para impedir.
    """
    pacote = _pacote_decisivo(tmp_path)
    modelo = aj.ModeloFalso(caixas=[(0, 0.90)])
    classificador, _, preparo = _classificador_e_preparo(pacote, modelo)
    resultado = _rodar(tmp_path, classificador, preparo)
    assert resultado.status == "inconclusivo"
    assert resultado.aprovado is False
    por_vista = {(m.vista, m.dominio): m.classe for m in resultado.medidas}
    assert por_vista[(Vista.LATERAL1, Dominio.TAMPA)] is Classe.NORMAL
    assert por_vista[(Vista.LATERAL1, Dominio.CORPO)] is Classe.INCONCLUSIVO


def test_pacote_invalido_para_a_cadeia_com_erro_declarado(tmp_path):
    from orquestracao import ErroDeOrquestracao

    destino = tmp_path / "vazio"
    destino.mkdir()
    with pytest.raises(ErroDeOrquestracao):
        abrir_pacote_de_visao(destino)


def test_executar_sem_preparo_e_sem_roi_falha(tmp_path):
    from orquestracao import ErroDeOrquestracao

    pacote = _pacote_decisivo(tmp_path)
    classificador, _, _ = _classificador_e_preparo(pacote, aj.ModeloFalso())
    item = _item(_captura(tmp_path / "captura"))
    registro = Registro.abrir(tmp_path / "hub.db")
    try:
        with pytest.raises(ErroDeOrquestracao, match="nao declarada"):
            executar(item, classificador, registro, IDENTIDADE)
    finally:
        registro.fechar()


def test_contrato_sem_camera_para_a_vista_falha(tmp_path):
    """Contrato que so declara a camera csi: a lateral2 nao tem ROI e a cadeia NAO inventa uma."""
    from orquestracao import ErroDeOrquestracao

    dados = aj.contrato(vistas={"csi": "lateral1"})
    dados["roi_por_camera"] = {"csi": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}}
    dados["rotacao_graus"] = {"csi": 0}
    pacote = aj.pacote(tmp_path / "pacote", contrato_dados=dados)
    classificador, _, preparo = _classificador_e_preparo(pacote, aj.ModeloFalso())
    item = _item(_captura(tmp_path / "captura"))
    registro = Registro.abrir(tmp_path / "hub.db")
    try:
        with pytest.raises(ErroDeOrquestracao):
            executar(item, classificador, registro, IDENTIDADE, preparo=preparo)
    finally:
        registro.fechar()


def _rodar(tmp_path: Path, classificador, preparo, *, nome_db: str = "hub.db",
           nome_captura: str = "captura"):
    raiz = tmp_path / nome_captura
    if not (raiz / ITEM).is_dir():
        _captura(raiz)
    item = _item(raiz)
    registro = Registro.abrir(tmp_path / nome_db)
    try:
        return executar(item, classificador, registro, IDENTIDADE, preparo=preparo)
    finally:
        registro.fechar()
