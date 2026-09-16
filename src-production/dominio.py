"""Dominio do sistema: classes por dominio, evidencia tipada e o evento rastreavel.

Regras que este modulo faz valer (nao sao comentario, sao guarda):
  - D-28: a classe pertence a um dominio. Classe fora do vocabulario do seu dominio e recusada na
    construcao da medida; `deformidade` nao existe no dominio da tampa e vice-versa.
  - D-30: toda medida diz QUEM decidiu (`Papel.decide`) e o que e apenas auxiliar
    (`Papel.auxiliar`) ou rota de excecao (`Papel.fallback`). Medida auxiliar nao vira voto.
  - Contrato do evento (docs/arquitetura.md): identificador, timestamp com fuso, origem,
    localizacao, esteira, vistas, classe, qualidade, evidencia e versao do contrato.

Nada aqui importa o namespace de PoCs: o corte com `src/pocs` e limpo, por decisao.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

VERSAO_CONTRATO = "1"


class Dominio(str, Enum):
    TAMPA = "tampa"
    CORPO = "corpo"


class Classe(str, Enum):
    NORMAL = "normal"
    TAMPA_AUSENTE = "tampa_ausente"
    DEFEITO_TAMPA = "defeito_tampa"  # D-31: funde mal_rosqueada + danificada + aberta
    DEFORMIDADE = "deformidade"
    INCONCLUSIVO = "inconclusivo"


#: D-28; vocabulario canonico por dominio. Fonte unica da verdade.
VOCABULARIO: dict[Dominio, frozenset[Classe]] = {
    Dominio.TAMPA: frozenset(
        {Classe.NORMAL, Classe.TAMPA_AUSENTE, Classe.DEFEITO_TAMPA, Classe.INCONCLUSIVO}
    ),
    Dominio.CORPO: frozenset({Classe.NORMAL, Classe.DEFORMIDADE, Classe.INCONCLUSIVO}),
}


class Papel(str, Enum):
    """D-30: quem sustenta a decisao."""

    DECIDE = "decide"
    AUXILIAR = "auxiliar"
    FALLBACK = "fallback"


class Origem(str, Enum):
    CLASSIFICADOR = "classificador"
    GEOMETRIA = "geometria"


class Vista(str, Enum):
    LATERAL1 = "lateral1"
    LATERAL2 = "lateral2"
    TOPO = "topo"


class Qualidade(str, Enum):
    OK = "ok"
    INSUFICIENTE = "insuficiente"


@dataclass(frozen=True)
class Evidencia:
    """O que sustentou a decisao: grandeza, valor, unidade, quem produziu e com que papel.

    `fonte` e obrigatoria quando a grandeza e um limiar que decide: sem `arquivo:linha` ou
    protocolo registrado, o limiar nao passa de parametro provisorio (D-24).
    """

    grandeza: str
    valor: float | None
    unidade: str
    origem: Origem
    papel: Papel
    metodo: str
    fonte: str | None = None

    def provisorio(self) -> bool:
        return self.fonte is None


@dataclass(frozen=True)
class Medida:
    """Resultado de uma vista para um dominio. Classe validada contra o dominio (D-28)."""

    vista: Vista
    dominio: Dominio
    classe: Classe
    confianca: float
    qualidade: Qualidade = Qualidade.OK
    evidencias: tuple[Evidencia, ...] = ()

    def __post_init__(self) -> None:
        if self.classe not in VOCABULARIO[self.dominio]:
            raise ValueError(
                f"classe {self.classe.value!r} nao existe no dominio {self.dominio.value!r} "
                f"(vocabulario: {sorted(c.value for c in VOCABULARIO[self.dominio])})"
            )
        if not 0.0 <= self.confianca <= 1.0:
            raise ValueError(f"confianca fora de [0,1]: {self.confianca}")

    @property
    def conclusiva(self) -> bool:
        return self.qualidade is Qualidade.OK and self.classe is not Classe.INCONCLUSIVO


@dataclass(frozen=True)
class Evento:
    """O item como evento rastreavel. Os campos minimos do contrato, todos obrigatorios."""

    item_id: str
    capturado_em: datetime
    equipamento: str
    localizacao: str
    vistas: tuple[Vista, ...]
    medidas: tuple[Medida, ...]
    status: Classe
    esteira: str | None = None
    versao_contrato: str = VERSAO_CONTRATO

    def __post_init__(self) -> None:
        if self.capturado_em.tzinfo is None:
            raise ValueError(
                "capturado_em precisa de fuso (timestamp sem fuso nao e rastreavel)"
            )
        if not self.vistas:
            raise ValueError(
                "evento sem vista nenhuma nao e evento: ausencia de evidencia e inconclusivo"
            )

    @staticmethod
    def agora() -> datetime:
        return datetime.now(timezone.utc)
