#!/usr/bin/env python3
"""Avaliacao OOD do detector contra o MVTec AD (benchmark, fora do dominio PET).

Contexto (analises anteriores, fora deste repositorio): MVTec AD bottle e LOCO juice_bottle entram
como benchmark, nunca como classe - anomalia generica != estado de tampa, e MVTec nao garante PET.
As referencias publicas de dataset estao em `docs/reference/datasets-externos-roboflow.md`.

Este modulo NAO anota nada no Label Studio. Ele mede o modelo treinado contra a
verdade do MVTec, offline:

  * nivel de imagem : AUROC entre imagens `good` e imagens defeituosas, por categoria
  * nivel de pixel  : AUROC por pixel (mascara da fonte) quando o scorer devolve mapa
  * caixas          : recall/precisao por IoU quando o scorer devolve caixas

Scorer e um alvo plugavel "modulo:funcao":
  - funcao(caminho) -> float            (probabilidade de defeito)
  - funcao(caminho) -> ndarray (H,W)    (mapa de anomalia; ativa AUROC de pixel)
  - funcao(caminho) -> list[box]        (boxes [x1,y1,x2,y2] em pixel; ativa modo caixa)

Autoteste deterministico (nao depende de modelo):
  python avaliacao_ood.py --mvtec RAIZ --baseline oracle
  python avaliacao_ood.py --mvtec RAIZ --baseline aleatorio --seed 7
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

CATEGORIAS_PADRAO = ("bottle",)
# defeitos do MVTec que nao sao imagem (pasta auxiliar)
IGNORAR = {"ground_truth", "license.txt", "readme.txt"}


def auroc(positivos, negativos) -> float:
    """AUROC por estatistica de postos (Mann-Whitney), sem sklearn."""
    pos = np.asarray(positivos, dtype=float)
    neg = np.asarray(negativos, dtype=float)
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    todos = np.concatenate([pos, neg])
    ordem = todos.argsort()
    postos = np.empty_like(ordem, dtype=float)
    postos[ordem] = np.arange(1, todos.size + 1)
    # empates recebem posto medio
    valores, contagens = np.unique(todos, return_counts=True)
    for v, c in zip(valores, contagens, strict=False):
        if c > 1:
            idx = np.nonzero(todos == v)[0]
            postos[idx] = postos[idx].mean()
    r_pos = postos[: pos.size].sum()
    u = r_pos - pos.size * (pos.size + 1) / 2
    return float(u / (pos.size * neg.size))


def iou(a, b) -> float:
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    uniao = area_a + area_b - inter
    return float(inter / uniao) if uniao > 0 else 0.0


def caixa_da_mascara(mascara: Path) -> tuple[int, int, int, int] | None:
    if np is None:
        return None
    try:
        from PIL import Image
    except ImportError:
        return None
    with Image.open(mascara) as im:
        arr = np.asarray(im.convert("L")) > 0
    ys, xs = np.nonzero(arr)
    if ys.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def imagens_da_categoria(raiz: Path, categoria: str):
    """Devolve (defeito, caminho_imagem, caminho_mascara|None) para a categoria."""
    base = raiz / categoria
    if not base.is_dir():
        return []
    itens = []
    for pasta in sorted(base.glob("test/*")):
        if not pasta.is_dir():
            continue
        defeito = pasta.name
        for img in sorted(
            p for p in pasta.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")
        ):
            mascara = base / "ground_truth" / defeito / (img.stem + "_mask.png")
            itens.append((defeito, img, mascara if mascara.is_file() else None))
    return itens


def scorer_baseline(nome: str, seed: int, defeito: str, mascara: Path | None):
    """Baselines usados no autoteste do proprio harness."""
    if nome == "oracle":
        return 1.0 if defeito != "good" else 0.0
    if nome == "oracle-invertido":  # teste de mutação do próprio harness
        return 0.0 if defeito != "good" else 1.0
    if nome == "oracle-mapa":
        if mascara is None:
            return np.zeros((16, 16), dtype=float)
        from PIL import Image

        with Image.open(mascara) as im:
            return (np.asarray(im.convert("L").resize((16, 16))) > 0).astype(float)
    if nome == "aleatorio":
        r = random.Random(f"{seed}:{defeito}")  # seed já inclui o nome do arquivo
        return r.random()
    raise SystemExit(f"baseline desconhecido: {nome}")


def carrega_scorer(alvo: str):
    modulo, _, funcao = alvo.partition(":")
    caminho = Path(modulo).resolve()
    sys.path.insert(0, str(caminho.parent))
    spec = __import__(caminho.stem)
    return getattr(spec, funcao)


def avalia(
    raiz: Path, categorias, scorer, nome_scorer: str, iou_min: float, passo_pixel: int
):
    relatorio = {
        "scorer": nome_scorer,
        "raiz": str(raiz),
        "categorias": {},
        "iou_min": iou_min,
    }
    for categoria in categorias:
        itens = imagens_da_categoria(raiz, categoria)
        if not itens:
            relatorio["categorias"][categoria] = {"erro": "sem imagens"}
            continue
        pont_pos, pont_neg, masc_ok = [], [], 0
        pixel_pos, pixel_neg = [], []
        acertos_caixa = 0
        total_defeito = 0
        falsos_positivos_good = 0
        total_good = 0
        modo = None
        for defeito, img, mascara in itens:
            saida = scorer(str(img))
            if modo is None:
                if np is not None and isinstance(saida, np.ndarray):
                    modo = "mapa"
                elif isinstance(saida, (list, tuple)):
                    modo = "caixa"
                else:
                    modo = "imagem"
            if modo == "imagem":
                (pont_pos if defeito != "good" else pont_neg).append(float(saida))
            elif modo == "mapa":
                mapa = np.asarray(saida, dtype=float)
                if mascara is not None:
                    from PIL import Image

                    with Image.open(mascara) as im:
                        m = np.asarray(im.convert("L").resize(mapa.shape[::-1])) > 0
                    masc_ok += 1
                else:
                    m = np.zeros_like(mapa, dtype=bool)
                amostra = mapa[::passo_pixel, ::passo_pixel].ravel()
                rot = m[::passo_pixel, ::passo_pixel].ravel()
                pixel_pos.extend(amostra[rot].tolist())
                pixel_neg.extend(amostra[~rot].tolist())
            else:  # caixa
                if defeito == "good":
                    total_good += 1
                    if saida:
                        falsos_positivos_good += 1
                else:
                    total_defeito += 1
                    gt = caixa_da_mascara(mascara) if mascara else None
                    if gt and any(iou(b, gt) >= iou_min for b in saida):
                        acertos_caixa += 1
        entrada = {
            "imagens": len(itens),
            "modo": modo,
            "good": sum(1 for d, _, _ in itens if d == "good"),
            "defeito": sum(1 for d, _, _ in itens if d != "good"),
        }
        if modo == "imagem":
            entrada["auroc_imagem"] = round(auroc(pont_pos, pont_neg), 4)
        elif modo == "mapa":
            entrada["auroc_pixel"] = round(auroc(pixel_pos, pixel_neg), 4)
            entrada["mascaras_usadas"] = masc_ok
        else:
            entrada["recall_defeito"] = (
                round(acertos_caixa / total_defeito, 4) if total_defeito else None
            )
            entrada["fpr_good"] = (
                round(falsos_positivos_good / total_good, 4) if total_good else None
            )
        relatorio["categorias"][categoria] = entrada
    return relatorio


def main() -> int:
    ap = argparse.ArgumentParser(description="AUROC OOD do detector contra o MVTec AD")
    ap.add_argument(
        "--mvtec", required=True, help="raiz do MVTec (com <categoria>/test/<defeito>/)"
    )
    ap.add_argument("--categorias", nargs="*", default=list(CATEGORIAS_PADRAO))
    ap.add_argument("--scorer", help='alvo "modulo:funcao" para o modelo real')
    ap.add_argument(
        "--baseline",
        choices=["oracle", "oracle-invertido", "oracle-mapa", "aleatorio"],
        help="baseline deterministico (autoteste do harness)",
    )
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--iou-min", type=float, default=0.3)
    ap.add_argument("--passo-pixel", type=int, default=4)
    ap.add_argument("--saida", default="relatorio-ood.json")
    a = ap.parse_args()

    raiz = Path(a.mvtec)
    if not raiz.is_dir():
        print("raiz inexistente:", raiz)
        return 2
    if a.baseline:
        nome = f"baseline:{a.baseline}"
        def scorer(caminho):
            return _baseline_por_imagem(a.baseline, a.seed, raiz, caminho)
    elif a.scorer:
        nome = a.scorer
        scorer = carrega_scorer(a.scorer)
    else:
        print("informe --scorer ou --baseline")
        return 2

    rel = avalia(raiz, a.categorias, scorer, nome, a.iou_min, a.passo_pixel)
    rel["mvtec_sha256_manifesto"] = hashlib.sha256(
        json.dumps(
            sorted(
                str(p.relative_to(raiz))
                for c in a.categorias
                for _, p, _ in imagens_da_categoria(raiz, c)
            )
        ).encode()
    ).hexdigest()[:32]
    Path(a.saida).write_text(json.dumps(rel, ensure_ascii=False, indent=1))
    print(json.dumps(rel, ensure_ascii=False, indent=1))
    return 0


def _baseline_por_imagem(nome: str, seed: int, raiz: Path, caminho: str):
    """Descobre o defeito pelo caminho (test/<defeito>/<arquivo>) e chama o baseline."""
    p = Path(caminho)
    defeito = p.parent.name
    mascara = None
    # mascara: <raiz>/<categoria>/ground_truth/<defeito>/<stem>_mask.png
    if "test" in p.parts:
        idx = p.parts.index("test")
        base = Path(*p.parts[:idx])
        cand = base / "ground_truth" / defeito / (p.stem + "_mask.png")
        mascara = cand if cand.is_file() else None
    # semente por IMAGEM (nome do arquivo), senão todas as imagens de uma pasta
    # recebem o mesmo valor e o baseline aleatório vira separador perfeito por acaso
    return scorer_baseline(nome, f"{seed}:{p.name}", defeito, mascara)


if __name__ == "__main__":
    sys.exit(main())
