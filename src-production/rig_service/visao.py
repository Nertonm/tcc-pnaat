"""Identifica o que a camera do Pi ve na garrafa: OK ou qual defeito (geometria, sem modelo).

Sem OpenCV: apenas numpy + Pillow. A decisao e RELATIVA a uma referencia capturada no proprio setup:
  1. `fundo`   = cena sem a garrafa  -> base da segmentacao por diferenca;
  2. `referencia` = garrafa boa -> guarda as medidas E a SILHUETA (mascara);
  3. cada item e comparado com a referencia: coincide (IoU) -> OK; diferenca no topo -> tampa
     ausente/torta; diferenca no corpo -> deformidade; sem evidencia -> inconclusivo.

Regras de honestidade embutidas (todas testadas):
  * nenhum limiar de captura e absoluto: foco, brilho e saturacao sao comparados com a referencia
    (limiar derivado do setup, como exige D-24 do projeto);
  * a comparacao com o fundo corrige offset e GANHO de exposicao (mudanca de exposicao nao vira
    "garrafa"); o ajuste e feito nos pixels de fundo, em duas passadas;
  * cena trocada/camera movida e detectada pela ESTRUTURA no anel da ROI;
  * a silhueta passa por testes de plausibilidade (area, aspecto, topo x corpo);
  * quando nao da para medir, o sistema diz o motivo -- nao inventa veredito.

Medidas por imagem (relativas; distancia da camera nao muda o veredito):
  altura_rel    = altura da silhueta / largura MEDIANA (robusta a bojo local)
  tilt_tampa    = inclinacao do topo em relacao ao quadro (informativa; o veredito usa o
                  tilt DIFERENCIAL contra a referencia)
  nitidez       = Tenengrad (media do gradiente central ao quadrado) - mesma definicao do repo
"""
from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

DIR = Path(__file__).resolve().parent
DADOS = DIR / "dados"
DADOS.mkdir(exist_ok=True)

# Limiares. Os de aceitacao (nitidez/brilho/saturacao) sao RELATIVOS a referencia capturada neste
# setup. Os de tilt seguem PROVISORIOS (sem fonte primaria nem calibracao): servem como parametro de
# ajuste, nao como criterio de aceitacao publicado.
SCHEMA_METRICAS = 2   # sobe quando a definicao de alguma metrica muda (invalida referencias antigas)

LIMIARES_PADRAO = {
    "diff_fundo": 18,            # piso do limiar adaptativo (diferenca media do cenario)
    "k_mad": 6.0,                # sensibilidade adaptativa: mediana + k*MAD da diferenca
    "area_min": 0.01,            # fracao minima da ROI que a silhueta precisa ocupar
    "area_max": 0.85,            # dentro da ROI (nao do quadro): garrafa nunca enche a janela
    "aspecto_min": 1.2,         # garrafa em pe: altura/largura plausivel
    "aspecto_max": 9.0,
    "topo_rel_max": 1.30,        # topo da silhueta vs largura tipica: acima disso a mascara esta errada
    "area_razao_min": 0.5,       # area da silhueta vs referencia: fora disso nao e comparavel
    "area_razao_max": 2.0,
    # desvio de estrutura no anel da ROI. Medido em 5 pares reais: mesma cena 0,273/0,356/0,424;
    # cena diferente 0,563/0,709.
    "estrutura_max": 0.50,
    "altura_min_frac": 0.15,     # silhueta menor que isto da altura do quadro: nao ha garrafa
    "nitidez_rel": 0.50,         # nitidez minima como fracao da nitidez da referencia
    "brilho_tol_rel": 0.35,      # |brilho - brilho_ref| / brilho_ref
    "saturado_tol_rel": 0.01,    # saturado ate saturado_ref + 1 p.p.
    "iou_ok": 0.97,              # silhueta igual a da referencia: aprovado
    "queda_topo_min": 0.06,      # topo da silhueta comecando mais baixo: tampa ausente
    "dif_topo_min": 0.50,        # fracao da diferenca concentrada no topo
    "dif_corpo_max": 0.35,       # ... e no corpo
    "sobra_baixo_max": 0.15,    # silhueta estendendo abaixo disso: item fora de posicao
    "tilt_incerto_graus": 2.0,   # zona cinzenta -> inconclusivo (PROVISORIO)
    "tilt_reprova_graus": 5.0,   # acima disto: tampa torta (PROVISORIO)
    "deformidade_frac": 0.10,    # desvio de perfil acima disto: deformidade provavel
}


def limiares() -> dict:
    arq = DADOS / "limiares.json"
    if arq.exists():
        try:
            do_arquivo = json.loads(arq.read_text())
            # so chaves conhecidas: arquivo com chave inventada nao pode poluir os limiares em uso
            return {**LIMIARES_PADRAO, **{k: float(v) for k, v in do_arquivo.items()
                                          if k in LIMIARES_PADRAO}}
        except Exception:
            pass
    return dict(LIMIARES_PADRAO)


