#!/usr/bin/env python3
"""PoC-03 (demo de conceito): mede o corpo e decide NORMAL / DEFORMIDADE / INCONCLUSIVO.

Conceito demonstrado: a forma do corpo pode ser medida contra uma referencia do proprio rig, e um
desvio aparece como sinal. A demo NAO e a validacao do requisito: e a prova visual de que o metodo
funciona ponta a ponta.

Como funciona (sem segmentar a garrafa inteira, que e transparente):
  1. recorta a ROI do corpo (fracao do quadro: vale em qualquer resolucao);
  2. binariza a ROI e mede a largura da silhueta linha a linha;
  3. normaliza o perfil (100 pontos, largura relativa) -> comparavel entre capturas do mesmo rig;
  4. compara com a banda de referencia (mediana + percentis das capturas normais do rig);
  5. emite veredito, desvio, imagem anotada e JSON.

Uso:
    python demo.py --referencia DIR        # constroi a banda a partir das normais do rig
    python demo.py --imagem FOTO.jpg       # mede UMA foto -> veredito + anotada + json
    python demo.py --avaliar DIR           # roda em lote e imprime a tabela
    python demo.py --capturar [--saida F]  # captura do Pi (rpicam-still) e mede

AVISO DE ESCOPO: capturas de rigs diferentes (outra camera, outra distancia) nao podem ser
comparadas com esta banda. A referencia e a medicao precisam vir do MESMO enquadramento.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROI = (0.05, 0.03, 0.97, 0.97)      # x1, y1, x2, y2 (fracao do quadro): quadro util do rig
N_PONTOS = 100
LIMIAR_AREA_MIN = 0.004             # silhueta minima dentro da ROI (senao: inconclusivo)
VERSAO = "poc03-demo-2"


# ----------------------------------------------------------------- medidas

def recorte_roi(im: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    h, w = im.shape[:2]
    x1, y1, x2, y2 = (int(w * ROI[0]), int(h * ROI[1]), int(w * ROI[2]), int(h * ROI[3]))
    return im[y1:y2, x1:x2], (x1, y1, x2, y2)


def perfil_corpo(im: np.ndarray) -> dict | None:
    """Silhueta do corpo na ROI: perfil de largura por linha (100 pontos), em pixels.

    Sem morfologia: o fechamento morfologico funde a garrafa com a mesa/sombra e quebra a medida.
    """
    roi, caixa = recorte_roi(im)
    if roi.size == 0:
        return None
    g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (7, 7), 0)
    _, b = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contornos, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return None
    c = max(contornos, key=cv2.contourArea)
    h, w = b.shape
    if cv2.contourArea(c) < LIMIAR_AREA_MIN * h * w:
        return None
    mascara = np.zeros_like(b)
    cv2.drawContours(mascara, [c], -1, 255, -1)
    bx, by, bw, bh = cv2.boundingRect(c)
    if bh < 20 or bw < 10:
        return None
    sub = mascara[by:by + bh, bx:bx + bw]
    larg = np.array([int((sub[r] > 0).sum()) for r in range(bh)], dtype="float32")
    if larg.max() <= 0:
        return None
    # descarta o tampo/mesa no fim do perfil: linhas com largura de quadro inteiro nao sao a garrafa
    cheias = np.where(larg > 0.9 * w)[0]
    if len(cheias) and cheias[0] > 0.4 * len(larg):
        larg, bh = larg[:cheias[0]], int(cheias[0])
    if bh < 20:
        return None
    rel = np.interp(np.linspace(0, 1, N_PONTOS), np.linspace(0, 1, bh), larg)
    return {"perfil": rel, "largura_px": int(larg.max()), "altura_px": int(bh),
            "area_rel": float(cv2.contourArea(c) / (h * w)), "caixa": caixa,
            "bbox": (bx, by, bw, bh)}


def desvio(perfil: np.ndarray, ref: np.ndarray) -> float:
    return float(np.mean(np.abs(perfil - ref)) / (ref.mean() + 1e-9))


# ----------------------------------------------------------------- referencia

def construir_referencia(diretorio: Path, saida: Path, padrao: str = "*.jpg") -> dict:
    perfis, usados, falhas = [], [], []
    for f in sorted(diretorio.glob(padrao)):
        m = perfil_corpo(cv2.imread(str(f)))
        if m is None:
            falhas.append(f.name)
            continue
        perfis.append(m["perfil"])
        usados.append(f.name)
    if len(perfis) < 5:
        raise SystemExit("referencia insuficiente: %d capturas validas (minimo 5)" % len(perfis))
    pilha = np.stack(perfis)
    ref = np.median(pilha, axis=0)
    d = np.array([desvio(p, ref) for p in perfis])
    dados = {"versao": VERSAO, "origem": str(diretorio), "padrao": padrao, "n": len(perfis),
             "capturas": usados, "falhas": falhas, "roi": ROI,
             "limiar": float(np.percentile(d, 97.5)), "p50": float(np.median(d)),
             "min": float(d.min()), "max": float(d.max()), "referencia": ref.tolist()}
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=1))
    print("referencia: %d capturas (%d falhas) | desvio p50=%.4f limiar(p97.5)=%.4f" %
          (len(perfis), len(falhas), dados["p50"], dados["limiar"]))
    print("salva em %s" % saida)
    return dados


def carregar_referencia(caminho: Path) -> dict:
    return json.loads(caminho.read_text())


# ----------------------------------------------------------------- decisao + desenho

def decidir(medida: dict | None, ref: dict) -> dict:
    if medida is None:
        return {"classe": "inconclusivo", "motivo": "sem_silhueta_na_roi", "desvio": None}
    d = desvio(medida["perfil"], np.array(ref["referencia"]))
    lim = ref["limiar"]
    if d <= lim:
        classe, motivo = "normal", "dentro_da_banda"
    else:
        classe, motivo = "deformidade", "acima_da_banda"
    return {"classe": classe, "motivo": motivo, "desvio": round(d, 4), "limiar": round(lim, 4)}


CORES = {"normal": (230, 120, 60), "deformidade": (60, 60, 230), "inconclusivo": (60, 180, 230)}
COR_REF = (90, 220, 90)          # referencia sempre verde
ALTURA_PAINEL = 480


def painel_perfil(perfil: np.ndarray, ref: np.ndarray, cor, rotulo_medido: str):
    """Painel do perfil: referencia (verde) x medido (cor do veredito), com eixos."""
    H, W = ALTURA_PAINEL, 520
    p = np.full((H, W, 3), 26, np.uint8)
    x0, y0, xm, ym = 48, 34, W - 16, H - 44
    cv2.line(p, (x0, ym), (xm, ym), (95, 95, 95), 1)
    cv2.line(p, (x0, y0), (x0, ym), (95, 95, 95), 1)
    escala = max(float(np.max(perfil)), float(np.max(ref))) or 1.0

    def pt(i, v):
        return (int(x0 + i / (len(perfil) - 1) * (xm - x0)), int(ym - v / escala * (ym - y0)))

    for frac in (0.25, 0.5, 0.75, 1.0):
        y = int(ym - frac * (ym - y0))
        cv2.line(p, (x0 - 4, y), (x0, y), (95, 95, 95), 1)
        cv2.putText(p, "%.2f" % (frac * escala), (4, y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
    cv2.polylines(p, [np.array([pt(i, v) for i, v in enumerate(ref)], np.int32)], False, COR_REF, 2)
    cv2.polylines(p, [np.array([pt(i, v) for i, v in enumerate(perfil)], np.int32)], False, cor, 3)
    cv2.putText(p, "perfil de largura do corpo (100 pontos, px)", (x0, 22), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (210, 210, 210), 1)
    cv2.putText(p, "verde = referencia do rig", (x0, H - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, COR_REF, 1)
    cv2.putText(p, "traco grosso = %s" % rotulo_medido, (x0, H - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, cor, 1)
    return p


def anotar(im: np.ndarray, medida: dict | None, ref: dict, decisao: dict, destino: Path) -> Path:
    cor = CORES[decisao["classe"]]
    foto = im.copy()
    x1, y1, x2, y2 = medida["caixa"] if medida else (0, 0, im.shape[1], im.shape[0])
    if medida is not None:
        bx, by, bw, bh = medida["bbox"]
        cv2.rectangle(foto, (x1 + bx, y1 + by), (x1 + bx + bw, y1 + by + bh), cor, 2)
        # desenha O QUE FOI MEDIDO: contorno simetrico derivado do perfil (medido x referencia)
        perfil = np.asarray(medida["perfil"], np.float32)
        ref_n = np.asarray(ref["referencia"], np.float32)
        x_centro = x1 + bx + bw // 2
        y_topo = y1 + by

        def contorno_lateral(valores):
            pts = []
            for i, v in enumerate(valores):
                y = y_topo + int(i / (len(valores) - 1) * (bh - 1))
                pts.append((int(x_centro + v / 2), y))
            for i in range(len(valores) - 1, -1, -1):
                y = y_topo + int(i / (len(valores) - 1) * (bh - 1))
                pts.append((int(x_centro - valores[i] / 2), y))
            return np.array(pts, np.int32)

        cv2.polylines(foto, [contorno_lateral(ref_n)], True, COR_REF, 2)
        cv2.polylines(foto, [contorno_lateral(perfil)], True, cor, 2)
        # recorta ao redor da garrafa para a apresentacao ficar legivel
        margem = int(0.12 * max(bw, bh))
        ax1, ay1 = max(0, x1 + bx - margem), max(0, y1 + by - margem)
        ax2, ay2 = min(im.shape[1], x1 + bx + bw + margem), min(im.shape[0], y1 + by + bh + margem)
        foto = foto[ay1:ay2, ax1:ax2]
    texto = "PoC-03 | %s" % decisao["classe"].upper()
    if decisao["desvio"] is not None:
        texto += " | desvio=%.4f  limiar=%.4f" % (decisao["desvio"], decisao["limiar"])
    if decisao["motivo"] != "dentro_da_banda":
        texto += " | %s" % decisao["motivo"]
    faixa = np.full((36, foto.shape[1], 3), 24, np.uint8)
    cv2.putText(faixa, texto, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
    foto = np.vstack([faixa, foto])
    if medida is None:
        mont = foto
    else:
        painel = painel_perfil(np.asarray(medida["perfil"], np.float32),
                               np.asarray(ref["referencia"], np.float32), cor,
                               "medido (%s)" % decisao["classe"])
        alvo = max(foto.shape[0], painel.shape[0])
        def pad(x):
            if x.shape[0] < alvo:
                x = cv2.copyMakeBorder(x, 0, alvo - x.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(26, 26, 26))
            return x
        mont = np.hstack([pad(foto), pad(painel)])
    destino.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino), mont)
    return destino


# ----------------------------------------------------------------- entradas

def avaliar_imagem(caminho: Path, ref: dict, saida_dir: Path | None = None) -> dict:
    im = cv2.imread(str(caminho))
    if im is None:
        return {"arquivo": caminho.name, "classe": "inconclusivo", "motivo": "imagem_ilegivel"}
    medida = perfil_corpo(im)
    decisao = decidir(medida, ref)
    registro = {"arquivo": caminho.name, "resolucao": list(im.shape[:2]), **decisao}
    if saida_dir is not None:
        registro["anotada"] = str(anotar(im, medida, ref, decisao, saida_dir / ("%s_anotada.png" % caminho.stem)))
        (saida_dir / ("%s_resultado.json" % caminho.stem)).write_text(
            json.dumps(registro, ensure_ascii=False, indent=1))
    return registro


def capturar(destino: Path) -> Path:
    if shutil.which("rpicam-still") is None:
        raise SystemExit("rpicam-still nao encontrado: esta demo de captura roda no Raspberry Pi")
    destino.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rpicam-still", "-o", str(destino), "-t", "800", "--width", "1195",
                    "--height", "896", "-n"], check=True)
    return destino


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--referencia", type=Path, help="diretorio com capturas NORMAIS do rig")
    ap.add_argument("--padrao", default="*.jpg", help="glob das capturas da referencia (ex.: 'frame_*.jpg')")
    ap.add_argument("--salvar-referencia", type=Path, default=Path("poc03_referencia.json"))
    ap.add_argument("--ref", type=Path, help="JSON da referencia ja construida")
    ap.add_argument("--imagem", type=Path, help="mede uma foto")
    ap.add_argument("--avaliar", type=Path, help="mede todas as fotos de um diretorio")
    ap.add_argument("--capturar", action="store_true", help="captura do Pi e mede")
    ap.add_argument("--saida", type=Path, default=Path("poc03_saida"), help="diretorio de saida")
    a = ap.parse_args()

    if a.referencia:
        construir_referencia(a.referencia, a.salvar_referencia, a.padrao)
        return 0

    caminho_ref = a.ref or a.salvar_referencia
    if not caminho_ref.exists():
        raise SystemExit("referencia ausente (%s): rode --referencia DIR primeiro" % caminho_ref)
    ref = carregar_referencia(caminho_ref)

    if a.capturar:
        foto = capturar(a.saida / "captura.jpg")
        r = avaliar_imagem(foto, ref, a.saida)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0

    if a.imagem:
        r = avaliar_imagem(a.imagem, ref, a.saida)
        print(" %s -> %s (desvio %s, limiar %s)" % (r["arquivo"], r["classe"].upper(), r.get("desvio"), r.get("limiar")))
        if "anotada" in r:
            print(" anotada: %s" % r["anotada"])
        return 0

    if a.avaliar:
        fotos = sorted(a.avaliar.glob("*.jpg")) + sorted(a.avaliar.glob("*.png"))
        if not fotos:
            raise SystemExit("nenhuma foto em %s" % a.avaliar)
        saida = a.saida / a.avaliar.name
        linhas = [avaliar_imagem(f, ref, saida) for f in fotos]
        contagem = {}
        for r in linhas:
            contagem[r["classe"]] = contagem.get(r["classe"], 0) + 1
        print("%-34s %-14s %8s" % ("arquivo", "classe", "desvio"))
        for r in linhas:
            print("%-34s %-14s %8s" % (r["arquivo"], r["classe"], r.get("desvio")))
        print("\nresumo: %s (n=%d)" % (contagem, len(linhas)))
        resumo = a.saida / ("resumo_%s.json" % a.avaliar.name)
        resumo.write_text(json.dumps({"referencia": str(caminho_ref), "resultados": linhas,
                                      "contagem": contagem}, ensure_ascii=False, indent=1))
        print("resumo: %s" % resumo)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
