"""Pre-processamento deterministico; PADRAO DO PROJETO (portado do PoC-08).

Fonte canonica: a PoC-08 (`docs/pocs/poc08_preproc/README.md`); a versao portada e este modulo. O padrao do projeto exige
que o MESMO pipeline rode no treino e na inferencia, com a versao registrada no manifesto; por
isso a versao vive aqui e vai em todo sidecar.

Cadeia (a ordem do documento):
    1. flat-field + dark-frame      (so com gabarito; ausente => registrado como nao aplicado)
    2. alinhamento por template NCC (ancora: anel do gargalo)
    3. recorte de ROI               (terco superior = tampa; restante = corpo)
    4. CLAHE + normalizacao         (nas ROIs, nao no quadro inteiro)
    5. mascara de especular         (limiar ~245)
    6. metricas de qualidade        (Tenengrad, cobertura especular, CNR)
    7. geometria da tampa           (Canny + elipse por minimos quadrados com RANSAC)

LIMITE DECLARADO: as etapas 1, 2 e 5 nao estavam na cadeia no PoC-08 (README, "Limite atual").
Aqui elas estao ligadas, mas continuam CONDICIONAIS: sem gabarito de flat/dark a etapa 1 nao
roda e o sidecar diz `aplicado: false` com o motivo. Nada e inventado no lugar do que nao foi
medido.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np

#: Versao do pipeline. Vai em todo sidecar e tem de mudar quando qualquer etapa mudar de
#: comportamento: e o que permite dizer que treino e inferencia viram a mesma coisa.
VERSAO_PIPELINE = "pet-preproc-3"  # P1 + guarda de finitude no ajuste de elipse

#: Limiar de especular do documento (secao 2, passo 7).
LIMIAR_ESPECULAR = 245

#: Fracao do quadro que corresponde ao terco superior, usada SO quando nao ha caixa declarada.
FRACAO_TOPO = 1.0 / 3.0

#: NCC minimo para aceitar um alinhamento. Abaixo disso o alinhamento e declarado falho; um
#: deslocamento errado e pior que deslocamento nenhum, porque move a ROI de lugar em silencio.
NCC_MINIMO = 0.5


class ErroDePreprocessamento(Exception):
    """Falha explicita do pipeline: imagem ilegivel, ROI fora do quadro, etc."""


# --------------------------------------------------------------------------- aquisicao


def flat_field(
    img: np.ndarray, flat: np.ndarray, dark: np.ndarray | None = None, eps: float = 1e-6
) -> np.ndarray:
    """Correcao de campo plano: I' = (I - D) / (F - D) * mean(F - D)."""
    i = img.astype(np.float32)
    f = flat.astype(np.float32)
    d = dark.astype(np.float32) if dark is not None else 0.0
    den = np.maximum(f - d, eps)
    return np.clip((i - d) / den * float(den.mean()), 0, 255).astype(np.uint8)


