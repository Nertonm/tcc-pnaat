#!/usr/bin/env python3
"""Impressão digital do estado do Label Studio; para detectar material novo.

Serve de trava: antes de montar dataset, comparar o estado ATUAL do LS com o estado
no momento do export canônico. Se algo avançou (anotação submetida, rascunho novo,
upload novo), a montagem para; foi essa checagem que faltou e fez o v1 ser montado
com retrato velho, deixando de fora 16 imagens novas e 8 rascunhos da equipe.

Somente leitura (abre o sqlite em mode=ro).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
import os as _os
from pathlib import Path as _Path
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO

DB_PADRAO = '/srv/label-studio/data/label_studio.sqlite3'
RECIBOS = _RAIZ_REPO / 'dataset/TRABALHO/_exportacoes'


def fingerprint(db: str = DB_PADRAO) -> dict:
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)

    def um(sql, *args):
        r = con.execute(sql, args).fetchone()
        return r[0] if r else None

    return {
        'tarefas': um('select count(*) from task'),
        'anotacoes': um('select count(*) from task_completion'),
        'anotacoes_max_updated': um('select max(updated_at) from task_completion'),
        'drafts': um('select count(*) from tasks_annotationdraft'),
        'drafts_max_updated': um('select max(updated_at) from tasks_annotationdraft'),
        'uploads': um('select count(*) from data_import_fileupload'),
    }


def difere(atual: dict, referencia: dict) -> dict:
    """Campos onde o estado atual avançou (drafts/anotações/uploads/tarefas)."""
    campos = [c for c in atual if c in referencia]
    return {c: {'agora': atual[c], 'no_export': referencia[c]}
            for c in campos if atual[c] != referencia[c]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=DB_PADRAO)
    ap.add_argument('--recibo', default=None, help='recibo de export a comparar (default: o mais novo)')
    ap.add_argument('--simular', default=None, help='JSON com fingerprint falso (teste do caminho de aborto)')
    a = ap.parse_args()

    atual = fingerprint(a.db)
    if a.simular:
        referencia = json.loads(a.simular)
        origem = 'simulado'
    else:
        recibos = sorted(RECIBOS.glob('recibo-*.json')) if RECIBOS.is_dir() else []
        alvo = Path(a.recibo) if a.recibo else (recibos[-1] if recibos else None)
        if alvo is None or not Path(alvo).is_file():
            print('SEM RECIBO de export: rode antes o exportador canônico')
            print(json.dumps(atual, ensure_ascii=False, indent=1, default=str))
            return 3
        ref = json.loads(Path(alvo).read_text())
        referencia = ref.get('fingerprint_ls')
        origem = Path(alvo).name
        if not referencia:
            print(f'recibo {origem} não tem fingerprint (export anterior à trava); tratado como desatualizado')
            print(json.dumps(atual, ensure_ascii=False, indent=1, default=str))
            return 3

    d = difere(atual, referencia)
    print(f'fingerprint atual:      {json.dumps(atual, ensure_ascii=False, default=str)}')
    print(f'fingerprint referência: {json.dumps(referencia, ensure_ascii=False, default=str)} ({origem})')
    if d:
        print('\nLS AVANÇOU DESDE O EXPORT; montagem deve parar:')
        for campo, v in d.items():
            print(f'  {campo}: {v["no_export"]} -> {v["agora"]}')
        return 3
    print('\nestado igual ao export: pode montar dataset')
    return 0


if __name__ == '__main__':
    sys.exit(main())
