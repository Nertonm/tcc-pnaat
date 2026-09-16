"""Ajudantes de teste: contrato, pacote e modelo falso.

O fingerprint e recalculado aqui com uma implementacao INDEPENDENTE (lista de campos propria): se o
calculo do modulo mudar sem que o formato mude, este teste acusa em vez de acompanhar.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

CAMPOS_DO_FINGERPRINT = ("roi_por_camera", "rotacao_graus", "orientacao_entrada", "imgsz_treino",
                         "letterbox", "classes", "vista_por_camera", "regra_decisao")

CLASSES = ["normal", "tampa_ausente", "defeito_tampa"]


def sha256_de(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def fingerprint_do_contrato(contrato: dict) -> str:
    canonico = {campo: contrato[campo] for campo in CAMPOS_DO_FINGERPRINT}
    canonico["modelo_sha256"] = contrato["modelo"]["sha256"]
    return sha256_de(json.dumps(canonico, sort_keys=True, ensure_ascii=False).encode())


def contrato(*, peso_sha256: str = "0" * 64, peso_nome: str = "detector.pt", imgsz: int = 480,
             calibrado: bool = True, orientacao_entrada: str = "quadro_ja_orientado",
             roi_csi: dict | None = None, roi_usb: dict | None = None,
             rotacao_csi: int = 0, rotacao_usb: int = 90,
             classes: list[str] | None = None, limiares: dict | None = None,
             vistas: dict | None = None, fingerprint: str | None = None) -> dict:
    classes = list(classes or CLASSES)
    padrao = {"normal": 0.30, "tampa_ausente": 0.15, "defeito_tampa": 0.30}
    escolhidos = dict(limiares or padrao)
    entrada = {classe: escolhidos.get(classe) for classe in classes}
    entrada["calibrado"] = bool(calibrado)
    if calibrado:
        entrada["fonte"] = "calibra_limiar_val.py"
        entrada["f1_val_por_classe"] = {classe: 0.9 for classe in classes}
    dados = {
        "nome": "pnaat-preprocessamento",
        "versao": 1,
        "roi_por_camera": {
            "csi": dict(roi_csi or {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}),
            "usb": dict(roi_usb or {"x": 0.25, "y": 0.0, "w": 0.5, "h": 0.5}),
        },
        "rotacao_graus": {"csi": rotacao_csi, "usb": rotacao_usb},
        "orientacao_entrada": orientacao_entrada,
        "imgsz_treino": imgsz,
        "letterbox": True,
        "classes": classes,
        "limiares_por_imgsz": {str(imgsz): entrada},
        "modelo": {"arquivo": peso_nome, "sha256": peso_sha256,
                   "tamanho_bytes": None},
        "vista_por_camera": dict(vistas or {"csi": "lateral1", "usb": "lateral2"}),
        "regra_decisao": "limiar por classe; sem caixa acima do limiar -> REVISAR",
    }
    dados["fingerprint"] = fingerprint or fingerprint_do_contrato(dados)
    return dados


def metadados_do_treino(*, peso_sha256: str, classes: list[str] | None = None, imgsz: int = 480,
                        peso: str = "detector.pt") -> dict:
    return {
        "tag": "teste",
        "classes": list(classes or CLASSES),
        "peso": peso,
        "peso_sha256": peso_sha256,
        "peso_bytes": None,
        "args": {"imgsz": imgsz, "epochs": 1},
        "warning": "teste: metadados sinteticos, nenhum treino real",
        "metricas_val": {},
    }


def pacote(destino: Path, *, bytes_do_peso: bytes = b"peso-sintetico-de-teste",
           contrato_dados: dict | None = None, metadados_dados: dict | None = None,
           manifesto_extra: dict | None = None,
           peso_declarado_no_contrato: str | None = None) -> Path:
    """Escreve um pacote completo e valido; devolve o diretorio.

    O contrato e SINCRONIZADO com o peso que o pacote realmente carrega (sha e fingerprint
    recalculados), como acontece na vida real: quem gera o contrato o gera para o peso medido. Um
    contrato de outro peso passa a exigir `peso_declarado_no_contrato`, que e o caso negativo.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    peso_nome = "detector.pt"
    (destino / peso_nome).write_bytes(bytes_do_peso)
    peso_sha = sha256_de(bytes_do_peso)
    dados = dict(contrato_dados) if contrato_dados else contrato(peso_sha256=peso_sha,
                                                                 peso_nome=peso_nome)
    dados["modelo"] = {"arquivo": peso_nome,
                       "sha256": peso_declarado_no_contrato or peso_sha,
                       "tamanho_bytes": None}
    dados["fingerprint"] = fingerprint_do_contrato(dados)
    texto_contrato = json.dumps(dados, ensure_ascii=False, indent=1).encode()
    texto_metadados = json.dumps(metadados_dados or metadados_do_treino(peso_sha256=peso_sha),
                                 ensure_ascii=False, indent=1).encode()
    (destino / "preprocessamento.json").write_bytes(texto_contrato)
    (destino / "metadados-treino.json").write_bytes(texto_metadados)
    manifesto = {
        "versao": 1,
        "estado": "candidato_nao_promovido",
        "arquivo": peso_nome,
        "sha256": peso_sha,
        "classes": CLASSES,
        "imgsz_treino": (contrato_dados or {}).get("imgsz_treino", 480),
        "imgsz_calibrados": [(contrato_dados or {}).get("imgsz_treino", 480)],
        "manifests": {"dataset": {"sha256": None, "verificado": False}},
        "preprocessamento_sha256": sha256_de(texto_contrato),
        "metadados_treino_sha256": sha256_de(texto_metadados),
        "limitacoes_declaradas": ["pacote de teste: nenhuma medida de desempenho aqui"],
    }
    manifesto.update(manifesto_extra or {})
    (destino / "modelo.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2))
    linhas = []
    for arquivo in sorted(destino.iterdir()):
        if arquivo.name == "SHA256SUMS":
            continue
        linhas.append(f"{sha256_de(arquivo.read_bytes())}  {arquivo.name}\n")
    (destino / "SHA256SUMS").write_text("".join(linhas))
    return destino


class TensorFalso:
    """Interface minima de tensor do torch que o classificador usa (`.cpu().numpy()`)."""

    def __init__(self, valores):
        self._valores = np.asarray(valores)

    def cpu(self):
        return self

    def numpy(self):
        return self._valores


class CaixasFalsas:
    def __init__(self, caixas):
        self._caixas = list(caixas)

    def __len__(self):
        return len(self._caixas)

    @property
    def conf(self):
        return TensorFalso([conf for _, conf in self._caixas])

    @property
    def cls(self):
        return TensorFalso([indice for indice, _ in self._caixas])


class ResultadoFalso:
    def __init__(self, caixas):
        self.boxes = CaixasFalsas(caixas) if caixas else None


class ModeloFalso:
    """Detector falso deterministico: decide pelas caixas que o teste mandar.

    `por_media` mapeia um predicado sobre a media do recorte para a lista de caixas. Sem isso, o
    teste nao dependeria de torch nem de peso real, e o caminho exercitado seria o mesmo do detector.
    """

    def __init__(self, caixas=(), *, por_media=None, names=None, erro=None):
        self.caixas = list(caixas)
        self.por_media = list(por_media or ())
        self.names = dict(names or {0: "normal", 1: "tampa_ausente", 2: "defeito_tampa"})
        self.erro = erro
        self.chamadas: list[dict] = []

    def predict(self, imagem, imgsz=None, conf=None, verbose=False):
        if self.erro is not None:
            raise self.erro
        self.chamadas.append({"shape": tuple(np.asarray(imagem).shape), "imgsz": imgsz, "conf": conf})
        caixas = self.caixas
        media = float(np.asarray(imagem).mean()) if np.asarray(imagem).size else 0.0
        for predicado, do_predicado in self.por_media:
            if predicado(media):
                caixas = do_predicado
        return [ResultadoFalso(caixas)]


def carregador(modelo: ModeloFalso):
    """Callable no lugar do `YOLO(...)`: o teste nao carrega peso."""
    return lambda _caminho: modelo


class VerificadorFalso:
    """Diz que o item esta alinhado: sem isso nenhuma vista e utilizavel (fail-closed do captura)."""

    def __init__(self, resultado=None):
        self.resultado = resultado

    def verificar(self, _imagem):
        if self.resultado is not None:
            return self.resultado
        from captura import Alinhamento
        return Alinhamento.OK, 0.0
