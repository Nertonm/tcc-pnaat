"""Fonte de eventos de gatilho do release: le o CSV do ensaio e o persiste no registro.

Por que esta fonte existe: RF-01.1 (`docs/requisitos/01-funcionais.md:25`) exige UM evento de
gatilho por passagem, com timestamp, debounce e identificacao da origem, e o criterio de
reprovacao cobre disparo falso, evento duplicado e ausencia de registro quando o sinal for
invalido. O gatilho e gravado SEPARADO do item (`esquema.sql`, tabela `evento_gatilho`)
justamente porque o disparo que nao virou item precisa entrar: e o unico jeito de falso disparo,
duplicata e sinal invalido ficarem observaveis (`painel.gatilho_por_fonte`).

O CSV e a ENTRADA. O arquivo e o que a bancada/ensaio gravou; este modulo nao gera evento
sintetico, nao preenche linha faltante, nao inventa `item_id`, nao cria item e nao conserta token
fora do vocabulario. Ler um ensaio e transcrever, nao produzir.

Estado fora de `aceito|duplicado|falso|invalido` derruba o ARQUIVO INTEIRO
(`EstadoForaDoVocabulario`): se o estado da linha nao pertence ao vocabulario, nao se sabe o que a
linha e, nao e um evento a menos, e um arquivo que este leitor nao sabe ler. O arquivo e validado
por COMPLETO antes do primeiro INSERT, entao a falha fica observavel no banco (nada gravado), e
nao so na excecao. Cabecalho fora do contrato falha pelo mesmo motivo e com a mesma garantia.

O que esta fonte NAO verifica, e por que nao:
  - PERDA DE DETECCAO (item passou sem disparar): nenhum evento de gatilho existe para ela; o
    gatilho prova o que disparou, e o item que passou sem disparar nao deixou registro. Medir isso
    exige referencia externa: contagem do encoder KY-040 (decisao D-21). Por isso o resumo carrega
    a declaracao `perda_de_deteccao` em vez de um zero que pareceria medicao, em linha com
    `painel.perda_de_deteccao()`;
  - MONOTONICIDADE do timestamp (RF-01.1): ela e propriedade do relogio do ESP32 no momento da
    passagem, nao de um arquivo relido depois. Aqui se verifica que cada timestamp e um instante
    absoluto (com fuso, senao nao e rastreavel); a ordem do arquivo e preservada como ordem de
    gravacao, sem reordenar nem deduzir o que veio antes;
  - REINGESTAO: processar o mesmo arquivo duas vezes grava duas vezes. `evento_gatilho` nao tem
    chave natural e inventar uma (hash da linha) seria inventar identidade. Ingerir o mesmo ensaio
    duas vezes e erro de operacao do ensaio, e aparece somado em `painel.gatilho_por_fonte()`.

Sem `dict[str, Any]`: a entrada e `EventoDeGatilho`, a saida e `ResumoDaFonte`.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import IO

from registro import EventoInvalido, Registro

# ---------------------------------------------------------------- contrato do arquivo

COLUNA_TIMESTAMP = "timestamp"
COLUNA_ESTADO = "estado"
COLUNA_FONTE = "fonte"
COLUNA_MOTIVO = "motivo"
COLUNA_ITEM = "item_id"
COLUNA_DEBOUNCE = "debounce_ms"

COLUNAS_OBRIGATORIAS: tuple[str, ...] = (COLUNA_TIMESTAMP, COLUNA_ESTADO, COLUNA_FONTE)
#: Uma coluna que este leitor nao conhece seria dado do ensaio jogado fora em silencio (o caso real
#: e a coluna escrita como `item` no lugar de `item_id`, que perderia todo vinculo do arquivo).
#: Coluna desconhecida recusa o cabecalho inteiro; a ordem das colunas, por outro lado, nao importa:
#: a leitura e por NOME.
COLUNAS_ACEITAS: tuple[str, ...] = COLUNAS_OBRIGATORIAS + (
    COLUNA_MOTIVO,
    COLUNA_ITEM,
    COLUNA_DEBOUNCE,
)

#: RF-01.1: o evento de gatilho torna observaveis o disparo falso, o duplicado e o sinal invalido. A
#: perda de deteccao NAO esta nessa lista e nao pode ser reportada como zero: exige referencia
#: externa (contagem do encoder KY-040, D-21).
PERDA_DE_DETECCAO = (
    "perda de deteccao (item passou sem disparar) nao e observavel pelo gatilho: "
    "exige referencia externa (contagem do encoder KY-040, D-21)"
)

#: debounce em milissegundos: inteiro nao negativo. Outra grafia ('-5', '50ms', ' 50') e recusada em
#: vez de interpretada; normalizar o token seria gravar um numero que o arquivo nao disse.
_DEBOUNCE_INTEIRO = re.compile(r"[0-9]+")


class EstadoDeGatilho(str, Enum):
    """Vocabulario fechado de RF-01.1, o mesmo `CHECK` de `evento_gatilho.estado`."""

    ACEITO = "aceito"
    DUPLICADO = "duplicado"
    FALSO = "falso"
    INVALIDO = "invalido"


class FonteDeGatilho(str, Enum):
    """Origem declarada do disparo (`evento_gatilho.fonte`).

    `NAO_DECLARADA` e ESTADO, nao recusa: o arquivo declarou que a origem nao foi identificada, e o
    esquema tem esse valor para isso (`captura.py` faz o mesmo com `no_janela=None`). Um valor
    PREENCHIDO fora do vocabulario e outra coisa: e uma origem que o arquivo diz ser algo que este
    leitor nao conhece, e gravar `nao_declarada` apagaria o que o arquivo disse.
    """

    E18_D80NK = "e18_d80nk"
    VL53L0X = "vl53l0x"
    AMBOS_CORRELACIONADOS = "ambos_correlacionados"
    NAO_DECLARADA = "nao_declarada"


ESTADOS: tuple[str, ...] = tuple(e.value for e in EstadoDeGatilho)
FONTES: tuple[str, ...] = tuple(f.value for f in FonteDeGatilho)


class ErroDeFonteDeGatilho(Exception):
    """O arquivo inteiro nao pode ser processado. Nada foi gravado."""


class ArquivoDeGatilhoIlegivel(ErroDeFonteDeGatilho):
    """O arquivo nao existe ou nao pode ser lido como texto utf-8."""


class CabecalhoInvalido(ErroDeFonteDeGatilho):
    """O cabecalho nao e o do contrato: sem ele nao ha coluna a interpretar."""


class EstadoForaDoVocabulario(ErroDeFonteDeGatilho):
    """Uma linha declara estado fora de `aceito|duplicado|falso|invalido`."""


class MotivoDeRecusa(str, Enum):
    """Por que UMA linha foi recusada sem ser gravada. Recusa nao e silencio: vai para o resumo."""

    TIMESTAMP_AUSENTE = "timestamp_ausente"  # campo vazio: sem instante nao ha evento
    TIMESTAMP_ILEGIVEL = "timestamp_ilegivel"  # nao e ISO 8601
    TIMESTAMP_SEM_FUSO = (
        "timestamp_sem_fuso"  # ISO 8601 sem deslocamento: nao rastreavel
    )
    FONTE_DESCONHECIDA = "fonte_desconhecida"  # valor preenchido fora do vocabulario
    DEBOUNCE_INVALIDO = "debounce_invalido"  # nao e inteiro nao negativo
    COLUNAS_DIVERGENTES = "colunas_divergentes"  # numero de campos != cabecalho
    ITEM_RECUSADO_PELO_REGISTRO = (
        "item_recusado_pelo_registro"  # quem recusou foi a API do registro
    )


@dataclass(frozen=True)
class Recusa:
    """Uma linha que NAO entrou no registro, com o motivo declarado.

    `linha` e a linha FISICA do arquivo (1 = cabecalho), a mesma que o operador ve no editor: um
    motivo com quebra de linha dentro do campo desloca as linhas seguintes, e o numero fisico e o
    unico que continua localizando a linha no arquivo.
    """

    linha: int
    motivo: MotivoDeRecusa
    #: texto do arquivo (ou da API do registro) que sustenta a recusa; None quando nao ha valor a citar
    detalhe: str | None = None


@dataclass(frozen=True)
class EventoDeGatilho:
    """Um evento de gatilho lido do arquivo, ja validado e ainda NAO gravado."""

    linha: int
    timestamp: datetime
    estado: EstadoDeGatilho
    fonte: FonteDeGatilho
    motivo: str | None = None
    #: None = o arquivo nao declarou vinculo. Nao existe default inventado: o gatilho precede o item
    #: (RF-01.1), entao aceito sem item e um estado legitimo, nao uma falta a preencher.
    item_id: str | None = None
    debounce_ms: int | None = None

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ErroDeFonteDeGatilho(
                f"linha {self.linha}: timestamp sem fuso horario nao e rastreavel"
            )


@dataclass(frozen=True)
class LeituraDoArquivo:
    """O que o arquivo diz, ja validado. Nada foi gravado: `processar` e quem grava."""

    eventos: tuple[EventoDeGatilho, ...]
    recusas: tuple[Recusa, ...]
    #: linhas em branco do arquivo: nao sao evento nem recusa, e tambem nao sao silencio; contadas.
    linhas_em_branco: int

    @property
    def linhas_de_dados(self) -> int:
        """Linhas com conteudo: cada uma ou vira evento, ou e recusada com motivo."""
        return len(self.eventos) + len(self.recusas)


@dataclass(frozen=True)
class ContagemPorEstado:
    estado: EstadoDeGatilho
    eventos: int


@dataclass(frozen=True)
class ResumoDaFonte:
    """O que o processamento fez. As invariantes sao conferidas na construcao (nao ha resumo solto).

    `por_estado` sai em `EstadoDeGatilho` (os QUATRO), com zero onde nao houve evento: um estado
    ausente do resumo seria indistinguivel de zero eventos, e o criterio de reprovacao de RF-01.1
    pergunta exatamente por falso disparo e duplicata.
    """

    #: linhas de dados do arquivo (fora o cabecalho e as linhas em branco)
    lidas: int
    #: ids devolvidos por `registro.registrar_gatilho`; um por evento gravado
    ids_criados: int
    por_estado: tuple[ContagemPorEstado, ...]
    #: em ordem de linha do arquivo, com o motivo de cada uma
    recusas: tuple[Recusa, ...]
    linhas_em_branco: int
    #: RF-01.1: declarada, nunca contada como zero (ver `PERDA_DE_DETECCAO`)
    perda_de_deteccao: str = PERDA_DE_DETECCAO

    def __post_init__(self) -> None:
        estados = tuple(c.estado for c in self.por_estado)
        if len(set(estados)) != len(estados) or set(estados) != set(EstadoDeGatilho):
            raise ErroDeFonteDeGatilho(
                "resumo sem os quatro estados canonicos, sem repeticao: estado ausente do resumo e "
                f"indistinguivel de zero eventos; lidos: {[e.value for e in estados]}"
            )
        if sum(c.eventos for c in self.por_estado) != self.ids_criados:
            raise ErroDeFonteDeGatilho(
                f"resumo nao fecha: por_estado soma {sum(c.eventos for c in self.por_estado)} e "
                f"ids_criados diz {self.ids_criados}"
            )
        if self.lidas != self.ids_criados + len(self.recusas):
            raise ErroDeFonteDeGatilho(
                "resumo nao fecha: cada linha do arquivo ou virou evento ou foi recusada com motivo "
                f"(lidas={self.lidas}, ids_criados={self.ids_criados}, recusadas={len(self.recusas)})"
            )

    @property
    def linhas_recusadas(self) -> int:
        return len(self.recusas)


class FonteDeCsvDeGatilho:
    """Le o CSV de eventos de gatilho ja gravado no ensaio (bancada) e o persiste no registro.

    Duas etapas, nesta ordem: `ler()` valida o arquivo inteiro (cabecalho, vocabulario de estado,
    timestamps) e so depois `processar(registro)` grava. Essa ordem e o que faz "estado fora do
    vocabulario FALHA o processamento inteiro" valer tambem no banco: nenhuma linha e gravada antes
    de o arquivo inteiro passar, e nada e reparado em silencio.
    """

    nome = "csv_de_gatilho"

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)

    # ---------------------------------------------------------- leitura (nao grava)

    def ler(self) -> LeituraDoArquivo:
        """Devolve o que o arquivo diz, ja validado. Nao toca no registro."""
        if not self.caminho.is_file():
            raise ArquivoDeGatilhoIlegivel(
                f"arquivo de gatilho inexistente: {self.caminho}"
            )
        try:
            with self.caminho.open("r", encoding="utf-8", newline="") as arquivo:
                return self._ler_de(arquivo)
        except UnicodeDecodeError as erro:
            raise ArquivoDeGatilhoIlegivel(
                f"{self.caminho} nao esta em utf-8: {erro}"
            ) from erro

    def _ler_de(self, arquivo: IO[str]) -> LeituraDoArquivo:
        """Cada linha de dados ou vira `EventoDeGatilho`, ou vira `Recusa`; nunca as duas, e nunca
        nenhuma das duas. `csv` (e nao `split`) porque o motivo do ensaio pode ter virgula, e o
        numero de campos e conferido contra o cabecalho: virgula nao escapada desloca as colunas, e
        reinterpretar a linha deslocada seria trocar evidencia por palpite."""
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor, None)
        if cabecalho is None:
            raise CabecalhoInvalido(
                f"{self.caminho}: arquivo vazio, sem cabecalho nao ha coluna nenhuma"
            )
        _validar_cabecalho(cabecalho, self.caminho)

        eventos: list[EventoDeGatilho] = []
        recusas: list[Recusa] = []
        em_branco = 0
        for campos in leitor:
            linha = leitor.line_num
            if all(campo == "" for campo in campos):
                em_branco += 1
                continue
            if len(campos) != len(cabecalho):
                recusas.append(
                    Recusa(
                        linha,
                        MotivoDeRecusa.COLUNAS_DIVERGENTES,
                        f"esperado {len(cabecalho)} campos, lidos {len(campos)}",
                    )
                )
                continue
            lido = _evento_da_linha(linha, dict(zip(cabecalho, campos)))
            if isinstance(lido, Recusa):
                recusas.append(lido)
            else:
                eventos.append(lido)
        return LeituraDoArquivo(
            eventos=tuple(eventos), recusas=tuple(recusas), linhas_em_branco=em_branco
        )

    # ---------------------------------------------------------- gravacao

    def processar(self, registro: Registro) -> ResumoDaFonte:
        """Grava os eventos lidos, na ordem do arquivo, e devolve o resumo do que entrou e do que caiu.

        O vinculo com o item vai pelo proprio `registrar_gatilho`, que confere a chave estrangeira
        ANTES de inserir: uma linha que aponta para item inexistente cai inteira, sem gatilho gravado
        pela metade, e o item NAO e criado aqui. `vincular_gatilho_a_item` e o caminho do rig ao vivo
        (o gatilho nasce antes do item e o vinculo vem depois); no arquivo o vinculo ja vem
        declarado, e ligar depois de um INSERT recusado deixaria gravado um gatilho que o resumo
        declararia recusado. `ponto_id` fica NULL: o arquivo de bancada nao traz o ponto, e herdar um
        ponto adivinhado seria inventar origem.
        """
        leitura = self.ler()
        contagem = dict.fromkeys(EstadoDeGatilho, 0)
        recusas = list(leitura.recusas)
        criados = 0
        for evento in leitura.eventos:
            try:
                registro.registrar_gatilho(
                    evento.timestamp.isoformat(),
                    evento.estado.value,
                    fonte=evento.fonte.value,
                    item_id=evento.item_id,
                    motivo=evento.motivo,
                    debounce_ms=evento.debounce_ms,
                )
            except EventoInvalido as erro:
                # a recusa vem da API do registro e nao e re-diagnosticada aqui: o que sobrar de erro
                # e da ingestao inteira, e sobe como falha em vez de virar linha recusada.
                recusas.append(
                    Recusa(
                        evento.linha,
                        MotivoDeRecusa.ITEM_RECUSADO_PELO_REGISTRO,
                        str(erro),
                    )
                )
                continue
            criados += 1
            contagem[evento.estado] += 1
        return ResumoDaFonte(
            lidas=leitura.linhas_de_dados,
            ids_criados=criados,
            por_estado=tuple(
                ContagemPorEstado(estado, contagem[estado])
                for estado in EstadoDeGatilho
            ),
            recusas=tuple(sorted(recusas, key=lambda recusa: recusa.linha)),
            linhas_em_branco=leitura.linhas_em_branco,
        )


# ---------------------------------------------------------------- leitura de uma linha


def _validar_cabecalho(cabecalho: Sequence[str], caminho: Path) -> None:
    """O cabecalho e lido por NOME, na ordem que o arquivo tiver. Sem BOM: `utf-8` puro, porque o
    BOM muda o nome da primeira coluna e o erro; que mostra as colunas lidas; e o que localiza
    isso. O erro e explicito em vez de tentar adivinhar o que a coluna queria ser."""
    faltando = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in cabecalho]
    if faltando:
        raise CabecalhoInvalido(
            f"{caminho}: cabecalho sem coluna obrigatoria {faltando}; lidas: {list(cabecalho)}"
        )
    repetidas = sorted({coluna for coluna in cabecalho if cabecalho.count(coluna) > 1})
    if repetidas:
        raise CabecalhoInvalido(f"{caminho}: coluna repetida no cabecalho: {repetidas}")
    desconhecidas = [coluna for coluna in cabecalho if coluna not in COLUNAS_ACEITAS]
    if desconhecidas:
        raise CabecalhoInvalido(
            f"{caminho}: coluna desconhecida no cabecalho: {desconhecidas}; aceitas: "
            f"{list(COLUNAS_ACEITAS)}; uma coluna que este leitor nao conhece seria dado do ensaio "
            "jogado fora"
        )


def _evento_da_linha(
    linha: int, valores: Mapping[str, str]
) -> EventoDeGatilho | Recusa:
    """Interpreta uma linha ja com o numero de campos conferido. Levanta para estado fora do
    vocabulario (falha do arquivo inteiro) e devolve `Recusa` para defeito da propria linha."""
    estado = _estado(valores[COLUNA_ESTADO], linha)

    bruto = valores[COLUNA_TIMESTAMP]
    if bruto == "":
        return Recusa(linha, MotivoDeRecusa.TIMESTAMP_AUSENTE)
    try:
        quando = datetime.fromisoformat(bruto)
    except ValueError:
        return Recusa(linha, MotivoDeRecusa.TIMESTAMP_ILEGIVEL, bruto)
    if quando.tzinfo is None:
        return Recusa(linha, MotivoDeRecusa.TIMESTAMP_SEM_FUSO, bruto)

    fonte_bruta = valores[COLUNA_FONTE]
    if fonte_bruta == "":
        fonte = FonteDeGatilho.NAO_DECLARADA
    elif fonte_bruta in FONTES:
        fonte = FonteDeGatilho(fonte_bruta)
    else:
        return Recusa(linha, MotivoDeRecusa.FONTE_DESCONHECIDA, fonte_bruta)

    debounce_bruto = valores[COLUNA_DEBOUNCE]
    if debounce_bruto == "":
        debounce = None
    elif _DEBOUNCE_INTEIRO.fullmatch(debounce_bruto) is None:
        return Recusa(linha, MotivoDeRecusa.DEBOUNCE_INVALIDO, debounce_bruto)
    else:
        debounce = int(debounce_bruto)

    return EventoDeGatilho(
        linha=linha,
        timestamp=quando,
        estado=estado,
        fonte=fonte,
        motivo=valores[COLUNA_MOTIVO] or None,
        item_id=valores[COLUNA_ITEM] or None,
        debounce_ms=debounce,
    )


def _estado(bruto: str, linha: int) -> EstadoDeGatilho:
    """Estado e o unico campo cuja ignorancia e do ARQUIVO, nao da linha: sem saber o que a linha e,
    recusar linha a linha esconderia que o arquivo nao e de eventos de gatilho. Por isso levanta.

    A comparacao e literal. `aceito ` (com espaco) nao e `aceito`: reparar o token em silencio seria
    gravar um estado que o arquivo nao escreveu, e o operador nunca saberia que o arquivo tem lixo.
    """
    if bruto not in ESTADOS:
        raise EstadoForaDoVocabulario(
            f"linha {linha}: estado {bruto!r} fora do vocabulario {'|'.join(ESTADOS)}; "
            "o arquivo inteiro e recusado e nada foi gravado"
        )
    return EstadoDeGatilho(bruto)
