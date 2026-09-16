"""Compara EXTRATORES congelados com a MESMA receita, para escolher o melhor com evidencia.

Receita fixa (a que ja deu defeito_tampa 1,00): extrator congelado -> PCA256 (fit no train) ->
padronizacao por fonte (stats do train) -> regressao logistica balanceada.
Muda so o extrator. Avaliacao identica, no mesmo conjunto (43 de desenvolvimento), com:
recall por classe + IC95 de Wilson, FP separado, e inconclusivo no limiar 0,95 (provisorio).

Honestidade obrigatoria: 43 itens, 9 negativos. Este numero ORDENA candidatos; nao valida modelo.
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib
import sys
import time

import numpy as np
import os as _os
from pathlib import Path as _Path
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO

G = _RAIZ_REPO
D = G / "dataset"
CLASSES = ["normal", "tampa_ausente", "defeito_tampa"]
APOIO = {"externo:kmitl-bottle-cap", "externo:aitech-bottle-cap"}
SEMENTE = 7
PCA_DIM = 256
LIMIAR = 0.95
CACHE_DIR = D / "_cache-extratores"
CACHE_DIR.mkdir(exist_ok=True)

EXTRATORES = {
    "mobilenetv3s": {"tipo": "torchvision", "fn": "mobilenet_v3_small", "pesos": "IMAGENET1K_V1",
                     "size": 224, "corta": "classifier"},
    "efficientnet_b0": {"tipo": "torchvision", "fn": "efficientnet_b0", "pesos": "IMAGENET1K_V1",
                        "size": 224, "corta": "classifier"},
    "convnext_tiny": {"tipo": "torchvision", "fn": "convnext_tiny", "pesos": "IMAGENET1K_V1",
                      "size": 224, "corta": "classifier"},
    "dinov2_vits14": {"tipo": "hub", "repo": "facebookresearch/dinov2", "fn": "dinov2_vits14",
                      "size": 224, "corta": ""},
}


def carrega():
    split = {r["arquivo"]: r["split"] for r in csv.DictReader((D / "split.csv").open(newline="", encoding="utf-8"))}
    man = {r["arquivo"]: r for r in csv.DictReader((D / "MANIFEST.csv").open(newline="", encoding="utf-8"))}
    itens = []
    for j in sorted((D / "normalizado").rglob("*.json")):
        crop = j.with_name(j.stem + "_tampa.jpg")
        if not crop.exists():
            continue
        try:
            rel = str(pathlib.Path(json.loads(j.read_text())["fonte"]).relative_to(D))
        except Exception:
            continue
        c = man.get(rel, {}).get("classe") or ""
        s = split.get(rel)
        if c not in CLASSES or not s:
            continue
        b = man.get(rel, {}).get("bloco", "")
        dom = "apoio" if b in APOIO else ("nosso" if b.startswith("nosso") else "publico")
        itens.append({"crop": str(crop), "classe": c, "split": s, "dominio": dom})
    return itens


def carrega_extrator(nome, cfg):
    import torch
    if cfg["tipo"] == "torchvision":
        import torchvision
        # a enum de pesos e POR MODELO (nao existe torchvision.models.IMAGENET1K_V1)
        ENUM = {"mobilenet_v3_small": "MobileNet_V3_Small_Weights",
                "efficientnet_b0": "EfficientNet_B0_Weights",
                "convnext_tiny": "ConvNeXt_Tiny_Weights"}
        pesos = None
        if cfg["pesos"]:
            pesos = getattr(torchvision.models, ENUM[cfg["fn"]]).IMAGENET1K_V1
        m = getattr(torchvision.models, cfg["fn"])(weights=pesos)
    else:
        m = torch.hub.load(cfg["repo"], cfg["fn"], pretrained=True, trust_repo=True)
    if cfg["corta"]:
        setattr(m, cfg["corta"], torch.nn.Identity())
    m.eval()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    return m.to(dev), dev


def extrai(nome, cfg, caminhos):
    cache = CACHE_DIR / f"{nome}.npz"
    assin = ",".join(caminhos[:20]) + f"|{len(caminhos)}|{cfg['size']}"
    if cache.exists():
        z = np.load(cache, allow_pickle=False)
        if str(z["assinatura"]) == assin:
            return z["X"], "cache"
    import torch
    from PIL import Image
    from torchvision import transforms
    m, dev = carrega_extrator(nome, cfg)
    tf = transforms.Compose([transforms.Resize((cfg["size"], cfg["size"])), transforms.ToTensor(),
                             transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
    saida = []
    t0 = time.time()
    with torch.no_grad():
        for i in range(0, len(caminhos), 32):
            x = torch.stack([tf(Image.open(p).convert("RGB")) for p in caminhos[i:i + 32]]).to(dev)
            e = m(x)
            if isinstance(e, dict):
                e = e.get("x_norm_clstoken", list(e.values())[0])
            saida.append(e.flatten(1).cpu().numpy())
    X = np.vstack(saida)
    np.savez(cache, X=X, assinatura=assin)
    return X, f"{time.time()-t0:.0f}s ({dev})"


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    mm = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - mm), min(1.0, c + mm))


def avalia(X, itens):
    from sklearn.linear_model import LogisticRegression
    y = np.array([i["classe"] for i in itens])
    dom = np.array([i["dominio"] for i in itens])
    sp = np.array([i["split"] for i in itens])
    m_tr = sp == "train"
    mu0 = X[m_tr].mean(0)
    _, _, Vt = np.linalg.svd(X[m_tr] - mu0, full_matrices=False)
    k = min(PCA_DIM, Vt.shape[0])
    P = Vt[:k].T
    Z = (X - mu0) @ P
    stats = {}
    for d in sorted(set(dom.tolist())):
        m = (dom == d) & m_tr
        if m.sum() >= 5:
            stats[d] = {"mu": Z[m].mean(0), "sd": Z[m].std(0) + 1e-6}
    Zs = Z.copy()
    for d, st in stats.items():
        Zs[dom == d] = (Z[dom == d] - st["mu"]) / st["sd"]
    clf = LogisticRegression(C=0.5, max_iter=4000, class_weight="balanced", random_state=SEMENTE)
    clf.fit(Zs[m_tr], y[m_tr])
    classes = list(clf.classes_)
    aval = (dom == "nosso") & ((sp == "val") | (sp == "test"))
    Pa = clf.predict_proba(Zs[aval])
    pred = np.array([classes[int(i)] for i in Pa.argmax(1)])
    conf = Pa.max(1)
    yv = y[aval]
    pred_abst = np.where(conf >= LIMIAR, pred, "inconclusivo")
    res = {"n": int(aval.sum()), "por_classe": {}, "inconclusivo": float((pred_abst == "inconclusivo").mean())}
    for c in CLASSES:
        m = yv == c
        n = int(m.sum())
        k = int((pred[m] == c).sum())
        li, ls = wilson(k, n)
        fp = int(((pred == c) & (yv != c)).sum())
        res["por_classe"][c] = {"n": n, "recall": (k / n if n else None), "ic95": [li, ls], "fn": n - k, "fp": fp}
    rec = [v["recall"] for v in res["por_classe"].values() if v["recall"] is not None]
    res["recall_medio"] = float(np.mean(rec)) if rec else None
    res["classe"] = classes
    return res, (mu0, P, stats, clf.coef_, clf.intercept_, classes)


def main():
    itens = carrega()
    print(f"recortes: {len(itens)} | {dict(collections.Counter(i['dominio'] for i in itens))}", flush=True)
    caminhos = [i["crop"] for i in itens]
    resultados, artefatos = {}, {}
    for nome, cfg in EXTRATORES.items():
        print(f"\n== {nome} ==", flush=True)
        try:
            X, como = extrai(nome, cfg, caminhos)
            print(f"   features: {X.shape} ({como})", flush=True)
            res, art = avalia(X, itens)
            resultados[nome] = res
            artefatos[nome] = art
            for c, v in res["por_classe"].items():
                print("   %-14s recall=%-6s IC95 [%.2f, %.2f] n=%d FN=%d FP=%d" % (
                    c, (f"{v['recall']:.3f}" if v["recall"] is not None else "-"),
                    v["ic95"][0], v["ic95"][1], v["n"], v["fn"], v["fp"]), flush=True)
            print(f"   recall medio {res['recall_medio']:.3f} | inconclusivo {100*res['inconclusivo']:.1f}%", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"   FALHOU: {type(e).__name__}: {e}", flush=True)
            resultados[nome] = {"erro": f"{type(e).__name__}: {e}"}

    validos = {k: v for k, v in resultados.items() if "erro" not in v}
    if not validos:
        print("\nnenhum extrator funcionou"); return 1
    # criterio declarado: maior recall de defeito_tampa; desempate pelo recall medio
    melhor = max(validos, key=lambda k: ((validos[k]["por_classe"]["defeito_tampa"]["recall"] or 0),
                                         validos[k]["recall_medio"] or 0))
    print(f"\n== ESCOLHIDO: {melhor} ==", flush=True)
    (D / "_COMPARACAO-EXTRATORES.json").write_text(json.dumps(
        {"criterio": "maior recall de defeito_tampa, desempate por recall medio",
         "conjunto": "43 de desenvolvimento (nao teste)", "limiar_abstencao": LIMIAR,
         "escolhido": melhor, "resultados": resultados}, ensure_ascii=False, indent=1), encoding="utf-8")

    mu0, P, stats, coef, inter, classes = artefatos[melhor]
    import shutil
    for p in (D / "modelo-inferencia.npz", D / "modelo-inferencia.json"):
        if p.exists():
            shutil.copy2(p, p.with_suffix(p.suffix + ".bkp-20260914-extrator"))
    np.savez(D / "modelo-inferencia.npz", mu0=mu0, P=P, classes=np.array(classes),
             coef=coef, intercept=inter,
             **{f"mu_{d}": v["mu"] for d, v in stats.items()},
             **{f"sd_{d}": v["sd"] for d, v in stats.items()})
    meta = {"vintage": f"pet-infer-3 ({melhor} congelado + PCA256 + padronizacao por fonte + logreg)",
            "extrator": melhor, "config_extrator": EXTRATORES[melhor],
            "aviso": ("PROTOTIPO, NAO VALIDADO: avaliacao = 43 de desenvolvimento, nao teste; "
                      "sem verificacao de presenca; escopo = recorte de gargalo."),
            "avaliacao": validos[melhor], "limiar_abstencao": LIMIAR,
            "comparacao": {k: {"recall_medio": v.get("recall_medio"),
                               "defeito_recall": v.get("por_classe", {}).get("defeito_tampa", {}).get("recall")}
                           for k, v in resultados.items()}}
    (D / "modelo-inferencia.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print("artefato exportado: dataset/modelo-inferencia.npz (.bkp com o anterior)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
