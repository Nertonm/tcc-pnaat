#!/usr/bin/env python3
"""Benchmark JUSTO + paridade: torch x onnx, ambos em CPU (a borda não tem a GPU do host).

Correção do erro anterior: o YOLO escolhe CUDA sozinho, então a medida do torch saiu na GPU
e a do ONNX na CPU — comparação inválida. Aqui o torch é forçado a CPU e ainda se mede a
AGREGAÇÃO de predições (mesmas 18 imagens, IoU>=0.5) para separar "exportou diferente" de
"medido diferente".
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '4')


def iou(a, b) -> float:
    xi1, yi1 = max(a[0], b[0]), max(a[1], b[1])
    xi2, yi2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def mede(modelo, img: Path, imgsz: int, n: int = 20) -> dict:
    ts = []
    for _ in range(n):
        t = time.time()
        modelo.predict(str(img), imgsz=imgsz, conf=0.15, device='cpu', verbose=False)
        ts.append((time.time() - t) * 1000)
    return {'mediana_ms': round(statistics.median(ts), 1), 'min_ms': round(min(ts), 1)}


def predicoes(modelo, imgs: list[Path], imgsz: int) -> dict:
    saida = {}
    for p in imgs:
        r = modelo.predict(str(p), imgsz=imgsz, conf=0.15, device='cpu', verbose=False)[0]
        caixas = []
        if r.boxes is not None and len(r.boxes):
            xy = r.boxes.xyxy.cpu().numpy()
            cl = r.boxes.cls.cpu().numpy().astype(int)
            cf = r.boxes.conf.cpu().numpy()
            caixas = sorted([(int(c), tuple(float(v) for v in b), float(f)) for b, c, f in zip(xy, cl, cf)],
                            key=lambda x: -x[2])
        saida[p.name] = caixas
    return saida


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--peso', required=True)
    ap.add_argument('--onnx', required=True)
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--saida', default='/var/tmp/otimizacao')
    a = ap.parse_args()

    from ultralytics import YOLO

    ds = Path(a.dataset)
    imgs = sorted(ds.glob('images/test/*'))[:1]
    todas = sorted(ds.glob('images/test/*'))
    rel = {'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'aviso': 'torch forçado a CPU (device=cpu); na GPU do host ele é ~7x mais rápido',
           'formatos': {}}

    print('torch (CPU): medindo...')
    m = YOLO(a.peso)
    rel['formatos']['torch_cpu'] = mede(m, imgs[0], a.imgsz)
    pt = predicoes(m, todas, a.imgsz)

    print('onnx (CPU): medindo...')
    mo = YOLO(a.onnx)
    rel['formatos']['onnx_cpu'] = mede(mo, imgs[0], a.imgsz)
    po = predicoes(mo, todas, a.imgsz)

    # paridade: mesmo numero de caixas por classe e casamento por IoU
    iguais = 0
    total = 0
    for nome, a_pt in pt.items():
        b_on = po.get(nome, [])
        usados = set()
        for cl, box, _ in a_pt:
            total += 1
            for i, (cl2, box2, _) in enumerate(b_on):
                if i in usados or cl2 != cl:
                    continue
                if iou(box, box2) >= 0.5:
                    usados.add(i)
                    iguais += 1
                    break
    rel['paridade'] = {'caixas_torch': total, 'caixas_casadas_no_onnx': iguais,
                       'taxa': round(iguais / total, 4) if total else None, 'iou_min': 0.5}

    (Path(a.saida) / 'benchmark-justo.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1))
    print('\n=== BENCHMARK EM CPU (comparável) ===')
    for nome, d in rel['formatos'].items():
        print(f"  {nome:12s} mediana {d['mediana_ms']:7.1f} ms  (min {d['min_ms']:.1f})")
    print(f"  paridade de caixas torch x onnx (IoU>=0,5): {iguais}/{total} = {rel['paridade']['taxa']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
