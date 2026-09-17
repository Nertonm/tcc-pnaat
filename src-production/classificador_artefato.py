"""Classificador de vista que REPRODUZ o artefato medido; nao treina, nao inventa vintage.

Artefato: `dataset/modelo-inferencia.npz` + `.json`. A receita abaixo foi portada de
`src-production/treino/compara_extratores.py` (produtor versionado); o consumidor original
(`servico_inferencia3.py`) nao e versionado. Os numeros conferem entre produtor e este modulo:

    BGR -> RGB -> Resize(size) -> ToTensor -> Normalize(ImageNet)     [contrato de treino]
    embedding do extrator congelado (declarado em `config_extrator` no json)
    z = (e - mu0) @ P                                                 [PCA256 fit no train]
    z = (z - mu_fonte) / sd_fonte                                     [padronizacao por fonte]
    prob = softmax(coef @ z + intercept)                              [logreg]
    classe = classes[argmax]; conf < limiar -> INCONCLUSIVO (D-26)

O que este modulo NAO afrouxa:

  * vintage, extrator, limiar, avaliacao e aviso vem do **json do artefato**, nunca de constante no
    codigo: um numero sem procedencia nao entra na cadeia;
  * json sem `vintage`/`extrator`/`limiar_abstencao`, ou npz sem as chaves da receita, e ERRO; nao
    existe classificador anonimo;
  * fonte sem estatistica no artefato e ERRO: padronizar com a fonte errada muda a escala do vetor
    sem avisar em lugar nenhum (o proprio json avisa: "camera nova = recalibrar");
  * classe prevista fora do vocabulario do dominio e ERRO (D-28), nunca coacao para `normal`;
  * dominio CORPO devolve `None` declarado: nao existe modelo do corpo, e `None` diz isso;
  * a limitacao que o artefato declara sobre si mesmo (`aviso`) viaja junto na `Medida`, como
    evidencia sem fonte; para a cadeia nao registrar mais do que o artefato assina.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from classificador import ErroDeClassificacao, _classe_da_tampa
from dominio import Classe, Dominio, Evidencia, Medida, Origem, Papel, Qualidade, Vista

#: raiz do clone (este arquivo mora em src-production/)
RAIZ_DO_REPO = Path(__file__).resolve().parent.parent
ARTEFATO_PADRAO = RAIZ_DO_REPO / "dataset" / "modelo-inferencia.npz"

#: a camera da bancada. O json avisa: "Camera nova = recalibrar."
FONTE_PADRAO = "nosso"

#: chaves da receita que o npz tem de ter (as de fonte sao conferidas a parte, por nome)
CHAVES_DA_RECEITA = ("mu0", "P", "classes", "coef", "intercept")

MEDIA_DA_IMAGENET = (0.485, 0.456, 0.406)
DESVIO_DA_IMAGENET = (0.229, 0.224, 0.225)

_EMBUTIDORES: dict[str, Callable[[np.ndarray], np.ndarray]] = {}


@dataclass(frozen=True)
class Procedencia:
    """Tudo que o artefato declara sobre si mesmo, em um lugar so (D-24: sem numero sem fonte)."""

    caminho: str
    sha256: str
    meta_caminho: str
    vintage: str
    extrator: str
    config_extrator: Mapping[str, Any]
    limiar_de_abstencao: float
    fonte_das_estatisticas: str
    classes: tuple[str, ...]
    avaliacao: Mapping[str, Any]
    aviso: str
    treino: int | None

    def linha(self) -> str:
        """Uma linha para o log/registro: o que rodou e o que o artefato admite sobre si."""
        partes = [
            f"artefato={Path(self.caminho).name}",
            f"sha256={self.sha256[:12]}",
            f"vintage={self.vintage!r}",
            f"extrator={self.extrator}",
            f"fonte={self.fonte_das_estatisticas}",
            f"limiar={self.limiar_de_abstencao}",
            f"classes={list(self.classes)}",
        ]
        if self.aviso:
            partes.append(f"aviso={self.aviso!r}")
        return " | ".join(partes)


def _sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def construir_embutidor(
    config: Mapping[str, Any],
) -> Callable[[np.ndarray], np.ndarray]:
    """Embutidor (BGR ndarray -> embedding) do extrator declarado em `config_extrator`."""
    tipo = str(config.get("tipo", "")).lower()
    if tipo not in {"hub", "torchvision"}:
        raise ErroDeClassificacao(
            f"config_extrator.tipo desconhecido: {config.get('tipo')!r}; só 'hub' e 'torchvision' "
            f"(config recebido: {dict(config)!r})"
        )
    if tipo == "hub" and not config.get("repo"):
        raise ErroDeClassificacao(
            f"config_extrator tipo 'hub' sem 'repo': {dict(config)!r}"
        )
    if tipo == "torchvision" and not config.get("fn"):
        raise ErroDeClassificacao(
            f"config_extrator tipo 'torchvision' sem 'fn': {dict(config)!r}"
        )

    chave = json.dumps(dict(config), sort_keys=True)
    if chave in _EMBUTIDORES:
        return _EMBUTIDORES[chave]

    lado = int(config.get("size", 224))

    def carregar():  # pragma: no cover - exercitado no canario com torch real
        import torch
        import torchvision

        if tipo == "hub":
            modelo = torch.hub.load(
                config["repo"], config["fn"], pretrained=True, trust_repo=True
            )
        else:
            fabrica = getattr(torchvision.models, str(config["fn"]), None)
            if fabrica is None:
                raise ErroDeClassificacao(
                    f"torchvision nao tem o modelo {config['fn']!r}"
                )
            pesos = getattr(
                torchvision.models,
                f"{str(config['fn']).title().replace('_', '')}_Weights",
                None,
            )
            pesos = (
                getattr(pesos, str(config["pesos"]))
                if pesos and config.get("pesos")
                else None
            )
            modelo = fabrica(weights=pesos)
            corta = str(config.get("corta") or "classifier")
            if corta and hasattr(modelo, corta):
                setattr(modelo, corta, torch.nn.Identity())
        modelo.eval()
        return modelo

    def embutir(recorte_bgr: np.ndarray) -> np.ndarray:  # pragma: no cover - canario
        import cv2
        import torch
        from PIL import Image
        from torchvision import transforms

        estado = _EMBUTIDORES.get(f"modelo::{chave}")
        if estado is None:
            modelo = carregar()
            dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
            modelo = modelo.to(dispositivo)
            estado = (
                modelo,
                dispositivo,
                transforms.Compose(
                    [
                        transforms.Resize((lado, lado)),
                        transforms.ToTensor(),
                        transforms.Normalize(
                            mean=list(MEDIA_DA_IMAGENET), std=list(DESVIO_DA_IMAGENET)
                        ),
                    ]
                ),
            )
            _EMBUTIDORES[f"modelo::{chave}"] = estado
        modelo, dispositivo, transformada = estado

        # o treino consumiu JPEG RGB (`Image.open(...).convert("RGB")`): a mesma ordem de canais.
        rgb = cv2.cvtColor(np.ascontiguousarray(recorte_bgr), cv2.COLOR_BGR2RGB)
        tensor = transformada(Image.fromarray(rgb)).unsqueeze(0).to(dispositivo)
        with torch.no_grad():
            saida = modelo(tensor)
        if isinstance(saida, dict):  # dinov2 devolve dict: o token CLS
            saida = saida.get("x_norm_clstoken") or next(iter(saida.values()), None)
            if saida is None:
                raise ErroDeClassificacao("modelo devolveu dicionario vazio")
        return np.asarray(saida.flatten(1).cpu().numpy()[0], dtype=np.float64)

    _EMBUTIDORES[chave] = embutir
    return embutir


class ClassificadorDoArtefato:
    """`ClassificadorDeVista` sobre o artefato congelado (implementa o mesmo contrato da cadeia)."""

    def __init__(
        self,
        *,
        dados: Mapping[str, np.ndarray],
        procedencia: Procedencia,
        embutidor: Callable[[np.ndarray], np.ndarray],
        limiar_de_confianca: float | None = None,
    ) -> None:
        self._mu0 = np.asarray(dados["mu0"], dtype=np.float64).reshape(-1)
        self._P = np.asarray(dados["P"], dtype=np.float64)
        self._coef = np.asarray(dados["coef"], dtype=np.float64)
        self._intercepto = np.asarray(dados["intercept"], dtype=np.float64).reshape(-1)
        self._nomes = tuple(str(n) for n in dados["classes"])
        self._media_da_fonte = np.asarray(
            dados[f"mu_{procedencia.fonte_das_estatisticas}"], dtype=np.float64
        ).reshape(-1)
        self._desvio_da_fonte = np.asarray(
            dados[f"sd_{procedencia.fonte_das_estatisticas}"], dtype=np.float64
        ).reshape(-1)
        self._embutidor = embutidor
        self._limiar_de_confianca = float(
            procedencia.limiar_de_abstencao
            if limiar_de_confianca is None
            else limiar_de_confianca
        )
        if not 0.0 <= self._limiar_de_confianca <= 1.0:
            raise ErroDeClassificacao(
                f"limiar de confianca fora de [0,1]: {self._limiar_de_confianca}"
            )
        self._classes = tuple(
            _classe_da_tampa(nome) for nome in self._nomes
        )  # D-28: recusa fora
        self.procedencia = procedencia

    # ------------------------------------------------------------------ abertura

    @property
    def identificacao(self) -> str:
        """O que rodou, sem enfeite: e isto que entra no registro como `metodo`."""
        return (
            f"artefato:{self.procedencia.vintage}|extrator={self.procedencia.extrator}"
            f"|pca={self._P.shape[1]}|fonte={self.procedencia.fonte_das_estatisticas}"
            f"|limiar={self._limiar_de_confianca:g}|sha256={self.procedencia.sha256[:12]}"
        )

    @property
    def limiar_de_confianca(self) -> float:
        return self._limiar_de_confianca

    @classmethod
    def abrir(
        cls,
        caminho: str | Path = ARTEFATO_PADRAO,
        *,
        fonte: str = FONTE_PADRAO,
        limiar_de_confianca: float | None = None,
        embutidor: Callable[[np.ndarray], np.ndarray] | None = None,
        meta_caminho: str | Path | None = None,
    ) -> ClassificadorDoArtefato:
        """Le o artefato e o json. Qualquer buraco na receita ou no metadado e erro declarado."""
        caminho = Path(caminho)
        meta = (
            Path(meta_caminho)
            if meta_caminho is not None
            else caminho.with_suffix(".json")
        )
        if not caminho.is_file():
            raise ErroDeClassificacao(f"artefato nao existe: {caminho}")
        if not meta.is_file():
            raise ErroDeClassificacao(
                f"artefato sem metadado: {meta}; sem o json nao ha vintage, extrator nem limiar; "
                f"um artefato anonimo nao entra na cadeia"
            )

        try:
            declarado = json.loads(meta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as erro:
            raise ErroDeClassificacao(f"metadado ilegivel em {meta}: {erro}") from erro

        faltando = [
            c for c in ("vintage", "extrator", "limiar_abstencao") if c not in declarado
        ]
        if faltando:
            raise ErroDeClassificacao(
                f"metadado sem {faltando} em {meta}: {sorted(declarado)}"
            )

        with np.load(caminho, allow_pickle=False) as arquivo:
            dados = {chave: arquivo[chave] for chave in arquivo.files}

        ausentes = [chave for chave in CHAVES_DA_RECEITA if chave not in dados]
        if ausentes:
            raise ErroDeClassificacao(
                f"artefato {caminho.name} sem as chaves da receita {ausentes}; tem {sorted(dados)}"
            )
        for chave in (f"mu_{fonte}", f"sd_{fonte}"):
            if chave not in dados:
                fontes = sorted(
                    c.removeprefix("mu_") for c in dados if c.startswith("mu_")
                )
                raise ErroDeClassificacao(
                    f"artefato nao tem estatistica da fonte {fonte!r} ({chave}): padronizar com a fonte "
                    f"errada muda a escala do vetor sem avisar. Fontes no artefato: {fontes}"
                )

        mu0 = np.asarray(dados["mu0"]).reshape(-1)
        P = np.asarray(dados["P"])
        coef = np.asarray(dados["coef"])
        intercepto = np.asarray(dados["intercept"]).reshape(-1)
        classes = tuple(str(n) for n in dados["classes"])
        problemas = []
        if P.ndim != 2 or P.shape[0] != mu0.shape[0]:
            problemas.append(f"P{P.shape} nao projeta mu0{mu0.shape}")
        if coef.ndim != 2 or P.ndim == 2 and coef.shape[1] != P.shape[1]:
            problemas.append(f"coef{coef.shape} nao casa com P{P.shape}")
        if coef.ndim == 2 and coef.shape[0] != len(classes):
            problemas.append(
                f"{len(classes)} classes para {coef.shape[0]} linhas de coef"
            )
        if intercepto.shape[0] != len(classes):
            problemas.append(f"intercept{intercepto.shape} para {len(classes)} classes")
        for chave in (f"mu_{fonte}", f"sd_{fonte}"):
            if np.asarray(dados[chave]).reshape(-1).shape[0] != (
                P.shape[1] if P.ndim == 2 else -1
            ):
                problemas.append(f"{chave} nao tem a dimensao do PCA ({P.shape[1]})")
        if np.any(np.asarray(dados[f"sd_{fonte}"]) == 0):
            problemas.append("desvio da fonte com zero: divisao impossivel")
        if problemas:
            raise ErroDeClassificacao(
                f"artefato {caminho.name} inconsistente: " + "; ".join(problemas)
            )

        limiar = float(declarado["limiar_abstencao"])
        if not 0.0 <= limiar <= 1.0:
            raise ErroDeClassificacao(
                f"limiar_abstencao do metadado fora de [0,1]: {limiar}"
            )

        procedencia = Procedencia(
            caminho=str(caminho),
            sha256=_sha256(caminho),
            meta_caminho=str(meta),
            vintage=str(declarado["vintage"]),
            extrator=str(declarado["extrator"]),
            config_extrator=declarado.get("config_extrator") or {},
            limiar_de_abstencao=limiar,
            fonte_das_estatisticas=fonte,
            classes=classes,
            avaliacao=declarado.get("avaliacao") or {},
            aviso=str(declarado.get("aviso") or ""),
            treino=declarado.get("treino"),
        )

        if embutidor is None:
            embutidor = construir_embutidor(procedencia.config_extrator)

        return cls(
            dados=dados,
            procedencia=procedencia,
            embutidor=embutidor,
            limiar_de_confianca=limiar_de_confianca,
        )

    # ------------------------------------------------------------------ o contrato

    def probabilidades(self, embedding: np.ndarray) -> np.ndarray:
        """A matematica do artefato, sem torch: PCA -> padronizacao por fonte -> softmax da logreg."""
        e = np.asarray(embedding, dtype=np.float64).reshape(-1)
        if e.shape[0] != self._mu0.shape[0]:
            raise ErroDeClassificacao(
                f"embedding com {e.shape[0]} dimensoes; o artefato espera {self._mu0.shape[0]} "
                f"(extrator={self.procedencia.extrator})"
            )
        z = (e - self._mu0) @ self._P
        z = (z - self._media_da_fonte) / self._desvio_da_fonte
        pontuacoes = self._coef @ z + self._intercepto
        pontuacoes = pontuacoes - pontuacoes.max()  # estabilidade numerica
        exponenciais = np.exp(pontuacoes)
        return exponenciais / exponenciais.sum()

    def prever(self, recorte, dominio: Dominio, vista: Vista) -> Medida | None:
        """Medida da vista/dominio, ou `None` quando nao ha modelo para decidir (CORPO)."""
        return self.avaliar(recorte, dominio, vista)[1]

    def avaliar(
        self, recorte, dominio: Dominio, vista: Vista
    ) -> tuple[np.ndarray, Medida | None]:
        """Probabilidades E medida de UMA embutida.

        Existe porque o canario precisa das duas coisas sobre a mesma imagem: a classe do argmax (para
        recomputar o recall declarado, que o produtor mede sem abstencao) e a medida com o limiar
        aplicado (para a taxa de inconclusivo). Embutir duas vezes daria o mesmo numero por caminhos
        diferentes e mais tempo de bancada por nada.
        """
        if not isinstance(dominio, Dominio):
            raise ErroDeClassificacao(
                f"dominio tem de ser dominio.Dominio, recebido {dominio!r}"
            )
        if not isinstance(vista, Vista):
            raise ErroDeClassificacao(
                f"vista tem de ser dominio.Vista, recebida {vista!r}"
            )
        if dominio is not Dominio.TAMPA:
            return np.empty(0, dtype=np.float64), None
        if not isinstance(recorte, np.ndarray):
            raise ErroDeClassificacao(
                f"recorte tem de ser a imagem ja extraida (ndarray BGR), recebido "
                f"{type(recorte).__name__}: o classificador nao abre arquivo (a captura mora fora daqui)"
            )
        if recorte.ndim != 3 or recorte.shape[2] != 3 or recorte.size == 0:
            raise ErroDeClassificacao(
                f"recorte tem de ser imagem BGR (H, W, 3) nao vazia, recebido shape={getattr(recorte, 'shape', None)}"
            )

        probabilidades = self.probabilidades(self._embutidor(recorte))
        if probabilidades.shape[0] != len(self._classes):
            raise ErroDeClassificacao(
                f"artefato devolveu {probabilidades.shape[0]} probabilidades para {len(self._classes)} "
                f"classes: mapeamento impossivel"
            )
        escolhida = int(np.argmax(probabilidades))
        classe, confianca = self._classes[escolhida], float(probabilidades[escolhida])
        if confianca < self._limiar_de_confianca:
            return probabilidades, Medida(
                vista=vista,
                dominio=dominio,
                classe=Classe.INCONCLUSIVO,
                confianca=confianca,
                qualidade=Qualidade.INSUFICIENTE,
                evidencias=self._evidencias(confianca, roteou=True),
            )
        return probabilidades, Medida(
            vista=vista,
            dominio=dominio,
            classe=classe,
            confianca=confianca,
            evidencias=self._evidencias(confianca, roteou=False),
        )

    # ------------------------------------------------------------------ rastro

    def _evidencias(self, confianca: float, *, roteou: bool) -> tuple[Evidencia, ...]:
        """Rastro da decisao: a probabilidade, o limiar que a roteou e a limitacao declarada."""
        fonte_do_artefato = (
            f"{Path(self.procedencia.caminho).name}#{self.procedencia.sha256[:12]}"
        )
        evidencias = [
            Evidencia(
                grandeza="probabilidade_da_classe_decidida",
                valor=confianca,
                unidade="probabilidade",
                origem=Origem.CLASSIFICADOR,
                papel=Papel.FALLBACK if roteou else Papel.DECIDE,
                metodo=self.identificacao,
                fonte=fonte_do_artefato,
            ),
            Evidencia(
                grandeza="limiar_de_confianca_do_fallback",
                valor=self._limiar_de_confianca,
                unidade="probabilidade",
                origem=Origem.CLASSIFICADOR,
                papel=Papel.FALLBACK,
                metodo=self.identificacao,
                fonte=f"{Path(self.procedencia.meta_caminho).name}#limiar_abstencao",
            ),
        ]
        if self.procedencia.aviso:
            # sem `fonte`: e a propria limitacao que o artefato declara; parametro provisorio, nao
            # numero validado (D-24). Se o artefato se declara prototipo, o registro diz isso.
            evidencias.append(
                Evidencia(
                    grandeza="limitacao_declarada_pelo_artefato",
                    valor=None,
                    unidade="texto",
                    origem=Origem.CLASSIFICADOR,
                    papel=Papel.FALLBACK,
                    metodo=self.procedencia.aviso,
                    fonte=None,
                )
            )
        return tuple(evidencias)
