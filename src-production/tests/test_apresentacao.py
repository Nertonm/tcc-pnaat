"""Testes da apresentacao: cada numero que o HTML mostra e conferido a mao.

A base e montada pela API do registro (`Registro.abrir` + `registrar`), igual a
`tests/test_painel.py`, para os mesmos quatro itens darem os mesmos numeros la conferidos. O que
nao vem da API esta marcado no lugar: um `UPDATE` de evidencia, os eventos de gatilho (que a API
tem) e, na base de texto hostil, as mudancas de lote/motivo/codigo que existem para exercitar
escape e campo NULL.

As assercoes leem o HTML pelo `id` de cada celula e de cada tabela. Procurar o digito solto no
documento nao provaria nada: o que a regra exige e o numero certo no lugar certo.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from apresentacao import (
    SEM_DADO,
    Celula,
    PapelNaAprovacao,
    Tabela,
    montar_relatorio,
    papel_na_aprovacao,
    relatorio_html,
    renderizar,
    secao_resumo,
)
from dominio import Classe, Dominio, Evento, Medida, Qualidade, Vista
from painel import Painel
from registro import Registro

T0 = datetime(2026, 9, 12, 23, 0, tzinfo=timezone.utc)
RAIZ = Path(__file__).resolve().parent.parent

#: blocos que o relatorio promete; conferidos por id, nao por titulo escrito a mao
SECOES = (
    "resumo",
    "taxa-por-lote",
    "defeitos-frequentes",
    "itens-criticos",
    "inconclusivos-por-motivo",
    "discordancia",
    "gatilho",
)
TABELAS = (
    "tabela-por-estado",
    "tabela-taxa-por-lote",
    "tabela-defeitos-frequentes",
    "tabela-itens-criticos",
    "tabela-inconclusivos-por-motivo",
    "tabela-gatilho-por-fonte",
)


# ---------------------------------------------------------------- leitura do HTML


def valores(html: str) -> dict[str, str]:
    """Todas as celulas do relatorio, por identificador. Devolve o dicionario inteiro para o teste
    poder exigir que nao exista celula a mais (numero que apareceu sem consulta) nem a menos."""
    achados = re.findall(r'<dd[^>]*id="([^"]+)"[^>]*>(.*?)</dd>', html, re.DOTALL)
    return {identificador: valor.strip() for identificador, valor in achados}


def celula(html: str, identificador: str) -> str:
    """Valor de uma celula especifica. Falha alto se a celula nao existir."""
    m = re.search(
        rf'<dd[^>]*id="{re.escape(identificador)}"[^>]*>(.*?)</dd>', html, re.DOTALL
    )
    assert m is not None, f"celula ausente no relatorio: {identificador}"
    return m.group(1).strip()


def tabela(html: str, identificador: str) -> str:
    """Marcacao da tabela pelo id."""
    m = re.search(
        rf'<table id="{re.escape(identificador)}">.*?</table>', html, re.DOTALL
    )
    assert m is not None, f"tabela ausente no relatorio: {identificador}"
    return m.group(0)


def linhas(html: str, identificador: str) -> list[list[str]]:
    """Linhas do corpo da tabela. Quadro sem dado devolve `[['sem dado']]` (uma celula que ocupa a
    largura toda), nao uma lista vazia: e assim que o HTML distingue ausencia de zero."""
    corpo = re.search(r"<tbody>(.*?)</tbody>", tabela(html, identificador), re.DOTALL)
    assert corpo is not None, f"tabela sem corpo: {identificador}"
    return [
        re.findall(r"<td[^>]*>(.*?)</td>", linha, re.DOTALL)
        for linha in re.findall(r"<tr>(.*?)</tr>", corpo.group(1), re.DOTALL)
    ]


# ---------------------------------------------------------------- bases


def _m(vista, dominio, classe, conf=0.9, q=Qualidade.OK):
    return Medida(
        vista=vista, dominio=dominio, classe=classe, confianca=conf, qualidade=q
    )


def _completo(lat1, lat2, corpo=Classe.NORMAL):
    return (
        _m(Vista.LATERAL1, Dominio.TAMPA, lat1),
        _m(Vista.LATERAL2, Dominio.TAMPA, lat2),
        _m(Vista.LATERAL1, Dominio.CORPO, corpo),
        _m(Vista.LATERAL2, Dominio.CORPO, corpo),
    )


def _ev(item_id, quando, medidas, classe):
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
def painel(tmp_path):
    """L1: ok / mal rosqueada / tampa ausente (critico). L2: inconclusivo (uma lateral so)."""
    reg = Registro.abrir(tmp_path / "hub.db")
    cx = reg._cx
    cx.execute("INSERT INTO lote (lote_id, data_inicio) VALUES ('L1','2026-09-12')")
    cx.execute("INSERT INTO lote (lote_id, data_inicio) VALUES ('L2','2026-09-12')")
    cx.execute(
        "INSERT INTO ponto_linha (ponto_id, nome, tipo) VALUES (1,'bancada-b','rig')"
    )

    reg.registrar(
        _ev("i-A", T0, _completo(Classe.NORMAL, Classe.NORMAL), Classe.NORMAL)
    )
    reg.registrar(
        _ev(
            "i-B",
            T0 + timedelta(seconds=10),
            _completo(Classe.DEFEITO_TAMPA, Classe.NORMAL),
            Classe.DEFEITO_TAMPA,
        )
    )
    reg.registrar(
        _ev(
            "i-C",
            T0 + timedelta(hours=1),
            _completo(Classe.TAMPA_AUSENTE, Classe.TAMPA_AUSENTE),
            Classe.TAMPA_AUSENTE,
        )
    )
    reg.registrar(
        _ev(
            "i-D",
            T0 - timedelta(hours=1),
            (_m(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),),
            Classe.NORMAL,
        )
    )

    cx.execute("UPDATE item SET lote_id='L1' WHERE item_id IN ('i-A','i-B','i-C')")
    cx.execute("UPDATE item SET lote_id='L2' WHERE item_id='i-D'")
    # evidencia que o registro ainda nao produz: fica so na lateral1 do i-C, a lateral2 fica NULL
    cx.execute(
        "UPDATE inspecao_vista SET caminho_evidencia='ev/i-C-lateral1.jpg'"
        " WHERE item_id='i-C' AND vista='lateral1' AND dominio='tampa'"
    )
    reg.registrar_gatilho(
        "2026-09-12T22:59:59+00:00",
        "aceito",
        fonte="e18_d80nk",
        item_id="i-A",
        ponto_id=1,
    )
    reg.registrar_gatilho(
        "2026-09-12T23:00:10+00:00",
        "aceito",
        fonte="e18_d80nk",
        item_id="i-B",
        ponto_id=1,
    )
    reg.registrar_gatilho(
        "2026-09-12T23:00:10.050+00:00",
        "duplicado",
        fonte="e18_d80nk",
        ponto_id=1,
        motivo="debounce",
    )
    reg.registrar_gatilho(
        "2026-09-12T23:05:00+00:00",
        "falso",
        fonte="e18_d80nk",
        ponto_id=1,
        motivo="sem captura na janela",
    )
    reg.registrar_gatilho(
        "2026-09-12T22:59:58+00:00",
        "aceito",
        fonte="vl53l0x",
        item_id="i-D",
        ponto_id=1,
    )
    cx.commit()

    p = Painel(cx)
    yield p
    reg.fechar()


@pytest.fixture()
def painel_vazio(tmp_path):
    """Esquema sem nenhuma linha: e a base em que todo numero seria 0 e nenhum seria verdade."""
    reg = Registro.abrir(tmp_path / "vazio.db")
    yield Painel(reg._cx)
    reg.fechar()


@pytest.fixture()
def painel_com_texto_hostil(tmp_path):
    """Base com texto do banco que quebraria o HTML se nao fosse escapado.

    i-F e inconclusivo (uma lateral) e fica com lote e motivo hostis. Os dois codigos de defeito
    existem em `taxonomia_defeito` (a FK exige); o `UPDATE` so aponta a linha de inspecao para eles,
    para exercitar texto hostil e severidade NULL sem inventar registro.
    """
    reg = Registro.abrir(tmp_path / "hostil.db")
    cx = reg._cx
    cx.execute(
        "INSERT INTO lote (lote_id, data_inicio) VALUES ('L1<script>','2026-09-12')"
    )
    cx.execute(
        "INSERT INTO taxonomia_defeito (codigo, descricao, classe, dominio, severidade)"
        " VALUES ('<b>DEFEITO</b>','descricao','tampa_ausente','tampa','critico')"
    )
    cx.execute(
        "INSERT INTO taxonomia_defeito (codigo, descricao, classe, dominio, severidade)"
        " VALUES ('SEM_SEVERIDADE_LEVE','descricao','deformidade','corpo',NULL)"
    )

    reg.registrar(
        _ev(
            "i-F",
            T0,
            (_m(Vista.LATERAL1, Dominio.TAMPA, Classe.NORMAL),),
            Classe.NORMAL,
        )
    )
    reg.registrar(
        _ev(
            "i-G",
            T0 + timedelta(seconds=5),
            _completo(Classe.NORMAL, Classe.NORMAL),
            Classe.NORMAL,
        )
    )
    cx.execute(
        "UPDATE item SET lote_id='L1<script>', motivo_inconclusivo='motivo\"<i>'"
    )
    cx.execute(
        "UPDATE inspecao_vista SET codigo_defeito='<b>DEFEITO</b>',"
        " caminho_evidencia='ev/<b>x</b>.jpg'"
        " WHERE item_id='i-F' AND vista='lateral1' AND dominio='tampa'"
    )
    cx.execute(
        "UPDATE inspecao_vista SET codigo_defeito='SEM_SEVERIDADE_LEVE'"
        " WHERE item_id='i-G' AND vista='lateral2' AND dominio='tampa'"
    )
    cx.commit()

    p = Painel(cx)
    yield p
    reg.fechar()


# ---------------------------------------------------------------- estrutura


def test_relatorio_tem_os_blocos_exigidos(painel):
    html = relatorio_html(painel)
    for identificador in SECOES:
        assert f'<section id="{identificador}">' in html
    for identificador in TABELAS:
        assert f'<table id="{identificador}">' in html


def test_relatorio_html_e_a_renderizacao_do_mesmo_relatorio(painel):
    """Prova que a separacao dado/HTML nao e decorativa: as duas portas dao no mesmo texto."""
    assert relatorio_html(painel) == renderizar(montar_relatorio(painel))


def test_mesmo_banco_da_a_mesma_saida(painel):
    """Sem carimbo de data/hora na saida, o relatorio e reproduzivel: dois HTMLs identicos byte a
    byte significam que nenhum valor veio do relogio."""
    assert relatorio_html(painel) == relatorio_html(painel)


# ---------------------------------------------------------------- 1. resumo


def test_todos_os_valores_do_relatorio_conferidos_a_mao(painel):
    """O dicionario inteiro das celulas tem que bater: celula a mais seria numero sem consulta,
    celula a menos seria dado apresentado a mao em outro formato."""
    esperado = {
        "resumo-total": "4",  # i-A, i-B, i-C, i-D
        "resumo-aprovados": "1",  # so i-A
        "resumo-defeitos": "2",  # i-B, i-C
        "resumo-inconclusivos": "1",  # i-D
        "resumo-erro-processamento": "0",
        "resumo-conferencia-aprovacao": "as duas consultas concordam: 1",
        "discordancia-itens-com-duas-laterais": "3",  # i-A, i-B, i-C tem 4 medidas laterais
        "discordancia-discordantes": "1",  # i-B: mal rosqueada x normal
        "discordancia-taxa": "33.3%",  # 1/3
        "gatilho-perda-de-deteccao-instrumentada": "nao",
    }
    assert valores(relatorio_html(painel)) == esperado


def test_inconclusivo_nunca_entra_no_numero_de_aprovados(painel):
    """Regra 1, travada por tres lados: o numero, os rotulos e a tabela de estados."""
    html = relatorio_html(painel)
    aprovados = celula(html, "resumo-aprovados")
    inconclusivos = celula(html, "resumo-inconclusivos")
    assert (aprovados, inconclusivos) == ("1", "1")
    assert aprovados != str(int(aprovados) + int(inconclusivos))  # 1 != 2: nao ha soma
    # o rotulo tambem nao pode mentir: quem le tem que saber o que o numero NAO inclui
    assert "somente status ok" in html
    assert "fora dos aprovados" in html
    assert linhas(html, "tabela-por-estado") == [
        ["defeito", "2", "nao"],
        ["inconclusivo", "1", "nao"],
        ["ok", "1", "sim"],
    ]


def test_estado_desconhecido_nao_vira_aprovacao():
    """Fail-closed: so o `ok` explicito conta. Estado que este modulo nao conhece, inclusive um que
    o esquema nao descreve, nao aprova por omissao."""
    assert papel_na_aprovacao("ok") is PapelNaAprovacao.CONTA
    assert papel_na_aprovacao("inconclusivo") is PapelNaAprovacao.NAO_CONTA
    assert papel_na_aprovacao("defeito") is PapelNaAprovacao.NAO_CONTA
    assert papel_na_aprovacao("erro_processamento") is PapelNaAprovacao.NAO_CONTA
    assert (
        papel_na_aprovacao("estado_que_o_esquema_nao_descreve")
        is PapelNaAprovacao.NAO_CONTA
    )


def test_conferencia_de_aprovacao_mostra_divergencia():
    """Com o SQL atual as duas consultas nao podem divergir, entao o ramo da divergencia nao tem
    como aparecer num banco de teste. O duble prova que se um dia puderem, o relatorio MOSTRA a
    divergencia em vez de escolher um dos numeros."""

    class PainelDivergente:
        def contagem_por_estado(self) -> dict[str, int]:
            return {"ok": 5, "defeito": 1}

        def aprovados(self) -> int:
            return 4

    celulas = {
        c.identificador: c.valor for c in secao_resumo(PainelDivergente()).celulas
    }
    assert celulas["resumo-conferencia-aprovacao"] == (
        "divergencia entre consultas: aprovados()=4, contagem de ok=5; o relatorio nao escolheu "
        "nenhum dos dois"
    )


# ---------------------------------------------------------------- 2. lote


def test_taxa_por_lote_calculada_a_mao(painel):
    assert linhas(relatorio_html(painel), "tabela-taxa-por-lote") == [
        ["L1", "3", "2", "0", "66.7%"],  # 2 defeitos em 3 itens
        ["L2", "1", "0", "1", "0.0%"],  # zero defeito COM base medida: 0.0% e honesto
    ]


# ---------------------------------------------------------------- 3. defeitos frequentes


def test_defeitos_frequentes_com_severidade(painel):
    """TAMPA_AUSENTE ocorre em duas laterais do i-C; TAMPA_MAL_ROSQUEADA so na lateral1 do i-B."""
    assert linhas(relatorio_html(painel), "tabela-defeitos-frequentes") == [
        ["TAMPA_AUSENTE", "critico", "2"],
        ["TAMPA_DEFEITO", "major", "1"],
    ]


# ---------------------------------------------------------------- 4. itens criticos


def test_itens_criticos_trazem_a_referencia_de_evidencia(painel):
    """Uma linha por lateral critica do i-C. A lateral2 nao tem caminho no banco: a ausencia
    aparece escrita, nunca deduzida do item_id."""
    assert set(map(tuple, linhas(relatorio_html(painel), "tabela-itens-criticos"))) == {
        ("i-C", "TAMPA_AUSENTE", "critico", "lateral1", "ev/i-C-lateral1.jpg"),
        ("i-C", "TAMPA_AUSENTE", "critico", "lateral2", "sem evidencia registrada"),
    }


# ---------------------------------------------------------------- 5. inconclusivos


def test_inconclusivos_por_lote_e_motivo(painel):
    assert linhas(relatorio_html(painel), "tabela-inconclusivos-por-motivo") == [
        ["L2", "vista_lateral_ausente", "1"],
    ]


# ---------------------------------------------------------------- 6. discordancia


def test_discordancia_sem_base_nao_publica_taxa(painel_vazio):
    """Regra 2 no lugar onde ela mais importa: sem item com as duas laterais, o painel devolve
    0.0 por divisao de base vazia, e 0.0% na tela se leria como "nenhuma discordancia medida"."""
    html = relatorio_html(painel_vazio)
    assert celula(html, "discordancia-taxa") == SEM_DADO
    assert celula(html, "discordancia-itens-com-duas-laterais") == SEM_DADO
    assert celula(html, "discordancia-discordantes") == SEM_DADO


def test_zero_com_base_medida_nao_e_sem_dado(tmp_path):
    """A regra nao e "nunca mostre zero": e "nao mostre zero sem base". Com um item de duas laterais
    medidas, 0.0% e medicao, e tem que aparecer."""
    reg = Registro.abrir(tmp_path / "um.db")
    reg.registrar(
        _ev("i-A", T0, _completo(Classe.NORMAL, Classe.NORMAL), Classe.NORMAL)
    )
    html = relatorio_html(Painel(reg._cx))
    assert celula(html, "discordancia-itens-com-duas-laterais") == "1"
    assert celula(html, "discordancia-discordantes") == "0"
    assert celula(html, "discordancia-taxa") == "0.0%"
    reg.fechar()


# ---------------------------------------------------------------- 7. gatilho


def test_gatilho_por_fonte_com_falso_e_duplicado(painel):
    """e18_d80nk: 4 eventos (2 aceitos, 1 falso, 1 duplicado) -> 25.0% de falso.
    vl53l0x: 1 evento aceito -> 0.0% com base medida."""
    assert linhas(relatorio_html(painel), "tabela-gatilho-por-fonte") == [
        ["e18_d80nk", "4", "2", "1", "1", "0", "25.0%"],
        ["vl53l0x", "1", "1", "0", "0", "0", "0.0%"],
    ]


# ---------------------------------------------------------------- base vazia


def test_base_vazia_diz_sem_dado_em_toda_celula(painel_vazio):
    """Base vazia: nenhum numero e verdade, entao nenhuma celula pode mostrar numero. A unica
    excecao e a declaracao de perda de deteccao, que nao e contagem: e declaracao do painel."""
    html = relatorio_html(painel_vazio)
    esperado = {
        identificador: SEM_DADO
        for identificador in (
            "resumo-total",
            "resumo-aprovados",
            "resumo-defeitos",
            "resumo-inconclusivos",
            "resumo-erro-processamento",
            "resumo-conferencia-aprovacao",
            "discordancia-itens-com-duas-laterais",
            "discordancia-discordantes",
            "discordancia-taxa",
        )
    }
    esperado["gatilho-perda-de-deteccao-instrumentada"] = "nao"
    assert valores(html) == esperado
    assert not re.search(r"<dd[^>]*>\s*0\s*</dd>", html), (
        "zero apareceu numa base sem medicao"
    )


def test_base_vazia_diz_sem_dado_em_todo_quadro(painel_vazio):
    html = relatorio_html(painel_vazio)
    for identificador in TABELAS:
        assert linhas(html, identificador) == [[SEM_DADO]]
    # e a nota diz QUAL consulta ficou sem linha, para nao parecer quadro quebrado
    assert "a consulta contagem_por_estado nao devolveu nenhuma linha" in html
    assert "a consulta gatilho_por_fonte nao devolveu nenhuma linha" in html


# ---------------------------------------------------------------- escape


def test_texto_do_banco_e_escapado(painel_com_texto_hostil):
    """Texto que vem do banco nao pode virar marcacao, e tambem nao pode sumir: escapar errado
    seria perder o dado, nao escapado seria quebrar o documento."""
    html = relatorio_html(painel_com_texto_hostil)
    assert "<script>" not in html
    assert "<b>DEFEITO</b>" not in html
    assert "<i>" not in html
    assert "<b>x</b>" not in html
    # e o texto tem que continuar visivel, escapado
    assert "L1&lt;script&gt;" in html
    assert "&lt;b&gt;DEFEITO&lt;/b&gt;" in html
    assert "motivo&quot;&lt;i&gt;" in html
    assert "ev/&lt;b&gt;x&lt;/b&gt;.jpg" in html


def test_codigo_com_texto_hostil_chega_escapado_nas_tabelas(painel_com_texto_hostil):
    """O escape e ponto unico no renderizador: vale para `lote_id`, `motivo` e tambem para o codigo
    do catalogo, que e texto do banco como qualquer outro."""
    html = relatorio_html(painel_com_texto_hostil)
    assert linhas(html, "tabela-defeitos-frequentes") == [
        ["&lt;b&gt;DEFEITO&lt;/b&gt;", "critico", "1"],
        ["SEM_SEVERIDADE_LEVE", "nao declarado", "1"],
    ]
    assert linhas(html, "tabela-taxa-por-lote") == [
        ["L1&lt;script&gt;", "2", "0", "1", "0.0%"]
    ]
    assert linhas(html, "tabela-inconclusivos-por-motivo") == [
        ["L1&lt;script&gt;", "motivo&quot;&lt;i&gt;", "1"],
    ]
    assert linhas(html, "tabela-itens-criticos") == [
        [
            "i-F",
            "&lt;b&gt;DEFEITO&lt;/b&gt;",
            "critico",
            "lateral1",
            "ev/&lt;b&gt;x&lt;/b&gt;.jpg",
        ],
    ]


# ---------------------------------------------------------------- guardas do proprio contrato


def test_tabela_recusa_linha_fora_do_formato():
    """Linha com numero de celulas diferente do cabecalho geraria HTML torto em silencio."""
    with pytest.raises(ValueError):
        Tabela(identificador="t", titulo="t", colunas=("a", "b"), linhas=(("1",),))
    with pytest.raises(ValueError):
        Tabela(identificador="t", titulo="t", colunas=(), linhas=())
    with pytest.raises(ValueError):
        Tabela(identificador="", titulo="t", colunas=("a",), linhas=())


def test_celula_recusa_identificador_e_rotulo_vazios():
    """Numero sem rotulo mente por omissao; celula sem id nao pode ser exigida por nenhum teste."""
    with pytest.raises(ValueError):
        Celula(identificador="", rotulo="r", valor="1")
    with pytest.raises(ValueError):
        Celula(identificador="c", rotulo="", valor="1")


# ---------------------------------------------------------------- de arquivo a arquivo


def test_cli_gera_o_relatorio_de_um_arquivo_de_banco(tmp_path):
    """O artefato tem que nascer de um banco na linha de comando, sem servidor e sem pacote
    instalado: este teste prova que ele existe nesse formato."""
    caminho = tmp_path / "linha.db"
    reg = Registro.abrir(caminho)
    reg.registrar(
        _ev("i-A", T0, _completo(Classe.NORMAL, Classe.NORMAL), Classe.NORMAL)
    )
    reg.fechar()

    saida = subprocess.run(
        [sys.executable, str(RAIZ / "apresentacao.py"), str(caminho)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert '<section id="resumo">' in saida.stdout
    assert celula(saida.stdout, "resumo-aprovados") == "1"
    assert celula(saida.stdout, "resumo-inconclusivos") == "0"

    sem_argumento = subprocess.run(
        [sys.executable, str(RAIZ / "apresentacao.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert sem_argumento.returncode == 2
    assert "uso: apresentacao.py" in sem_argumento.stdout


def test_cli_com_banco_inexistente_falha_sem_gerar_relatorio(tmp_path):
    """Banco que nao existe nao pode virar HTML: um relatorio sem linha tem cara de "sistema sem
    defeito". O processo falha e nao escreve nada na saida."""
    saida = subprocess.run(
        [
            sys.executable,
            str(RAIZ / "apresentacao.py"),
            str(tmp_path / "nao_existe.db"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert saida.returncode != 0
    assert saida.stdout == ""
