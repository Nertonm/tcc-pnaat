"""Classificador MEDIDO da tampa (D-30): extrator congelado + cabeca rasa treinada na hora.

O que este modulo porta, medido em 2026-09-11: YOLO COCO (`yolov8n.pt`, conf 0.15, imgsz 960) acha a
caixa da garrafa; a faixa SUPERIOR de 22% da altura dessa caixa (a tampa/gargalo) e recortada e
redimensionada para 224x224; o embedding vem do MobileNetV3-small CONGELADO (pesos ImageNet DEFAULT,
`classifier = Identity`); a decisao e de uma regressao logistica (`C=0.5`, `max_iter=3000`) sobre
`StandardScaler`. Referencia no conjunto proprio: acuracia 0,977, LB95 0,882, maioria 0,455,
ganho +0,523, n=44 (`docs/DECISIONS.md:509`; saida bruta em `aval_cnn_sem_conf.txt`).

Nao existe peso treinado versionado; de proposito. O que existe e o conjunto rotulado e ESTE codigo:
o treino acontece na hora, no conjunto proprio (`CONJUNTO_PADRAO`), porque um `.pt`/`.pkl` binario
versionado esconderia a receita e envelheceria sem aviso. Peso inventado aqui nao entra: a
identificacao declarada e a RECEITA (`IDENTIFICACAO`), composta das mesmas constantes que o codigo usa.

Hipotese declarada (H-1, requisito desta portagem): o classificador recebe o RECORTE da tampa JA
EXTRAIDO; ndarray BGR uint8, o mesmo que `captura`/`orquestracao.recorte_da_vista` produzem; e NAO
abre arquivo. Quem abre arquivo e o treino (`amostras_do_conjunto`) e o detector; `prever` so ve
pixels. Motivo: em producao o recorte vem da ROI declarada pelo rig, nao de um caminho de arquivo;
um classificador que abre arquivo esconderia a captura dentro da decisao, e o ligamento
captura -> decisao deixaria de ser verificavel. Receber caminho e ERRO explicito, nao conveniencia.

Dominios (D-28/D-30): da TAMPA existe modelo; do CORPO nao existe; `prever` devolve `None` para o
corpo, e `None` significa "nao posso decidir", que e exatamente o que aciona o fallback da D-30
(inconclusivo + analise humana). Classe inventada nunca: a classe prevista e validada contra
`VOCABULARIO` do dominio antes de virar `Medida`, e a propria `Medida` recusa classe fora do dominio.

Nada de torch no import: `torch`, `torchvision`, `ultralytics`, `sklearn`, `numpy` e `cv2` entram
tarde, dentro das funcoes/classes que precisam deles. O modulo tem de ser importavel (e os testes tem
de rodar) numa maquina sem a stack de inferencia; o `pyproject` declara isso como extra `inferencia`.
"""

from __future__ import annotations

import os

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from dominio import (
    VOCABULARIO,
    Classe,
    Dominio,
    Evidencia,
    Medida,
    Origem,
    Papel,
    Qualidade,
    Vista,
)

if TYPE_CHECKING:  # anotacao apenas: numpy nao entra no import do modulo
    import numpy as np


# ---------------------------------------------------------------- receita (constantes declaradas)

#: conjunto rotulado proprio do dominio da tampa (a fonte de verdade das imagens). Versionado no
#: repo, em dataset/nosso/tampa; reorganizado em 2026-09-13: o rig virou bloco separado
#: (dataset/nosso/rig, 81 frames normais, nunca treinado) e os publicos ficaram fora do git.
#: Caminho declarado e nao procurado; conjunto ausente e ERRO, nao "treina com o que tem".
def raiz_do_clone(inicio: Path | None = None) -> Path:
    """Raiz do clone descoberta pelo conteudo (docs/ + dataset/), nao pelo $HOME de quem roda.

    O ambiente declarado vence: `PNAAT_RAIZ_DO_CLONE`. Sem ele, sobe a partir deste arquivo ate
    achar a raiz; caminho de usuario fixo quebrava em clone de outro lugar e passava despercebido
    numa maquina so.
    """
    declarada = os.environ.get("PNAAT_RAIZ_DO_CLONE")
    if declarada:
        return Path(declarada)
    origem = (inicio or Path(__file__).resolve().parent.parent).resolve()
    for candidato in (origem, *origem.parents):
        if (candidato / "docs").is_dir() and (candidato / "dataset").is_dir():
            return candidato
    raise RuntimeError(f"raiz do clone nao encontrada a partir de {origem} (docs/ + dataset/)")


CONJUNTO_PADRAO = Path(
    os.environ.get("PNAAT_CONJUNTO_TAMPA")
    or raiz_do_clone() / "dataset/nosso/tampa"
)

