"""Consultas de apresentacao do site: LISTAR capturas e ABRIR um item.

Por que este modulo existe separado do `painel`: o painel responde indicador (taxa, latencia,
discordancia) e cada numero dele tem teste celula a celula. Estas consultas respondem outra
pergunta — "o que passou por esta vista" e "mostre este item" — com paging e filtro. Misturar as
duas coisas faria o modulo de indicador carregar SQL de tela.

Contrato: dataclasses congeladas, nenhum `dict` cru na fronteira; a API serializa o dataclass e nao
reinventa campo. `caminho_evidencia` sai como o caminho gravado no banco — quem monta URL e a API.
"""
from __future__ import annotations

from dataclasses import dataclass

from painel import Painel


@dataclass(frozen=True)
class CapturaResumida:
    """Uma linha de vista inspecionada, com o estado do ITEM ao lado (a vista sozinha nao decide)."""

    id: int
    item_id: str
    vista: str
    dominio: str | None
    papel: str
    status_vista: str | None
    codigo_defeito: str | None
    confianca: float | None
    latencia_ms: int | None
    caminho_evidencia: str | None
    timestamp_captura: str | None
    status_final: str | None
    lote_id: str | None
    qualidade_registro: str | None
    motivo_inconclusivo: str | None
    timestamp_trigger: str
    discordancia_lateral: int


@dataclass(frozen=True)
class EvidenciaDoItem:
    """Grandeza que sustentou uma decisao (D-30). E o rastro, nao o voto."""

    grandeza: str
    valor: float | None
    unidade: str
    origem: str
    papel: str
    metodo: str
    fonte: str | None


@dataclass(frozen=True)
class ItemDetalhe:
    item_id: str
    lote_id: str | None
    timestamp_trigger: str
    status_final: str | None
    status_tampa: str | None
    status_corpo: str | None
    qualidade_registro: str | None
    motivo_inconclusivo: str | None
    discordancia_lateral: int
    equipamento: str | None
    localizacao: str | None
    fonte_trigger: str | None
    velocidade_rig_mm_s: float | None
    vistas: tuple[CapturaResumida, ...]
    evidencias: tuple[EvidenciaDoItem, ...]
    correcoes: tuple[object, ...]
    #: decisao que VALE (ultima correcao humana) e o registro dela; `None` quando ninguem corrigiu
    decisao_efetiva: str | None = None
    correcao_vigente: dict[str, object] | None = None


@dataclass(frozen=True)
class LoteResumo:
    lote_id: str
    data_inicio: str | None
    itens: int
    ok: int
    defeitos: int
    inconclusivos: int
    taxa_defeito: float | None


_SELECT_VISTA = (
    "SELECT v.id AS id, v.item_id AS item_id, v.vista AS vista, v.dominio AS dominio,"
    " v.papel AS papel, v.status_vista AS status_vista, v.codigo_defeito AS codigo_defeito,"
    " v.confianca AS confianca, v.latencia_ms AS latencia_ms, v.caminho_evidencia AS caminho_evidencia,"
    " v.timestamp_captura AS timestamp_captura, i.status_final AS status_final,"
    " i.lote_id AS lote_id, i.qualidade_registro AS qualidade_registro,"
    " i.motivo_inconclusivo AS motivo_inconclusivo, i.timestamp_trigger AS timestamp_trigger,"
    " i.discordancia_lateral AS discordancia_lateral"
    " FROM inspecao_vista v JOIN item i ON i.item_id = v.item_id"
)


def _linha(r) -> CapturaResumida:
    return CapturaResumida(
        id=r["id"], item_id=r["item_id"], vista=r["vista"], dominio=r["dominio"], papel=r["papel"],
        status_vista=r["status_vista"], codigo_defeito=r["codigo_defeito"], confianca=r["confianca"],
        latencia_ms=r["latencia_ms"], caminho_evidencia=r["caminho_evidencia"],
        timestamp_captura=r["timestamp_captura"], status_final=r["status_final"], lote_id=r["lote_id"],
        qualidade_registro=r["qualidade_registro"], motivo_inconclusivo=r["motivo_inconclusivo"],
        timestamp_trigger=r["timestamp_trigger"], discordancia_lateral=r["discordancia_lateral"])


def capturas_recentes(painel: Painel, limite: int = 100, vista: str | None = None,
                      estado: str | None = None) -> tuple[CapturaResumida, ...]:
    """Mais recente primeiro. `estado` filtra pelo ITEM (`status_final`), `vista` pela linha."""
    if limite < 1:
        raise ValueError("limite deve ser >= 1")
    if vista is not None and vista not in ("topo", "lateral1", "lateral2"):
        raise ValueError(f"vista fora do vocabulario: {vista!r}")
    if estado is not None and estado not in ("ok", "defeito", "inconclusivo", "erro_processamento"):
        raise ValueError(f"estado fora do vocabulario: {estado!r}")
    sql = _SELECT_VISTA + " WHERE 1=1"
    par: list = []
    if vista:
        sql += " AND v.vista = ?"
        par.append(vista)
    if estado:
        sql += " AND i.status_final = ?"
        par.append(estado)
    sql += " ORDER BY i.timestamp_trigger DESC, v.item_id DESC, v.vista LIMIT ?"
    par.append(int(limite))
    return tuple(_linha(r) for r in painel.conexao.execute(sql, par))


def total_de_capturas(painel: Painel) -> int:
    """Base do recorte: sem ela, lista vazia e indistinguivel de filtro que zerou tudo."""
    return int(painel.conexao.execute("SELECT COUNT(*) FROM inspecao_vista").fetchone()[0])