def to_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def align_by_template(
    img: np.ndarray, template: np.ndarray, pyramid: int = 4
) -> tuple[int, int, float]:
    """Localiza o template (anel do gargalo) em piramide. Retorna (dx, dy, score NCC)."""
    g_i, g_t = to_gray(img), to_gray(template)
    k = max(1, int(pyramid))
    s_i = cv2.resize(g_i, None, fx=1.0 / k, fy=1.0 / k, interpolation=cv2.INTER_AREA)
    s_t = cv2.resize(g_t, None, fx=1.0 / k, fy=1.0 / k, interpolation=cv2.INTER_AREA)
    if s_t.shape[0] > s_i.shape[0] or s_t.shape[1] > s_i.shape[1]:
        raise ErroDePreprocessamento("template maior que a imagem")
    res = cv2.matchTemplate(s_i, s_t, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    return int(loc[0] * k), int(loc[1] * k), float(score)


def crop_roi(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = (int(v) for v in box)
    H, W = img.shape[:2]
    return img[max(0, y) : min(H, y + h), max(0, x) : min(W, x + w)]


def deslocar(img: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """Aplica o deslocamento achado pelo alinhamento (translacao pura, sem reescalar)."""
    H, W = img.shape[:2]
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(
        img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )


# --------------------------------------------------------------------------- realce / mascara


def clahe_normalize(gray: np.ndarray, clip: float = 2.0, tiles: int = 8) -> np.ndarray:
    g = to_gray(gray)
    cl = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tiles, tiles)).apply(g)
    x = cl.astype(np.float32) / 255.0
    return ((x - x.mean()) / (x.std() + 1e-6)).astype(np.float32)


def clahe_para_png(gray: np.ndarray, clip: float = 2.0, tiles: int = 8) -> np.ndarray:
    """A mesma CLAHE, mas devolvida em 8 bits para poder ser gravada e vista por um humano.

    `clahe_normalize` devolve float normalizado (z-score); correto para o modelo, ilegivel
    como imagem. Esta versao grava o que o modelo ve depois de reescalado, e o sidecar diz que
    foi assim, em vez de fingir que o PNG e a saida do modelo.
    """
    z = clahe_normalize(gray, clip=clip, tiles=tiles)
    lo, hi = float(z.min()), float(z.max())
    if hi - lo < 1e-9:
        return np.zeros_like(to_gray(gray), dtype=np.uint8)
    return np.clip((z - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)


def specular_mask(gray: np.ndarray, thr: int = LIMIAR_ESPECULAR) -> np.ndarray:
    return to_gray(gray) >= thr


def specular_coverage(gray: np.ndarray, thr: int = LIMIAR_ESPECULAR) -> float:
    return float(specular_mask(gray, thr).mean())


# --------------------------------------------------------------------------- metricas


def tenengrad(gray: np.ndarray) -> float:
    """Nitidez (Tenengrad) via diferencas centrais em numpy (evita bug do cv2.Sobel 5.0)."""
    g = to_gray(gray).astype(np.float32)
    gx = np.zeros_like(g)
    gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    gy[1:-1, :] = g[2:, :] - g[:-2, :]
    return float(np.mean(gx * gx + gy * gy))


def cnr(region_a: np.ndarray, region_b: np.ndarray) -> float:
    a, b = region_a.astype(np.float32).ravel(), region_b.astype(np.float32).ravel()
    return float(abs(a.mean() - b.mean()) / np.sqrt(a.var() + b.var() + 1e-9))


def cnr_central(gray: np.ndarray, fracao: float = 0.15) -> float | None:
    """CNR entre o miolo e a moldura da ROI; a borda da silhueta sem precisar de mascara.

    None quando a ROI e pequena demais para as duas amostras; nao se inventa numero.
    """
    g = to_gray(gray).astype(np.float32)
    H, W = g.shape[:2]
    my, mx = int(H * fracao), int(W * fracao)
    if H < 4 * my or W < 4 * mx:
        return None
    miolo = g[my : H - my, mx : W - mx]
    moldura = np.concatenate(
        [
            g[:my, :].ravel(),
            g[H - my :, :].ravel(),
            g[my : H - my, :mx].ravel(),
            g[my : H - my, W - mx :].ravel(),
        ]
    )
    if miolo.size == 0 or moldura.size == 0:
        return None
    return cnr(miolo, moldura.reshape(-1, 1))


# --------------------------------------------------------------------------- elipse / geometria


def validar_eixos_da_elipse(Ap: float, Cp: float, Fp: float) -> None:
    """Recusa conica degenerada ANTES de dividir.

    Com Ap ou Cp = 0 a divisao vira inf/NaN; `-Fp/Ap <= 0` da False (ou NaN) e a funcao devolvia
    `axis = inf` com `ok: True`; medicao invalida passando por valida. Esta funcao existe separada
    para poder ser testada com os valores degenerados LITERAIS (construir um input real que produza
    Ap=0 e possivel, mas fragil; o teste com o valor literal e o que pega a regressao).
    """
    for nome, v in (("Ap", Ap), ("Cp", Cp), ("Fp", Fp)):
        if not np.isfinite(v):
            raise ValueError(f"conica degenerada ({nome} nao finito)")
    if Ap == 0 or Cp == 0:
        raise ValueError("conica degenerada (eixo nulo)")


def fit_ellipse_direct_ls(
    points: np.ndarray,
) -> tuple[float, float, float, float, float]:
    """Ajuste direto de elipse por minimos quadrados (Fitzgibbon/Halir).

    Retorna (cx, cy, semi_eixo_maior, semi_eixo_menor, angulo_graus[0,180)).
    """
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    if pts.shape[0] < 5:
        raise ValueError("precisa de >=5 pontos")
    x, y = pts[:, 0], pts[:, 1]
    D = np.column_stack([x * x, x * y, y * y, x, y, np.ones_like(x)])
    S = D.T @ D
    C = np.zeros((6, 6))
    C[0, 2] = C[2, 0] = 2.0
    C[1, 1] = -1.0
    try:
        from scipy.linalg import eig

        _, evecs = eig(S, C)
    except Exception:  # noqa: BLE001  # fallback sem scipy
        _, evecs = np.linalg.eig(np.linalg.pinv(C) @ S)
    evecs = np.real(evecs)
    cond = 4 * evecs[0] * evecs[2] - evecs[1] ** 2
    cand = evecs[:, cond > 0]
    if cand.shape[1] == 0:
        raise ValueError("sem solucao eliptica")
    A, B, Cc, Dd, E, F = cand[:, 0]

    den = B * B - 4 * A * Cc
    cx = (2 * Cc * Dd - B * E) / den
    cy = (2 * A * E - B * Dd) / den
    theta = 0.5 * np.arctan2(B, A - Cc)

    Fp = A * cx * cx + B * cx * cy + Cc * cy * cy + Dd * cx + E * cy + F
    ct, st = np.cos(theta), np.sin(theta)
    Ap = A * ct * ct + B * ct * st + Cc * st * st
    Cp = A * st * st - B * ct * st + Cc * ct * ct
    validar_eixos_da_elipse(Ap, Cp, Fp)
    if -Fp / Ap <= 0 or -Fp / Cp <= 0:
        raise ValueError("conica nao fecha elipse")
    axis1 = float(np.sqrt(-Fp / Ap))
    axis2 = float(np.sqrt(-Fp / Cp))
    if not np.isfinite([axis1, axis2]).all():
        raise ValueError("eixos nao finitos")
    major, minor = max(axis1, axis2), min(axis1, axis2)
    angle = np.degrees(theta) if axis1 >= axis2 else np.degrees(theta) + 90.0
    return float(cx), float(cy), major, minor, float(angle % 180.0)


def ellipse_residual(
    points: np.ndarray, params: tuple[float, float, float, float, float]
) -> np.ndarray:
    """Residuo adimensional |(u/a)^2 + (v/b)^2 - 1| (u,v no referencial da elipse)."""
    cx, cy, a, b, ang = params
    th = np.radians(ang)
    dx = points[:, 0] - cx
    dy = points[:, 1] - cy
    u = dx * np.cos(th) + dy * np.sin(th)
    v = -dx * np.sin(th) + dy * np.cos(th)
    return np.abs((u / a) ** 2 + (v / b) ** 2 - 1.0)


def ellipse_distance_px(
    points: np.ndarray, params: tuple[float, float, float, float, float]
) -> np.ndarray:
    """Distancia aproximada (px) do ponto a elipse: |r-1| * (a*b)/gradiente. Robusta p/ RANSAC."""
    cx, cy, a, b, ang = params
    th = np.radians(ang)
    dx = points[:, 0] - cx
    dy = points[:, 1] - cy
    u = dx * np.cos(th) + dy * np.sin(th)
    v = -dx * np.sin(th) + dy * np.cos(th)
    r = np.sqrt((u / a) ** 2 + (v / b) ** 2 + 1e-12)
    phi = np.arctan2(v / b, u / a)
    grad = np.sqrt((b * np.cos(phi)) ** 2 + (a * np.sin(phi)) ** 2) + 1e-12
    return np.abs(r - 1.0) * (a * b) / grad


def fit_ellipse_ransac(
    points: np.ndarray,
    iters: int = 500,
    thresh_px: float = 2.0,
    min_inliers: int = 10,
    seed: int = 0,
) -> tuple[tuple[float, float, float, float, float], int]:
    """RANSAC sobre o ajuste direto (rejeita rebarbas/outliers no friso). Limiar em PIXELS."""
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    if pts.shape[0] < min_inliers:
        raise ValueError("poucos pontos para RANSAC")
    rng = np.random.default_rng(seed)
    extent = float(max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1])))
    best_params, best_n = None, -1
    for _ in range(iters):
        idx = rng.choice(pts.shape[0], 5, replace=False)
        try:
            params = fit_ellipse_direct_ls(pts[idx])
        except ValueError:
            continue
        _, _, a, b, _ = params
        if not (2.0 < a < 5 * extent and 2.0 < b < 5 * extent):
            continue
        n_inl = int((ellipse_distance_px(pts, params) < thresh_px).sum())
        if n_inl > best_n:
            best_params, best_n = params, n_inl
    if best_params is None or best_n < min_inliers:
        raise ValueError("RANSAC nao convergiu")
    inl = pts[ellipse_distance_px(pts, best_params) < thresh_px]
    if len(inl) < min_inliers:
        raise ValueError("RANSAC: inliers insuficientes")
    return fit_ellipse_direct_ls(inl), len(inl)


