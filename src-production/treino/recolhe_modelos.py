"""Recolhe os modelos treinados num acervo canonico e regenera o indice versionado.

Origem:  PNAAT_MODELOS (ver treino/caminhos.py; so leitura: nada e movido nem apagado de la)
Destino: <diretorio pai do clone>/modelos/<familia>/<tag>/  -- copias conferidas por sha256
Repo:    models/INDEX.csv e models/README.md (caminhos relativos, sem caminho pessoal)

Uso:
    make indice-modelos                       # usa o default de caminhos.py
    make indice-modelos PNAAT_MODELOS=<dir>   # aponta outro diretorio de runs

Cada copia e conferida por sha256 contra a origem; peso de sha identico nao e copiado duas vezes.
Campo de metrica vazio no indice significa que a medida nao foi encontrada ao lado do peso.
"""
import csv
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import caminhos

RAIZ_REPO = caminhos.RAIZ_REPO
ACERVO = RAIZ_REPO.parent / 'modelos'
INDICE = RAIZ_REPO / 'models' / 'INDEX.csv'
README = RAIZ_REPO / 'models' / 'README.md'
CAMPOS = ['modelo_id', 'familia', 'tag', 'arquivo', 'sha256', 'bytes', 'imgsz', 'epochs',
          'metrica', 'metrica_fonte', 'quando', 'origem', 'copia_canonica']


def sha(p: Path) -> str:
    with p.open('rb') as fh:
        return hashlib.file_digest(fh, 'sha256').hexdigest()


def familia_de(rel: Path) -> str:
    return rel.parts[0] if len(rel.parts) > 1 else 'raiz'


def tag_de(rel: Path) -> str:
    partes = list(rel.parts[:-1])
    if 'weights' in partes:
        return partes[partes.index('weights') - 1]
    return partes[-1] if partes else 'raiz'


def metrica_do_entorno(peso: Path, familia_dir: Path, raiz: Path) -> dict:
    """Metadados do run: o que existir ao lado do peso, sem sintetizar numero."""
    saida = {'imgsz': '', 'epochs': '', 'metrica': '', 'metrica_fonte': '', 'quando': ''}
    for cand in (peso.parent.parent / 'model-meta.json', familia_dir / 'model-meta.json'):
        if not cand.is_file():
            continue
        try:
            dado = json.loads(cand.read_text())
        except (OSError, ValueError):
            continue
        args = dado.get('args') or {}
        saida['imgsz'] = args.get('imgsz', saida['imgsz'])
        saida['epochs'] = args.get('epochs', saida['epochs'])
        metricas = dado.get('metricas_val') or {}
        chave = next((k for k in metricas if 'mAP50(B)' in k), None)
        if chave:
            saida['metrica'] = round(float(metricas[chave]), 4)
            saida['metrica_fonte'] = f'{cand.relative_to(raiz).as_posix()}#metricas_val'
        saida['quando'] = dado.get('quando', saida['quando'])
        break
    return saida


def copiar_metadados(raiz: Path) -> int:
    """Metadados de TODA pasta de topo dos runs: ha familia sem peso proprio (ex.: so medidas)."""
    copiados = 0
    for pasta in sorted(p for p in raiz.iterdir() if p.is_dir()):
        destino = ACERVO / pasta.name
        destino.mkdir(parents=True, exist_ok=True)
        for padrao in ('*.json', '*.yaml'):
            for p in sorted(pasta.glob(padrao)):
                if not (destino / p.name).exists():
                    shutil.copyfile(p, destino / p.name)
                    copiados += 1
    return copiados


def copiar_pacotes(raiz: Path) -> int:
    entrega = raiz / 'ENTREGA'
    if not entrega.is_dir():
        return 0
    copiados = 0
    for d in sorted(entrega.iterdir()):
        if not d.is_dir():
            continue
        destino = ACERVO / 'ENTREGA' / d.name
        destino.mkdir(parents=True, exist_ok=True)
        for arquivo in sorted(d.iterdir()):
            if arquivo.is_file() and not (destino / arquivo.name).exists():
                shutil.copyfile(arquivo, destino / arquivo.name)
                copiados += 1
    return copiados


