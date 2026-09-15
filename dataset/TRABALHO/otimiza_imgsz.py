#!/usr/bin/env python3
"""Otimização que importa na borda: resolução de entrada (imgsz) — acurácia x latência em CPU.

O export ONNX não compensou (mais lento na CPU e 0,15 de mAP50 abaixo). O que sobra de real
é reduzir o custo por quadro: menos pixels de entrada. Mede 320, 416 e 480 no MESMO teste,
em torch, com a latência em CPU — e devolve a configuração recomendada com o número.
"""
from __future__ import annotations

import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '4')

# raiz do repo e pasta de modelos derivadas do proprio arquivo (sem caminho pessoal)
G = Path(__file__).resolve().parents[2]
M = G.parent.parent / 'pnaat-modelos'
PESO = M / 'v7a-lateral-detector-roi/runs/v7a-rig/weights/best.pt'
DS = M / 'v7-3-lateral-detector-roi/dataset'
YAML = DS / 'data-3.yaml'

from ultralytics import YOLO  # noqa: E402

amostra = sorted(DS.glob('images/test/*'))[0]
rel = {'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'peso': str(PESO), 'por_imgsz': {}}

for imgsz in (320, 416, 480):
    m = YOLO(str(PESO))
    v = m.val(data=str(YAML), split='test', imgsz=imgsz, verbose=False, plots=False)
    ts = []
    for _ in range(20):
        t = time.time()
        m.predict(str(amostra), imgsz=imgsz, conf=0.15, device='cpu', verbose=False)
        ts.append((time.time() - t) * 1000)
    lat = statistics.median(ts)
    rel['por_imgsz'][str(imgsz)] = {'mAP50': round(float(v.box.map50), 4),
                                    'mAP50-95': round(float(v.box.map), 4),
                                    'latencia_cpu_ms': round(lat, 1)}
    print(f"  imgsz {imgsz}: mAP50={v.box.map50:.4f} mAP50-95={v.box.map:.4f} "
          f"latência CPU {lat:.1f} ms")

base = rel['por_imgsz']['480']
melhor = None
for k, d in rel['por_imgsz'].items():
    ganho = 1 - d['latencia_cpu_ms'] / base['latencia_cpu_ms']
    perda = base['mAP50'] - d['mAP50']
    d['ganho_latencia_vs_480'] = round(ganho, 3)
    d['perda_mAP50_vs_480'] = round(perda, 4)
    print(f"  {k}: {ganho*100:+.0f}% de latência, {-perda:+.4f} de mAP50")
    if perda <= 0.03 and (melhor is None or ganho > melhor[1]):
        melhor = (k, ganho)

rel['recomendacao'] = {'imgsz': melhor[0], 'ganho_latencia': round(melhor[1], 3)} if melhor else \
                      {'imgsz': '480', 'motivo': 'nenhuma redução manteve a acurácia dentro de 0,03'}
Path('/var/tmp/otimizacao-imgsz.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1))
print('\nrecomendação:', rel['recomendacao'])
print('gravado: /var/tmp/otimizacao-imgsz.json')
