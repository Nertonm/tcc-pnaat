"""Caminhos do pipeline, independentes da profundidade do checkout (stdlib)."""
from pathlib import Path
import os

PIPELINE = Path(__file__).resolve().parent


def _descobrir_raiz(inicio: Path) -> Path:
    for candidato in (inicio, *inicio.parents):
        if (candidato / "docs").is_dir() and (candidato / "dataset").is_dir():
            return candidato
    raise RuntimeError(f"Raiz com docs e dataset nao encontrada a partir de {inicio}")


RAIZ_REPO = _descobrir_raiz(PIPELINE)
_RAIZ_REPO = RAIZ_REPO
CONTRATO = PIPELINE / "contrato"
PNAAT_DADOS = Path(os.environ.get("PNAAT_DADOS") or RAIZ_REPO.parent)
PNAAT_MODELOS = Path(os.environ.get("PNAAT_MODELOS") or RAIZ_REPO.parent.parent / "pnaat-modelos")
