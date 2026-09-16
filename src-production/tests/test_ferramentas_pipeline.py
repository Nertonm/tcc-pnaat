"""Ferramentas do pipeline portadas de revisar: existem, sao executaveis e nao fogem das regras.

Regras que este teste faz valer (sao regra do projeto, nao preferencia):
  * intermediario NUNCA em /tmp (o tmpfs compartilhado ja perdeu um dataset);
  * a frente CORPO tem os dois lados (montagem e treino) na arvore;
  * o guardiao de recursos existe e e shell valido;
  * os alvos do Makefile para essas ferramentas respondem.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
TREINO = APP / 'treino'

CORPO = ['monta_corpo.py', 'monta_corpo_detector.py', 'treina_corpo.py', 'treina_corpo_cls.py',
         'monta_deformidade.py', 'le_smoke_corpo.py']


def test_frente_corpo_esta_na_arvore():
    for nome in CORPO:
        assert (TREINO / nome).is_file(), nome


def test_frente_corpo_compila():
    for nome in CORPO + ['auditoria_dataset.py']:
        r = subprocess.run(['python3', '-m', 'py_compile', str(TREINO / nome)],
                           capture_output=True, text=True)
        assert r.returncode == 0, f'{nome}: {r.stderr}'


def test_auditoria_de_dataset_existe_e_roda():
    alvo = TREINO / 'auditoria_dataset.py'
    assert alvo.is_file()
    r = subprocess.run(['python3', str(alvo), '--help'], capture_output=True, text=True)
    assert r.returncode == 0 and '--dataset' in r.stdout


def test_nenhum_script_de_treino_usa_tmp_como_intermediario():
    """A regra e literal: caminho /tmp/ em CODIGO (comentario pode citar a regra)."""
    ofensores = []
    for caminho in sorted(TREINO.glob('*.py')):
        for numero, linha in enumerate(caminho.read_text().splitlines(), 1):
            if linha.lstrip().startswith('#'):
                continue
            if re.search(r'["\']/tmp/', linha):
                ofensores.append(f'{caminho.name}:{numero}: {linha.strip()[:80]}')
    assert not ofensores, 'intermediario em /tmp: ' + ' | '.join(ofensores)


def test_guardiao_de_recursos_existe_e_e_shell_valido():
    alvo = TREINO / 'guardiao_treino.sh'
    assert alvo.is_file()
    r = subprocess.run(['bash', '-n', str(alvo)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    texto = alvo.read_text()
    for marca in ('RAM_MIN_MB', 'LOAD_MAX', 'TEMP_ABORTA', 'WATCHDOG'):
        assert marca in texto, marca


def test_alvos_do_makefile_para_as_ferramentas():
    for alvo in ('auditar-dataset', 'treino-corpo-dataset', 'treino-corpo-run', 'treino-run-seguro'):
        r = subprocess.run(['make', '-n', alvo], cwd=str(APP), capture_output=True, text=True,
                           env={'PATH': '/usr/bin:/bin', 'PNAAT_MODELOS': '/tmp/modelos'})
        assert r.returncode == 0, f'{alvo}: {r.stderr}'
        assert 'auditoria_dataset.py' in r.stdout or 'corpo' in r.stdout or 'guardiao' in r.stdout