#: pesos da deteccao. O arquivo vive na raiz do clone; NAO ha download automatico: baixar peso em
#: silencio seria efeito de rede escondido dentro da decisao (falha explicita se faltar).
#: NAO derivar de CONJUNTO_PADRAO: o conjunto proprio mudou de lugar (dataset/nosso/tampa) e o peso
#: continua na raiz do clone.
RAIZ_DO_CLONE = raiz_do_clone()
PESOS_DA_DETECCAO = str(RAIZ_DO_CLONE / "yolov8n.pt")
CLASSE_DA_CAIXA = "bottle"
CONFIANCA_DA_DETECCAO = 0.15
TAMANHO_DA_DETECCAO = 960

#: fracao da ALTURA da caixa COCO que corresponde a tampa (gargalo/rosca); medido, nao estimado
FRACAO_DO_TOPO = 0.22
LADO_DA_ENTRADA = 224

#: extrator congelado: so o corpo da rede, sem a cabeca de 1000 classes do ImageNet
EXTRATOR = "mobilenet_v3_small"
PESOS_DO_EXTRATOR = "imagenet-default"

#: cabeca rasa
C_DA_REGULARIZACAO = 0.5
MAX_ITERACOES = 3000

#: protocolo de validacao (mesmo do numero de referencia: estratificado, embaralhado, semente fixa)
DOBRAS = 5
SEMENTE = 7

#: fonte do protocolo medido; `arquivo:linha` do numero que sustenta a D-30 (D-24)
FONTE_DO_PROTOCOLO = "docs/DECISIONS.md:509"

#: identificacao do artefato. E a receita inteira: mudar qualquer constante acima muda esta string,
#: e o teste de identificacao falha se elas divergirem.
VERSAO = "medida-cnn-recorte-1"
IDENTIFICACAO = (
    f"{VERSAO}"
    f"|extrator={EXTRATOR}({PESOS_DO_EXTRATOR},congelado,classifier=Identity)"
    f"|cabeca=logistic-regression(C={C_DA_REGULARIZACAO},max_iter={MAX_ITERACOES})+StandardScaler"
    f"|deteccao={Path(PESOS_DA_DETECCAO).name}(classe={CLASSE_DA_CAIXA},conf={CONFIANCA_DA_DETECCAO},"
    f"imgsz={TAMANHO_DA_DETECCAO})"
    f"|recorte={FRACAO_DO_TOPO:.0%}-do-topo-do-box"
    f"|entrada={LADO_DA_ENTRADA}px"
    f"|validacao={DOBRAS}dobras-semente{SEMENTE}"
)

#: rotulo por prefixo do nome de arquivo. Fonte unica do mapeamento (nao ha rotulo em outro lugar).
#: `deformidade` entra como NORMAL: a deformidade e do CORPO, e a tampa daquela garrafa esta boa;
#: rotular `deformidade` no dominio da tampa seria exatamente o confundimento classe x dominio que a
#: D-30 manda evitar. `frame_` sao capturas do rig (garrafa normal, outro enquadramento).
PREFIXO_DAS_CAPTURAS_DO_RIG = "frame_"
ROTULOS_POR_PREFIXO: tuple[tuple[str, Classe], ...] = (
    ("tampa_ausente", Classe.TAMPA_AUSENTE),
    (
        "tampa_mal_rosqueada",
        Classe.DEFEITO_TAMPA,
    ),  # D-31: o dado mantem o nome, a classe funde
    ("deformidade", Classe.NORMAL),
    (PREFIXO_DAS_CAPTURAS_DO_RIG, Classe.NORMAL),
)


class ErroDeClassificacao(Exception):
    """O classificador nao pode decidir como foi pedido (entrada incoerente, sem rotulo, sem caixa).

    Falha explicita no lugar de default silencioso: recorte que nao e imagem, caminho de arquivo no
    lugar de pixels, classe fora do dominio ou conjunto ausente tem de parar a cadeia, nao virar
    "normal" por omissao (D-04/D-28).
    """


# ---------------------------------------------------------------- rotulos do conjunto


@dataclass(frozen=True)
class ItemRotulado:
    """Uma imagem do conjunto com a classe verdadeira declarada pelo nome do arquivo."""

    arquivo: Path
    classe: Classe


def rotulo_do_nome(nome: str) -> Classe:
    """Classe verdadeira a partir do nome do arquivo do conjunto (mapeamento declarado acima).

    Sem prefixo conhecido e ERRO: nome novo nao vira `normal` por omissao; um arquivo rotulado errado
    envenena o treino em silencio, que e o pior modo de falhar de um classificador.
    """
    for prefixo, classe in ROTULOS_POR_PREFIXO:
        if nome.startswith(prefixo):
            return classe
    raise ErroDeClassificacao(
        f"nome sem rotulo declarado: {nome!r} (prefixos conhecidos: "
        f"{[p for p, _ in ROTULOS_POR_PREFIXO]})"
    )


