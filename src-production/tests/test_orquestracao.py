"""Testes da orquestracao: uma cadeia, sem atalho, e as travas de origem.

O decisor falso conta quantas vezes foi chamado — e por onde. Assim o teste prova nao so o
resultado, mas quais vistas chegaram a ser consultadas.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from captura import Alinhamento, ItemCapturado, VistaCapturada
from dominio import Classe, Dominio, Medida, Qualidade, Vista
from conformidade import MOTIVO_CHECK_AUSENTE, MOTIVO_RIG_INCOMPLETO, ConfiguracaoDoRig
from orquestracao import ErroDeOrquestracao, IdentidadeDoRig, executar
from registro import Registro

AGORA = datetime(2026, 9, 13, 1, 0, tzinfo=timezone.utc)
RIG = IdentidadeDoRig(equipamento="pi5-rig", localizacao="bancada-b")


def _item(alinhamentos=None, faltantes=()) -> ItemCapturado:
    alinhamentos = alinhamentos or {}
    vistas = []
    for v in (Vista.TOPO, Vista.LATERAL1, Vista.LATERAL2):
        if v in faltantes:
            continue
        vistas.append(VistaCapturada(vista=v, imagem=f"{v.value}.jpg", capturado_em=AGORA,
                                     alinhamento=alinhamentos.get(v, Alinhamento.OK)))
    return ItemCapturado(item_id="i-1", trigger_em=AGORA, vistas=tuple(vistas))


class DecisorFalso:
    """Devolve a classe pedida por (vista, dominio) e registra quem foi consultado."""

    def __init__(self, respostas=None, defeitos=None, mutar=None):
        self.respostas = respostas or {}
        self.defeitos = defeitos or {}
        self.mutar = mutar
        self.chamadas: list[tuple[str, str]] = []

    def __call__(self, vistacap, dominio):
        self.chamadas.append((vistacap.vista.value, dominio.value))
        if (vistacap.vista, dominio) in self.defeitos:
            classe = self.defeitos[(vistacap.vista, dominio)]
        else:
            classe = self.respostas.get((vistacap.vista, dominio), Classe.NORMAL)
        if classe is None:
            return None
        if self.mutar:
            vistacap, dominio = self.mutar(vistacap, dominio)
        return Medida(vista=vistacap.vista, dominio=dominio, classe=classe, confianca=0.95)


@pytest.fixture()
def reg(tmp_path):
    r = Registro.abrir(tmp_path / "hub.db")
    yield r
    r.fechar()


CHECK_OK = lambda vistacap: (False, None)          # check instrumentado e sem violacao


def test_caminho_completo_grava_item_aprovado(reg):
    """Com o check instrumentado e as duas laterais normais, o item e aprovado."""
    d = DecisorFalso()
    r = executar(_item(), d, reg, RIG, check=CHECK_OK)
    assert r.status == "ok" and r.gravacao == "inserido" and r.aprovado and r.check_presente
    assert sorted(d.chamadas) == [("lateral1", "corpo"), ("lateral1", "tampa"),
                                  ("lateral2", "corpo"), ("lateral2", "tampa")]


def test_topo_nunca_e_consultado_para_classificar(reg):
    """D-23/D-30: o topo nao emite classe. Nenhuma consulta ao decisor sai da vista topo."""
    d = DecisorFalso()
    executar(_item(), d, reg, RIG, check=CHECK_OK)
    assert not [c for c in d.chamadas if c[0] == "topo"]


def test_sem_check_instrumentado_nada_e_aprovado(reg):
    """Evidencia ausente nao vira aprovacao (D-04): sem check, o item fica inconclusivo."""
    r = executar(_item(), DecisorFalso(), reg, RIG)      # check=None
    assert r.status == "inconclusivo" and not r.check_presente
    assert MOTIVO_CHECK_AUSENTE in r.conformidade.motivos


def test_check_que_escala_leva_a_inconclusivo(reg):
    r = executar(_item(), DecisorFalso(), reg, RIG,
                 check=lambda vistacap: (True, "dimensao_violada"))
    assert r.status == "inconclusivo" and "dimensao_violada" in r.conformidade.motivos
    gravado = reg.ler("i-1")
    assert gravado.status_final == "ok"
    assert (gravado.status_tampa, gravado.status_corpo) == ("ok", "ok")


def test_vista_fora_do_alinhamento_nao_e_consultada(reg):
    d = DecisorFalso()
    r = executar(_item(alinhamentos={Vista.LATERAL2: Alinhamento.FORA_DA_TOLERANCIA}), d, reg, RIG)
    assert ("lateral2", "tampa") not in d.chamadas          # evidencia descartada nao vira medicao
    assert r.status == "inconclusivo"
    assert any("vistas_insuficientes" in m for m in r.conformidade.motivos)


def test_decisor_nao_pode_mentir_sobre_a_origem(reg):
    d = DecisorFalso(mutar=lambda vistacap, dominio: (
        VistaCapturada(vista=Vista.LATERAL1, imagem="x.jpg", capturado_em=AGORA,
                       alinhamento=Alinhamento.OK), dominio))
    with pytest.raises(ErroDeOrquestracao):
        executar(_item(alinhamentos={Vista.LATERAL2: Alinhamento.OK}), d, reg, RIG)
    assert reg.contar() == 0                                 # nada foi gravado com origem falsa


def test_sem_decisao_para_um_dominio_fica_inconclusivo(reg):
    d = DecisorFalso(respostas={})
    d.defeitos = {}
    original = DecisorFalso.__call__.__get__(d)

    def so_tampa(vistacap, dominio):
        if dominio is Dominio.CORPO:
            d.chamadas.append((vistacap.vista.value, dominio.value))
            return None
        return original(vistacap, dominio)

    r = executar(_item(), so_tampa, reg, RIG)
    assert r.status == "inconclusivo"
    assert reg.ler("i-1").status_final == "inconclusivo"


def test_defeito_em_uma_lateral_grava_defeito(reg):
    d = DecisorFalso(defeitos={(Vista.LATERAL1, Dominio.TAMPA): Classe.TAMPA_AUSENTE})
    r = executar(_item(), d, reg, RIG, check=CHECK_OK)
    assert r.status == "defeito"
    assert reg.ler("i-1").status_tampa == "defeito"


def test_replay_do_mesmo_item_nao_duplica(reg):
    d = DecisorFalso()
    assert executar(_item(), d, reg, RIG, check=CHECK_OK).gravacao == "inserido"
    assert executar(_item(), DecisorFalso(), reg, RIG, check=CHECK_OK).gravacao == "repetido"
    assert reg.contar() == 1


def test_identidade_do_rig_e_obrigatoria():
    with pytest.raises(ErroDeOrquestracao):
        IdentidadeDoRig(equipamento="  ", localizacao="bancada-b")


def test_rig_reduzido_nao_aprova_na_cadeia(reg):
    d = DecisorFalso()
    r = executar(_item(faltantes=(Vista.LATERAL2,)), d, reg,
                 RIG, config=ConfiguracaoDoRig(vistas_decisorias=(Vista.LATERAL1,)))
    assert r.status == "inconclusivo" and MOTIVO_RIG_INCOMPLETO in r.conformidade.motivos


def test_vista_ausente_continua_declarada_no_evento(reg):
    d = DecisorFalso()
    executar(_item(faltantes=(Vista.TOPO,)), d, reg, RIG, check=CHECK_OK)
    linhas = reg._cx.execute("SELECT vista, papel FROM inspecao_vista WHERE item_id='i-1'").fetchall()
    assert [r["vista"] for r in linhas].count("topo") == 0    # nao capturada: ausencia registrada
    assert reg.ler("i-1").qualidade_registro == "completo"    # as duas laterais foram medidas
