#!/usr/bin/env python3
"""Avalia o modelo SEPARADO por domínio (rig vs externo) no split de teste.

Motivo: no v1 o mAP de val é 98% dado externo. Promover modelo por esse número é
promover por métrica de outro domínio. Aqui cada domínio tem seu próprio número,
usando as listas geradas por oversample_dominio.py.

Uso: python avalia_por_dominio.py --dataset DIR --peso best.pt [--split test]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--peso', required=True)
    ap.add_argument('--split', default='test', choices=['val', 'test'])
    ap.add_argument('--imgsz', type=int, default=320)
    ap.add_argument('--saida', default=None)
    a = ap.parse_args()

    base = Path(a.dataset)
    peso = Path(a.peso)
    if not peso.is_file():
        print('peso ausente:', peso)
        return 2
    from ultralytics import YOLO
    modelo = YOLO(str(peso))

    resultado = {'peso': str(peso), 'dataset': str(base), 'split': a.split,
                 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'dominios': {}}
    for dominio in ('rig', 'externo'):
        lista = base / f'{a.split}-{dominio}.txt'
        if not lista.is_file():
            print('lista ausente:', lista, '(rode oversample_dominio.py)')
            continue
        if not [l for l in lista.read_text().splitlines() if l.strip()]:
            print(f'lista vazia para o dominio {dominio}; pulando (dataset sem esse dominio)')
            continue
        yaml_provisorio = base / f'_aval-{a.split}-{dominio}.yaml'
        imagens = [l for l in lista.read_text().splitlines() if l.strip()]
        yaml_provisorio.write_text(
            f'path: {base}\ntrain: {lista.name}\nval: {lista.name}\n'
            f'nc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n')
        try:
            m = modelo.val(data=str(yaml_provisorio), imgsz=a.imgsz, verbose=False, split='val')
            d = dict(m.results_dict)
            classes = {}
            if getattr(m, 'box', None) is not None and getattr(m.box, 'ap_class_index', None) is not None:
                for idx, c in enumerate(m.box.ap_class_index):
                    nome = m.names.get(int(c), str(c))
                    classes[nome] = {'mAP50': round(float(m.box.ap50[idx]), 4),
                                     'mAP50-95': round(float(m.box.ap[idx]), 4)}
            resultado['dominios'][dominio] = {
                'imagens': len(imagens),
                'metricas': {k: (round(float(v), 4) if isinstance(v, (int, float)) else v)
                             for k, v in d.items()},
                'por_classe': classes}
            print(f'{dominio:8s} imagens={len(imagens):4d} ' +
                  ' '.join(f'{k.split("/")[-1]}={round(float(v), 4)}' for k, v in d.items()))
        finally:
            yaml_provisorio.unlink(missing_ok=True)

    destino = Path(a.saida) if a.saida else base / f'avaliacao-por-dominio-{a.split}.json'
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=1))
    print('gravado:', destino)
    return 0


if __name__ == '__main__':
    sys.exit(main())
