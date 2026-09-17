#!/usr/bin/env python3
"""Exporta candidato, nunca promove nem desserializa pesos.

CLI exige peso, contrato de preprocessamento e model-meta.json reais. Dry-run é
padrão. Metadados usam peso_sha256, classes, args.imgsz e, quando disponível,
dataset_manifest_sha256 (dataset/manifest.json). Não infere métricas ausentes.
SHA256SUMS verifica integridade, não autenticidade nem qualidade do detector.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # modulos da arvore


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value),
            'SHA-256 ausente ou inválido')
    return value


def finite_tree(value):
    if isinstance(value, float):
        require(math.isfinite(value), 'número não finito')
    elif isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'chave JSON duplicada')
            result[key] = value
        return result
    raw = path.read_bytes()
    obj = json.loads(raw, object_pairs_hook=pairs)
    require(isinstance(obj, dict), 'JSON deve ser objeto')
    finite_tree(obj)
    return raw, obj


def number(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def validate(peso, contrato, metadados):
    raw_c, c = read_json(contrato)
    weight_hash = sha256(peso)
    require(digest(c['modelo']['sha256']) == weight_hash, 'peso/contrato SHA-256 divergente')
    raw_m, m = read_json(metadados)
    require(digest(m['peso_sha256']) == weight_hash, 'peso/metadados SHA-256 divergente')
    if 'tamanho_bytes' in c['modelo']:
        require(c['modelo']['tamanho_bytes'] == peso.stat().st_size, 'tamanho do peso divergente')
    if 'peso_bytes' in m:
        require(m['peso_bytes'] == peso.stat().st_size, 'tamanho dos metadados divergente')
    classes = c['classes']
    require(isinstance(classes, list) and classes and all(isinstance(x, str) and x.strip() for x in classes)
            and len(set(classes)) == len(classes), 'classes inválidas')
    require(m['classes'] == classes, 'classes divergentes')
    size = c['imgsz_treino']
    require(type(size) is int and size > 0 and m['args']['imgsz'] == size
            and type(m['args']['imgsz']) is int, 'imgsz divergente/inválido')
    require(c['letterbox'] is True, 'letterbox deve ser true')
    rois, rotations = c['roi_por_camera'], c['rotacao_graus']
    require(isinstance(rois, dict) and rois and isinstance(rotations, dict)
            and set(rois) == set(rotations), 'ROI/rotações incompatíveis')
    for camera, roi in rois.items():
        require(isinstance(camera, str) and camera.strip() and isinstance(roi, dict), 'ROI inválida')
        x, y, w, h = (roi[k] for k in ('x', 'y', 'w', 'h'))
        require(all(number(v, 0, 1) for v in (x, y, w, h))
                and w > 0 and h > 0 and x + w <= 1 and y + h <= 1, 'ROI fora dos limites')
        require(type(rotations[camera]) is int and rotations[camera] in (0, 90, 180, 270), 'rotação inválida')
    thresholds = c['limiares_por_imgsz']
    require(isinstance(thresholds, dict) and str(size) in thresholds, 'imgsz sem limiares')
    calibrated = []
    for key, entry in thresholds.items():
        require(isinstance(key, str) and key.isdecimal() and int(key) > 0
                and str(int(key)) == key and isinstance(entry, dict), 'limiares inválidos')
        require(type(entry.get('calibrado')) is bool, 'calibração não declarada')
        if entry['calibrado']:
            require(isinstance(entry.get('fonte'), str) and entry['fonte'].strip(), 'fonte da calibração ausente')
            require(all(number(entry.get(cls), 0, 1) for cls in classes), 'limiar inválido')
            calibrated.append(int(key))
        else:
            require(all(entry.get(cls) is None for cls in classes), 'limiares não calibrados preenchidos')
    require(size in calibrated, 'imgsz de treino não calibrado')
    limitations = ['Candidato não promovido; exportação não valida inferência, segurança ou qualidade.',
                   'Calibração e classes são declarações dos insumos; peso não desserializado.']
    require(isinstance(m.get('limitacoes_declaradas', []), list)
            and all(isinstance(x, str) and x.strip() for x in m.get('limitacoes_declaradas', [])), 'limitações inválidas')
    limitations.extend(m.get('limitacoes_declaradas', []))
    if not m.get('metricas_val'):
        limitations.append('Métricas de validação ausentes; nenhuma métrica sintetizada.')
    if m.get('warning'):
        require(isinstance(m['warning'], str), 'warning inválido')
        limitations.append(m['warning'])
    manifests = {}
    declared = m.get('dataset_manifest_sha256')
    if declared is not None:
        digest(declared)
    manifest = None
    if m.get('dataset'):
        manifest = Path(m['dataset']) / 'manifest.json'
        if not manifest.is_absolute():
            manifest = metadados.parent / manifest
    if manifest is not None and manifest.is_file():
        require(declared is not None and sha256(manifest) == declared, 'manifest SHA-256 divergente/ausente')
        manifests['dataset'] = {'sha256': declared, 'verificado': True}
    else:
        manifests['dataset'] = {'sha256': declared, 'verificado': False}
        limitations.append('Manifest do dataset indisponível; procedência não verificada localmente.')
    return raw_c, raw_m, {
        'versao': 1, 'estado': 'candidato_nao_promovido', 'arquivo': peso.name,
        'sha256': weight_hash, 'classes': classes, 'imgsz_treino': size,
        'imgsz_calibrados': sorted(calibrated), 'manifests': manifests,
        'preprocessamento_sha256': hashlib.sha256(raw_c).hexdigest(),
        'metadados_treino_sha256': hashlib.sha256(raw_m).hexdigest(),
        'limitacoes_declaradas': limitations,
    }


def verify_bundle(directory):
    """Read-back fechado com a MESMA verificacao do consumidor (definicao unica do pacote).

    Antes esta funcao era uma copia propria: dois lugares definindo o formato do pacote divergem no
    primeiro ajuste, e o lado que fica para tras aceita o que o outro recusa.
    """
    from pacote_detector import verificar_bundle

    return verificar_bundle(directory)


def rename_new(source, destination):
    """Linux renameat2 NOREPLACE: destino concorrente jamais é sobrescrito."""
    libc = ctypes.CDLL(None, use_errno=True)
    fn = libc.renameat2
    fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    fn.restype = ctypes.c_int
    if fn(-100, os.fsencode(source), -100, os.fsencode(destination), 1):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


def export_bundle(peso, contrato, metadados, saida, *, apply=False):
    peso, contrato, metadados, saida = map(Path, (peso, contrato, metadados, saida))
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.pt', peso.name), 'basename do peso inseguro (exige .pt)')
    require(not os.path.lexists(saida), 'saída já existe; nunca sobrescrever')
    require(saida.parent.is_dir(), 'diretório pai da saída deve existir')
    raw_c, raw_m, model = validate(peso, contrato, metadados)
    if not apply:
        return model
    staging = Path(tempfile.mkdtemp(prefix='.pacote-detector-', dir=saida.parent))
    try:
        shutil.copyfile(peso, staging / peso.name)
        (staging / 'preprocessamento.json').write_bytes(raw_c)
        (staging / 'metadados-treino.json').write_bytes(raw_m)
        (staging / 'modelo.json').write_text(json.dumps(model, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        (staging / 'SHA256SUMS').write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in sorted(staging.iterdir())))
        verify_bundle(staging)
        rename_new(staging, saida)
        return verify_bundle(saida)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def conferir(diretorio):
    """Read-back de um pacote ja gravado, com a mesma verificacao do consumidor.

    Existe porque a doc manda conferir o pacote e nao havia CLI para isso: o verificador so rodava
    dentro da exportacao. Nao promove nada.
    """
    try:
        modelo = verify_bundle(diretorio)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'BLOQUEADO: {exc}', file=sys.stderr)
        return 2
    print('pacote confere:', diretorio)
    if isinstance(modelo, dict):
        for chave, rotulo in (('arquivo', 'peso'), ('sha256', 'sha256'),
                              ('classes', 'classes'), ('imgsz_treino', 'imgsz de treino'),
                              ('imgsz_calibrados', 'imgsz calibrados'), ('estado', 'estado')):
            if chave in modelo:
                valor = modelo[chave]
                if chave == 'sha256':
                    valor = f'{str(valor)[:32]}...'
                print(f'  {rotulo}: {valor}')
    else:
        print('  ', modelo)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pacote', type=Path, default=None,
                        help='confere um pacote JA gravado (peso + contrato + metadados + '
                             'modelo.json + SHA256SUMS) e sai; nao exporta nada')
    for option in ('peso', 'contrato', 'metadados-treino', 'saida'):
        parser.add_argument('--' + option, type=Path)
    parser.add_argument('--apply', action='store_true', help='gravar novo bundle candidato')
    args = parser.parse_args(argv)

    if args.pacote is not None:
        return conferir(args.pacote)

    faltando = [nome for nome, valor in (('--peso', args.peso), ('--contrato', args.contrato),
                                         ('--metadados-treino', args.metadados_treino),
                                         ('--saida', args.saida)) if valor is None]
    if faltando:
        parser.error('para exportar faltam: ' + ', '.join(faltando)
                     + ' (ou use --pacote DIR para conferir um pacote ja gravado)')

    try:
        model = export_bundle(args.peso, args.contrato, args.metadados_treino, args.saida, apply=args.apply)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f'BLOQUEADO: {exc}', file=sys.stderr)
        return 2
    print(json.dumps({'modo': 'apply' if args.apply else 'dry-run', 'saida': str(args.saida), 'modelo': model}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
