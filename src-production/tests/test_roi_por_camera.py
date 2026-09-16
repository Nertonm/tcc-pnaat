"""ROI por camera: a derivacao TEM de separar vista, e a saturacao TEM de falhar.

Bug medido em 2026-09-16: o deriador misturava caixas de `topo` e `lateral` no mesmo envelope por
camera; com caixas de topo (que atravessam o quadro), a ROI derivada virava o quadro inteiro e o script
ainda imprimia `cobertura=1.000 OK`. Comparado com a ROI que montou o treino do v9b, divergia em
csi/usb/espcam. Este teste fixa as duas coisas: o filtro de vista e o gate de saturacao.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
SCRIPT = APP / 'treino' / 'roi_por_camera.py'

LATERAIS = [
    ('nosso/rig/frame_0001.jpg', 'lateral', 'tampa', 40.0, 5.0, 10.0, 12.0),
    ('nosso/rig/frame_0002.jpg', 'lateral', 'tampa', 44.0, 4.0, 9.0, 11.0),
]
TOPO = [
    ('nosso/rig/topo_frame_0001.jpg', 'topo', 'tampa', 5.0, 5.0, 90.0, 88.0),
]


def _csv(tmp_path: Path, linhas) -> Path:
    caminho = tmp_path / 'anotacoes.csv'
    with caminho.open('w', newline='', encoding='utf-8') as fh:
        escritor = csv.writer(fh)
        escritor.writerow(['task_id', 'imagem', 'vista', 'coerencia', 'caixas', 'valido'])
        for indice, (imagem, vista, rotulo, x, y, w, h) in enumerate(linhas, 1):
            caixas = json.dumps([{'rotulo': rotulo, 'x': x, 'y': y, 'width': w, 'height': h}])
            escritor.writerow([indice, imagem, vista, 'concorda_com_a_fonte', caixas, 'sim'])
    return caminho


def _roda(tmp_path: Path, linhas, *extras: str) -> subprocess.CompletedProcess:
    saida = tmp_path / 'roi.json'
    r = subprocess.run([sys.executable, str(SCRIPT), '--csv', str(_csv(tmp_path, linhas)),
                        '--saida', str(saida), *extras], capture_output=True, text=True, cwd=str(APP))
    return r, saida


def test_roi_ignora_caixas_de_outra_vista(tmp_path):
    r, saida = _roda(tmp_path, LATERAIS + TOPO)
    assert r.returncode == 0, r.stdout + r.stderr
    roi = json.loads(saida.read_text())['cameras']['rig']['roi_normalizada']
    # envelope SO das laterais: x 0.28/w 0.37/h 0.29 -- e NAO o quadro inteiro das caixas de topo
    assert abs(roi['x'] - 0.28) < 0.01, roi
    assert abs(roi['w'] - 0.37) < 0.02, roi
    assert abs(roi['h'] - 0.29) < 0.02, roi
    assert roi['w'] < 0.9 and roi['h'] < 0.9, roi


def test_roi_de_topo_satura_e_exige_pedido(tmp_path):
    """Caixa de topo cobre a cena: o envelope satura, e saturar tem de falhar por padrao."""
    r, saida = _roda(tmp_path, LATERAIS + TOPO, '--vista', 'topo')
    assert r.returncode == 3 and 'SATURACAO' in r.stdout, r.stdout
    assert not saida.exists()
    r2, saida2 = _roda(tmp_path, LATERAIS + TOPO, '--vista', 'topo', '--permitir-saturacao')
    assert r2.returncode == 0, r2.stdout + r2.stderr
    roi = json.loads(saida2.read_text())['cameras']['rig']['roi_normalizada']
    assert roi['w'] >= 0.9 and roi['h'] >= 0.9, roi


def test_saturacao_reprova_o_gate(tmp_path):
    largas = [('nosso/rig/frame_%04d.jpg' % i, 'lateral', 'tampa', 2.0, 2.0, 96.0, 96.0)
              for i in range(3)]
    r, saida = _roda(tmp_path, largas)
    assert r.returncode == 3, r.stdout + r.stderr
    assert 'SATURACAO' in r.stdout
    assert not saida.exists(), 'ROI saturada foi gravada'


def test_saturacao_aceita_com_pedido_explicito(tmp_path):
    largas = [('nosso/rig/frame_%04d.jpg' % i, 'lateral', 'tampa', 2.0, 2.0, 96.0, 96.0)
              for i in range(3)]
    r, saida = _roda(tmp_path, largas, '--permitir-saturacao')
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(saida.read_text())['cameras']['rig'].get('saturada') is True


def test_default_nao_escreve_no_contrato_da_arvore(tmp_path):
    """O default grava no contrato da arvore; o teste usa --saida e confirma que o arquivo do contrato
    nao foi tocado por esta bateria."""
    alvo = APP / 'treino' / 'contrato' / 'roi-por-camera.json'
    import hashlib
    antes = hashlib.sha256(alvo.read_bytes()).hexdigest() if alvo.is_file() else None
    _roda(tmp_path, LATERAIS)
    depois = hashlib.sha256(alvo.read_bytes()).hexdigest() if alvo.is_file() else None
    assert antes == depois
