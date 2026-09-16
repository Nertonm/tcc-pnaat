"""Apresentacao: o elo `apresenta` da conjectura, onde as consultas do painel viram HTML estatico.

Por que este modulo existe, e o que ele se recusa a fazer:

  * o registro ja grava e o painel ja responde; faltava o elo que apresenta. Relatorio e justamente
    onde um numero errado passa despercebido, porque ninguem confere tabela por tabela. Por isso as
    tres regras abaixo sao comportamento testado, nao recomendacao de estilo:
      1. inconclusivo NUNCA aparece somado a aprovado. Item sem evidencia suficiente nao e item
         bom, e rotulo que mente custa mais caro que numero errado, porque nao da para perceber;
      2. consulta sem dado vira `SEM_DADO`, nunca 0. Zero na tela se le como "nenhum defeito", e
         ausencia de medicao nao e medicao de ausencia: a D-04 vale tambem para quem le o relatorio;
      3. todo numero sai de uma consulta do painel. Este modulo nao calcula indicador novo: quando
         o painel nao responde, a lacuna fica visivel em vez de preenchida.
  * HTML estatico, uma string, sem servidor e sem dependencia externa (somente a biblioteca padrao):
    o artefato tem que abrir de arquivo anos depois, sem infraestrutura viva. Relatorio que depende
    de servico para ser lido deixa de ser evidencia.
  * nao ha carimbo de data/hora na saida: o mesmo banco tem que produzir os mesmos bytes. Quem data
    o artefato e o sistema de arquivos; carimbar o conteudo o tornaria irreproduzivel.
  * o que NAO esta nesta fatia, de proposito: latencia por vista, saturacao por vista, saude dos
    nos, tendencia por hora, correcoes para auditoria, separacoes nao confirmadas e distribuicao por
    dominio. Cada bloco que entra tem valor conferido celula por celula nos testes; bloco que
    entrasse sem essa conferencia seria so mais uma tabela bonita que ninguem validou.

Escape: quem renderiza escapa (`_escapar`), num ponto unico. Assim nenhum construtor de bloco
precisa lembrar de escapar `lote_id`, `motivo_inconclusivo` ou `codigo_defeito`, que sao texto do
banco e podem conter `<`.

Contratos: `Celula`, `Tabela`, `Secao` e `Relatorio`, todos dataclasses congeladas. Nenhuma funcao
daqui devolve `dict` cru; o unico dicionario em jogo e o que `painel.contagem_por_estado()` ja
devolve.
"""

from __future__ import annotations

import html
import sys
from collections.abc import Sized
from dataclasses import dataclass
from enum import Enum

from painel import Painel

#: Literal unico de ausencia de dado. Existe como constante para o teste exigir o MESMO texto em
#: todo bloco: se cada bloco inventasse o seu ("n/d", "-", "0"), a regra nao teria ponto unico de
#: verificacao e um bloco poderia escapar dela sem ninguem notar.
SEM_DADO = "sem dado"
#: Celula de tabela com valor NULL no banco. Nao e o mesmo que `SEM_DADO` (consulta sem linha):
#: aqui a linha existe e falta o campo. A celula diz qual campo falta em vez de ficar vazia, que se
#: leria como "sem defeito".
NAO_DECLARADO = "nao declarado"
#: Item critico cuja linha nao tem caminho de evidencia. A ausencia fica escrita, porque o leitor
#: precisa saber que o rastro nao esta registrado; deduzir o caminho a partir do `item_id` seria
#: inventar prova.
SEM_EVIDENCIA = "sem evidencia registrada"
#: Unico status do registro que conta como aprovacao.
SOMENTE_OK = "ok"

AVISO = (
    "Relatorio estatico gerado a partir das consultas do painel. Nenhum numero foi digitado a "
    f"mao: onde a consulta nao devolveu dado esta escrito '{SEM_DADO}', e inconclusivo nao "
    "entra na contagem de aprovados."
)
RODAPE = (
    "Gerado por apresentacao.relatorio_html() com a biblioteca padrao do Python. "
    "Arquivo autocontido: abre de arquivo, sem servidor."
)


