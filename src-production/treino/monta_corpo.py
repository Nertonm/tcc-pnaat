"""Monta o dataset de CORPO (YOLO) a partir das fontes com supervisao de corpo.

Classes: 0 normal, 1 deformidade.
Mapeamento declarado:
  c6ts8        : crumbled -> deformidade | not-crumbled -> normal | cap/label/no-cap DESCARTADOS
  deformed-bottle: NG-13 -> deformidade  | normal -> normal
Conversao de rotulo: len==5 -> cx cy w h; poligono (1+2N) -> AABB (min/max), com registro do tipo.
Split por sha256 da imagem (90/10), sem usar o split da fonte (que pode ter augmentation antes).
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import shutil
import os as _os
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_MODELOS
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_MODELOS

RAIZ = _RAIZ_REPO / "dataset/externo"
# Saida do dataset derivado: NUNCA em /tmp (tmpfs compartilhado ja perdeu dataset neste projeto).
SAIDA = pathlib.Path(_os.environ.get("PNAAT_CORPO_DATASET") or (PNAAT_MODELOS / "corpo-dataset"))
FONTES = [
    ("c6ts8", RAIZ / "bottle-defect-detection-c6ts8",
     {"crumbled": 1, "not-crumbled": 0}),
    ("deformed-bottle", RAIZ / "deformed-bottle",
     {"NG-13": 1, "normal": 0}),
]
# nomes de classe por indice no data.yaml de cada fonte
NOMES = {
    "c6ts8": {0: "cap", 1: "crumbled", 2: "label", 3: "no-cap", 4: "not-crumbled"},
    "deformed-bottle": {0: "NG-13", 1: "normal"},
}


def sha(p, bloco=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(bloco), b""):
            h.update(b)
    return h.hexdigest()


def converte_linha(partes, mapa):
    if len(partes) < 5:
        return None
    cid = int(partes[0])
    nome = NOMES_ATUAL.get(cid)
    if nome not in mapa:
        return None
    vals = [float(v) for v in partes[1:]]
    if len(partes) == 5:
        cx, cy, w, h = vals
        tipo = "box"
    elif len(vals) >= 6 and len(vals) % 2 == 0:
        xs, ys = vals[0::2], vals[1::2]
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
        cx, cy, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
        tipo = "poligono->aabb"
    else:
        return None
    if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1):
        return None
    return f"{mapa[nome]} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}", tipo


if SAIDA.exists():
    shutil.rmtree(SAIDA)
for sub in ("images/train", "images/val", "labels/train", "labels/val"):
    (SAIDA / sub).mkdir(parents=True, exist_ok=True)

resumo = collections.Counter()
tipos = collections.Counter()
feitos = set()
for nome_fonte, base, mapa in FONTES:
    NOMES_ATUAL = NOMES[nome_fonte]
    globals()["NOMES_ATUAL"] = NOMES_ATUAL
    imgs = [p for p in base.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    print(f"== {nome_fonte}: {len(imgs)} imagens")
    for img in sorted(imgs):
        # dois layouts: <ds>/<split>/images/x.jpg + <split>/labels ; e <ds>/images/<split>/x.jpg + labels/<split>
        cands = [
            img.parent.parent / "labels" / img.with_suffix(".txt").name,
            img.parent.parent / "labels" / img.parent.name / img.with_suffix(".txt").name,
            base / "labels" / img.parent.name / img.with_suffix(".txt").name,
        ]
        partes = list(img.parts)
        for i, seg in enumerate(partes):
            if seg in ("images", "image"):
                cands.append(pathlib.Path(*partes[:i]) / "labels" / pathlib.Path(*partes[i + 1:]).with_suffix(".txt"))
                break
        lab = next((c for c in cands if c.exists()), None)
        if lab is None:
            continue
        linhas = []
        for l in lab.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            r = converte_linha(l.split(), mapa)
            if r:
                linhas.append(r[0])
                tipos[r[1]] += 1
        if not linhas:
            continue
        h = sha(img)
        if h in feitos:
            continue
        feitos.add(h)
        dest = "val" if (int(h[:8], 16) % 10 == 0) else "train"
        ext = img.suffix.lower()
        novo = f"{nome_fonte}__{h[:12]}{ext}"
        shutil.copy2(img, SAIDA / "images" / dest / novo)
        (SAIDA / "labels" / dest / (novo.rsplit(".", 1)[0] + ".txt")).write_text("\n".join(linhas) + "\n")
        for l in linhas:
            resumo[(dest, l.split()[0])] += 1

yaml = (f"path: {SAIDA}\ntrain: images/train\nval: images/val\nnc: 2\n"
        "names: ['normal', 'deformidade']\n")
(SAIDA / "data.yaml").write_text(yaml)
n_tr = len(list((SAIDA / "images/train").iterdir()))
n_va = len(list((SAIDA / "images/val").iterdir()))
print(f"\ntreino: {n_tr} imagens | val: {n_va} imagens | duplicadas por sha200_puladas: {len(feitos)}")
print("caixas por split/classe:", dict(resumo))
print("tipos de rotulo convertidos:", dict(tipos))
print("data.yaml:")
print(yaml)
json.dump({"treino": n_tr, "val": n_va, "caixas": {f"{k[0]}/{k[1]}": v for k, v in resumo.items()},
           "tipos": dict(tipos)}, open(SAIDA / "resumo.json", "w"), ensure_ascii=False, indent=1)
print("saida:", SAIDA)