def conjunto_rotulado(
    base: Path = CONJUNTO_PADRAO, *, ignorar: tuple[str, ...] = ()
) -> tuple[ItemRotulado, ...]:
    """Le o conjunto rotulado da pasta. Ordem estavel (nome), para o resultado ser reproduzivel.

    `ignorar` e explicito em quem chama, nunca implicito: o numero de referencia (0,977) foi medido
    SEM as capturas do rig, e o chamador que quer esse protocolo declara
    `ignorar=(PREFIXO_DAS_CAPTURAS_DO_RIG,)`. Sem `ignorar`, entram todos os rotulados.
    """
    if not base.is_dir():
        raise ErroDeClassificacao(f"conjunto rotulado nao encontrado: {base}")
    itens = tuple(
        ItemRotulado(caminho, rotulo_do_nome(caminho.name))
        for caminho in sorted(base.glob("*.jpg"))
        if not any(caminho.name.startswith(p) for p in ignorar)
    )
    if not itens:
        raise ErroDeClassificacao(
            f"conjunto rotulado vazio em {base}: nao ha o que treinar"
        )
    return itens


def distribuicao(itens: Sequence[ItemRotulado]) -> tuple[tuple[Classe, int], ...]:
    """Contagem por classe, ordenada: e o que permite ver a maioria do conjunto (baseline honesto)."""
    contagem = Counter(item.classe for item in itens)
    # ordem DECLARADA (a do enum), nao alfabetica: renomear uma classe nao pode reordenar o
    # relatorio. Antes era `key=lambda c: c.value`, o que fazia a ordem depender do nome.
    declarada = {classe: i for i, classe in enumerate(Classe)}
    return tuple(
        (classe, contagem[classe])
        for classe in sorted(contagem, key=lambda c: declarada[c])
    )


# ---------------------------------------------------------------- recorte e extrator


def recorte_da_tampa(
    quadro: np.ndarray, caixa: tuple[int, int, int, int]
) -> np.ndarray:
    """Recorta a faixa SUPERIOR da caixa (22% da altura); a tampa/gargalo, na escala do quadro.

    Mesma conta do protocolo medido: `int(y1 + (y2 - y1) * FRACAO_DO_TOPO)`, sem arredondar. Caixa
    degenerada ou fora do quadro e ERRO: o protocolo de referencia pulava esses itens em silencio, e
    silencio e justamente o que nao pode existir num recorte que decide.
    """
    import numpy as np

    if not isinstance(quadro, np.ndarray) or quadro.ndim != 3 or quadro.shape[2] != 3:
        raise ErroDeClassificacao(
            f"quadro tem de ser imagem BGR (altura, largura, 3): recebido "
            f"{type(quadro).__name__} com forma {getattr(quadro, 'shape', None)}"
        )
    x1, y1, x2, y2 = (int(v) for v in caixa)
    altura, largura = quadro.shape[:2]
    if not (0 <= x1 < x2 <= largura and 0 <= y1 < y2 <= altura):
        raise ErroDeClassificacao(
            f"caixa {caixa} fora do quadro {largura}x{altura} ou degenerada: recorte sem pixels"
        )
    recorte = quadro[y1 : int(y1 + (y2 - y1) * FRACAO_DO_TOPO), x1:x2]
    if recorte.size == 0:
        raise ErroDeClassificacao(
            f"caixa {caixa} produz recorte vazio (fracao {FRACAO_DO_TOPO})"
        )
    return recorte


