"""Classificador do pacote: o que ele NUNCA pode fazer.

Os testes que importam sao os de decisao, porque sao os que trocam de resultado em silencio:

  * caixa `normal` mais confiante NAO pode suprimir caixa de defeito acima do limiar dela;
  * nenhuma caixa acima do limiar -> `inconclusivo` (nunca `normal` por silencio);
  * `topo` e CORPO devolvem `None` (fallback), nao um voto;
  * classes do PESO divergentes das do contrato sao erro na carga, nao na decisao;
  * pacote corrompido, metadados de outro peso ou contrato nao calibrado sem pedido explicito nao
    abrem.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

import ajudantes_pacote as aj
from classificador_yolo import (ClassificadorDoPacote, ErroDeClassificacao, camera_da_vista,
                                mapa_camera_vista, roi_por_vista)
from dominio import Classe, Dominio, Papel, Qualidade, Vista

RECORTE = np.full((40, 60, 3), 120, dtype=np.uint8)


def _abrir(tmp_path, modelo=None, **kwargs):
    modelo = modelo if modelo is not None else aj.ModeloFalso()
    destino = aj.pacote(tmp_path / "pacote")
    return ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(modelo), **kwargs)


def test_identificacao_carrega_peso_contrato_e_calibracao(tmp_path):
    classificador = _abrir(tmp_path)
    assert "detector.pt" in classificador.identificacao
    assert "imgsz=480" in classificador.identificacao
    assert "calibrado=sim" in classificador.identificacao


def test_caixa_normal_mais_confiante_nao_suprime_defeito(tmp_path):
    """O defeito perdeu a disputa de confianca e ainda assim tem de decidir: e o erro irreversivel."""
    modelo = aj.ModeloFalso(caixas=[(0, 0.97), (2, 0.31)])
    classificador = _abrir(tmp_path, modelo)
    medida = classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert medida.classe is Classe.DEFEITO_TAMPA
    assert medida.confianca == pytest.approx(0.31)


def test_silencio_vira_inconclusivo_e_nunca_normal(tmp_path):
    classificador = _abrir(tmp_path, aj.ModeloFalso(caixas=[]))
    medida = classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert medida.classe is Classe.INCONCLUSIVO
    assert medida.qualidade is Qualidade.INSUFICIENTE
    assert any(e.grandeza == "motivo_do_inconclusivo" for e in medida.evidencias)


def test_caixa_abaixo_do_limiar_da_classe_nao_decide(tmp_path):
    modelo = aj.ModeloFalso(caixas=[(0, 0.20), (2, 0.10)])       # normal < 0.30, defeito < 0.30
    classificador = _abrir(tmp_path, modelo)
    assert classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1).classe is Classe.INCONCLUSIVO


def test_normal_acima_do_limiar_decide_normal(tmp_path):
    classificador = _abrir(tmp_path, aj.ModeloFalso(caixas=[(0, 0.61)]))
    medida = classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert medida.classe is Classe.NORMAL
    assert medida.evidencias[0].papel is Papel.DECIDE
    assert medida.evidencias[0].fonte is not None               # rastro do pacote, nao provisorio


def test_deteccao_roda_no_imgsz_do_contrato_e_no_piso_de_confianca(tmp_path):
    modelo = aj.ModeloFalso(caixas=[(0, 0.9)])
    classificador = _abrir(tmp_path, modelo)
    classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert modelo.chamadas[0]["imgsz"] == 480
    assert modelo.chamadas[0]["conf"] == pytest.approx(0.01)


def test_corpo_e_topo_nao_recebem_voto(tmp_path):
    classificador = _abrir(tmp_path)
    assert classificador.prever(RECORTE, Dominio.CORPO, Vista.LATERAL1) is None
    assert classificador.prever(RECORTE, Dominio.TAMPA, Vista.TOPO) is None


def test_recorte_errado_e_erro_declarado(tmp_path):
    classificador = _abrir(tmp_path)
    with pytest.raises(ErroDeClassificacao):
        classificador.prever("caminho/da/imagem.jpg", Dominio.TAMPA, Vista.LATERAL1)
    with pytest.raises(ErroDeClassificacao):
        classificador.prever(np.zeros((4, 4), dtype=np.uint8), Dominio.TAMPA, Vista.LATERAL1)


def test_classes_do_peso_divergentes_falham_na_carga(tmp_path):
    modelo = aj.ModeloFalso(names={0: "normal", 1: "tampa_ausente", 2: "rotulo_estranho"})
    classificador = _abrir(tmp_path, modelo)
    with pytest.raises(ErroDeClassificacao):
        classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)


def test_peso_com_numero_de_classes_diferente_falha(tmp_path):
    modelo = aj.ModeloFalso(names={0: "normal"})
    classificador = _abrir(tmp_path, modelo)
    with pytest.raises(ErroDeClassificacao):
        classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)


def test_peso_alterado_no_disco_nao_abre(tmp_path):
    destino = aj.pacote(tmp_path / "pacote")
    (destino / "detector.pt").write_bytes(b"outro peso")
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))


def test_manifesto_com_arquivo_extra_nao_abre(tmp_path):
    destino = aj.pacote(tmp_path / "pacote")
    (destino / "sobra.txt").write_text("nao pertenco ao pacote")
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))


def test_metadados_de_outro_peso_nao_abrem(tmp_path):
    metadados = aj.metadados_do_treino(peso_sha256="d" * 64)
    destino = aj.pacote(tmp_path / "pacote", metadados_dados=metadados)
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))


def test_contrato_calibrado_para_outro_peso_nao_abre(tmp_path):
    """Contrato e peso andam juntos: ROI/imgsz/limiar de um peso nao valem para outro."""
    destino = aj.pacote(tmp_path / "pacote", peso_declarado_no_contrato="c" * 64)
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))


def test_classes_do_contrato_divergentes_do_manifesto_nao_abrem(tmp_path):
    dados = aj.contrato(classes=["normal", "tampa_ausente"])
    metadados = aj.metadados_do_treino(peso_sha256="0" * 64, classes=["normal", "tampa_ausente"])
    destino = aj.pacote(tmp_path / "pacote", contrato_dados=dados, metadados_dados=metadados)
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))


def test_imgsz_do_treino_divergente_do_contrato_nao_abre(tmp_path):
    metadados = aj.metadados_do_treino(peso_sha256="0" * 64, imgsz=320)
    destino = aj.pacote(tmp_path / "pacote", metadados_dados=metadados)
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))


def test_pacote_com_limiar_nao_calibrado_nao_abre(tmp_path):
    """Producao nao decide com limiar provisorio: o pacote sem calibracao e recusado."""
    dados = aj.contrato(calibrado=False)
    destino = aj.pacote(tmp_path / "pacote", contrato_dados=dados)
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))
    import inspect
    assert 'permitir_nao_calibrado' not in inspect.signature(
        ClassificadorDoPacote.abrir).parameters


def test_limitacoes_do_pacote_entram_no_rastro(tmp_path):
    classificador = _abrir(tmp_path)
    medida = classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    limitacoes = [e for e in medida.evidencias if e.grandeza == "limitacao_declarada_pelo_pacote"]
    assert limitacoes and all(e.fonte is None and e.provisorio() for e in limitacoes)


# --------------------------------------------------------------------------- mapas

def test_mapa_de_camera_para_vista_vem_do_contrato(tmp_path):
    classificador = _abrir(tmp_path)
    assert mapa_camera_vista(classificador.contrato) == {"csi": Vista.LATERAL1,
                                                         "usb": Vista.LATERAL2}
    camera = camera_da_vista(classificador.contrato)
    assert camera[Vista.LATERAL2] == "usb"
    roi = roi_por_vista(classificador.contrato)
    assert roi[Vista.LATERAL1] == {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}


def test_vista_repetida_em_duas_cameras_e_erro(tmp_path):
    dados = aj.contrato(vistas={"csi": "lateral1", "usb": "lateral1"})
    destino = aj.pacote(tmp_path / "pacote", contrato_dados=dados)
    classificador = ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))
    with pytest.raises(ErroDeClassificacao):
        camera_da_vista(classificador.contrato)


def test_carregar_o_peso_e_tardio(tmp_path):
    """Import e leitura do peso so acontecem na primeira inferencia."""
    classificador = _abrir(tmp_path, aj.ModeloFalso(caixas=[(0, 0.9)]))
    assert classificador._modelo is None
    classificador.prever(RECORTE, Dominio.TAMPA, Vista.LATERAL1)
    assert classificador._modelo is not None


def test_pacote_sem_checksums_nao_abre(tmp_path):
    destino = aj.pacote(tmp_path / "pacote")
    (destino / "SHA256SUMS").unlink()
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))


def test_manifesto_com_campo_faltando_nao_abre(tmp_path):
    destino = aj.pacote(tmp_path / "pacote")
    caminho = destino / "modelo.json"
    manifesto = json.loads(caminho.read_text())
    del manifesto["imgsz_calibrados"]
    caminho.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2))
    # ate o checksum tem de bater: reescrever o manifesto invalida o pacote inteiro
    with pytest.raises(ErroDeClassificacao):
        ClassificadorDoPacote.abrir(destino, carregador=aj.carregador(aj.ModeloFalso()))
