"""Testes do painel: cada consulta assere um numero calculado a mao.

Base montada pela propria API do registro (nao INSERT na mao para o que a API cobre), com os
campos que o registro ainda nao produz (latencia, saturacao, ambiente, heartbeat, lote) inseridos
por SQL — e declarados como tal.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dominio import Classe, Dominio, Evento, Medida, Qualidade, Vista
from painel import Painel
from registro import Registro

T0 = datetime(2026, 9, 12, 23, 0, tzinfo=timezone.utc)


def _m(vista, dominio, classe, conf=0.9, q=Qualidade.OK):
    return Medida(vista=vista, dominio=dominio, classe=classe, confianca=conf, qualidade=q)


def _completo(vista_lat1, vista_lat2, corpo=Classe.NORMAL):
    return (_m(Vista.LATERAL1, Dominio.TAMPA, vista_lat1),
            _m(Vista.LATERAL2, Dominio.TAMPA, vista_lat2),
            _m(Vista.LATERAL1, Dominio.CORPO, corpo),
            _m(Vista.LATERAL2, Dominio.CORPO, corpo))


def _ev(item_id, quando, medidas, classe):
    return Evento(item_id=item_id, capturado_em=quando, equipamento="pi5-rig",
                  localizacao="bancada-b", vistas=(Vista.TOPO,), medidas=medidas, status=classe)


@pytest.fixture()
def painel(tmp_path):
    reg = Registro.abrir(tmp_path / "hub.db")
    cx = reg._cx
    cx.execute("INSERT INTO lote (lote_id, data_inicio) VALUES ('L1','2026-09-12')")
    cx.execute("INSERT INTO lote (lote_id, data_inicio) VALUES ('L2','2026-09-12')")
    # o esquema tem FK real (PRAGMA foreign_keys=ON): sem o ponto de linha o ambiente nao entra
    cx.execute("INSERT INTO ponto_linha (ponto_id, nome, tipo) VALUES (1,'bancada-b','rig')")

    # L1: ok / mal rosqueada / tampa ausente (critico) ; L2: inconclusivo (falta uma lateral)
    reg.registrar(_ev("i-A", T0, _completo(Classe.NORMAL, Classe.NORMAL), Classe.NORMAL))
    reg.registrar(_ev("i-B", T0 + timedelta(seconds=10),
                      _completo(Classe.TAMPA_MAL_ROSQUEADA, Classe.NORMAL), Classe.TAMPA_MAL_ROSQUEADA))
    reg.registrar(_ev("i-C", T0 + timedelta(hours=1),
                      _completo(Classe.TAMPA_AUSENTE, Classe.TAMPA_AUSENTE), Classe.TAMPA_AUSENTE))
    reg.registrar(_ev("i-D", T0 - timedelta(hours=1),
                      (_m(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),), Classe.NORMAL))

    cx.execute("UPDATE item SET lote_id='L1', fonte_trigger='e18_d80nk' WHERE item_id IN ('i-A','i-B','i-C')")
    cx.execute("UPDATE item SET lote_id='L2', fonte_trigger='e18_d80nk' WHERE item_id='i-D'")
    # campos que o registro ainda nao produz: latencia, saturacao, evidencia, ambiente, heartbeat
    cx.execute("UPDATE inspecao_vista SET latencia_ms=40, pixels_saturados_pct=1.5 WHERE vista='lateral1'")
    cx.execute("UPDATE inspecao_vista SET latencia_ms=60, pixels_saturados_pct=0.5 WHERE vista='lateral2'")
    cx.execute("UPDATE inspecao_vista SET caminho_evidencia='ev/i-C-lateral1.jpg' WHERE item_id='i-C' AND vista='lateral1'")
    for i, (dt, temp) in enumerate([(T0, 21.0), (T0 + timedelta(seconds=5), 22.0),
                                    (T0 + timedelta(seconds=9), 20.5)]):
        cx.execute("INSERT INTO evento_ambiental (timestamp, ponto_id, temperatura) VALUES (?,?,?)",
                   ((dt.isoformat()), 1, temp))
    cx.execute("INSERT INTO heartbeat_no (ponto_id, timestamp, status, fila_pendente, latencia_envio_ms)"
               " VALUES (1, ?, 'online', 0, 12)", (datetime.now(timezone.utc).isoformat(),))
    cx.execute("INSERT INTO heartbeat_no (ponto_id, timestamp, status, fila_pendente)"
               " VALUES (1, ?, 'offline', 3)", ((datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),))
    cx.execute("INSERT INTO correcao_operador (item_id, decisao_original, decisao_corrigida, corrigido_por, timestamp)"
               " VALUES ('i-B','tampa_mal_rosqueada','normal','operador-1','2026-09-12T23:30:00+00:00')")
    cx.execute("INSERT INTO evento_rejeicao (item_id, timestamp_ordenado, status_ordem, status, via_sensor)"
               " VALUES ('i-C','2026-09-13T00:00:00+00:00','emitida','timeout','e18_d80nk')")
    cx.commit()

    p = Painel(cx)
    yield p
    reg.fechar()


def test_taxa_de_defeito_por_lote(painel):
    t = {r.lote_id: r for r in painel.taxa_de_defeito_por_lote()}
    assert (t["L1"].itens, t["L1"].defeitos, t["L1"].inconclusivos) == (3, 2, 0)
    assert t["L1"].taxa_defeito == pytest.approx(2 / 3)
    assert (t["L2"].itens, t["L2"].defeitos, t["L2"].inconclusivos) == (1, 0, 1)


def test_defeitos_frequentes_com_severidade(painel):
    d = {r.codigo: r for r in painel.defeitos_frequentes()}
    assert d["TAMPA_MAL_ROSQUEADA"].severidade == "major" and d["TAMPA_MAL_ROSQUEADA"].ocorrencias == 1
    assert d["TAMPA_AUSENTE"].severidade == "critico" and d["TAMPA_AUSENTE"].ocorrencias == 2


def test_tendencia_por_hora(painel):
    t = {r.hora: r for r in painel.tendencia_por_hora()}
    assert t["2026-09-12T22"].itens == 1 and t["2026-09-12T22"].defeitos == 0
    assert t["2026-09-12T23"].itens == 2 and t["2026-09-12T23"].defeitos == 1
    assert t["2026-09-13T00"].itens == 1 and t["2026-09-13T00"].defeitos == 1


def test_correlacao_ambiental_pareia_na_janela(painel):
    c = painel.correlacao_ambiental(janela_s=30)
    assert c.pares == 6          # i-A e i-B distam 10 s: cada um casa com os 3 eventos
    assert c.r is not None       # o rotulo varia entre os itens pareados


def test_itens_criticos_traz_evidencia(painel):
    c = painel.itens_criticos()
    assert len(c) == 2 and {i.item_id for i in c} == {"i-C"}       # uma linha por lateral do item
    assert {i.codigo_defeito for i in c} == {"TAMPA_AUSENTE"}
    assert any(i.caminho_evidencia == "ev/i-C-lateral1.jpg" for i in c)


def test_saude_dos_nos_so_na_janela(painel):
    s = painel.saude_dos_nos(janela_h=1)
    assert len(s) == 1 and s[0].status == "online" and s[0].fila_pendente == 0


def test_latencia_por_vista(painel):
    l = {r.vista: r for r in painel.latencia_por_vista()}
    assert (l["lateral1"].medidas, l["lateral1"].media_ms, l["lateral1"].maxima_ms) == (7, 40.0, 40)
    assert (l["lateral2"].medidas, l["lateral2"].media_ms) == (6, 60.0)
    assert "topo" not in l       # o topo nao tem latencia de decisao registrada


def test_correcoes_e_separacoes(painel):
    c = painel.correcoes_para_auditoria()
    assert len(c) == 1 and c[0].item_id == "i-B" and c[0].decisao_corrigida == "normal"
    s = painel.separacoes_nao_confirmadas()
    assert len(s) == 1 and s[0].status == "timeout" and s[0].item_id == "i-C"


def test_gatilho_por_fonte_declara_o_que_nao_e_observavel(painel):
    g = {r.fonte_trigger: r for r in painel.gatilho_por_fonte()}
    assert g["e18_d80nk"].itens == 4
    assert g["e18_d80nk"].falso_disparo_observavel is False


def test_saturacao_por_vista(painel):
    s = {r.vista: r for r in painel.saturacao_por_vista()}
    assert (s["lateral1"].medidas, s["lateral1"].media_pct, s["lateral1"].maxima_pct) == (7, 1.5, 1.5)
    assert s["lateral2"].media_pct == pytest.approx(0.5)


def test_inconclusivos_por_lote_e_motivo(painel):
    i = painel.inconclusivos_por_lote()
    assert len(i) == 1 and i[0].lote_id == "L2" and i[0].motivo == "vista_lateral_ausente"


def test_distribuicao_por_dominio(painel):
    d = {(r.dominio, r.estado): r.ocorrencias for r in painel.distribuicao_por_dominio()}
    # i-D tem UMA lateral na tampa: dominio inconclusivo, nao ok (D-04/D-29)
    assert d[("tampa", "defeito")] == 2 and d[("tampa", "ok")] == 1 and d[("tampa", "inconclusivo")] == 1
    assert d[("corpo", "ok")] == 3 and d[("corpo", "inconclusivo")] == 1


def test_discordancia_lateral(painel):
    d = painel.discordancia_lateral()
    assert d.itens_com_duas_laterais == 3      # i-D so tem uma lateral: nao entra
    assert d.discordantes == 1                 # i-B: lateral1 mal rosqueada x lateral2 normal
    assert d.taxa == pytest.approx(1 / 3)


def test_inconclusivo_nunca_e_aprovado(painel):
    estados = painel.contagem_por_estado()
    assert estados == {"ok": 1, "defeito": 2, "inconclusivo": 1}
    assert painel.aprovados() == 1
    assert painel.aprovados() != sum(v for k, v in estados.items() if k != "defeito")