class PapelNaAprovacao(str, Enum):
    """Se o estado conta como aprovacao. Enum, e nao bool solto, para o numero aparecer na tela
    junto do rotulo: quem le ve "inconclusivo -> nao" sem precisar confiar na coluna nem em mim."""

    CONTA = "sim"
    NAO_CONTA = "nao"


def papel_na_aprovacao(estado: str) -> PapelNaAprovacao:
    """Diz se o estado conta como aprovacao. SO `ok` conta.

    Por que a funcao existe em vez de um conjunto literal no meio do bloco: a decisao precisa de um
    lugar onde o padrao seja a recusa. Estado que nao esta no vocabulario do esquema, inclusive um
    que o esquema nao descreve, nao vira aprovacao por omissao (fail-closed).
    """
    return (
        PapelNaAprovacao.CONTA if estado == SOMENTE_OK else PapelNaAprovacao.NAO_CONTA
    )


# ---------------------------------------------------------------- contratos


@dataclass(frozen=True)
class Celula:
    """Um valor do relatorio com identidade estavel.

    `valor=None` significa "a consulta nao tem dado" e e renderizado como `SEM_DADO`. String vazia
    nao serve: `""` e `0` parecem iguais na tela, e a regra deste relatorio e exatamente nao deixar
    ausencia passar por numero. O identificador e o que permite ao teste exigir o numero certo no
    lugar certo, em vez de procurar um digito em qualquer parte do HTML.
    """

    identificador: str
    rotulo: str
    valor: str | None
    nota: str = ""

    def __post_init__(self) -> None:
        if not self.identificador:
            raise ValueError("celula sem identificador nao e auditavel")
        if not self.rotulo:
            raise ValueError(
                f"celula {self.identificador!r} sem rotulo: numero sem rotulo mente"
            )


@dataclass(frozen=True)
class Tabela:
    """Quadro do relatorio. `linhas` vazia nao vira tabela vazia: vira `SEM_DADO` com nota que diz
    qual consulta ficou sem linha: sem a nota, tabela vazia e indistinguivel de dado nao carregado.
    """

    identificador: str
    titulo: str
    colunas: tuple[str, ...]
    linhas: tuple[tuple[str, ...], ...]
    nota: str = ""

    def __post_init__(self) -> None:
        if not self.identificador:
            raise ValueError("tabela sem identificador nao e auditavel")
        if not self.colunas:
            raise ValueError(
                f"tabela {self.identificador!r} sem coluna nao tem o que apresentar"
            )
        largura = len(self.colunas)
        for linha in self.linhas:
            if len(linha) != largura:
                raise ValueError(
                    f"tabela {self.identificador!r}: linha com {len(linha)} celula(s) para "
                    f"{largura} coluna(s)"
                )

    @property
    def vazia(self) -> bool:
        return not self.linhas


@dataclass(frozen=True)
class Secao:
    """Bloco de apresentacao: celulas (valores soltos), tabelas e a nota que explica o recorte."""

    identificador: str
    titulo: str
    celulas: tuple[Celula, ...] = ()
    tabelas: tuple[Tabela, ...] = ()
    nota: str = ""


@dataclass(frozen=True)
class Relatorio:
    """O relatorio inteiro antes de virar HTML: e o que os testes conferem sem regex."""

    titulo: str
    secoes: tuple[Secao, ...]


# ---------------------------------------------------------------- apoio de formatacao


def _exibivel(valor: str | None) -> str:
    """Valor ausente vira o literal unico de ausencia, nunca texto vazio."""
    return SEM_DADO if valor is None else valor


def _num(valor: int | None) -> str | None:
    """Inteiro ja contado por uma consulta, ou ausencia. Existe para `None` nao virar "None" na
    tela nem 0: 0 e uma contagem, ausencia nao e."""
    return None if valor is None else str(valor)


