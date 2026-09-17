"""Testes da orquestracao: a cadeia inteira passando pelo Decisor REAL da D-30.

O ponto destes testes: as pontas nao podem ser testadas cada uma com o seu dublê. Aqui o
classificador falso entra pelo `Decisor` de producao (`decisao.Decisor`), e o que se assere inclui
o que so o caminho real produz; o papel `fallback` gravado no registro, por exemplo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import get_type_hints

import cv2
import numpy as np
import pytest
from captura import Alinhamento, ItemCapturado, VistaCapturada
from conformidade import MOTIVO_CHECK_AUSENTE, MOTIVO_RIG_INCOMPLETO, ConfiguracaoDoRig
from decisao import ErroDeDecisao
from dominio import Classe, Dominio, Evidencia, Medida, Origem, Papel, Vista
from orquestracao import ErroDeOrquestracao, IdentidadeDoRig, executar
from registro import Registro

AGORA = datetime(2026, 9, 13, 4, 0, tzinfo=timezone.utc)
RIG = IdentidadeDoRig(equipamento="pi5-rig", localizacao="bancada-b")
ROI = (0.0, 0.0, 1.0, 1.0)  # recorte do quadro inteiro: o teste nao mede ROI
def CHECK_OK(vistacap):
    return (False, None)  # check instrumentado, sem violacao


class ClassificadorFalso:
    """Preve por dominio. `sem_decisao` lista dominios em que ele nao consegue decidir."""

    identificacao = "falso-v1"

    def __init__(
        self,
        defeitos=None,
        sem_decisao=(),
        mentir_vista: bool = False,
        mentir_dominio: Dominio | None = None,
    ):
        self.defeitos = defeitos or {}
        self.sem_decisao = set(sem_decisao)
        self.mentir_vista = mentir_vista
        self.mentir_dominio = mentir_dominio
        self.chamadas: list[tuple[str, str]] = []

    def prever(self, recorte, dominio: Dominio, vista: Vista) -> Medida | None:
        self.chamadas.append((vista.value, dominio.value))
        if dominio in self.sem_decisao:
            return None
        classe = self.defeitos.get(dominio, Classe.NORMAL)
        return Medida(
            vista=Vista.TOPO if self.mentir_vista else vista,
            dominio=self.mentir_dominio or dominio,
            classe=classe,
            confianca=0.95,
        )


class MedidorFalso:
    identificacao = "geo-falso"

    def __init__(self):
        self.chamadas = 0

    def medir(self, recorte):
        self.chamadas += 1
        return (
            Evidencia(
                grandeza="tilt_graus",
                valor=1.2,
                unidade="grau",
                origem=Origem.GEOMETRIA,
                papel=Papel.AUXILIAR,
                metodo="fake-v1",
            ),
        )


def _imagem(tmp_path, nome: str, tom: int = 40):
    pasta = tmp_path / "i-1"
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{nome}.jpg"
    im = np.full((48, 64), tom, np.uint8)
    im[10:30, 10:40] = 200
    cv2.imwrite(str(caminho), im)
    return caminho


def _item(
    tmp_path, alinhamentos=None, faltantes=(), duplicadas=(), tons=(40, 60, 80)
) -> ItemCapturado:
    alinhamentos = alinhamentos or {}
    vistas = []
    for v, tom in zip((Vista.TOPO, Vista.LATERAL1, Vista.LATERAL2), tons, strict=False):
        if v in faltantes:
            continue
        vistas.append(
            VistaCapturada(
                vista=v,
                imagem=_imagem(tmp_path, v.value, tom),
                capturado_em=AGORA,
                alinhamento=alinhamentos.get(v, Alinhamento.OK),
                no_janela=True,
                duplicada=v in duplicadas,
            )
        )
    return ItemCapturado(item_id="i-1", trigger_em=AGORA, vistas=tuple(vistas))


@pytest.fixture()
def reg(tmp_path):
    r = Registro.abrir(tmp_path / "hub.db")
    yield r
    r.fechar()


def test_caminho_completo_grava_item_aprovado(tmp_path, reg):
    c = ClassificadorFalso()
    r = executar(_item(tmp_path), c, reg, RIG, roi=ROI, check=CHECK_OK)
    assert (
        r.status == "ok"
        and r.gravacao == "inserido"
        and r.aprovado
        and r.check_presente
    )
    assert sorted(c.chamadas) == [
        ("lateral1", "corpo"),
        ("lateral1", "tampa"),
        ("lateral2", "corpo"),
        ("lateral2", "tampa"),
    ]
    g = reg.ler("i-1")
    assert (g.status_tampa, g.status_corpo, g.status_final) == ("ok", "ok", "ok")


def test_topo_nunca_e_consultado_para_classificar(tmp_path, reg):
    c = ClassificadorFalso()
    executar(_item(tmp_path), c, reg, RIG, roi=ROI, check=CHECK_OK)
    assert not [
        x for x in c.chamadas if x[0] == "topo"
    ]  # com 3 vistas seriam 6 se o topo classificasse


def test_sem_recorte_declarado_nao_decide(tmp_path, reg):
    """Regiao nao declarada = medicao da area errada: para antes de gravar."""
    with pytest.raises(ErroDeOrquestracao):
        executar(_item(tmp_path), ClassificadorFalso(), reg, RIG, check=CHECK_OK)
    assert reg.contar() == 0


def test_sem_check_instrumentado_nada_e_aprovado(tmp_path, reg):
    r = executar(_item(tmp_path), ClassificadorFalso(), reg, RIG, roi=ROI)
    assert r.status == "inconclusivo" and not r.check_presente
    assert MOTIVO_CHECK_AUSENTE in r.conformidade.motivos
    # o contrato inteiro: o que foi GRAVADO tem de contar a mesma historia da conformidade
    linha = reg._cx.execute(
        "SELECT status_final, motivo_inconclusivo FROM item"
    ).fetchone()
    assert linha["status_final"] == "inconclusivo", (
        "item nao aprovado saiu aprovado no banco"
    )
    assert linha["motivo_inconclusivo"] == MOTIVO_CHECK_AUSENTE


def test_check_que_escala_leva_a_inconclusivo(tmp_path, reg):
    r = executar(
        _item(tmp_path),
        ClassificadorFalso(),
        reg,
        RIG,
        roi=ROI,
        check=lambda vistacap: (True, "dimensao_violada"),
    )
    assert r.status == "inconclusivo" and "dimensao_violada" in r.conformidade.motivos
    linha = reg._cx.execute(
        "SELECT status_final, motivo_inconclusivo FROM item"
    ).fetchone()
    assert linha["status_final"] == "inconclusivo", (
        "check escalonado saiu aprovado no banco"
    )
    assert linha["motivo_inconclusivo"] == "dimensao_violada"


def test_vista_fora_do_alinhamento_nao_e_consultada(tmp_path, reg):
    c = ClassificadorFalso()
    r = executar(
        _item(tmp_path, alinhamentos={Vista.LATERAL2: Alinhamento.FORA_DA_TOLERANCIA}),
        c,
        reg,
        RIG,
        roi=ROI,
        check=CHECK_OK,
    )
    assert len(c.chamadas) == 2  # so a lateral1 utilizavel
    assert r.status == "inconclusivo"


def test_classificador_que_mente_sobre_a_origem_para_a_execucao(tmp_path, reg):
    c = ClassificadorFalso(mentir_vista=True)
    with pytest.raises(ErroDeDecisao):
        executar(_item(tmp_path), c, reg, RIG, roi=ROI, check=CHECK_OK)
    assert reg.contar() == 0  # nada gravado com origem falsa


def test_dominio_sem_decisao_vira_fallback_e_escala(tmp_path, reg):
    """None do classificador aciona a D-30: inconclusivo, papel `fallback` GRAVADO no registro."""
    c = ClassificadorFalso(sem_decisao=(Dominio.CORPO,))
    r = executar(_item(tmp_path), c, reg, RIG, roi=ROI, check=CHECK_OK)
    assert r.status == "inconclusivo"
    papeis = {
        x["vista"]: x["papel"]
        for x in reg._cx.execute(
            "SELECT vista, papel FROM inspecao_vista WHERE item_id='i-1' AND dominio='corpo'"
        )
    }
    assert papeis and set(papeis.values()) == {"fallback"}


def test_defeito_em_uma_lateral_grava_defeito(tmp_path, reg):
    c = ClassificadorFalso(defeitos={Dominio.TAMPA: Classe.TAMPA_AUSENTE})
    r = executar(_item(tmp_path), c, reg, RIG, roi=ROI, check=CHECK_OK)
    assert r.status == "defeito" and reg.ler("i-1").status_tampa == "defeito"


def test_evidencia_geometrica_acompanha_a_medida(tmp_path, reg):
    """A D-30 manda a geometria entrar como rastro: aqui ela chega ate a medida do evento."""
    r = executar(
        _item(tmp_path),
        ClassificadorFalso(),
        reg,
        RIG,
        roi=ROI,
        check=CHECK_OK,
        medidor=MedidorFalso(),
    )
    grandezas = {e.grandeza for m in r.medidas for e in m.evidencias}
    assert grandezas == {"tilt_graus"}


def test_replay_do_mesmo_item_nao_duplica(tmp_path, reg):
    assert (
        executar(
            _item(tmp_path), ClassificadorFalso(), reg, RIG, roi=ROI, check=CHECK_OK
        ).gravacao
        == "inserido"
    )
    assert (
        executar(
            _item(tmp_path), ClassificadorFalso(), reg, RIG, roi=ROI, check=CHECK_OK
        ).gravacao
        == "repetido"
    )
    assert reg.contar() == 1


def test_identidade_do_rig_e_obrigatoria():
    with pytest.raises(ErroDeOrquestracao):
        IdentidadeDoRig(equipamento="  ", localizacao="bancada-b")


def test_rig_reduzido_nao_aprova_na_cadeia(tmp_path, reg):
    r = executar(
        _item(tmp_path, faltantes=(Vista.LATERAL2,)),
        ClassificadorFalso(),
        reg,
        RIG,
        roi=ROI,
        config=ConfiguracaoDoRig(vistas_decisorias=(Vista.LATERAL1,)),
        check=CHECK_OK,
    )
    assert (
        r.status == "inconclusivo" and MOTIVO_RIG_INCOMPLETO in r.conformidade.motivos
    )


def test_vista_duplicada_nao_e_consultada_e_invalida_o_item(tmp_path, reg):
    c = ClassificadorFalso()
    executar(
        _item(tmp_path, duplicadas=(Vista.LATERAL2,)),
        c,
        reg,
        RIG,
        roi=ROI,
        check=CHECK_OK,
    )
    assert len(c.chamadas) == 2
    g = reg.ler("i-1")
    assert (
        g.qualidade_registro == "invalido"
        and g.motivo_inconclusivo == "vista_duplicada"
    )


def test_evidencia_geometrica_chega_ao_banco(tmp_path, reg):
    """Fecha o elo: o rastro que a D-30 manda registrar tem de existir NO BANCO, nao so na medida."""
    executar(
        _item(tmp_path),
        ClassificadorFalso(),
        reg,
        RIG,
        roi=ROI,
        check=CHECK_OK,
        medidor=MedidorFalso(),
    )
    linhas = reg._cx.execute("SELECT grandeza, papel, metodo FROM evidencia").fetchall()
    assert [(x["grandeza"], x["papel"]) for x in linhas] == [
        ("tilt_graus", "auxiliar")
    ] * 4


def test_hash_da_evidencia_e_gravado_por_vista(tmp_path, reg):
    executar(_item(tmp_path), ClassificadorFalso(), reg, RIG, roi=ROI, check=CHECK_OK)
    linhas = reg._cx.execute(
        "SELECT vista, sha256_evidencia FROM inspecao_vista"
    ).fetchall()
    assert all(len(x["sha256_evidencia"]) == 64 for x in linhas)
    assert len({x["sha256_evidencia"] for x in linhas}) == 3  # uma prova por vista


def test_geometria_e_medida_uma_vez_por_vista(tmp_path, reg):
    """Duas laterais = duas medicoes, nao quatro: a medicao e da vista, nao do dominio."""
    medidor = MedidorFalso()
    executar(
        _item(tmp_path),
        ClassificadorFalso(),
        reg,
        RIG,
        roi=ROI,
        check=CHECK_OK,
        medidor=medidor,
    )
    assert medidor.chamadas == 2
    # o rastro continua nas duas linhas de cada lateral: duas decisoes sustentadas pela mesma medida
    por_vista = {}
    for x in reg._cx.execute(
        "SELECT v.vista, COUNT(*) AS n FROM evidencia e"
        " JOIN inspecao_vista v ON v.id = e.inspecao_vista_id GROUP BY v.vista"
    ):
        por_vista[x["vista"]] = x["n"]
    assert por_vista == {"lateral1": 2, "lateral2": 2}


def test_anotacoes_de_criar_classificador_resolvem():
    from orquestracao import criar_classificador

    assert get_type_hints(criar_classificador)["artefato"]
