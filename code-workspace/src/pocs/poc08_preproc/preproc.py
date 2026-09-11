"""Pre-processamento para inspecao de garrafas PET (MVP, deterministico).

Depende de numpy + opencv (venv com anomalib: <TCC_HOME>/github/.venv).
Etapas: flat-field -> alinhamento por template -> ROI -> geometria (Canny + elipse por
minimos quadrados diretos com RANSAC) -> CLAHE/normalizacao -> mascara de especular +
metricas de qualidade (CNR, Tenengrad, cobertura especular).
"""
from __future__ import annotations

import numpy as np
import cv2

# ----------------------------------------------------------------------------- aquisicao


def flat_field(img: np.ndarray, flat: np.ndarray, dark: np.ndarray | None = None, eps: float = 1e-6) -> np.ndarray:
    """Correcao de campo plano: I' = (I - D) / (F - D) * mean(F - D)."""
    i = img.astype(np.float32)
    f = flat.astype(np.float32)
    d = dark.astype(np.float32) if dark is not None else 0.0
    den = np.maximum(f - d, eps)
    return np.clip((i - d) / den * float(den.mean()), 0, 255).astype(np.uint8)


def to_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def align_by_template(img: np.ndarray, template: np.ndarray, pyramid: int = 4) -> tuple[int, int, float]:
    """Localiza o template (ex.: anel do gargalo) em piramide. Retorna (dx, dy, score NCC)."""
    g_i, g_t = to_gray(img), to_gray(template)
    k = max(1, int(pyramid))
    s_i = cv2.resize(g_i, None, fx=1.0 / k, fy=1.0 / k, interpolation=cv2.INTER_AREA)
    s_t = cv2.resize(g_t, None, fx=1.0 / k, fy=1.0 / k, interpolation=cv2.INTER_AREA)
    if s_t.shape[0] > s_i.shape[0] or s_t.shape[1] > s_i.shape[1]:
        raise ValueError("template maior que a imagem")
    res = cv2.matchTemplate(s_i, s_t, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    return int(loc[0] * k), int(loc[1] * k), float(score)


def crop_roi(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = (int(v) for v in box)
    H, W = img.shape[:2]
    return img[max(0, y):min(H, y + h), max(0, x):min(W, x + w)]


# ----------------------------------------------------------------------------- realce / mascara


def clahe_normalize(gray: np.ndarray, clip: float = 2.0, tiles: int = 8) -> np.ndarray:
    g = to_gray(gray)
    cl = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tiles, tiles)).apply(g)
    x = cl.astype(np.float32) / 255.0
    return ((x - x.mean()) / (x.std() + 1e-6)).astype(np.float32)


def specular_mask(gray: np.ndarray, thr: int = 245) -> np.ndarray:
    return to_gray(gray) >= thr


def specular_coverage(gray: np.ndarray, thr: int = 245) -> float:
    return float(specular_mask(gray, thr).mean())


# ----------------------------------------------------------------------------- metricas de qualidade


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


# ----------------------------------------------------------------------------- geometria: elipse


def fit_ellipse_direct_ls(points: np.ndarray) -> tuple[float, float, float, float, float]:
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
    except Exception:  # fallback sem scipy
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
    if -Fp / Ap <= 0 or -Fp / Cp <= 0:
        raise ValueError("conica nao fecha elipse")
    axis1 = float(np.sqrt(-Fp / Ap))
    axis2 = float(np.sqrt(-Fp / Cp))
    major, minor = max(axis1, axis2), min(axis1, axis2)
    angle = np.degrees(theta) if axis1 >= axis2 else np.degrees(theta) + 90.0
    return float(cx), float(cy), major, minor, float(angle % 180.0)


def ellipse_residual(points: np.ndarray, params: tuple[float, float, float, float, float]) -> np.ndarray:
    """Residuo adimensional |(u/a)^2 + (v/b)^2 - 1| (u,v no referencial da elipse)."""
    cx, cy, a, b, ang = params
    th = np.radians(ang)
    dx = points[:, 0] - cx
    dy = points[:, 1] - cy
    u = dx * np.cos(th) + dy * np.sin(th)
    v = -dx * np.sin(th) + dy * np.cos(th)
    return np.abs((u / a) ** 2 + (v / b) ** 2 - 1.0)


def ellipse_distance_px(points: np.ndarray, params: tuple[float, float, float, float, float]) -> np.ndarray:
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


def fit_ellipse_ransac(points: np.ndarray, iters: int = 500, thresh_px: float = 2.0,
                       min_inliers: int = 10, seed: int = 0) -> tuple[tuple[float, float, float, float, float], int]:
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
        except Exception:
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
    return fit_ellipse_direct_ls(inl), int(len(inl))


def cap_geometry(gray_roi: np.ndarray, canny_low: int = 60, canny_high: int = 160,
                 ransac_iters: int = 300) -> dict:
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
    return {"ok": True, "cx": cx, "cy": cy, "semi_maior": a, "semi_menor": b,
            "tilt_graus": ang, "inliers": n_inl, "pontos": int(pts.shape[0])}


# ----------------------------------------------------------------------------- pipeline


def preprocess(img: np.ndarray, flat: np.ndarray | None = None, dark: np.ndarray | None = None,
               template: np.ndarray | None = None) -> dict:
    """Executa as etapas disponiveis e devolve ROIs + geometria + metricas de qualidade."""
    out: dict = {}
    work = flat_field(img, flat, dark) if flat is not None else img
    out["flat_field"] = flat is not None
    if template is not None:
        dx, dy, score = align_by_template(work, template)
        out["alinhamento"] = {"dx": dx, "dy": dy, "ncc": score}
    g = to_gray(work)
    out["cnr_borda_topo"] = None
    out["tenengrad"] = tenengrad(g)
    out["especular_cobertura"] = specular_coverage(g)
    geom = cap_geometry(g)
    out["tampa"] = geom
    return out