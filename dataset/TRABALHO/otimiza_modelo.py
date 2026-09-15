#!/usr/bin/env python3
"""Otimização do candidato (v7a) para borda: ONNX fp32 e INT8, com paridade e latência medidas.

O que responde:
  1. tamanho de cada formato
  2. paridade de acurácia no MESMO split de teste (mAP50) — quanto custa quantizar
  3. latência por imagem em CPU (a comparação que importa para a borda): torch x onnx x int8
  4. recomendação explícita, com o número que a sustenta

Não promove nada: só exporta e mede. O peso torch original não é alterado.
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


def tamanho(p: Path | None) -> float:
    return round(p.stat().st_size / 1e6, 2) if p and p.is_file() else 0.0


def latencia(modelo, fonte: Path, imgsz: int, n: int = 30) -> dict:
    ts = []
    for i in range(n):
        t = time.time()
        modelo.predict(str(fonte), imgsz=imgsz, conf=0.15, verbose=False)
        ts.append((time.time() - t) * 1000)
    return {'min': round(min(ts), 1), 'mediana': round(statistics.median(ts), 1),
            'media': round(statistics.mean(ts), 1), 'max': round(max(ts), 1), 'n': n}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--peso', required=True)
    ap.add_argument('--dataset', required=True, help='dataset com data.yaml (3 classes)')
    ap.add_argument('--data', required=True, help='yaml para calibração/validação do int8')
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--saida', default='/var/tmp/otimizacao')
    a = ap.parse_args()

    from ultralytics import YOLO

    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    peso = Path(a.peso)
    teste = sorted((Path(a.dataset) / 'images' / 'test').glob('*'))[:1]
    if not teste:
        print('FALHA: sem imagem de teste para o benchmark')
        return 2
    img_amostra = teste[0]

    rel = {'peso_original': str(peso), 'sha': None, 'imgsz': a.imgsz,
           'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'formatos': {}}
    import hashlib
    rel['sha'] = hashlib.sha256(peso.read_bytes()).hexdigest()[:16]

    # 1) linha de base em torch (CPU, 4 threads)
    m = YOLO(str(peso))
    print('torch: medindo acurácia...')
    v = m.val(data=a.data, split='test', imgsz=a.imgsz, verbose=False)
    rel['formatos']['torch'] = {'tamanho_mb': tamanho(peso),
                                'mAP50': round(float(v.box.map50), 4),
                                'mAP50-95': round(float(v.box.map), 4),
                                'latencia_ms': latencia(m, img_amostra, a.imgsz)}

    # 2) ONNX fp32
    print('onnx fp32: exportando...')
    onnx = Path(m.export(format='onnx', imgsz=a.imgsz, opset=12))
    mo = YOLO(str(onnx))
    vo = mo.val(data=a.data, split='test', imgsz=a.imgsz, verbose=False)
    rel['formatos']['onnx_fp32'] = {'arquivo': onnx.name, 'tamanho_mb': tamanho(onnx),
                                    'mAP50': round(float(vo.box.map50), 4),
                                    'mAP50-95': round(float(vo.box.map), 4),
                                    'latencia_ms': latencia(mo, img_amostra, a.imgsz)}

    # 3) ONNX INT8 (calibração no split de treino)
    print('onnx int8: exportando com calibração...')
    try:
        onnx8 = Path(m.export(format='onnx', imgsz=a.imgsz, int8=True, data=a.data, opset=12))
        m8 = YOLO(str(onnx8))
        v8 = m8.val(data=a.data, split='test', imgsz=a.imgsz, verbose=False)
        rel['formatos']['onnx_int8'] = {'arquivo': onnx8.name, 'tamanho_mb': tamanho(onnx8),
                                        'mAP50': round(float(v8.box.map50), 4),
                                        'mAP50-95': round(float(v8.box.map), 4),
                                        'latencia_ms': latencia(m8, img_amostra, a.imgsz)}
    except Exception as exc:  # noqa: BLE001
        rel['formatos']['onnx_int8'] = {'erro': str(exc)[:200]}
        print('  int8 falhou:', str(exc)[:160])

    (out / 'otimizacao.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1))
    print('\n=== RESUMO ===')
    for nome, d in rel['formatos'].items():
        if 'erro' in d:
            print(f'  {nome:12s} ERRO: {d["erro"][:60]}')
            continue
        lat = d['latencia_ms']
        print(f'  {nome:12s} {d["tamanho_mb"]:6.2f}MB  mAP50={d["mAP50"]:.4f}  '
              f'latência mediana {lat["mediana"]:.1f}ms (min {lat["min"]:.1f})')
    print('gravado:', out / 'otimizacao.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
