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
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from caminhos import RAIZ_REPO, CONTRATO, PNAAT_MODELOS
from validacao_dataset import validar_dataset, congelar_yaml

RAIZ = PNAAT_MODELOS
ARGS_YAML = CONTRATO / 'treino-v1-args.yaml'


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
    if not isinstance(kwargs, dict) or any(k in kwargs for k in ('data', 'project', 'name', 'exist_ok', 'resume')):
        print('ABORTADO args reservados/inseguros')
        return 2
    if a.epochs:
        kwargs['epochs'] = a.epochs
    if a.imgsz:
        kwargs['imgsz'] = a.imgsz

    try:
        evidencia = validar_dataset(data_yaml)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('ABORTADO gate dataset:', exc)
        return 3
    # O gate é independente do builder e obrigatório mesmo com --data/--sem-meta.
    nome_run = a.nome or (f'{a.tag}-{a.vista}-{Path(a.modelo).stem}'
                          + ('-dominio' if a.oversampled else ''))
    if nome_run in ('', '.', '..') or a.tag in ('', '.', '..') or Path(nome_run).name != nome_run or Path(a.tag).name != a.tag:
        print('ABORTADO tag/nome devem ser componentes simples')
        return 2
    run = base / 'runs' / nome_run
    try:
        run.mkdir(parents=True, exist_ok=False)  # reserva atômica; nunca reutiliza run
    except FileExistsError:
        print('ABORTADO run ja existe:', run)
        return 4
    efetivo = congelar_yaml(evidencia, run)
    (run / 'dataset-evidence.json').write_text(json.dumps(evidencia, ensure_ascii=False, indent=1))
    from ultralytics import YOLO
    try:
        modelo = YOLO(a.modelo)
        modelo.train(data=str(efetivo), project=str(base / 'runs'),
                     name=nome_run, exist_ok=True, **kwargs)
        peso = run / 'weights' / 'best.pt'
        if not peso.is_file() or peso.stat().st_size == 0:
            print('ABORTADO best.pt ausente/vazio:', peso)
            return 5
        # Não usar última linha de results.csv: mede o checkpoint que será entregue.
        val_args = {k: kwargs[k] for k in ('imgsz', 'batch', 'device', 'workers') if k in kwargs}
        resultado = YOLO(str(peso)).val(data=str(efetivo), split='val',
                                       project=str(run), name='val-best', **val_args)
        metricas = {k: float(v) for k, v in resultado.results_dict.items()}
        import math
        if not metricas or not all(math.isfinite(v) for v in metricas.values()):
            raise ValueError('metricas best/val ausentes ou nao finitas')
    except Exception as exc:
        print('ABORTADO treino/validacao:', exc)
        return 5
    meta = {**evidencia, 'vista': a.vista, 'tag': a.tag, 'modelo_base': a.modelo,
            'modelo_base_sha256': sha256(Path(a.modelo)) if Path(a.modelo).is_file() else None,
            'base_inicial_auditada': False,
            'data_yaml_efetivo': str(efetivo), 'data_yaml_efetivo_sha256': sha256(efetivo),
            'roi_solicitada': bool(a.roi), 'oversampled': bool(a.oversampled),
            'peso': str(peso), 'peso_sha256': sha256(peso), 'peso_bytes': peso.stat().st_size,
            'args': kwargs, 'args_yaml_sha256': sha256(ARGS_YAML),
            'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'git_head': subprocess.run(['git', '-C', str(RAIZ_REPO), 'rev-parse', 'HEAD'],
                                       capture_output=True, text=True).stdout.strip(),
            'warning': 'gate do dataset nao prova pureza da base inicial nem identidade fisica ausente do manifest',
            'avaliacao': 'best.pt/val', 'metricas_val': metricas}
    texto = json.dumps(meta, ensure_ascii=False, indent=1, allow_nan=False)
    (run / 'training-evidence.json').write_text(texto)
    if not a.sem_meta:
        (run / 'model-meta.json').write_text(texto)
    print('evidencia:', run / 'training-evidence.json')
    print('peso:', meta['peso'], '| sha:', meta['peso_sha256'][:16])
    print('metricas val:', meta['metricas_val'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