class DetectorDeGarrafa:
    """Acha a caixa da garrafa (YOLO COCO). Entre as caixas `bottle`, fica a de MAIOR confianca.

    Nao baixa peso e nao abre arquivo: recebe o quadro ja lido. Nenhuma caixa da classe `bottle` e
    ERRO; sem caixa nao ha recorte, e um recorte inventado decidiria sobre a area errada. Quadro que
    nao e imagem tambem e ERRO, e por um motivo concreto: sem fonte, o YOLO cai num asset empacotado
    (`.../ultralytics/assets`) e devolveria a caixa de OUTRA imagem com cara de valida; default
    silencioso, exatamente o que este modulo recusa.
    """

    identificacao = (
        f"{Path(PESOS_DA_DETECCAO).name}(classe={CLASSE_DA_CAIXA},"
        f"conf={CONFIANCA_DA_DETECCAO},imgsz={TAMANHO_DA_DETECCAO})"
    )

    def __init__(
        self, pesos: str = PESOS_DA_DETECCAO, dispositivo: str | None = None
    ) -> None:
        import torch
        from ultralytics import YOLO

        if not Path(pesos).is_file():
            raise ErroDeClassificacao(
                f"pesos de deteccao ausentes: {pesos} (sem download automatico)"
            )
        self._dispositivo = _resolver_dispositivo(dispositivo, torch)
        self._detector = YOLO(pesos)

    def caixa(
        self, quadro: np.ndarray, *, origem: str = "quadro"
    ) -> tuple[int, int, int, int]:
        import numpy as np

        if (
            not isinstance(quadro, np.ndarray)
            or quadro.ndim != 3
            or quadro.shape[2] != 3
        ):
            raise ErroDeClassificacao(
                f"quadro em {origem} tem de ser imagem BGR (altura, largura, 3): recebido "
                f"{type(quadro).__name__} com forma {getattr(quadro, 'shape', None)}"
            )
        resultado = self._detector.predict(
            quadro,
            conf=CONFIANCA_DA_DETECCAO,
            imgsz=TAMANHO_DA_DETECCAO,
            device=self._dispositivo,
            verbose=False,
        )[0]
        caixas = resultado.boxes
        candidatas = (
            [
                i
                for i in range(len(caixas))
                if str(resultado.names[int(caixas.cls[i])]) == CLASSE_DA_CAIXA
            ]
            if caixas is not None and len(caixas)
            else []
        )
        if not candidatas:
            raise ErroDeClassificacao(
                f"nenhuma caixa {CLASSE_DA_CAIXA!r} em {origem}: sem caixa nao ha "
                f"recorte (fail-closed)"
            )
        melhor = max(candidatas, key=lambda i: float(caixas.conf[i]))
        return tuple(int(v) for v in caixas.xyxy[melhor].tolist())  # type: ignore[return-value]


class ExtratorDeEmbedding:
    """MobileNetV3-small congelado sobre o RECORTE (pesos ImageNet DEFAULT, `classifier = Identity`).

    Congelado de proposito: o que se treina e a cabeca rasa, e um extrator congelado nao aprende o
    conjunto de 44 itens (que decora facil e generaliza mal). O pre-processamento e o `transforms()`
    do proprio preset dos pesos, aplicado ao tensor 224x224; inclusive o `Resize(256)` +
    `CenterCrop(224)` que o preset faz DEPOIS do resize de 224 do protocolo: esse ida-e-volta faz
    parte do numero medido, e "limpar" isso mudaria a referencia (decisao declarada, nao descuido).
    """

    identificacao = f"{EXTRATOR}({PESOS_DO_EXTRATOR},congelado,classifier=Identity)"

    def __init__(self, dispositivo: str | None = None) -> None:
        import torch
        from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

        self._torch = torch
        self._dispositivo = _resolver_dispositivo(dispositivo, torch)
        pesos = MobileNet_V3_Small_Weights.DEFAULT
        modelo = mobilenet_v3_small(weights=pesos)
        modelo.classifier = torch.nn.Identity()
        modelo.eval()
        modelo.to(self._dispositivo)
        self._modelo = modelo
        self._prep = pesos.transforms()

    @property
    def dispositivo(self) -> str:
        return self._dispositivo

    def embedding(self, recorte: np.ndarray) -> np.ndarray:
        """Vetor do recorte (BGR uint8). Nenhum arquivo e aberto aqui: so pixels."""
        import cv2
        import numpy as np
        import torch

        if (
            not isinstance(recorte, np.ndarray)
            or recorte.ndim != 3
            or recorte.shape[2] != 3
        ):
            raise ErroDeClassificacao(
                f"recorte tem de ser imagem BGR (altura, largura, 3): recebido "
                f"{type(recorte).__name__} com forma {getattr(recorte, 'shape', None)}"
            )
        rgb = cv2.cvtColor(
            cv2.resize(recorte, (LADO_DA_ENTRADA, LADO_DA_ENTRADA)), cv2.COLOR_BGR2RGB
        )
        tensor = (
            torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).float() / 255.0
        )
        with torch.no_grad():
            return (
                self._modelo(self._prep(tensor).unsqueeze(0).to(self._dispositivo))
                .cpu()
                .numpy()[0]
            )


def _resolver_dispositivo(dispositivo: str | None, torch) -> str:
    """`None` = o melhor disponivel (cuda se houver). Dispositivo declarado e respeitado ou ERRO."""
    if dispositivo is None:
        return "cuda" if torch.cuda.is_available() else "cpu"
    if dispositivo.startswith("cuda") and not torch.cuda.is_available():
        raise ErroDeClassificacao(
            f"dispositivo {dispositivo!r} declarado sem CUDA disponivel"
        )
    return dispositivo


