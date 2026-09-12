"""Registro local: grava o evento e responde ao reenvio sem duplicar.

Regras que este modulo faz valer (nao sao comentario, sao comportamento testado):
  - idempotencia por `item_id`: a MESMA evidencia reenviada nao cria linha nova. A comparacao e
    feita sobre a evidencia gravada, nao sobre um hash inventado numa coluna nova;
  - divergencia no mesmo `item_id` NAO sobrescreve: levanta `ConflitoDeItem`. Evidencia nao se
    reescreve em silencio (rastreabilidade);
  - D-04: defeito detectado em qualquer dominio reprova o item; sem defeito, mas com vista
    faltante ou evidencia insuficiente, o item fica `inconclusivo` — nunca aprovacao silenciosa;
  - D-23/D-30: a linha de inspecao declara o `papel` (quem decidiu) e o banco recusa
    `papel='decide'` com `vista='topo'` ou sem dominio. O invariante vive no esquema.

Sem `dict[str, Any]`: entrada e `Evento`, saida e `ItemGravado`.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from dominio import Classe, Dominio, Evento, Medida, Papel, Qualidade, Vista

ESQUEMA = Path(__file__).resolve().parent / "esquema.sql"
#: classe -> codigo do catalogo, apenas onde o mapeamento e 1:1. `deformidade` tem dois codigos
#: (severo/leve) e depende de uma fonte de severidade que ainda nao existe: fica NULL, nao inventado.
MAPA_CODIGO = {Classe.TAMPA_AUSENTE: "TAMPA_AUSENTE", Classe.TAMPA_MAL_ROSQUEADA: "TAMPA_MAL_ROSQUEADA"}
VISTAS_LATERAIS = (Vista.LATERAL1, Vista.LATERAL2)


class ErroDeRegistro(Exception):
    """Base dos erros deste modulo."""


class EventoInvalido(ErroDeRegistro):
    """O evento nao pode ser gravado como esta (falta evidencia minima ou coerencia)."""


class ConflitoDeItem(ErroDeRegistro):
    """Ja existe evidencia diferente para este `item_id`. Nada foi sobrescrito."""


@dataclass(frozen=True)
class LinhaDeVista:
    """Projecao do que o banco guarda. `status` e o estado do dominio (ok|defeito|inconclusivo):
    e ele que torna o round-trip comparavel — a classe `normal` nao existe no catalogo de defeito."""
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


# ---------------------------------------------------------------- mapeamentos puros

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
    if medida.classe is Classe.INCONCLUSIVO or medida.qualidade is Qualidade.INSUFICIENTE:
        return Papel.FALLBACK
    return Papel.DECIDE


def status_final(estados: dict[Dominio, str], evidencias_faltando: bool) -> str:
    """Defeito manda; sem defeito e com evidencia faltando, inconclusivo; senao ok."""
    if any(e == "defeito" for e in estados.values()):
        return "defeito"
    if evidencias_faltando or any(e == "inconclusivo" for e in estados.values()):
        return "inconclusivo"
    return "ok"


def qualidade_registro(laterais_decisorias: int) -> str:
    faltando = len(VISTAS_LATERAIS) - laterais_decisorias
    if faltando <= 0:
        return "completo"
    return "parcial_1_vista_faltante" if faltando == 1 else "evidencia_insuficiente"


def discordancia(medidas: tuple[Medida, ...], dominio: Dominio) -> bool:
    classes = {m.classe for m in medidas if m.vista in VISTAS_LATERAIS and m.dominio is dominio}
    return len(classes) > 1


# ---------------------------------------------------------------- registro

class Registro:
    """Registro local em SQLite. Uma instancia = um arquivo."""

    def __init__(self, conexao: sqlite3.Connection):
        self._cx = conexao

    @classmethod
    def abrir(cls, caminho: str | Path) -> "Registro":
        cx = sqlite3.connect(str(caminho))
        cx.row_factory = sqlite3.Row
        cx.executescript(ESQUEMA.read_text(encoding="utf-8"))
        cx.commit()
        return cls(cx)

    def fechar(self) -> None:
        self._cx.close()

    # -------------------------------------------------- escrita

    def registrar(self, evento: Evento) -> str:
        """Grava o evento. Devolve 'inserido' ou 'repetido'. Nunca sobrescreve."""
        self._validar(evento)
        existente = self.ler(evento.item_id)
        if existente is not None:
            if self._mesma_evidencia(existente, evento):
                return "repetido"
            raise ConflitoDeItem(
                f"item {evento.item_id!r} ja tem evidencia diferente gravada; nada foi alterado")

        estados = self._estados(evento)
        dec = {v: sum(1 for m in evento.medidas
                      if m.vista is v and m.dominio is not None) for v in VISTAS_LATERAIS}
        faltando = any(dec[v] == 0 for v in VISTAS_LATERAIS)
        self._cx.execute(
            "INSERT INTO item (item_id, timestamp_trigger, status_tampa, status_corpo,"
            " discordancia_lateral, status_final, motivo_inconclusivo, qualidade_registro)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (evento.item_id, evento.capturado_em.isoformat(),
             estados[Dominio.TAMPA], estados[Dominio.CORPO],
             int(discordancia(evento.medidas, Dominio.TAMPA) or discordancia(evento.medidas, Dominio.CORPO)),
             status_final(estados, faltando),
             None if not faltando else "vista_lateral_ausente",
             qualidade_registro(sum(1 for v in VISTAS_LATERAIS if dec[v] > 0))))
        for linha, classe in self._linhas(evento):
            self._cx.execute(
                "INSERT INTO inspecao_vista (item_id, vista, dominio, papel, vista_disponivel,"
                " qualidade_imagem, status_vista, codigo_defeito, confianca) VALUES (?,?,?,?,?,?,?,?,?)",
                (evento.item_id, linha.vista.value,
                 linha.dominio.value if linha.dominio else None, linha.papel.value,
                 int(linha.disponivel),
                 "adequada" if linha.status != "inconclusivo" else "baixa",
                 linha.status, MAPA_CODIGO.get(classe), linha.confianca))
        self._cx.commit()
        return "inserido"

    def _validar(self, evento: Evento) -> None:
        """Evento sem medida NAO e invalido: e um item inconclusivo (D-04). O que nao pode e
        evento sem identidade."""
        if not evento.item_id.strip():
            raise EventoInvalido("evento sem item_id nao e rastreavel")

    def _estados(self, evento: Evento) -> dict[Dominio, str]:
        estados: dict[Dominio, str] = {}
        for dom in (Dominio.TAMPA, Dominio.CORPO):
            classes = {m.classe for m in evento.medidas if m.dominio is dom and m.vista in VISTAS_LATERAIS}
            if not classes:
                estados[dom] = "inconclusivo"
            elif Classe.INCONCLUSIVO in classes:
                estados[dom] = "inconclusivo"
            elif any(c is not Classe.NORMAL for c in classes):
                estados[dom] = "defeito"
            else:
                estados[dom] = "ok"
        return estados

    def _linhas(self, evento: Evento) -> tuple[tuple[LinhaDeVista, Classe | None], ...]:
        """Cada medida vira uma linha; cada vista declarada sem medida vira linha auxiliar
        inconclusiva (capturada e nao decidida — nao e evidencia de nada)."""
        pares: list[tuple[LinhaDeVista, Classe | None]] = []
        decididas: set[Vista] = set()
        for m in evento.medidas:
            pares.append((LinhaDeVista(vista=m.vista, dominio=m.dominio, papel=papel_da_linha(m.vista, m),
                                       disponivel=True, status=estado_da_classe(m.classe),
                                       confianca=m.confianca), m.classe))
            decididas.add(m.vista)
        for v in evento.vistas:
            if v not in decididas:
                pares.append((LinhaDeVista(vista=v, dominio=None, papel=Papel.AUXILIAR, disponivel=True,
                                           status="inconclusivo", confianca=None), None))
        return tuple(sorted(pares, key=lambda par: (par[0].vista.value, par[0].dominio.value if par[0].dominio else "")))

    # -------------------------------------------------- leitura

    def ler(self, item_id: str) -> ItemGravado | None:
        r = self._cx.execute("SELECT * FROM item WHERE item_id = ?", (item_id,)).fetchone()
        if r is None:
            return None
        vistas = tuple(
            LinhaDeVista(vista=Vista(v["vista"]),
                         dominio=Dominio(v["dominio"]) if v["dominio"] else None,
                         papel=Papel(v["papel"]), disponivel=bool(v["vista_disponivel"]),
                         status=v["status_vista"], confianca=v["confianca"])
            for v in self._cx.execute(
                "SELECT * FROM inspecao_vista WHERE item_id = ? ORDER BY id", (item_id,)).fetchall())
        return ItemGravado(item_id=r["item_id"], capturado_em=r["timestamp_trigger"],
                           status_tampa=r["status_tampa"], status_corpo=r["status_corpo"],
                           status_final=r["status_final"], qualidade_registro=r["qualidade_registro"],
                           motivo_inconclusivo=r["motivo_inconclusivo"], vistas=vistas)

    def contar(self) -> int:
        return int(self._cx.execute("SELECT COUNT(*) FROM item").fetchone()[0])

    def _mesma_evidencia(self, gravado: ItemGravado, evento: Evento) -> bool:
        """Reenvio da MESMA evidencia: comparar a evidencia GRAVADA e mais forte que comparar um
        hash inventado. A projecao usa exatamente o que o banco representa."""
        return _chave(gravado.vistas) == _chave(l for l, _ in self._linhas(evento))


def _chave(linhas) -> tuple:
    """Projecao comparavel de um conjunto de linhas de vista."""
    return tuple(sorted((l.vista.value, l.dominio.value if l.dominio else None, l.papel.value,
                         l.disponivel, l.status, l.confianca) for l in linhas))
