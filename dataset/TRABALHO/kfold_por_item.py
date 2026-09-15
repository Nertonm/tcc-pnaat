#!/usr/bin/env python3
"""Validação cruzada POR ITEM — versão corrigida (v2).

Defeitos da v1 (achados em auditoria, 2026-09-15):
  - o MESMO arquivo de lista era usado em train e val  -> treinava na validação (inválido)
  - arquivos em /tmp/kfold-{d}.* sem unicidade por execução -> colisão entre runs simultâneos
  - sem verificação de disjunção treino x validação

Correção: diretório único por execução (mkdtemp), listas separadas, asserção de disjunção,
e o resultado grava o caminho das listas para auditoria posterior.

Uso: python kfold_por_item.py --dataset DIR --k 5 [--modelo PESO] [--vista lateral]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

MODELOS = os.environ.get('PNAAT_MODELOS') or str(Path.home() / 'pnaat-modelos')
G = Path(__file__).resolve().parents[2]
PY = G / '.venv/bin/python'
TREINA = G / 'dataset/TRABALHO/treina_v1.py'


def valida_disjuncao(treino: list[str], val: list[str], dobra: int) -> None:
    """Falha alto: nenhuma imagem pode estar nos dois lados."""
    t, v = set(treino), set(val)
    inter = t & v
    if inter:
        raise SystemExit(f'ABORTADO dobra {dobra}: {len(inter)} imagens em treino E validação '
                         f'(ex.: {sorted(inter)[:3]})')
    if not v:
        raise SystemExit(f'ABORTADO dobra {dobra}: validação vazia')
    if not t:
        raise SystemExit(f'ABORTADO dobra {dobra}: treino vazio')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--epochs', type=int, default=150)
    ap.add_argument('--tag', default='kfold')
    ap.add_argument('--vista', default='lateral', choices=['lateral', 'topo'])
    ap.add_argument('--modelo', default='yolov8n.pt')
    ap.add_argument('--ensaio', action='store_true')
    a = ap.parse_args()

    base = Path(a.dataset)
    man = json.loads((base / 'manifest.json').read_text())['itens']
    por_item: dict[str, list[dict]] = defaultdict(list)
    for i in man:
        if i['origem'].startswith(('corpus', 'nosso')):
            por_item[i['item']].append(i)
    itens = sorted(por_item)
    print(f'itens do domínio próprio: {len(itens)} | imagens: {sum(len(v) for v in por_item.values())}')
    if len(itens) < a.k:
        print('itens insuficientes para k dobras')
        return 2

    dobras: dict[int, list[str]] = defaultdict(list)
    for item in itens:
        idx = int(hashlib.sha256(item.encode()).hexdigest()[:8], 16) % a.k
        dobras[idx].append(item)

    run_dir = Path(tempfile.mkdtemp(prefix=f'kfold-{a.tag}-'))
    print(f'diretório das listas: {run_dir}')
    resultado = {'dataset': str(base), 'k': a.k, 'imgsz': a.imgsz, 'epochs': a.epochs,
                 'modelo_inicial': a.modelo, 'listas': str(run_dir),
                 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'dobras': []}

    for d in sorted(dobras):
        validacao = set(dobras[d])
        treino = [i for i in itens if i not in validacao]
        linhas_t = [str(base / 'images' / it['split'] / it['arquivo'])
                    for i in treino for it in por_item[i]]
        linhas_v = [str(base / 'images' / it['split'] / it['arquivo'])
                    for i in sorted(validacao) for it in por_item[i]]
        valida_disjuncao(linhas_t, linhas_v, d)

        txt_t = run_dir / f'train-dobra{d}.txt'
        txt_v = run_dir / f'val-dobra{d}.txt'
        txt_t.write_text('\n'.join(sorted(linhas_t)) + '\n')
        txt_v.write_text('\n'.join(sorted(linhas_v)) + '\n')
        yaml_fold = run_dir / f'dobra{d}.yaml'
        yaml_fold.write_text(f'path: {base}\ntrain: {txt_t}\nval: {txt_v}\n'
                             f'nc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n')

        classes_val = Counter(it['classe'] for i in validacao for it in por_item[i])
        print(f'\n--- dobra {d}: itens treino {len(treino)} / validação {len(validacao)} | '
              f'imgs treino {len(linhas_t)} / val {len(linhas_v)} | classes val {dict(classes_val)}')
        if a.ensaio:
            continue

        cmd = [str(PY), str(TREINA), '--vista', a.vista, '--tag', a.tag, '--roi',
               '--epochs', str(a.epochs), '--imgsz', str(a.imgsz), '--modelo', a.modelo,
               '--data', str(yaml_fold), '--sem-meta', '--nome', f'kfold-{d}']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print('  treino falhou:', r.stdout[-300:], r.stderr[-300:])
            continue
        csv = Path(MODELOS) / f'{a.tag}-{a.vista}-detector-roi/runs/kfold-{d}/results.csv'
        if not csv.is_file():
            print('  sem results.csv')
            continue
        linhas_csv = csv.read_text().splitlines()
        m = dict(zip(linhas_csv[0].split(','), linhas_csv[-1].split(',')))
        resultado['dobras'].append({
            'dobra': d, 'itens_treino': len(treino), 'itens_validacao': len(validacao),
            'imgs_treino': len(linhas_t), 'imgs_validacao': len(linhas_v),
            'classes_validacao': dict(classes_val),
            'precision': round(float(m['metrics/precision(B)']), 4),
            'recall': round(float(m['metrics/recall(B)']), 4),
            'mAP50': round(float(m['metrics/mAP50(B)']), 4),
            'mAP50-95': round(float(m['metrics/mAP50-95(B)']), 4)})
        print('   ', resultado['dobras'][-1])

    if not a.ensaio and resultado['dobras']:
        for metrica in ('precision', 'recall', 'mAP50', 'mAP50-95'):
            vals = [d[metrica] for d in resultado['dobras']]
            resultado[f'{metrica}_media'] = round(statistics.mean(vals), 4)
            resultado[f'{metrica}_desvio'] = round(statistics.pstdev(vals), 4)
            resultado[f'{metrica}_min'] = round(min(vals), 4)
            resultado[f'{metrica}_max'] = round(max(vals), 4)
        print('\n=== RESUMO k-fold por ITEM (média ± desvio | min–max) ===')
        for metrica in ('precision', 'recall', 'mAP50', 'mAP50-95'):
            print(f'  {metrica:10s} {resultado[f"{metrica}_media"]:.4f} ± {resultado[f"{metrica}_desvio"]:.4f}'
                  f'  [{resultado[f"{metrica}_min"]:.4f}–{resultado[f"{metrica}_max"]:.4f}]')
        saida = base.parent / (f'kfold-{a.k}x-item-{a.vista}-imgsz{a.imgsz}-'
                               f'{Path(a.modelo).stem}-v2corrigido.json')
        saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=1))
        print('gravado:', saida)
    return 0


if __name__ == '__main__':
    sys.exit(main())
