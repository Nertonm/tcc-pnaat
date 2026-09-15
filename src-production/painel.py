"""Painel: as consultas analiticas de `docs/dados-telemetria.md` §3 sobre o registro.

Somente leitura. Cada metodo devolve dataclass tipado, nunca `dict`.

Regra da fonte que este modulo faz valer: `ok`, `defeito`, `inconclusivo` e `erro_processamento` sao
estados DIFERENTES, e **inconclusivo nunca conta como aprovado**. `aprovados()` existe separado de
`contagem_por_estado()` justamente para que somar "nao defeito" nao passe por aprovacao.

Duas consultas dependem de dado que o registro ainda nao produz, e isso esta dito no proprio metodo
em vez de virar numero inventado:
  * gatilho por fonte (disparo falso / perda de deteccao) — o schema guarda `fonte_trigger`, mas nao
    guarda evento de gatilho sem item, entao falso disparo nao e observavel hoje;
  * saturacao por configuracao de iluminacao — a coluna existe por vista; a configuracao de luz nao.
"""
from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass

VISTAS = ("topo", "lateral1", "lateral2")
DOMINIOS = ("tampa", "corpo")


@dataclass(frozen=True)
class TaxaDeDefeito:
    lote_id: str
    itens: int
    defeitos: int
    inconclusivos: int
    taxa_defeito: float


@dataclass(frozen=True)
class DefeitoFrequente:
    codigo: str
    severidade: str | None
    ocorrencias: int


@dataclass(frozen=True)
class CorrelacaoAmbiental:
    variavel: str
    janela_s: int
    pares: int
    r: float | None


@dataclass(frozen=True)
class TendenciaPorHora:
    hora: str
    itens: int
    defeitos: int
    taxa_defeito: float


@dataclass(frozen=True)
class ItemCritico:
    item_id: str
    codigo_defeito: str
    severidade: str
    vista: str
    caminho_evidencia: str | None


@dataclass(frozen=True)
class SaudeDoNo:
    ponto_id: int
    timestamp: str
    status: str
    fila_pendente: int | None


@dataclass(frozen=True)
class LatenciaPorVista:
    vista: str
    medidas: int
    media_ms: float
    maxima_ms: int


@dataclass(frozen=True)
class CorrecaoParaAuditoria:
    item_id: str
    decisao_original: str | None
    decisao_corrigida: str | None
    corrigido_por: str | None
    timestamp: str | None


@dataclass(frozen=True)
class SeparacaoNaoConfirmada:
    item_id: str
    status: str
    tentativa: int | None
    via_sensor: str | None


@dataclass(frozen=True)
class GatilhoPorFonte:
    fonte: str
    eventos: int
    aceitos: int
    falsos: int
    duplicados: int
    invalidos: int
    taxa_falso: float


@dataclass(frozen=True)
class PerdaDeDeteccao:
    """O que NAO da para medir so com o gatilho: item que passou sem disparar."""
    instrumentada: bool
    motivo: str


@dataclass(frozen=True)
class SaturacaoPorVista:
    vista: str
    medidas: int
    media_pct: float
    maxima_pct: float


@dataclass(frozen=True)
class InconclusivoPorLote:
    lote_id: str
    motivo: str
    ocorrencias: int


@dataclass(frozen=True)
class DistribuicaoPorDominio:
    dominio: str
    estado: str
    ocorrencias: int


@dataclass(frozen=True)
class DiscordanciaLateral:
    itens_com_duas_laterais: int
    discordantes: int
    taxa: float


