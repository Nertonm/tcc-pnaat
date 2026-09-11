"""PoC-04: fusao deterministica por dominio (D-04, com a emenda D-23).

O que esta regra corrige: a versao anterior votava por maioria GLOBAL entre vistas e, com isso,
podia cancelar um defeito detectado em um dominio -- apagando o achado mais importante do item.
Aqui:

  * a decisao e POR DOMINIO (tampa e corpo) e nenhum dominio cancela o outro;
  * a vista de topo NAO decide tampa: ela e check dimensional independente (so veta/escala);
  * discordancia entre as vistas decisorias e preservada e registrada;
  * evidencia insuficiente vira `inconclusivo` -- nunca aprovacao silenciosa;
  * dominio declarado como nao medido impede aprovacao, mas nao inventa defeito;
  * a origem de cada medida e registrada (view_id, dominio, classe).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..events import CLASSES_DE_DEFEITO, DefectClass, Dominio, Qualidade, ViewResult

DECISORIA = "decisoria"
CHECAGEM = "checagem"

#: Papel de cada vista no rig (D-19/D-23). Vista desconhecida e ERRO, nao suposicao.
PAPEIS: dict[str, str] = {
    "lateral1": DECISORIA,
    "lateral2": DECISORIA,
    "topo": CHECAGEM,
}

#: Dominios que a regra decide e a ordem declarada de precedencia entre eles.
DOMINIOS_DECIDIDOS: tuple[Dominio, ...] = (Dominio.TAMPA, Dominio.CORPO)

#: Precedencia deterministica dentro do dominio (ausente e mais grave que mal rosqueada).
PRECEDENCIA: dict[DefectClass, int] = {
    DefectClass.TAMPA_AUSENTE: 2,
    DefectClass.TAMPA_MAL_ROSQUEADA: 1,
    DefectClass.DEFORMIDADE: 1,
}

OK = "ok"
DEFEITO = "defeito"
INCONCLUSIVO = "inconclusivo"

MOTIVO_SEM_VISTA = "sem_vista_decisoria"
MOTIVO_VISTA_AUSENTE = "vista_decisoria_ausente"
MOTIVO_EVIDENCIA_INSUFICIENTE = "evidencia_insuficiente"
MOTIVO_DISCORDANCIA = "discordancia"
MOTIVO_CLASSES_DIVERGENTES = "classes_divergentes"
MOTIVO_DOMINIO_NAO_MEDIDO = "dominio_nao_medido"
MOTIVO_CHECK_AUSENTE = "check_dimensional_ausente"
MOTIVO_CHECK_INDISPONIVEL = "check_dimensional_indisponivel"
MOTIVO_CHECK_VIOLADO = "check_dimensional_violado"


@dataclass(frozen=True)
class ConfiguracaoFusao:
    """Configuracao DECLARADA do rig que produziu as vistas.

    A regra nao adivinha a bancada: ela recebe o que o rig declara conseguir medir.
    `vistas_decisoria_por_dominio` = quantas vistas precisam concordar para APROVAR o dominio.
    """

    rig_id: str = "nao-declarado"
    vistas_decisoria_por_dominio: int = 2
    checagem_obrigatoria: bool = True
    dominios_medidos: tuple[Dominio, ...] = DOMINIOS_DECIDIDOS


@dataclass(frozen=True)
class Fusao:
    """Resultado do item: classe final mais o estado por dominio (campos do schema `item`)."""

    classe: DefectClass
    confidence: float
    status_tampa: str
    status_corpo: str
    classe_tampa: DefectClass | None = None
    classe_corpo: DefectClass | None = None
    discordancia_lateral: bool = False
    escalonado: bool = False
    qualidade_registro: str = "completo"
    motivos: tuple[str, ...] = ()
    origens: tuple[tuple[str, str, str], ...] = ()

    def como_dict(self) -> dict:
        """Serializa no vocabulario do schema de telemetria (dados-telemetria.md)."""
        return {
            "classe": self.classe.value,
            "confidence": self.confidence,
            "status_tampa": self.status_tampa,
            "status_corpo": self.status_corpo,
            "classe_tampa": None if self.classe_tampa is None else self.classe_tampa.value,
            "classe_corpo": None if self.classe_corpo is None else self.classe_corpo.value,
            "discordancia_lateral": int(self.discordancia_lateral),
            "escalonado": self.escalonado,
            "qualidade_registro": self.qualidade_registro,
            "motivos": list(self.motivos),
            "origens": [list(o) for o in self.origens],
        }


def papel(view_id: str) -> str:
    """Papel da vista no rig. Vista desconhecida -> erro (fail closed)."""
    try:
        return PAPEIS[view_id]
    except KeyError:
        raise ValueError(
            f"vista desconhecida: {view_id!r} (conhecidas: {sorted(PAPEIS)})"
        ) from None


def _validar(views: Sequence[ViewResult]) -> None:
    if not views:
        raise ValueError("sem vistas para fundir")
    vistas_usadas: set[tuple[str, Dominio]] = set()
    for v in views:
        papel(v.view_id)  # vista fora do rig nao entra na decisao
        chave = (v.view_id, v.dominio)
        if chave in vistas_usadas:
            raise ValueError(
                f"medicao duplicada da vista {v.view_id!r} no dominio {v.dominio.value!r}"
            )
        vistas_usadas.add(chave)


def _decidir_dominio(
    vistas_dominio: Sequence[ViewResult],
    dominio: Dominio,
    config: ConfiguracaoFusao,
    motivos: list[str],
) -> tuple[str, DefectClass | None, bool]:
    """Decide UM dominio com as vistas decisorias que o medem."""
    if dominio not in config.dominios_medidos:
        motivos.append(f"{MOTIVO_DOMINIO_NAO_MEDIDO}_{dominio.value}")
        return INCONCLUSIVO, None, False

    if not vistas_dominio:
        motivos.append(f"{MOTIVO_SEM_VISTA}_{dominio.value}")
        return INCONCLUSIVO, None, False

    # Discordancia lateral = as vistas decisorias do dominio NAO emitiram a mesma classe.
    # Vale para "defeito x normal" e tambem para "defeito x defeito de outra classe".
    classes_vistas = {v.defect for v in vistas_dominio}
    discordancia = len(vistas_dominio) > 1 and len(classes_vistas) > 1
    if discordancia:
        motivos.append(f"{MOTIVO_DISCORDANCIA}_{dominio.value}")

    defeitos = [v for v in vistas_dominio if v.defect in CLASSES_DE_DEFEITO[dominio]]
    if defeitos:
        # Defeito detectado em qualquer vista do dominio REPROVA e nao e cancelado por ninguem.
        # Decisao conservadora: vale mesmo com qualidade insuficiente (o item vai para analise).
        escolhido = max(defeitos, key=lambda v: (PRECEDENCIA[v.defect], v.confidence))
        if len({v.defect for v in defeitos}) > 1:
            motivos.append(f"{MOTIVO_CLASSES_DIVERGENTES}_{dominio.value}")
        return DEFEITO, escolhido.defect, discordancia

    if len(vistas_dominio) < config.vistas_decisoria_por_dominio:
        motivos.append(f"{MOTIVO_VISTA_AUSENTE}_{dominio.value}")
        return INCONCLUSIVO, None, discordancia

    insuficientes = [
        v
        for v in vistas_dominio
        if v.qualidade != Qualidade.OK or v.defect == DefectClass.INCONCLUSIVO
    ]
    if insuficientes:
        motivos.append(f"{MOTIVO_EVIDENCIA_INSUFICIENTE}_{dominio.value}")
        return INCONCLUSIVO, None, discordancia

    return OK, None, discordancia


def fundir(views: Sequence[ViewResult], config: ConfiguracaoFusao = ConfiguracaoFusao()) -> Fusao:
    """Funde as medidas das vistas em uma decisao de item por dominio."""
    _validar(views)

    decisors = [v for v in views if papel(v.view_id) == DECISORIA]
    checagens = [v for v in views if papel(v.view_id) == CHECAGEM]
    motivos: list[str] = []

    status: dict[Dominio, str] = {}
    classes: dict[Dominio, DefectClass | None] = {}
    discordancia = False
    for dominio in DOMINIOS_DECIDIDOS:
        vistas_dominio = [v for v in decisors if v.dominio == dominio]
        st, cl, disc = _decidir_dominio(vistas_dominio, dominio, config, motivos)
        status[dominio] = st
        classes[dominio] = cl
        discordancia = discordancia or disc

    # Escalonamento pedido por uma vista decisoria (ex.: suspeita do detector de anomalia, D-11).
    escalonado = False
    for v in decisors:
        if v.escalona:
            escalonado = True
            motivos.append(v.motivo or "escalonado_por_vista_decisoria")

    # Check dimensional (D-23): nao classifica e nao aprova; so veta/escala.
    if not checagens:
        if config.checagem_obrigatoria:
            escalonado = True
            motivos.append(MOTIVO_CHECK_AUSENTE)
    for v in checagens:
        if v.escalona:
            escalonado = True
            motivos.append(v.motivo or MOTIVO_CHECK_VIOLADO)
        if v.qualidade != Qualidade.OK or v.defect == DefectClass.INCONCLUSIVO:
            escalonado = True
            motivos.append(MOTIVO_CHECK_INDISPONIVEL)

    # Decisao do item: defeito em qualquer dominio reprova; aprovacao exige TODOS os dominios ok.
    if status[Dominio.TAMPA] == DEFEITO:
        classe = classes[Dominio.TAMPA]
    elif status[Dominio.CORPO] == DEFEITO:
        classe = classes[Dominio.CORPO]
    elif INCONCLUSIVO in (status[Dominio.TAMPA], status[Dominio.CORPO]) or escalonado:
        classe = DefectClass.INCONCLUSIVO
    else:
        classe = DefectClass.NORMAL
    assert classe is not None  # status DEFEITO sempre traz a classe escolhida

    confianca = _confianca(classe, views, decisors)

    if any(m.startswith(MOTIVO_EVIDENCIA_INSUFICIENTE) for m in motivos):
        qualidade_registro = "evidencia_insuficiente"
    elif any(
        m.startswith((MOTIVO_VISTA_AUSENTE, MOTIVO_SEM_VISTA, MOTIVO_DOMINIO_NAO_MEDIDO, MOTIVO_CHECK_AUSENTE))
        for m in motivos
    ):
        qualidade_registro = "parcial_1_vista_faltante"
    else:
        qualidade_registro = "completo"

    origens = tuple((v.view_id, v.dominio.value, v.defect.value) for v in views)
    return Fusao(
        classe=classe,
        confidence=confianca,
        status_tampa=status[Dominio.TAMPA],
        status_corpo=status[Dominio.CORPO],
        classe_tampa=classes[Dominio.TAMPA],
        classe_corpo=classes[Dominio.CORPO],
        discordancia_lateral=discordancia,
        escalonado=escalonado,
        qualidade_registro=qualidade_registro,
        motivos=tuple(motivos),
        origens=origens,
    )


def _confianca(
    classe: DefectClass, views: Sequence[ViewResult], decisors: Sequence[ViewResult]
) -> float:
    """Confianca declarada com a classe final.

    * defeito: maior confianca entre as vistas que apontaram aquela classe;
    * normal: MENOR confianca entre as vistas decisorias que sustentam a aprovacao (elo fraco);
    * inconclusivo: maior confianca entre as vistas disponiveis (a evidencia que existe).
    """
    if classe == DefectClass.NORMAL:
        apoios = [v.confidence for v in decisors if v.defect == DefectClass.NORMAL]
        return round(min(apoios), 4) if apoios else 0.0
    if classe == DefectClass.INCONCLUSIVO:
        return round(max((v.confidence for v in views), default=0.0), 4)
    apoios = [v.confidence for v in views if v.defect == classe]
    return round(max(apoios), 4) if apoios else 0.0
