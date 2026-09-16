"""Captura: monta as vistas do MESMO item em um `ItemCapturado`.

O que este modulo faz valer:
  - tres vistas por item (RF-01/RF-01.2): `topo`, `lateral1`, `lateral2`;
  - o `item_id` vem do gatilho: captura sem identidade nao existe (levanta `ErroDeCaptura`);
  - **janela temporal** (RF-01.2): cada vista tem a sua hora REAL de captura (mtime do arquivo, no
    source de bancada) e so entra em `vistas_utilizaveis` se estiver dentro da janela declarada do
    rig. Vista fora da janela e identificada como faltante, como manda o contrato da interface
    (`docs/requisitos/03-dados-interfaces.md:68-69`), e a divergencia de timestamp e reportada para o
    registro virar `timestamp_divergente` (`DAT-03:24`);
  - **fail-closed nas duas verificacoes**: sem janela declarada a associacao temporal nao esta
    verificada, e vista nao verificada NAO e utilizavel; igual ao alinhamento. Nada e aprovado por
    omissao (D-04);
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
MOTIVO_FORA_DA_JANELA = "fora_da_janela"
MOTIVO_JANELA_NAO_DECLARADA = "janela_nao_declarada"
MOTIVO_DUPLICADA = "vista_duplicada"


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
    #: True = dentro da janela declarada; False = fora dela; None = NAO VERIFICADO. O default e None
    #: de proposito: item montado a mao nao pode afirmar "na janela" sem que ninguem tenha medido.
    no_janela: bool | None = None
    motivo_da_janela: str | None = MOTIVO_JANELA_NAO_DECLARADA
    #: duas evidencias para a mesma vista, ou a mesma imagem em duas vistas: ambigua ou falsa
    #: concordancia entre as laterais. Descartada como evidencia (RF-01.2).
    duplicada: bool = False

    def __post_init__(self) -> None:
        if self.capturado_em.tzinfo is None:
            raise ErroDeCaptura("captura sem fuso horario nao e rastreavel")

    @property
    def utilizavel(self) -> bool:
        return (
            self.alinhamento is Alinhamento.OK
            and self.no_janela is True
            and not self.duplicada
        )


@dataclass(frozen=True)
class ItemCapturado:
    item_id: str
    trigger_em: datetime
    vistas: tuple[VistaCapturada, ...]

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ErroDeCaptura(
                "item sem identificador nao existe: o item_id vem do gatilho"
            )
        if self.trigger_em.tzinfo is None:
            raise ErroDeCaptura("trigger sem fuso horario nao e rastreavel")
        vistas = [v.vista for v in self.vistas]
        if len(set(vistas)) != len(vistas):
            raise ErroDeCaptura(f"vista repetida no mesmo item: {vistas}")

    @property
    def vistas_utilizaveis(self) -> tuple[VistaCapturada, ...]:
        """Só o que passou no alinhamento E esta dentro da janela. Fail-closed por construcao."""
        return tuple(v for v in self.vistas if v.utilizavel)

    @property
    def fora_da_janela(self) -> tuple[VistaCapturada, ...]:
        """Capturadas, mas fora da janela: o registro marca o item como `timestamp_divergente`."""
        return tuple(v for v in self.vistas if v.no_janela is False)

    @property
    def duplicadas(self) -> tuple[VistaCapturada, ...]:
        """Evidencia descartada por duplicacao; registrada, nunca silenciada."""
        return tuple(v for v in self.vistas if v.duplicada)

    @property
    def nao_verificadas(self) -> tuple[VistaCapturada, ...]:
        """Janela nunca medida para estas vistas: nao entram como evidencia, e o motivo e declarado."""
        return tuple(v for v in self.vistas if v.no_janela is None)

    @property
    def faltantes(self) -> tuple[Vista, ...]:
        """Vistas que nao entram como evidencia: nao capturadas OU fora da janela."""
        presentes = {v.vista for v in self.vistas if v.no_janela is True}
        return tuple(v for v in VISTAS_ESPERADAS if v not in presentes)


class VerificadorDeAlinhamento(Protocol):
    """Diz se o item esta na posicao de captura. Nunca decide a classe do defeito."""

    def verificar(self, imagem: np.ndarray) -> tuple[Alinhamento, float]: ...


class VerificadorPorTemplate:
    """Localiza o gabarito por NCC e julga o **deslocamento** contra a posicao de referencia.

    Por que deslocamento e nao o score: o template matching acha o padrao em QUALQUER posicao da
    imagem; com o item fora de lugar ele encontra o mesmo padrao no lugar novo e devolve score ~1,0.
    Score responde "o gabarito aparece?"; a pergunta do rig e "o item esta onde deveria?". Quem
    responde isso e a distancia, em pixels, entre a posicao encontrada e a esperada, contra a
    tolerancia declarada. O deslocamento entra no registro como metrica da captura.
    """

    def __init__(
        self,
        template: np.ndarray,
        posicao_esperada: tuple[int, int],
        tolerancia_px: float = 8.0,
        limite: float = LIMITE_ALINHAMENTO,
    ):
        if template.ndim == 3 and template.shape[2] > 1:
            template = _cinza(template)
        self.template = template.reshape(template.shape[0], template.shape[1]).astype(
            np.float32
        )
        self.posicao_esperada = (int(posicao_esperada[0]), int(posicao_esperada[1]))
        self.tolerancia_px = float(tolerancia_px)
        self.limite = float(limite)

    def medir_deslocamento(self, imagem: np.ndarray) -> tuple[float, float]:
        """Devolve (deslocamento_px, score). Deslocamento infinito quando o gabarito nao aparece."""
        import cv2

        alvo = _cinza(imagem)
        if (
            alvo.shape[0] < self.template.shape[0]
            or alvo.shape[1] < self.template.shape[1]
        ):
            raise ErroDeCaptura(
                "template maior que a imagem: o rig mudou de enquadramento"
            )
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
    """Le `<raiz>/<item_id>/<vista>.jpg`. Bancada e ensaio gravado; nao e camera ao vivo.

    `janela_s` e a janela temporal declarada do rig: vista capturada fora dela nao entra como
    evidencia. Sem `janela_s`, a associacao temporal nao esta verificada e o item fica inconclusivo;
    o rig precisa DECLARAR a janela, senao o numero nao tem significado.
    """

    nome = "diretorio"

    def __init__(
        self,
        raiz: str | Path,
        verificador: VerificadorDeAlinhamento | None = None,
        janela_s: float | None = None,
        extensoes: tuple[str, ...] = (".jpg", ".jpeg", ".png"),
    ):
        self.raiz = Path(raiz)
        self.verificador = verificador
        self.janela_s = janela_s
        self.extensoes = extensoes

    def capturar(self, item_id: str, trigger_em: datetime) -> ItemCapturado:
        import cv2

        if not item_id.strip():
            raise ErroDeCaptura("item_id vazio")
        pasta = self.raiz / item_id
        if not pasta.is_dir():
            raise ErroDeCaptura(
                f"sem pasta de captura para o item {item_id!r}: {pasta}"
            )
        vistas: list[VistaCapturada] = []
        for vista in VISTAS_ESPERADAS:
            candidatos = self._candidatos(pasta, vista)
            if not candidatos:
                continue
            caminho = candidatos[0]
            capturado_em = datetime.fromtimestamp(caminho.stat().st_mtime).astimezone()
            no_janela, motivo = self._na_janela(capturado_em, trigger_em)
            if self.verificador is None:
                alinhamento = Alinhamento.NAO_VERIFICADO
            else:
                imagem = cv2.imread(str(caminho))
                if imagem is None:
                    raise ErroDeCaptura(f"imagem ilegivel: {caminho}")
                alinhamento, _ = self.verificador.verificar(imagem)
            vistas.append(
                VistaCapturada(
                    vista=vista,
                    imagem=caminho,
                    capturado_em=capturado_em,
                    alinhamento=alinhamento,
                    no_janela=no_janela,
                    motivo_da_janela=motivo,
                    duplicada=len(candidatos) > 1,
                )
            )
        if not vistas:
            raise ErroDeCaptura(f"nenhuma vista encontrada para o item {item_id!r}")
        return ItemCapturado(
            item_id=item_id,
            trigger_em=trigger_em,
            vistas=self._marcar_conteudo_repetido(tuple(vistas)),
        )

    def _na_janela(
        self, capturado_em: datetime, trigger_em: datetime
    ) -> tuple[bool | None, str | None]:
        """None = nao verificado (janela nao declarada). False = medido e fora. Sao coisas distintas:
        confundir as duas faria a ausencia de declaracao aparecer como divergencia de timestamp."""
        if self.janela_s is None:
            return None, MOTIVO_JANELA_NAO_DECLARADA
        atraso = abs((capturado_em - trigger_em).total_seconds())
        return (atraso <= self.janela_s), (
            None if atraso <= self.janela_s else MOTIVO_FORA_DA_JANELA
        )

    def _candidatos(self, pasta: Path, vista: Vista) -> list[Path]:
        """Todos os arquivos que respondem por esta vista. Mais de um = captura ambigua."""
        achados: list[Path] = []
        for ext in self.extensoes:
            for nome in (f"{vista.value}{ext}", f"{vista.value}{ext.upper()}"):
                candidato = pasta / nome
                if candidato.is_file() and candidato not in achados:
                    achados.append(candidato)
        return sorted(achados)

    def _marcar_conteudo_repetido(
        self, vistas: tuple[VistaCapturada, ...]
    ) -> tuple[VistaCapturada, ...]:
        """Mesma imagem em duas vistas = concordancia falsa entre as laterais. Marca as duas."""
        import hashlib

        por_hash: dict[str, list[Vista]] = {}
        for v in vistas:
            digest = hashlib.sha256(v.imagem.read_bytes()).hexdigest()
            por_hash.setdefault(digest, []).append(v.vista)
        repetidas = {
            vista
            for vistas_mesmas in por_hash.values()
            if len(vistas_mesmas) > 1
            for vista in vistas_mesmas
        }
        if not repetidas:
            return vistas
        return tuple(
            VistaCapturada(
                vista=v.vista,
                imagem=v.imagem,
                capturado_em=v.capturado_em,
                alinhamento=v.alinhamento,
                no_janela=v.no_janela,
                motivo_da_janela=v.motivo_da_janela,
                duplicada=True if v.vista in repetidas else v.duplicada,
            )
            for v in vistas
        )


def _cinza(imagem: np.ndarray) -> np.ndarray:
    import cv2

    if imagem.ndim == 2:
        return imagem.astype(np.float32)
    return cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY).astype(np.float32)