def _pct(fracao: float) -> str:
    """Taxa como porcentagem com uma casa. Arredonda a exibicao, nao o dado: as parcelas seguem
    inteiras na mesma tabela, entao o leitor pode refazer a conta."""
    return f"{fracao:.1%}"


def _sim_nao(valor: bool) -> str:
    """Booleano do dominio virando rotulo. `sim`/`nao` explicitos porque celula vazia em campo
    booleano se le como ausencia de dado."""
    return "sim" if valor else "nao"


def _nota_sem_linha(linhas: Sized, consulta: str) -> str:
    """Nota para quadro sem linha. Diz QUAL consulta ficou sem dado, para o leitor nao precisar
    adivinhar se a tabela esta vazia porque nao ha defeito ou porque nada foi medido."""
    if len(linhas) > 0:
        return ""
    return (
        f"a consulta {consulta} nao devolveu nenhuma linha, entao o quadro mostra "
        f"'{SEM_DADO}': nao ha medicao por tras de um zero aqui"
    )


# ---------------------------------------------------------------- 1. resumo


def secao_resumo(painel: Painel) -> Secao:
    """Resumo da base, com a contagem de aprovados conferida contra a contagem por estado.

    Por que duas consultas aparecem em celulas separadas: `contagem_por_estado()` e `aprovados()`
    sao chamadas independentes, e o relatorio CONFERE uma contra a outra. Se algum dia a contagem
    passar a incluir `inconclusivo` em `ok`, o relatorio mostra a divergencia em vez de escolher o
    numero que conta a historia mais confortavel.
    """
    estados = painel.contagem_por_estado()
    aprovados = painel.aprovados()
    tem_base = len(estados) > 0
    total = sum(estados.values()) if tem_base else None

    def por_estado(chave: str) -> str | None:
        """Contagem do estado. Sem item nenhum no banco nao existe contagem: 0 ali seria leitura de
        "nada aprovado" quando o caso e "nada medido"."""
        return _num(estados.get(chave, 0)) if tem_base else None

    celulas = (
        Celula(
            "resumo-total",
            "total de itens",
            _num(total),
            nota="soma da contagem por estado (contagem_por_estado)",
        ),
        Celula(
            "resumo-aprovados",
            "aprovados (somente status ok)",
            _num(aprovados) if tem_base else None,
            nota="consulta aprovados(): inconclusivo NAO entra neste numero; soma-lo seria "
            "rotulo que mente",
        ),
        Celula("resumo-defeitos", "defeitos", por_estado("defeito")),
        Celula(
            "resumo-inconclusivos",
            "inconclusivos (fora dos aprovados)",
            por_estado("inconclusivo"),
            nota="item sem evidencia suficiente: aparece separado dos aprovados, nunca dentro",
        ),
        Celula(
            "resumo-erro-processamento",
            "erro_processamento (fora dos aprovados)",
            por_estado("erro_processamento"),
        ),
        Celula(
            "resumo-conferencia-aprovacao",
            "conferencia da aprovacao",
            _conferencia(estados, aprovados, tem_base),
            nota="as duas consultas de aprovacao sao comparadas aqui; o relatorio nao escolhe "
            "um dos numeros quando eles divergem",
        ),
    )
    tabela = Tabela(
        identificador="tabela-por-estado",
        titulo="Itens por estado, e o que conta como aprovacao",
        colunas=("estado", "itens", "conta como aprovacao"),
        linhas=tuple(
            (estado, str(itens), papel_na_aprovacao(estado).value)
            for estado, itens in sorted(estados.items())
        ),
        nota=_nota_sem_linha(estados, "contagem_por_estado"),
    )
    return Secao(
        "resumo",
        "Resumo",
        celulas,
        (tabela,),
        nota="A coluna 'conta como aprovacao' e a resposta a pergunta que o resumo nao "
        "pode deixar implicita: so `ok` aprova.",
    )


