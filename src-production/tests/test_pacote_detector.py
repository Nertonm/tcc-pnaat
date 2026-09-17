"""Fixtures sintéticas de bytes; não carregam torch/pickle nem promovem modelos."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'treino/pacote_entrega.py'


def load():
    spec = importlib.util.spec_from_file_location('pacote_detector_testado', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inputs(tmp_path):
    p = tmp_path / 'fixture.pt'
    p.write_bytes(b'NOT A PICKLE: synthetic test weight')
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    c = {'modelo': {'sha256': sha}, 'classes': ['normal', 'defeito'],
         'imgsz_treino': 480, 'letterbox': True,
         'roi_por_camera': {'usb': {'x': 0, 'y': 0, 'w': 1, 'h': 1}},
         'rotacao_graus': {'usb': 90},
         'limiares_por_imgsz': {'480': {'normal': .3, 'defeito': .2, 'calibrado': True, 'fonte': 'fixture-only'},
                                '416': {'normal': None, 'defeito': None, 'calibrado': False}}}
    manifest = tmp_path / 'manifest.json'
    manifest.write_bytes(b'{"fixture": true}')
    m = {'peso_sha256': sha, 'classes': c['classes'], 'args': {'imgsz': 480},
         'dataset': str(tmp_path), 'dataset_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest()}
    cp, mp = tmp_path / 'c.json', tmp_path / 'm.json'
    cp.write_text(json.dumps(c))
    mp.write_text(json.dumps(m))
    return p, cp, mp, tmp_path / 'output'


def edit(path, change):
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value))


def test_import_has_no_side_effects():
    with patch('pathlib.Path.mkdir', side_effect=AssertionError('mkdir on import')), patch('shutil.copy2', side_effect=AssertionError('copy on import')):
        assert callable(load().export_bundle)


def test_cli_dry_run_apply_readback(inputs):
    mod = load()
    command = [sys.executable, str(SCRIPT)]
    for option, path in zip(('peso', 'contrato', 'metadados-treino', 'saida'), inputs, strict=False):
        command += ['--' + option, str(path)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not inputs[3].exists()
    result = subprocess.run(command + ['--apply'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    model = mod.verify_bundle(inputs[3])
    assert (inputs[3] / 'preprocessamento.json').read_bytes() == inputs[1].read_bytes()
    assert (inputs[3] / 'metadados-treino.json').read_bytes() == inputs[2].read_bytes()
    assert (inputs[3] / inputs[0].name).read_bytes() == inputs[0].read_bytes()
    assert model['imgsz_calibrados'] == [480]
    assert model['manifests']['dataset']['verificado'] is True
    assert 'metricas_medidas' not in model
    assert any('ausentes' in x for x in model['limitacoes_declaradas'])
    assert model['estado'] == 'candidato_nao_promovido'


@pytest.mark.parametrize('target,change,match', [
    (1, lambda c: c['modelo'].update(sha256='0'*64), 'peso/contrato'),
    (2, lambda m: m.update(peso_sha256='0'*64), 'peso/metadados'),
    (2, lambda m: m.update(classes=['defeito', 'normal']), 'classes divergentes'),
    (2, lambda m: m['args'].update(imgsz=416), 'imgsz'),
    (1, lambda c: c['roi_por_camera']['usb'].update(w=1.1), 'ROI'),
    (1, lambda c: c['roi_por_camera']['usb'].update(w=0), 'ROI'),
    (1, lambda c: c['roi_por_camera']['usb'].update(x=.1), 'ROI'),
    (1, lambda c: c['roi_por_camera']['usb'].update(x=float('nan')), 'finito'),
    (1, lambda c: c['rotacao_graus'].update(usb=45), 'rotação'),
    (1, lambda c: c['limiares_por_imgsz']['480'].update(calibrado=False), 'calibrad'),
    (1, lambda c: c['limiares_por_imgsz']['480'].update(fonte=''), 'fonte'),
    (1, lambda c: c['limiares_por_imgsz']['480'].update(normal=1.1), 'limiar'),
    (1, lambda c: c['limiares_por_imgsz']['480'].update(normal=True), 'limiar'),
    (1, lambda c: c['limiares_por_imgsz']['416'].update(normal=.3), 'calibrad'),
    (2, lambda m: m.update(metricas_val={'f1': float('inf')}), 'finito'),
    (2, lambda m: m.update(dataset_manifest_sha256='0'*64), 'manifest'),
    (2, lambda m: m.pop('dataset_manifest_sha256'), 'manifest'),
])
def test_negative_gates(inputs, target, change, match):
    edit(inputs[target], change)
    with pytest.raises(ValueError, match=match):
        load().export_bundle(*inputs, apply=True)
    assert not inputs[3].exists()
    assert not list(inputs[3].parent.glob('.pacote-detector-*'))


def test_missing_metadata(inputs):
    inputs[2].unlink()
    with pytest.raises(FileNotFoundError):
        load().export_bundle(*inputs)


def test_existing_and_racing_output_preserved(inputs):
    mod = load()
    inputs[3].mkdir()
    sentinel = inputs[3] / 'keep'
    sentinel.write_bytes(b'keep')
    with pytest.raises(ValueError, match='existe'):
        mod.export_bundle(*inputs, apply=True)
    assert sentinel.read_bytes() == b'keep'
    sentinel.unlink()
    inputs[3].rmdir()
    original = mod.rename_new
    def racing(source, dest):
        dest.mkdir()
        (dest / 'other').write_bytes(b'other writer')
        original(source, dest)
    with patch.object(mod, 'rename_new', racing), pytest.raises(FileExistsError):
        mod.export_bundle(*inputs, apply=True)
    assert (inputs[3] / 'other').read_bytes() == b'other writer'
    assert not list(inputs[3].parent.glob('.pacote-detector-*'))


def test_failure_only_removes_owned_staging(inputs):
    mod = load()
    unrelated = inputs[3].parent / '.pacote-detector-existing'
    unrelated.mkdir()
    with patch.object(mod.shutil, 'copyfile', side_effect=OSError('injected')), pytest.raises(OSError):
        mod.export_bundle(*inputs, apply=True)
    assert list(inputs[3].parent.glob('.pacote-detector-*')) == [unrelated]
    assert not inputs[3].exists()


def test_weight_change_during_copy_rejected(inputs):
    """Copia corrompida no meio da escrita tem de ser RECUSADA (mensagem e do verificador).
    """
    mod = load()
    original = mod.shutil.copyfile
    def corrupt(source, dest):
        original(source, dest)
        Path(dest).write_bytes(b'corrupt')
    with patch.object(mod.shutil, 'copyfile', corrupt), pytest.raises(ValueError, match='checksum|nao casa|divergente'):
        mod.export_bundle(*inputs, apply=True)
    assert not inputs[3].exists()


def test_checksum_readback_rejects_tamper(inputs):
    mod = load()
    mod.export_bundle(*inputs, apply=True)
    (inputs[3] / inputs[0].name).write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='checksum'):
        mod.verify_bundle(inputs[3])
