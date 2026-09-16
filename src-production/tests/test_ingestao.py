"""Testes da ingestao de serie do rig -> item do registro.

O que estes testes protegem:
  * a serie vira item COM as vistas associadas por mapa DECLARADO (nao por ordem de arquivo);
  * a evidencia e copiada para a raiz do hub com sha256 conferido (a prova viaja com o registro);
  * serie parcial declara a vista que falta em vez de virar item "completo";
  * sem janela declarada nada e utilizavel (fail-closed), e o item sai inconclusivo;
  * camera fora do mapa / vista repetida / serie sem manifesto sao RECUSADAS com motivo.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import pytest
from dominio import Classe, Dominio, Medida, Qualidade, Vista
from ingerir_serie import _copia_para_evidencia, ingerir
from mapeamento_rig import ErroDeMapeamento, fotos_do_manifesto, ler_mapa
from registro import Registro

#: mapa do teste: cameras GENERICAS (o repositorio nao carrega nome de camera da instalacao)
MAPA_DO_TESTE = "camera-1=lateral1,camera-2=lateral2,camera-3=topo"


class ClassificadorFalso:
    """Devolve sempre a mesma classe: o teste e da INGESTAO, nao do modelo."""

    identificacao = "classificador-falso-de-teste"

    def prever(self, recorte, dominio: Dominio, vista: Vista):
        return Medida(
            vista=vista,
            dominio=dominio,
            classe=Classe.NORMAL,
            confianca=0.99,
            qualidade=Qualidade.OK,
        )


def _jpeg(caminho: Path, tom: int = 128) -> Path:
    imagem = np.full((64, 64, 3), tom, dtype=np.uint8)
    cv2.imwrite(str(caminho), imagem)
    return caminho


@pytest.fixture()
def serie(tmp_path) -> Path:
    """Serie completa com as tres cameras do rig e manifesto com bytes."""
    pasta = tmp_path / "series-3-cameras" / "20260914-191045-472"
    pasta.mkdir(parents=True)
    fontes = []
    for indice, (camera, nome) in enumerate(
        (
            ("camera-1", "camera-1.jpg"),
            ("camera-2", "camera-2.jpg"),
            ("camera-3", "camera-3.jpg"),
        )
    ):
        caminho = _jpeg(pasta / nome, tom=40 * (indice + 1))
        os.utime(caminho, (1789417845.97, 1789417845.97))
        fontes.append({"camera": camera, "nome": nome, "bytes": caminho.stat().st_size})
    (pasta / "manifest.json").write_text(
        json.dumps(
            {
                "serie": pasta.name,
                "capturado_em": "2026-09-14 19:10:45",
                "trigger_n": 712,
                "trigger_em": 1789417845.97,
                "captura_inicio_epoch": 1789417845.97,
                "captura_fim_epoch": 1789417850.67,
                "delay_trigger_ate_fim_ms": 4699,
                "fontes": fontes,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return pasta


def _banco(tmp_path) -> Path:
    caminho = tmp_path / "hub.db"
    registro = Registro.abrir(caminho)
    registro._cx.execute(
        "INSERT INTO lote (lote_id, data_inicio) VALUES ('L1','2026-09-15')"
    )
    registro._cx.commit()
    registro.fechar()
    return caminho


def test_ingere_serie_completa_com_as_tres_vistas(serie, tmp_path):
    banco = _banco(tmp_path)
    resultado = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )

    assert resultado["serie"] == "20260914-191045-472"
    assert resultado["item_id"].startswith("L1-"), resultado["item_id"]
    assert sorted(resultado["vistas"]) == ["lateral1", "lateral2", "topo"]
    assert resultado["faltantes"] == []

    # a evidencia foi COPIADA para a raiz do hub, com hash conferido contra o original
    for camera, prova in resultado["evidencias"].items():
        alvo = Path(prova["caminho"])
        assert alvo.is_file() and str(alvo).startswith(str(tmp_path))
        esperado = hashlib.sha256((serie / alvo.name).read_bytes()).hexdigest()
        assert prova["sha256"] == esperado, camera

    # e o registro guardou: item + 3 vistas + hash
    registro = Registro.abrir(banco)
    try:
        linhas = registro._cx.execute(
            "SELECT v.vista, v.dominio, v.caminho_evidencia, v.sha256_evidencia FROM inspecao_vista v"
            " JOIN item i ON i.item_id = v.item_id WHERE i.item_id = ? ORDER BY v.vista, v.dominio",
            (resultado["item_id"],),
        ).fetchall()
    finally:
        registro.fechar()

    # o esquema tem uma linha por (vista, dominio): as vistas DISTINTAS sao as tres do rig...
    assert sorted({l["vista"] for l in linhas}) == ["lateral1", "lateral2", "topo"]
    # ...e cada vista tem pelo menos uma linha com a prova (caminho + hash) preenchida
    com_prova = {
        l["vista"] for l in linhas if l["caminho_evidencia"] and l["sha256_evidencia"]
    }
    assert com_prova == {"lateral1", "lateral2", "topo"}, com_prova


def test_a_ordem_do_manifesto_nao_define_a_vista(serie, tmp_path):
    """O mapa e a associacao valem; trocar a ORDEM das fontes nao pode trocar vista."""
    banco = _banco(tmp_path)
    manifesto = json.loads((serie / "manifest.json").read_text())
    manifesto["fontes"] = list(reversed(manifesto["fontes"]))
    (serie / "manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")

    resultado = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )
    assert resultado["evidencias"]["camera-1"]["vista"] == "lateral1"
    assert resultado["evidencias"]["camera-3"]["vista"] == "topo"


def test_serie_parcial_declara_a_vista_faltante(serie, tmp_path):
    banco = _banco(tmp_path)
    manifesto = json.loads((serie / "manifest.json").read_text())
    manifesto["fontes"] = [f for f in manifesto["fontes"] if f["camera"] != "camera-3"]
    (serie / "manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")
    (serie / "camera-3.jpg").unlink()

    resultado = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )
    assert resultado["faltantes"] == ["topo"]
    assert "topo" not in resultado["vistas"]


def test_sem_janela_declarada_nada_e_utilizavel(serie, tmp_path):
    """Fail-closed: janela nao declarada -> nenhuma vista utilizavel, item inconclusivo."""
    banco = _banco(tmp_path)
    resultado = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=None,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )
    assert resultado["vistas_utilizaveis"] == []
    assert resultado["status"] == "inconclusivo"


def test_alinhamento_nao_verificado_nao_vira_evidencia(serie, tmp_path):
    banco = _banco(tmp_path)
    resultado = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=False,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )
    assert resultado["alinhamento"] == "nao_verificado"
    assert resultado["vistas_utilizaveis"] == []


def test_camera_fora_do_mapa_e_recusada(serie, tmp_path):
    manifesto = json.loads((serie / "manifest.json").read_text())
    manifesto["fontes"][0]["camera"] = "camera-nova"
    with pytest.raises(ErroDeMapeamento, match="camera-nova"):
        fotos_do_manifesto(manifesto, ler_mapa(MAPA_DO_TESTE))


def test_mapa_ausente_para_a_ingestao(tmp_path):
    """Sem mapa declarado a ingestao PARA (o repositorio nao tem default com nome de camera)."""
    with pytest.raises(ErroDeMapeamento, match="nao declarado"):
        ler_mapa(None, arquivo=tmp_path / "nao-existe.json")


def test_vista_repetida_no_mapa_e_erro():
    with pytest.raises(ErroDeMapeamento, match="repetida"):
        ler_mapa("c1=lateral1,c2=lateral1,c3=topo")


def test_vista_desconhecida_no_mapa_e_erro():
    with pytest.raises(ErroDeMapeamento, match="desconhecida"):
        ler_mapa("c1=frente")


def test_duas_cameras_para_a_mesma_vista_no_manifesto_e_erro():
    manifesto = {
        "fontes": [
            {"camera": "camera-1", "nome": "a.jpg"},
            {"camera": "camera-2", "nome": "b.jpg"},
        ]
    }
    mapa = {"camera-1": Vista.LATERAL1, "camera-2": Vista.LATERAL1}
    with pytest.raises(ErroDeMapeamento):
        fotos_do_manifesto(manifesto, mapa)


def test_serie_sem_manifesto_e_recusada(tmp_path):
    pasta = tmp_path / "sem-manifesto"
    pasta.mkdir()
    with pytest.raises(ErroDeMapeamento, match="manifest.json"):
        ingerir(
            pasta,
            lote="L1",
            db=_banco(tmp_path),
            roi=(0.0, 0.0, 1.0, 1.0),
            janela_ms=800,
            alinhamento_declarado=True,
            classificador=ClassificadorFalso(),
            mapa_texto=MAPA_DO_TESTE,
        )


def test_vincula_o_evento_de_gatilho_ao_item(serie, tmp_path):
    banco = _banco(tmp_path)
    registro = Registro.abrir(banco)
    try:
        gatilho = registro.registrar_gatilho(
            datetime.now(UTC).isoformat(timespec="seconds"),
            "aceito",
            fonte="e18_d80nk",
            motivo="teste de ingestao",
        )
    finally:
        registro.fechar()

    resultado = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
        gatilho_id=gatilho,
    )

    registro = Registro.abrir(banco)
    try:
        linha = registro._cx.execute(
            "SELECT item_id FROM evento_gatilho WHERE id = ?", (gatilho,)
        ).fetchone()
    finally:
        registro.fechar()
    assert linha["item_id"] == resultado["item_id"]


def test_id_sai_da_sequencia_do_lote(serie, tmp_path):
    """A sequencia e ancorada no que FOI GRAVADO: dois itens ingeridos nao repetem id.

    (Reservar duas vezes sem gravar devolve o mesmo numero; de proposito: reservar sem escrever nao
    consome identidade, e e o que impede id "gasto" por tentativa que falhou.)
    """
    banco = _banco(tmp_path)
    primeiro = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )
    segundo = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )

    assert primeiro["item_id"] != segundo["item_id"]
    assert primeiro["item_id"].endswith("000001") and segundo["item_id"].endswith(
        "000002"
    )


def test_manifesto_rejeita_nome_de_foto_com_traversal():
    with pytest.raises(
        ErroDeMapeamento, match="nome.*seguro|caminho.*invalido|traversal"
    ):
        fotos_do_manifesto(
            {"fontes": [{"camera": "camera-1", "nome": "../../fora.jpg"}]},
            {"camera-1": Vista.LATERAL1},
        )


def test_foto_fora_da_janela_nao_e_utilizavel(serie, tmp_path):
    banco = _banco(tmp_path)
    os.utime(serie / "camera-1.jpg", (1789417850.0, 1789417850.0))
    resultado = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
    )
    assert "lateral1" not in resultado["vistas_utilizaveis"]
    assert "lateral1" in resultado["fora_da_janela"]


# ---------------------------------------------------------------- colisao de evidencia


def test_serie_homonima_nao_sobrescreve_evidencia_de_item_anterior(serie, tmp_path):
    """Duas series com o MESMO basename nao podem apagar a prova da primeira.

    O banco guarda o sha256 do arquivo, nao uma copia: sobrescrever os bytes faria o item ja
    registrado apontar para conteudo que nao e o dele.
    """
    evidencias = tmp_path / "ev"
    primeiro = ingerir(
        serie,
        lote="L1",
        db=banco,
        roi=(0.0, 0.0, 1.0, 1.0),
        janela_ms=800,
        alinhamento_declarado=True,
        classificador=ClassificadorFalso(),
        mapa_texto=MAPA_DO_TESTE,
        evidencias=evidencias,
    )
    alvo = Path(primeiro["evidencias"]["camera-1"]["caminho"])
    antes = hashlib.sha256(alvo.read_bytes()).hexdigest()
    assert antes == primeiro["evidencias"]["camera-1"]["sha256"]

    # mesma pasta de serie (mesmo basename), bytes diferentes
    _jpeg(serie / "camera-1.jpg", tom=200)
    os.utime(serie / "camera-1.jpg", (1789417845.97, 1789417845.97))

    with pytest.raises(ErroDeMapeamento, match="colisao de evidencia"):
        ingerir(
            serie,
            lote="L1",
            db=banco,
            roi=(0.0, 0.0, 1.0, 1.0),
            janela_ms=800,
            alinhamento_declarado=True,
            classificador=ClassificadorFalso(),
            mapa_texto=MAPA_DO_TESTE,
            evidencias=evidencias,
        )

    assert hashlib.sha256(alvo.read_bytes()).hexdigest() == antes, (
        "a prova do item 1 foi alterada"
    )
    registro = Registro.abrir(banco)
    try:
        gravado = registro.ler(primeiro["item_id"])
    finally:
        registro.fechar()
    referencia = next(r for r in gravado.referencias if r.caminho == str(alvo))
    assert referencia.sha256 == antes, "sha do banco divergiu do arquivo"


def test_reingestao_do_mesmo_conteudo_e_idempotente(serie, tmp_path):
    """Mesmos bytes no mesmo destino: reaproveita em vez de recusar (replay nao vira erro)."""
    banco = _banco(tmp_path)
    evidencias = tmp_path / "ev"
    alvo = (evidencias / "series" / serie.name / "camera-1.jpg").resolve()
    alvo.parent.mkdir(parents=True, exist_ok=True)
    with alvo.open("wb") as fh:
        fh.write((serie / "camera-1.jpg").read_bytes())
    assert _copia_para_evidencia(serie, alvo.parent, "camera-1.jpg") == alvo
