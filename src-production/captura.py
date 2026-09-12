"""Captura: monta as vistas do MESMO item em um `ItemCapturado`.

O que este modulo faz valer:
  - tres vistas por item (RF-01/RF-01.2): `topo`, `lateral1`, `lateral2`;
  - o `item_id` vem do gatilho: captura sem identidade nao existe (levanta `ErroDeCaptura`);
  - ROI fixa **com verificacao de alinhamento** por NCC + tolerancia de deslocamento em px, e
    **fail-closed**: vista fora da tolerancia (ou com o gabarito ausente) nao vira evidencia — sai de
    `vistas_utilizaveis` em vez de ser medida torta e parecer valida. Vista NAO verificada tambem nao
    e utilizavel: sem template do rig o conjunto nao esta calibrado e o item fica inconclusivo
    (D-04), nunca aprovado por omissao;
  - vista ausente nao e erro: e estado. O registro converte ausencia em `inconclusivo`.

Sem camera aqui: a fonte le do disco (bancada/ensaio). A fonte de camera entra quando o rig existir,
atras do mesmo Protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Protocol

import numpy as np

from dominio import Vista

VISTAS_ESPERADAS: tuple[Vista, ...] = (Vista.TOPO, Vista.LATERAL1, Vista.LATERAL2)
LIMITE_ALINHAMENTO = 0.80


class ErroDeCaptura(Exception):
    """A captura nao pode ser montada (identidade, formato, template invalido)."""


class Alinhamento(str, Enum):
    OK = "ok"
    FORA_DA_TOLERANCIA = "fora_da_tolerancia"
    NAO_VERIFICADO = "nao_verificado"


@dataclass(frozen=True)
class VistaCapturada:
    vista: Vista
    imagem: Path
    capturado_em: datetime
    alinhamento: Alinhamento

    def __post_init__(self) -> None:
        if self.capturado_em.tzinfo is None:
            raise ErroDeCaptura("captura sem fuso horario nao e rastreavel")


@dataclass(frozen=True)
class ItemCapturado:
    item_id: str
    trigger_em: datetime
    vistas: tuple[VistaCapturada, ...]

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ErroDeCaptura("item sem identificador nao existe: o item_id vem do gatilho")
        if self.trigger_em.tzinfo is None:
            raise ErroDeCaptura("trigger sem fuso horario nao e rastreavel")
        vistas = [v.vista for v in self.vistas]
        if len(set(vistas)) != len(vistas):
            raise ErroDeCaptura(f"vista repetida no mesmo item: {vistas}")

    @property
    def vistas_utilizaveis(self) -> tuple[VistaCapturada, ...]:
        """Só o que passou na verificacao de alinhamento. Fail-closed por construcao."""
        return tuple(v for v in self.vistas if v.alinhamento is Alinhamento.OK)

    @property
    def faltantes(self) -> tuple[Vista, ...]:
        presentes = {v.vista for v in self.vistas}
        return tuple(v for v in VISTAS_ESPERADAS if v not in presentes)


class VerificadorDeAlinhamento(Protocol):
    """Diz se o item esta na posicao de captura. Nunca decide a classe do defeito."""

    def verificar(self, imagem: np.ndarray) -> tuple[Alinhamento, float]: ...


class VerificadorPorTemplate:
    """Localiza o gabarito por NCC e julga o **deslocamento** contra a posicao de referencia.

    Por que deslocamento e nao o score: o template matching acha o padrao em QUALQUER posicao da
    imagem — com o item fora de lugar ele encontra o mesmo padrao no lugar novo e devolve score ~1,0.
    Score responde "o gabarito aparece?"; a pergunta do rig e "o item esta onde deveria?". Quem
    responde isso e a distancia, em pixels, entre a posicao encontrada e a esperada, contra a
    tolerancia declarada. O deslocamento entra no registro como metrica da captura.
    """

    def __init__(self, template: np.ndarray, posicao_esperada: tuple[int, int],
                 tolerancia_px: float = 8.0, limite: float = LIMITE_ALINHAMENTO):
        if template.ndim == 3 and template.shape[2] > 1:
            template = _cinza(template)
        self.template = template.reshape(template.shape[0], template.shape[1]).astype(np.float32)
        self.posicao_esperada = (int(posicao_esperada[0]), int(posicao_esperada[1]))
        self.tolerancia_px = float(tolerancia_px)
        self.limite = float(limite)

    def medir_deslocamento(self, imagem: np.ndarray) -> tuple[float, float]:
        """Devolve (deslocamento_px, score). Deslocamento infinito quando o gabarito nao aparece."""
        import cv2

        alvo = _cinza(imagem)
        if alvo.shape[0] < self.template.shape[0] or alvo.shape[1] < self.template.shape[1]:
            raise ErroDeCaptura("template maior que a imagem: o rig mudou de enquadramento")
        mapa = cv2.matchTemplate(alvo, self.template, cv2.TM_CCOEFF_NORMED)
        _, score, _, local = cv2.minMaxLoc(mapa)
        if score < self.limite:
            return float("inf"), float(score)
        dx = local[0] - self.posicao_esperada[0]
        dy = local[1] - self.posicao_esperada[1]
        return float((dx * dx + dy * dy) ** 0.5), float(score)

    def verificar(self, imagem: np.ndarray) -> tuple[Alinhamento, float]:
        deslocamento, _ = self.medir_deslocamento(imagem)
        ok = deslocamento <= self.tolerancia_px
        return (Alinhamento.OK if ok else Alinhamento.FORA_DA_TOLERANCIA), deslocamento


class FonteDeDiretorio:
    """Le `<raiz>/<item_id>/<vista>.jpg`. Bancada e ensaio gravado — nao e camera ao vivo."""

    nome = "diretorio"

    def __init__(self, raiz: str | Path, verificador: VerificadorDeAlinhamento | None = None,
                 extensoes: tuple[str, ...] = (".jpg", ".jpeg", ".png")):
        self.raiz = Path(raiz)
        self.verificador = verificador
        self.extensoes = extensoes

    def capturar(self, item_id: str, trigger_em: datetime) -> ItemCapturado:
        import cv2

        if not item_id.strip():
            raise ErroDeCaptura("item_id vazio")
        pasta = self.raiz / item_id
        if not pasta.is_dir():
            raise ErroDeCaptura(f"sem pasta de captura para o item {item_id!r}: {pasta}")
        vistas: list[VistaCapturada] = []
        for vista in VISTAS_ESPERADAS:
            caminho = self._arquivo(pasta, vista)
            if caminho is None:
                continue
            if self.verificador is None:
                alinhamento = Alinhamento.NAO_VERIFICADO
            else:
                imagem = cv2.imread(str(caminho))
                if imagem is None:
                    raise ErroDeCaptura(f"imagem ilegivel: {caminho}")
                alinhamento, _ = self.verificador.verificar(imagem)
            vistas.append(VistaCapturada(vista=vista, imagem=caminho, capturado_em=trigger_em,
                                         alinhamento=alinhamento))
        if not vistas:
            raise ErroDeCaptura(f"nenhuma vista encontrada para o item {item_id!r}")
        return ItemCapturado(item_id=item_id, trigger_em=trigger_em, vistas=tuple(vistas))

    def _arquivo(self, pasta: Path, vista: Vista) -> Path | None:
        for ext in self.extensoes:
            for nome in (f"{vista.value}{ext}", f"{vista.value}{ext.upper()}"):
                candidato = pasta / nome
                if candidato.is_file():
                    return candidato
        return None


def _cinza(imagem: np.ndarray) -> np.ndarray:
    import cv2

    if imagem.ndim == 2:
        return imagem.astype(np.float32)
    return cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY).astype(np.float32)
