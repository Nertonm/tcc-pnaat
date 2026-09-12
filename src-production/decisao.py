"""Decisao da tampa e do corpo (D-30): o classificador decide; a geometria e auxiliar.

Tres caminhos, e so tres:
  1. o classificador da vista devolve classe conclusiva  -> DECIDE (papel `decide`);
  2. o classificador nao pode decidir (indisponivel/inconclusivo) -> FALLBACK: a geometria mede e
     ROTEIA, o resultado sai `inconclusivo` e escalona para analise humana. A geometria NUNCA aprova
     e NUNCA reprova sozinha (D-04 preservada, D-30 explicito);
  3. sempre, em qualquer caminho, as medicoes geometricas entram como `auxiliar` — rastro do que
     sustentou a decisao, nunca voto.

As interfaces sao Protocol: o decisor nao sabe (nem precisa saber) se o classificador e uma CNN, e
a geometria e funcao pura de imagem.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from dominio import Classe, Dominio, Evidencia, Medida, Origem, Papel, Qualidade, Vista


class ClassificadorDeVista(Protocol):
    """Devolve a medida do dominio para a vista, ou None quando nao consegue decidir."""

    identificacao: str

    def prever(self, recorte, dominio: Dominio) -> Medida | None: ...


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

    def __init__(self, classificador: ClassificadorDeVista, geometria: MedidorGeometrico | None = None):
        self._classificador = classificador
        self._geometria = geometria

    def decidir(self, recorte, dominio: Dominio, vista: Vista) -> Resultado:
        medicoes = tuple(self._medir_geometria(recorte))          # papel auxiliar, sempre
        medida = self._classificador.prever(recorte, dominio)      # pode levantar ou devolver None
        if medida is None:
            return self._fallback(dominio, vista, medicoes, motivo="classificador_indisponivel")
        if medida.classe is Classe.INCONCLUSIVO or medida.qualidade is Qualidade.INSUFICIENTE:
            return self._fallback(dominio, vista, medicoes + medida.evidencias,
                                  motivo=f"classificador_inconclusivo:{medida.classe.value}")
        return Resultado(dominio=dominio, vista=vista, classe=medida.classe,
                         confianca=medida.confianca, papel=Papel.DECIDE, escalona=False,
                         motivo="decisao_do_classificador", evidencias=medicoes + medida.evidencias)

    # ---------------------------------------------------------------- interno

    def _medir_geometria(self, recorte) -> tuple[Evidencia, ...]:
        if self._geometria is None:
            return ()
        return tuple(self._geometria.medir(recorte))

    def _fallback(self, dominio: Dominio, vista: Vista, evidencias: tuple[Evidencia, ...],
                  motivo: str) -> Resultado:
        """Sem decisao do classificador, a geometria roteia: inconclusivo + escala. Nunca aprova."""
        return Resultado(dominio=dominio, vista=vista, classe=Classe.INCONCLUSIVO, confianca=0.0,
                         papel=Papel.FALLBACK, escalona=True, motivo=motivo, evidencias=evidencias)
