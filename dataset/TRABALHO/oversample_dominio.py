#!/usr/bin/env python3
"""Super-amostragem do NOSSO domínio no treino + listas por domínio para avaliação.

Por que: no v1 o treino é 98% externo (sdp 80%) e só 67 imagens são do rig. Assim o
mAP de val não fala nada sobre o rig. Aqui:
  - gera train-dominioxN.txt com as imagens do nosso domínio repetidas N vezes
    (ultralytics aceita lista .txt de caminhos de imagem como `train:`)
  - gera val-rig.txt / val-externo.txt / test-rig.txt / test-externo.txt para medir
    o modelo SEPARADO por domínio (é isso que decide promoção)
Não altera nada do dataset: só escreve listas novas + um data-oversampled.yaml.

Uso: python oversample_dominio.py --dataset DIR [--fator 5] [--ensaio]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

NOSSO = ('corpus', 'nosso')


def dominio(origem: str) -> str:
    return 'rig' if origem.startswith(NOSSO) else 'externo'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--fator', type=int, default=5)
    ap.add_argument('--ensaio', action='store_true')
    ap.add_argument('--permitir-vazio', action='store_true',
                    help='aceita lista de dominio vazio (dataset 100% proprio)')
    a = ap.parse_args()

    base = Path(a.dataset)
    man = base / 'manifest.json'
    if not man.is_file():
        print('sem manifest em', man)
        return 2
    itens = json.loads(man.read_text())['itens']

    listas: dict[str, list[str]] = {}
    contagem = Counter()
    for split in ('train', 'val', 'test'):
        rig = [i for i in itens if i['split'] == split and dominio(i['origem']) == 'rig']
        ext = [i for i in itens if i['split'] == split and dominio(i['origem']) == 'externo']
        contagem[(split, 'rig')] = len(rig)
        contagem[(split, 'externo')] = len(ext)
        if split == 'train':
            caminhos = []
            for i in rig:
                caminhos += [str(base / 'images' / split / i['arquivo'])] * a.fator
            caminhos += [str(base / 'images' / split / i['arquivo']) for i in ext]
            listas['train-dominiox%d.txt' % a.fator] = caminhos
        else:
            listas[f'{split}-rig.txt'] = [str(base / 'images' / split / i['arquivo']) for i in rig]
            listas[f'{split}-externo.txt'] = [str(base / 'images' / split / i['arquivo']) for i in ext]

    print(f'dataset: {base}')
    for (split, d), n in sorted(contagem.items()):
        print(f'  {split:5s} {d:7s} {n}')
    for nome, linhas in listas.items():
        print(f'  lista {nome}: {len(linhas)} linhas')
    if any(not l for l in listas.values()) and not a.permitir_vazio:
        print('ABORT: lista vazia (domínio sem imagem em algum split)')
        return 3
    if a.ensaio:
        print('(ensaio)')
        return 0

    for nome, linhas in listas.items():
        (base / nome).write_text('\n'.join(linhas) + '\n')
    yml = (base / 'data.yaml').read_text().splitlines()
    novo = []
    for linha in yml:
        if linha.startswith('train:'):
            novo.append('train: train-dominiox%d.txt' % a.fator)
            continue
        if linha.startswith('val:'):
            novo.append('val: images/val')
            continue
        if linha.startswith('test:'):
            novo.append('test: images/test')
            continue
        novo.append(linha)
    (base / 'data-oversampled.yaml').write_text('\n'.join(novo) + '\n')
    print('gravado:', base / 'data-oversampled.yaml')
    print((base / 'data-oversampled.yaml').read_text())
    return 0


if __name__ == '__main__':
    sys.exit(main())