def _conferencia(estados: dict[str, int], aprovados: int, tem_base: bool) -> str | None:
    """Compara as duas consultas de aprovacao. Sem base nao ha o que conferir."""
    if not tem_base:
        return None
    contados = estados.get(SOMENTE_OK, 0)
    if contados == aprovados:
        return f"as duas consultas concordam: {aprovados}"
    return (
        f"divergencia entre consultas: aprovados()={aprovados}, contagem de ok={contados}; "
        "o relatorio nao escolheu nenhum dos dois"
    )


# ---------------------------------------------------------------- 2. lote


def secao_taxa_por_lote(painel: Painel) -> Secao:
    """Taxa de defeito por lote, com inconclusivos na mesma linha.

    Por que os inconclusivos ficam ao lado e nunca somados aos defeitos: um lote com item nao medido
    nao tem taxa confiavel, e mostrar so a taxa esconderia justamente a parcela que impede a
    conclusao.
    """
    linhas = painel.taxa_de_defeito_por_lote()
    tabela = Tabela(
        identificador="tabela-taxa-por-lote",
        titulo="Taxa de defeito por lote",
        colunas=("lote", "itens", "defeitos", "inconclusivos", "taxa de defeito"),
        linhas=tuple(
            (
                lote.lote_id,
                str(lote.itens),
                str(lote.defeitos),
                str(lote.inconclusivos),
                _pct(lote.taxa_defeito),
            )
            for lote in linhas
        ),
        nota=_nota_sem_linha(linhas, "taxa_de_defeito_por_lote"),
    )
    return Secao(
        "taxa-por-lote",
        "Defeito por lote",
        (),
        (tabela,),
        nota="A taxa e defeitos/itens do proprio lote; os inconclusivos aparecem como "
        "coluna e nao entram na conta.",
    )


# ---------------------------------------------------------------- 3. defeitos frequentes


def secao_defeitos_frequentes(painel: Painel) -> Secao:
    """Defeitos mais frequentes com a severidade declarada no catalogo.

    Por que a severidade aparece como coluna e nao como ordem: sem severidade o ranking e so
    frequencia. `NAO_DECLARADO` e o campo NULL da taxonomia: o relatorio nao deduz severidade a
    partir do codigo.
    """
    linhas = painel.defeitos_frequentes()
    tabela = Tabela(
        identificador="tabela-defeitos-frequentes",
        titulo="Defeitos mais frequentes",
        colunas=("codigo do defeito", "severidade", "ocorrencias"),
        linhas=tuple(
            (d.codigo, d.severidade or NAO_DECLARADO, str(d.ocorrencias))
            for d in linhas
        ),
        nota=_nota_sem_linha(linhas, "defeitos_frequentes"),
    )
    return Secao(
        "defeitos-frequentes",
        "Defeitos frequentes",
        (),
        (tabela,),
        nota=f"severidade '{NAO_DECLARADO}' e campo NULL na taxonomia_defeito: falta o "
        "dado, nao e defeito leve.",
    )


# ---------------------------------------------------------------- 4. itens criticos


def secao_itens_criticos(painel: Painel) -> Secao:
    """Itens com defeito de severidade critico, cada um com a referencia de evidencia.

    Por que a evidencia e coluna obrigatoria: item critico sem rastro registrado precisa aparecer
    assim, como ausencia. Esconder a linha, ou preencher o caminho por deducao do `item_id`, seria
    apresentar prova que nao existe.
    """
    linhas = painel.itens_criticos()
    tabela = Tabela(
        identificador="tabela-itens-criticos",
        titulo="Itens criticos e a referencia de evidencia",
        colunas=(
            "item",
            "codigo do defeito",
            "severidade",
            "vista",
            "referencia de evidencia",
        ),
        linhas=tuple(
            (
                i.item_id,
                i.codigo_defeito,
                i.severidade,
                i.vista,
                i.caminho_evidencia or SEM_EVIDENCIA,
            )
            for i in linhas
        ),
        nota=_nota_sem_linha(linhas, "itens_criticos"),
    )
    return Secao(
        "itens-criticos",
        "Itens criticos",
        (),
        (tabela,),
        nota=f"'{SEM_EVIDENCIA}' e ausencia registrada: o item e critico e o rastro nao "
        "esta no banco.",
    )


