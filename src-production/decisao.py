"""Decisao da tampa e do corpo (D-30): o classificador decide; a geometria e auxiliar.

Tres caminhos, e so tres:
  1. o classificador da vista devolve classe conclusiva  -> DECIDE (papel `decide`);
  2. o classificador nao pode decidir (indisponivel/inconclusivo) -> FALLBACK: a geometria mede e
     ROTEIA, o resultado sai `inconclusivo` e escalona para analise humana. A geometria NUNCA aprova
     e NUNCA reprova sozinha (D-04 preservada, D-30 explicito);
  3. sempre, em qualquer caminho, as medicoes geometricas entram como `auxiliar`; rastro do que
     sustentou a decisao, nunca voto.

As interfaces sao Protocol: o decisor nao sabe (nem precisa saber) se o classificador e uma CNN, e
a geometria e funcao pura de imagem.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from dominio import Classe, Dominio, Evidencia, Medida, Origem, Papel, Qualidade, Vista


class ErroDeDecisao(Exception):
    """O classificador devolveu algo incoerente com o que foi pedido (fail-closed)."""


class ClassificadorDeVista(Protocol):
    """Devolve a medida do dominio para a vista, ou None quando nao consegue decidir."""

    identificacao: str

    def prever(self, recorte, dominio: Dominio, vista: Vista) -> Medida | None:
        """Devolve a medida do dominio PARA ESTA VISTA, ou None quando nao consegue decidir.

        A vista entra como argumento porque so quem chamou sabe de onde veio o recorte: o
        classificador recebe um recorte, nao um arquivo identificado. A medida devolvida tem de
        declarar essa vista e esse dominio; o `Decisor` recusa medida incoerente (fail-closed).
        """


class MedidorGeometrico(Protocol):
    """Mede a vista. Devolve evidencias de papel `auxiliar`; nao decide nada."""

    identificacao: str

    def medir(self, recorte) -> Sequence[Evidencia]: ...


@dataclass(frozen=True)
class Resultado:
    dominio: Dominio
    vista: Vista
    classe: Classe
    confianca: float
    papel: Papel
    escalona: bool
    motivo: str
    evidencias: tuple[Evidencia, ...]

    @property
    def aprovado(self) -> bool:
        return self.classe is Classe.NORMAL and not self.escalona


class Decisor:
    """Aplica D-30 para UMA vista e UM dominio."""

    def __init__(
        self,
        classificador: ClassificadorDeVista,
        geometria: MedidorGeometrico | None = None,
    ):
        self._classificador = classificador
        self._geometria = geometria

    def decidir(
        self,
        recorte,
        dominio: Dominio,
        vista: Vista,
        medicoes: tuple[Evidencia, ...] | None = None,
    ) -> Resultado:
        """Aplica D-30 para UMA vista e UM dominio, e recusa medida que minta sobre a origem.

        `medicoes`: quando a pipeline passa as medicoes da vista, elas sao reaproveitadas. A
        geometria mede a VISTA (um recorte), nao o dominio; medir duas vezes para a mesma vista
        gastava o dobro do tempo e nao acrescentava evidencia nenhuma. Sozinho (sem o argumento), o
        Decisor continua medindo, para poder ser usado fora da pipeline."""
        if medicoes is None:
            medicoes = tuple(self._medir_geometria(recorte))  # papel auxiliar, sempre
        medida = self._classificador.prever(
            recorte, dominio, vista
        )  # pode levantar ou devolver None
        if medida is not None and (
            medida.vista is not vista or medida.dominio is not dominio
        ):
            raise ErroDeDecisao(
                f"classificador {self._classificador.identificacao!r} devolveu medida de "
                f"{medida.vista.value}/{medida.dominio.value} quando foi consultado para "
                f"{vista.value}/{dominio.value}"
            )
        if medida is None:
            return self._fallback(
                dominio, vista, medicoes, motivo="classificador_indisponivel"
            )
        if (
            medida.classe is Classe.INCONCLUSIVO
            or medida.qualidade is Qualidade.INSUFICIENTE
        ):
            return self._fallback(
                dominio,
                vista,
                medicoes + medida.evidencias,
                motivo=f"classificador_inconclusivo:{medida.classe.value}",
            )
        return Resultado(
            dominio=dominio,
            vista=vista,
            classe=medida.classe,
            confianca=medida.confianca,
            papel=Papel.DECIDE,
            escalona=False,
            motivo="decisao_do_classificador",
            evidencias=medicoes + medida.evidencias,
        )

    # ---------------------------------------------------------------- interno

    def _medir_geometria(self, recorte) -> tuple[Evidencia, ...]:
        if self._geometria is None:
            return ()
        evidencias = tuple(self._geometria.medir(recorte))
        invalidas = tuple(
            e
            for e in evidencias
            if e.origem is not Origem.GEOMETRIA or e.papel is not Papel.AUXILIAR
        )
        if invalidas:
            raise ErroDeDecisao(
                "geometria deve produzir somente evidencias com origem geometria e papel auxiliar"
            )
        return evidencias

    def _fallback(
        self,
        dominio: Dominio,
        vista: Vista,
        evidencias: tuple[Evidencia, ...],
        motivo: str,
    ) -> Resultado:
        """Sem decisao do classificador, a geometria roteia: inconclusivo + escala. Nunca aprova."""
        return Resultado(
            dominio=dominio,
            vista=vista,
            classe=Classe.INCONCLUSIVO,
            confianca=0.0,
            papel=Papel.FALLBACK,
            escalona=True,
            motivo=motivo,
            evidencias=evidencias,
        )