class Painel:
    """Leitura sobre o banco do registro. Nao escreve nada."""

    def __init__(self, conexao: sqlite3.Connection):
        self._cx = conexao
        self._cx.row_factory = sqlite3.Row

    @classmethod
    def abrir(cls, caminho) -> "Painel":
        cx = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
        return cls(cx)

    # -------------------------------------------------------------- 1

    def taxa_de_defeito_por_lote(self) -> tuple[TaxaDeDefeito, ...]:
        linhas = self._cx.execute(
            "SELECT COALESCE(lote_id,'(sem lote)') AS lote, COUNT(*) AS itens,"
            " SUM(status_final='defeito') AS defeitos, SUM(status_final='inconclusivo') AS inconc"
            " FROM item GROUP BY lote ORDER BY lote").fetchall()
        return tuple(TaxaDeDefeito(r["lote"], r["itens"], r["defeitos"] or 0, r["inconc"] or 0,
                                   (r["defeitos"] or 0) / r["itens"]) for r in linhas)

    # -------------------------------------------------------------- 2

    def defeitos_frequentes(self, de: str | None = None, ate: str | None = None) -> tuple[DefeitoFrequente, ...]:
        sql = ("SELECT v.codigo_defeito AS codigo, t.severidade AS sev, COUNT(*) AS n"
               " FROM inspecao_vista v JOIN item i ON i.item_id = v.item_id"
               " LEFT JOIN taxonomia_defeito t ON t.codigo = v.codigo_defeito"
               " WHERE v.codigo_defeito IS NOT NULL")
        par: list = []
        if de:
            sql += " AND i.timestamp_trigger >= ?"; par.append(de)
        if ate:
            sql += " AND i.timestamp_trigger <= ?"; par.append(ate)
        sql += " GROUP BY v.codigo_defeito, t.severidade ORDER BY n DESC, codigo"
        return tuple(DefeitoFrequente(r["codigo"], r["sev"], r["n"]) for r in self._cx.execute(sql, par))

    # -------------------------------------------------------------- 3

    def correlacao_ambiental(self, janela_s: int = 30, variavel: str = "temperatura") -> CorrelacaoAmbiental:
        """Correlacao ponto-bisserial entre a variavel ambiente e o item ter saido com defeito.

        Pareia cada item com os eventos ambientais dentro de +-`janela_s`. Sem ao menos 3 pares com
        os dois valores, devolve `r=None` — nao inventa correlacao com n pequeno."""
        if variavel not in ("temperatura", "umidade", "qualidade_ar"):
            raise ValueError(f"variavel nao suportada: {variavel}")
        itens = self._cx.execute(
            "SELECT item_id, timestamp_trigger, (status_final='defeito') AS y FROM item").fetchall()
        pares: list[tuple[float, float]] = []
        for it in itens:
            amb = self._cx.execute(
                f"SELECT {variavel} AS v FROM evento_ambiental"
                " WHERE ABS(strftime('%s', timestamp) - strftime('%s', ?)) <= ? AND "
                f"{variavel} IS NOT NULL", (it["timestamp_trigger"], janela_s)).fetchall()
            for a in amb:
                pares.append((float(a["v"]), float(it["y"])))
        r = _pearson(pares) if len(pares) >= 3 else None
        return CorrelacaoAmbiental(variavel, janela_s, len(pares), r)

    # -------------------------------------------------------------- 4

    def tendencia_por_hora(self) -> tuple[TendenciaPorHora, ...]:
        linhas = self._cx.execute(
            "SELECT strftime('%Y-%m-%dT%H', timestamp_trigger) AS hora, COUNT(*) AS itens,"
            " SUM(status_final='defeito') AS defeitos FROM item GROUP BY hora ORDER BY hora").fetchall()
        return tuple(TendenciaPorHora(r["hora"], r["itens"], r["defeitos"] or 0,
                                      (r["defeitos"] or 0) / r["itens"]) for r in linhas)

    # -------------------------------------------------------------- 5

    def itens_criticos(self, limite: int = 100) -> tuple[ItemCritico, ...]:
        linhas = self._cx.execute(
            "SELECT i.item_id, v.codigo_defeito, t.severidade, v.vista, v.caminho_evidencia"
            " FROM item i JOIN inspecao_vista v ON v.item_id = i.item_id"
            " JOIN taxonomia_defeito t ON t.codigo = v.codigo_defeito"
            " WHERE t.severidade = 'critico' ORDER BY i.timestamp_trigger DESC LIMIT ?",
            (limite,)).fetchall()
        return tuple(ItemCritico(r["item_id"], r["codigo_defeito"], r["severidade"], r["vista"],
                                 r["caminho_evidencia"]) for r in linhas)

    # -------------------------------------------------------------- 6

    def saude_dos_nos(self, janela_h: int = 1) -> tuple[SaudeDoNo, ...]:
        linhas = self._cx.execute(
            "SELECT ponto_id, timestamp, status, fila_pendente FROM heartbeat_no"
            " WHERE datetime(timestamp) >= datetime('now', ?) ORDER BY timestamp DESC",
            (f"-{janela_h} hours",)).fetchall()
        return tuple(SaudeDoNo(r["ponto_id"], r["timestamp"], r["status"], r["fila_pendente"]) for r in linhas)

    # -------------------------------------------------------------- 7

    def latencia_por_vista(self) -> tuple[LatenciaPorVista, ...]:
        linhas = self._cx.execute(
            "SELECT vista, COUNT(latencia_ms) AS n, AVG(latencia_ms) AS media, MAX(latencia_ms) AS maxima"
            " FROM inspecao_vista WHERE latencia_ms IS NOT NULL GROUP BY vista ORDER BY vista").fetchall()
        return tuple(LatenciaPorVista(r["vista"], r["n"], r["media"], r["maxima"]) for r in linhas)

    # -------------------------------------------------------------- 8

    def correcoes_para_auditoria(self) -> tuple[CorrecaoParaAuditoria, ...]:
        return tuple(CorrecaoParaAuditoria(r["item_id"], r["decisao_original"], r["decisao_corrigida"],
                                           r["corrigido_por"], r["timestamp"])
                     for r in self._cx.execute("SELECT * FROM correcao_operador ORDER BY timestamp"))

    # -------------------------------------------------------------- 9

    def separacoes_nao_confirmadas(self) -> tuple[SeparacaoNaoConfirmada, ...]:
        return tuple(SeparacaoNaoConfirmada(r["item_id"], r["status"], r["tentativa"], r["via_sensor"])
                     for r in self._cx.execute(
                         "SELECT * FROM evento_rejeicao WHERE status IN ('falha','timeout')"
                         " OR status_ordem = 'falha' ORDER BY id"))

    # -------------------------------------------------------------- 10

    def gatilho_por_fonte(self) -> tuple[GatilhoPorFonte, ...]:
        """Taxa de disparo falso por fonte (consulta 10). Agora e observavel: o evento de gatilho
        existe separado do item, entao o disparo que nao virou item entra na conta."""
        linhas = self._cx.execute(
            "SELECT COALESCE(fonte,'nao_declarada') AS fonte, COUNT(*) AS eventos,"
            " SUM(estado='aceito') AS aceitos, SUM(estado='falso') AS falsos,"
            " SUM(estado='duplicado') AS duplicados, SUM(estado='invalido') AS invalidos"
            " FROM evento_gatilho GROUP BY fonte ORDER BY eventos DESC").fetchall()
        return tuple(GatilhoPorFonte(r["fonte"], r["eventos"], r["aceitos"] or 0, r["falsos"] or 0,
                                     r["duplicados"] or 0, r["invalidos"] or 0,
                                     (r["falsos"] or 0) / r["eventos"]) for r in linhas)

    def perda_de_deteccao(self) -> PerdaDeDeteccao:
        """Item que passou sem disparar o gatilho NAO e observavel pelo proprio gatilho: exige
        referencia externa (contagem por encoder). Declarado aqui em vez de reportado como zero."""
        return PerdaDeDeteccao(False, "exige referencia externa (contagem do encoder KY-040, D-21)")

    # -------------------------------------------------------------- 11

    def saturacao_por_vista(self) -> tuple[SaturacaoPorVista, ...]:
        linhas = self._cx.execute(
            "SELECT vista, COUNT(pixels_saturados_pct) AS n, AVG(pixels_saturados_pct) AS media,"
            " MAX(pixels_saturados_pct) AS maxima FROM inspecao_vista"
            " WHERE pixels_saturados_pct IS NOT NULL GROUP BY vista ORDER BY vista").fetchall()
        return tuple(SaturacaoPorVista(r["vista"], r["n"], r["media"], r["maxima"]) for r in linhas)

    # -------------------------------------------------------------- 12

    def inconclusivos_por_lote(self) -> tuple[InconclusivoPorLote, ...]:
        linhas = self._cx.execute(
            "SELECT COALESCE(lote_id,'(sem lote)') AS lote,"
            " COALESCE(motivo_inconclusivo,'(sem motivo declarado)') AS motivo, COUNT(*) AS n"
            " FROM item WHERE status_final = 'inconclusivo' GROUP BY lote, motivo ORDER BY n DESC").fetchall()
        return tuple(InconclusivoPorLote(r["lote"], r["motivo"], r["n"]) for r in linhas)

    # -------------------------------------------------------------- 13

    def distribuicao_por_dominio(self) -> tuple[DistribuicaoPorDominio, ...]:
        partes = []
        for dom, col in (("tampa", "status_tampa"), ("corpo", "status_corpo")):
            for r in self._cx.execute(
                    f"SELECT {col} AS estado, COUNT(*) AS n FROM item"
                    f" WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY n DESC"):
                partes.append(DistribuicaoPorDominio(dom, r["estado"], r["n"]))
        return tuple(partes)

    # -------------------------------------------------------------- 14

    def discordancia_lateral(self) -> DiscordanciaLateral:
        r = self._cx.execute(
            "SELECT SUM(CASE WHEN n_med >= 4 THEN 1 ELSE 0 END) AS pares,"
            " SUM(CASE WHEN n_med >= 4 THEN disc ELSE 0 END) AS disc FROM ("
            "  SELECT i.discordancia_lateral AS disc,"
            "   (SELECT COUNT(*) FROM inspecao_vista v WHERE v.item_id = i.item_id"
            "     AND v.vista IN ('lateral1','lateral2') AND v.papel = 'decide'"
            "     AND v.dominio IS NOT NULL) AS n_med FROM item i)").fetchone()
        pares = r["pares"] or 0
        disc = r["disc"] or 0
        return DiscordanciaLateral(pares, disc, (disc / pares) if pares else 0.0)

    # -------------------------------------------------------------- contagem separada

    def contagem_por_estado(self) -> dict[str, int]:
        return {r["status_final"]: r["n"] for r in self._cx.execute(
            "SELECT status_final, COUNT(*) AS n FROM item GROUP BY status_final")}

    def aprovados(self) -> int:
        """Só `ok`. Inconclusivo NAO entra (regra da §3)."""
        return int(self._cx.execute(
            "SELECT COUNT(*) FROM item WHERE status_final = 'ok'").fetchone()[0])

    @property
    def conexao(self):
        """Handle SOMENTE leitura para as consultas de apresentacao (`consultas_site`).

        Existe para as listagens do site pararem de tocar em `_cx`: quem lista usa um nome
        publico, e o modulo que so responde indicador nao vira o unico caminho de leitura.
        A conexao e a mesma que `abrir()` criou em modo read-only.
        """
        return self._cx


def _pearson(pares) -> float | None:
    n = len(pares)
    mx = sum(p[0] for p in pares) / n
    my = sum(p[1] for p in pares) / n
    sx = math.sqrt(sum((p[0] - mx) ** 2 for p in pares))
    sy = math.sqrt(sum((p[1] - my) ** 2 for p in pares))
    if sx == 0 or sy == 0:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pares) / (sx * sy)