def cap_geometry(
    gray_roi: np.ndarray,
    canny_low: int = 60,
    canny_high: int = 160,
    ransac_iters: int = 300,
) -> dict:
    """Geometria da tampa: bordas -> maior contorno -> elipse (RANSAC)."""
    g = to_gray(gray_roi)
    g = cv2.GaussianBlur(g, (3, 3), 0)
    edges = cv2.Canny(g, canny_low, canny_high)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return {"ok": False, "motivo": "sem contornos"}
    cnt = max(contours, key=cv2.contourArea)
    pts = cnt.reshape(-1, 2).astype(np.float64)
    if pts.shape[0] < 20:
        return {"ok": False, "motivo": "contorno pequeno"}
    try:
        params, n_inl = fit_ellipse_ransac(pts, iters=ransac_iters)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "motivo": f"elipse: {e}"}
    cx, cy, a, b, ang = params
    return {
        "ok": True,
        "cx": cx,
        "cy": cy,
        "semi_maior": a,
        "semi_menor": b,
        "tilt_graus": ang,
        "inliers": n_inl,
        "pontos": int(pts.shape[0]),
    }


# --------------------------------------------------------------------------- cadeia completa


def sha256_de(caminho: str | Path, bloco: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for pedaco in iter(lambda: f.read(bloco), b""):
            h.update(pedaco)
    return h.hexdigest()


def _roi_do_quadro(
    roi: tuple[float, float, float, float] | None, W: int, H: int
) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int] | None]:
    """Devolve (roi_tampa, roi_corpo) em pixels do quadro; o corpo pode ser None.

    `roi` e a caixa de interesse da TAMPA, em fracao do quadro (x1,y1,x2,y2). Sem caixa
    declarada a tampa e o terco superior; e o sidecar diz isso, para nao parecer medicao.

    Se a ROI da tampa cobre o quadro inteiro (imagem que JA e um recorte), NAO existe corpo
    separado: devolver um retangulo degenerado fazia o OpenCV receber imagem vazia e estourar.
    Corpo indisponivel e uma informacao, nao um erro.
    """
    if roi is None:
        return (0, 0, W, int(H * FRACAO_TOPO)), (0, int(H * FRACAO_TOPO), W, H)
    x1, y1, x2, y2 = (float(v) for v in roi)
    t = (
        max(0, int(x1 * W)),
        max(0, int(y1 * H)),
        min(W, int(x2 * W)),
        min(H, int(y2 * H)),
    )
    if t[2] <= t[0] or t[3] <= t[1]:
        raise ErroDePreprocessamento(f"ROI de tampa invalida: {roi}")
    corpo = (0, min(H, t[3]), W, H)
    if corpo[3] <= corpo[1] or corpo[2] <= corpo[0]:
        corpo = None
    return t, corpo