def salvar_limiares(novos: dict) -> dict:
    """Aplica os limiares conhecidos. Chave desconhecida ou valor invalido e REPORTADO, nao ignorado."""
    atuais = limiares()
    ignorados: dict[str, str] = {}
    for k, v in (novos or {}).items():
        if k not in atuais:
            ignorados[k] = "limiar desconhecido"
            continue
        if v is None or v == "":
            continue
        try:
            atuais[k] = float(v)
        except (TypeError, ValueError):
            ignorados[k] = f"valor invalido: {v!r}"
    (DADOS / "limiares.json").write_text(json.dumps(atuais, indent=1))
    atuais["_ignorados"] = ignorados
    return atuais


# ---------------------------------------------------------------- camera (MJPEG continua)

class Camera:
    """Dona unica da camera: mantem um rpicam-vid rodando e guarda o ultimo frame JPEG."""

    def __init__(self, largura=1296, altura=972, fps=12, qualidade=80):
        self.largura, self.altura, self.fps, self.qualidade = largura, altura, fps, qualidade
        self._frame: bytes | None = None
        self._ts = 0.0
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._erro: str | None = None
        self._thread: threading.Thread | None = None

    def iniciar(self):
        if self._proc is not None:
            return
        cmd = ["rpicam-vid", "-t", "0", "--codec", "mjpeg", "--width", str(self.largura),
               "--height", str(self.altura), "--framerate", str(self.fps),
               "--quality", str(self.qualidade), "--nopreview", "-o", "-"]
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self._thread = threading.Thread(target=self._ler, name="mjpeg", daemon=True)
        self._thread.start()

    def _ler(self):
        buf = b""
        stream = self._proc.stdout
        while True:
            pedaco = stream.read(65536)
            if not pedaco:
                self._erro = "stream da camera terminou"
                return
            buf += pedaco
            while True:
                i = buf.find(b"\xff\xd8\xff")
                j = buf.find(b"\xff\xd9", i + 3) if i >= 0 else -1
                if i < 0 or j < 0:
                    break
                jpeg = buf[i:j + 2]
                buf = buf[j + 2:]
                with self._lock:
                    self._frame = jpeg
                    self._ts = time.time()

    def ultimo(self) -> tuple[bytes | None, float]:
        with self._lock:
            return self._frame, self._ts

    def esperar_frame(self, timeout=6.0) -> bytes | None:
        limite = time.time() + timeout
        while time.time() < limite:
            f, _ = self.ultimo()
            if f:
                return f
            time.sleep(0.15)
        return None

    @property
    def erro(self):
        return self._erro

    def parar(self):
        if self._proc:
            self._proc.terminate()
            self._proc = None


# ---------------------------------------------------------------- ROI fixa do rig

#: Janela de captura em fracao do quadro. Com a camera fixa, a garrafa tem posicao conhecida:
#: medir dentro desta janela e o que torna a segmentacao estavel (o resto do quadro -- parede,
#: cabos, sombra -- deixa de entrar na conta).
ROI_PADRAO = (0.0, 0.0, 1.0, 1.0)   # quadro inteiro por padrao; a ROI e ferramenta de
                                    # ajuste para cena poluida (nao melhora a mascara sozinha)


def roi_atual() -> tuple[float, float, float, float]:
    arq = DADOS / "roi.json"
    if arq.exists():
        try:
            r = json.loads(arq.read_text())
            return (float(r["x0"]), float(r["y0"]), float(r["x1"]), float(r["y1"]))
        except Exception:
            pass
    return ROI_PADRAO


def salvar_roi(x0, y0, x1, y1) -> tuple[float, float, float, float]:
    x0, x1 = sorted((float(x0), float(x1)))
    y0, y1 = sorted((float(y0), float(y1)))
    x0, x1 = max(0.0, x0), min(1.0, x1)
    y0, y1 = max(0.0, y0), min(1.0, y1)
    if x1 - x0 < 0.1 or y1 - y0 < 0.1:
        raise ValueError("ROI pequena demais")
    (DADOS / "roi.json").write_text(json.dumps({"x0": x0, "y0": y0, "x1": x1, "y1": y1}, indent=1))
    return (x0, y0, x1, y1)


def roi_px(shape, roi_rel) -> tuple[int, int, int, int]:
    h, w = shape[:2]
    x0, y0, x1, y1 = roi_rel
    return (max(0, int(w * x0)), max(0, int(h * y0)),
            min(w, int(w * x1)), min(h, int(h * y1)))


def _otsu(g: np.ndarray) -> float:
    """Limiar de Otsu por histograma (numpy puro). O valor e o INDICE do limiar:
    lado escuro = g <= limiar, lado claro = g > limiar."""
    hist, _ = np.histogram(g.ravel(), bins=256, range=(0, 256))
    p = hist.astype(np.float64) / max(1, g.size)
    omega = np.cumsum(p)
    mu = np.cumsum(p * np.arange(256))
    mu_t = mu[-1]
    denom = omega * (1.0 - omega)
    variancia = np.where(denom > 1e-12, (mu_t * omega - mu) ** 2 / np.maximum(denom, 1e-12), 0.0)
    return float(np.argmax(variancia))


def _dilatar(m: np.ndarray, px: int = 12) -> np.ndarray:
    """Engorda a mascara para separar objeto de fundo (k=2*px+1 tem de ser impar no MaxFilter)."""
    k = 2 * max(1, px) + 1
    im = Image.fromarray((m.astype(np.uint8) * 255), "L").filter(ImageFilter.MaxFilter(k))
    return np.asarray(im) > 127


