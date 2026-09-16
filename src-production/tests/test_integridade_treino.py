"""Regressões CPU-only: dados sintéticos, YOLO simulado só na fronteira GPU."""
import hashlib
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

PIPELINE = Path(__file__).resolve().parents[1] / 'treino'
sys.path.insert(0, str(PIPELINE))


def dataset(tmp_path, n=6):
    base = tmp_path / 'ds'
    itens = []
    for i in range(n):
        split = ('train', 'val', 'test')[i % 3]
        image = base / 'images' / split / f'{i}.jpg'
        label = base / 'labels' / split / f'{i}.txt'
        image.parent.mkdir(parents=True, exist_ok=True)
        label.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(f'image-{i}'.encode())
        label.write_text('0 0.5 0.5 0.2 0.2\n')
        itens.append(dict(arquivo=image.name, item=f'item-{i}', split=split,
                          origem=f'/data/upload/19/{i}.jpg', classe='normal',
                          sha256=hashlib.sha256(image.read_bytes()).hexdigest()))
    (base / 'manifest.json').write_text(json.dumps({'itens': itens}))
    (base / 'data.yaml').write_text(yaml.safe_dump(dict(path=str(base), train='images/train',
                        val='images/val', test='images/test', nc=1, names=['normal'])))
    return base, itens


def validator():
    try:
        return importlib.import_module('validacao_dataset').validar_dataset
    except ModuleNotFoundError:
        pytest.fail('gate independente de dataset ainda não implementado')


def test_dataset_real_override(tmp_path):
    base, _ = dataset(tmp_path)
    result = validator()(base / 'data.yaml')
    assert result['dataset'] == str(base)
    assert result['classes'] == ['normal']
    assert result['dataset_manifest_sha256'] == hashlib.sha256((base / 'manifest.json').read_bytes()).hexdigest()


@pytest.mark.parametrize('defeito', ['item', 'bytes', 'source', 'box', 'nan', 'classe', 'label', 'manifest', 'coverage', 'derived'])
def test_gate_rejeita_dados_invalidos(tmp_path, defeito):
    base, itens = dataset(tmp_path)
    if defeito == 'item':
        itens[1]['item'] = itens[0]['item']
    elif defeito == 'bytes':
        (base / 'images/val/1.jpg').write_bytes((base / 'images/train/0.jpg').read_bytes())
    elif defeito == 'source':
        itens[1]['sha256'] = itens[0]['sha256']
    elif defeito in ('box', 'nan', 'classe'):
        (base / 'labels/train/0.txt').write_text({'box': '0 0.9 0.5 0.8 0.2', 'nan': '0 nan 0.5 0.2 0.2', 'classe': '1 0.5 0.5 0.2 0.2'}[defeito])
    elif defeito == 'label':
        (base / 'labels/train/0.txt').unlink()
    elif defeito == 'coverage':
        itens.pop(0)
    elif defeito == 'derived':
        itens[0]['sha256_derivado'] = '0' * 64
    (base / 'manifest.json').write_text(json.dumps({'itens': itens}))
    if defeito == 'manifest':
        (base / 'manifest.json').unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        validator()(base / 'data.yaml')


def test_roi_interseccao_em_pixels():
    m = importlib.import_module('monta_v1_detector')
    assert hasattr(m, 'caixas_no_recorte'), 'falta transformacao ROI por esquinas/pixels'
    # ROI pixels x=10..60; caixa original x=0..20 -> interseção x=10..20.
    assert m.caixas_no_recorte([(0, .1, .5, .2, .2)], (100, 100), (10, 0, 60, 100))[0] == pytest.approx((0, .1, .5, .2, .2))
    assert m.caixas_no_recorte([(0, .9, .5, .1, .2)], (100, 100), (10, 0, 60, 100)) == []