def escrever_indice(linhas: list[dict]) -> None:
    INDICE.parent.mkdir(parents=True, exist_ok=True)
    with INDICE.open('w', newline='', encoding='utf-8') as fh:
        escritor = csv.DictWriter(fh, fieldnames=CAMPOS)
        escritor.writeheader()
        for linha in sorted(linhas, key=lambda l: l['modelo_id']):
            escritor.writerow(linha)
    por_familia = defaultdict(int)
    for linha in linhas:
        por_familia[linha['familia']] += 1
    README.parent.mkdir(parents=True, exist_ok=True)
    README.write_text(
        '# Modelos treinados: acervo e indice\n'
        '\n'
        '`INDEX.csv` e a lista de TODO peso treinado deste projeto: id, familia, run, sha256, bytes,\n'
        'imgsz/epocas quando o run declara, metrica de validacao quando existe e o caminho de origem.\n'
        'Nao ha numero sintetizado: campo vazio significa que a medida nao foi encontrada ao lado do\n'
        'peso.\n'
        '\n'
        'O peso NAO entra no repositorio (dado, nao codigo). O acervo canonico fica fora do clone, no\n'
        'diretorio irmao:\n'
        '\n'
        '```text\n'
        '<pai do clone>/modelos/<familia>/<tag>/<peso>.pt     copia conferida por sha256\n'
        '<pai do clone>/modelos/ENTREGA/<pacote>/            pacotes de entrega como estao\n'
        '```\n'
        '\n'
        'A origem (o diretorio de runs em `PNAAT_MODELOS`) e somente leitura: nada e movido nem\n'
        'apagado de la. Para reindexar depois de treinar:\n'
        '\n'
        '```sh\n'
        'make indice-modelos\n'
        '```\n'
        '\n'
        f'Estado do indice: {len(linhas)} peso(s) em {len(por_familia)} familia(s), '
        f'gerado em {datetime.now(timezone.utc).isoformat(timespec="seconds")}.\n')


def main() -> int:
    raiz = caminhos.PNAAT_MODELOS
    if not raiz.is_dir():
        sys.exit(f'PNAAT_MODELOS nao e diretorio: {raiz}')
    pesos = sorted(p for p in raiz.rglob('*.pt') if p.is_file())
    print(f'origem: {raiz} | pesos encontrados: {len(pesos)}')

    linhas, vistos, copiados, iguais, falhas = [], {}, 0, 0, []
    for peso in pesos:
        rel = peso.relative_to(raiz)
        familia, tag = familia_de(rel), tag_de(rel)
        digest = sha(peso)
        if digest in vistos:
            copia, iguais = vistos[digest], iguais + 1
        else:
            destino_dir = ACERVO / familia / tag
            destino_dir.mkdir(parents=True, exist_ok=True)
            destino = destino_dir / peso.name
            try:
                shutil.copyfile(peso, destino)
            except OSError as erro:
                falhas.append(f'{rel}: {erro}')
                continue
            if sha(destino) != digest:
                falhas.append(f'{rel}: sha divergente na copia')
                continue
            copia = destino.relative_to(ACERVO).as_posix()
            vistos[digest] = copia
            copiados += 1
        meta = metrica_do_entorno(peso, raiz / familia, raiz)
        linhas.append({
            'modelo_id': f'{familia}/{tag}/{peso.name}', 'familia': familia, 'tag': tag,
            'arquivo': peso.name, 'sha256': digest, 'bytes': peso.stat().st_size,
            'imgsz': meta['imgsz'], 'epochs': meta['epochs'], 'metrica': meta['metrica'],
            'metrica_fonte': meta['metrica_fonte'], 'quando': meta['quando'],
            'origem': f'{raiz.name}/{rel.as_posix()}', 'copia_canonica': copia})

    extras = copiar_metadados(raiz)
    pacotes = copiar_pacotes(raiz)
    escrever_indice(linhas)
    print(f'pesos copiados: {copiados} | sha identico ja coberto: {iguais} | '
          f'metadados: {extras} | arquivos de pacote: {pacotes}')
    print('falhas:', falhas or 'nenhuma')
    print('indice:', INDICE.relative_to(RAIZ_REPO), '| linhas:', len(linhas))
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
