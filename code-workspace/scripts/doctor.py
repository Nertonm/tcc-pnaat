#!/usr/bin/env python3
"""Doctor: verifica ambiente, API do anomalib, dados e higiene do repo.

Cada item sai PASS/FAIL. Sai != 0 se qualquer item essencial falhar.
Uso: python doctor.py [--repo DIR] [--data DIR]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

TCC_HOME = os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat"))
BASE_GITHUB = Path(TCC_HOME) / "github"
BASE_DATASETS = Path(TCC_HOME) / "datasets"

FAILS: list[str] = []
WARNS: list[str] = []


def check(nome: str, ok: bool, detalhe: str = "", essencial: bool = True) -> None:
    print(f"{'PASS' if ok else 'FAIL' if essencial else 'WARN'} {nome}: {detalhe}")
    if not ok:
        (FAILS if essencial else WARNS).append(nome)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=BASE_GITHUB)
    ap.add_argument("--data", type=Path, default=BASE_DATASETS / "pnaat")
    a = ap.parse_args()

    v = sys.version_info
    check("python", (3, 10) <= (v.major, v.minor) <= (3, 12), f"{v.major}.{v.minor} (anomalib exige 3.10-3.12)")

    try:
        import anomalib  # noqa: F401
        ver = getattr(anomalib, "__version__", "?")
        check("anomalib", ver.startswith("2."), f"versao {ver} (esperado 2.x; 1.x usa MVTec/imgaug, 2.x usa MVTecAD)")
    except Exception as e:  # noqa: BLE001
        check("anomalib", False, f"import falhou: {e}")

    try:
        from anomalib.data import MVTecAD  # noqa: F401
        from anomalib.engine import Engine  # noqa: F401
        from anomalib.models import EfficientAd, Fastflow, Padim, Patchcore  # noqa: F401
        check("api anomalib (MVTecAD/Engine/modelos)", True, "imports ok")
    except Exception as e:  # noqa: BLE001
        check("api anomalib (MVTecAD/Engine/modelos)", False, f"import falhou: {e}")

    for mod in ("numpy", "cv2", "scipy", "PIL"):
        try:
            m = __import__(mod)
            check(f"dep {mod}", True, getattr(m, "__version__", "ok"))
        except Exception as e:  # noqa: BLE001
            check(f"dep {mod}", False, str(e))

    try:
        import numpy as np
        if np.lib.NumpyVersion(np.__version__) >= "2.0.0":
            WARNS.append("numpy2-sem-ptp")
            print("WARN numpy2: ndarray.ptp() removido — use np.ptp() (ja usado no preproc)")
    except Exception:
        pass

    for d in ("origem", "gerados", "dataset/normal", "dataset/defective", "entrada"):
        p = a.data / d
        check(f"dados {d}", p.exists(), str(p))

    n_norm = len(list((a.data / "dataset/normal").glob("*"))) if (a.data / "dataset/normal").exists() else 0
    n_def = len(list((a.data / "dataset/defective").glob("*"))) if (a.data / "dataset/defective").exists() else 0
    print(f"INFO dataset: normal={n_norm} defective={n_def}")

    mv = BASE_DATASETS / "MVTecAD" / "bottle"
    check("MVTecAD bottle (proxy)", mv.exists(), str(mv), essencial=False)

    if (a.repo / ".git").exists():
        try:
            out = subprocess.run(["git", "-C", str(a.repo), "ls-files"], capture_output=True, text=True).stdout
            media = [l for l in out.splitlines() if l.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".stl", ".step"))]
            # Excecao declarada no commit_gate.sh: as imagens em dataset/ sao versionadas de proposito.
            media_fora = [m for m in media if not m.startswith("dataset/")]
            detalhe = f"{len(media_fora)} arquivo(s)" + (f" ex: {media_fora[:2]}" if media_fora else f" (dataset/ versionado: {len(media)} arquivos, excecao declarada)")
            check("repo sem midia versionada fora de dataset/", not media_fora, detalhe)
        except Exception as e:  # noqa: BLE001
            check("repo sem midia versionada fora de dataset/", False, str(e), essencial=False)
        gi = (a.repo / ".gitignore").read_text() if (a.repo / ".gitignore").exists() else ""
        check(".gitignore cobre /dataset", "/dataset" in gi or "dataset/" in gi, "ok" if "dataset" in gi else "ausente", essencial=False)

    print(f"\nRESULTADO: {len(FAILS)} FAIL, {len(WARNS)} WARN")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())