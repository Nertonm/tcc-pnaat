#!/usr/bin/env python3
"""Monta o dataset do detector de CORPO (uma classe: corpo_deformidade).

Diferenças em relação ao detector de tampa (de propósito):
  - uma classe só: `corpo_deformidade` (não compete com tampa, foi o que derrubou o modelo de 4)
  - NEGATIVOS explícitos: imagens com `corpo_regiao` e SEM deformidade entram com rótulo vazio
    ("corpo normal aqui"); sem isso o modelo aprende que todo corpo é defeito
  - rótulos SÃO transformados para o espaço do recorte (a correção feita no montador hoje)
  - split por item, mesma regra

Uso: monta_corpo_detector.py [--dry-run]
"""
from __future__ import annotations
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

G = _RAIZ_REPO
M = PNAAT_MODELOS
DS = G / 'dataset'
RAIZES = (DS, G, Path('/srv/label-studio/corpus'), Path('/srv/label-studio'))
CSV = DS / 'TRABALHO' / 'anotacoes-ls.csv'
ROI_JSON = CONTRATO / 'roi-por-camera.json'
OUT = M / 'corpo-detector-roi/dataset'
CLASSES = ['corpo_deformidade']
PROPORCAO = {'train': 0.70, 'val': 0.15, 'test': 0.15}
SEED = 7


def resolve(rel: str):
    for r in RAIZES:
        c = r / rel
        if c.is_file():
            return c
    return None


def camera(rel: str) -> str:
    for c in ('csi', 'usb', 'espcam'):
        if c in rel:
            return c
    return 'rig'


def split_de(item: str) -> str:
    h = int(hashlib.sha256(f'{SEED}:{item}'.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return 'train' if h < PROPORCAO['train'] else ('val' if h < PROPORCAO['train'] + PROPORCAO['val'] else 'test')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    roi = {c: v['roi_normalizada'] for c, v in json.loads(ROI_JSON.read_text())['cameras'].items()
           if v.get('roi_normalizada')}

    itens: dict[str, dict] = {}
    with open(CSV, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['valido'] != 'sim' or r['vista'] != 'lateral':
                continue
            caixas = json.loads(r['caixas'] or '[]')
            rot = {b.get('rotulo') for b in caixas}
            if not (rot & {'corpo_deformidade', 'corpo_regiao'}):
                continue
            rel = r['imagem']
            d = itens.setdefault(rel, {'rel': rel, 'pos': [], 'tem_reg': False, 'tem_def': False,
                                       'item': f"img:{rel}"})
            for b in caixas:
                if b.get('rotulo') == 'corpo_regiao':
                    d['tem_reg'] = True
                if b.get('rotulo') == 'corpo_deformidade':
                    d['tem_def'] = True
                    d['pos'].append((float(b['x']) / 100, float(b['y']) / 100,
                                     float(b['width']) / 100, float(b['height']) / 100))

    pos = [d for d in itens.values() if d['tem_def']]
    neg = [d for d in itens.values() if d['tem_reg'] and not d['tem_def']]
    print(f'itens laterais com corpo: {len(itens)} | com defeito: {len(pos)} | negativos (corpo ok): {len(neg)}')
    if len(pos) < 5:
        print('ABORT: defeitos de corpo insuficientes')
        return 2
    if a.dry_run:
        print('(dry-run) nada foi escrito')
        return 0

    for sub in ('images/train', 'images/val', 'images/test', 'labels/train', 'labels/val', 'labels/test'):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    manifesto = []
    for d in itens.values():
        src = resolve(d['rel'])
        if src is None:
            continue
        sp = split_de(d['item'])
        sufixo = hashlib.sha1(d['rel'].encode()).hexdigest()[:8]
        nome = f'corpo__{sufixo}__{src.name}'
        cam = camera(d['rel'])
        caixa = roi.get(cam)
        if caixa:
            from PIL import Image
            with Image.open(src) as im:
                L, A = im.size
                box = (int(caixa['x'] * L), int(caixa['y'] * A),
                       int((caixa['x'] + caixa['w']) * L), int((caixa['y'] + caixa['h']) * A))
                im.crop(box).save(OUT / 'images' / sp / nome, format='JPEG', quality=95, subsampling=0)
        else:
            shutil.copy2(src, OUT / 'images' / sp / nome)
        linhas = []
        for x, y, w, h in d['pos']:            # transforma para o espaço do recorte
            if caixa:
                cx = (x + w / 2 - caixa['x']) / caixa['w']
                cy = (y + h / 2 - caixa['y']) / caixa['h']
                w2, h2 = w / caixa['w'], h / caixa['h']
            else:
                cx, cy, w2, h2 = x + w / 2, y + h / 2, w, h
            linhas.append(f'0 {min(max(cx,0),1):.6f} {min(max(cy,0),1):.6f} '
                          f'{min(max(w2,0),1):.6f} {min(max(h2,0),1):.6f}')
        (OUT / 'labels' / sp / (Path(nome).stem + '.txt')).write_text(
            ('\n'.join(linhas) + '\n') if linhas else '')   # vazio = negativo explícito
        manifesto.append({'arquivo': nome, 'item': d['item'], 'split': sp,
                          'classe': 'corpo_deformidade' if d['tem_def'] else 'corpo_normal',
                          'origem': d['rel'], 'sha256': hashlib.sha256(src.read_bytes()).hexdigest()})

    resumo_img = Counter(m['split'] for m in manifesto)
    resumo_cls = Counter(f"{m['split']}/{m['classe']}" for m in manifesto)
    (OUT / 'data.yaml').write_text(
        f'path: {OUT}\ntrain: images/train\nval: images/val\ntest: images/test\n'
        f'nc: 1\nnames: {CLASSES}\n')
    (OUT / 'manifest.json').write_text(json.dumps(
        {'classes': CLASSES, 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
         'proporcao': PROPORCAO, 'imagens_por_split': dict(resumo_img),
         'por_split_classe': dict(resumo_cls), 'itens': manifesto}, ensure_ascii=False, indent=1))
    print('saída:', OUT)
    print('imagens por split:', dict(resumo_img))
    print('por split/classe:', dict(resumo_cls))
    return 0


if __name__ == '__main__':
    sys.exit(main())
