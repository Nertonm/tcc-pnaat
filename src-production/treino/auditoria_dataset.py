#!/usr/bin/env python3
"""Auditoria adversarial do DATASET montado: cada checagem pode FALHAR, e o valor esta em falhar alto.

Por que existe: os numeros de deteccao so valem se o split for honesto. O montador ja impoe o split por
item, mas quem consome o dataset (treino, k-fold, avaliacao) confia no artefato do montador. Esta
ferramenta audita o ARTEFATO -- o que esta no disco -- e nao a intencao do montador.

Checagens (todas sobre o que existe, sem reamostrar nada):

  A. integridade     todo arquivo do manifesto existe, e o sha256 confere
  B. split por item  nenhum item aparece em dois splits
  C. imagem unica    nenhum sha256 de imagem aparece em dois splits
  D. rotulos         rotulo existe, e finito, dentro de [0,1], area > 0 e classe dentro do `nc`
  E. k-fold          listas de treino e validacao disjuntas, validacao nao vazia, exatamente `k` dobras
  F. quase-duplicata mesma imagem re-fotografada em outro split (dHash) -- o vazamento que o sha nao pega

Uso:
  auditoria_dataset.py --dataset DIR [--kfold DIR] [--tolerancia-dhash N]

Severidade: as checagens A a E falham. A quase-duplicata (F) so falha com `--tolerancia-dhash 0`
(dHash exato, a mesma regra que o montador usa para agrupar); com tolerancia > 0 ela sai como
AVISO, porque nesta base a tolerancia 4 e frouxa (medido: aHash <= 4 colapsou 123 de 124 frames).

Sai 0 quando passa; 1 quando acha problema (lista ate 5 de cada); 2 quando a entrada nao serve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import numpy as np
from collections import defaultdict
from pathlib import Path

def sha256(p: Path) -> str:
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def dhash(caminho: Path, tam: int = 8) -> str | None:
    """Hash perceptual do mesmo tipo usado no montador; None quando a imagem nao abre.

    Imagem SEM estrutura (cor chapada, desfoque total) produz hash degenerado -- todos os bits iguais
    -- e nesse caso o dHash nao decide nada: comparar dois chapados acusaria "quase-duplicata" em
    qualquer par. Quem chama trata `None` como "sem sinal", nunca como "igual".
    """
    try:
        from PIL import Image
        with Image.open(caminho) as im:
            cinza = np.asarray(im.convert('L').resize((tam + 1, tam)), dtype=np.int16)
    except Exception:
        return None
    comparacoes = cinza[:, :-1] > cinza[:, 1:]
    if comparacoes.all() or not comparacoes.any():
        return None                     # sem gradiente: dHash nao distingue nada
    bits = 0
    for linha in comparacoes.reshape(-1):
        bits = (bits << 1) | (1 if linha else 0)
    return f'{bits:0{tam * tam // 4}x}'


def distancia(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count('1')


def ler_data_yaml(caminho: Path) -> list[str]:
    texto = caminho.read_text(errors='ignore')
    if 'names:' not in texto:
        raise ValueError(f'data.yaml sem names: {caminho}')
    resto = texto.split('names:', 1)[1].strip()
    if resto.startswith('['):
        return [x.strip().strip('\'"') for x in resto.strip('[]').split(',') if x.strip()]
    nomes = []
    for linha in resto.splitlines():
        if linha.strip().startswith('-'):
            nomes.append(linha.strip()[1:].strip().strip('\'"'))
    return nomes


def checar(dataset: Path, kfold: Path | None,
           tolerancia: int = 0) -> tuple[list[str], list[str], list[str]]:
    """`tolerancia=0` compara dHash EXATO (regra do montador); >0 vira aviso, nao falha."""
    problemas: list[str] = []
    avisos: list[str] = []
    resumo: list[str] = []
    manifesto = dataset / 'manifest.json'
    if not manifesto.is_file():
        raise ValueError(f'sem manifest.json em {dataset}: monte o dataset antes de auditar')
    itens = json.loads(manifesto.read_text()).get('itens') or []
    if not itens:
        raise ValueError('manifesto sem itens')

    # A. integridade. Convencao do manifesto: `sha256` e da FONTE e `sha256_derivado` do arquivo
    # gravado (recorte/transformacao muda os bytes). Sem o derivado declarado, o sha NAO e conferivel
    # aqui -- isso e aviso, nao falha, e inventar falha aqui acusaria o montador por um manifesto
    # legado legitimo.
    sem_arquivo, sha_divergente, nao_conferivel = [], [], 0
    for item in itens:
        caminho = dataset / 'images' / item['split'] / item['arquivo']
        if not caminho.is_file():
            sem_arquivo.append(str(caminho.relative_to(dataset)))
            continue
        derivado = item.get('sha256_derivado')
        if derivado:
            if sha256(caminho) != derivado:
                sha_divergente.append(str(caminho.relative_to(dataset)))
        else:
            nao_conferivel += 1
    conferidos = len(itens) - len(sem_arquivo) - nao_conferivel
    resumo.append(f'A integridade      : {conferidos}/{len(itens)} arquivo(s) com sha conferido'
                  f' ({nao_conferivel} sem sha256_derivado declarado)')
    problemas += [f'A arquivo ausente: {p}' for p in sem_arquivo[:5]]
    problemas += [f'A sha derivado divergente: {p}' for p in sha_divergente[:5]]
    if nao_conferivel:
        avisos.append(f'A {nao_conferivel} item(ns) sem sha256_derivado: integridade nao conferivel '
                      f'localmente (manifesto legado grava o sha da fonte)')

    # B. split por item
    splits_do_item: dict[str, set[str]] = defaultdict(set)
    for item in itens:
        splits_do_item[item['item']].add(item['split'])
    cruzando = {k: sorted(v) for k, v in splits_do_item.items() if len(v) > 1}
    resumo.append(f'B split por item   : {len(splits_do_item)} item(ns), {len(cruzando)} em mais de um split')
    problemas += [f'B item {k} em {v}' for k, v in list(cruzando.items())[:5]]

    # C. mesma imagem (sha) em dois splits
    por_sha: dict[str, set[str]] = defaultdict(set)
    for item in itens:
        por_sha[item.get('sha256') or item['arquivo']].add(item['split'])
    repetidas = {k: sorted(v) for k, v in por_sha.items() if len(v) > 1}
    resumo.append(f'C imagem unica     : {len(por_sha)} sha(s), {len(repetidas)} em mais de um split')
    problemas += [f'C sha {k[:12]} em {v}' for k, v in list(repetidas.items())[:5]]

    # D. rotulos
    nc = len(ler_data_yaml(dataset / 'data.yaml'))
    ruins = []
    for item in itens:
        rotulo = dataset / 'labels' / item['split'] / (Path(item['arquivo']).stem + '.txt')
        if not rotulo.is_file():
            continue                      # imagem sem rotulo = negativa explicita
        for numero, linha in enumerate(rotulo.read_text().splitlines(), 1):
            partes = linha.split()
            if len(partes) != 5:
                ruins.append(f'{rotulo.name}:{numero} formato')
                continue
            try:
                classe = int(partes[0])
                cx, cy, w, h = (float(v) for v in partes[1:])
            except ValueError:
                ruins.append(f'{rotulo.name}:{numero} nao numerico')
                continue
            if not all(math.isfinite(v) for v in (cx, cy, w, h)) or w <= 0 or h <= 0:
                ruins.append(f'{rotulo.name}:{numero} caixa invalida')
            elif not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and 0.0 <= w <= 1.0 and 0.0 <= h <= 1.0):
                ruins.append(f'{rotulo.name}:{numero} fora de [0,1]')
            elif classe < 0 or classe >= nc:
                ruins.append(f'{rotulo.name}:{numero} classe {classe} fora de nc={nc}')
    resumo.append(f'D rotulos          : {len(itens)} imagem(ns), {len(ruins)} linha(s) ruim(ns) (nc={nc})')
    problemas += [f'D {r}' for r in ruins[:5]]

    # E. k-fold
    if kfold:
        dobras = sorted(kfold.glob('train-dobra*.txt'))
        val = sorted(kfold.glob('val-dobra*.txt'))
        resumo.append(f'E k-fold           : {len(dobras)} dobra(s) de treino, {len(val)} de validacao')
        if not dobras or len(dobras) != len(val):
            problemas.append(f'E arquivos de dobra desemparelhados: {len(dobras)} treino x {len(val)} val')
        for treino_txt in dobras:
            numero = treino_txt.stem.split('dobra')[-1]
            val_txt = kfold / f'val-dobra{numero}.txt'
            if not val_txt.is_file():
                problemas.append(f'E dobra {numero} sem val')
                continue
            t = {l.strip() for l in treino_txt.read_text().splitlines() if l.strip()}
            v = {l.strip() for l in val_txt.read_text().splitlines() if l.strip()}
            if not v:
                problemas.append(f'E dobra {numero} com validacao vazia')
            if t & v:
                problemas.append(f'E dobra {numero}: {len(t & v)} imagem(ns) em treino E val')

    # F. quase-duplicata entre splits
    por_split: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for item in itens:
        caminho = dataset / 'images' / item['split'] / item['arquivo']
        if not caminho.is_file():
            continue
        h = dhash(caminho)
        if h:
            por_split[item['split']].append((h, item['arquivo']))
    pares = []
    for split_a, split_b in (('train', 'val'), ('train', 'test'), ('val', 'test')):
        for ha, nome_a in por_split.get(split_a, []):
            for hb, nome_b in por_split.get(split_b, []):
                if distancia(ha, hb) <= tolerancia:
                    pares.append(f'{nome_a} ({split_a}) ~ {nome_b} ({split_b})')
    resumo.append(f'F quase-duplicata  : {len(pares)} par(es) com dHash <= {tolerancia} cruzando splits'
                  f' ({len(por_split.get("train", []))} train x {len(por_split.get("val", []))} val x '
                  f'{len(por_split.get("test", []))} test)')
    if tolerancia == 0:
        problemas += [f'F mesmo dHash em splits diferentes: {p}' for p in pares[:5]]
    else:
        avisos += [f'F suspeita (dHash <= {tolerancia}) {p}' for p in pares[:5]]
        if pares:
            avisos.append('F atencao: nesta base a tolerancia 4 e frouxa (aHash <= 4 ja colapsou 123 de '
                          '124 frames proprios); trate como suspeita para inspecao, nao como vazamento '
                          'provado. Use --tolerancia-dhash 0 para a regra exata do montador.')
    return resumo, problemas, avisos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', required=True, type=Path)
    ap.add_argument('--kfold', type=Path, default=None,
                    help='diretorio com train-dobraN.txt/val-dobraN.txt (opcional)')
    ap.add_argument('--tolerancia-dhash', type=int, default=0,
                    help='0 = dHash exato (regra do montador, falha); >0 = suspeita (aviso)')
    a = ap.parse_args(argv)
    try:
        resumo, problemas, avisos = checar(a.dataset, a.kfold, a.tolerancia_dhash)
    except (OSError, ValueError, KeyError) as erro:
        print(f'ENTRADA INVALIDA: {erro}', file=sys.stderr)
        return 2
    print(f'auditoria de {a.dataset}')
    for linha in resumo:
        print('  ', linha)
    for aviso in avisos:
        print('  AVISO', aviso)
    if not problemas:
        print('\nRESULTADO: OK (nenhum vazamento ou rotulo invalido encontrado)'
              + (' com avisos acima' if avisos else ''))
        return 0
    print(f'\nRESULTADO: {len(problemas)} PROBLEMA(S)')
    for p in problemas:
        print('  -', p)
    return 1


if __name__ == '__main__':
    sys.exit(main())
