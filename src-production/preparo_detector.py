"""Pre-processamento do detector: UMA definicao, consumida pelo treino e pela inferencia.

O requisito nao e estetico. Medido em 2026-09-15: o treino recortava 0,573x0,512 da cena e o deploy
usava o quadro inteiro; a mesma rede, os mesmos pesos, 0,17 de F1 macro de diferenca. Duas copias da
regra divergem sempre; uma definicao compartilhada nao pode divergir.

O que este modulo define, e nada mais:

  * `retangulo_de_recorte`  o retangulo INTEIRO (x1, y1, x2, y2) em pixels, a partir da ROI
    normalizada. E a MESMA funcao que o montador de dataset usa: piso em cada componente, recorte
    `[x1:x2, y1:y2]`. Antes o treino usava PIL e a inferencia usava outra formula de arredondamento,
    o que deslocava a caixa e a regiao em 1 px;
  * `orientar`              rotacao por camera, com a CONVENCAO declarada (graus, horario);
  * `recorte_da_vista`      orienta + recorta, devolvendo o recorte BGR e o rastro do que foi feito;
  * `ContratoDePreprocessamento`  leitura e validacao do `preprocessamento.json`.

O `imgsz` NAO e aplicado aqui de proposito: quem redimensiona e a biblioteca do detector
(`predict(imgsz=...)`), igual ao treino (letterbox do Ultralytics). Reescalar antes seria uma segunda
regra de escala, exatamente o defeito que este modulo existe para impedir.

Ambiguidade de orientacao e erro, nunca default. O contrato precisa declarar
`orientacao_entrada`:

    "quadro_ja_orientado"   a fonte entrega o quadro na orientacao do treino; o consumidor NAO
                            rotaciona. Foi o caso do corpus deste projeto: as series do rig ja
                            vinham rotacionadas por camera (usb 90, espcam 180).
    "rotacionar_no_consumo" a fonte entrega o quadro cru; o consumidor aplica `rotacao_graus[camera]`
                            antes de recortar a ROI (que e declarada no espaco JA rotacionado).

Sem essa declaracao o consumo falha, porque adivinhar troca 90 por 0 em silencio e o modelo ve outra
imagem sem que nada no registro diga isso.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from dominio import Vista

#: orientacoes de entrada aceitas; qualquer outro valor e erro declarado
ORIENTACOES = ("quadro_ja_orientado", "rotacionar_no_consumo")

ROTACOES_VALIDAS = (0, 90, 180, 270)

#: campos sem os quais o contrato nao descreve o que treino e inferencia tem de fazer igual
CAMPOS_OBRIGATORIOS = (
    "nome", "versao", "roi_por_camera", "rotacao_graus", "orientacao_entrada", "imgsz_treino",
    "letterbox", "classes", "limiares_por_imgsz", "modelo", "vista_por_camera", "regra_decisao",
    "fingerprint",
)

#: campos que mudam a predicao; o `fingerprint` e o hash canonico deles
CAMPOS_DO_FINGERPRINT = ("roi_por_camera", "rotacao_graus", "orientacao_entrada", "imgsz_treino",
                         "letterbox", "classes", "vista_por_camera", "regra_decisao")


class ErroDePreparo(ValueError):
    """O contrato nao permite preparar a imagem com honestidade (falta, diverge ou e ambiguo)."""


def retangulo_de_recorte(tamanho: tuple[int, int], roi) -> tuple[int, int, int, int]:
    """Retangulo inteiro `(x1, y1, x2, y2)` da ROI normalizada, em pixels.

    Regra unica, replicada pelo montador de dataset: piso independente de `x`, `y`, `w` e `h`
    (`x2 = x1 + floor(w*L)`, nunca `floor((x+w)*L)`). As duas formulas diferem em 1 px conforme a
    largura, e 1 px de deslocamento entre treino e inferencia desloca toda a caixa anotada.
    """
    if not isinstance(tamanho, (tuple, list)) or len(tamanho) != 2:
        raise ErroDePreparo(f"tamanho de imagem invalido: {tamanho!r}")
    largura, altura = (int(v) for v in tamanho)
    if largura <= 0 or altura <= 0:
        raise ErroDePreparo(f"tamanho de imagem nao positivo: {tamanho!r}")
    if not isinstance(roi, dict):
        raise ErroDePreparo(f"roi invalida (esperado mapa x/y/w/h): {roi!r}")
    try:
        x, y, w, h = (float(roi[chave]) for chave in ("x", "y", "w", "h"))
    except (KeyError, TypeError, ValueError) as erro:
        raise ErroDePreparo(f"roi incompleta ou nao numerica: {roi!r} ({erro})") from erro
    if not all(math.isfinite(v) for v in (x, y, w, h)):
        raise ErroDePreparo(f"roi com valor nao finito: {roi!r}")
    if not (0.0 <= x < 1.0 and 0.0 <= y < 1.0 and w > 0.0 and h > 0.0
            and x + w <= 1.0 + 1e-9 and y + h <= 1.0 + 1e-9):
        raise ErroDePreparo(f"roi fora de [0,1] ou degenerada: {roi!r}")
    x1, y1 = int(x * largura), int(y * altura)
    x2, y2 = x1 + int(w * largura), y1 + int(h * altura)
    if x2 > largura or y2 > altura:
        raise ErroDePreparo(f"roi produz retangulo fora do quadro: {(x1, y1, x2, y2)} em {tamanho}")
    if x2 <= x1 or y2 <= y1:
        raise ErroDePreparo(f"roi degenerada em pixels: {(x1, y1, x2, y2)} em {tamanho}")
    return x1, y1, x2, y2


def _validar_frame(frame) -> np.ndarray:
    if not isinstance(frame, np.ndarray):
        raise ErroDePreparo(
            f"quadro tem de ser ndarray BGR, recebido {type(frame).__name__}: a leitura de arquivo "
            f"mora na captura, nao aqui")
    if frame.ndim != 3 or frame.shape[2] != 3 or frame.size == 0:
        raise ErroDePreparo(f"quadro tem de ser (H, W, 3) nao vazio: shape={frame.shape}")
    if frame.dtype != np.uint8:
        raise ErroDePreparo(f"quadro tem de ser uint8 (BGR de 8 bits): dtype={frame.dtype}")
    return frame


def orientar(frame: np.ndarray, graus: int) -> np.ndarray:
    """Aplica rotacao em GRAUS, no sentido HORARIO (convencao declarada do contrato).

    `np.rot90` gira anti-horario para `k` positivo; o mapa abaixo e explicito para ninguem precisar
    refazer essa conta: 90 -> k=-1, 180 -> k=2, 270 -> k=1.
    """
    _validar_frame(frame)
    if graus not in ROTACOES_VALIDAS:
        raise ErroDePreparo(f"rotacao invalida: {graus!r} (validas: {ROTACOES_VALIDAS})")
    if graus == 0:
        return frame
    return np.ascontiguousarray(np.rot90(frame, k={90: -1, 180: 2, 270: 1}[graus]))


def recorte_normalizado(frame: np.ndarray, roi) -> np.ndarray:
    """Recorta a ROI normalizada da imagem, sem redimensionar e sem inventar borda."""
    _validar_frame(frame)
    altura, largura = frame.shape[:2]
    x1, y1, x2, y2 = retangulo_de_recorte((largura, altura), roi)
    recorte = frame[y1:y2, x1:x2]
    if recorte.size == 0:
        raise ErroDePreparo(f"recorte vazio com roi={roi!r} em {(largura, altura)}")
    return np.ascontiguousarray(recorte)


def ler_bgr(caminho) -> np.ndarray:
    """Le a imagem em BGR uint8; ilegivel e erro declarado, nunca imagem vazia silenciosa."""
    import cv2

    quadro = cv2.imread(str(caminho))
    if quadro is None:
        raise ErroDePreparo(f"imagem ilegivel: {caminho}")
    return _validar_frame(quadro)


@dataclass(frozen=True)
class Preparo:
    """O recorte pronto para o detector e o rastro de como ele foi obtido."""

    recorte: np.ndarray
    camera: str
    rotacao_aplicada: int
    retangulo: tuple[int, int, int, int]


class ContratoDePreprocessamento:
    """`preprocessamento.json` lido, validado e consultavel por camera.

    A validacao aqui e semantica: os hashes do pacote (`pacote_detector.verificar_bundle`) provam que
    os bytes nao mudaram; so esta classe diz se os campos descrevem uma preparacao executavel.
    """

    def __init__(self, dados: dict, caminho: str):
        self._dados = dados
        self.caminho = caminho
        self._validar()

    # ------------------------------------------------------------------ abertura

    @property
    def classes(self) -> tuple[str, ...]:
        return tuple(self._dados["classes"])

    @property
    def imgsz_treino(self) -> int:
        return int(self._dados["imgsz_treino"])

    @property
    def modelo(self) -> dict:
        return dict(self._dados["modelo"])

    @property
    def versao(self) -> int:
        return int(self._dados["versao"])

    @property
    def nome(self) -> str:
        return str(self._dados["nome"])

    @property
    def orientacao_entrada(self) -> str:
        return str(self._dados["orientacao_entrada"])

    @classmethod
    def abrir(cls, caminho: str | Path):
        caminho = Path(caminho)
        if not caminho.is_file():
            raise ErroDePreparo(f"contrato de pre-processamento nao existe: {caminho}")
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as erro:
            raise ErroDePreparo(f"contrato ilegivel em {caminho}: {erro}") from erro
        if not isinstance(dados, dict):
            raise ErroDePreparo(f"contrato tem de ser objeto JSON: {caminho}")
        return cls(dados, str(caminho))

    # ------------------------------------------------------------------ consulta

    def cameras(self) -> tuple[str, ...]:
        return tuple(sorted(self._dados["roi_por_camera"]))

    def roi_da_camera(self, camera: str) -> dict:
        try:
            return dict(self._dados["roi_por_camera"][camera])
        except KeyError as erro:
            raise ErroDePreparo(
                f"camera nao declarada no contrato: {camera!r} (declaradas: {self.cameras()})"
            ) from erro

    def rotacao_da_camera(self, camera: str) -> int:
        try:
            return int(self._dados["rotacao_graus"][camera])
        except KeyError as erro:
            raise ErroDePreparo(f"camera sem rotacao declarada: {camera!r}") from erro

    def vista_da_camera(self, camera: str) -> Vista:
        try:
            return Vista(str(self._dados["vista_por_camera"][camera]))
        except KeyError as erro:
            raise ErroDePreparo(f"camera sem vista declarada: {camera!r}") from erro

    def limiares(self, imgsz: int) -> dict[str, float]:
        """Limiar por classe no `imgsz` pedido; ausente/nao calibrado e erro, nao default."""
        tabela = self._dados["limiares_por_imgsz"]
        entrada = tabela.get(str(int(imgsz)))
        if entrada is None:
            raise ErroDePreparo(
                f"imgsz {imgsz} nao esta no contrato (declarados: {sorted(tabela)}); um limiar "
                f"calibrado em outro tamanho nao vale aqui")
        if not entrada.get("calibrado"):
                raise ErroDePreparo(
                    f"imgsz {imgsz} marcado como NAO calibrado no contrato: recalibrar na validacao "
                    f"antes de decidir com ele (contrato sem calibracao nao abre)")
        return {classe: entrada[classe] for classe in self.classes}

    def calibrado_no_imgsz_de_treino(self) -> bool:
        """True quando o imgsz de treino tem limiar calibrado com fonte declarada."""
        entrada = self._dados["limiares_por_imgsz"].get(str(self.imgsz_treino)) or {}
        return bool(entrada.get("calibrado"))

    def fingerprint_calculado(self) -> str:
        canonico = {campo: self._dados[campo] for campo in CAMPOS_DO_FINGERPRINT}
        canonico["modelo_sha256"] = self._dados["modelo"]["sha256"]
        return hashlib.sha256(
            json.dumps(canonico, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    # ------------------------------------------------------------------ preparo

    def preparar(self, frame: np.ndarray, camera: str) -> Preparo:
        """Orienta (conforme declarado) e recorta a ROI da camera; devolve o rastro do que fez."""
        _validar_frame(frame)
        rotacao = self.rotacao_da_camera(camera)
        graus = rotacao if self.orientacao_entrada == "rotacionar_no_consumo" else 0
        orientado = orientar(frame, graus)
        roi = self.roi_da_camera(camera)
        altura, largura = orientado.shape[:2]
        retangulo = retangulo_de_recorte((largura, altura), roi)
        recorte = recorte_normalizado(orientado, roi)
        return Preparo(recorte=recorte, camera=camera, rotacao_aplicada=graus, retangulo=retangulo)

    # ------------------------------------------------------------------ validacao

    def _validar(self) -> None:
        dados = self._dados
        faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in dados]
        if faltando:
            raise ErroDePreparo(f"contrato sem os campos {faltando}: tem {sorted(dados)}")
        if dados["orientacao_entrada"] not in ORIENTACOES:
            raise ErroDePreparo(
                f"orientacao_entrada invalida: {dados['orientacao_entrada']!r} "
                f"(validas: {ORIENTACOES}); orientacao ambigua nao pode virar default")
        rois, rotacoes = dados["roi_por_camera"], dados["rotacao_graus"]
        vistas = dados["vista_por_camera"]
        for nome, valor in (("roi_por_camera", rois), ("rotacao_graus", rotacoes),
                            ("vista_por_camera", vistas)):
            if not isinstance(valor, dict) or not valor:
                raise ErroDePreparo(f"{nome} tem de ser mapa nao vazio")
        if not (set(rois) == set(rotacoes) == set(vistas)):
            raise ErroDePreparo(
                f"cameras divergentes entre roi_por_camera{ sorted(rois) }, "
                f"rotacao_graus{ sorted(rotacoes) } e vista_por_camera{ sorted(vistas) }")
        for camera in rois:
            if not isinstance(camera, str) or not camera.strip():
                raise ErroDePreparo(f"nome de camera invalido: {camera!r}")
            retangulo_de_recorte((1000, 1000), rois[camera])
            if int(rotacoes[camera]) not in ROTACOES_VALIDAS:
                raise ErroDePreparo(f"rotacao de {camera!r} invalida: {rotacoes[camera]!r}")
            try:
                Vista(str(vistas[camera]))
            except ValueError as erro:
                raise ErroDePreparo(
                    f"vista invalida para {camera!r}: {vistas[camera]!r} "
                    f"(validas: {[v.value for v in Vista]})") from erro
        classes = dados["classes"]
        if (not isinstance(classes, list) or not classes
                or not all(isinstance(c, str) and c.strip() for c in classes)
                or len(set(classes)) != len(classes)):
            raise ErroDePreparo(f"classes invalidas: {classes!r}")
        if not isinstance(dados["letterbox"], bool) or dados["letterbox"] is not True:
            raise ErroDePreparo("letterbox tem de ser true: e o que o treino usa")
        imgsz = dados["imgsz_treino"]
        if not isinstance(imgsz, int) or isinstance(imgsz, bool) or imgsz <= 0:
            raise ErroDePreparo(f"imgsz_treino invalido: {imgsz!r}")
        tabela = dados["limiares_por_imgsz"]
        if not isinstance(tabela, dict) or str(imgsz) not in tabela:
            raise ErroDePreparo(f"limiares_por_imgsz nao cobre o imgsz de treino {imgsz}")
        for chave, entrada in tabela.items():
            if not isinstance(entrada, dict):
                raise ErroDePreparo(f"entrada de limiares invalida em {chave!r}")
            calibrado = entrada.get("calibrado")
            if not isinstance(calibrado, bool):
                raise ErroDePreparo(f"calibrado ausente/nao booleano em imgsz {chave}")
            if calibrado:
                if not isinstance(entrada.get("fonte"), str) or not entrada["fonte"].strip():
                    raise ErroDePreparo(
                        f"limiares de imgsz {chave} ditos calibrados sem 'fonte': limiar sem fonte "
                        f"e provisorio (D-24)")
                for classe in classes:
                    valor = entrada.get(classe)
                    if not isinstance(valor, (int, float)) or isinstance(valor, bool) \
                            or not math.isfinite(float(valor)) or not 0.0 <= float(valor) <= 1.0:
                        raise ErroDePreparo(f"limiar invalido de {classe!r} em imgsz {chave}: {valor!r}")
        if not self.calibrado_no_imgsz_de_treino():
            raise ErroDePreparo(
                f"o imgsz de treino ({dados['imgsz_treino']}) nao esta calibrado no contrato: "
                f"decidir com limiar de outro tamanho nao vale; recalibre na validacao "
                f"(`treino/calibra_limiar_val.py`) ")
        proprio = self.fingerprint_calculado()
        declarado = dados["fingerprint"]
        if not isinstance(declarado, str) or declarado != proprio:
            raise ErroDePreparo(
                f"fingerprint do contrato nao casa: declarado {declarado!r}, calculado {proprio[:16]}…; "
                f"o arquivo foi editado a mao ou os campos de predicao mudaram")
