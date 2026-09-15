#!/usr/bin/env python3
"""Treina o detector v1 (lateral ou topo) e grava o model-meta.json no padrão do projeto.

Contrato:
  - entrada: dataset do v1 (monta_v1_detector.py), com split POR ITEM já embutido
  - aumento por treino lido de treino-v1-args.yaml (docs/reference/augmentacao-e-preprocessing-*)
  - saída: runs/v1-<vista>-yolov8n/weights/best.pt + model-meta.json com sha do peso,
    sha do manifest do dataset, métricas de validação e o aviso de que val não é teste
  - teste (images/test, por item) NÃO é usado no treino: serve para a avaliação final

Uso:
  python treina_v1.py --vista lateral [--epochs 2] [--sem-meta]
"""
from __future__ import annotations

import argparse
import os
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(os.environ.get('PNAAT_MODELOS') or (Path.home() / 'pnaat-modelos'))
ARGS_YAML = Path(__file__).resolve().parents[2] / 'dataset/TRABALHO/treino-v1-args.yaml'


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--vista', required=True, choices=['lateral', 'topo'])
    ap.add_argument('--epochs', type=int, default=None)
    ap.add_argument('--modelo', default='yolov8n.pt')
    ap.add_argument('--sem-meta', action='store_true')
    ap.add_argument('--roi', action='store_true', help='dataset/saida do build com ROI (-roi)')
    ap.add_argument('--tag', default='v1', help='prefixo da pasta de modelos (v1, v2, ...)')
    ap.add_argument('--imgsz', type=int, default=None, help='resolucao de entrada (sobrepoe o yaml)')
    ap.add_argument('--data', default=None, help='yaml de dados alternativo (ex.: dobra de k-fold)')
    ap.add_argument('--oversampled', action='store_true',
                    help='usa data-oversampled.yaml (nosso dominio repetido N vezes)')
    ap.add_argument('--nome', default=None, help='nome do run (default v1-<vista>-<modelo>)')
    a = ap.parse_args()

    base = RAIZ / (f'{a.tag}-{a.vista}-detector' + ('-roi' if a.roi else ''))
    dados = base / 'dataset'
    data_yaml = Path(a.data) if a.data else dados / ('data-oversampled.yaml' if a.oversampled else 'data.yaml')
    if not data_yaml.is_file():
        print('dataset do v1 ausente:', data_yaml)
        return 2

    try:
        import yaml
        kwargs = yaml.safe_load(ARGS_YAML.read_text()) or {}
    except Exception as exc:  # noqa: BLE001
        print('falha lendo args:', exc)
        return 2
    if a.epochs:
        kwargs['epochs'] = a.epochs
    if a.imgsz:
        kwargs['imgsz'] = a.imgsz

    from ultralytics import YOLO
    nome_run = a.nome or (f'{a.tag}-{a.vista}-{Path(a.modelo).stem}'
                          + ('-dominio' if a.oversampled else ''))
    modelo = YOLO(a.modelo)
    resultado = modelo.train(data=str(data_yaml), project=str(base / 'runs'),
                             name=nome_run, exist_ok=True, **kwargs)

    peso = base / 'runs' / nome_run / 'weights' / 'best.pt'
    meta = {a.tag: a.vista, 'tag': a.tag, 'modelo_base': a.modelo, 'classes': ['normal', 'tampa_ausente', 'defeito_tampa'],
            'dataset': str(dados), 'data_yaml': str(data_yaml), 'roi': bool(a.roi),
            'oversampled': bool(a.oversampled),
            'dataset_manifest_sha256': (sha256(dados / 'manifest.json')
                                        if (dados / 'manifest.json').is_file() else None),
            'peso': str(peso), 'peso_sha256': sha256(peso) if peso.is_file() else None,
            'peso_bytes': peso.stat().st_size if peso.is_file() else None,
            'args': kwargs,
            'args_yaml_sha256': sha256(ARGS_YAML),
            'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'git_head': subprocess.run(['git', '-C', str(Path(__file__).resolve().parents[2]), 'rev-parse', 'HEAD'],
                                       capture_output=True, text=True).stdout.strip(),
            'warning': ('val e split por item; teste (images/test) NAO foi usado — promover só com '
                        'canário de garrafa real no rig e gate OOD (evaluations/ood-mvtec-*)'),
            'metricas_val': {}}
    try:
        m = resultado.results_dict if hasattr(resultado, 'results_dict') else {}
        meta['metricas_val'] = {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in (m or {}).items()}
    except Exception:  # noqa: BLE001
        pass
    if not a.sem_meta:
        (base / 'model-meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print('model-meta gravado em', base / 'model-meta.json')
    print('peso:', meta['peso'], '| sha:', (meta['peso_sha256'] or '')[:16])
    print('metricas val:', meta['metricas_val'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
