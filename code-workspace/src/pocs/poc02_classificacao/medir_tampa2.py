"""Medicao v2 da tampa: caixa apertada no objeto + features relativas ao proprio objeto.

Correcoes em relacao a v1:
 (a) APERTAR a caixa: o box do COCO e frouxo (pega parede). Aqui o objeto e re-segmentado DENTRO do
     box (cor de fundo = moldura do box, maior componente) -> caixa justa. Medidas deixam de ser
     contaminadas por fundo.
 (b) FEATURES no anel/boca, nao na cupula: perfil de LARGURA por linha dentro da caixa justa.
     - largura do topo (tampa/boca) em fracao da largura maxima do objeto
     - degrau tampa->anel (a tampa sobressai do anel quando presente)
     - posicao do alargamento no topo (onde esta a tampa/anel, em fracao da altura)
     - fracao escura no topo (boca aberta)
     - DESVIO DO EIXO: centroide do topo vs centroide do corpo, em fracao da largura
       (assinatura de tampa mal rosqueada, medida no referencial do proprio objeto ->
        a inclinacao da garrafa no quadro se cancela -- o tilt absoluto da v1 nao fazia isso)
 Aposenta o tilt absoluto da elipse (que saiu degenerado: p97,5 = 86,4 graus).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import os

FRACAO_TOPO = 0.25
FRACAO_ALTURA_BOCA = 0.08
TOL_FUNDO = 26.0
MARGEM_CAIXA = 0.02


def apertar_caixa(im, caixa, tol=TOL_FUNDO):
    """Segmenta o objeto DENTRO do box detectado e devolve a caixa justa + a mascara.

    Fundo de referencia: apenas os CANTOS SUPERIORES do box (a garrafa e estreita no topo, entao
    ali ha parede de verdade). A moldura inteira nao serve: o rodape do box pega mesa/sombra e
    contamina o fundo (bug da versao anterior: mascara=box inteiro, perfil constante).
    """
    h, w = im.shape[:2]
    x1 = max(0, min(int(caixa[0]), w - 2))
    y1 = max(0, min(int(caixa[1]), h - 2))
    x2 = max(x1 + 2, min(int(caixa[2]), w))
    y2 = max(y1 + 2, min(int(caixa[3]), h))
    rec = im[y1:y2, x1:x2]
    if rec.size == 0:
        return caixa, None, {"motivo": "recorte_vazio"}
    rb = cv2.GaussianBlur(rec, (5, 5), 0).astype(np.float32)
    H, W = rec.shape[:2]
    ka, kb = max(2, int(H * 0.12)), max(2, int(W * 0.18))
    cantos = np.concatenate([rb[:ka, :kb].reshape(-1, 3), rb[:ka, -kb:].reshape(-1, 3)])
    fundo = np.median(cantos, axis=0)
    dif = np.linalg.norm(rb - fundo, axis=2)
    m = (dif > tol).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return caixa, None, {"motivo": "sem_objeto_no_box"}
    cand = sorted(range(1, n), key=lambda i: -stats[i, 4])
    escolhido = None
    for i in cand:
        x, y, ww, hh, a = stats[i]
        if hh >= 1.2 * ww and a > 0.01 * m.size:
            escolhido = i
            break
    if escolhido is None:
        escolhido = cand[0]
    x, y, ww, hh, a = stats[escolhido]
    if a < 0.15 * m.size:
        return caixa, (lab == escolhido).astype(np.uint8) * 255, {"motivo": "fragmentado", "aceito": False}
    mx, my = int(ww * MARGEM_CAIXA), int(hh * MARGEM_CAIXA)
    justa = [x1 + max(0, x - mx), y1 + max(0, y - my), x1 + min(rec.shape[1], x + ww + mx),
             y1 + min(rec.shape[0], y + hh + my)]
    # a mascara tem de sair no MESMO sistema de coordenadas da caixa justa (bug anterior:
    # ficava no recorte original e, quando o aperto movia a caixa, os indices nao batiam)
    fina = (lab == escolhido).astype(np.uint8) * 255
    ix0 = max(0, justa[0] - x1)
    iy0 = max(0, justa[1] - y1)
    ix1 = min(rec.shape[1], justa[2] - x1)
    iy1 = min(rec.shape[0], justa[3] - y1)
    masc_justa = fina[iy0:iy1, ix0:ix1]
    return justa, masc_justa, {"motivo": "ok", "aceito": True,
                               "area_rel": float(a) / m.size,
                               "fundo": [round(float(v), 1) for v in fundo]}


def features(im, caixa_objeto, caixa_justa, mascara):
    """Features relativas ao proprio objeto, medidas no perfil de largura + inclinacao relativa.

    `mascara` vem no sistema de coordenadas da caixa justa (garantido por apertar_caixa).
    """
    x1, y1, x2, y2 = caixa_justa
    if mascara is None or (mascara > 0).sum() < 50:
        return None
    mi = mascara.copy()
    rec = im[y1:y2, x1:x2]
    if rec.size == 0 or mi.shape[0] != rec.shape[0] or mi.shape[1] != rec.shape[1]:
        return None
    ys, xs = np.where(mi > 0)
    y_topo, y_base = ys.min(), ys.max()
    alt = y_base - y_topo + 1
    larguras, cent, escuros, esq, dir_ = [], [], [], [], []
    g = cv2.cvtColor(rec, cv2.COLOR_BGR2GRAY)
    for r in range(y_topo, y_base + 1):
        cols = np.where(mi[r] > 0)[0]
        if len(cols) == 0:
            larguras.append(0)
            cent.append(np.nan)
            escuros.append(np.nan)
            esq.append(np.nan)
            dir_.append(np.nan)
            continue
        larguras.append(int(cols.max() - cols.min() + 1))
        cent.append(float(np.mean(cols)))
        esq.append(float(cols.min()))
        dir_.append(float(cols.max()))
        linha = g[r, cols.min():cols.max() + 1]
        escuros.append(float((linha < 90).mean()) if linha.size else 0.0)
    L = np.array(larguras, dtype=np.float32)
    larg_max = float(L.max()) if L.size else 0.0
    if larg_max <= 0:
        return None
    n_topo = max(2, int(FRACAO_TOPO * alt))
    n_boca = max(1, int(FRACAO_ALTURA_BOCA * alt))
    n_corpo = max(2, int(0.5 * alt))
    Ltopo = L[:n_topo]
    larg_topo = float(np.median(Ltopo[:max(2, n_boca)]))          # boca/tampa no extremo
    larg_anel = float(np.max(Ltopo))                              # alargamento no topo (anel ou tampa)
    idx_anel = int(np.argmax(Ltopo))
    larg_corpo_med = float(np.median(L[n_topo:n_topo + n_corpo])) if alt > n_topo + n_corpo else larg_max
    c_topo = np.nanmean(np.array(cent[:n_topo], dtype=np.float32))
    c_corpo = np.nanmean(np.array(cent[n_topo:n_topo + n_corpo], dtype=np.float32))
    esc_topo = np.nanmean(np.array(escuros[:n_boca], dtype=np.float32))
    # inclinacao: eixo do corpo (bordas esq/dir no meio do objeto) vs topo da tampa (primeiras linhas)
    def inclinacao(v_esq, v_dir, de, ate):
        a = np.array(v_esq[de:ate], dtype=np.float32)
        b = np.array(v_dir[de:ate], dtype=np.float32)
        yy = np.arange(de, ate, dtype=np.float32)
        ok = ~np.isnan(a) & ~np.isnan(b)
        if ok.sum() < 8:
            return None
        ce = np.polyfit(yy[ok], a[ok], 1)[0]
        cd = np.polyfit(yy[ok], b[ok], 1)[0]
        return float(np.degrees(np.arctan((ce + cd) / 2.0)))
    i0, i1 = int(0.45 * alt), int(0.9 * alt)
    eixo_corpo = inclinacao(esq, dir_, i0, i1)
    # topo da tampa: linha superior da silhueta por coluna, sobre as colunas da faixa de topo
    topo_y = []
    col_ini = max(0, int(larg_max * 0.0))
    for c in range(int(mi[y_topo:y_topo + n_topo].shape[1])):
        col = np.where(mi[y_topo:y_topo + n_topo, c] > 0)[0]
        topo_y.append(float(col.min()) if len(col) else np.nan)
    ty = np.array(topo_y, dtype=np.float32)
    xs_validos = np.where(~np.isnan(ty))[0].astype(np.float32)
    incl_topo = None
    if xs_validos.size >= 8:
        incl_topo = float(np.degrees(np.arctan(np.polyfit(xs_validos, ty[~np.isnan(ty)], 1)[0])))
    return {
        "altura_px": int(alt), "larg_max_px": int(larg_max),
        "aspecto": float(larg_max) / max(alt, 1),
        # quantas vezes o topo e mais estreito que a parte mais larga do objeto
        "boca_rel": larg_topo / max(larg_corpo_med, 1.0),
        "anel_rel": larg_anel / max(larg_corpo_med, 1.0),
        # degrau: quanto o alargamento do topo sobressai da boca -> tampa existe
        "degrau": (larg_anel - larg_topo) / max(larg_max, 1.0),
        "pos_anel": float(idx_anel) / max(n_topo - 1, 1),
        "boca_escura": float(esc_topo) if esc_topo == esc_topo else 0.0,
        # desvio do eixo: tampa descentralizada em relacao ao corpo (mal rosqueada)
        "desvio_eixo": abs(c_topo - c_corpo) / max(larg_max, 1.0) if c_corpo == c_corpo else 0.0,
        # inclinacao da tampa RELATIVA ao eixo do corpo (assinatura de tampa frouxa)
        "inclinacao_topo": incl_topo if incl_topo is not None else 0.0,
        "inclinacao_corpo": eixo_corpo if eixo_corpo is not None else 0.0,
        "inclinacao_rel": (abs(incl_topo - eixo_corpo)
                           if (incl_topo is not None and eixo_corpo is not None) else 0.0),
    }


def medir_array(im, caixa=None, fracao_topo=FRACAO_TOPO):
    """Igual a medir(), mas recebe a imagem JA decodificada (uso ao vivo, sem passar por arquivo)."""
    if im is None:
        return None
    h, w = im.shape[:2]
    if caixa is None:
        caixa = [0, 0, w, h]
    justa, masc, diag = apertar_caixa(im, caixa)
    f = features(im, caixa, justa, masc)
    if f is None:
        return {"arquivo": "live", "ok": False, "motivo": diag.get("motivo", "sem_features"),
                "caixa_objeto": list(caixa), "caixa_justa": list(justa), "diag": diag}
    f.update({"arquivo": "live", "ok": True, "caixa_objeto": list(caixa),
              "caixa_justa": list(justa), "diag": diag})
    return f


def medir(caminho: Path, caixa=None, fracao_topo=FRACAO_TOPO):
    im = cv2.imread(str(caminho))
    if im is None:
        return None
    r = medir_array(im, caixa, fracao_topo)
    if r is not None:
        r["arquivo"] = Path(caminho).name
    return r


def verdade(nome):
    if nome.startswith("frame_"):
        return "normal"
    if nome.startswith("tampa_ausente"):
        return "tampa_ausente"
    if nome.startswith("tampa_mal"):
        return "tampa_mal_rosqueada"
    return "?"


def main():
    """Distribuicao das features por classe (antes de qualquer regra): as features separam?"""
    from ultralytics import YOLO
    base = Path(os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat"))) / "github" / "dataset"
    modelo = YOLO("yolov8n.pt")
    campos = ["boca_rel", "anel_rel", "degrau", "pos_anel", "boca_escura", "desvio_eixo", "aspecto"]
    por_classe = {}
    n_ok = 0
    for f in sorted(base.glob("*.jpg")):
        r = modelo.predict(str(f), conf=0.15, imgsz=960, verbose=False)[0]
        idx = [i for i in range(len(r.boxes)) if str(r.names[int(r.boxes.cls[i])]) == "bottle"] \
            if r.boxes is not None and len(r.boxes) else []
        if not idx:
            continue
        i = max(idx, key=lambda j: float(r.boxes.conf[j]))
        caixa = [int(v) for v in r.boxes.xyxy[i].tolist()]
        m = medir(f, caixa)
        if not m or not m.get("ok"):
            continue
        n_ok += 1
        por_classe.setdefault(verdade(f.name), []).append(m)
    print("itens medidos: %d\n" % n_ok)
    print("%-12s %5s " % ("classe", "n") + " ".join("%11s" % c[:11] for c in campos))
    for v in ("normal", "tampa_ausente", "tampa_mal_rosqueada"):
        itens = por_classe.get(v, [])
        if not itens:
            continue
        print("%-12s %5d " % (v, len(itens)) + " ".join(
            "%11.3f" % float(np.median([x[c] for x in itens])) for c in campos))
    print("\n(p50 por classe; '?' = %d itens de deformidade ignorados)"
          % len(por_classe.get("?", [])))


if __name__ == "__main__":
    sys.exit(main() or 0)