# ---------------------------------------------------------------- 5. inconclusivos


def secao_inconclusivos_por_motivo(painel: Painel) -> Secao:
    """Inconclusivos agrupados por lote e motivo declarado.

    Por que este bloco existe separado: inconclusivo nao e defeito nem aprovacao. Sem a lista de
    motivos, o item nao medido sumiria do relatorio (ficaria so na conta de "nao aprovados") e
    ninguem saberia se o problema e captura, vista faltante ou evidencia insuficiente.
    """
    linhas = painel.inconclusivos_por_lote()
    tabela = Tabela(
        identificador="tabela-inconclusivos-por-motivo",
        titulo="Inconclusivos por lote e motivo",
        colunas=("lote", "motivo do inconclusivo", "ocorrencias"),
        linhas=tuple((i.lote_id, i.motivo, str(i.ocorrencias)) for i in linhas),
        nota=_nota_sem_linha(linhas, "inconclusivos_por_lote"),
    )
    return Secao(
        "inconclusivos-por-motivo",
        "Inconclusivos por motivo",
        (),
        (tabela,),
        nota="Estes itens nao estao aprovados e nao estao reprovados: precisam de "
        "decisao humana.",
    )


# ---------------------------------------------------------------- 6. discordancia lateral


def secao_discordancia_lateral(painel: Painel) -> Secao:
    """Discordancia entre as duas laterais de um mesmo item.

    Por que a base e conferida antes da taxa: `discordancia_lateral()` devolve taxa 0.0 tanto para
    "nenhum discordante entre os itens medidos" quanto para "nenhum item com as duas laterais". Sao
    coisas diferentes, e o relatorio recusa publicar taxa quando a base e zero (divisao de base
    vazia), mostra `SEM_DADO` nas tres celulas.
    """
    d = painel.discordancia_lateral()
    tem_base = d.itens_com_duas_laterais > 0
    celulas = (
        Celula(
            "discordancia-itens-com-duas-laterais",
            "itens com as duas laterais medidas",
            _num(d.itens_com_duas_laterais) if tem_base else None,
            nota="base da taxa: item com as duas laterais decisorias; vista unica nao e "
            "discordancia",
        ),
        Celula(
            "discordancia-discordantes",
            "itens discordantes",
            _num(d.discordantes) if tem_base else None,
            nota="item cujas laterais decisorias nao emitiram a mesma classe",
        ),
        Celula(
            "discordancia-taxa",
            "taxa de discordancia",
            _pct(d.taxa) if tem_base else None,
            nota="com base zero a consulta devolve 0.0 por divisao de base vazia: o relatorio "
            f"diz '{SEM_DADO}' em vez de publicar uma taxa que nao existe",
        ),
    )
    return Secao(
        "discordancia",
        "Discordancia lateral",
        celulas,
        (),
        nota="Discordancia e sinal de conflito entre vistas, nao de defeito: o item fica "
        "marcado para revisao.",
    )


# ---------------------------------------------------------------- 7. gatilho