def test_builder_roi_pixels_hashes_e_overwrite(tmp_path, monkeypatch):
    import csv
    from PIL import Image
    m = importlib.import_module('monta_v1_detector')
    rows = []
    for i in range(3):
        image = tmp_path / f'frame{i}.png'
        Image.new('RGB', (101, 100), (40 + i * 60, 10, 20)).save(image)
        rows.append({'imagem': str(image), 'valido': 'sim', 'vista': 'lateral',
                     'classe': 'normal', 'caixas': json.dumps([{'rotulo': 'tampa', 'x': 0, 'y': 40, 'width': 20, 'height': 20}])})
    source = tmp_path / 'anotacoes.csv'
    with source.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    roi = tmp_path / 'roi.json'
    roi.write_text(json.dumps({'cameras': {'cam': {'roi_normalizada': {'x': .1, 'y': 0, 'w': .5, 'h': 1}}}}))
    monkeypatch.setattr(m, 'CSV_HUMANO', source)
    monkeypatch.setattr(m, 'FONTES', {})
    monkeypatch.setattr(m, 'ROI_JSON', roi)
    monkeypatch.setattr(m, 'camera_do_caminho', lambda _: 'cam')
    monkeypatch.setattr(m, 'split_do_item', lambda key: ('train', 'val', 'test')[int(Path(key).stem[-1])])
    out = tmp_path / 'out'
    monkeypatch.setattr(sys, 'argv', ['builder', '--roi', '--sem-phash', '--ignorar-frescor',
                                    '--permitir-classe-ausente', '--out', str(out)])
    assert m.main() == 0
    manifest = json.loads((out / 'manifest.json').read_text())
    for row in manifest['itens']:
        image = out / 'images' / row['split'] / row['arquivo']
        assert Image.open(image).size == (50, 100)
        assert row['recorte_pixels'] == [10, 0, 60, 100]
        assert row['sha256_derivado'] == hashlib.sha256(image.read_bytes()).hexdigest()
        assert row['sha256_fonte'] != row['sha256_derivado']
        box = [float(v) for v in (out / 'labels' / row['split'] / (image.stem + '.txt')).read_text().split()]
        assert box == pytest.approx([0, .102, .5, .204, .2])
    before = (out / 'manifest.json').read_bytes()
    assert m.main() != 0
    assert (out / 'manifest.json').read_bytes() == before


def test_sequencias_nosso_agrupadas():
    m = importlib.import_module('monta_v1_detector')
    assert m.chave_de_item('nosso/rig/frame_0013.jpg') == m.chave_de_item('nosso/rig/frame_0014.jpg')


def treino_setup(tmp_path, monkeypatch):
    t = importlib.import_module('treina_v1')
    base, _ = dataset(tmp_path)
    args = tmp_path / 'args.yaml'
    args.write_text('epochs: 1\nimgsz: 480\n')
    monkeypatch.setattr(t, 'RAIZ', tmp_path / 'modelos')
    monkeypatch.setattr(t, 'ARGS_YAML', args)
    monkeypatch.setattr(sys, 'argv', ['treina', '--vista', 'lateral', '--tag', 'outro', '--data', str(base / 'data.yaml'), '--nome', 'run'])
    calls = []
    class YOLO:
        def __init__(self, model):
            self.model = str(model)
        def train(self, **kw):
            calls.append(kw)
            if not getattr(t, '_teste_sem_peso', False):
                w = Path(kw['project']) / kw['name'] / 'weights/best.pt'
                w.parent.mkdir(parents=True, exist_ok=True)
                w.write_bytes(b'best')
            return SimpleNamespace(results_dict={'metrics/mAP50(B)': .1})
        def val(self, **kw):
            assert self.model.endswith('best.pt')
            return SimpleNamespace(results_dict={'metrics/mAP50(B)': .9})
    monkeypatch.setitem(sys.modules, 'ultralytics', SimpleNamespace(YOLO=YOLO))
    return t, base, calls


