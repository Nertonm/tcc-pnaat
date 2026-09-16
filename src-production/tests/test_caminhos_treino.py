"""Regressoes de caminhos: sem treino, GPU ou escrita de artefatos ML."""
import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

APP = Path(__file__).resolve().parents[1]
REPO = next(p for p in APP.parents if (p / 'docs').is_dir() and (p / 'dataset').is_dir())
PIPELINE = APP / 'treino'


def load_helper(path):
    spec = importlib.util.spec_from_file_location('caminhos_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_raizes_e_contrato(monkeypatch):
    monkeypatch.delenv('PNAAT_DADOS', raising=False)
    monkeypatch.delenv('PNAAT_MODELOS', raising=False)
    m = load_helper(PIPELINE / 'caminhos.py')
    assert m.RAIZ_REPO == REPO
    assert m.PIPELINE == PIPELINE
    assert m.CONTRATO == PIPELINE / 'contrato'
    assert m.PNAAT_DADOS == REPO.parent
    assert m.PNAAT_MODELOS == REPO.parent.parent / 'pnaat-modelos'


def test_realocacao_e_ambiente(tmp_path, monkeypatch):
    repo = tmp_path / 'clone'
    (repo / 'docs').mkdir(parents=True)
    (repo / 'dataset').mkdir()
    path = repo / 'layout' / 'mais' / 'profundo' / 'treino' / 'caminhos.py'
    path.parent.mkdir(parents=True)
    path.write_bytes((PIPELINE / 'caminhos.py').read_bytes())
    monkeypatch.setenv('PNAAT_DADOS', str(tmp_path / 'dados'))
    monkeypatch.setenv('PNAAT_MODELOS', str(tmp_path / 'pesos'))
    m = load_helper(path)
    assert m.RAIZ_REPO == repo
    assert m.CONTRATO == path.parent / 'contrato'
    assert m.PNAAT_DADOS == tmp_path / 'dados'
    assert m.PNAAT_MODELOS == tmp_path / 'pesos'
    (repo / 'docs').rmdir()
    with pytest.raises(RuntimeError, match='docs.*dataset'):
        load_helper(path)


def test_make_caminhos_e_parametros():
    env = {k: v for k, v in os.environ.items() if k not in ('PY', 'PNAAT_MODELOS', 'PNAAT_DADOS')}
    p = subprocess.run(['make', '-n', 'treino-run'], cwd=APP, env=env, text=True, capture_output=True)
    assert p.returncode == 0, p.stderr
    assert str(REPO / '.venv/bin/python') in p.stdout
    assert str(REPO.parent.parent / 'pnaat-modelos/v10-lateral-detector-roi') in p.stdout
    assert str(PIPELINE / 'treina_v1.py') in p.stdout
    p = subprocess.run(['make', '-n', 'treino-run', 'PY=' + sys.executable, 'PNAAT_MODELOS=/tmp/modelos', 'TAG=probe', 'EPOCHS=3', 'IMGSZ=64'], cwd=APP, env=env, text=True, capture_output=True)
    assert p.returncode == 0, p.stderr
    assert sys.executable in p.stdout
    assert '/tmp/modelos/probe-lateral-detector-roi' in p.stdout
    assert '--epochs 3' in p.stdout and '--imgsz 64' in p.stdout


def test_make_sem_fallback(tmp_path):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'dataset').mkdir()
    app = tmp_path / 'arvore' / 'revisar'
    app.mkdir(parents=True)
    (app / 'Makefile').write_bytes((APP / 'Makefile').read_bytes())
    p = subprocess.run(['make', '-n', 'test'], cwd=app, text=True, capture_output=True, env={k:v for k,v in os.environ.items() if k != 'PY'})
    assert p.returncode != 0
    assert 'PY' in p.stderr


def test_montador_import_seguro():
    # o montador do pipeline ativo; o v0 e historico e nao vive na arvore de producao
    sys.path.insert(0, str(PIPELINE))
    try:
        import monta_v1_detector as m
    finally:
        sys.path.pop(0)
    assert m.G == REPO
    assert m.DS == REPO / 'dataset'
    assert m.CSV_HUMANO == REPO / 'dataset' / 'TRABALHO' / 'anotacoes-ls.csv'


def test_scripts_sem_ancestral_fixo():
    # Historicos executam ML ou escrevem metadados ao importar: inspecionar AST.
    excluded = {'treina_v1.py', 'pacote_entrega.py', 'monta_v1_detector.py', 'kfold_por_item.py'}
    for path in PIPELINE.glob('*.py'):
        if path.name in excluded:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == 'parents':
                assert '__file__' not in ast.unparse(node), path.name


def test_filas_raizes_sem_executar_fluxos():
    for path in (PIPELINE / 'filas').glob('*.sh'):
        lines = path.read_text().splitlines()
        starts = [i for i, line in enumerate(lines) if line.startswith(('RAIZ=', 'REPO='))]
        if not starts:
            continue
        start = starts[0]
        var = lines[start].split('=', 1)[0]
        end = next(i for i in range(start, len(lines)) if lines[i] == 'done')
        fragment = '\n'.join(lines[start:end + 1])
        pip = next((line for line in lines if line.startswith('PIP=')), '')
        fragment += '\n' + pip + '\nprintf "%s\\n" "$' + var + '" "${PIP:-}"'
        p = subprocess.run(['bash', '-c', fragment, str(path)], cwd='/tmp', text=True, capture_output=True)
        assert p.returncode == 0, (path.name, p.stderr)
        result = p.stdout.splitlines()
        assert result[0] == str(REPO), path.name
        if pip:
            assert result[1] == str(PIPELINE), path.name
