"""Contrato: produtor e consumidor TEM de concordar (a incongruencia que a revisao achou).

O gerador emitia um contrato sem `orientacao_entrada`/`vista_por_camera` e com fingerprint de outra
lista de campos: o consumidor recusava o que o produtor gerava. Este teste faz a ida e volta de
verdade, com insumos minimos, e falha se os dois lados divergirem de novo.

Tambem confere os caminhos entre scripts da cadeia do corpo (saida do montador == entrada do treino;
smoke lido de onde o treino grava) -- a outra incongruencia encontrada.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
TREINO = APP / 'treino'
PY = sys.executable


def _insumos(tmp_path: Path) -> dict:
    peso = tmp_path / 'candidato.pt'
    peso.write_bytes(b'peso-sintetico')
    sha = hashlib.sha256(peso.read_bytes()).hexdigest()
    meta = tmp_path / 'model-meta.json'
    meta.write_text(json.dumps({
        'tag': 'v10', 'classes': ['normal', 'tampa_ausente', 'defeito_tampa'],
        'peso': str(peso), 'peso_sha256': sha, 'args': {'imgsz': 480},
        'dataset_manifest_sha256': None, 'metricas_val': {}, 'warning': 'fixture de teste',
    }, ensure_ascii=False))
    roi = tmp_path / 'roi-por-camera.json'
    roi.write_text(json.dumps({'cameras': {
        'csi': {'roi_normalizada': {'x': 0.0, 'y': 0.0, 'w': 0.5, 'h': 0.5}},
        'usb': {'roi_normalizada': {'x': 0.25, 'y': 0.0, 'w': 0.5, 'h': 0.5}},
    }}, ensure_ascii=False))
    calibracao = tmp_path / 'calibracao-limiar.json'
    calibracao.write_text(json.dumps({
        'peso': str(peso), 'dataset': '/tmp/ds', 'imgsz': 480,
        'limiares_escolhidos_na_val': {
            'normal': {'conf': 0.30, 'f1_val': 0.82},
            'tampa_ausente': {'conf': 0.15, 'f1_val': 1.0},
            'defeito_tampa': {'conf': 0.30, 'f1_val': 1.0}},
    }, ensure_ascii=False))
    return {'peso': peso, 'meta': meta, 'roi': roi, 'calibracao': calibracao}


def _gerar(tmp_path: Path, insumos: dict, *extras: str) -> subprocess.CompletedProcess:
    base = [PY, str(TREINO / 'gera_contrato_preproc.py'),
            '--peso', str(insumos['peso']), '--metadados', str(insumos['meta']),
            '--roi', str(insumos['roi']), '--calibracao', str(insumos['calibracao']),
            '--vistas', 'csi=lateral1,usb=lateral2', '--rotacao', 'csi=0,usb=90',
            '--saida', str(tmp_path / 'preprocessamento.json'), *extras]
    return subprocess.run(base, capture_output=True, text=True, cwd=str(APP))


def test_contrato_gerado_e_aceito_pelo_consumidor(tmp_path):
    insumos = _insumos(tmp_path)
    r = _gerar(tmp_path, insumos)
    assert r.returncode == 0, r.stdout + r.stderr
    sys.path.insert(0, str(APP))
    from preparo_detector import ContratoDePreprocessamento
    contrato = ContratoDePreprocessamento.abrir(tmp_path / 'preprocessamento.json')
    assert contrato.imgsz_treino == 480
    assert contrato.calibrado_no_imgsz_de_treino() is True
    assert contrato.limiares(480)['tampa_ausente'] == pytest.approx(0.15)
    assert contrato.vista_da_camera('usb').value == 'lateral2'
    assert contrato.roi_da_camera('csi')['w'] == pytest.approx(0.5)


def test_gerador_recusa_declaracao_incompleta(tmp_path):
    insumos = _insumos(tmp_path)
    for extras in (('--vistas', 'csi=lateral1'), ('--rotacao', 'csi=0')):
        r = _gerar(tmp_path, insumos, *extras)
        assert r.returncode == 2, (extras, r.stdout + r.stderr)
        # a recusa nomeia o que falta (vista lateral2 ou rotacao da camera) -- nunca passa
        assert re.search(r'declaracao incompleta|sem rotacao', r.stdout + r.stderr), (
            extras, r.stdout + r.stderr)


def test_gerador_recusa_calibracao_de_outro_peso(tmp_path):
    insumos = _insumos(tmp_path)
    outro = tmp_path / 'outro.pt'
    outro.write_bytes(b'outro-peso')
    calibracao = json.loads(insumos['calibracao'].read_text())
    calibracao['peso'] = str(outro)
    insumos['calibracao'].write_text(json.dumps(calibracao))
    r = _gerar(tmp_path, insumos)
    assert r.returncode == 2 and 'OUTRO peso' in (r.stdout + r.stderr)


def test_gerador_sem_calibracao_recusa_por_padrao(tmp_path):
    """Fail-closed: contrato sem limiar calibrado nao sai sem pedido explicito."""
    insumos = _insumos(tmp_path)
    base = [PY, str(TREINO / 'gera_contrato_preproc.py'), '--peso', str(insumos['peso']),
            '--metadados', str(insumos['meta']), '--roi', str(insumos['roi']),
            '--vistas', 'csi=lateral1,usb=lateral2', '--rotacao', 'csi=0,usb=90',
            '--saida', str(tmp_path / 'preprocessamento.json')]
    r = subprocess.run(base, capture_output=True, text=True, cwd=str(APP))
    assert r.returncode == 2, r.stdout + r.stderr
    assert not (tmp_path / 'preprocessamento.json').exists(), 'contrato provisorio foi gravado'
    fonte = (TREINO / 'gera_contrato_preproc.py').read_text()
    assert '--permitir-nao-calibrado' not in fonte, (
        'o gerador voltou a oferecer contrato provisorio: producao nao aceita')


def test_gerador_nao_sobrescreve_sem_forcar(tmp_path):
    insumos = _insumos(tmp_path)
    assert _gerar(tmp_path, insumos).returncode == 0
    r = _gerar(tmp_path, insumos)
    assert r.returncode == 2 and 'ja existe' in (r.stdout + r.stderr)


def test_fingerprint_usa_os_campos_do_consumidor():
    sys.path.insert(0, str(APP))
    from preparo_detector import CAMPOS_DO_FINGERPRINT
    fonte = (TREINO / 'gera_contrato_preproc.py').read_text()
    assert 'CAMPOS_DO_FINGERPRINT' in fonte, 'o gerador voltou a manter lista propria de campos'
    for campo in ('orientacao_entrada', 'vista_por_camera'):
        assert campo in fonte
    assert len(CAMPOS_DO_FINGERPRINT) >= 8


def test_caminhos_da_cadeia_do_corpo_combinam():
    montador = (TREINO / 'monta_corpo_detector.py').read_text()
    treino = (TREINO / 'treina_corpo.py').read_text()
    leitor = (TREINO / 'le_smoke_corpo.py').read_text()
    saida = re.search(r"OUT = M / '([^']+)'", montador)
    entrada = re.search(r'PNAAT_MODELOS / "([^"]+)" / "([^"]+)" / "data.yaml"', treino)
    assert saida and entrada, 'padrao de caminho mudou: revisar esta checagem'
    lido = f'{entrada.group(1)}/{entrada.group(2)}'
    assert saida.group(1) == lido, (
        f'montador escreve em {saida.group(1)} e o treino le {lido}')
    proj = re.search(r'PROJ = str\(PNAAT_MODELOS / "([^"]+)"\)', treino)
    assert proj and f'{proj.group(1)}/corpo/smoke-proprio.json' in leitor, (
        'o leitor do smoke nao aponta para onde o treino grava')
