"""Conformidade por dominio: a regra da D-04 (+ emenda) e da D-29, em um lugar so.

Nome: as decisoes D-04 e D-29 chamam este passo de "fusao por dominios", mas o lexico corrente do
repo para o comportamento e "regra deterministica" (`docs/pocs/README.md:10`) e "combinacao das
decisoes" (D-05:83); e "fusao" carrega a conotacao de votacao que a D-04/D-30 rejeitam. Este modulo usa o
vocabulario de qualidade: item conforme, nao conforme ou inconclusivo. Divergencia de vocabulario
declarada; alinhar o texto das decisoes e decisao do usuario, nao minha.

Nao existe maioria global entre vistas. As duas laterais decidem; o topo e check dimensional que
pode escalonar e NUNCA aprovar. Regras, todas testadas:
  1. papel por vista e declarado no rig (`ConfiguracaoDoRig`); vista fora do conjunto e ERRO, nao
     suposicao (fail-closed);
  2. defeito detectado em qualquer vista decisoria do dominio REPROVA, com precedencia declarada
     (no dominio da tampa: `tampa_ausente` > `defeito_tampa`; empate de classe resolvido pela
     maior confianca);
  3. aprovacao exige TODOS os dominios medidos, com todas as vistas decisorias emitindo `normal` e
     qualidade ok. Qualquer ausencia, vista de menos, qualidade ruim ou inconclusivo produz
     `inconclusivo`; nunca aprovacao silenciosa;
  4. discordancia lateral = as vistas decisorias de um dominio NAO emitiram a mesma classe; vista
     unica nunca e discordancia;
  5. o check dimensional (topo) nao classifica: escalonamento pedido, qualidade ruim ou motivo
     declarado tambem levam o item a `inconclusivo` (vai para analise humana), jamais a aprovado;
  6. a origem de cada medida (vista, classe) fica registrada no resultado.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from dominio import Classe, Dominio, Medida, Qualidade, Vista

#: precedencia declarada por dominio (D-29). Onde ha uma classe so, a precedencia e trivial.
PRECEDENCIA: dict[Dominio, tuple[Classe, ...]] = {
    Dominio.TAMPA: (Classe.TAMPA_AUSENTE, Classe.DEFEITO_TAMPA, Classe.NORMAL),
    Dominio.CORPO: (Classe.DEFORMIDADE, Classe.NORMAL),
}

MOTIVO_RIG_INCOMPLETO = "rig_incompleto"

#: o que o PROJETO exige (RF-01/RF-01.2 + D-23): dois dominios, duas vistas decisorias e o check.
#: A configuracao do rig pode REDUZIR isso; e reducao bloqueia aprovacao, nunca a libera (D-29).
DOMINIOS_ESPERADOS: tuple[Dominio, ...] = (Dominio.TAMPA, Dominio.CORPO)
VISTAS_DECISORIAS_ESPERADAS = 2

MOTIVO_CHECK_AUSENTE = "check_dimensional_ausente"
MOTIVO_CHECK_ESCALONADO = "check_dimensional_escalonado"
MOTIVO_CHECK_VIOLADO = "check_dimensional_violado"


class ErroDeConformidade(Exception):
    """A conformidade nao pode ser aplicada (entrada incoerente com o rig declarado)."""


@dataclass(frozen=True)
class ConfiguracaoDoRig:
    """O rig declarado. Configuracao menor nao vira aprovacao: domingo nao medido bloqueia."""

    vistas_decisorias: tuple[Vista, ...] = (Vista.LATERAL1, Vista.LATERAL2)
    vista_check: Vista = Vista.TOPO
    check_obrigatorio: bool = True
    dominios_medidos: frozenset[Dominio] = frozenset({Dominio.TAMPA, Dominio.CORPO})

    @property
    def vistas_conhecidas(self) -> frozenset[Vista]:
        return frozenset(self.vistas_decisorias) | {self.vista_check}


@dataclass(frozen=True)
class ResultadoDeDominio:
    dominio: Dominio
    status: str
    classe: Classe | None
    origem: tuple[tuple[Vista, Classe], ...]
    motivos: tuple[str, ...]


@dataclass(frozen=True)
class ResultadoDaConformidade:
    status: str  # ok | defeito | inconclusivo
    por_dominio: tuple[ResultadoDeDominio, ...]
    discordancia_lateral: bool
    motivos: tuple[str, ...]
    check_escalonado: bool
    #: origem das medidas do check dimensional (vista, classe): o check nao vota, mas fica registrado
    check_origem: tuple[tuple[Vista, Classe], ...] = ()


def avaliar_conformidade(
    medidas: Sequence[Medida],
    config: ConfiguracaoDoRig | None = None,
    check_escalonado: bool = False,
    check_motivo: str | None = None,
    check_presente: bool | None = None,
) -> ResultadoDaConformidade:
    """Aplica as regras.

    `check_escalonado`/`check_motivo` e o pedido vindo do check dimensional (topo), que NAO
    classifica. `check_presente` diz se o check foi executado de fato: quando None, deduz das medidas
    de topo recebidas. Check nao instrumentado com `check_obrigatorio=True` bloqueia a aprovacao;
    evidencia ausente nao vira aprovacao (D-04)."""
    config = config or ConfiguracaoDoRig()
    for m in medidas:
        if m.vista not in config.vistas_conhecidas:
            raise ErroDeConformidade(
                f"vista {m.vista.value!r} nao esta no rig declarado "
                f"({sorted(v.value for v in config.vistas_conhecidas)})"
            )

    decisorias = [m for m in medidas if m.vista in config.vistas_decisorias]
    do_check = [m for m in medidas if m.vista is config.vista_check]

    resultados: list[ResultadoDeDominio] = []
    for (
        dominio
    ) in DOMINIOS_ESPERADOS:  # sempre os dois: dominio nao declarado tambem reporta
        resultados.append(_avaliar_dominio(dominio, decisorias, config))

    motivos: list[str] = [m for r in resultados for m in r.motivos]
    escalonado = False
    if check_escalonado:
        escalonado = True
        motivos.append(check_motivo or MOTIVO_CHECK_VIOLADO)
    if any(m.qualidade is Qualidade.INSUFICIENTE for m in do_check):
        escalonado = True
        motivos.append(MOTIVO_CHECK_ESCALONADO)
    presente = (len(do_check) > 0) if check_presente is None else check_presente
    if config.check_obrigatorio and not presente:
        escalonado = True
        motivos.append(MOTIVO_CHECK_AUSENTE)

    discordancia = any(
        "classes_divergentes" in m for r in resultados for m in r.motivos
    )
    if any(r.status == "defeito" for r in resultados):
        status = "defeito"
    elif escalonado or any(r.status == "inconclusivo" for r in resultados):
        status = "inconclusivo"
    else:
        status = "ok"
    if not _rig_completo(config):
        motivos.append(
            MOTIVO_RIG_INCOMPLETO
        )  # sempre visivel, nao so quando seria aprovado
        if status == "ok":
            status = "inconclusivo"
    return ResultadoDaConformidade(
        status=status,
        por_dominio=tuple(resultados),
        discordancia_lateral=discordancia,
        motivos=tuple(motivos),
        check_escalonado=escalonado,
        check_origem=tuple((m.vista, m.classe) for m in do_check),
    )


def _rig_completo(config: ConfiguracaoDoRig) -> bool:
    """Aprovacao so existe em rig completo. Reduzir a configuracao nunca pode liberar item (D-29)."""
    return (
        len(config.vistas_decisorias) >= VISTAS_DECISORIAS_ESPERADAS
        and config.check_obrigatorio
        and all(d in config.dominios_medidos for d in DOMINIOS_ESPERADOS)
    )


def _avaliar_dominio(
    dominio: Dominio, medidas: Sequence[Medida], config: ConfiguracaoDoRig
) -> ResultadoDeDominio:
    do_dominio = [m for m in medidas if m.dominio is dominio]
    origem = tuple((m.vista, m.classe) for m in do_dominio)
    motivos: list[str] = []

    if dominio not in config.dominios_medidos:
        return ResultadoDeDominio(
            dominio,
            "inconclusivo",
            None,
            origem,
            (f"dominio_nao_declarado_{dominio.value}",),
        )
    if not do_dominio:
        return ResultadoDeDominio(
            dominio,
            "inconclusivo",
            None,
            origem,
            (f"dominio_nao_medido_{dominio.value}",),
        )
    vistas = {m.vista for m in do_dominio}
    if len(vistas) < len(config.vistas_decisorias):
        motivos.append(f"vistas_insuficientes_{dominio.value}")
    classes = {m.classe for m in do_dominio}
    if len(classes) > 1:
        motivos.append(f"classes_divergentes_{dominio.value}")

    defeitos = [
        m for m in do_dominio if m.classe not in (Classe.NORMAL, Classe.INCONCLUSIVO)
    ]
    if defeitos:
        classe = _por_precedencia(dominio, defeitos)
        return ResultadoDeDominio(dominio, "defeito", classe, origem, tuple(motivos))
    if (
        Classe.INCONCLUSIVO in classes
        or motivos
        or any(m.qualidade is not Qualidade.OK for m in do_dominio)
    ):
        return ResultadoDeDominio(dominio, "inconclusivo", None, origem, tuple(motivos))
    return ResultadoDeDominio(dominio, "ok", Classe.NORMAL, origem, ())


def _por_precedencia(dominio: Dominio, defeitos: Sequence[Medida]) -> Classe:
    ordem = PRECEDENCIA[dominio]
    for classe in ordem:
        do_grupo = [m for m in defeitos if m.classe is classe]
        if do_grupo:
            return max(do_grupo, key=lambda m: m.confianca).classe
    raise ErroDeConformidade(
        f"classe de defeito fora da precedencia declarada para {dominio.value}"
    )
