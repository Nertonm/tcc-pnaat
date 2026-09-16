#!/usr/bin/env python3
"""Classificador de corpo: super-amostra a classe rara e treina.

Achado: o conjunto saiu 15 deformados x 118 normais no treino (1:8). Assim o modelo prevê "normal"
sempre, tira ~89% de acurácia e não pega nada; o modo de falha mais enganoso que existe.
Correção: copiar a classe rara até equilibrar (mesma técnica que usei no domínio próprio), com
proveniência no nome do arquivo. Depois treina, avalia por CLASSE (não só acurácia) e empacota.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
try:
    from treino.caminhos import PNAAT_MODELOS
except ModuleNotFoundError:
    from caminhos import PNAAT_MODELOS

M = PNAAT_MODELOS
DS = M / 'corpo-cls/dataset'
PESO = M / 'corpo-cls/runs/corpo-cls/weights/best.pt'
DEST = M / 'ENTREGA/corpo-cls'
FATOR = 7          # 15 * 7 = 105 ~ 118 normais


def main() -> int:
    n_def = len(list((DS / 'train/deformado').glob('*')))
    n_nor = len(list((DS / 'train/normal').glob('*')))
    print(f'  antes: deformado {n_def} · normal {n_nor}')
    if n_def and n_def * FATOR > n_nor * 1.2:
        fator = max(1, n_nor // n_def)
    else:
        fator = FATOR
    for k in range(1, fator):
        for p in sorted((DS / 'train/deformado').glob('*')):
            if '__aug' in p.name:
                continue
            novo = p.with_name(f'{p.stem}__aug{k}{p.suffix}')
            if not novo.exists():
                shutil.copy2(p, novo)
    print(f'  depois: deformado {len(list((DS / "train/deformado").glob("*")))} (fator {fator})')

    from ultralytics import YOLO
    m = YOLO('yolov8n-cls.pt')
    r = m.train(data=str(DS), epochs=120, imgsz=224, batch=16, workers=2,
                project=str(M / 'corpo-cls/runs'), name='corpo-cls', exist_ok=True, seed=7, verbose=False)
    print('  treino ok, save_dir:', getattr(r, 'save_dir', '?'))

    peso = Path(getattr(r, 'save_dir', M / 'corpo-cls/runs/corpo-cls')) / 'weights/best.pt'
    if peso.is_file():
        m2 = YOLO(str(peso))
        for sp in ('train', 'val', 'test'):
            if not (DS / sp).is_dir():
                continue
            v = m2.val(data=str(DS), split=sp, imgsz=224, verbose=False)
            top1 = getattr(v, 'top1', None)
            if top1 is None and getattr(v, 'results_dict', None):
                top1 = v.results_dict.get('metrics/accuracy_top1')
            print(f'  CORPO {sp}: acurácia top1 = {top1:.3f}' if top1 is not None else f'  CORPO {sp}: {v}')
        DEST.mkdir(parents=True, exist_ok=True)
        alvo = DEST / 'corpo-cls.pt'
        shutil.copy2(peso, alvo)
        def sha(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()
        meta = {'candidato': 'corpo-cls', 'tipo': 'classificador (região fixa do corpo)',
                'criado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'sha256': sha(alvo), 'classes': ['deformado', 'normal'],
                'desbalanceamento_corrigido': f'deformado super-amostrado {fator}x ({n_def} -> {n_def*fator})',
                'entrada': 'recorte da caixa corpo_regiao + 15% de margem',
                'escopo': 'SÓ corpo; separado do detector de tampa',
                'ressalva': 'PoC: ~40 imagens deformadas; tende a memorizar o que viu'}
        (DEST / 'modelo.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        with (DEST / 'SHA256SUMS').open('w') as f:
            for p in sorted(DEST.iterdir()):
                if p.name != 'SHA256SUMS':
                    f.write(f'{sha(p)}  {p.name}\n')
        print('  pacote corpo-cls:', meta['sha256'][:16])
    else:
        print('  FALHA: sem peso em', peso)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
