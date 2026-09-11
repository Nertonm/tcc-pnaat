"""Rascunho da PoC-02 (versao que roda): conjuntos publicos -> recortes -> classificador leve -> avaliacao.

Feio de proposital: CPU, sem instalar nada (torch, torchvision, sklearn, cv2 do venv do projeto).
Cobre os dois formatos que temos:
  - Roboflow: <projeto>/<split>/{images,labels} + classes por nome no data.yaml
  - Kaggle:   <projeto>/{images,labels}/<split> + classe pelo prefixo do arquivo e caixa alvo no yaml
Uso:  python rascunho.py [--limite 1200] [--so-avaliar]
Saidas: ~/tcc-pnaat/datasets/classify_externo, ~/tcc-pnaat/resultados_publico/{manifest.csv,predicoes.json,anotados/}
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import subprocess
import time
from collections import Counter
from pathlib import Path

RAIZ = Path.home() / "tcc-pnaat"
EXT = RAIZ / "datasets/externos"
DEST = RAIZ / "datasets/classify_externo"
OUT = RAIZ / "resultados_publico"
PY = RAIZ / "github/.venv/bin/python"
HARNESS = RAIZ / "github/code-workspace/scripts/avaliar_poc02.py"
LADO, MARGEM, SEED = 224, 0.08, 1234

# nome de classe publica -> nossa classe (Roboflow)
MAPA_NOME = {}
for c in ("no_cap", "no-cap", "No Cap", "Missing cap"):
    MAPA_NOME[c] = "tampa_ausente"
for c in ("misplaced_cap", "Loose Cap", "loos-cap", "Unclosed"):
    MAPA_NOME[c] = "tampa_mal_rosqueada"
for c in ("good_cap", "Good Cap", "Closed", "cap", "good"):
    MAPA_NOME[c] = "normal"

# prefixo do arquivo -> (nossa classe, classe da caixa a recortar) no conjunto Kaggle
MAPA_KAGGLE = {
    "good": ("normal", "bottle_ron88"),
    "no_cap": ("tampa_ausente", "defect_no_cap"),
    "loose_cap": ("tampa_mal_rosqueada", "defect_loose_cap"),
}


def ler_nomes(yaml_path: Path) -> list[str]:
    linhas, out, dentro, bloco = yaml_path.read_text(errors="ignore").splitlines(), [], False, {}
    for l in linhas:
        if l.strip().startswith("names:"):
            resto = l.split(":", 1)[1].strip()
            if resto.startswith("["):
                return [x.strip().strip("'\"") for x in resto.strip("[]").split(",")]
            dentro = True
            continue
        if dentro:
            if ":" in l and l.strip()[0].isdigit():
                k, v = l.split(":", 1)
                bloco[int(k.strip())] = v.split("#")[0].strip().strip("'\"")
            elif l.strip().startswith("- "):
                out.append(l.strip()[2:].strip().strip("'\""))
            elif l.strip() and not l.startswith(" "):
                break
    return [bloco[k] for k in sorted(bloco)] if bloco else out


def caixas(lab: Path):
    for l in lab.read_text(errors="ignore").splitlines():
        p = l.split()
        if len(p) >= 5 and p[0].lstrip("-").isdigit():
            yield int(float(p[0])), (float(p[1]), float(p[2]), float(p[3]), float(p[4]))


def recorta(cv2, img: Path, cx, cy, bw, bh, saida: Path):
    im = cv2.imread(str(img))
    if im is None:
        return False
    h, w = im.shape[:2]
    x1 = max(0, int((cx - bw / 2) * w - MARGEM * bw * w))
    y1 = max(0, int((cy - bh / 2) * h - MARGEM * bh * h))
    x2 = min(w, int((cx + bw / 2) * w + MARGEM * bw * w))
    y2 = min(h, int((cy + bh / 2) * h + MARGEM * bh * h))
    if x2 - x1 < 16 or y2 - y1 < 16:
        return False
    saida.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(saida), cv2.resize(im[y1:y2, x1:x2], (LADO, LADO)), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return True


def coleta(limite: int):
    import cv2
    linhas, por_classe, ignoradas, vistos = [], Counter(), Counter(), set()

    for proj in sorted(p for p in EXT.iterdir() if p.is_dir()):
        yml = proj / "data.yaml"
        if not yml.exists():
            continue
        cls = ler_nomes(yml)
        flat = (proj / "images").is_dir()  # layout Kaggle
        partes = [("images/" + s, "labels/" + s, s) for s in ("train", "val")] if flat else \
                 [(s + "/images", s + "/labels", s) for s in ("train", "valid", "test")]

        for dir_img, dir_lab, split in partes:
            limg, llab = proj / dir_img, proj / dir_lab
            if not limg.is_dir():
                continue
            for img in sorted(limg.glob("*.jpg")) + sorted(limg.glob("*.png")):
                stem = "%s__%s" % (proj.name, img.stem)
                if stem in vistos:
                    continue
                lab = llab / (img.stem + ".txt")
                if not lab.exists():
                    continue
                alvo = alvo_caixa = None
                if flat:  # Kaggle: classe pelo prefixo do nome, caixa alvo pelo yaml
                    prefixo = img.stem.rsplit("_", 3)[0]
                    regra = MAPA_KAGGLE.get(prefixo) or MAPA_KAGGLE.get(prefixo.split("_")[0])
                    if not regra or prefixo.split("_")[0] not in ("good", "no", "loose"):
                        ignoradas[prefixo] += 1
                        continue
                    alvo, alvo_caixa = regra
                melhor = None
                for cid, (cx, cy, bw, bh) in caixas(lab):
                    nome = cls[cid] if cid < len(cls) else "?"
                    if flat:
                        if nome != alvo_caixa:
                            continue
                        escolhida = (bw * bh, alvo, cx, cy, bw, bh, nome)
                    else:
                        mapeada = MAPA_NOME.get(nome)
                        if mapeada is None:
                            ignoradas[nome] += 1
                            continue
                        escolhida = (bw * bh, mapeada, cx, cy, bw, bh, nome)
                    if melhor is None or escolhida[0] > melhor[0]:
                        melhor = escolhida
                if melhor is None:
                    continue
                vistos.add(stem)
                _, alvo, cx, cy, bw, bh, nome_publico = melhor
                destino = DEST / alvo / (stem + ".jpg")
                if not recorta(cv2, img, cx, cy, bw, bh, destino):
                    continue
                hh = int(hashlib.sha256(stem.encode()).hexdigest()[:8], 16) % 100
                parte = "train" if hh < 70 else ("val" if hh < 85 else "test")
                linhas.append({"item_id": stem, "fonte": proj.name, "classe_verdade": alvo,
                               "arquivo": str(destino), "classe_publica": nome_publico, "split": parte})
                por_classe[alvo] += 1

    print("recortes: %d | por classe: %s" % (len(linhas), dict(por_classe)))
    print("classes ignoradas: %s" % dict(ignoradas.most_common(6)))
    random.Random(SEED).shuffle(linhas)
    sel, cont = [], Counter()
    for r in linhas:
        if cont[r["classe_verdade"]] < limite:
            sel.append(r)
            cont[r["classe_verdade"]] += 1
    print("apos balancear (%d por classe): %d | por split: %s"
          % (limite, len(sel), dict(Counter(r["split"] for r in sel))))
    return sel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=1200)
    ap.add_argument("--so-avaliar", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    if a.so_avaliar and (OUT / "manifest.csv").exists():
        pass
    else:
        linhas = coleta(a.limite)
        import numpy as np
        import torch
        from sklearn.linear_model import LogisticRegression
        from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small
        import cv2

        pesos = MobileNet_V3_Small_Weights.DEFAULT
        modelo = mobilenet_v3_small(weights=pesos)
        modelo.classifier = torch.nn.Identity()
        modelo.eval()
        prep = pesos.transforms()
        X = np.zeros((len(linhas), 576), dtype="float32")
        with torch.no_grad():
            lote = []
            for i, r in enumerate(linhas):
                im = cv2.cvtColor(cv2.imread(r["arquivo"]), cv2.COLOR_BGR2RGB)
                lote.append(prep(torch.from_numpy(im).permute(2, 0, 1)))
                if len(lote) == 64 or i == len(linhas) - 1:
                    X[i - len(lote) + 1:i + 1] = modelo(torch.stack(lote)).numpy()
                    lote = []
        tr = [i for i, r in enumerate(linhas) if r["split"] == "train"]
        te = [i for i, r in enumerate(linhas) if r["split"] == "test"]
        clf = LogisticRegression(max_iter=1000, n_jobs=-1)
        clf.fit(X[tr], [linhas[i]["classe_verdade"] for i in tr])
        print("acuracia: treino %.3f | teste %.3f (treino=%d teste=%d) em %.0fs"
              % (clf.score(X[tr], [linhas[i]["classe_verdade"] for i in tr]),
                 clf.score(X[te], [linhas[i]["classe_verdade"] for i in te]), len(tr), len(te), time.time() - t0))
        proba, pred = clf.predict_proba(X[te]), clf.predict(X[te])
        (OUT / "predicoes.json").write_text(json.dumps(
            {linhas[i]["item_id"]: {"classe": str(pred[k]), "confianca": float(proba[k].max()),
                                    "medidas": {}, "motivos": []} for k, i in enumerate(te)}))
        with (OUT / "manifest.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["item_id", "fonte", "classe_verdade", "arquivo"])
            w.writeheader()
            for i in te:
                w.writerow({k: linhas[i][k] for k in ("item_id", "fonte", "classe_verdade", "arquivo")})

    print("\n===== RELATORIO (harness da PoC-02) =====")
    p = subprocess.run([PY, str(HARNESS), "--manifest", str(OUT / "manifest.csv"),
                        "--predicoes", str(OUT / "predicoes.json"), "--anotar", str(OUT / "anotados")],
                       capture_output=True, text=True, timeout=3000)
    print(p.stdout.strip() or p.stderr.strip()[-500:])


if __name__ == "__main__":
    main()
