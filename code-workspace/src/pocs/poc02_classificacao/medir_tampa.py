"""Adaptador que faltava: da medicao crua do preproc para o contrato `GeometriaTampa` da politica.

Por que existe: `preproc.cap_geometry` entrega elipse crua (ok, centro, semi-eixos, angulo, inliers).
`politica_tampa.GeometriaTampa` espera `contorno_ok`, `arco_visivel_graus`, `tilt_graus` (0 = rosqueada
corretamente), `altura_cupula_px`, `cnr`, `especular`. Nada no sistema fazia essa conversao: a politica
so era exercitada com valores escritos a mao nos testes.

Limites declarados (proxy, nao metrologia):
  - `tilt_graus`: desvio do eixo maior da elipse do anel em relacao a horizontal da imagem. Numa
    montagem fixa serve como proxy de tampa torta; NAO e o angulo do plano da tampa em 3D.
  - `altura_cupula_px`: altura da cupula acima do centro da elipse, em pixels. Depende da escala:
    so comparavel dentro do mesmo rig (a razao altura/semi_maior tambem e devolvida para inspecao).
  - `arco_visivel_graus`: cobertura angular dos pontos de borda que caem sobre a elipse ajustada.
  - `cnr` sem regiao de corpo informada vira proxy (metade de cima contra metade de baixo do recorte).
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from poc08_preproc import preproc  # noqa: E402

TOL_PX_ARCO = 2.0
PASSO_GRAUS = 2.0


def pontos_borda(gray: np.ndarray, canny_low: int = 60, canny_high: int = 160):
    g = cv2.GaussianBlur(preproc.to_gray(gray), (3, 3), 0)
    bordas = cv2.Canny(g, canny_low, canny_high)
    contornos, _ = cv2.findContours(bordas, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return None
    return max(contornos, key=cv2.contourArea).reshape(-1, 2).astype(np.float64)


def arco_visivel(pontos: np.ndarray, params, tol_px: float = TOL_PX_ARCO):
    """Cobertura angular (graus) dos pontos de borda a menos de `tol_px` da elipse ajustada."""
    cx, cy, a, b, ang = params
    d = preproc.ellipse_distance_px(pontos, params)
    sel = pontos[d < tol_px]
    if len(sel) < 5:
        return 0.0, int(len(sel))
    th = np.radians(ang)
    dx, dy = sel[:, 0] - cx, sel[:, 1] - cy
    u = dx * np.cos(th) + dy * np.sin(th)
    v = -dx * np.sin(th) + dy * np.cos(th)
    phi = np.degrees(np.arctan2(v / max(b, 1e-9), u / max(a, 1e-9))) % 360.0
    ocupados = np.unique((phi // PASSO_GRAUS).astype(int))
    return float(len(ocupados) * PASSO_GRAUS), int(len(sel))


def altura_cupula(gray: np.ndarray, cy: float) -> float:
    """Altura (px) da cupula acima da linha do centro da elipse, pela silhueta do maior contorno."""
    g = preproc.to_gray(gray)
    _, binaria = cv2.threshold(cv2.GaussianBlur(g, (7, 7), 0), 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contornos, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return 0.0
    y_topo = min(cv2.boundingRect(c)[1] for c in contornos if cv2.contourArea(c) > 500) \
        if any(cv2.contourArea(c) > 500 for c in contornos) else 0
    return float(max(0.0, cy - y_topo))


def medir_tampa(img: np.ndarray, corpo: np.ndarray | None = None) -> dict:
    """Mede a tampa e devolve os campos que a politica consome, mais os diagnosticos."""
    gray = preproc.to_gray(img)
    g = preproc.cap_geometry(gray)
    especular = preproc.specular_coverage(gray)
    saida = {"contorno_ok": bool(g.get("ok")), "motivo": g.get("motivo"),
             "especular": float(especular), "cnr_proxy": corpo is None}
    if not saida["contorno_ok"]:
        saida.update({"arco_visivel_graus": 0.0, "tilt_graus": 0.0, "altura_cupula_px": 0.0,
                      "cnr": 0.0, "inliers": 0, "semi_maior": 0.0, "razao_eixos": 0.0})
        return saida
    params = (g["cx"], g["cy"], g["semi_maior"], g["semi_menor"], g["tilt_graus"])
    pontos = pontos_borda(gray)
    arco, n_perto = arco_visivel(pontos, params) if pontos is not None else (0.0, 0)
    altura = altura_cupula(gray, g["cy"])
    if corpo is not None:
        cnr = float(preproc.cnr(img, corpo))
    else:
        h = gray.shape[0]
        cnr = float(preproc.cnr(gray[: h // 2, :], gray[h // 2:, :]))
    ang = float(g["tilt_graus"])
    desvio = float(min(ang, 180.0 - ang))          # 0 = eixo maior na horizontal da imagem
    semi = float(g["semi_maior"])
    saida.update({"arco_visivel_graus": arco, "tilt_graus": desvio, "altura_cupula_px": altura,
                  "altura_relativa": float(altura / semi) if semi > 0 else 0.0,
                  "cnr": cnr, "inliers": int(g["inliers"]), "semi_maior": semi,
                  "razao_eixos": float(g["semi_menor"] / semi) if semi > 0 else 0.0,
                  "angulo_cru": ang, "pontos_perto": n_perto})
    return saida


def geometria_tampa(img: np.ndarray, corpo: np.ndarray | None = None):
    """Devolve uma `GeometriaTampa` pronta para `politica_tampa.decidir`."""
    from poc02_classificacao.politica_tampa import GeometriaTampa
    m = medir_tampa(img, corpo)
    return GeometriaTampa(contorno_ok=m["contorno_ok"], arco_visivel_graus=m["arco_visivel_graus"],
                          tilt_graus=m["tilt_graus"], altura_cupula_px=m["altura_cupula_px"],
                          cnr=m["cnr"], especular=m["especular"], inliers=m["inliers"]), m