@dataclass(frozen=True, eq=False)
class Amostra:
    """Um item do conjunto ja recortado: origem (rastro), classe verdadeira e embedding do recorte.

    `eq=False` de proposito: comparar `Amostra` compararia `ndarray` campo a campo e levantaria
    "truth value of an array is ambiguous" no meio de um teste; igualdade aqui nao e contrato.
    """

    origem: str
    classe: Classe
    embedding: np.ndarray


def amostras_do_conjunto(
    itens: Sequence[ItemRotulado],
    detector: DetectorDeGarrafa,
    extrator: ExtratorDeEmbedding,
) -> tuple[Amostra, ...]:
    """Recorta e extrai o embedding de cada item. E AQUI que o arquivo e aberto; nunca em `prever`.

    Separar a extracao do classificador e o que torna o treino reproduzivel: o mesmo recorte que a
    cadeia vai passar em producao (ROI do rig) e o que a cabeca ve no treino.
    """
    import cv2

    amostras: list[Amostra] = []
    for item in itens:
        quadro = cv2.imread(str(item.arquivo))
        if quadro is None:
            raise ErroDeClassificacao(f"imagem ilegivel: {item.arquivo}")
        caixa = detector.caixa(quadro, origem=str(item.arquivo))
        recorte = recorte_da_tampa(quadro, caixa)
        amostras.append(
            Amostra(
                origem=item.arquivo.name,
                classe=item.classe,
                embedding=extrator.embedding(recorte),
            )
        )
    if not amostras:
        raise ErroDeClassificacao("nenhuma amostra extraida: nao ha o que treinar")
    return tuple(amostras)


# ---------------------------------------------------------------- validacao (o numero de referencia)


@dataclass(frozen=True)
class Desempenho:
    """Recall de uma classe com o limite inferior de Wilson (95%); IC de proporcao honesto em n baixo."""

    classe: Classe
    n: int
    acertos: int
    recall: float
    lb95: float


@dataclass(frozen=True)
class ResultadoDaValidacao:
    """O que a validacao cruzada devolve: acuracia, piso honesto (LB95), baseline e ganho.

    `maioria` e o preditor constante do conjunto (a classe mais frequente): sem ela, uma acuracia alta
    em conjunto desbalanceado nao diz nada. `ganho` = acuracia - maioria e o numero que a D-30 cita.
    """

    n: int
    acertos: int
    acuracia: float
    lb95: float
    maioria: float
    ganho: float
    por_classe: tuple[Desempenho, ...]
    dobras: int
    semente: int
    fonte: str | None = None


