"""PoC-02: politica de decisao da tampa: geometria primaria + escalonamento para modelo auxiliar.

CONTRATO (alinhado a D-04 "decisao por dominio" e D-11 "camada secundaria nao cancela o nucleo"):

  entrada : medidas da geometria da tampa na vista primaria + qualidade da captura
  saida   : decisao (normal | tampa_ausente | tampa_mal_rosqueada | inconclusivo)
            + flag de escalonamento e o MOTIVO

  O fallback NAO esta sempre ligado: ele e acionado quando um limiar da geometria NAO e atingido
  (contorno insuficiente, incerteza do angulo cruzando o limite, captura degradada). Nesse caminho,
  o recorte da tampa na OUTRA vista vai para um modelo auxiliar. Como e caminho raro, o custo extra
  so incide na minoria dos itens.

  Assimetria obrigatoria (D-11): a saida do modelo auxiliar NUNCA cancela reprovacao da geometria;
  ela so pode reprovar, confirmar ou manter inconclusivo. Evidencia insuficiente nunca vira aprovacao.
"""
from __future__ import annotations

from dataclasses import dataclass, field

NORMAL = "normal"
AUSENTE = "tampa_ausente"
MAL_ROSQUEADA = "tampa_mal_rosqueada"
INCONCLUSIVO = "inconclusivo"

# Motivos de escalonamento (para medir depois quanto o fallback e acionado e por que)
MOTIVO_ARCO_INSUFICIENTE = "arco_insuficiente"
MOTIVO_ANGULO_NA_ZONA_CINZENTA = "angulo_zona_cinzenta"
MOTIVO_CAPTURA_DEGRADADA = "captura_degradada"
MOTIVO_SEM_GEOMETRIA = "sem_geometria"


@dataclass(frozen=True)
class Limiares:
    arco_visivel_min_graus: float = 300.0    # precondicao de captura medida no harness de elipse
    # PROVISORIO (D-24): sem fonte primaria transferivel; nao usar como criterio de aceitacao
    # ate a calibracao empirica (docs/reference/limiares-tampa-fonte-e-calibracao.md)
    tilt_reprova_graus: float = 4.0           # acima disso: mal rosqueada
    tilt_incerto_graus: float = 2.0           # entre incerto e reprova: zona cinzenta -> escalona
    altura_ausente_px: float = 3.0            # silhueta sem cupula da tampa (em px)
    cnr_min: float = 12.0                     # qualidade minima de contraste (provisorio: sem fonte primaria, D-24)
    especular_max: float = 0.03               # cobertura especular maxima


@dataclass(frozen=True)
class GeometriaTampa:
    """Medidas da vista primaria (o que o PoC-08/preproc entrega)."""

    contorno_ok: bool
    arco_visivel_graus: float
    tilt_graus: float                          # 0 = rosqueada corretamente
    altura_cupula_px: float                    # altura da cupula da tampa na silhueta
    cnr: float = 20.0
    especular: float = 0.0
    inliers: int = 0


@dataclass(frozen=True)
class Decisao:
    classe: str
    escalar: bool = False
    motivos: tuple[str, ...] = field(default_factory=tuple)
    origem: str = "geometria"                  # geometria | auxiliar | politica


def decidir(g: GeometriaTampa, lim: Limiares = Limiares()) -> Decisao:
    """Decisao pela geometria, com o gatilho de fallback embutido."""
    motivos: list[str] = []

    # 1) captura degradada: qualidade insuficiente nao pode virar aprovacao silenciosa (D-04)
    if g.cnr < lim.cnr_min or g.especular > lim.especular_max:
        return Decisao(INCONCLUSIVO, escalar=True, motivos=(MOTIVO_CAPTURA_DEGRADADA,))

    # 2) sem contorno utilizavel: nao ha o que medir -> outra vista
    if not g.contorno_ok:
        return Decisao(INCONCLUSIVO, escalar=True, motivos=(MOTIVO_SEM_GEOMETRIA,))

    # 3) tampa ausente por silhueta: decisao forte, NAO escala (medida direta, sem angulo)
    if g.altura_cupula_px < lim.altura_ausente_px:
        return Decisao(AUSENTE, escalar=False, motivos=())

    # 4) contorno insuficiente para confiar no angulo -> recorte da outra vista
    if g.arco_visivel_graus < lim.arco_visivel_min_graus:
        motivos.append(MOTIVO_ARCO_INSUFICIENTE)

    # 5) angulo: reprova com margem; zona cinzenta tambem escalona (dupla checagem)
    tilt = abs(g.tilt_graus)
    if tilt >= lim.tilt_reprova_graus:
        classe = MAL_ROSQUEADA
    elif tilt >= lim.tilt_incerto_graus:
        classe = INCONCLUSIVO
        motivos.append(MOTIVO_ANGULO_NA_ZONA_CINZENTA)
    else:
        classe = NORMAL

    escalar = bool(motivos)
    return Decisao(classe, escalar=escalar, motivos=tuple(motivos))


def aplicar_auxiliar(base: Decisao, auxiliar: dict | None) -> Decisao:
    """Funde a saida do modelo auxiliar (recorte da outra vista) na decisao da geometria.

    Regras assimetricas (D-11):
      * auxiliar indisponivel/inconclusivo  -> mantem a decisao base (nao inventa aprovacao);
      * geometria REPROVOU                  -> auxiliar NAO cancela (nunca rebaixa reprovacao);
      * geometria inconclusiva              -> auxiliar pode concluir (para qualquer classe);
      * geometria aprovou e escala          -> auxiliar pode reprovar ou confirmar normal.
    """
    if not base.escalar or auxiliar is None:
        # auxiliar None = caminho de fallback nao executado: mantem a decisao base
        return base

    classe_aux = auxiliar.get("classe")
    if classe_aux in (None, INCONCLUSIVO):
        # escalamos PORQUE a evidencia era insuficiente (contorno/qualidade): sem conclusao do
        # auxiliar, o item NAO pode voltar como aprovado -- vira inconclusivo (D-04).
        return Decisao(INCONCLUSIVO, escalar=False,
                       motivos=base.motivos + ("auxiliar_inconclusivo",), origem="auxiliar")

    if base.classe == MAL_ROSQUEADA or base.classe == AUSENTE:
        return base                                        # geometria reprovou: nao cancela

    if base.classe == NORMAL and classe_aux != NORMAL:
        return Decisao(classe_aux, escalar=False,
                       motivos=base.motivos + ("auxiliar_reprovou",), origem="auxiliar")

    if base.classe == INCONCLUSIVO:
        return Decisao(classe_aux, escalar=False,
                       motivos=base.motivos + ("auxiliar_concluiu",), origem="auxiliar")

    return base
