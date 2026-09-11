"""Testes do pre-processamento PET (rodam com o venv que tem numpy/opencv/scipy)."""
import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
from pocs.poc08_preproc import preproc  # noqa: E402


def _ellipse_points(a=80.0, b=40.0, ang=25.0, cx=160.0, cy=120.0, n=400, noise=0.4, seed=0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    th = np.radians(ang)
    x = a * np.cos(t)
    y = b * np.sin(t)
    xr = cx + x * np.cos(th) - y * np.sin(th)
    yr = cy + x * np.sin(th) + y * np.cos(th)
    rng = np.random.default_rng(seed)
    return np.column_stack([xr, yr]) + rng.normal(0, noise, (n, 2))


def test_flat_field_uniformiza():
    yy, xx = np.mgrid[0:200, 0:200].astype(np.float32)
    vign = np.clip(255.0 - 120.0 * (((xx - 100) ** 2 + (yy - 100) ** 2) / 20000.0), 1, 255)
    flat = vign.astype(np.uint8)
    # captura = cena uniforme 128 * resposta do campo plano
    img = np.clip(128.0 * flat / flat.mean(), 0, 255).astype(np.uint8)
    corr = preproc.flat_field(img, flat)
    assert img.std() > 10
    assert corr.std() < 2.0


def test_align_recovers_shift():
    base = np.random.default_rng(7).integers(0, 255, (200, 200), dtype=np.uint8)
    template = base[40:60, 60:90].copy()
    M = np.float32([[1, 0, 7], [0, 1, 5]])
    shifted = cv2.warpAffine(base, M, (200, 200), borderValue=0)
    dx, dy, score = preproc.align_by_template(shifted, template, pyramid=1)
    assert (dx, dy) == (67, 45)
    assert score > 0.9


def test_fit_ellipse_direct_ls_recupera_parametros():
    pts = _ellipse_points()
    cx, cy, a, b, ang = preproc.fit_ellipse_direct_ls(pts)
    assert abs(cx - 160) < 2 and abs(cy - 120) < 2
    assert abs(a - 80) < 2 and abs(b - 40) < 2
    assert min(abs(ang - 25), abs(ang - 25 - 180), abs(ang - 25 + 180)) < 2


def test_ransac_rejeita_outliers():
    pts = _ellipse_points()
    rng = np.random.default_rng(1)
    outliers = rng.uniform(0, 320, (120, 2))
    todos = np.vstack([pts, outliers])
    (cx, cy, a, b, ang), n_inl = preproc.fit_ellipse_ransac(todos, iters=400, seed=1)
    assert abs(a - 80) < 6 and abs(b - 40) < 6
    assert min(abs(ang - 25), abs(ang - 25 - 180), abs(ang - 25 + 180)) < 4
    assert n_inl >= len(pts) * 0.8


def test_cap_geometry_acha_elipse():
    img = np.zeros((200, 200), np.uint8)
    cv2.ellipse(img, (100, 100), (60, 25), 30, 0, 360, 255, 2)
    g = preproc.cap_geometry(img)
    assert g["ok"] is True
    assert abs(g["cx"] - 100) < 5 and abs(g["cy"] - 100) < 5
    assert abs(g["semi_maior"] - 60) < 8


def test_specular_coverage_conta_area_clara():
    img = np.zeros((100, 100), np.uint8)
    img[10:20, 10:20] = 255
    assert abs(preproc.specular_coverage(img) - 0.01) < 0.002


def test_tenengrad_maior_em_imagem_nitida():
    nitida = np.random.default_rng(3).integers(0, 255, (64, 64), dtype=np.uint8)
    borrada = cv2.GaussianBlur(nitida, (9, 9), 3)
    assert preproc.tenengrad(nitida) > 3 * preproc.tenengrad(borrada)


def test_cnr_distingue_regioes():
    rng = np.random.default_rng(2)
    a = (100 + rng.normal(0, 5, (40, 40))).astype(np.float32)
    b = (200 + rng.normal(0, 5, (40, 40))).astype(np.float32)
    assert preproc.cnr(a, b) > 5


def test_clahe_normalize_formato():
    img = np.full((64, 64), 120, np.uint8)
    out = preproc.clahe_normalize(img)
    assert out.shape == (64, 64) and out.dtype == np.float32


def test_preprocess_roda_sem_flat():
    img = np.zeros((160, 160), np.uint8)
    cv2.ellipse(img, (80, 80), (50, 20), 15, 0, 360, 255, 2)
    out = preproc.preprocess(img)
    assert "tenengrad" in out and out["tampa"]["ok"] is True