def gatilhos_recentes(painel: Painel, limite: int = 50) -> tuple[dict, ...]:
    """Ultimos eventos de gatilho, mais recente primeiro.

    O registro guarda o disparo que NAO virou item (falso, duplicado, invalido) — e o unico jeito de
    isso ser observavel. `teste` marca o ensaio de bancada (motivo), para nao se confundir com o
    disparo do sensor em producao.
    """
    linhas = painel.conexao.execute(
        "SELECT id, timestamp, ponto_id, fonte, estado, item_id, motivo, debounce_ms"
        " FROM evento_gatilho ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
    return tuple({
        "id": linha["id"], "timestamp": linha["timestamp"], "ponto_id": linha["ponto_id"],
        "fonte": linha["fonte"], "estado": linha["estado"], "item_id": linha["item_id"],
        "motivo": linha["motivo"], "debounce_ms": linha["debounce_ms"],
        "teste": bool(linha["motivo"] and ("bancada" in linha["motivo"] or "debug" in linha["motivo"])),
    } for linha in linhas)


def item_detalhe(painel: Painel, item_id: str) -> ItemDetalhe | None:
    """Item + vistas + evidencias + correcoes; `None` quando o item nao existe (a API devolve 404)."""
    r = painel.conexao.execute(
        "SELECT item_id, lote_id, timestamp_trigger, status_final, status_tampa, status_corpo,"
        " qualidade_registro, motivo_inconclusivo, discordancia_lateral, equipamento, localizacao,"
        " fonte_trigger, velocidade_rig_mm_s FROM item WHERE item_id = ?", (item_id,)).fetchone()
    if r is None:
        return None
    vistas = tuple(_linha(x) for x in painel.conexao.execute(
        _SELECT_VISTA + " WHERE v.item_id = ? ORDER BY v.vista", (item_id,)))
    evidencias = tuple(
        EvidenciaDoItem(grandeza=e["grandeza"], valor=e["valor"], unidade=e["unidade"],
                        origem=e["origem"], papel=e["papel"], metodo=e["metodo"], fonte=e["fonte"])
        for e in painel.conexao.execute(
            "SELECT e.grandeza, e.valor, e.unidade, e.origem, e.papel, e.metodo, e.fonte"
            " FROM evidencia e JOIN inspecao_vista v ON v.id = e.inspecao_vista_id"
            " WHERE v.item_id = ? ORDER BY e.id", (item_id,)))
    # consulta filtrada (nao a tabela inteira em Python): o detalhe de um item nao cresce com o
    # historico do hub. O indice `idx_correcao_item` sustenta o WHERE.
    correcoes = painel.correcoes_do_item(item_id)
    vigente = correcoes[-1] if correcoes else None
    return ItemDetalhe(
        item_id=r["item_id"], lote_id=r["lote_id"], timestamp_trigger=r["timestamp_trigger"],
        status_final=r["status_final"], status_tampa=r["status_tampa"], status_corpo=r["status_corpo"],
        qualidade_registro=r["qualidade_registro"], motivo_inconclusivo=r["motivo_inconclusivo"],
        decisao_efetiva=str(vigente.decisao_corrigida) if vigente else r["status_final"],
        correcao_vigente=(None if vigente is None else {
            "decisao_original": vigente.decisao_original,
            "decisao_corrigida": vigente.decisao_corrigida,
            "corrigido_por": vigente.corrigido_por,
            "timestamp": vigente.timestamp,
        }),
        discordancia_lateral=r["discordancia_lateral"], equipamento=r["equipamento"],
        localizacao=r["localizacao"], fonte_trigger=r["fonte_trigger"],
        velocidade_rig_mm_s=r["velocidade_rig_mm_s"], vistas=vistas, evidencias=evidencias,
        correcoes=correcoes)


def lotes_resumo(painel: Painel) -> tuple[LoteResumo, ...]:
    """Lote com contagem por estado.

    A taxa e `defeitos / itens` — o inconclusivo tem coluna propria mas ENTRA no denominador (o item
    foi inspecionado; o que ele nao fez foi decidir). Lote sem item devolve `taxa_defeito=None`, e nao
    0.0: zero se leria como "nenhum defeito medido" quando nao houve medida.
    """
    linhas = painel.conexao.execute(
        "SELECT COALESCE(l.lote_id, '(sem lote)') AS lote_id, l.data_inicio AS data_inicio,"
        " COUNT(i.item_id) AS itens, SUM(i.status_final = 'ok') AS ok,"
        " SUM(i.status_final = 'defeito') AS defeitos,"
        " SUM(i.status_final = 'inconclusivo') AS inconclusivos"
        " FROM item i LEFT JOIN lote l ON l.lote_id = i.lote_id"
        " GROUP BY l.lote_id, l.data_inicio ORDER BY l.data_inicio, lote_id").fetchall()
    return tuple(LoteResumo(lote_id=r["lote_id"], data_inicio=r["data_inicio"], itens=r["itens"],
                            ok=r["ok"] or 0, defeitos=r["defeitos"] or 0,
                            inconclusivos=r["inconclusivos"] or 0,
                            taxa_defeito=(r["defeitos"] or 0) / r["itens"] if r["itens"] else None)
                 for r in linhas)


def caminho_da_evidencia(painel: Painel, item_id: str, vista: str) -> str | None:
    """Caminho gravado para a evidencia desta vista. `None` = nao ha rastro registrado."""
    r = painel.conexao.execute(
        "SELECT caminho_evidencia FROM inspecao_vista WHERE item_id = ? AND vista = ?"
        " AND caminho_evidencia IS NOT NULL ORDER BY id LIMIT 1", (item_id, vista)).fetchone()
    return r["caminho_evidencia"] if r else None
