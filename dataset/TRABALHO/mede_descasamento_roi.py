#!/usr/bin/env python3
"""Custo medido do descasamento treino x deploy: o modelo foi treinado no RECORTE da ROI;
o deploy consome o QUADRO INTEIRO. Quanto isso custa?

Método (falsificável):
  - mesmas 18 imagens de teste do split por item
  - (A) entrada = recorte da ROI  -> números do relatório
  - (B) entrada = quadro inteiro  -> as caixas detectadas são mapeadas PARA o espaço da ROI
        (afim por eixo: (x_frac - rx)/rw) e comparadas com os rótulos, que vivem no espaço da ROI
  - mesmo protocolo de casamento (IoU>=0,3, mesma classe)

Não é estimativa: é a mesma métrica, com a entrada diferente.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

G = Path(__file__).resolve().parents[2]
M = G.parent.parent / 'pnaat-modelos'
DS = M / 'v7-3-lateral-detector-roi/dataset'
BASE_LATERAL = M / 'ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt'
PESO = M / 'v7a-lateral-detector-roi/runs/v7a-rig/weights/best.pt'
ROI_JSON = G / 'dataset/TRABALHO/roi-por-camera.json'
RAIZES = (G, Path('/srv/label-studio/corpus'), Path('/srv/label-studio'))

roi = {c: v['roi_normalizada'] for c, v in json.loads(ROI_JSON.read_text())['cameras'].items()
       if v.get('roi_normalizada')}
man = json.loads((DS / 'manifest.json').read_text())
itens = [i for i in man['itens'] if i['split'] == 'test']


def resolve(rel: str):
    for r in RAIZES:
        p = r / rel
        if p.is_file():
            return p
    return None


def camera(rel: str) -> str:
    for c in ('csi', 'usb', 'espcam'):
        if c in rel:
            return c
    return 'rig'


def iou(a, b) -> float:
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def metricas(modelo, modo: str):
    tp, fp, fn = Counter(), Counter(), Counter()
    for it in itens:
        img_crop = DS / 'images/test' / it['arquivo']
        lab = DS / 'labels/test' / (Path(it['arquivo']).stem + '.txt')
        gt = []
        if lab.is_file():
            for l in lab.read_text().splitlines():
                p = l.split()
                if len(p) == 5:
                    gt.append((int(p[0]), tuple(map(float, p[1:]))))  # já no espaço da ROI (cx cy w h)
        if modo == 'crop':
            entrada = img_crop
        else:
            orig = resolve(it["origem"])
            if orig is None:
                continue
            entrada = orig
        r = modelo.predict(str(entrada), imgsz=416, conf=0.05, verbose=False)[0]
        caixas = []
        if r.boxes is not None and len(r.boxes):
            with Image.open(entrada) as im:
                L, A = im.size
            cam = camera(it["origem"])
            rr = roi.get(cam) or {'x': 0.0, 'y': 0.0, 'w': 1.0, 'h': 1.0}
            xy = r.boxes.xyxy.cpu().numpy()
            cl = r.boxes.cls.cpu().numpy().astype(int)
            for b, c in zip(xy, cl):
                x1, y1, x2, y2 = [float(v) for v in b]
                if modo == 'full':
                    # frac -> espaço da ROI (afim por eixo)
                    x1 = (x1 / L - rr['x']) / rr['w']
                    x2 = (x2 / L - rr['x']) / rr['w']
                    y1 = (y1 / A - rr['y']) / rr['h']
                    y2 = (y2 / A - rr['y']) / rr['h']
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                w, h = abs(x2 - x1), abs(y2 - y1)
                caixas.append((int(c), (cx, cy, w, h)))
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
    f1s = []
    for i in range(3):
        P = tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) else 0.0
        R = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) else 0.0
        f1s.append(round(2 * P * R / (P + R) if (P + R) else 0.0, 3))
    return {'f1_macro': round(sum(f1s) / 3, 3), 'por_classe': f1s,
            'tp': {str(k): int(v) for k, v in tp.items()}, 'fn': {str(k): int(v) for k, v in fn.items()}}


m = YOLO(str(PESO))
a = metricas(m, 'crop')
b = metricas(m, 'full')
print(f"  COM recorte de ROI : F1 macro {a['f1_macro']}  por classe {a['por_classe']}")
print(f"  COM quadro inteiro : F1 macro {b['f1_macro']}  por classe {b['por_classe']}")
print(f"  custo do descasamento: {round(a['f1_macro'] - b['f1_macro'], 3)} de F1 macro")
Path('/var/tmp/descasamento-roi.json').write_text(json.dumps(
    {'roi_recorte': a, 'quadro_inteiro': b,
     'custo_f1_macro': round(a['f1_macro'] - b['f1_macro'], 3),
     'obs': 'modelo treinado no recorte; teste mede o mesmo protocolo com a entrada do deploy'},
    ensure_ascii=False, indent=1))
print('gravado: /var/tmp/descasamento-roi.json')
