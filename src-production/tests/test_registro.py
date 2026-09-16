"""Testes do registro: idempotencia, conflito, regra D-04 e invariantes do proprio banco.

Cada teste falha se a regra for desfeita; inclusive quando a "resposta errada" seria gravar.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest
from dominio import Classe, Dominio, Evento, Medida, Papel, Qualidade, Vista
from registro import (
    ConflitoDeItem,
    EventoInvalido,
    Registro,
    estado_da_classe,
    papel_da_linha,
    qualidade_registro,
    status_final,
)

AGORA = datetime(2026, 9, 12, 23, 40, tzinfo=timezone.utc)


def _medida(vista, dominio, classe, conf=0.95, qualidade=Qualidade.OK):
    return Medida(
        vista=vista, dominio=dominio, classe=classe, confianca=conf, qualidade=qualidade
    )


def _evento(item_id="i-001", medidas=None, vistas=None, classe=Classe.NORMAL) -> Evento:
    if medidas is None:
        medidas = (
            _medida(Vista.LATERAL1, Dominio.TAMPA, classe),
            _medida(Vista.LATERAL2, Dominio.TAMPA, classe),
            _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
            _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
        )
    return Evento(
        item_id=item_id,
        capturado_em=AGORA,
        equipamento="pi5-rig",
        localizacao="bancada",
        vistas=vistas or (Vista.TOPO,),
        medidas=medidas,
        status=classe,
    )


@pytest.fixture()
def reg(tmp_path):
    r = Registro.abrir(tmp_path / "hub.db")
    yield r
    r.fechar()


# ---------------------------------------------------------------- mapeamentos


def test_estado_da_classe():
    assert estado_da_classe(Classe.NORMAL) == "ok"
    assert estado_da_classe(Classe.TAMPA_AUSENTE) == "defeito"
    assert estado_da_classe(Classe.DEFORMIDADE) == "defeito"
    assert estado_da_classe(Classe.INCONCLUSIVO) == "inconclusivo"


def test_papel_do_topo_nunca_decide():
    m = _medida(Vista.TOPO, Dominio.CORPO, Classe.NORMAL)
    assert papel_da_linha(Vista.TOPO, m) is Papel.AUXILIAR
    assert papel_da_linha(Vista.LATERAL1, m) is Papel.DECIDE
    inconclusiva = _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.INCONCLUSIVO, conf=0.0)
    assert papel_da_linha(Vista.LATERAL2, inconclusiva) is Papel.FALLBACK


def test_status_final_prioriza_defeito_e_protege_inconclusivo():
    assert status_final({Dominio.TAMPA: "ok", Dominio.CORPO: "ok"}, False) == "ok"
    assert (
        status_final({Dominio.TAMPA: "defeito", Dominio.CORPO: "ok"}, False)
        == "defeito"
    )
    assert (
        status_final({Dominio.TAMPA: "ok", Dominio.CORPO: "inconclusivo"}, False)
        == "inconclusivo"
    )
    assert (
        status_final({Dominio.TAMPA: "ok", Dominio.CORPO: "ok"}, True) == "inconclusivo"
    )


def test_qualidade_do_registro():
    assert qualidade_registro(2) == "completo"
    assert qualidade_registro(1) == "parcial_1_vista_faltante"
    assert qualidade_registro(0) == "evidencia_insuficiente"


# ---------------------------------------------------------------- esquema


def test_catalogo_de_referencia_aponta_para_as_laterais(reg):
    linhas = {
        r["codigo"]: r
        for r in reg._cx.execute(
            "SELECT codigo, classe, dominio, severidade, vista_esperada FROM taxonomia_defeito"
        )
    }
    assert (
        len(linhas) == 8
    )  # D-31: entraram TAMPA_DEFEITO, TAMPA_DANIFICADA, TAMPA_ABERTA
    for codigo in (
        "TAMPA_AUSENTE",
        "TAMPA_DEFEITO",
        "TAMPA_MAL_ROSQUEADA",
        "TAMPA_DANIFICADA",
        "TAMPA_ABERTA",
    ):
        assert linhas[codigo]["vista_esperada"] == "lateral1,lateral2"  # D-23/D-30
        assert linhas[codigo]["dominio"] == "tampa"
    assert linhas["CORPO_DEFORMADO_SEVERO"]["classe"] == "deformidade"
    assert linhas["CORPO_DEFORMADO_SEVERO"]["severidade"] == "critico"
    assert linhas["CORPO_DEFORMADO_LEVE"]["severidade"] == "minor"
    assert linhas["ERRO_PROCESSAMENTO"]["classe"] is None  # categoria tecnica


def test_banco_recusa_topo_decidindo(reg):
    reg._cx.execute("INSERT INTO item (item_id, timestamp_trigger) VALUES ('x', 't')")
    with pytest.raises(sqlite3.IntegrityError):
        reg._cx.execute(
            "INSERT INTO inspecao_vista (item_id, vista, dominio, papel) VALUES ('x','topo','tampa','decide')"
        )


def test_banco_recusa_decidir_sem_dominio(reg):
    reg._cx.execute("INSERT INTO item (item_id, timestamp_trigger) VALUES ('y', 't')")
    with pytest.raises(sqlite3.IntegrityError):
        reg._cx.execute(
            "INSERT INTO inspecao_vista (item_id, vista, papel) VALUES ('y','lateral1','decide')"
        )


# ---------------------------------------------------------------- escrita


def test_round_trip_item_completo(reg):
    assert reg.registrar(_evento()) == "inserido"
    g = reg.ler("i-001")
    assert g.status_tampa == "ok" and g.status_corpo == "ok" and g.status_final == "ok"
    assert g.qualidade_registro == "completo"
    assert [l.papel for l in g.vistas if l.vista is Vista.TOPO] == [Papel.AUXILIAR]


def test_reenvio_da_mesma_evidencia_nao_duplica(reg):
    e = _evento()
    assert reg.registrar(e) == "inserido"
    assert reg.registrar(e) == "repetido"
    assert reg.contar() == 1
    assert reg._cx.execute("SELECT COUNT(*) FROM inspecao_vista").fetchone()[0] == 5


def test_evidencia_divergente_no_mesmo_item_da_conflito(reg):
    reg.registrar(_evento())
    outra = _evento(
        medidas=(
            _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
            _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
        )
    )
    with pytest.raises(ConflitoDeItem):
        reg.registrar(outra)
    assert reg.ler("i-001").status_tampa == "ok"  # nada foi sobrescrito
    assert reg.contar() == 1


def test_defeito_em_um_dominio_reprova_e_marca_discordancia(reg):
    medidas = (
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.DEFEITO_TAMPA),
        _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.NORMAL),
        _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
        _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
    )
    reg.registrar(_evento(medidas=medidas))
    g = reg.ler("i-001")
    assert g.status_tampa == "defeito" and g.status_final == "defeito"
    assert (
        reg._cx.execute(
            "SELECT discordancia_lateral FROM item WHERE item_id='i-001'"
        ).fetchone()[0]
        == 1
    )


def test_vista_lateral_faltante_vira_inconclusivo(reg):
    medidas = (_medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),)
    reg.registrar(_evento(medidas=medidas))
    g = reg.ler("i-001")
    assert g.status_final == "inconclusivo"
    assert g.qualidade_registro == "parcial_1_vista_faltante"
    assert g.motivo_inconclusivo == "vista_lateral_ausente"


def test_evento_sem_identidade_e_recusado(reg):
    with pytest.raises(EventoInvalido):
        reg.registrar(
            Evento(
                item_id="  ",
                capturado_em=AGORA,
                equipamento="pi5",
                localizacao="b",
                vistas=(Vista.LATERAL1,),
                medidas=(),
                status=Classe.NORMAL,
            )
        )


def test_vista_sem_medida_grava_inconclusivo_e_nao_aprova(reg):
    """Capturada e nao decidida nao e evidencia de nada (D-04)."""
    reg.registrar(
        Evento(
            item_id="i-002",
            capturado_em=AGORA,
            equipamento="pi5",
            localizacao="b",
            vistas=(Vista.LATERAL1,),
            medidas=(),
            status=Classe.NORMAL,
        )
    )
    g = reg.ler("i-002")
    assert g.status_final == "inconclusivo"
    assert g.qualidade_registro == "evidencia_insuficiente"
    assert [(l.vista, l.papel, l.status) for l in g.vistas] == [
        (Vista.LATERAL1, Papel.AUXILIAR, "inconclusivo")
    ]


def test_codigo_do_catalogo_e_gravado_quando_o_mapa_e_1_para_1(reg):
    medidas = (
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
        _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
    )
    reg.registrar(_evento(medidas=medidas))
    codigos = [
        r[0]
        for r in reg._cx.execute(
            "SELECT codigo_defeito FROM inspecao_vista WHERE item_id='i-001' AND vista LIKE 'lateral%'"
        )
    ]
    assert codigos == ["TAMPA_AUSENTE", "TAMPA_AUSENTE"]


def test_dominio_com_uma_lateral_nao_e_aprovado(reg):
    """D-04/D-29: vista unica nao sustenta aprovacao do dominio."""
    medidas = (
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),
        _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
        _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
    )
    reg.registrar(_evento(medidas=medidas))
    g = reg.ler("i-001")
    assert g.status_tampa == "inconclusivo"  # so uma lateral na tampa
    assert g.status_corpo == "ok"  # as duas laterais no corpo
    assert g.status_final == "inconclusivo"


def test_vista_fora_da_janela_marca_timestamp_divergente(reg):
    """DAT-03: divergencia de timestamp tem estado proprio e nao vira 'completo'."""
    from dominio import Vista as V

    medidas = (
        _medida(V.LATERAL1, Dominio.TAMPA, Classe.NORMAL),
        _medida(V.LATERAL2, Dominio.TAMPA, Classe.NORMAL),
        _medida(V.LATERAL1, Dominio.CORPO, Classe.NORMAL),
        _medida(V.LATERAL2, Dominio.CORPO, Classe.NORMAL),
    )
    reg.registrar(_evento(medidas=medidas), fora_da_janela=(V.LATERAL2,))
    g = reg.ler("i-001")
    assert g.qualidade_registro == "timestamp_divergente"
    assert g.motivo_inconclusivo == "timestamp_divergente"


def test_qualidade_distinta_para_cada_caso():
    from registro import qualidade_registro as q

    assert q(2, fora_da_janela=0) == "completo"
    assert (
        q(2, fora_da_janela=1) == "timestamp_divergente"
    )  # divergencia manda sobre o resto
    assert q(1, fora_da_janela=0) == "parcial_1_vista_faltante"
    assert q(0, fora_da_janela=0) == "evidencia_insuficiente"


def test_vista_duplicada_invalida_o_conjunto(reg):
    """Duplicata e o estado mais grave: conjunto invalido, nunca apresentado como completo."""
    medidas = (
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),
        _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.NORMAL),
    )
    reg.registrar(_evento(medidas=medidas), duplicadas=(Vista.LATERAL2,))
    g = reg.ler("i-001")
    assert g.qualidade_registro == "invalido"
    assert g.motivo_inconclusivo == "vista_duplicada"


def test_precedencia_das_qualidades():
    from registro import qualidade_registro as q

    assert q(2, duplicadas=1, fora_da_janela=1) == "invalido"
    assert q(2, fora_da_janela=1) == "timestamp_divergente"
    assert q(1) == "parcial_1_vista_faltante"
    assert q(2) == "completo"


# ---------------------------------------------------------------- eventos de gatilho (RF-01.1)


def test_gatilho_aceito_nasce_sem_item_e_e_vinculado_depois(reg):
    """O gatilho precede o item: registrar o gatilho e ligar depois e a ordem real do rig."""
    gid = reg.registrar_gatilho(
        "2026-09-13T03:00:00+00:00", "aceito", fonte="e18_d80nk"
    )
    assert (
        reg._cx.execute(
            "SELECT item_id FROM evento_gatilho WHERE id=?", (gid,)
        ).fetchone()[0]
        is None
    )
    reg.registrar(_evento())
    reg.vincular_gatilho_a_item(gid, "i-001")
    assert (
        reg._cx.execute(
            "SELECT item_id FROM evento_gatilho WHERE id=?", (gid,)
        ).fetchone()[0]
        == "i-001"
    )


def test_gatilho_para_item_inexistente_e_recusado(reg):
    from registro import EventoInvalido

    with pytest.raises(EventoInvalido):
        reg.registrar_gatilho(
            "2026-09-13T03:00:00+00:00",
            "aceito",
            fonte="e18_d80nk",
            item_id="nao-existe",
        )


def test_vincular_gatilho_inexistente_e_recusado(reg):
    from registro import EventoInvalido

    reg.registrar(_evento())
    with pytest.raises(EventoInvalido):
        reg.vincular_gatilho_a_item(999, "i-001")


def test_estado_de_gatilho_invalido_e_recusado(reg):
    from registro import EventoInvalido

    with pytest.raises(EventoInvalido):
        reg.registrar_gatilho("2026-09-13T03:00:00+00:00", "sei_la")


def test_gatilho_falso_e_registrado_sem_item(reg):
    """O disparo que nao virou item e o que precisa entrar: e o unico jeito de medir falso disparo."""
    ident = reg.registrar_gatilho(
        "2026-09-13T03:00:01+00:00",
        "falso",
        fonte="e18_d80nk",
        motivo="sem captura na janela",
        ponto_id=None,
    )
    assert ident >= 1
    linha = reg._cx.execute(
        "SELECT estado, item_id FROM evento_gatilho WHERE id = ?", (ident,)
    ).fetchone()
    assert linha["estado"] == "falso" and linha["item_id"] is None


def test_gatilho_duplicado_e_registrado(reg):
    reg.registrar(_evento())
    reg.registrar_gatilho(
        "2026-09-13T03:00:02+00:00", "aceito", fonte="e18_d80nk", item_id="i-001"
    )
    reg.registrar_gatilho(
        "2026-09-13T03:00:02.100+00:00",
        "duplicado",
        fonte="e18_d80nk",
        motivo="debounce",
    )
    estados = [
        r["estado"]
        for r in reg._cx.execute("SELECT estado FROM evento_gatilho ORDER BY id")
    ]
    assert estados == ["aceito", "duplicado"]


def test_banco_recusa_estado_de_gatilho_fora_da_lista(reg):
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        reg._cx.execute(
            "INSERT INTO evento_gatilho (timestamp, estado) VALUES ('t','talvez')"
        )


# ---------------------------------------------------------------- contrato e evidencia (auditoria)


def test_contrato_do_evento_gravado_inteiro(reg):
    """docs/arquitetura.md: origem, localizacao e versao do contrato nao podem ficar so em memoria."""
    reg.registrar(_evento())
    linha = reg._cx.execute(
        "SELECT equipamento, localizacao, versao_contrato FROM item"
    ).fetchone()
    assert (linha["equipamento"], linha["localizacao"], linha["versao_contrato"]) == (
        "pi5-rig",
        "bancada",
        "1",
    )


def test_lote_vem_do_item_id_e_id_fora_do_formato_nao_inventa_lote(reg):
    reg.registrar(_evento(item_id="L7-000042"))
    item = reg._cx.execute(
        "SELECT lote_id FROM item WHERE item_id='L7-000042'"
    ).fetchone()
    lote = reg._cx.execute(
        "SELECT lote_id, data_inicio FROM lote WHERE lote_id='L7'"
    ).fetchone()
    assert (
        item["lote_id"] == "L7" and lote["data_inicio"] == "2026-09-12"
    )  # data do AGORA do arquivo

    reg.registrar(_evento(item_id="registro-antigo"))
    assert (
        reg._cx.execute(
            "SELECT lote_id FROM item WHERE item_id='registro-antigo'"
        ).fetchone()[0]
        is None
    )


def test_referencia_da_evidencia_grava_caminho_e_hash(reg):
    from registro import ReferenciaDaEvidencia

    medidas = (_medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),)
    reg.registrar(
        _evento(medidas=medidas),
        referencias=(
            ReferenciaDaEvidencia(
                vista=Vista.LATERAL1, caminho="ev/l1.jpg", sha256="a" * 64
            ),
        ),
    )
    linha = reg._cx.execute(
        "SELECT caminho_evidencia, sha256_evidencia FROM inspecao_vista"
    ).fetchone()
    assert (linha["caminho_evidencia"], linha["sha256_evidencia"]) == (
        "ev/l1.jpg",
        "a" * 64,
    )


def test_evidencia_do_que_sustentou_a_decisao_e_persistida(reg):
    """D-30: a medicao entra como rastro. Sem isso ela morre com o processo."""
    from dominio import Evidencia, Origem, Papel

    m = Medida(
        vista=Vista.LATERAL1,
        dominio=Dominio.TAMPA,
        classe=Classe.NORMAL,
        confianca=0.9,
        evidencias=(
            Evidencia(
                grandeza="tilt_graus",
                valor=1.25,
                unidade="grau",
                origem=Origem.GEOMETRIA,
                papel=Papel.AUXILIAR,
                metodo="elipse-ls-v1",
                fonte=None,
            ),
        ),
    )
    reg.registrar(_evento(medidas=(m,)))
    linha = reg._cx.execute(
        "SELECT grandeza, valor, unidade, origem, papel, metodo, fonte FROM evidencia"
    ).fetchone()
    assert dict(linha) == {
        "grandeza": "tilt_graus",
        "valor": 1.25,
        "unidade": "grau",
        "origem": "geometria",
        "papel": "auxiliar",
        "metodo": "elipse-ls-v1",
        "fonte": None,
    }
    assert reg._cx.execute("SELECT COUNT(*) FROM evidencia").fetchone()[0] == 1


# ------------------------------------------------ o veredito da conformidade chega ao banco
# Medido antes da correcao: as duas laterais normais + check dimensional ausente eram gravadas
# como status_final='ok', motivo=None, qualidade='completo'. O item saia APROVADO no banco
# enquanto a conformidade decidia inconclusivo: e a API publica aprovado = (status_final == 'ok').


def _quatro_normais():
    return (
        _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),
        _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.NORMAL),
        _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
        _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
    )


def test_conformidade_inconclusiva_nao_e_gravada_como_ok(reg):
    e = Evento(
        item_id="i-conf",
        capturado_em=AGORA,
        equipamento="pi5",
        localizacao="bancada",
        vistas=(Vista.TOPO,),
        medidas=_quatro_normais(),
        status=Classe.INCONCLUSIVO,
    )
    reg.registrar(e, motivos_conformidade=("check_dimensional_ausente",))
    linha = reg._cx.execute(
        "SELECT status_final, motivo_inconclusivo FROM item"
    ).fetchone()
    assert linha["status_final"] == "inconclusivo"
    assert linha["motivo_inconclusivo"] == "check_dimensional_ausente"


def test_conformidade_reprovada_nao_e_gravada_como_ok(reg):
    e = Evento(
        item_id="i-conf2",
        capturado_em=AGORA,
        equipamento="pi5",
        localizacao="bancada",
        vistas=(Vista.TOPO,),
        medidas=_quatro_normais(),
        status=Classe.TAMPA_AUSENTE,
    )
    reg.registrar(e)
    assert (
        reg._cx.execute("SELECT status_final FROM item").fetchone()["status_final"]
        == "defeito"
    )


def test_aprovacao_legitima_continua_ok(reg):
    e = Evento(
        item_id="i-ok",
        capturado_em=AGORA,
        equipamento="pi5",
        localizacao="bancada",
        vistas=(Vista.TOPO,),
        medidas=_quatro_normais(),
        status=Classe.NORMAL,
    )
    reg.registrar(e)
    linha = reg._cx.execute(
        "SELECT status_final, motivo_inconclusivo FROM item"
    ).fetchone()
    assert linha["status_final"] == "ok" and linha["motivo_inconclusivo"] is None


def test_gatilho_vinculado_nao_pode_ser_reatribuido(reg):
    gid = reg.registrar_gatilho(
        "2026-09-13T03:00:00+00:00", "aceito", fonte="e18_d80nk"
    )
    reg.registrar(_evento(item_id="i-001"))
    reg.registrar(_evento(item_id="i-002"))
    reg.vincular_gatilho_a_item(gid, "i-001")
    with pytest.raises(EventoInvalido, match="ja vinculado|conflito"):
        reg.vincular_gatilho_a_item(gid, "i-002")
    assert (
        reg._cx.execute(
            "SELECT item_id FROM evento_gatilho WHERE id = ?", (gid,)
        ).fetchone()[0]
        == "i-001"
    )
