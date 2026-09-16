"""Gate independente para o YAML EFETIVO; não prova identidade física não anotada.

Manifest legado: `sha256` é da fonte, não do JPEG derivado. Sempre recalculamos
hash dos bytes consumidos; quando declarado, conferimos `sha256_derivado`.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import yaml

EXTENSOES = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff'}


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ler_data(path: Path) -> tuple[dict, Path, list[str]]:
    path = path.resolve(strict=True)
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError('YAML de dados deve ser um mapa')
    root = Path(data.get('path') or path.parent)
    if not root.is_absolute():
        root = path.parent / root
    root = root.resolve(strict=True)
    names = data.get('names')
    if isinstance(names, dict):
        if set(names) != set(range(len(names))):
            raise ValueError('indices de classes devem ser consecutivos desde zero')
        names = [names[i] for i in range(len(names))]
    if not isinstance(names, list) or not names or not all(isinstance(n, str) and n for n in names):
        raise ValueError('names ausente/invalido')
    if len(set(names)) != len(names) or data.get('nc', len(names)) != len(names):
        raise ValueError('nc/names incoerentes')
    return data, root, names


def caminhos_split(root: Path, entry) -> list[Path]:
    """Diretórios ou listas; relativos sem ./ resolvem contra cwd como Ultralytics.

    Nas listas, ./ é relativo à própria lista (semântica Ultralytics). O runner
    reemite listas absolutas congeladas; nunca deixa o trainer reinterpretar YAML.
    """
    paths = []
    for value in entry if isinstance(entry, list) else [entry]:
        if not value:
            continue
        p = Path(value)
        if not p.is_absolute():
            p = root / p
        p = p.resolve(strict=True)
        if p.is_dir():
            paths.extend(sorted(q.resolve() for q in p.rglob('*') if q.suffix.lower() in EXTENSOES and q.is_file()))
        elif p.suffix.lower() == '.txt':
            for line in p.read_text().splitlines():
                line = line.strip()
                if line:
                    q = p.parent / line[2:] if line.startswith('./') else Path(line)
                    paths.append(q.resolve(strict=True))
        else:
            raise ValueError(f'entrada nao suportada: {p}')
    return paths


def label_da_imagem(image: Path) -> Path:
    parts = list(image.parts)
    if 'images' not in parts:
        raise ValueError(f'caminho sem images/: {image}')
    index = len(parts) - 1 - parts[::-1].index('images')
    parts[index] = 'labels'
    return Path(*parts).with_suffix('.txt')


def validar_boxes(label: Path, nc: int) -> list[int]:
    classes = []
    for number, line in enumerate(label.read_text().splitlines(), 1):
        if not line.strip():
            continue
        values = [float(v) for v in line.split()]
        if len(values) != 5 or not all(math.isfinite(v) for v in values):
            raise ValueError(f'box invalida {label}:{number}')
        cid, cx, cy, w, h = values
        if not cid.is_integer() or not 0 <= cid < nc:
            raise ValueError(f'classe invalida {label}:{number}')
        if (w <= 0 or h <= 0 or min(cx-w/2, cy-h/2) < -1e-6
                or max(cx+w/2, cy+h/2) > 1+1e-6):
            raise ValueError(f'box fora da imagem {label}:{number}')
        classes.append(int(cid))
    return classes


def validar_dataset(data_yaml: Path) -> dict:
    data_yaml = Path(data_yaml).resolve(strict=True)
    data, root, names = ler_data(data_yaml)
    manifest = root / 'manifest.json'
    raw = json.loads(manifest.read_text())
    if raw.get('classes') is not None and raw['classes'] != names:
        raise ValueError('classes do manifest/YAML divergentes')
    records = raw['itens']
    por_path = {}
    for item in records:
        path = (root / 'images' / item['split'] / item['arquivo']).resolve()
        if path in por_path:
            raise ValueError(f'imagem repetida no manifest: {path}')
        if not item.get('item'):
            raise ValueError(f'item ausente: {path}')
        por_path[path] = item
    seen = {key: {} for key in ('path', 'item', 'bytes', 'source')}
    evidence = {}
    for split in ('train', 'val', 'test'):
        paths = caminhos_split(root, data.get(split))
        if split in ('train', 'val') and not paths:
            raise ValueError(f'{split} vazio')
        evidence[split] = []
        for image in paths:
            if image not in por_path:
                raise ValueError(f'imagem sem proveniencia no manifest: {image}')
            record = por_path[image]
            digest = sha256(image)
            if record.get('sha256_derivado') and record['sha256_derivado'] != digest:
                raise ValueError(f'hash derivado divergente: {image}')
            source = record.get('sha256_fonte') or record.get('sha256')
            if not source or len(source) != 64 or any(c not in '0123456789abcdef' for c in source):
                raise ValueError(f'hash fonte ausente/invalido: {image}')
            keys = {'path': str(image), 'item': record['item'], 'bytes': digest, 'source': source}
            for key, value in keys.items():
                previous = seen[key].get(value)
                if previous is not None and previous != split:
                    raise ValueError(f'vazamento {key}: {previous}/{split}: {image}')
                seen[key][value] = split
            label = label_da_imagem(image)
            classes = validar_boxes(label, len(names))
            evidence[split].append({'path': str(image), 'item': record['item'],
                                    'sha256': digest, 'label_sha256': sha256(label),
                                    'classes': classes})
    return {'dataset': str(root), 'data_yaml': str(data_yaml),
            'data_yaml_sha256': sha256(data_yaml), 'classes': names,
            'dataset_manifest_sha256': sha256(manifest), 'splits': evidence,
            'preprocessamento': raw.get('preprocessamento'),
            'limite': 'disjuncao por item declarado e hashes; nao certifica identidade fisica, quase-duplicatas ou base inicial'}


def congelar_yaml(evidence: dict, directory: Path) -> Path:
    """Usa exatamente os caminhos que passaram no gate, sem defaults globais YOLO."""
    data = {'path': evidence['dataset'], 'nc': len(evidence['classes']), 'names': evidence['classes']}
    for split, records in evidence['splits'].items():
        if records:
            path = directory / f'{split}.txt'
            path.write_text(''.join(r['path'] + '\n' for r in records))
            data[split] = str(path.resolve())
    target = directory / 'data-validado.yaml'
    target.write_text(yaml.safe_dump(data, sort_keys=False))
    return target
