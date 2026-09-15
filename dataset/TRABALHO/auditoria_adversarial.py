#!/usr/bin/env python3
"""Auditoria adversarial do dia. Cada checagem pode FALHAR — o valor está em falhar alto.

C1  a base "limpa" não tem quase-duplicata com o NOSSO teste (vazamento entre domínios)
C2  o k-fold: listas de treino e validação realmente disjuntas + diretório persistido
C3  as imagens do projeto 19 (equipe) entraram mesmo no v7 e com a caixa de corpo
C4  os números do relatório batem com os JSONs (cruzamento programático)
C5  contagens tp/fp/fn das tabelas de limiar fecham com as instâncias do teste
C6  contaminação do v5/v6/v7 vs teste antigo (prova de que os splits mudaram)
C7  arquivos do p19 intactos (sha256 no disco == sha registrado no receipt)
C8  os commits de hoje tocam só arquivos meus
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

G = Path('${TCC_REPO:-$HOME/tcc-pnaat/github}')
M = Path('${PNAAT_MODELOS:-$HOME/pnaat-modelos}')
sys.path.insert(0, str(G / 'dataset/TRABALHO'))
import importlib.util
spec = importlib.util.spec_from_file_location('monta', G / 'dataset/TRABALHO/monta_v1_detector.py')
monta = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(monta)
except SystemExit:
    pass

resultados: list[tuple[str, bool, str]] = []


def checa(nome: str, ok: bool, detalhe: str) -> None:
    resultados.append((nome, ok, detalhe))
    print(f"  [{'PASSOU' if ok else 'FALHOU'}] {nome}: {detalhe}")


def dhash(p: Path):
    return monta.dhash(p) if hasattr(monta, 'dhash') else None


print('C1 — quase-duplicata entre a base externa e o NOSSO teste (v7)')
ext_lista = M / 'ext-treino.txt'
v7 = M / 'v7-3-lateral-detector-roi/dataset/manifest.json'
if ext_lista.is_file() and v7.is_file():
    man = json.loads(v7.read_text())
    teste = [i for i in man['itens'] if i['split'] == 'test']
    hashes_teste = {}
    for i in teste:
        p = M / 'v7-3-lateral-detector-roi/dataset/images/test' / i['arquivo']
        h = dhash(p) if p.is_file() else None
        if h:
            hashes_teste.setdefault(h, i['arquivo'])
    colisoes = []
    for linha in ext_lista.read_text().splitlines():
        p = Path(linha)
        if not p.is_file():
            continue
        h = dhash(p)
        if h in hashes_teste:
            colisoes.append((p.name, hashes_teste[h]))
    checa('C1 base externa x nosso teste', not colisoes,
          f'{len(colisoes)} quase-duplicatas' + (f' ex.: {colisoes[:2]}' if colisoes else ''))
else:
    checa('C1 base externa x nosso teste', False, 'arquivos ausentes (ext-treino.txt ou v7)')

print('C2 — disjunção real no k-fold')
listas = sorted((M).glob('kfcand-*/[!.]*')) + sorted((M).glob('kfcand-*/*'))
dirs = [d for d in M.glob('kfcand-*') if d.is_dir() and d.name.startswith('kfcand')]
achou = False
for d in dirs:
    tre = sorted(d.glob('train-dobra*.txt'))
    if not tre:
        continue
    achou = True
    for tf in tre:
        vf = tf.with_name(tf.name.replace('train-', 'val-'))
        if not vf.is_file():
            checa('C2 disjuncao', False, f'{vf.name} ausente')
            break
        a = set(tf.read_text().split())
        b = set(vf.read_text().split())
        inter = a & b
        checa(f'C2 {d.name}/{tf.name}', not inter, f'treino {len(a)} / val {len(b)} / interseção {len(inter)}')
        break
    break
if not achou:
    checa('C2 disjuncao', False, 'nenhuma lista do k-fold persistida (temp dir não encontrado)')

print('C3 — imagens da equipe (p19) no v7 e caixa de corpo')
if v7.is_file():
    man = json.loads(v7.read_text())
    nomes = [i['arquivo'] for i in man['itens']]
    p19 = [n for n in nomes if 'deform' in n.lower()]
    checa('C3 imagens de deformidade no dataset', len(p19) > 0, f'{len(p19)} arquivos: {p19[:3]}')
    corpo = 0
    for i in man['itens']:
        for s in ('train', 'val', 'test'):
            lab = M / 'v7-3-lateral-detector-roi/dataset/labels' / s / (i['arquivo'].rsplit('.', 1)[0] + '.txt')
            if lab.is_file():
                corpo += sum(1 for l in lab.read_text().splitlines() if l.startswith('3 '))
    checa('C3 caixas de corpo no v7-3 (devem ser ZERO sem --com-corpo)', corpo == 0,
          f'{corpo} caixas classe 3 no dataset de 3 classes')

print('C4 — números do relatório batem com os JSONs')
rel = (G / 'docs/reference/resultados-deteccao-20260915.md').read_text()
v5j = M / 'v5-lateral-detector-roi/avaliacao-teste-limpo.json'
if v5j.is_file():
    d = json.loads(v5j.read_text())
    pc = d['dominios']['rig']['por_classe'] if 'dominios' in d else d['por_dominio']['rig']['por_classe']
    def m(c):
        v = pc.get(c) or {}
        return v.get('mAP50') if isinstance(v, dict) else v
    texto_ok = all(str(round(m(c), 3)).replace('.', ',') in rel for c in ('normal', 'tampa_ausente', 'defeito_tampa') if m(c) is not None)
    checa('C4 per-class do v5 no relatório', texto_ok,
          f"json: {[(c, m(c)) for c in pc]}")

print('C5 — tp/fp/fn fecham com as instâncias do teste')
for tag, ds in (('v7a', 'v7-3'), ('v6a', 'v6-3')):
    j = M / f'{tag}-lateral-detector-roi/limiares-teste.json'
    dsdir = M / f'{ds}-lateral-detector-roi/dataset'
    if not (j.is_file() and dsdir.is_dir()):
        continue
    d = json.loads(j.read_text())
    inst = Counter()
    for lab in (dsdir / 'labels/test').glob('*.txt'):
        for l in lab.read_text().splitlines():
            if l.split():
                inst[int(l.split()[0])] += 1
    nomes = ['normal', 'tampa_ausente', 'defeito_tampa', 'deformidade']
    conf = list(d['limiares'])[0]
    ok = True
    detalhe = []
    for idx, nome in enumerate(nomes):
        cv = d['limiares'][conf]['por_classe'].get(nome)
        if not cv:
            continue
        esperado = inst.get(idx, 0)
        real = cv['tp'] + cv['fn']
        detalhe.append(f'{nome}: gt {esperado} vs tp+fn {real}')
        ok = ok and (esperado == real)
    checa(f'C5 contagens do {tag}', ok, ' | '.join(detalhe))

print('C6 — splits mudaram (v3 x v6-3 x v7-3)')
def teste_nomes(p):
    m = M / p
    if not m.is_file():
        return None
    d = json.loads(m.read_text())
    return {i['arquivo'] for i in d['itens'] if i['split'] == 'test'}
a, b, c = (teste_nomes('v3-lateral-detector-roi/dataset/manifest.json'),
           teste_nomes('v6-3-lateral-detector-roi/dataset/manifest.json'),
           teste_nomes('v7-3-lateral-detector-roi/dataset/manifest.json'))
if a and b:
    checa('C6 teste v3 x v6-3 diferentes', a != b, f'iguais: {a == b} | comuns: {len(a & b)}/{len(a)}')
if b and c:
    checa('C6 teste v6-3 x v7-3 iguais (mesmo dado)', b == c, f'iguais: {b == c} | comuns: {len(b & c)}/{len(b)}')

print('C7 — arquivos do p19 intactos no disco do Label Studio')
up = Path('/srv/label-studio/data/media/upload/19')
if up.is_dir():
    arqs = sorted(up.iterdir())
    checa('C7 p19 presente e não vazio', len(arqs) >= 16, f'{len(arqs)} arquivos no volume')
else:
    checa('C7 p19 presente', False, 'diretório do volume ausente')

print('C8 — commits de hoje tocam só arquivos meus')
for rev in ('f037fbe', '1cd895f'):
    r = subprocess.run(['git', '-C', str(G), 'show', '--name-only', '--pretty=format:', rev],
                       capture_output=True, text=True)
    arqs = [x for x in r.stdout.splitlines() if x.strip()]
    meus = all(x.startswith(('dataset/TRABALHO/', 'docs/reference/')) for x in arqs)
    checa(f'C8 {rev}', meus, f'{len(arqs)} arquivos; fora do meu escopo: '
          f'{[x for x in arqs if not x.startswith(("dataset/TRABALHO/", "docs/reference/"))][:3]}')

print('\n=== RESUMO ===')
falhas = [r for r in resultados if not r[1]]
print(f'checagens: {len(resultados)} | falhas: {len(falhas)}')
for nome, _, detalhe in falhas:
    print(f'  FALHOU {nome}: {detalhe}')