def test_train_override_proveniencia_e_best(tmp_path, monkeypatch):
    t, base, calls = treino_setup(tmp_path, monkeypatch)
    assert t.main() == 0
    receipt = t.RAIZ / 'outro-lateral-detector/runs/run/training-evidence.json'
    assert receipt.is_file(), 'evidencia obrigatoria ausente'
    meta = json.loads(receipt.read_text())
    assert meta['dataset'] == str(base)
    assert meta['classes'] == ['normal']
    assert meta['metricas_val']['metrics/mAP50(B)'] == .9
    assert meta['dataset_manifest_sha256'] is not None


def test_train_sem_best_falha(tmp_path, monkeypatch):
    t, _, _ = treino_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(t, '_teste_sem_peso', True, raising=False)
    assert t.main() != 0


def test_train_run_existente_nao_sobrescreve(tmp_path, monkeypatch):
    t, _, calls = treino_setup(tmp_path, monkeypatch)
    run = t.RAIZ / 'outro-lateral-detector/runs/run'
    run.mkdir(parents=True)
    assert t.main() != 0
    assert calls == []


def test_train_gate_antes_yolo(tmp_path, monkeypatch):
    t, base, calls = treino_setup(tmp_path, monkeypatch)
    (base / 'manifest.json').unlink()
    assert t.main() != 0
    assert calls == []


def test_kfold_exclui_test_e_inclui_upload(tmp_path, monkeypatch):
    k = importlib.import_module('kfold_por_item')
    base, itens = dataset(tmp_path, 12)
    monkeypatch.setattr(sys, 'argv', ['kfold', '--dataset', str(base), '--k', '2', '--dry-run'])
    assert k.main() == 0
    files = list((base / 'kfold-listas').rglob('val-dobra*.txt'))
    assert len(files) == 2
    paths = [x for f in files for x in f.read_text().splitlines()]
    assert len(paths) == 8
    assert all('/test/' not in p for p in paths)
    for f in (base / 'kfold-listas').rglob('dobra*.yaml'):
        assert yaml.safe_load(f.read_text())['names'] == ['normal']


@pytest.mark.parametrize('kvalue', [2, 8])
def test_kfold_completo_recibos_best(tmp_path, monkeypatch, kvalue):
    k = importlib.import_module('kfold_por_item')
    base, _ = dataset(tmp_path, 12)
    modelos = tmp_path / 'modelos'
    monkeypatch.setattr(k, 'MODELOS', str(modelos))
    monkeypatch.setattr(sys, 'argv', ['kfold', '--dataset', str(base), '--k', str(kvalue)])
    calls = []
    def train(cmd, **kwargs):
        calls.append(cmd)
        name = cmd[cmd.index('--nome') + 1]
        data = Path(cmd[cmd.index('--data') + 1])
        receipt = modelos / 'kfold-lateral-detector-roi/runs' / name / 'training-evidence.json'
        receipt.parent.mkdir(parents=True)
        metrics = {f'metrics/{m}(B)': .75 for m in ('precision', 'recall', 'mAP50', 'mAP50-95')}
        receipt.write_text(json.dumps({'data_yaml_sha256': hashlib.sha256(data.read_bytes()).hexdigest(),
                                     'avaliacao': 'best.pt/val', 'metricas_val': metrics}))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(k.subprocess, 'run', train)
    assert k.main() == 0
    assert len(calls) == kvalue
    result = json.loads(next((base / 'kfold-listas').rglob('resultado.json')).read_text())
    assert len(result['dobras']) == kvalue
    assert result['mAP50_media'] == .75


def test_kfold_falha_subprocess(tmp_path, monkeypatch):
    k = importlib.import_module('kfold_por_item')
    base, itens = dataset(tmp_path, 12)
    for i in itens:
        i['origem'] = 'nosso/' + i['arquivo']
    (base / 'manifest.json').write_text(json.dumps({'itens': itens}))
    monkeypatch.setattr(sys, 'argv', ['kfold', '--dataset', str(base), '--k', '2'])
    monkeypatch.setattr(k.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=1, stdout='', stderr='falha simulada'))
    assert k.main() != 0
    assert not list(base.parent.glob('kfold-*json'))