def secao_gatilho_por_fonte(painel: Painel) -> Secao:
    """Disparo falso, duplicado e invalido por fonte do gatilho.

    Por que a celula de perda de deteccao esta aqui, ao lado do quadro: o gatilho so registra o
    disparo que ACONTECEU. O item que passou sem disparar nao deixa evento, e sem esta celula a
    ausencia se leria como linha limpa. O painel declara que a grandeza nao esta instrumentada; o
    relatorio repete a declaracao em vez de omitir a lacuna.
    """
    linhas = painel.gatilho_por_fonte()
    perda = painel.perda_de_deteccao()
    tabela = Tabela(
        identificador="tabela-gatilho-por-fonte",
        titulo="Gatilho por fonte: falso, duplicado e invalido",
        colunas=(
            "fonte",
            "eventos",
            "aceitos",
            "falsos",
            "duplicados",
            "invalidos",
            "taxa de falso",
        ),
        linhas=tuple(
            (
                g.fonte,
                str(g.eventos),
                str(g.aceitos),
                str(g.falsos),
                str(g.duplicados),
                str(g.invalidos),
                _pct(g.taxa_falso),
            )
            for g in linhas
        ),
        nota=_nota_sem_linha(linhas, "gatilho_por_fonte"),
    )
    celulas = (
        Celula(
            "gatilho-perda-de-deteccao-instrumentada",
            "perda de deteccao instrumentada",
            _sim_nao(perda.instrumentada),
            nota=f"declaracao do painel, nao medicao: {perda.motivo}",
        ),
    )
    return Secao(
        "gatilho",
        "Gatilho por fonte",
        celulas,
        (tabela,),
        nota="A taxa de falso e falsos/eventos da propria fonte; o disparo que nao virou "
        "item entra nessa conta.",
    )


# ---------------------------------------------------------------- montagem e HTML


def montar_relatorio(painel: Painel) -> Relatorio:
    """Consulta uma vez cada bloco e devolve a estrutura do relatorio, ainda sem HTML.

    Por que separar de `renderizar`: o dado apresentado pode ser conferido sem regex em HTML, e o
    HTML pode ser conferido sem banco. Um so corpo de funcao faria os dois e nenhum teste saberia
    qual dos dois falhou.
    """
    return Relatorio(
        titulo="Relatorio de inspecao de itens (iamralp)",
        secoes=(
            secao_resumo(painel),
            secao_taxa_por_lote(painel),
            secao_defeitos_frequentes(painel),
            secao_itens_criticos(painel),
            secao_inconclusivos_por_motivo(painel),
            secao_discordancia_lateral(painel),
            secao_gatilho_por_fonte(painel),
        ),
    )


def relatorio_html(painel: Painel) -> str:
    """O elo `apresenta`: o painel entra, uma string HTML pronta para abrir de arquivo sai."""
    return renderizar(montar_relatorio(painel))


def _escapar(texto: str) -> str:
    """Ponto unico de escape do HTML: passa por aqui o texto do banco (`lote_id`, `motivo`,
    `codigo`) e tambem o nosso. Escapar num so lugar e o que impede o esquecimento num bloco novo
    de virar HTML quebrado; nenhum construtor de bloco chama `html.escape` por conta propria."""
    return html.escape(texto, quote=True)


