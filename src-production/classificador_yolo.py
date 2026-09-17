"""Classificador da cadeia a partir de um PACOTE de detector (Ultralytics/PyTorch).

Este e o consumidor que faltava. O modelo que a cadeia realmente serve e um detector YOLO treinado
fora de `src-production/`, empacotado com contrato; o unico caminho que existia era o artefato `.npz`
(D-37), que e outra rede. Sem este modulo, o peso do detector nao entrava na decisao.

Regras que a decisao aqui faz valer (sao guarda, nao comentario):

  * o pacote e verificado antes de qualquer inferencia (`pacote_detector.verificar_bundle`) e o
    contrato e validado semanticamente (`preparo_detector.ContratoDePreprocessamento`);
  * as classes do PESO tem de casar com as do contrato: `model.names` divergente e erro, porque a
    ordem do indice e a identidade da classe no `.pt`;
  * o `imgsz` usado no predict e o do contrato, e o limiar tem de existir PARA ESSE `imgsz`;
  * **silencio nunca vira `normal`**: nenhuma caixa acima do limiar -> `inconclusivo`, com motivo;
  * **classe de defeito nao e suprimida por `normal` mais confiante**: se ha caixa de defeito acima do
    limiar dela, a decisao e de defeito, mesmo que uma caixa `normal` tenha confianca maior;
  * a vista `topo` nunca decide (D-23/D-30) e o dominio CORPO nao tem modelo neste pacote: os dois
    devolvem `None`, que o `Decisor` transforma em fallback;
  * loader e import de torch/ultralytics sao tardios: importar este modulo nao carrega peso nenhum.

O que este modulo NAO faz: nao recorta ROI, nao rotaciona e nao redimensiona. O preparo da imagem e
`preparo_detector` (mesma funcao do treino) e o redimensionamento e da biblioteca do detector.
Receber o recorte pronto e o que permite a mesma imagem ser decidida por modelos diferentes.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np

from dominio import Classe, Dominio, Evidencia, Medida, Origem, Papel, Qualidade, Vista
from pacote_detector import ErroDePacote, abrir_pacote, sha256_do_arquivo
from preparo_detector import ErroDePreparo, ContratoDePreprocessamento

#: classes que o detector de tampa pode emitir; o mapa e por NOME, nunca por indice posicional
_NOME_PARA_CLASSE = {
    "normal": Classe.NORMAL,
    "tampa_ausente": Classe.TAMPA_AUSENTE,
    "defeito_tampa": Classe.DEFEITO_TAMPA,
}

#: vistas que este detector pode decidir: o modelo e do lateral. `topo` nunca decide (D-23/D-30).
VISTAS_DECIDIVEIS = (Vista.LATERAL1, Vista.LATERAL2)

#: piso de confianca passado ao predict (o limiar que DECIDE e sempre o calibrado): para o imgsz:
#: alto o bastante para nao gastar tempo com ruido, baixo o bastante para nao descartar caixa. A
#: decisao correspondente fica marcada como provisoria (D-24), nunca como limiar medido.
PISO_DE_CONFIANCA = 0.01


class ErroDeClassificacao(Exception):
    """O pacote/contrato nao permite decidir com honestidade, ou a medida saiu incoerente."""


class ClassificadorDoPacote:
    """Detector YOLO empacotado, atras do protocolo `ClassificadorDeVista` (D-30)."""

    def __init__(self, peso: Path, modelo: dict, contrato: ContratoDePreprocessamento,
                 metadados: dict, *, carregador=None):
        self.peso = Path(peso)
        self.manifesto = dict(modelo)
        self.contrato = contrato
        self.metadados = dict(metadados)
        self._carregador = carregador
        self._modelo = None
        self._validar_semanticamente()

    # ------------------------------------------------------------------ abertura

    @classmethod
    def abrir(cls, diretorio: str | Path, *, carregador=None) -> "ClassificadorDoPacote":
        """Verifica o pacote, valida o contrato e devolve o classificador (sem carregar o peso)."""
        try:
            peso, contrato_caminho, metadados_caminho, manifesto = abrir_pacote(diretorio)
        except ErroDePacote as erro:
            raise ErroDeClassificacao(f"pacote {diretorio} invalido: {erro}") from erro
        try:
            contrato = ContratoDePreprocessamento.abrir(
                contrato_caminho)
        except ErroDePreparo as erro:
            raise ErroDeClassificacao(
                f"contrato de pre-processamento do pacote nao serve: {erro}") from erro
        import json
        metadados = json.loads(Path(metadados_caminho).read_text(encoding="utf-8"))
        return cls(peso, manifesto, contrato, metadados, carregador=carregador)

    def _validar_semanticamente(self) -> None:
        """O que o checksum nao prova: contrato x manifesto x metadados do treino."""
        if self.contrato.classes != tuple(self.manifesto["classes"]):
            raise ErroDeClassificacao(
                f"classes divergentes entre contrato {self.contrato.classes} e manifesto "
                f"{tuple(self.manifesto['classes'])}")
        if int(self.manifesto["imgsz_treino"]) != self.contrato.imgsz_treino:
            raise ErroDeClassificacao(
                f"imgsz divergente entre manifesto {self.manifesto['imgsz_treino']} e contrato "
                f"{self.contrato.imgsz_treino}")
        if self.contrato.imgsz_treino not in [int(v) for v in self.manifesto["imgsz_calibrados"]]:
                raise ErroDeClassificacao(
                    f"imgsz {self.contrato.imgsz_treino} nao esta entre os calibrados do manifesto "
                    f"{self.manifesto['imgsz_calibrados']}: limiar calibrado em outro tamanho nao vale")
        # contrato declarado no manifesto == bytes do contrato no pacote (verificado de novo aqui)
        if sha256_do_arquivo(Path(self.contrato.caminho)) != self.manifesto["preprocessamento_sha256"]:
            raise ErroDeClassificacao("contrato lido nao e o contrato declarado no manifesto")
        if self.contrato.modelo.get("sha256") != self.manifesto["sha256"]:
            raise ErroDeClassificacao(
                "o contrato de pre-processamento foi calibrado para OUTRO peso "
                f"({str(self.contrato.modelo.get('sha256'))[:12]}… x {self.manifesto['sha256'][:12]}…): "
                "ROI, imgsz e limiar nao valem para este pacote")
        if self.manifesto["sha256"] != sha256_do_arquivo(self.peso):
            raise ErroDeClassificacao("peso do pacote nao casa com o sha256 do manifesto")
        # metadados do treino: procedencia do peso, classes e imgsz (o produtor ja confere; o
        # consumidor nao aceita a palavra do produtor, confere de novo)
        if self.metadados.get("peso_sha256") != self.manifesto["sha256"]:
            raise ErroDeClassificacao(
                "metadados do treino declaram outro peso: procedencia do pacote nao fecha")
        if list(self.metadados.get("classes") or []) != list(self.manifesto["classes"]):
            raise ErroDeClassificacao("metadados do treino declaram outras classes")
        args = self.metadados.get("args") or {}
        if int(args.get("imgsz", -1)) != self.contrato.imgsz_treino:
            raise ErroDeClassificacao(
                f"metadados do treino treinaram em imgsz {args.get('imgsz')!r}, contrato diz "
                f"{self.contrato.imgsz_treino}")
        desconhecidas = [c for c in self.contrato.classes if c not in _NOME_PARA_CLASSE]
        if desconhecidas:
            raise ErroDeClassificacao(
                f"classes sem mapeamento para o dominio da tampa: {desconhecidas} "
                f"(conhecidas: {sorted(_NOME_PARA_CLASSE)})")

    # ------------------------------------------------------------------ identificacao

    @property
    def identificacao(self) -> str:
        """O que rodou, sem enfeite; e isto que entra no registro como `metodo`."""
        return (f"pacote:{self.peso.name}|sha256={self.manifesto['sha256'][:12]}"
                f"|imgsz={self.contrato.imgsz_treino}"
                f"|contrato={Path(self.contrato.caminho).name}"
                f"|fingerprint={self.contrato.fingerprint_calculado()[:12]}"
                f"|calibrado={'sim' if self.calibrado else 'nao'}")

    @property
    def calibrado(self) -> bool:
        return self.contrato.calibrado_no_imgsz_de_treino()

    @property
    def limitacoes_declaradas(self) -> tuple[str, ...]:
        return tuple(self.manifesto.get("limitacoes_declaradas") or ())

    # ------------------------------------------------------------------ o contrato

    def _carregar_modelo(self):
        """Carrega o peso na primeira inferencia (import e leitura de peso sao tardios)."""
        if self._modelo is None:
            if self._carregador is not None:
                self._modelo = self._carregador(str(self.peso))
            else:
                from ultralytics import YOLO          # import tardio: sem peso na importacao
                self._modelo = YOLO(str(self.peso))
            nomes = list(getattr(self._modelo, "names", {}).values())
            if sorted(nomes) != sorted(self.contrato.classes):
                raise ErroDeClassificacao(
                    f"classes do peso {sorted(nomes)} nao casam com o contrato "
                    f"{sorted(self.contrato.classes)}: o indice de classe nao e confiavel")
        return self._modelo

    def caixas(self, recorte: np.ndarray) -> list[tuple[Classe, float]]:
        """Caixas do detector no recorte, como `(classe, confianca)`, em ordem de confianca."""
        modelo = self._carregar_modelo()
        resultado = modelo.predict(recorte, imgsz=self.contrato.imgsz_treino,
                                   conf=PISO_DE_CONFIANCA, verbose=False)[0]
        caixas = getattr(resultado, "boxes", None)
        if caixas is None or not len(caixas):
            return []
        nomes = getattr(modelo, "names", {})
        saida: list[tuple[Classe, float]] = []
        for confianca, indice in zip(caixas.conf.cpu().numpy(), caixas.cls.cpu().numpy().astype(int), strict=False):
            nome = str(nomes.get(int(indice), indice))
            classe = _NOME_PARA_CLASSE.get(nome)
            if classe is None:
                raise ErroDeClassificacao(f"peso emitiu classe fora do contrato: {nome!r}")
            saida.append((classe, float(confianca)))
        return sorted(saida, key=lambda par: -par[1])

    def prever(self, recorte, dominio: Dominio, vista: Vista) -> Medida | None:
        """Medida da vista/dominio, ou `None` quando este pacote nao decide aquela vista/dominio."""
        if not isinstance(dominio, Dominio):
            raise ErroDeClassificacao(f"dominio tem de ser dominio.Dominio, recebido {dominio!r}")
        if not isinstance(vista, Vista):
            raise ErroDeClassificacao(f"vista tem de ser dominio.Vista, recebida {vista!r}")
        if dominio is not Dominio.TAMPA:
            return None                       # CORPO nao tem modelo neste pacote: fallback (D-30)
        if vista not in VISTAS_DECIDIVEIS:
            return None                       # topo nunca decide (D-23/D-30)
        if not isinstance(recorte, np.ndarray):
            raise ErroDeClassificacao(
                f"recorte tem de ser a imagem ja recortada (ndarray BGR), recebido "
                f"{type(recorte).__name__}: o preparo da imagem mora em preparo_detector")
        if recorte.ndim != 3 or recorte.shape[2] != 3 or recorte.size == 0:
            raise ErroDeClassificacao(
                f"recorte tem de ser BGR (H, W, 3) nao vazio: shape={getattr(recorte, 'shape', None)}")

        limiares = self.contrato.limiares(self.contrato.imgsz_treino)
        caixas = self.caixas(recorte)
        aceitas = [(classe, conf) for classe, conf in caixas
                   if conf >= float(limiares[classe.value])]
        defeitos = [(classe, conf) for classe, conf in aceitas if classe is not Classe.NORMAL]
        if defeitos:
            classe, confianca = defeitos[0]                  # mais confiavel entre os defeitos
            return self._medida(dominio, vista, classe, confianca, aceitas, limiares, roteou=False)
        normais = [(classe, conf) for classe, conf in aceitas if classe is Classe.NORMAL]
        if normais:
            return self._medida(dominio, vista, Classe.NORMAL, normais[0][1], aceitas, limiares,
                                roteou=False)
        return Medida(vista=vista, dominio=dominio, classe=Classe.INCONCLUSIVO, confianca=0.0,
                      qualidade=Qualidade.INSUFICIENTE,
                      evidencias=self._evidencias(0.0, aceitas, limiares, roteou=True,
                                                  motivo="nenhuma caixa acima do limiar da classe"))

    # ------------------------------------------------------------------ rastro

    def _medida(self, dominio: Dominio, vista: Vista, classe: Classe, confianca: float,
                aceitas: list, limiares: dict, *, roteou: bool) -> Medida:
        return Medida(vista=vista, dominio=dominio, classe=classe, confianca=confianca,
                      evidencias=self._evidencias(confianca, aceitas, limiares, roteou=roteou))

    def _evidencias(self, confianca: float, aceitas: list, limiares: dict, *, roteou: bool,
                    motivo: str | None = None) -> tuple[Evidencia, ...]:
        fonte_do_pacote = f"{self.peso.name}#{self.manifesto['sha256'][:12]}"
        classe_decidida = aceitas[0][0] if aceitas else None
        limiar = limiares.get(classe_decidida.value) if classe_decidida is not None else None
        origem_do_limiar = (f"{Path(self.contrato.caminho).name}"
                            f"#limiares_por_imgsz/{self.contrato.imgsz_treino}/{classe_decidida.value}"
                            if limiar is not None else None)
        evidencias = [
            Evidencia(grandeza="confianca_da_caixa_decidida", valor=confianca, unidade="confianca",
                      origem=Origem.CLASSIFICADOR, papel=Papel.FALLBACK if roteou else Papel.DECIDE,
                      metodo=self.identificacao, fonte=fonte_do_pacote),
            Evidencia(grandeza="limiar_de_confianca_da_classe", valor=limiar, unidade="confianca",
                      origem=Origem.CLASSIFICADOR, papel=Papel.FALLBACK, metodo=self.identificacao,
                      fonte=origem_do_limiar),
            Evidencia(grandeza="caixas_acima_do_limiar", valor=float(len(aceitas)), unidade="contagem",
                      origem=Origem.CLASSIFICADOR, papel=Papel.AUXILIAR, metodo=self.identificacao,
                      fonte=fonte_do_pacote),
        ]
        if motivo is not None:
            evidencias.append(Evidencia(grandeza="motivo_do_inconclusivo", valor=None, unidade="texto",
                                        origem=Origem.CLASSIFICADOR, papel=Papel.FALLBACK,
                                        metodo=motivo, fonte=None))
        for limitacao in self.limitacoes_declaradas:
            # sem `fonte`: e a limitacao que o proprio pacote declara; parametro provisorio, nao
            # grandeza medida (D-24). Se o pacote se declara candidato, o registro diz isso.
            evidencias.append(Evidencia(grandeza="limitacao_declarada_pelo_pacote", valor=None,
                                        unidade="texto", origem=Origem.CLASSIFICADOR,
                                        papel=Papel.FALLBACK, metodo=limitacao, fonte=None))
        return tuple(evidencias)


def mapa_camera_vista(contrato: ContratoDePreprocessamento) -> dict[str, Vista]:
    """Vista declarada por camera, lida do contrato (a associacao nunca e inferida do nome)."""
    return {camera: contrato.vista_da_camera(camera) for camera in contrato.cameras()}


def camera_da_vista(contrato: ContratoDePreprocessamento) -> dict[Vista, str]:
    """Inverso do mapa do contrato; vista repetida em duas cameras e erro, nao 'a primeira vale'."""
    mapa: dict[Vista, str] = {}
    for camera, vista in mapa_camera_vista(contrato).items():
        if vista in mapa:
            raise ErroDeClassificacao(
                f"vista {vista.value} declarada em duas cameras ({mapa[vista]!r} e {camera!r}): "
                f"sem associacao unica, o recorte do item seria ambiguo")
        mapa[vista] = camera
    return mapa


def roi_por_vista(contrato: ContratoDePreprocessamento, mapa: Mapping[str, Vista] | None = None
                  ) -> dict[Vista, dict]:
    """ROI por VISTA derivada do contrato (o rig tem uma camera por vista)."""
    associacao = dict(mapa) if mapa is not None else mapa_camera_vista(contrato)
    por_vista: dict[Vista, dict] = {}
    for camera, vista in associacao.items():
        por_vista[vista] = contrato.roi_da_camera(camera)
    return por_vista