def normalizar_imagem(
    caminho: str | Path,
    *,
    roi: tuple[float, float, float, float] | None = None,
    dominio: str = "indefinido",
    template: np.ndarray | None = None,
    flat: np.ndarray | None = None,
    dark: np.ndarray | None = None,
    permitir_alinhamento: bool = True,
) -> dict:
    """Roda o padrao do projeto numa imagem e devolve o sidecar + as imagens da cadeia.

    Fail-closed: imagem ilegivel levanta. O alinhamento so e ACEITO acima de `NCC_MINIMO`;
    abaixo disso o quadro NAO e deslocado (um deslocamento errado move a ROI em silencio) e o
    sidecar registra o motivo. Nada aqui aprova nem reprova tampa; isto e pre-processamento.
    """
    caminho = Path(caminho)
    quadro = cv2.imread(str(caminho))
    if quadro is None:
        raise ErroDePreprocessamento(f"imagem ilegivel: {caminho}")
    H, W = quadro.shape[:2]

    out: dict = {
        "versao_pipeline": VERSAO_PIPELINE,
        "fonte": str(caminho),
        "sha256_origem": sha256_de(caminho),
        "largura": W,
        "altura": H,
        "dominio": dominio,
        "shape_origem": [H, W],
        "etapas": {},
        "tags": {},
        "caixas": [],
    }

    trabalho = quadro
    if flat is not None:
        trabalho = flat_field(trabalho, flat, dark)
        out["etapas"]["flat_field"] = {"aplicado": True}
    else:
        out["etapas"]["flat_field"] = {
            "aplicado": False,
            "motivo": "sem gabarito de flat/dark",
        }

    if template is not None and permitir_alinhamento:
        dx, dy, score = align_by_template(trabalho, template)
        if score >= NCC_MINIMO:
            trabalho = deslocar(trabalho, dx, dy)
            out["etapas"]["alinhamento"] = {
                "aplicado": True,
                "dx": dx,
                "dy": dy,
                "ncc": round(score, 4),
            }
        else:
            out["etapas"]["alinhamento"] = {
                "aplicado": False,
                "dx": dx,
                "dy": dy,
                "ncc": round(score, 4),
                "motivo": f"ncc abaixo de {NCC_MINIMO}",
            }
    else:
        out["etapas"]["alinhamento"] = {
            "aplicado": False,
            "motivo": "sem template"
            if template is None
            else "dominio declara alinhamento nao aplicavel",
        }

    roi_tampa, roi_corpo = _roi_do_quadro(roi, W, H)
    out["roi_tampa"] = list(roi_tampa)  # x1,y1,x2,y2 em pixel do quadro normalizado
    out["roi_corpo"] = None if roi_corpo is None else list(roi_corpo)
    out["roi_declarada"] = roi is not None
    out["corpo_disponivel"] = roi_corpo is not None

    x1, y1, x2, y2 = roi_tampa
    tampa = trabalho[y1:y2, x1:x2]
    corpo = None
    if roi_corpo is not None:
        cx1, cy1, cx2, cy2 = roi_corpo
        corpo = trabalho[cy1:cy2, cx1:cx2]

    out["tampa_bgr"] = tampa
    out["corpo_bgr"] = corpo
    out["quadro_normalizado"] = trabalho

    g_tampa = to_gray(tampa)
    out["tampa_clahe8"] = clahe_para_png(g_tampa)
    out["corpo_clahe8"] = None if corpo is None else clahe_para_png(to_gray(corpo))
    out["mascara"] = specular_mask(g_tampa).astype(np.uint8) * 255

    out["qualidade"] = {
        "tenengrad": round(tenengrad(to_gray(trabalho)), 2),
        "especular_cobertura": round(specular_coverage(to_gray(trabalho)), 4),
        "cnr_roi_tampa": (
            None if cnr_central(g_tampa) is None else round(cnr_central(g_tampa), 3)
        ),
        "largura_roi_tampa": int(x2 - x1),
        "altura_roi_tampa": int(y2 - y1),
    }
    try:
        out["tampa"] = cap_geometry(g_tampa)
    except Exception as e:  # noqa: BLE001
        out["tampa"] = {"ok": False, "motivo": f"geometria: {e}"}
    out["etapas"]["clahe"] = {
        "aplicado": True,
        "nas_rois": True,
        "saida": "clahe_para_png (8 bits) para gravar; o modelo usa z-score float",
    }
    out["etapas"]["mascara_especular"] = {"aplicado": True, "limiar": LIMIAR_ESPECULAR}
    return out
