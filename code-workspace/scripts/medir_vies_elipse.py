#!/usr/bin/env python3
"""Mede o vies do ajuste direto de elipse (Fitzgibbon/Halir) nas condicoes do nosso rig.

Motivo: o paper original (Halir & Flusser, 1998 -- verificado) afirma que o ajuste por
distancia *algebrica* tem vies sistematico que encolhe a elipse e que o metodo "cannot be
used directly in applications where excellent accuracy of the fitting is required".
Como o RF-15/RNF-14 mira 0,5 mm de erro absoluto, precisamos saber se esse vies cabe no
orcamento -- ou se exige refino geometrico/subpixel antes de qualquer medida em mm.

Uso:
    python scripts/medir_vies_elipse.py                 # tabela
    python scripts/medir_vies_elipse.py --json saida.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from pocs.poc08_preproc import preproc

# Escala das NOSSAS frames atuais: tampa nominal 28 mm (PCO 1881) sobre 45,8 px medidos
# (semi-eixo maior 22,9 px) -> ~0,61 mm/px. Estimativa ate haver calibracao (Charuco).
ESCALA_PADRAO_MM_PX = 28.0 / 45.8


def amostrar_elipse(
    cx: float,
    cy: float,
    a: float,
    b: float,
    ang_deg: float,
    n: int = 720,
    arco: tuple[float, float] = (0.0, 360.0),
) -> np.ndarray:
    """Pontos sobre a elipse verdadeira, em graus (arco permite simular oclusao)."""
    t = np.radians(np.linspace(arco[0], arco[1], n, endpoint=False))
    th = np.radians(ang_deg)
    x, y = a * np.cos(t), b * np.sin(t)
    return np.column_stack(
        [cx + x * np.cos(th) - y * np.sin(th), cy + x * np.sin(th) + y * np.cos(th)]
    )


def _erro_angulo(estimado: float, real: float) -> float:
    d = abs(estimado - real) % 180.0
    return min(d, 180.0 - d)


def medir(
    a: float,
    b: float,
    ang: float,
    sigma: float,
    arco: tuple[float, float],
    trials: int,
    seed: int,
    usar_ransac: bool,
) -> dict:
    rng = np.random.default_rng(seed)
    erros_a, erros_b, erros_ang = [], [], []
    descartes = 0
    for _ in range(trials):
        pts = amostrar_elipse(120.0, 120.0, a, b, ang, arco=arco)
        if sigma > 0:
            pts = pts + rng.normal(0.0, sigma, pts.shape)
        try:
            if usar_ransac:
                params, _ = preproc.fit_ellipse_ransac(pts, seed=int(rng.integers(0, 10**6)))
            else:
                params = preproc.fit_ellipse_direct_ls(pts)
        except Exception:
            descartes += 1
            continue
        _, _, fa, fb, fang = params
        erros_a.append(fa - a)
        erros_b.append(fb - b)
        erros_ang.append(_erro_angulo(fang, ang))
    if not erros_a:
        return {"sigma_px": sigma, "arco_deg": arco[1] - arco[0], "n": 0, "descartes": descartes}
    ea, eb, eg = np.array(erros_a), np.array(erros_b), np.array(erros_ang)
    return {
        "sigma_px": sigma,
        "arco_deg": round(arco[1] - arco[0], 1),
        "n": int(ea.size),
        "descartes": descartes,
        "bias_a_px": round(float(ea.mean()), 4),
        "std_a_px": round(float(ea.std(ddof=1)), 4),
        "bias_b_px": round(float(eb.mean()), 4),
        "bias_ang_deg": round(float(eg.mean()), 4),
        "std_ang_deg": round(float(eg.std(ddof=1)), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", type=float, default=22.9, help="semi-eixo maior verdadeiro (px)")
    ap.add_argument("--b", type=float, default=21.0, help="semi-eixo menor verdadeiro (px)")
    ap.add_argument("--ang", type=float, default=30.0, help="angulo verdadeiro (graus)")
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--mm-por-px", type=float, default=ESCALA_PADRAO_MM_PX)
    ap.add_argument("--ransac", action="store_true", help="medir com fit_ellipse_ransac")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    sigmas = [0.0, 0.25, 0.5, 1.0, 2.0]
    arcos = [(0.0, 360.0), (0.0, 270.0)]
    linhas = []
    for arco in arcos:
        for sigma in sigmas:
            linhas.append(
                medir(args.a, args.b, args.ang, sigma, arco, args.trials, args.seed, args.ransac)
            )

    escala = args.mm_por_px
    print(f"escala assumida: {escala:.4f} mm/px  (tampa 28 mm / 45,8 px -> 1 px = {escala:.3f} mm)")
    print(f"alvo RNF-14: 0,5 mm  =>  {0.5 / escala:.2f} px")
    print()
    print(f"{'arco':>6} {'sigma':>6} {'n':>4} {'bias_a(px)':>11} {'bias_a(mm)':>11} "
          f"{'bias_b(px)':>11} {'bias_ang(deg)':>13}")
    for r in linhas:
        if not r.get("n"):
            print(f"{r['arco_deg']:>6} {r['sigma_px']:>6} {0:>4}  (sem ajuste valido)")
            continue
        print(
            f"{r['arco_deg']:>6} {r['sigma_px']:>6} {r['n']:>4} {r['bias_a_px']:>11.4f} "
            f"{r['bias_a_px'] * escala:>11.4f} {r['bias_b_px']:>11.4f} {r['bias_ang_deg']:>13.4f}"
        )
    if args.json:
        args.json.write_text(
            json.dumps(
                {"escala_mm_px": escala, "alvo_mm": 0.5, "ransac": args.ransac, "medidas": linhas},
                indent=1,
            )
        )
        print(f"\njson: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
