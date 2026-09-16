#!/usr/bin/env python3
"""Calibra o limiar por classe NA VALIDAÇÃO (protocolo correto) e grava no contrato.

Por que separado: hoje o limiar foi escolhido no teste (inflou ~0,14 de F1). Este script faz o
fluxo certo; varre na val, escolhe lá, e reporta o que o teste dá com a escolha. Depois
atualiza `limiares_por_imgsz` no contrato de pré-processamento e marca como calibrado.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

CONFS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)


def iou(a, b) -> float:
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def avalia(modelo, ds: Path, split: str, conf: float, imgsz: int):
    tp, fp, fn = Counter(), Counter(), Counter()
    for img in sorted((ds / 'images' / split).glob('*')):
        lab = ds / 'labels' / split / (img.stem + '.txt')
        gt = []
        if lab.is_file():
            for l in lab.read_text().splitlines():
                p = l.split()
                if len(p) == 5:
                    cl, cx, cy, w, h = int(p[0]), *map(float, p[1:])
                    with Image.open(img) as im:
                        L, A = im.size
                    gt.append((cl, ((cx - w / 2) * L, (cy - h / 2) * A, (cx + w / 2) * L, (cy + h / 2) * A)))
        r = modelo.predict(str(img), imgsz=imgsz, conf=conf, verbose=False)[0]
        caixas = []
        if r.boxes is not None and len(r.boxes):
            xy = r.boxes.xyxy.cpu().numpy()
            cl = r.boxes.cls.cpu().numpy().astype(int)
            caixas = [(int(c), tuple(float(v) for v in b)) for b, c in zip(xy, cl)]
        usados = set()
        for cg, bg in gt:
            achou = False
            for k, (cp, bp) in enumerate(caixas):
                if k in usados or cp != cg:
                    continue
                if iou(bg, bp) >= 0.3:
                    usados.add(k); achou = True; break
            tp[cg] += 1 if achou else 0
            fn[cg] += 0 if achou else 1
        for k, (cp, _) in enumerate(caixas):
            if k not in usados:
                fp[cp] += 1
    f1 = {}
    for i in range(3):
        P = tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) else 0.0
        R = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) else 0.0
        f1[i] = 2 * P * R / (P + R) if (P + R) else 0.0
    return {'f1': f1, 'macro': sum(f1.values()) / 3, 'tp': tp, 'fp': fp, 'fn': fn}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--peso', required=True)
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--contrato', default=None, help='preprocessamento.json para atualizar os limiares')
    ap.add_argument('--saida', default='/var/tmp/calibracao-limiar.json')
    a = ap.parse_args()

    ds = Path(a.dataset)
    m = YOLO(a.peso)
    nomes = ['normal', 'tampa_ausente', 'defeito_tampa']

    # 1) varredura na VAL: escolhe o limiar POR CLASSE que maximiza o F1 daquela classe
    por_classe = {i: [] for i in range(3)}
    for conf in CONFS:
        r = avalia(m, ds, 'val', conf, a.imgsz)
        for i in range(3):
            por_classe[i].append((conf, r['f1'][i]))
        print(f'  val conf {conf:.2f}: macro {r["macro"]:.3f} | '
              + ' '.join(f'{nomes[i]}={r["f1"][i]:.3f}' for i in range(3)))

    escolhidos = {}
    for i in range(3):
        c, v = max(por_classe[i], key=lambda x: x[1])
        escolhidos[nomes[i]] = {'conf': c, 'f1_val': round(v, 3)}
    print('\n  limiar escolhido NA VAL por classe:', {k: v['conf'] for k, v in escolhidos.items()})

    # 2) o que o TESTE dá com os limiares escolhidos (uma passada por limiar distinto)
    teste = {}
    for conf in sorted({v['conf'] for v in escolhidos.values()}):
        r = avalia(m, ds, 'test', conf, a.imgsz)
        teste[str(conf)] = {'f1': {nomes[i]: round(r['f1'][i], 3) for i in range(3)},
                            'macro': round(r['macro'], 3)}
        print(f'  teste conf {conf:.2f}: macro {r["macro"]:.3f} f1 {teste[str(conf)]["f1"]}')

    saida = {'peso': a.peso, 'dataset': str(ds), 'imgsz': a.imgsz,
             'limiares_escolhidos_na_val': escolhidos, 'teste_por_limiar': teste,
             'obs': 'limiar por classe escolhido na VAL (protocolo correto), medido no teste depois'}
    Path(a.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=1))

    if a.contrato:
        c = json.loads(Path(a.contrato).read_text())
        c['limiares_por_imgsz'][str(a.imgsz)] = {
            **{n: escolhidos[n]['conf'] for n in nomes},
            'calibrado': True,
            'f1_val_por_classe': {n: escolhidos[n]['f1_val'] for n in nomes},
            'fonte': 'calibra_limiar_val.py',
        }
        Path(a.contrato).write_text(json.dumps(c, ensure_ascii=False, indent=1))
        print('  contrato atualizado:', a.contrato)
    print('gravado:', a.saida)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