def wilson(acertos: int, n: int, z: float = 1.959963984540054) -> float:
    """Limite inferior do intervalo de Wilson. `n = 0` devolve 0,0: sem itens, sem confianca."""
    if n <= 0:
        return 0.0
    p, z2 = acertos / n, z * z
    centro = p + z2 / (2 * n)
    margem = z * (p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5
    return max(0.0, (centro - margem) / (1 + z2 / n))


def medir_por_validacao_cruzada(
    amostras: Sequence[Amostra],
    *,
    dobras: int = DOBRAS,
    semente: int = SEMENTE,
    fonte: str | None = None,
) -> ResultadoDaValidacao:
    """Valida a receita no conjunto proprio, por validacao cruzada estratificada.

    Treina e testa no MESMO dominio (nossas imagens), com as dobras estratificadas e embaralhadas com
    semente fixa; sem isso o numero nao se reproduz e nao vale como evidencia. A escala (`StandardScaler`)
    e refeita DENTRO de cada dobra: ajustar a escala no conjunto todo vazaria o teste para o treino.
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    if not amostras:
        raise ErroDeClassificacao("validacao sem amostras: nada a medir")
    X = np.array([a.embedding for a in amostras])
    y = np.array([a.classe.value for a in amostras])
    contagem = Counter(y)
    if len(contagem) < 2:
        raise ErroDeClassificacao(
            f"conjunto com uma classe so nao sustenta validacao cruzada: {sorted(contagem)}"
        )
    k = min(dobras, min(contagem.values()))
    if k < 2:
        raise ErroDeClassificacao(
            f"classe com menos de 2 itens nao sustenta validacao cruzada estratificada: {dict(contagem)}"
        )

    por_classe: dict[str, list[int]] = {}
    for treino, teste in StratifiedKFold(
        n_splits=k, shuffle=True, random_state=semente
    ).split(X, y):
        escala = StandardScaler().fit(X[treino])
        cabeca = LogisticRegression(max_iter=MAX_ITERACOES, C=C_DA_REGULARIZACAO).fit(
            escala.transform(X[treino]), y[treino]
        )
        for verdadeiro, previsto in zip(
            y[teste], cabeca.predict(escala.transform(X[teste]))
        ):
            linha = por_classe.setdefault(verdadeiro, [0, 0])
            linha[0] += 1
            linha[1] += int(verdadeiro == previsto)

    n = int(y.shape[0])
    acertos = sum(linha[1] for linha in por_classe.values())
    maioria = max(contagem.values()) / n
    return ResultadoDaValidacao(
        n=n,
        acertos=acertos,
        acuracia=acertos / n,
        lb95=wilson(acertos, n),
        maioria=maioria,
        ganho=acertos / n - maioria,
        dobras=k,
        semente=semente,
        fonte=fonte,
        por_classe=tuple(
            Desempenho(
                classe=Classe(nome),
                n=linha[0],
                acertos=linha[1],
                recall=linha[1] / linha[0],
                lb95=wilson(linha[1], linha[0]),
            )
            for nome, linha in sorted(por_classe.items())
        ),
    )


#: O numero medido que sustenta a D-30, com a fonte. Subconjunto de n=44: o conjunto proprio SEM as
#: capturas do rig (`ignorar=(PREFIXO_DAS_CAPTURAS_DO_RIG,)`), que sao de outro enquadramento; o
#: mesmo corte do script de referencia, e o unico conjunto em que o numero e comparavel.
REFERENCIA_MEDIDA = ResultadoDaValidacao(
    n=44,
    acertos=43,
    acuracia=0.977,
    lb95=0.882,
    maioria=0.455,
    ganho=0.523,
    dobras=5,
    semente=7,
    fonte=FONTE_DO_PROTOCOLO,
    por_classe=(
        Desempenho(classe=Classe.NORMAL, n=9, acertos=8, recall=0.889, lb95=0.565),
        Desempenho(
            classe=Classe.TAMPA_AUSENTE, n=15, acertos=15, recall=1.000, lb95=0.796
        ),
        Desempenho(
            classe=Classe.DEFEITO_TAMPA, n=20, acertos=20, recall=1.000, lb95=0.839
        ),
    ),
)


def comparar_com_a_referencia(
    obtido: ResultadoDaValidacao, referencia: ResultadoDaValidacao = REFERENCIA_MEDIDA
) -> tuple[bool, str]:
    """Compara a medicao com a referencia e devolve (bateu, motivo); sem maquiar diferenca.

    A comparacao e por `acertos` e `n`, nao por diferenca de acuracia arredondada: 0,977 com n=44 e
    43/44, e qualquer outro par nao "bate quase". Conjunto de tamanho diferente nao e comparavel, e o
    motivo diz isso em vez de fingir concordancia.
    """
    if obtido.n != referencia.n:
        return False, (
            f"conjuntos de tamanhos diferentes: obtido n={obtido.n} (acuracia "
            f"{obtido.acuracia:.3f}), referencia n={referencia.n} "
            f"({referencia.acuracia:.3f}); nao comparavel"
        )
    if obtido.acertos != referencia.acertos:
        return False, (
            f"acuracia {obtido.acuracia:.3f} ({obtido.acertos}/{obtido.n}) difere da "
            f"referencia {referencia.acuracia:.3f} ({referencia.acertos}/{referencia.n})"
        )
    return True, (
        f"acuracia {obtido.acuracia:.3f} ({obtido.acertos}/{obtido.n}), LB95 {obtido.lb95:.3f}, "
        f"maioria {obtido.maioria:.3f}, ganho {obtido.ganho:+.3f}; igual a referencia "
        f"({referencia.fonte})"
    )


# ---------------------------------------------------------------- o classificador atras do Protocol


class CabecaRasa(Protocol):
    """O que o classificador exige da cabeca treinada (o `Pipeline` do sklearn satisfaz)."""

    classes_: np.ndarray

    def predict_proba(self, X: np.ndarray) -> np.ndarray: ...


@dataclass(frozen=True)
class Procedencia:
    """Receita do modelo que esta em memoria: sem peso versionado, este recibo e o que resta do treino."""

    base: str
    itens: int
    por_classe: tuple[tuple[Classe, int], ...]
    dispositivo: str


class ClassificadorDeTampa:
    """A vista da tampa atras do `decisao.ClassificadorDeVista` (D-30): devolve `Medida` ou `None`.

    O contrato e do Protocol: `identificacao` (str) e `prever(recorte, dominio, vista)`. Recebe a
    VISTA de origem porque so quem chamou sabe de qual vista veio o recorte; a `Medida` exige vista,
    e chutar `lateral1` faria a medida mentir sobre a origem (o `Decisor` recusa com `ErroDeDecisao`).
    Por isso: a vista e o dominio DEVOLVIDOS sao exatamente os consultados.

    `None` = "nao posso decidir" e so isso: e o que aciona o fallback da D-30 (inconclusivo + analise
    humana). Hoje o dominio CORPO nao tem modelo, entao TODO recorte do corpo devolve `None`; nunca
    uma classe normal inventada, que seria aprovacao silenciosa (D-04).

    O PAPEL da vista nao e decidido aqui: quem declara que o topo nunca decide (D-23/D-30) e o rig
    (`conformidade.ConfiguracaoDoRig`, que nem consulta a vista de check) e o registro (o banco recusa
    `papel='decide'` em `vista='topo'`). Duplicar essa trava neste modulo criaria duas fontes para a
    mesma regra; o classificador sabe apenas a vista de onde o recorte veio, e a devolve.
    """

    #: receita declarada (constante de modulo, composta das constantes da receita)
    identificacao: str = IDENTIFICACAO

    def __init__(
        self,
        extrator: ExtratorDeEmbedding,
        cabeca: CabecaRasa,
        *,
        procedencia: Procedencia | None = None,
        limiar_de_confianca: float = 0.0,
    ) -> None:
        if not callable(getattr(extrator, "embedding", None)):
            raise ErroDeClassificacao(f"extrator sem embedding(): {extrator!r}")
        if not callable(getattr(cabeca, "predict_proba", None)):
            raise ErroDeClassificacao(f"cabeca sem predict_proba(): {cabeca!r}")
        if not 0.0 <= limiar_de_confianca <= 1.0:
            raise ErroDeClassificacao(
                f"limiar de confianca fora de [0,1]: {limiar_de_confianca}"
            )
        declaradas = getattr(cabeca, "classes_", None)
        nomes = () if declaradas is None else tuple(str(nome) for nome in declaradas)
        if not nomes:
            raise ErroDeClassificacao(
                "cabeca sem classes_: nao ha como mapear a probabilidade em classe"
            )
        self._extrator = extrator
        self._cabeca = cabeca
        self._limiar_de_confianca = float(limiar_de_confianca)
        self._classes = tuple(
            _classe_da_tampa(nome) for nome in nomes
        )  # recusa classe fora do dominio
        self.procedencia = procedencia

    # ------------------------------------------------------------ o contrato

    def prever(self, recorte, dominio: Dominio, vista: Vista) -> Medida | None:
        """Medida da vista/dominio consultados, ou `None` quando nao posso decidir.

        - dominio CORPO: `None` declarado (nao existe modelo do corpo). Nada e extraido: nao se mede o
          que nao se tem modelo para decidir;
        - recorte que nao e imagem BGR (caminho de arquivo, lista, vazio) e ERRO: a hipotese H-1 e que
          o recorte chega pronto, e aceitar caminho mudaria a hipotese em silencio;
        - classe prevista fora do vocabulario do dominio e ERRO (D-28), nunca coacao para `normal`;
        - confianca abaixo do limiar declarado roteia: medida `inconclusivo` com qualidade
          insuficiente, que o `Decisor` manda para o fallback em vez de decidir no cara-ou-coroa.
        """
        import numpy as np

        if not isinstance(dominio, Dominio):
            raise ErroDeClassificacao(
                f"dominio tem de ser dominio.Dominio, recebido {dominio!r}"
            )
        if not isinstance(vista, Vista):
            raise ErroDeClassificacao(
                f"vista tem de ser dominio.Vista, recebida {vista!r}"
            )
        if dominio is not Dominio.TAMPA:
            return None
        if not isinstance(recorte, np.ndarray):
            raise ErroDeClassificacao(
                f"recorte tem de ser a imagem ja extraida (ndarray BGR), recebido {type(recorte).__name__}: "
                f"o classificador nao abre arquivo (a captura mora fora daqui)"
            )

        probabilidades = np.asarray(
            self._cabeca.predict_proba(
                np.asarray(self._extrator.embedding(recorte)).reshape(1, -1)
            )
        )[0]
        if probabilidades.shape[0] != len(self._classes):
            raise ErroDeClassificacao(
                f"cabeca devolveu {probabilidades.shape[0]} probabilidades para {len(self._classes)} "
                f"classes: mapeamento impossivel"
            )
        escolhida = int(np.argmax(probabilidades))
        classe, confianca = self._classes[escolhida], float(probabilidades[escolhida])
        if confianca < self._limiar_de_confianca:
            return Medida(
                vista=vista,
                dominio=dominio,
                classe=Classe.INCONCLUSIVO,
                confianca=confianca,
                qualidade=Qualidade.INSUFICIENTE,
                evidencias=self._evidencias(confianca, roteou=True),
            )
        return Medida(
            vista=vista,
            dominio=dominio,
            classe=classe,
            confianca=confianca,
            evidencias=self._evidencias(confianca, roteou=False),
        )

    # ------------------------------------------------------------ treino na hora

    @classmethod
    def treinar_no_conjunto(
        cls,
        base: Path = CONJUNTO_PADRAO,
        *,
        ignorar: tuple[str, ...] = (),
        dispositivo: str | None = None,
        pesos_da_deteccao: str = PESOS_DA_DETECCAO,
        limiar_de_confianca: float = 0.0,
    ) -> ClassificadorDeTampa:
        """Treina a cabeca NA HORA com o conjunto proprio e devolve o classificador pronto.

        Por padrao entram TODOS os rotulados (as capturas do rig tambem: garrafa normal). O protocolo
        de referencia (0,977) e o subconjunto sem elas; quem quer reproduzir aquele numero chama
        `ignorar=(PREFIXO_DAS_CAPTURAS_DO_RIG,)` e mede com `medir_por_validacao_cruzada`.
        """
        itens = conjunto_rotulado(base, ignorar=ignorar)
        detector = DetectorDeGarrafa(pesos_da_deteccao, dispositivo)
        extrator = ExtratorDeEmbedding(dispositivo)
        amostras = amostras_do_conjunto(itens, detector, extrator)
        cabeca = _treinar_cabeca(amostras)
        return cls(
            extrator,
            cabeca,
            limiar_de_confianca=limiar_de_confianca,
            procedencia=Procedencia(
                base=str(base),
                itens=len(amostras),
                por_classe=distribuicao(itens),
                dispositivo=extrator.dispositivo,
            ),
        )

    # ------------------------------------------------------------ interno

    def _evidencias(self, confianca: float, *, roteou: bool) -> tuple[Evidencia, ...]:
        """Rastro da decisao (D-24/D-30): a probabilidade que decidiu e o limiar que a roteou.

        O limiar entra SEM fonte: a confianca minima que dispara o fallback segue em aberto na D-30
        (item (i)), entao ele e declarado provisorio (`Evidencia.provisorio()`), nunca um parametro
        calibrado com cara de definitivo.
        """
        papel = Papel.FALLBACK if roteou else Papel.DECIDE
        return (
            Evidencia(
                grandeza="probabilidade_da_classe_decidida",
                valor=confianca,
                unidade="probabilidade",
                origem=Origem.CLASSIFICADOR,
                papel=papel,
                metodo=self.identificacao,
                fonte=FONTE_DO_PROTOCOLO,
            ),
            Evidencia(
                grandeza="limiar_de_confianca_do_fallback",
                valor=self._limiar_de_confianca,
                unidade="probabilidade",
                origem=Origem.CLASSIFICADOR,
                papel=Papel.FALLBACK,
                metodo=self.identificacao,
                fonte=None,
            ),
        )


def _classe_da_tampa(nome: str) -> Classe:
    """Converte o nome de classe da cabeca em `Classe` do dominio da tampa (D-28). Erro fora disso."""
    try:
        classe = Classe(nome)
    except ValueError as erro:
        raise ErroDeClassificacao(
            f"classe desconhecida vinda da cabeca: {nome!r}"
        ) from erro
    if classe not in VOCABULARIO[Dominio.TAMPA]:
        raise ErroDeClassificacao(
            f"cabeca treinada com classe {nome!r}, que nao existe no dominio da tampa (D-28): "
            f"vocabulario {sorted(c.value for c in VOCABULARIO[Dominio.TAMPA])}"
        )
    return classe


def _treinar_cabeca(amostras: Sequence[Amostra]):
    """Ajusta `StandardScaler` + `LogisticRegression(C=0.5)` sobre os embeddings do conjunto.

    Uma classe so no conjunto e ERRO: sem duas classes nao existe classificador, e "treinar" assim
    devolveria um objeto que sempre responde a mesma coisa (aprovacao silenciosa disfarcada de modelo).
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    X = np.array([a.embedding for a in amostras])
    y = np.array([a.classe.value for a in amostras])
    if len(set(y.tolist())) < 2:
        raise ErroDeClassificacao(
            f"conjunto com uma classe so: {sorted(set(y.tolist()))}"
        )
    return Pipeline(
        [
            ("escala", StandardScaler()),
            (
                "cabeca",
                LogisticRegression(max_iter=MAX_ITERACOES, C=C_DA_REGULARIZACAO),
            ),
        ]
    ).fit(X, y)
