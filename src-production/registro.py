"""Registro local: grava o evento e responde ao reenvio sem duplicar.

Regras que este modulo faz valer (nao sao comentario, sao comportamento testado):
  - idempotencia por `item_id`: a MESMA evidencia reenviada nao cria linha nova. A comparacao e
    feita sobre a evidencia gravada, nao sobre um hash inventado numa coluna nova;
  - divergencia no mesmo `item_id` NAO sobrescreve: levanta `ConflitoDeItem`. Evidencia nao se
    reescreve em silencio (rastreabilidade);
  - D-04: defeito detectado em qualquer dominio reprova o item; sem defeito, mas com vista
    faltante ou evidencia insuficiente, o item fica `inconclusivo`; nunca aprovacao silenciosa;
  - D-23/D-30: a linha de inspecao declara o `papel` (quem decidiu) e o banco recusa
    `papel='decide'` com `vista='topo'` ou sem dominio. O invariante vive no esquema.

Sem `dict[str, Any]`: entrada e `Evento`, saida e `ItemGravado`.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dominio import Classe, Dominio, Evento, Evidencia, Medida, Papel, Qualidade, Vista
from identidade import ErroDeIdentidade, decompor

ESQUEMA = Path(__file__).resolve().parent / "esquema.sql"
#: classe -> codigo do catalogo, apenas onde o mapeamento e 1:1. `deformidade` tem dois codigos
#: (severo/leve) e depende de uma fonte de severidade que ainda nao existe: fica NULL, nao inventado.
MAPA_CODIGO = {
    Classe.TAMPA_AUSENTE: "TAMPA_AUSENTE",
    Classe.DEFEITO_TAMPA: "TAMPA_DEFEITO",
}
VISTAS_LATERAIS = (Vista.LATERAL1, Vista.LATERAL2)


class ErroDeRegistro(Exception):
    """Base dos erros deste modulo."""


class EventoInvalido(ErroDeRegistro):
    """O evento nao pode ser gravado como esta (falta evidencia minima ou coerencia)."""


class ConflitoDeItem(ErroDeRegistro):
    """Ja existe evidencia diferente para este `item_id`. Nada foi sobrescrito."""


@dataclass(frozen=True)
class ReferenciaDaEvidencia:
    """Onde vive a prova desta vista e com que hash; sem isso a rastreabilidade para no evento."""

    vista: Vista
    caminho: str
    sha256: str


@dataclass(frozen=True)
class LinhaDeVista:
    """Projecao do que o banco guarda. `status` e o estado do dominio (ok|defeito|inconclusivo):
    e ele que torna o round-trip comparavel; a classe `normal` nao existe no catalogo de defeito."""

    vista: Vista
    dominio: Dominio | None
    papel: Papel
    disponivel: bool
    status: str
    confianca: float | None


@dataclass(frozen=True)
class ItemGravado:
    item_id: str
    capturado_em: str
    status_tampa: str
    status_corpo: str
    status_final: str
    qualidade_registro: str
    motivo_inconclusivo: str | None
    vistas: tuple[LinhaDeVista, ...]
    referencias: tuple[ReferenciaDaEvidencia, ...] = ()


# ---------------------------------------------------------------- mapeamentos puros

#: nome de operador: identificacao, nao texto livre. Sem < > " ' & / = para nao virar markup.
OPERADOR_VALIDO = re.compile(r"[\w .,'-]{1,64}", re.UNICODE)


def estado_da_classe(classe: Classe) -> str:
    """Classe (D-28) -> estado do dominio no schema: ok | defeito | inconclusivo."""
    if classe is Classe.NORMAL:
        return "ok"
    if classe is Classe.INCONCLUSIVO:
        return "inconclusivo"
    return "defeito"


def papel_da_linha(vista: Vista, medida: Medida) -> Papel:
    """D-23/D-30: o topo nunca decide; inconclusivo ou qualidade ruim e rota de fallback."""
    if vista is Vista.TOPO:
        return Papel.AUXILIAR
    if (
        medida.classe is Classe.INCONCLUSIVO
        or medida.qualidade is Qualidade.INSUFICIENTE
    ):
        return Papel.FALLBACK
    return Papel.DECIDE


def status_final(estados: dict[Dominio, str], evidencias_faltando: bool) -> str:
    """Defeito manda; sem defeito e com evidencia faltando, inconclusivo; senao ok."""
    if any(e == "defeito" for e in estados.values()):
        return "defeito"
    if evidencias_faltando or any(e == "inconclusivo" for e in estados.values()):
        return "inconclusivo"
    return "ok"


def qualidade_registro(
    laterais_decisorias: int, fora_da_janela: int = 0, duplicadas: int = 0
) -> str:
    """Estados distintos do DAT-03, do mais grave para o menos: conjunto invalido (duplicata) >
    timestamp divergente > vista faltante. O item nao pode ser apresentado como completo em nenhum
    desses casos."""
    if duplicadas > 0:
        return "invalido"
    if fora_da_janela > 0:
        return "timestamp_divergente"
    faltando = len(VISTAS_LATERAIS) - laterais_decisorias
    if faltando <= 0:
        return "completo"
    return "parcial_1_vista_faltante" if faltando == 1 else "evidencia_insuficiente"


def discordancia(medidas: tuple[Medida, ...], dominio: Dominio) -> bool:
    classes = {
        m.classe for m in medidas if m.vista in VISTAS_LATERAIS and m.dominio is dominio
    }
    return len(classes) > 1


# ---------------------------------------------------------------- registro


class Registro:
    """Registro local em SQLite. Uma instancia = um arquivo."""

    def __init__(self, conexao: sqlite3.Connection):
        self._cx = conexao

    #: decisao HUMANA: o operador decide o veredito do item, nao a classe do defeito (D-30)
    DECISOES_HUMANAS = ("ok", "defeito")

    @classmethod
    def abrir(cls, caminho: str | Path) -> Registro:
        """Abre o registro com o modo de escrita que aguenta o rig escrevendo ao lado.

        - `journal_mode=WAL`: leitura nao bloqueia escrita e a escrita fica mais curta (medido: com um
          escritor segurando `BEGIN IMMEDIATE`, o POST do gatilho perdia o evento apos 5 s);
        - `busy_timeout` e `timeout` declarados: esperar o lock em vez de desistir no primeiro toque.
        """
        cx = sqlite3.connect(str(caminho), timeout=5.0)
        cx.row_factory = sqlite3.Row
        cx.execute("PRAGMA journal_mode=WAL")
        cx.execute("PRAGMA busy_timeout=5000")
        cx.executescript(ESQUEMA.read_text(encoding="utf-8"))
        cx.commit()
        return cls(cx)

    def fechar(self) -> None:
        self._cx.close()

    # -------------------------------------------------- escrita

    def registrar(
        self,
        evento: Evento,
        fora_da_janela: tuple[Vista, ...] = (),
        duplicadas: tuple[Vista, ...] = (),
        referencias: tuple[ReferenciaDaEvidencia, ...] = (),
        motivos_conformidade: tuple[str, ...] = (),
    ) -> str:
        """Grava o evento. Devolve 'inserido' ou 'repetido'. Nunca sobrescreve.

        `fora_da_janela` sao as vistas capturadas mas fora da janela temporal (RF-01.2): elas ficam
        registradas como auxiliares inconclusivas e o item recebe `qualidade_registro` =
        `timestamp_divergente` (DAT-03). `duplicadas` sao as descartadas por duplicacao: o conjunto
        e marcado `invalido`.

        `motivos_conformidade` e o motivo do veredito da conformidade (D-29) quando ele nao aprova:
        entra em `motivo_inconclusivo` se nenhuma condicao de qualidade ja tiver posto um. Sem esta
        passagem, um item com check dimensional ausente saia gravado como 'ok' sem nenhum motivo."""
        self._validar(evento)
        existente = self.ler(evento.item_id)
        if existente is not None:
            if self._mesma_evidencia(existente, evento, referencias):
                return "repetido"
            raise ConflitoDeItem(
                f"item {evento.item_id!r} ja tem evidencia diferente gravada; nada foi alterado"
            )

        try:
            estados = self._estados(evento)
            dec = {
                v: sum(
                    1 for m in evento.medidas if m.vista is v and m.dominio is not None
                )
                for v in VISTAS_LATERAIS
            }
            faltando = any(dec[v] == 0 for v in VISTAS_LATERAIS)
            divergente = len(fora_da_janela) > 0
            com_duplicata = len(duplicadas) > 0
            lote = self._garantir_lote(evento)
            veredito = status_final(estados, faltando)
            motivo = (
                "vista_duplicada"
                if com_duplicata
                else "timestamp_divergente"
                if divergente
                else None
                if not faltando
                else "vista_lateral_ausente"
            )
            # D-29: a conformidade decide. O registro nao pode SUBIR para 'ok' um item que a
            # conformidade roteou para inconclusivo (check dimensional ausente ou escalonado, rig
            # incompleto) nem rebaixar um 'defeito'. Medido antes da correcao: as duas laterais
            # normais + check ausente saiam gravadas como status_final='ok', motivo=None.
            estado_do_evento = estado_da_classe(evento.status)
            if veredito == "ok" and estado_do_evento != "ok":
                veredito = estado_do_evento
            if veredito == "inconclusivo" and not motivo:
                motivo = (
                    motivos_conformidade[0]
                    if motivos_conformidade
                    else "conformidade_nao_aprovou"
                )
            self._cx.execute(
                "INSERT INTO item (item_id, timestamp_trigger, status_tampa, status_corpo,"
                " discordancia_lateral, status_final, motivo_inconclusivo, qualidade_registro,"
                " equipamento, localizacao, versao_contrato, lote_id)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    evento.item_id,
                    evento.capturado_em.isoformat(),
                    estados[Dominio.TAMPA],
                    estados[Dominio.CORPO],
                    int(
                        discordancia(evento.medidas, Dominio.TAMPA)
                        or discordancia(evento.medidas, Dominio.CORPO)
                    ),
                    veredito,
                    motivo,
                    qualidade_registro(
                        sum(1 for v in VISTAS_LATERAIS if dec[v] > 0),
                        fora_da_janela=len(fora_da_janela),
                        duplicadas=len(duplicadas),
                    ),
                    evento.equipamento,
                    evento.localizacao,
                    evento.versao_contrato,
                    lote,
                ),
            )
            por_vista = {r.vista: r for r in referencias}
            for linha, classe, evidencias in self._linhas(evento):
                ref = por_vista.get(linha.vista)
                cur = self._cx.execute(
                    "INSERT INTO inspecao_vista (item_id, vista, dominio, papel, vista_disponivel,"
                    " qualidade_imagem, status_vista, codigo_defeito, confianca, caminho_evidencia,"
                    " sha256_evidencia) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        evento.item_id,
                        linha.vista.value,
                        linha.dominio.value if linha.dominio else None,
                        linha.papel.value,
                        int(linha.disponivel),
                        "adequada" if linha.status != "inconclusivo" else "baixa",
                        linha.status,
                        MAPA_CODIGO.get(classe),
                        linha.confianca,
                        ref.caminho if ref else None,
                        ref.sha256 if ref else None,
                    ),
                )
                self._gravar_evidencias(int(cur.lastrowid), evidencias)
            self._cx.commit()
        except Exception:
            self._cx.rollback()
            raise
        return "inserido"

    def registrar_gatilho(
        self,
        timestamp: str,
        estado: str,
        fonte: str = "nao_declarada",
        ponto_id: int | None = None,
        item_id: str | None = None,
        motivo: str | None = None,
        debounce_ms: int | None = None,
    ) -> int:
        """Registra um evento de gatilho (RF-01.1). O disparo que NAO virou item tambem entra;
        e o unico jeito de falso disparo e duplicata serem observaveis. Devolve o id."""
        if estado not in ("aceito", "duplicado", "falso", "invalido"):
            raise EventoInvalido(f"estado de gatilho invalido: {estado!r}")
        if item_id is not None and self.ler(item_id) is None:
            raise EventoInvalido(
                f"gatilho aponta para item inexistente: {item_id!r}; o gatilho PRECEDE o item; "
                "registre o gatilho e vincule depois com `vincular_gatilho_a_item`"
            )
        cur = self._cx.execute(
            "INSERT INTO evento_gatilho (timestamp, ponto_id, fonte, estado, item_id, motivo, debounce_ms)"
            " VALUES (?,?,?,?,?,?,?)",
            (timestamp, ponto_id, fonte, estado, item_id, motivo, debounce_ms),
        )
        self._cx.commit()
        return int(cur.lastrowid)

    def correcao_vigente(self, item_id: str) -> dict[str, object] | None:
        """A ultima correcao do item (a que vale), ou `None` quando o operador nunca decidiu."""
        linha = self._cx.execute(
            "SELECT id, item_id, decisao_original, decisao_corrigida, corrigido_por, timestamp"
            " FROM correcao_operador WHERE item_id = ? ORDER BY id DESC LIMIT 1",
            (item_id,),
        ).fetchone()
        return dict(linha) if linha else None

    def corrigir(
        self,
        item_id: str,
        decisao_corrigida: str,
        corrigido_por: str,
        timestamp: str | None = None,
    ) -> dict[str, object]:
        """Registra a decisao do operador sobre um item (P1/D-30). Devolve o que foi gravado.

        Regras (todas viram erro declarado, nao gravacao silenciosa):

        - o item tem de existir: o operador decide sobre um item, nao sobre um id de tela;
        - a decisao tem de estar em `DECISOES_HUMANAS`: o operador da o VEREDITO, e o vocabulario
          aberto convidaria a gravar classe de defeito no lugar de decisao;
        - o operador tem de estar identificado (1 a 64 caracteres imprimiveis): trilha sem autor nao e
          trilha;
        - correcao que repete o que ja vale e recusada: nao acrescenta trilha, so ruido.

        NAO toca em `item.status_final`: o que o classificador decidiu permanece no registro. Quem
        quiser a decisao que VALE le `correcao_vigente` (e a API expoe como `decisao_efetiva`).
        """
        identificador = str(item_id or "").strip()
        if not identificador:
            raise EventoInvalido("correcao sem item: o operador decide sobre um item")

        linha = self._cx.execute(
            "SELECT status_final FROM item WHERE item_id = ?", (identificador,)
        ).fetchone()
        if linha is None:
            raise EventoInvalido(f"item inexistente no registro: {identificador!r}")

        decisao = str(decisao_corrigida or "").strip().lower()
        if decisao not in self.DECISOES_HUMANAS:
            raise EventoInvalido(
                f"decisao do operador fora do vocabulario {list(self.DECISOES_HUMANAS)}: "
                f"{decisao_corrigida!r}"
            )

        operador = " ".join(str(corrigido_por or "").split())
        # Nome de operador e identificacao, nao texto livre: o charset e restrito na ORIGEM para que
        # nenhum payload chegue a ser gravado (XSS armazenado medido: `<img src=x onerror=...>`
        # passava por ser imprimivel). A tela tambem escapa, para as linhas gravadas antes disto.
        if (
            not operador
            or len(operador) > 64
            or not OPERADOR_VALIDO.fullmatch(operador)
        ):
            raise EventoInvalido(
                "correcao sem operador identificado: informe de 1 a 64 caracteres "
                "(letras, numeros, espaco, ponto, virgula, hifen e apostrofo)"
            )

        instante = timestamp or datetime.now(UTC).isoformat(timespec="seconds")
        # BEGIN IMMEDIATE serializa leitura+insert: duas correcoes concorrentes nao passam pelo
        # mesmo estado anterior. Qualquer saida (inclusive recusa) fecha a transacao, senao a
        # proxima chamada encontraria transacao aberta.
        self._cx.execute("BEGIN IMMEDIATE")
        try:
            vigente = self.correcao_vigente(identificador)
            anterior = (
                str(vigente["decisao_corrigida"])
                if vigente
                else str(linha["status_final"] or "")
            )
            if decisao == anterior:
                raise EventoInvalido(
                    f"o item ja esta em {anterior!r}: correcao repetida nao acrescenta trilha"
                )
            cur = self._cx.execute(
                "INSERT INTO correcao_operador"
                " (item_id, decisao_original, decisao_corrigida, corrigido_por, timestamp)"
                " VALUES (?,?,?,?,?)",
                (identificador, anterior, decisao, operador, instante),
            )
            self._cx.commit()
        except BaseException:
            self._cx.rollback()
            raise
        return {
            "id": int(cur.lastrowid),
            "item_id": identificador,
            "decisao_original": anterior,
            "decisao_corrigida": decisao,
            "corrigido_por": operador,
            "timestamp": instante,
        }

    def vincular_gatilho_a_item(self, gatilho_id: int, item_id: str) -> None:
        """Vincula um gatilho uma vez; reatribuir a outro item e conflito de rastreabilidade."""
        if self.ler(item_id) is None:
            raise EventoInvalido(f"item inexistente: {item_id!r}")
        gatilho = self._cx.execute(
            "SELECT item_id FROM evento_gatilho WHERE id = ?", (gatilho_id,)
        ).fetchone()
        if gatilho is None:
            raise EventoInvalido(f"evento de gatilho nao encontrado: {gatilho_id}")
        vinculado = gatilho["item_id"]
        if vinculado == item_id:
            return
        if vinculado is not None:
            raise EventoInvalido(
                f"gatilho {gatilho_id} ja vinculado ao item {vinculado!r}; conflito de rastreabilidade"
            )
        cur = self._cx.execute(
            "UPDATE evento_gatilho SET item_id = ? WHERE id = ? AND item_id IS NULL",
            (item_id, gatilho_id),
        )
        if cur.rowcount != 1:
            raise EventoInvalido(f"gatilho {gatilho_id} nao pode ser vinculado")
        self._cx.commit()

    def _validar(self, evento: Evento) -> None:
        """Evento sem medida NAO e invalido: e um item inconclusivo (D-04). O que nao pode e
        evento sem identidade."""
        if not evento.item_id.strip():
            raise EventoInvalido("evento sem item_id nao e rastreavel")

    def _estados(self, evento: Evento) -> dict[Dominio, str]:
        """Estado por dominio. Defeito em QUALQUER lateral reprova (D-04); aprovacao exige as DUAS
        laterais decisorias medidas e normais; com uma lateral so, o dominio fica `inconclusivo`,
        nunca `ok` (D-29: vista unica nao sustenta aprovacao)."""
        estados: dict[Dominio, str] = {}
        for dom in (Dominio.TAMPA, Dominio.CORPO):
            medidas = [
                m
                for m in evento.medidas
                if m.dominio is dom and m.vista in VISTAS_LATERAIS
            ]
            classes = {m.classe for m in medidas}
            vistas_medidas = {m.vista for m in medidas}
            if any(
                c is not Classe.NORMAL and c is not Classe.INCONCLUSIVO for c in classes
            ):
                estados[dom] = "defeito"
            elif (
                Classe.INCONCLUSIVO in classes
                or any(m.qualidade is not Qualidade.OK for m in medidas)
                or len(vistas_medidas) < len(VISTAS_LATERAIS)
            ):
                estados[dom] = "inconclusivo"
            else:
                estados[dom] = "ok"
        return estados

    def _garantir_lote(self, evento: Evento) -> str | None:
        """O lote vem do proprio `item_id` (`<lote>-<sequencia>`, DAT-01). Id fora do formato nao
        ganha lote inventado: fica NULL, e a consulta por lote mostra '(sem lote)'."""
        try:
            lote, _ = decompor(evento.item_id)
        except ErroDeIdentidade:
            return None
        self._cx.execute(
            "INSERT OR IGNORE INTO lote (lote_id, data_inicio) VALUES (?,?)",
            (lote, evento.capturado_em.date().isoformat()),
        )
        return lote

    def _gravar_evidencias(
        self, inspecao_vista_id: int, evidencias: tuple[Evidencia, ...]
    ) -> None:
        for e in evidencias:
            self._cx.execute(
                "INSERT INTO evidencia (inspecao_vista_id, grandeza, valor, unidade, origem, papel,"
                " metodo, fonte) VALUES (?,?,?,?,?,?,?,?)",
                (
                    inspecao_vista_id,
                    e.grandeza,
                    e.valor,
                    e.unidade,
                    e.origem.value,
                    e.papel.value,
                    e.metodo,
                    e.fonte,
                ),
            )

    def _linhas(
        self, evento: Evento
    ) -> tuple[tuple[LinhaDeVista, Classe | None, tuple[Evidencia, ...]], ...]:
        """Cada medida vira uma linha; cada vista declarada sem medida vira linha auxiliar
        inconclusiva (capturada e nao decidida; nao e evidencia de nada)."""
        pares: list[tuple[LinhaDeVista, Classe | None, tuple[Evidencia, ...]]] = []
        decididas: set[Vista] = set()
        for m in evento.medidas:
            pares.append(
                (
                    LinhaDeVista(
                        vista=m.vista,
                        dominio=m.dominio,
                        papel=papel_da_linha(m.vista, m),
                        disponivel=True,
                        status=estado_da_classe(m.classe),
                        confianca=m.confianca,
                    ),
                    m.classe,
                    tuple(m.evidencias),
                )
            )
            decididas.add(m.vista)
        for v in evento.vistas:
            if v not in decididas:
                pares.append(
                    (
                        LinhaDeVista(
                            vista=v,
                            dominio=None,
                            papel=Papel.AUXILIAR,
                            disponivel=True,
                            status="inconclusivo",
                            confianca=None,
                        ),
                        None,
                        (),
                    )
                )
        return tuple(
            sorted(
                pares,
                key=lambda par: (
                    par[0].vista.value,
                    par[0].dominio.value if par[0].dominio else "",
                ),
            )
        )

    # -------------------------------------------------- leitura

    def ler(self, item_id: str) -> ItemGravado | None:
        r = self._cx.execute(
            "SELECT * FROM item WHERE item_id = ?", (item_id,)
        ).fetchone()
        if r is None:
            return None
        rows = tuple(
            self._cx.execute(
                "SELECT * FROM inspecao_vista WHERE item_id = ? ORDER BY id", (item_id,)
            ).fetchall()
        )
        vistas = tuple(
            LinhaDeVista(
                vista=Vista(v["vista"]),
                dominio=Dominio(v["dominio"]) if v["dominio"] else None,
                papel=Papel(v["papel"]),
                disponivel=bool(v["vista_disponivel"]),
                status=v["status_vista"],
                confianca=v["confianca"],
            )
            for v in rows
        )
        referencias_por_vista: dict[Vista, ReferenciaDaEvidencia] = {}
        for row in rows:
            if row["caminho_evidencia"] is None and row["sha256_evidencia"] is None:
                continue
            vista = Vista(row["vista"])
            referencia = ReferenciaDaEvidencia(
                vista=vista,
                caminho=row["caminho_evidencia"],
                sha256=row["sha256_evidencia"],
            )
            anterior = referencias_por_vista.get(vista)
            if anterior is not None and anterior != referencia:
                raise ErroDeRegistro(
                    f"referencias divergentes gravadas para a vista {vista.value}"
                )
            referencias_por_vista[vista] = referencia
        return ItemGravado(
            item_id=r["item_id"],
            capturado_em=r["timestamp_trigger"],
            status_tampa=r["status_tampa"],
            status_corpo=r["status_corpo"],
            status_final=r["status_final"],
            qualidade_registro=r["qualidade_registro"],
            motivo_inconclusivo=r["motivo_inconclusivo"],
            vistas=vistas,
            referencias=tuple(referencias_por_vista.values()),
        )

    def contar(self) -> int:
        return int(self._cx.execute("SELECT COUNT(*) FROM item").fetchone()[0])

    def _mesma_evidencia(
        self,
        gravado: ItemGravado,
        evento: Evento,
        referencias: tuple[ReferenciaDaEvidencia, ...],
    ) -> bool:
        """Reenvio so e repetido se linhas E referencias gravadas forem identicas."""
        linhas = tuple(l for l, _, _ in self._linhas(evento))
        return _chave(gravado.vistas) == _chave(linhas) and _chave_referencias(
            gravado.referencias
        ) == _chave_referencias(referencias)


def _chave(linhas) -> tuple:
    """Projecao comparavel de um conjunto de linhas de vista."""
    return tuple(
        sorted(
            (
                l.vista.value,
                l.dominio.value if l.dominio else None,
                l.papel.value,
                l.disponivel,
                l.status,
                l.confianca,
            )
            for l in linhas
        )
    )


def _chave_referencias(referencias: tuple[ReferenciaDaEvidencia, ...]) -> tuple:
    """Projecao estavel da identidade fisica das imagens usadas como evidencia."""
    return tuple(sorted((r.vista.value, r.caminho, r.sha256) for r in referencias))
