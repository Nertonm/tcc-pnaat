"""Monta 3 frames de 'deformidade_frame_*' para inspecao visual (o detector diz que sao normais)."""
import cv2
import numpy as np
import os as _os
from pathlib import Path as _Path
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO

BASE = str(_RAIZ_REPO / "dataset/nosso/tampa")
cels = []
for n in ("0000", "0004", "0008"):
    im = cv2.imread(f"{BASE}/deformidade_frame_{n}.jpg")
    if im is None:
        print("falta", n)
        continue
    h, w = im.shape[:2]
    e = 420.0 / max(h, w)
    im = cv2.resize(im, (int(w * e), int(h * e)), interpolation=cv2.INTER_AREA)
    cels.append(im)
if not cels:
    raise SystemExit("sem imagens")
H = max(c.shape[0] for c in cels)
W = sum(c.shape[1] for c in cels)
out = np.full((H, W, 3), 25, np.uint8)
x = 0
for c in cels:
    out[:c.shape[0], x:x + c.shape[1]] = c
    x += c.shape[1]
DESTINO = _Path(_os.environ.get("PNAAT_DEFORMIDADE_JPG")
                or (PNAAT_MODELOS / "evidencias" / "deformidade_propria.jpg"))
DESTINO.parent.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(DESTINO), out, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
print("montagem:", out.shape, "->", DESTINO)