def zona_de_fundo(shape, mascara_obj: np.ndarray | None) -> np.ndarray:
    """Onde a checagem de cena deve olhar: FORA do objeto.

    Com a silhueta da referencia, a zona de fundo e o complemento dela (dilatado). Sem ela, usa a
    borda do quadro. Nunca usa a borda da ROI: quando a ROI esta apertada no objeto, a borda cai
    DENTRO da garrafa e qualquer variacao dela vira "cena mudou" (foi o que travou o fluxo do usuario).
    """
    h, w = shape[:2]
    if mascara_obj is not None and mascara_obj.shape[:2] == (h, w) and mascara_obj.any():
        return ~_dilatar(mascara_obj, 14)
    return _anel(shape, 0.10)


def _anel(shape, margem: float = 0.15) -> np.ndarray:
    """Banda externa da ROI (deve ser FUNDO nas duas capturas): sonda de cena/camera mudada."""
    h, w = shape[:2]
    m = np.ones((h, w), bool)
    dy, dx = max(2, int(h * margem)), max(2, int(w * margem))
    m[dy:h - dy, dx:w - dx] = False
    return m


# ---------------------------------------------------------------- metricas

def _para_cinza(img: np.ndarray) -> np.ndarray:
    return (0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]).astype(np.uint8)


def nitidez(img: np.ndarray) -> float:
    """Tenengrad: MEDIA do gradiente central ao quadrado. Mesma definicao de
    `poc08_preproc.tenengrad` (diferencas centrais em numpy, media simples) -- o numero e comparavel
    com o que o projeto ja mediu, e nao um valor de outra metrica."""
    g = _para_cinza(img).astype(np.float32)
    gx = np.zeros_like(g)
    gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    gy[1:-1, :] = g[2:, :] - g[:-2, :]
    return float(np.mean(gx * gx + gy * gy))


def _mediana3(m: np.ndarray) -> np.ndarray:
    im = Image.fromarray((m.astype(np.uint8) * 255), "L").filter(ImageFilter.MedianFilter(3))
    return np.asarray(im) > 127


def _box_blur(a: np.ndarray, k: int = 5) -> np.ndarray:
    """Media local por imagem integral (sem dependencia): corta ruido sem perder borda grande."""
    h, w = a.shape
    ii = np.pad(np.cumsum(np.cumsum(a, 0), 1), ((1, 0), (1, 0)))
    r = k // 2
    y0 = np.clip(np.arange(h) - r, 0, h)
    y1 = np.clip(np.arange(h) + r + 1, 0, h)
    x0 = np.clip(np.arange(w) - r, 0, w)
    x1 = np.clip(np.arange(w) + r + 1, 0, w)
    soma = (ii[np.ix_(y1, x1)] - ii[np.ix_(y0, x1)] - ii[np.ix_(y1, x0)] + ii[np.ix_(y0, x0)])
    area = (y1 - y0)[:, None] * (x1 - x0)[None, :]
    return (soma / np.maximum(area, 1)).astype(np.float32)


def _maior_componente(m: np.ndarray, passo: int = 8) -> np.ndarray:
    """Mantem a MAIOR componente conexa (4-vizinhos) da mascara.

    A diferenca contra o fundo deixa fragmentos (cabos, sombra, reflexo). Medir a caixa de todos
    eles mistura objetos diferentes; rotular em resolucao reduzida e devolver o vencedor para o
    tamanho original e barato e resolve isso.
    """
    h, w = m.shape
    pequena = m[::passo, ::passo]
    rot = (np.arange(pequena.size).reshape(pequena.shape) + 1) * pequena
    # a propagacao de rotulo avanca 1 celula por iteracao: o limite tem de cobrir ~2x a dimensao,
    # senao a componente fica TRUNCADA (foi o que gerou tilt falso de -26 graus numa garrafa reta)
    for _ in range(600):
        novo = rot.copy()
        novo[1:, :] = np.maximum(novo[1:, :], rot[:-1, :])
        novo[:-1, :] = np.maximum(novo[:-1, :], rot[1:, :])
        novo[:, 1:] = np.maximum(novo[:, 1:], rot[:, :-1])
        novo[:, :-1] = np.maximum(novo[:, :-1], rot[:, 1:])
        novo *= pequena
        if np.array_equal(novo, rot):
            break
        rot = novo
    if not rot.any():
        return m
    rotulos, contagem = np.unique(rot[rot > 0], return_counts=True)
    vencedor = int(rotulos[np.argmax(contagem)])
    ys, xs = np.nonzero(rot == vencedor)
    # usa a CAIXA da componente (nao o bloco ampliado): o corte em blocos aparava o topo da garrafa
    # e o tilt saia falso. A borda fina continua vindo da mascara em resolucao cheia.
    y0 = max(0, int(ys.min()) * passo - passo)
    y1 = min(h, (int(ys.max()) + 1) * passo + passo)
    x0 = max(0, int(xs.min()) * passo - passo)
    x1 = min(w, (int(xs.max()) + 1) * passo + passo)
    fora = np.zeros_like(m)
    fora[y0:y1, x0:x1] = True
    return m & fora


