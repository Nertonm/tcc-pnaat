#!/usr/bin/env python3
"""Duas lacunas de método, fechadas agora:

A) LIMIAR ESCOLHIDO EM VALIDAÇÃO (não no teste). O relatório declara a regra "limiar se escolhe
   em validação" mas as tabelas do dia foram calculadas no TESTE — incoerência. Aqui: varre os
   limiares na VAL e reporta o que o TESTE dá com o limiar escolhido (o fluxo correto).
B) MÉTRICA POR CÂMERA (csi / usb / espcam), que estava agrupada como "rig" — a heterogeneidade
   entre as câmeras laterais era uma limitação declarada e não medida.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

# raiz do repo e pasta de modelos derivadas do proprio arquivo (sem caminho pessoal)
_G = Path(__file__).resolve().parents[2]
M = _G.parent.parent / 'pnaat-modelos'
DS = M / 'v7-3-lateral-detector-roi/dataset'
PESO = M / 'v7a-lateral-detector-roi/runs/v7a-rig/weights/best.pt'
CONFS = (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50)


def iou(a, b) -> float:
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


man = json.loads((DS / 'manifest.json').read_text())
cam_por_arquivo = {}
for i in man['itens']:
    o = i.get('origem', '')
    cam = next((c for c in ('csi', 'usb', 'espcam', 'rig') if c in o), 'outra')
    cam_por_arquivo[i['arquivo']] = cam

modelo = YOLO(str(PESO))
nomes = None


def avalia(split: str, conf: float):
    global nomes
    tp, fp, fn = Counter(), Counter(), Counter()
    por_cam = defaultdict(lambda: {'tp': Counter(), 'fp': Counter(), 'fn': Counter()})
    imgs = sorted((DS / 'images' / split).glob('*'))
    for img in imgs:
        lab = DS / 'labels' / split / (img.stem + '.txt')
        gt = []
        if lab.is_file():
            for l in lab.read_text().splitlines():
                p = l.split()
                if len(p) == 5:
                    cl, cx, cy, w, h = int(p[0]), *map(float, p[1:])
                    with Image.open(img) as im:
                        L, A = im.size
                    gt.append((cl, ((cx - w / 2) * L, (cy - h / 2) * A, (cx + w / 2) * L, (cy + h / 2) * A)))
        r = modelo.predict(str(img), imgsz=416, conf=conf, verbose=False)[0]
        nomes = r.names or nomes
        caixas = []
        if r.boxes is not None and len(r.boxes):
            xy = r.boxes.xyxy.cpu().numpy()
            cl = r.boxes.cls.cpu().numpy().astype(int)
            caixas = [(int(c), tuple(float(v) for v in b)) for b, c in zip(xy, cl)]
        cam = cam_por_arquivo.get(img.name, 'outra')
        usados = set()
        for cg, bg in gt:
            achou = False
            for k, (cp, bp) in enumerate(caixas):
                if k in usados or cp != cg:
                    continue
                if iou(bg, bp) >= 0.3:
                    usados.add(k); achou = True; break
            if achou:
                tp[cg] += 1; por_cam[cam]['tp'][cg] += 1
            else:
                fn[cg] += 1; por_cam[cam]['fn'][cg] += 1
        for k, (cp, _) in enumerate(caixas):
            if k not in usados:
                fp[cp] += 1; por_cam[cam]['fp'][cp] += 1
    return {'tp': tp, 'fp': fp, 'fn': fn, 'por_cam': por_cam, 'n': len(imgs)}


def f1_macro(res, nclasses=3):
    f1s = []
    for idx in range(nclasses):
        P = res['tp'][idx] / (res['tp'][idx] + res['fp'][idx]) if (res['tp'][idx] + res['fp'][idx]) else 0.0
        R = res['tp'][idx] / (res['tp'][idx] + res['fn'][idx]) if (res['tp'][idx] + res['fn'][idx]) else 0.0
        f1s.append(2 * P * R / (P + R) if (P + R) else 0.0)
    return sum(f1s) / len(f1s), f1s


print('=== A) ESCOLHA DE LIMIAR NA VALIDAÇÃO (protocolo correto) ===')
linhas = []
for conf in CONFS:
    v = avalia('val', conf)
    f1m, _ = f1_macro(v)
    linhas.append((conf, f1m))
    print(f'  val  conf {conf:.2f}: F1 macro {f1m:.3f}')
melhor = max(linhas, key=lambda x: x[1])
print(f'  -> limiar escolhido NA VAL: {melhor[0]:.2f} (F1 val {melhor[1]:.3f})')

t = avalia('test', melhor[0])
f1t, f1s = f1_macro(t)
print(f'  teste com esse limiar: F1 macro {f1t:.3f} ({t["n"]} imagens)')
print(f'     por classe: normal {f1s[0]:.3f} · tampa_ausente {f1s[1]:.3f} · defeito_tampa {f1s[2]:.3f}')

print('\n=== B) MÉTRICA POR CÂMERA (teste, limiar da val) ===')
saida_cam = {}
for cam, d in sorted(t['por_cam'].items()):
    res = {'tp': d['tp'], 'fp': d['fp'], 'fn': d['fn']}
    f1c, f1s_c = f1_macro(res)
    saida_cam[cam] = {'f1_macro': round(f1c, 3), 'por_classe': [round(x, 3) for x in f1s_c],
                      'gt': {nomes.get(i, str(i)): int(d['tp'][i] + d['fn'][i]) for i in range(3)}}
    print(f'  {cam:8s} F1 macro {f1c:.3f} | por classe {[round(x,3) for x in f1s_c]} | '
          f'instâncias {saida_cam[cam]["gt"]}')

Path('/var/tmp/lacunas-metodo.json').write_text(json.dumps(
    {'limiar_escolhido_na_val': melhor[0], 'f1_val': round(melhor[1], 4),
     'f1_teste_com_esse_limiar': round(f1t, 4), 'por_camera': saida_cam,
     'obs': 'tabelas anteriores eram no teste; esta segue o protocolo declarado'},
    ensure_ascii=False, indent=1))
print('\ngravado: /var/tmp/lacunas-metodo.json')
