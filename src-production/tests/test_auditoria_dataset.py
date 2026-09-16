"""Auditoria do dataset montado: prova que ela pega vazamento e rotulo ruim, e que nao inventa problema.

O fixture monta um dataset minimo de verdade (imagens JPEG, rotulos YOLO, manifest com sha256) e depois
injeta cada defeito. Um auditor que nunca falha nao e verificacao; um que sempre falha tambem nao.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

APP = Path(__file__).resolve().parents[1]
AUDITOR = APP / 'treino' / 'auditoria_dataset.py'


def _auditor():
    spec = importlib.util.spec_from_file_location('auditoria_dataset', AUDITOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _imagem(caminho: Path, valor: int, *, semente: int = 0) -> Path:
    """Imagem com estrutura de BAIXA frequencia (bloco claro em fundo escuro), como uma foto real.

    Ruido aleatorio nao serve de fixture: depois do reencode o dHash dele muda, e o teste acusaria o
    auditor por um artefato do fixture.
    """
    from PIL import Image
    caminho.parent.mkdir(parents=True, exist_ok=True)
    gerador = np.random.default_rng(semente)
    quadro = np.full((24, 24, 3), 40, dtype=np.uint8)
    linha, coluna = (int(v) for v in gerador.integers(0, 12, size=2))
    quadro[linha:linha + 12, coluna:coluna + 12] = min(255, 120 + valor % 100)
    Image.fromarray(quadro).save(caminho, format='JPEG', quality=90)
    return caminho


def _dataset(tmp_path: Path, *, vazamento: bool = False, rotulo_ruim: bool = False) -> Path:
    base = tmp_path / 'dataset'
    for split in ('train', 'val', 'test'):
        (base / 'images' / split).mkdir(parents=True, exist_ok=True)
        (base / 'labels' / split).mkdir(parents=True, exist_ok=True)
    itens = []
    # 6 itens: 4 train, 1 val, 1 test; cada item tem 2 frames
    plano = [('item-a', 'train', 10), ('item-b', 'train', 30), ('item-c', 'train', 50),
             ('item-d', 'train', 70), ('item-e', 'val', 110), ('item-f', 'test', 150)]
    for indice, (item, split, tom) in enumerate(plano):
        for quadro in range(2):
            nome = f'{split}__{item}__{quadro}.jpg'
            caminho = _imagem(base / 'images' / split / nome, tom + quadro,
                              semente=indice * 10 + quadro)
            (base / 'labels' / split / (Path(nome).stem + '.txt')).write_text(
                '0 0.500000 0.500000 0.250000 0.250000\n')
            itens.append({'arquivo': nome, 'item': item, 'split': split, 'classe': 'normal',
                          'fonte': 'humano', 'origem': f'nosso/{nome}',
                          'sha256': hashlib.sha256(caminho.read_bytes()).hexdigest()})
    if vazamento:
        # copia byte-identica de um item de train dentro de test (o sha denuncia)
        origem = base / 'images' / 'train' / itens[0]['arquivo']
        destino = base / 'images' / 'test' / 'vazada.jpg'
        destino.write_bytes(origem.read_bytes())
        itens.append({'arquivo': destino.name, 'item': itens[0]['item'], 'split': 'test',
                      'classe': 'normal', 'fonte': 'humano', 'origem': 'vazada',
                      'sha256': hashlib.sha256(destino.read_bytes()).hexdigest()})
    if rotulo_ruim:
        (base / 'labels' / 'train' / (Path(itens[1]['arquivo']).stem + '.txt')).write_text(
            '0 1.200000 0.500000 0.250000 0.250000\n')   # centro fora de [0,1]
    (base / 'data.yaml').write_text(
        f'path: {base}\ntrain: images/train\nval: images/val\ntest: images/test\n'
        f'nc: 1\nnames: [normal]\n')
    (base / 'manifest.json').write_text(json.dumps(
        {'classes': ['normal'], 'itens': itens}, ensure_ascii=False))
    return base


def test_dataset_limpo_passa(tmp_path):
    resumo, problemas, _ = _auditor().checar(_dataset(tmp_path), None, 0)
    assert problemas == [], problemas
    assert any('split por item' in r for r in resumo)


def test_imagem_repetida_em_outro_split_e_pega(tmp_path):
    _, problemas, _ = _auditor().checar(_dataset(tmp_path, vazamento=True), None, 0)
    assert any(p.startswith('C ') for p in problemas), problemas
    assert any(p.startswith('B ') for p in problemas), problemas      # mesmo item em dois splits


def test_rotulo_fora_de_zero_um_e_pego(tmp_path):
    _, problemas, _ = _auditor().checar(_dataset(tmp_path, rotulo_ruim=True), None, 0)
    assert any('fora de [0,1]' in p for p in problemas), problemas


def test_quase_duplicata_entre_splits_e_pega(tmp_path):
    base = _dataset(tmp_path)
    # mesma cena com bytes diferentes (dHash igual): copia com textura levemente deslocada
    from PIL import Image
    origem = base / 'images' / 'val' / sorted((base / 'images' / 'val').glob('*.jpg'))[0].name
    igual = np.array(Image.open(origem)).astype(np.int16)
    # mesma cena, bytes diferentes: outro encode e brilho um pouco acima (caso real de re-foto).
    # +1 de brilho mantem a distancia de dHash em 2 (<= 4); +3 e q=60 ja cai para 8 e nao e o caso.
    quase = np.clip(igual + 1, 0, 255).astype(np.uint8)
    caminho = base / 'images' / 'test' / 'quase.jpg'
    Image.fromarray(quase).save(caminho, format='JPEG', quality=85)
    manifesto = json.loads((base / 'manifest.json').read_text())
    manifesto['itens'].append({'arquivo': caminho.name, 'item': 'item-g', 'split': 'test',
                               'classe': 'normal', 'fonte': 'humano', 'origem': 'quase',
                               'sha256': hashlib.sha256(caminho.read_bytes()).hexdigest()})
    (base / 'manifest.json').write_text(json.dumps(manifesto, ensure_ascii=False))
    _, problemas, avisos = _auditor().checar(base, None, 4)
    assert not any(p.startswith('F ') for p in problemas), 'tolerancia > 0 nao pode falhar'
    assert any('suspeita' in av for av in avisos), avisos
    _, problemas_exatos, _ = _auditor().checar(base, None, 0)
    assert not problemas_exatos, problemas_exatos      # dHash difere: o caso e tolerante, nao exato


def test_manifesto_legado_sem_derivado_vira_aviso_e_nao_falha(tmp_path):
    base = _dataset(tmp_path)
    manifesto = json.loads((base / 'manifest.json').read_text())
    for item in manifesto['itens'][:2]:
        item.pop('sha256')                      # legado: sem sha nenhum declarado
    (base / 'manifest.json').write_text(json.dumps(manifesto, ensure_ascii=False))
    resumo, problemas, avisos = _auditor().checar(base, None, 0)
    assert not any(p.startswith('A ') for p in problemas), problemas
    assert any('sem sha256_derivado' in a for a in avisos), avisos


def test_sha_derivado_divergente_e_falha(tmp_path):
    base = _dataset(tmp_path)
    manifesto = json.loads((base / 'manifest.json').read_text())
    manifesto['itens'][0]['sha256_derivado'] = 'f' * 64
    (base / 'manifest.json').write_text(json.dumps(manifesto, ensure_ascii=False))
    _, problemas, _ = _auditor().checar(base, None, 0)
    assert any('sha derivado divergente' in p for p in problemas), problemas


def test_kfold_com_vazamento_entre_listas_e_pego(tmp_path):
    base = _dataset(tmp_path)
    kfold = tmp_path / 'listas'
    kfold.mkdir()
    imagens = sorted(str(p) for p in (base / 'images' / 'train').glob('*.jpg'))
    (kfold / 'train-dobra0.txt').write_text('\n'.join(imagens) + '\n')
    (kfold / 'val-dobra0.txt').write_text(imagens[0] + '\n')     # mesma imagem nos dois lados
    _, problemas, _ = _auditor().checar(base, kfold, 0)
    assert any('treino E val' in p for p in problemas), problemas


def test_manifesto_ausente_e_entrada_invalida(tmp_path):
    with pytest.raises(ValueError):
        _auditor().checar(tmp_path, None, 4)


def test_cli_sai_um_quando_acha_problema(tmp_path):
    import subprocess, sys
    base = _dataset(tmp_path, vazamento=True)
    r = subprocess.run([sys.executable, str(AUDITOR), '--dataset', str(base)],
                       capture_output=True, text=True)
    assert r.returncode == 1, r.stdout + r.stderr
    assert 'PROBLEMA' in r.stdout


def test_cli_sai_zero_no_dataset_limpo(tmp_path):
    import subprocess, sys
    base = _dataset(tmp_path)
    r = subprocess.run([sys.executable, str(AUDITOR), '--dataset', str(base)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'RESULTADO: OK' in r.stdout