def _ajuste_afim(img: np.ndarray, fundo: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ganho e offset por canal que melhor alinham `fundo` a `img` nos pixels de FUNDO.

    Estimar pela estatistica do quadro inteiro nao serve: a propria garrafa (objeto escuro grande)
    desloca mediana/percentis e as duas imagens passam a normalizar em escalas diferentes -- foi o
    que fez o quadro inteiro virar "garrafa". Aqui o ajuste e feito nos pixels que provavelmente
    sao cenario (metade com menor residuo inicial), em duas passadas.
    """
    a = img.astype(np.float32)
    b = fundo.astype(np.float32)

    def normalizado(x):
        med = np.median(x, axis=(0, 1), keepdims=True)
        faixa = (np.percentile(x, 90, axis=(0, 1), keepdims=True)
                 - np.percentile(x, 10, axis=(0, 1), keepdims=True))
        return (x - med) / np.maximum(faixa, 1.0)

    r = np.abs(normalizado(a) - normalizado(b)).max(axis=2)
    ganho = np.ones(3, np.float32)
    offset = np.zeros(3, np.float32)
    for _ in range(2):
        corte = float(np.percentile(r, 50))
        sel = r <= corte
        if sel.mean() < 0.05:          # nada de cenario comum: mantem a estimativa anterior
            break
        for c in range(3):
            x = b[:, :, c][sel].astype(np.float64)
            y = a[:, :, c][sel].astype(np.float64)
            if x.size < 100 or x.std() < 1e-6:
                continue
            g = float(np.cov(x, y, bias=True)[0, 1] / x.var())
            ganho[c] = g
            offset[c] = float(y.mean() - g * x.mean())
        r = np.abs(a - (b * ganho + offset)).max(axis=2)
    return ganho, offset


def _estrutura(img: np.ndarray) -> np.ndarray:
    """Magnitude de gradiente suavizada e normalizada pela propria media: mede ESTRUTURA da cena.

    Um ganho de exposicao multiplica o gradiente por uma constante; dividir pela media do gradiente
    remove isso (invariante). Duas cenas diferentes tem estrutura diferente mesmo com brilho igual.
    """
    g = _para_cinza(img).astype(np.float32)
    gx = np.zeros_like(g)
    gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    gy[1:-1, :] = g[2:, :] - g[:-2, :]
    mag = _box_blur(np.sqrt(gx * gx + gy * gy), 9)
    return mag / max(1e-6, float(mag.mean()))


def descobrir_objeto(img: np.ndarray, fundo: np.ndarray, lim: dict
                     ) -> tuple[tuple[float, float, float, float] | None, str | None]:
    """Procura a garrafa no QUADRO INTEIRO e devolve a caixa dela (DIAGNOSTICO).

    NAO e mais usado para apertar a ROI de medicao: medir so dentro de uma caixa colada no objeto
    jogou a faixa de fundo para dentro da garrafa e produziu "cena mudou" em cena parada. A ROI
    segue disponivel como ferramenta manual (pagina) e o padrao e o quadro inteiro.
    """
    if img.shape != fundo.shape:
        return None, "tamanho_diferente_do_fundo"
    ganho, offset = _ajuste_afim(img, fundo)
    dif = np.abs(img.astype(np.float32) - (fundo.astype(np.float32) * ganho + offset)).max(axis=2)
    dif_suave = _box_blur(dif, 5)
    mediana = float(np.median(dif_suave))
    mad = float(np.median(np.abs(dif_suave - mediana))) * 1.4826
    limiar = max(float(lim["diff_fundo"]), mediana + float(lim["k_mad"]) * max(mad, 1.0))
    m = dif_suave > limiar
    if m.sum() < 200:
        return None, "sem_silhueta"
    m = _maior_componente(_mediana3(_mediana3(m)))
    if m.sum() < 200:
        return None, "sem_silhueta"
    ys, xs = np.nonzero(m)
    h0 = int(ys.max() - ys.min() + 1)
    w0 = int(xs.max() - xs.min() + 1)
    if not (float(lim["aspecto_min"]) <= h0 / max(1.0, w0) <= float(lim["aspecto_max"])):
        return None, f"objeto_nao_parece_garrafa (aspecto {h0/max(1.0,w0):.2f})"
    H, W = img.shape[:2]
    margem = 0.35
    x0 = max(0.0, (xs.min() - margem * w0) / W)
    x1 = min(1.0, (xs.max() + margem * w0) / W)
    y0 = max(0.0, (ys.min() - margem * h0) / H)
    y1 = min(1.0, (ys.max() + margem * h0) / H)
    if (x1 - x0) < 0.08 or (y1 - y0) < 0.08:
        return None, "roi_derivada_pequena_demais"
    return (round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)), None


def mascara_garrafa(img: np.ndarray, fundo: np.ndarray | None, lim: dict,
                    roi_rel=None, mascara_ref: np.ndarray | None = None
                    ) -> tuple[np.ndarray | None, str | None]:
    """Silhueta do objeto, com duas vias deterministicas:

      1. diferenca contra o fundo, com offset e ganho ajustados nos PIXELS DE FUNDO (duas passadas);
      2. Otsu na janela, quando nao ha fundo utilizavel ou quando a diferenca degenera.
    A janela (ROI) pode recortar o quadro para excluir parede/cabos -- ela e ferramenta de ajuste,
    nao um requisito: o padrao e o quadro inteiro, que foi o que se mostrou estavel nas medidas.
    """
    if fundo is not None and img.shape != fundo.shape:
        return None, "tamanho_diferente_do_fundo"

    roi_rel = roi_rel or roi_atual()
    x0, y0, x1, y1 = roi_px(img.shape, roi_rel)
    if x1 - x0 < 40 or y1 - y0 < 40:
        return None, "roi_pequena_demais"
    a = img[y0:y1, x0:x1]
    b = None if fundo is None else fundo[y0:y1, x0:x1]

    # cena trocada / camera movida: medido na ZONA DE FUNDO (fora da garrafa da referencia)
    if b is not None:
        zona = zona_de_fundo(img.shape, mascara_ref)[y0:y1, x0:x1]
        if zona.any():
            desvio = float(np.median(np.abs(_estrutura(a) - _estrutura(b))[zona]))
            if desvio > float(lim["estrutura_max"]):
                return None, "cena_diferente_do_fundo"

    m = None
    if b is not None:
        ganho, offset = _ajuste_afim(a, b)
        dif = np.abs(a.astype(np.float32) - (b.astype(np.float32) * ganho + offset)).max(axis=2)
        dif_suave = _box_blur(dif, 5)
        mediana = float(np.median(dif_suave))
        mad = float(np.median(np.abs(dif_suave - mediana))) * 1.4826
        limiar = max(float(lim["diff_fundo"]), mediana + float(lim["k_mad"]) * max(mad, 1.0))
        m = dif_suave > limiar
        if m.mean() > float(lim["area_max"]):
            m = None                     # diff degenerou: cai para o Otsu abaixo

    if m is None or m.sum() < 200:
        g = _para_cinza(a).astype(np.uint8)
        t_otsu = _otsu(g)
        # Otsu devolve o indice do limiar: lado escuro = g <= t, lado claro = g > t (com >= o
        # deslocamento de um nivel jogava tudo para o lado claro e a mascara saia VAZIA)
        claro = g > t_otsu
        # o objeto e o lado MENOR (a garrafa ocupa menos que o fundo dentro da janela)
        m = (g <= t_otsu) if claro.mean() > 0.5 else (g > t_otsu)
        if m.sum() < 200:
            return None, "sem_silhueta"

    m = _mediana3(_mediana3(m))
    m = _maior_componente(m)
    if m.sum() < 200:
        return None, "sem_silhueta"

    frac_area = float(m.mean())
    if frac_area > float(lim["area_max"]):
        return None, "objeto_grande_demais"
    if frac_area < float(lim["area_min"]):
        return None, "objeto_pequeno_demais"
    ys0, xs0 = np.nonzero(m)
    altura0 = ys0.max() - ys0.min() + 1
    largura0 = xs0.max() - xs0.min() + 1
    if not (float(lim["aspecto_min"]) <= altura0 / max(1.0, largura0) <= float(lim["aspecto_max"])):
        return None, "objeto_nao_parece_garrafa"

    # objeto cortado pela janela: se a mascara encosta muito na borda da ROI (e a ROI nao e o quadro
    # inteiro), a medicao esta vendo um PEDACO da garrafa -- a mensagem diz o que fazer
    roi_recortada = (x1 - x0) < img.shape[1] or (y1 - y0) < img.shape[0]
    borda_px = int(m[0, :].sum() + m[-1, :].sum() + m[:, 0].sum() + m[:, -1].sum())
    if roi_recortada and borda_px > 0.10 * float(m.sum()):
        return None, "objeto_cortado_pela_roi"

    # devolve em coordenadas do quadro cheio, com zeros fora da ROI
    cheia = np.zeros(img.shape[:2], bool)
    cheia[y0:y1, x0:x1] = m
    return cheia, None


def medir(img: np.ndarray, fundo: np.ndarray | None, lim: dict, roi_rel=None,
          mascara_ref: np.ndarray | None = None) -> dict:
    """Mede a garrafa na imagem. ok=False quando nao ha silhueta utilizavel (com o motivo)."""
    m, motivo = mascara_garrafa(img, fundo, lim, roi_rel, mascara_ref)
    if m is None:
        return {"ok": False, "motivo": motivo}
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    altura = y1 - y0 + 1
    largura_bbox = x1 - x0 + 1
    larguras_linha = m[y0:y1 + 1, x0:x1 + 1].sum(axis=1)
    validas = larguras_linha[larguras_linha > 0]
    largura_mediana = float(np.median(validas)) if validas.size else float(largura_bbox)
    escala = max(1.0, largura_mediana)
    perfil = larguras_linha / escala

    frac_altura = altura / float(m.shape[0])
    n_banda = max(3, int(0.15 * altura))
    largura_topo = float(perfil[:n_banda].max())
    largura_ombro = float(perfil[: max(2, altura // 2)].max())

    # invariante geometrico: garrafa em pe nao tem o TOPO mais largo que o corpo. Se o topo da
    # silhueta e muito mais largo, a mascara pegou fundo/objeto errado -> nao mede, avisa.
    if largura_topo > float(lim["topo_rel_max"]) * max(1e-6, float(np.median(perfil))):
        return {"ok": False, "motivo": "silhueta_inconsistente_topo_mais_largo_que_o_corpo"}

    tilt = 0.0
    faixa = m[y0:y0 + n_banda, x0:x1 + 1]
    linhas_y, centros = [], []
    for i in range(faixa.shape[0]):
        idx = np.nonzero(faixa[i])[0]
        if idx.size >= 2:
            linhas_y.append(i)
            centros.append(float(idx.mean()))
    if len(linhas_y) >= 4:
        tilt = float(np.degrees(np.arctan(np.polyfit(linhas_y, centros, 1)[0])))

    mf = metricas_frame(img)
    return {
        "ok": True,
        "mascara": m,
        "altura_px": altura,
        "largura_px": largura_bbox,
        "largura_mediana_px": round(largura_mediana, 1),
        "altura_rel": round(altura / escala, 4),
        "frac_altura_quadro": round(frac_altura, 4),
        "frac_area": round(float(m.mean()), 4),
        "largura_topo_rel": round(largura_topo, 4),
        "largura_ombro_rel": round(largura_ombro, 4),
        "tilt_tampa_graus": round(tilt, 2),
        "perfil": [round(float(v), 4) for v in perfil],
        "nitidez": mf["nitidez"],
        "brilho": mf["brilho"],
        "saturado": mf["saturado"],
        "bbox": [x0, y0, x1, y1],
    }


# ---------------------------------------------------------------- comparacao direta de silhuetas

def salvar_mascara(m: np.ndarray, nome: str = "referencia_mascara.png") -> None:
    Image.fromarray((m.astype(np.uint8) * 255), "L").convert("1").save(DADOS / nome)


def carregar_mascara(nome: str = "referencia_mascara.png") -> np.ndarray | None:
    arq = DADOS / nome
    if not arq.exists():
        return None
    try:
        a = np.asarray(Image.open(arq).convert("L"))
        return a > 127
    except Exception:
        return None


def comparar_mascaras(m_item: np.ndarray, m_ref: np.ndarray) -> dict:
    """Compara a silhueta do item com a da garrafa boa: o teste que responde 'e a mesma coisa?'.

    Medir geometria ABSOLUTA (tilt por ajuste de elipse/centro) e sensivel a erro de mascara e foi
    o que produziu "defeito" em garrafa boa. Comparar as DUAS silhuetas na mesma posicao e estavel:
    se o item e a mesma garrafa, as mascaras coincidem; se mudou, a diferenca diz ONDE mudou.
    """
    inter = int(np.logical_and(m_item, m_ref).sum())
    uniao = int(np.logical_or(m_item, m_ref).sum())
    iou = inter / uniao if uniao else 0.0

    ys_ref, xs_ref = np.nonzero(m_ref)
    ys_it, xs_it = np.nonzero(m_item)
    if ys_ref.size == 0 or ys_it.size == 0:
        return {"ok": False, "motivo": "mascara_vazia"}
    y0r, y1r = int(ys_ref.min()), int(ys_ref.max())
    y0i, y1i = int(ys_it.min()), int(ys_it.max())
    altura_ref = max(1, y1r - y0r + 1)
    altura_item = max(1, y1i - y0i + 1)

    # 1) o topo sumiu? (queda do inicio da silhueta, em fracao da altura da referencia)
    queda_topo = max(0.0, (y0i - y0r) / altura_ref)
    sobra_baixo = max(0.0, (y1i - y1r) / altura_ref)

    # 2) inclinacao DIFERENCIAL do topo: deslocamento lateral do centro, linha a linha, relativo
    banda = max(3, int(0.15 * altura_ref))
    linhas, desvios = [], []
    for y in range(y0r, y0r + banda):
        if y >= m_ref.shape[0] or y >= m_item.shape[0]:
            break
        ir = np.nonzero(m_ref[y])[0]
        ii = np.nonzero(m_item[y])[0]
        if ir.size >= 2 and ii.size >= 2:
            linhas.append(y - y0r)
            desvios.append(float(ii.mean() - ir.mean()))
    tilt_dif = 0.0
    if len(linhas) >= 4:
        tilt_dif = float(np.degrees(np.arctan(np.polyfit(linhas, desvios, 1)[0])))

    # 3) onde estao os pixels que diferem (topo x corpo), em fracao da altura
    so_item = np.logical_and(m_item, ~m_ref)
    so_ref = np.logical_and(m_ref, ~m_item)
    dif = np.logical_or(so_item, so_ref)
    onde = None
    peso_topo = 0.0
    if dif.any():
        ys_d = np.nonzero(dif)[0]
        rel = (ys_d - y0r) / altura_ref
        onde = float(np.median(rel))
        peso_topo = float((rel < 0.35).mean())
    return {"ok": True, "iou": round(iou, 4), "queda_topo": round(queda_topo, 4),
            "sobra_baixo": round(sobra_baixo, 4), "tilt_diferencial_graus": round(tilt_dif, 2),
            "onde_dif": None if onde is None else round(onde, 3),
            "frac_dif_no_topo": round(peso_topo, 3),
            "altura_razao": round(altura_item / altura_ref, 4),
            "area_item": int(m_item.sum()), "area_ref": int(m_ref.sum())}


def comparar_com_referencia(m: dict, ref: dict) -> dict:
    """Fallback: compara o perfil de largura com a referencia (usado quando nao ha mascara salva)."""
    p, pr = np.asarray(m["perfil"]), np.asarray(ref["perfil"])
    if min(len(p), len(pr)) < 8:
        return {"ok": False, "motivo": "perfil_curto"}
    pp = np.interp(np.linspace(0, 1, 64), np.linspace(0, 1, len(p)), p)
    rr = np.interp(np.linspace(0, 1, 64), np.linspace(0, 1, len(pr)), pr)
    dif = pp - rr
    i = int(np.argmax(np.abs(dif)))
    return {"ok": True, "desvio_corpo": round(float(np.abs(dif).max()), 4),
            "desvio_onde": round(i / 63.0, 3), "assina": float(dif[i]) > 0}


def qualidade(med: dict, ref: dict, lim: dict, apenas_foco: bool = False) -> list[str]:
    """Criterios de captura DERIVADOS DA REFERENCIA (nada de numero absoluto inventado)."""
    saida = []
    piso = float(lim["nitidez_rel"]) * float(ref["nitidez"])
    if med["nitidez"] < piso:
        saida.append(f"foco abaixo do padrao da referencia (nitidez {med['nitidez']:.0f} < {piso:.0f})")
    if apenas_foco:
        return saida
    tol = float(lim["brilho_tol_rel"]) * max(1.0, float(ref["brilho"]))
    if abs(med["brilho"] - ref["brilho"]) > tol:
        saida.append(f"exposicao diferente da referencia (brilho {med['brilho']:.0f} vs {ref['brilho']:.0f})")
    limite_sat = float(ref["saturado"]) + float(lim["saturado_tol_rel"])
    if med["saturado"] > limite_sat:
        saida.append(f"pixels estourados ({med['saturado']*100:.1f}% vs {ref['saturado']*100:.1f}% na referencia)")
    return saida


def metricas_frame(img: np.ndarray) -> dict:
    """Metricas de captura que NAO dependem de achar a garrafa (foco, exposicao, estouro)."""
    g = _para_cinza(img.astype(np.int16)).astype(np.float32)
    return {"nitidez": round(nitidez(img), 1), "brilho": round(float(g.mean()), 1),
            "saturado": round(float(((g <= 3) | (g >= 252)).mean()), 4)}


def decidir(med: dict, ref: dict | None, lim: dict, frame: dict | None = None,
            mascara_ref: np.ndarray | None = None) -> dict:
    """Veredito do item, com o motivo explicito de cada resultado.

    A classe de defeito sai da COMPARACAO das silhuetas (item x garrafa boa), nao de geometria
    absoluta: e o que evita "defeito" em garrafa boa na mesma posicao. Quando nao ha mascara da
    referencia (referencia antiga), cai para a comparacao de perfil.
    """
    if not med.get("ok"):
        motivo = med.get("motivo", "sem_silhueta")
        if ref is not None and frame is not None:
            falhas_foco = qualidade(frame, ref, lim, apenas_foco=True)
            if falhas_foco:
                return {"veredito": "inconclusivo", "classe": "inconclusivo",
                        "motivos": falhas_foco, "confianca": None}
        mensagens = {
            "cena_diferente_do_fundo": (
                "cena_mudou",
                "a imagem nao bate com o fundo salvo (camera ou cena mudaram) - recapture o fundo"),
            "silhueta_inconsistente_topo_mais_largo_que_o_corpo": (
                "inconclusivo",
                "a silhueta nao tem forma de garrafa (topo mais largo que o corpo): "
                "a segmentacao pegou fundo/objeto errado - ajuste a ROI ou a luz"),
            "sem_silhueta": ("sem_garrafa", "sem_silhueta"),
            "objeto_pequeno_demais": ("sem_garrafa", "objeto pequeno demais no quadro"),
            "objeto_nao_parece_garrafa": ("sem_garrafa", "a silhueta nao tem forma de garrafa"),
            "objeto_cortado_pela_roi": (
                "inconclusivo",
                "a garrafa esta cortada pela janela de medicao (ROI): aumente a janela ou "
                "volte para o quadro inteiro na secao ROI desta pagina"),
        }
        ver, msg = mensagens.get(motivo, ("inconclusivo", motivo))
        return {"veredito": ver, "classe": ver, "motivos": [msg], "confianca": None}

    if med["frac_altura_quadro"] < lim["altura_min_frac"]:
        return {"veredito": "sem_garrafa", "classe": "sem_garrafa",
                "motivos": ["objeto pequeno demais no quadro"], "confianca": None}

    if ref is None:
        return {"veredito": "sem_referencia", "classe": "sem_referencia",
                "motivos": ["capture uma garrafa boa como referencia"], "confianca": None,
                "medidas_para_referencia": True}

    motivos_q = qualidade(frame or med, ref, lim)
    if motivos_q:
        return {"veredito": "inconclusivo", "classe": "inconclusivo",
                "motivos": motivos_q, "confianca": None}

    # --- comparacao direta de silhuetas (preferida) ---
    m_item = med.get("mascara")
    if mascara_ref is not None and m_item is not None and m_item.shape == mascara_ref.shape:
        c = comparar_mascaras(m_item, mascara_ref)
        if c.get("ok"):
            iou = c["iou"]
            tilt = abs(c["tilt_diferencial_graus"])
            dif_topo = c["frac_dif_no_topo"]

            # 1) tampa torta: inclinacao DIFERENCIAL do topo em relacao a referencia
            if tilt >= float(lim["tilt_reprova_graus"]):
                return {"veredito": "defeito", "classe": "tampa_mal_rosqueada",
                        "motivos": [f"o topo esta {tilt:.1f} graus fora do eixo da referencia "
                                    f"(limite atual {lim['tilt_reprova_graus']:.1f} - provisorio)"],
                        "confianca": round(min(1.0, tilt / (lim["tilt_reprova_graus"] * 3)), 3)}

            # 2) tampa ausente: o topo da silhueta comeca mais abaixo e a diferenca esta no topo
            if c["queda_topo"] >= float(lim["queda_topo_min"]) and dif_topo >= float(lim["dif_topo_min"]):
                return {"veredito": "defeito", "classe": "tampa_ausente",
                        "motivos": [f"o topo comeca {c['queda_topo']*100:.0f}% mais baixo que a "
                                    f"referencia (altura {c['altura_razao']*100:.0f}% da referencia)"],
                        "confianca": round(min(1.0, c["queda_topo"] * 5), 3)}

            # 3) silhueta praticamente igual a da garrafa boa
            if iou >= float(lim["iou_ok"]):
                return {"veredito": "ok", "classe": "normal",
                        "motivos": [f"mesma silhueta da referencia (coincidencia {iou*100:.1f}%, "
                                    f"topo dentro de {tilt:.1f} grau)"],
                        "confianca": round(min(1.0, iou), 3)}

            # 3b) silhueta deslocada para baixo: o objeto nao esta na mesma altura da referencia
            if c["sobra_baixo"] >= float(lim["sobra_baixo_max"]):
                return {"veredito": "inconclusivo", "classe": "inconclusivo",
                        "motivos": [f"a silhueta se estende {c['sobra_baixo']*100:.0f}% abaixo da "
                                    f"referencia: o item nao esta na mesma posicao"],
                        "confianca": None}

            # 4) mudou fora do topo: corpo
            if dif_topo <= float(lim["dif_corpo_max"]):
                parte = "superior" if (c["onde_dif"] or 0) < 0.55 else "inferior"
                return {"veredito": "defeito", "classe": "deformidade",
                        "motivos": [f"o corpo difere da referencia na parte {parte} "
                                    f"(coincidencia {iou*100:.1f}%)"],
                        "confianca": round(max(0.0, 1.0 - iou), 3)}

            return {"veredito": "inconclusivo", "classe": "inconclusivo",
                    "motivos": [f"a silhueta difere da referencia de um jeito que a regra ainda nao "
                                f"classifica (coincidencia {iou*100:.1f}%, diferenca no topo "
                                f"{dif_topo*100:.0f}%)"], "confianca": None}

    # --- fallback: comparacao de perfil (referencia sem mascara salva) ---
    razao_area = med["frac_area"] / max(1e-9, float(ref.get("frac_area", 0) or 1))
    if "frac_area" in ref and not (float(lim["area_razao_min"]) <= razao_area
                                   <= float(lim["area_razao_max"])):
        return {"veredito": "inconclusivo", "classe": "inconclusivo",
                "motivos": ["silhueta incompativel com a referencia (segmentacao nao isolou o mesmo "
                            "objeto) - revisar enquadramento/luz"], "confianca": None}
    comp = comparar_com_referencia(med, ref)
    if not comp.get("ok"):
        return {"veredito": "inconclusivo", "classe": "inconclusivo",
                "motivos": [comp.get("motivo", "perfil invalido")], "confianca": None}
    razao_altura = med["altura_rel"] / ref["altura_rel"] if ref.get("altura_rel") else 1.0
    if razao_altura < (1.0 - float(lim["queda_topo_min"])) and comp["desvio_onde"] < 0.35:
        return {"veredito": "defeito", "classe": "tampa_ausente",
                "motivos": [f"topo {100*(1-razao_altura):.0f}% mais baixo que a referencia "
                            f"(comparacao de perfil)"],
                "confianca": round(min(1.0, (1 - razao_altura) * 8), 3)}
    if comp["desvio_corpo"] >= float(lim["deformidade_frac"]):
        if comp["desvio_onde"] < 0.35:
            return {"veredito": "defeito", "classe": "tampa_ausente",
                    "motivos": [f"topo fora do padrao em {comp['desvio_corpo']*100:.0f}% da largura"],
                    "confianca": round(min(1.0, comp["desvio_corpo"] * 3), 3)}
        return {"veredito": "defeito", "classe": "deformidade",
                "motivos": [f"perfil do corpo desvia {comp['desvio_corpo']*100:.0f}% da largura"],
                "confianca": round(min(1.0, comp["desvio_corpo"] * 3), 3)}
    confianca_ok = max(0.0, 1.0 - comp["desvio_corpo"] / max(1e-6, lim["deformidade_frac"]))
    return {"veredito": "ok", "classe": "normal",
            "motivos": [f"topo e corpo dentro do padrao da referencia "
                        f"(desvio {comp['desvio_corpo']*100:.1f}%, nitidez {med['nitidez']:.0f})"],
            "confianca": round(confianca_ok, 3)}


# ---------------------------------------------------------------- estado em disco

def salvar_frame(jpeg: bytes, nome: str) -> Path:
    arq = DADOS / nome
    arq.write_bytes(jpeg)
    return arq


def imagem(jpeg: bytes) -> np.ndarray:
    from io import BytesIO
    return np.asarray(Image.open(BytesIO(jpeg)).convert("RGB")).astype(np.int16)
