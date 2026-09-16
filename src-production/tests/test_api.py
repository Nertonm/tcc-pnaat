"""Testes da API do site: o caminho real e registro -> painel -> handler -> JSON.

Sem mock no meio: sobe o servidor de verdade numa porta efemera, com um banco de verdade criado
pela API do `Registro`, e fala HTTP. O que se quer provar nao e "a funcao devolve dict", e sim que
o site tem de onde tirar numero: cada rota responde o contrato que o `site/js/api.js` consome.

Regras que os testes protegem (sao as mesmas do relatorio, e por isso valem aqui):
  * `inconclusivo` nunca entra nos aprovados;
  * consulta sem base devolve ausencia DECLARADA, nunca um zero que se le como "nenhum defeito";
  * rota desconhecida responde JSON, nao a pagina de erro HTML;
  * o gatilho invalido e recusado ANTES de gravar, com 400 e motivo.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from api import criar_servidor
from dominio import Classe, Dominio, Evento, Medida, Qualidade, Vista
from registro import Registro

T0 = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)


def _medida(vista, dominio, classe, conf=0.9):
    return Medida(
        vista=vista,
        dominio=dominio,
        classe=classe,
        confianca=conf,
        qualidade=Qualidade.OK,
    )


def _evento(item_id, quando, medidas, classe, lote="L1"):
    return Evento(
        item_id=item_id,
        capturado_em=quando,
        equipamento="pi5-rig",
        localizacao="bancada-b",
        vistas=(Vista.TOPO,),
        medidas=medidas,
        status=classe,
    )


@pytest.fixture()
def banco(tmp_path):
    """Base real: 3 itens (ok, defeito, inconclusivo) + gatilho falso + evidencia em disco."""
    caminho = tmp_path / "hub.db"
    reg = Registro.abrir(caminho)
    cx = reg._cx
    cx.execute("INSERT INTO lote (lote_id, data_inicio) VALUES ('L1','2026-09-15')")
    cx.execute(
        "INSERT INTO ponto_linha (ponto_id, nome, tipo) VALUES (1,'bancada-b','rig')"
    )
    reg.registrar(
        _evento(
            "i-A",
            T0,
            (
                _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),
                _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.NORMAL),
                _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
                _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
            ),
            Classe.NORMAL,
        )
    )
    reg.registrar(
        _evento(
            "i-B",
            T0 + timedelta(seconds=5),
            (
                _medida(Vista.LATERAL1, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
                _medida(Vista.LATERAL2, Dominio.TAMPA, Classe.TAMPA_AUSENTE),
                _medida(Vista.LATERAL1, Dominio.CORPO, Classe.NORMAL),
                _medida(Vista.LATERAL2, Dominio.CORPO, Classe.NORMAL),
            ),
            Classe.TAMPA_AUSENTE,
        )
    )
    # i-C fica com UMA lateral de proposito: sem as duas, o dominio nao decide (D-04/D-29) e o item
    # tem de sair inconclusivo; e o caso que prova que o resumo nao soma inconclusivo em aprovado.
    reg.registrar(
        _evento(
            "i-C",
            T0 + timedelta(seconds=9),
            (_medida(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),),
            Classe.NORMAL,
        )
    )
    cx.execute("UPDATE item SET lote_id='L1', fonte_trigger='e18_d80nk'")
    cx.execute(
        "UPDATE inspecao_vista SET latencia_ms=42, pixels_saturados_pct=1.0"
        " WHERE vista='lateral1'"
    )
    evidencia = tmp_path / "ev.jpg"
    evidencia.write_bytes(b"\xff\xd8\xff\xe0evidencia-de-teste\xff\xd9")
    cx.execute(
        "UPDATE inspecao_vista SET caminho_evidencia=? WHERE item_id='i-B' AND vista='lateral1'",
        (str(evidencia),),
    )
    reg.registrar_gatilho(
        "2026-09-15T10:00:05+00:00",
        "aceito",
        fonte="e18_d80nk",
        item_id="i-B",
        ponto_id=1,
    )
    reg.registrar_gatilho(
        "2026-09-15T10:00:07+00:00",
        "falso",
        fonte="e18_d80nk",
        ponto_id=1,
        motivo="sem captura na janela",
    )
    cx.commit()
    reg.fechar()
    return caminho


@pytest.fixture()
def site(tmp_path):
    raiz = tmp_path / "site"
    (raiz / "js").mkdir(parents=True)
    (raiz / "index.html").write_text(
        "<!doctype html><title>PNAAT</title><div id=app></div>"
    )
    (raiz / "js" / "api.js").write_text("// adaptador\n")
    return raiz


@pytest.fixture()
def servidor(banco, site):
    srv = criar_servidor(banco, site, porta=0)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def pega(base, rota):
    with urllib.request.urlopen(base + rota, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode())


def pega_bytes(base, rota):
    with urllib.request.urlopen(base + rota, timeout=10) as resp:
        return resp.status, resp.headers.get("Content-Type"), resp.read()


def test_health_declara_o_que_esta_no_ar(servidor):
    status, corpo = pega(servidor, "/api/health")
    assert status == 200 and corpo["ok"] is True
    dados = corpo["dados"]
    assert dados["banco"]["existe"] is True and dados["banco"]["itens"] == 3
    assert dados["camera"]["adaptador"].endswith(":8093")
    assert isinstance(dados["servicos"], list) and dados["servicos"]


def test_resumo_nao_soma_inconclusivo_nos_aprovados(servidor):
    _, corpo = pega(servidor, "/api/resumo")
    dados = corpo["dados"]
    assert dados["contagem_por_estado"] == {"ok": 1, "defeito": 1, "inconclusivo": 1}
    assert dados["aprovados"] == 1
    assert (
        dados["por_lote"][0]["lote_id"] == "L1" and dados["por_lote"][0]["itens"] == 3
    )
    assert dados["tendencia"][0]["itens"] == 3


def test_capturas_lista_do_banco_com_url_de_evidencia(servidor):
    _, corpo = pega(servidor, "/api/capturas?limite=50")
    linhas = corpo["dados"]["capturas"]
    # toda linha de `inspecao_vista` entra, inclusive a do topo (papel auxiliar): ela e dado real
    assert corpo["dados"]["total"] == len(linhas) == corpo["dados"]["base"] == 12
    # o codigo do catalogo so existe na linha do DOMINIO que tem codigo: tampa defeituosa sim,
    # corpo normal nao (MAPA_CODIGO do registro so cobre as classes catalogadas)
    tampa = [
        c
        for c in linhas
        if c["item_id"] == "i-B"
        and c["vista"] == "lateral1"
        and c["dominio"] == "tampa"
    ][0]
    corpo_ok = [
        c
        for c in linhas
        if c["item_id"] == "i-B"
        and c["vista"] == "lateral1"
        and c["dominio"] == "corpo"
    ][0]
    assert (
        tampa["status_item"] == "defeito" and tampa["codigo_defeito"] == "TAMPA_AUSENTE"
    )
    assert tampa["status_vista"] == "defeito"
    assert corpo_ok["status_vista"] == "ok" and corpo_ok["codigo_defeito"] is None
    assert (
        corpo_ok["status_item"] == "defeito"
    )  # o ITEM tem defeito; a vista do corpo nao
    assert tampa["evidencia_url"] == "/api/evidencia?item=i-B&vista=lateral1"
    assert tampa["lote"] == "L1" and tampa["latencia_ms"] == 42


def test_capturas_filtra_por_estado_e_vista(servidor):
    _, defeitos = pega(servidor, "/api/capturas?estado=defeito")
    assert {c["item_id"] for c in defeitos["dados"]["capturas"]} == {"i-B"}
    _, laterais1 = pega(servidor, "/api/capturas?vista=lateral1")
    assert laterais1["dados"]["total"] == 5
    assert all(c["vista"] == "lateral1" for c in laterais1["dados"]["capturas"])


def test_capturas_recusa_filtro_fora_do_vocabulario(servidor):
    with pytest.raises(urllib.error.HTTPError) as erro:
        pega(servidor, "/api/capturas?vista=diagonal")
    assert erro.value.code == 400
    assert json.loads(erro.value.read().decode())["erro"] == "filtro_invalido"


def test_item_detalhe_traz_vistas_e_evidencias(servidor):
    _, corpo = pega(servidor, "/api/item/i-B")
    dados = corpo["dados"]
    assert dados["item_id"] == "i-B" and dados["status_final"] == "defeito"
    papeis = {v["vista"]: v["papel"] for v in dados["vistas"]}
    # D-23/D-30 no dado servido: as laterais decidem, o topo nunca decide
    assert papeis["lateral1"] == "decide" and papeis["lateral2"] == "decide"
    assert papeis["topo"] == "auxiliar"
    b = [v for v in dados["vistas"] if v["vista"] == "lateral1"][0]
    assert b["evidencia_url"].startswith("/api/evidencia?")


def test_item_inexistente_e_404_com_motivo(servidor):
    with pytest.raises(urllib.error.HTTPError) as erro:
        pega(servidor, "/api/item/nao-existe")
    assert erro.value.code == 404
    assert json.loads(erro.value.read().decode())["erro"] == "item_desconhecido"


def test_qualidade_declara_o_que_nao_e_observavel(servidor):
    _, corpo = pega(servidor, "/api/qualidade")
    dados = corpo["dados"]
    assert dados["latencia_por_vista"][0]["vista"] == "lateral1"
    assert dados["gatilho_por_fonte"][0]["falsos"] == 1
    assert dados["perda_de_deteccao"]["instrumentada"] is False
    assert "encoder" in dados["perda_de_deteccao"]["motivo"]


def test_evidencia_serve_o_jpeg_e_recusa_sem_arquivo(servidor):
    status, tipo, corpo = pega_bytes(servidor, "/api/evidencia?item=i-B&vista=lateral1")
    assert status == 200 and tipo == "image/jpeg" and corpo.startswith(b"\xff\xd8\xff")
    with pytest.raises(urllib.error.HTTPError) as erro:
        pega_bytes(servidor, "/api/evidencia?item=i-A&vista=lateral1")
    assert erro.value.code == 404


def test_gatilho_aceito_grava_e_devolve_id(servidor):
    pedido = urllib.request.Request(
        servidor + "/api/gatilho",
        method="POST",
        data=json.dumps(
            {
                "timestamp": "2026-09-15T10:10:00+00:00",
                "estado": "aceito",
                "fonte": "e18_d80nk",
                "item_id": "i-A",
                "debounce_ms": 20,
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=10) as resp:
        corpo = json.loads(resp.read().decode())
    assert resp.status == 200 and corpo["dados"]["gatilho_id"] > 0
    _, depois = pega(servidor, "/api/qualidade")
    aceitos = {g["fonte"]: g for g in depois["dados"]["gatilho_por_fonte"]}["e18_d80nk"]
    assert aceitos["aceitos"] == 2


def test_gatilho_invalido_e_recusado_antes_de_gravar(servidor):
    pedido = urllib.request.Request(
        servidor + "/api/gatilho",
        method="POST",
        data=json.dumps(
            {"timestamp": "2026-09-15T10:11:00+00:00", "estado": "talvez"}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as erro:
        urllib.request.urlopen(pedido, timeout=10)
    assert erro.value.code == 400
    assert "estado" in json.loads(erro.value.read().decode())["erro"]


def test_rota_desconhecida_responde_json(servidor):
    with pytest.raises(urllib.error.HTTPError) as erro:
        pega(servidor, "/api/nao-existe")
    assert erro.value.code == 404
    assert json.loads(erro.value.read().decode())["erro"] == "rota_desconhecida"


def test_site_e_servido_na_mesma_origem_da_api(servidor):
    with urllib.request.urlopen(servidor + "/", timeout=10) as resp:
        assert resp.status == 200 and b"PNAAT" in resp.read()
    with urllib.request.urlopen(servidor + "/js/api.js", timeout=10) as resp:
        assert resp.status == 200 and b"adaptador" in resp.read()


# ---------------------------------------------------------------- revisao ponta a ponta

import urllib.error
import urllib.request

import pytest


def _aponta_evidencia(banco, item, vista, caminho):
    cx = sqlite3.connect(banco)
    cx.execute(
        "UPDATE inspecao_vista SET caminho_evidencia=? WHERE item_id=? AND vista=?",
        (caminho, item, vista),
    )
    cx.commit()
    cx.close()


def _linha(servidor, item, vista):
    with urllib.request.urlopen(
        servidor + "/api/capturas?limite=200", timeout=10
    ) as resp:
        dados = json.loads(resp.read().decode())["dados"]["capturas"]
    return [c for c in dados if c["item_id"] == item and c["vista"] == vista][0]


def test_evidencia_fora_da_raiz_e_recusada(servidor, banco, tmp_path):
    """O caminho vem do banco: fora da raiz declarada nao se le nada, nem por tabela."""
    fora = tmp_path.parent / f"fora-da-raiz-{tmp_path.name}.txt"
    fora.write_text("conteudo-que-nao-pode-sair")
    _aponta_evidencia(banco, "i-A", "lateral1", str(fora))

    with pytest.raises(urllib.error.HTTPError) as erro:
        urllib.request.urlopen(
            servidor + "/api/evidencia?item=i-A&vista=lateral1", timeout=10
        )
    assert erro.value.code == 403
    corpo = erro.value.read().decode()
    assert json.loads(corpo)["erro"] == "evidencia_fora_da_raiz"
    assert "conteudo-que-nao-pode-sair" not in corpo


def test_evidencia_inexistente_nao_vira_url_nem_imagem_quebrada(
    servidor, banco, tmp_path
):
    """`tem_evidencia` sai do ARQUIVO, nao do campo: caminho gravado sem arquivo nao e evidencia."""
    _aponta_evidencia(banco, "i-A", "lateral1", str(tmp_path / "sumiu.jpg"))

    linha = _linha(servidor, "i-A", "lateral1")
    assert linha["tem_evidencia"] is False and linha["evidencia_url"] is None

    with pytest.raises(urllib.error.HTTPError) as erro:
        urllib.request.urlopen(
            servidor + "/api/evidencia?item=i-A&vista=lateral1", timeout=10
        )
    assert erro.value.code == 404
    assert (
        json.loads(erro.value.read().decode())["erro"] == "arquivo_de_evidencia_ausente"
    )


def test_arquivo_dentro_da_raiz_mas_nao_imagem_e_recusado(servidor, banco, tmp_path):
    """A rota serve imagem. Texto dentro da raiz nao vira `image/*` por conveniencia."""
    texto = tmp_path / "anotacao.txt"
    texto.write_text("nao-sou-imagem")
    _aponta_evidencia(banco, "i-A", "lateral1", str(texto))

    assert _linha(servidor, "i-A", "lateral1")["tem_evidencia"] is False
    with pytest.raises(urllib.error.HTTPError) as erro:
        urllib.request.urlopen(
            servidor + "/api/evidencia?item=i-A&vista=lateral1", timeout=10
        )
    assert erro.value.code == 404


def test_base_vazia_declara_ausencia_em_vez_de_zero(tmp_path, site):
    """Registro sem item: `aprovados` e `total` sao nulos com motivo; lista vazia tem base 0."""
    import threading

    from api import criar_servidor
    from registro import Registro

    vazio = tmp_path / "vazio.db"
    Registro.abrir(vazio).fechar()

    srv = criar_servidor(vazio, site, porta=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        with urllib.request.urlopen(base + "/api/resumo", timeout=10) as resp:
            resumo = json.loads(resp.read().decode())["dados"]
        assert resumo["sem_base"] is True
        assert resumo["aprovados"] is None and resumo["total"] is None
        assert "nao ha medicao" in resumo["motivo"]
        assert resumo["contagem_por_estado"] == {}

        with urllib.request.urlopen(base + "/api/capturas", timeout=10) as resp:
            capturas = json.loads(resp.read().decode())["dados"]
        assert (
            capturas["total"] == 0
            and capturas["base"] == 0
            and capturas["capturas"] == []
        )
    finally:
        srv.shutdown()
        srv.server_close()


def test_helper_de_evidencia_recusa_fora_da_raiz(tmp_path):
    """Pina a SEGUNDA camada: a mutacao da revisao mostrou que o guard da rota sozinho deixava o
    helper sem prova; com a rota mutada o teste de rota falha, mas o helper podia quebrar calado."""
    from api import _evidencia_valida

    dentro = tmp_path / "ok.jpg"
    dentro.write_bytes(b"\xff\xd8\xff")
    fora = tmp_path.parent / f"fora-{tmp_path.name}.jpg"
    fora.write_bytes(b"\xff\xd8\xff")
    texto = tmp_path / "nota.txt"
    texto.write_text("nao sou imagem")

    assert _evidencia_valida(str(dentro), tmp_path) == dentro.resolve()
    assert _evidencia_valida(str(fora), tmp_path) is None  # fora da raiz
    assert _evidencia_valida(str(tmp_path / "nao-existe.jpg"), tmp_path) is None
    assert _evidencia_valida(str(texto), tmp_path) is None  # dentro, mas nao e imagem
    assert _evidencia_valida(None, tmp_path) is None


# ------------------------------------------------------------------ correcao do operador (P1)


def _post_correcao(base, corpo):
    pedido = urllib.request.Request(
        f"{base}/api/correcao",
        method="POST",
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=5) as resposta:
        return resposta.status, json.loads(resposta.read())


def test_correcao_de_inconclusivo_e_confirmada_pela_leitura_de_volta(servidor):
    base = servidor  # o fixture ja e a base: http://127.0.0.1:<porta>
    codigo, corpo = _post_correcao(
        base,
        {
            "item_id": "i-C",
            "decisao_corrigida": "ok",
            "corrigido_por": "operador-de-teste",
        },
    )
    assert codigo == 200
    assert corpo["dados"]["decisao_efetiva"] == "ok"
    registro = corpo["dados"]["correcao"]
    assert registro["decisao_original"] == "inconclusivo"
    assert registro["corrigido_por"] == "operador-de-teste"

    # a decisao vigente aparece no detalhe do item e o status do registro NAO mudou
    with urllib.request.urlopen(f"{base}/api/item/i-C", timeout=5) as resposta:
        detalhe = json.loads(resposta.read())["dados"]
    assert detalhe["decisao_efetiva"] == "ok"
    assert detalhe["status_final"] == "inconclusivo"
    assert detalhe["correcao_vigente"]["corrigido_por"] == "operador-de-teste"


def test_correcao_recusa_item_inexistente_com_404(servidor):
    base = servidor  # o fixture ja e a base: http://127.0.0.1:<porta>
    with pytest.raises(urllib.error.HTTPError) as erro:
        _post_correcao(
            base,
            {
                "item_id": "nao-existe",
                "decisao_corrigida": "ok",
                "corrigido_por": "operador-de-teste",
            },
        )
    assert erro.value.code == 404
    assert json.loads(erro.value.read())["erro"] == "item_inexistente"


def test_correcao_recusa_pedido_incompleto_e_vocabulario(servidor):
    base = servidor  # o fixture ja e a base: http://127.0.0.1:<porta>
    for corpo, esperado in (
        ({"decisao_corrigida": "ok", "corrigido_por": "op"}, "campo_ausente"),
        ({"item_id": "i-C", "corrigido_por": "op"}, "campo_ausente"),
        ({"item_id": "i-C", "decisao_corrigida": "ok"}, "campo_ausente"),
        (
            {
                "item_id": "i-C",
                "decisao_corrigida": "tampa_ausente",
                "corrigido_por": "op",
            },
            "correcao_recusada_pelo_registro",
        ),
        (
            {"item_id": "i-C", "decisao_corrigida": "ok", "corrigido_por": 7},
            "campo_com_tipo_errado",
        ),
    ):
        with pytest.raises(urllib.error.HTTPError) as erro:
            _post_correcao(base, corpo)
        assert erro.value.code == 400, corpo
        assert json.loads(erro.value.read())["erro"] == esperado, corpo


def test_bind_remoto_exige_token(tmp_path, site):
    with pytest.raises(ValueError, match="token obrigatorio"):
        criar_servidor(tmp_path / "hub.db", site, porta=0, host="0.0.0.0")


def test_post_remoto_sem_token_e_recusado(tmp_path, site):
    servidor = criar_servidor(
        tmp_path / "hub.db", site, porta=0, host="127.0.0.1", token="segredo"
    )
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{servidor.server_address[1]}/api/gatilho"
        pedido = urllib.request.Request(
            url, data=b"{}", method="POST", headers={"Content-Type": "application/json"}
        )
        with pytest.raises(urllib.error.HTTPError) as erro:
            urllib.request.urlopen(pedido, timeout=2)
        assert erro.value.code == 401
    finally:
        servidor.shutdown()
        thread.join(timeout=2)
        servidor.server_close()


def test_url_de_evidencia_preserva_identificador_literal():
    from api import _url_evidencia

    url = _url_evidencia("item&vista=outra", "lateral 1", Path("foto.jpg"))
    assert parse_qs(urlsplit(url).query) == {
        "item": ["item&vista=outra"],
        "vista": ["lateral 1"],
    }
