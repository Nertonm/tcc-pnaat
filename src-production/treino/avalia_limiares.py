#!/usr/bin/env python3
"""Varredura de limiar por classe; a tabela honesta para "detectar com limiar baixo".

Para cada limiar de confiança: casa predição x verdade por IoU e classe, e reporta
precisão/recall/F1 por classe. Serve para mostrar o trade-off (recall alto x falsos
positivos) especialmente na classe com poucos exemplos (corpo_deformidade).

Uso: python avalia_limiares.py --dataset DIR --peso W [--split test] [--confs 0.05,0.15,0.3]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from ultralytics import YOLO


def iou(a, b) -> float:
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--peso', required=True)
    ap.add_argument('--split', default='test')
    ap.add_argument('--confs', default='0.05,0.15,0.30')
    ap.add_argument('--iou-min', type=float, default=0.3)
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--saida', default=None)
    a = ap.parse_args()

    base = Path(a.dataset)
    names = {}
    for linha in (base / 'data.yaml').read_text().splitlines():
        if linha.startswith('names:'):
            names = [x.strip().strip("'\"") for x in linha.split(':', 1)[1].strip().strip('[]').split(',')]
    print('classes do dataset:', names)

    img_dir = base / 'images' / a.split
    lab_dir = base / 'labels' / a.split
    imagens = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
    print(f'imagens no split {a.split}: {len(imagens)}')

    modelo = YOLO(a.peso)
    confs = [float(c) for c in a.confs.split(',')]
    resultado = {'peso': a.peso, 'dataset': str(base), 'split': a.split, 'iou_min': a.iou_min,
                 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'limiares': {}}

    for conf in confs:
        tp, fp, fn = Counter(), Counter(), Counter()
        for img in imagens:
            lab = lab_dir / (img.stem + '.txt')
            gt = []
            if lab.is_file():
                for linha in lab.read_text().splitlines():
                    c = linha.split()
                    if len(c) == 5:
                        cls, cx, cy, w, h = int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4])
                        with Image.open(img) as im:
                            L, A = im.size
                        gt.append((cls, ((cx - w / 2) * L, (cy - h / 2) * A,
                                         (cx + w / 2) * L, (cy + h / 2) * A)))
            pred = modelo.predict(str(img), imgsz=a.imgsz, conf=conf, verbose=False)[0]
            caixas = []
            if pred.boxes is not None and len(pred.boxes):
                xyxy = pred.boxes.xyxy.cpu().numpy()
                cls = pred.boxes.cls.cpu().numpy().astype(int)
                caixas = [(int(c), tuple(float(v) for v in b)) for b, c in zip(xyxy, cls, strict=False)]
            usados = set()
            for cg, bg in gt:
                achou = False
                for i, (cp, bp) in enumerate(caixas):
                    if i in usados or cp != cg:
                        continue
                    if iou(bg, bp) >= a.iou_min:
                        usados.add(i)
                        achou = True
                        break
                if achou:
                    tp[cg] += 1
                else:
                    fn[cg] += 1
            for i, (cp, _) in enumerate(caixas):
                if i not in usados:
                    fp[cp] += 1
        por_classe = {}
        for idx, nome in enumerate(names):
            P = tp[idx] / (tp[idx] + fp[idx]) if (tp[idx] + fp[idx]) else 0.0
            R = tp[idx] / (tp[idx] + fn[idx]) if (tp[idx] + fn[idx]) else 0.0
            F1 = 2 * P * R / (P + R) if (P + R) else 0.0
            por_classe[nome] = {'tp': tp[idx], 'fp': fp[idx], 'fn': fn[idx],
                                'precisao': round(P, 4), 'recall': round(R, 4), 'f1': round(F1, 4)}
        macro = sum(v['f1'] for v in por_classe.values()) / len(por_classe) if por_classe else 0
        resultado['limiares'][str(conf)] = {'por_classe': por_classe, 'f1_macro': round(macro, 4)}
        print(f'\n--- conf {conf} (IoU {a.iou_min}) ---')
        for nome, v in por_classe.items():
            print(f"  {nome:16s} tp={v['tp']:3d} fp={v['fp']:3d} fn={v['fn']:3d} "
                  f"P={v['precisao']:.3f} R={v['recall']:.3f} F1={v['f1']:.3f}")
        print(f'  F1 macro: {macro:.3f}')

    destino = Path(a.saida) if a.saida else base.parent / f'limiares-{a.split}.json'
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=1))
    print('\ngravado:', destino)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
