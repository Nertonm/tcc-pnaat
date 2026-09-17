"""Exporta os artefatos de inferencia com a receita validada (PCA + padronizacao por fonte + cabeca).

Sem isto o servico nao reproduz o que foi medido: o modelo final nao e so a cabeca; e a
transformacao (PCA fit no train, media/desvio por fonte tirados do train) mais a cabeca.

Grava `modelo-inferencia.npz` + um `modelo-inferencia.json` com a identificacao do vintage.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO

G = _RAIZ_REPO
D = G / "dataset"
CLASSES = ["normal", "tampa_ausente", "defeito_tampa"]
APOIO = {"externo:kmitl-bottle-cap", "externo:aitech-bottle-cap"}
ALVO = "nosso"
PCA_DIM = 256
SEMENTE = 7
CACHE = D / "_cache-embeddings.npz"


def carrega():
    split = {r["arquivo"]: r["split"] for r in csv.DictReader((D / "split.csv").open(newline="", encoding="utf-8"))}
    man = {r["arquivo"]: r for r in csv.DictReader((D / "MANIFEST.csv").open(newline="", encoding="utf-8"))}
    itens = []
    for j in (D / "normalizado").rglob("*.json"):
        crop = j.with_name(j.stem + "_tampa.jpg")
        if not crop.exists():
            continue
        try:
            rel = str(pathlib.Path(json.loads(j.read_text())["fonte"]).relative_to(D))
        except Exception:
            continue
        c = man.get(rel, {}).get("classe") or ""
        s = split.get(rel)
        if not c or c not in CLASSES or not s:
            continue
        b = man.get(rel, {}).get("bloco", "")
        dom = "apoio" if b in APOIO else ("nosso" if b.startswith("nosso") else "publico")
        itens.append({"crop": str(crop), "classe": c, "split": s, "dominio": dom})
    return itens


def embedding(caminhos):
    import torch
    import torchvision
    from torchvision import transforms
    from PIL import Image
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    m = torchvision.models.mobilenet_v3_small(weights=torchvision.models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
    m.classifier = torch.nn.Identity()
    m.eval().to(dev)
    tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                             transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
    out = []
    with torch.no_grad():
        for i in range(0, len(caminhos), 48):
            x = torch.stack([tf(Image.open(p).convert("RGB")) for p in caminhos[i:i + 48]]).to(dev)
            out.append(m(x).cpu().numpy())
    return np.vstack(out)


def main():
    from sklearn.linear_model import LogisticRegression
    itens = carrega()
    chaves = [i["crop"] for i in itens]
    if CACHE.exists() and str(np.load(CACHE, allow_pickle=False)["assinatura"]) == ",".join(chaves):
        X = np.load(CACHE, allow_pickle=False)["X"]
        print("embeddings do cache")
    else:
        X = embedding(chaves)
        np.savez(CACHE, X=X, assinatura=",".join(chaves))
    y = np.array([i["classe"] for i in itens])
    dom = np.array([i["dominio"] for i in itens])
    sp = np.array([i["split"] for i in itens])

    # 1) PCA fit no train
    m_tr = sp == "train"
    mu0 = X[m_tr].mean(0)
    _, _, Vt = np.linalg.svd(X[m_tr] - mu0, full_matrices=False)
    k = min(PCA_DIM, Vt.shape[0])
    P = Vt[:k].T
    Z = (X - mu0) @ P

    # 2) padronizacao por fonte, estatisticas SO do train
    stats = {}
    for d in sorted(set(dom.tolist())):
        m = (dom == d) & m_tr
        if m.sum() < 5:
            continue
        stats[d] = {"mu": Z[m].mean(0), "sd": Z[m].std(0) + 1e-6, "n": int(m.sum())}
    Zs = Z.copy()
    for d, st in stats.items():
        m = dom == d
        Zs[m] = (Z[m] - st["mu"]) / st["sd"]

    # 3) cabeca COM apoio (e o que o A/B mostrou melhor em defeito_tampa: 1.000)
    tre = sp == "train"
    clf = LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced", random_state=SEMENTE)
    clf.fit(Zs[tre], y[tre])

    # 4) avaliacao honesta no nosso dominio, para ir no metadado
    aval = (dom == ALVO) & ((sp == "val") | (sp == "test"))
    p = clf.predict(Zs[aval])
    rec = {}
    for c in CLASSES:
        mm = y[aval] == c
        rec[c] = float((p[mm] == c).mean()) if mm.sum() else None
    acc = float((p == y[aval]).mean()) if aval.sum() else None

    artef = D / "modelo-inferencia.npz"
    np.savez(artef, mu0=mu0, P=P, classes=np.array(clf.classes_),
             coef=clf.coef_, intercept=clf.intercept_,
             **{f"mu_{d}": v["mu"] for d, v in stats.items()},
             **{f"sd_{d}": v["sd"] for d, v in stats.items()})
    meta = {
        "vintage": "pet-infer-1 (mobilenetv3s congelado + PCA256 + padronizacao por fonte + logreg)",
        "classe_alvo_da_padronizacao": ALVO,
        "fontes_com_estatistica": {d: v["n"] for d, v in stats.items()},
        "treino": int(tre.sum()),
        "avaliacao_no_nosso_dominio": {"n": int(aval.sum()), "acuracia": acc, "recall": rec},
        "aviso": ("Padronizacao por fonte exige saber a fonte no momento da inferencia. Para a nossa "
                  "camera a fonte e 'nosso' (estatisticas do nosso train). Camera nova = recalibrar."),
    }
    (D / "modelo-inferencia.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"artefato: {artef.relative_to(D)} ({artef.stat().st_size/1e6:.1f} MB)")
    print("fontes com estatistica:", {d: v['n'] for d, v in stats.items()})
    print(f"avaliacao no nosso dominio: n={int(aval.sum())} acuracia={acc:.3f}" if acc else "sem avaliacao")
    print("recall:", {k: (None if v is None else round(v, 3)) for k, v in rec.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