def renderizar(relatorio: Relatorio) -> str:
    """Relatorio -> string HTML. Pura: a mesma estrutura produz exatamente a mesma saida."""
    partes = [
        "<!DOCTYPE html>",
        '<html lang="pt-BR">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{_escapar(relatorio.titulo)}</title>",
        "<style>",
        _CSS,
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{_escapar(relatorio.titulo)}</h1>",
        f'<p class="aviso">{_escapar(AVISO)}</p>',
    ]
    for indice, secao in enumerate(relatorio.secoes, start=1):
        partes.append(_render_secao(indice, secao))
    partes += [
        "<footer>",
        f"<p>{_escapar(RODAPE)}</p>",
        "</footer>",
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(partes)


def _render_secao(indice: int, secao: Secao) -> str:
    """Bloco do relatorio. A numeracao vem da posicao, para o texto nao ter um numero escrito a mao
    que desandaria ao reordenar as secoes."""
    partes = [
        f'<section id="{_escapar(secao.identificador)}">',
        f"<h2>{indice}. {_escapar(secao.titulo)}</h2>",
    ]
    if secao.celulas:
        partes.append("<dl>")
        partes.extend(_render_celula(c) for c in secao.celulas)
        partes.append("</dl>")
    if secao.nota:
        partes.append(f'<p class="nota">{_escapar(secao.nota)}</p>')
    partes.extend(_render_tabela(t) for t in secao.tabelas)
    partes.append("</section>")
    return "\n".join(partes)


def _render_celula(celula: Celula) -> str:
    """Celula com o valor visivel e o identificador estavel. A classe `sem-dado` existe para a
    ausencia ter aparencia propria em vez de parecer um numero baixo."""
    classe = "valor sem-dado" if celula.valor is None else "valor"
    partes = [
        '    <div class="celula">',
        f"      <dt>{_escapar(celula.rotulo)}</dt>",
        (
            f'      <dd class="{classe}" id="{_escapar(celula.identificador)}">'
            f"{_escapar(_exibivel(celula.valor))}</dd>"
        ),
    ]
    if celula.nota:
        partes.append(f'      <p class="nota">{_escapar(celula.nota)}</p>')
    partes.append("    </div>")
    return "\n".join(partes)


def _render_tabela(tabela: Tabela) -> str:
    """Quadro. Sem linha, o corpo recebe uma unica celula com `SEM_DADO` ocupando a largura toda,
    diferente de um `tbody` vazio, que na tela se le como "nenhum defeito"."""
    partes = [
        f'<table id="{_escapar(tabela.identificador)}">',
        f"  <caption>{_escapar(tabela.titulo)}</caption>",
        "  <thead><tr>"
        + "".join(f"<th>{_escapar(coluna)}</th>" for coluna in tabela.colunas)
        + "</tr></thead>",
        "  <tbody>",
    ]
    if tabela.vazia:
        partes.append(
            f'    <tr><td class="sem-dado" colspan="{len(tabela.colunas)}">'
            f"{SEM_DADO}</td></tr>"
        )
    else:
        for linha in tabela.linhas:
            partes.append(
                "    <tr>"
                + "".join(f"<td>{_escapar(valor)}</td>" for valor in linha)
                + "</tr>"
            )
    partes += ["  </tbody>", "</table>"]
    if tabela.nota:
        partes.append(f'<p class="nota">{_escapar(tabela.nota)}</p>')
    return "\n".join(partes)


_CSS = """\
body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 60rem; color: #1b1b1b;
       line-height: 1.4; }
h1 { font-size: 1.35rem; }
h2 { font-size: 1.05rem; margin-top: 2rem; border-bottom: 1px solid #ccc; padding-bottom: .2rem; }
.aviso, .nota { color: #6b5b00; font-size: .82rem; }
dl { margin: 0; }
.celula { display: inline-block; min-width: 15rem; vertical-align: top; margin: .6rem 1.2rem .6rem 0; }
.celula dt { font-size: .72rem; text-transform: uppercase; color: #555; }
.celula dd { margin: .1rem 0 0; font-size: 1.25rem; }
.celula dd.sem-dado { font-size: .95rem; }
table { border-collapse: collapse; margin: .6rem 0; }
caption { text-align: left; font-weight: 600; padding-bottom: .3rem; }
th, td { border: 1px solid #ccc; padding: .25rem .6rem; text-align: left; font-size: .88rem; }
th { background: #f2f2f2; }
td.sem-dado { background: #fff6d6; }
footer p { color: #555; font-size: .8rem; margin-top: 2rem; }
"""


# ---------------------------------------------------------------- linha de comando


def _principal(argumentos: list[str]) -> int:
    """Gera o relatorio a partir de um arquivo de banco. Uso:
    `python apresentacao.py CAMINHO_DO_BANCO > relatorio.html`.

    Por que existe: o artefato tem que nascer de um banco na linha de comando, sem servidor e sem
    pacote instalado. Banco inexistente levanta a excecao do sqlite em vez de imprimir um relatorio
    vazio: um HTML vazio tem cara de "sistema sem defeito".
    """
    if len(argumentos) != 1:
        print("uso: apresentacao.py CAMINHO_DO_BANCO")
        return 2
    painel = Painel.abrir(argumentos[0])
    print(relatorio_html(painel))
    return 0


if __name__ == "__main__":
    raise SystemExit(_principal(sys.argv[1:]))
