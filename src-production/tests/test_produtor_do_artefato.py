"""O produtor do artefato .npz tem de existir NA arvore de producao.

Por que este teste existe (achado 2026-09-16): o canario da cadeia
(`canario_modelo_artefato.py`) reusa o `carrega()` do produtor do artefato para montar EXATAMENTE o
conjunto que o json declara. O produtor tinha ficado so em `src-production/revisar/treino/`, e o
`dataset/TRABALHO/` que o canario apontava nao existe mais: o canario estava quebrado
(`ModuleNotFoundError`) sem nenhum teste acusando, porque nenhum exercitava esse caminho.

Este teste e barato de proposito: nao importa torch nem le dado. Ele verifica o CONTRATO de
existencia e de resolucao, que e o que faltava.
"""
from __future__ import annotations

import ast
import importlib.machinery
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
PIPELINE = APP / 'treino'
CANARIO = APP / 'canario_modelo_artefato.py'


def test_produtor_do_artefato_esta_na_arvore():
    assert (PIPELINE / 'compara_extratores.py').is_file()
    assert (PIPELINE / 'exporta_modelo.py').is_file()


def test_produtor_expoe_carrega():
    fonte = (PIPELINE / 'compara_extratores.py').read_text()
    funcoes = {no.name for no in ast.walk(ast.parse(fonte)) if isinstance(no, ast.FunctionDef)}
    assert 'carrega' in funcoes


def test_canario_resolve_o_produtor_pela_producao():
    fonte = CANARIO.read_text()
    assert 'PIPELINE = Path(__file__).resolve().parent / "treino"' in fonte
    assert 'str(RAIZ / "dataset" / "TRABALHO")' not in fonte, \
        'o canario voltou a apontar para o dado fora do git em vez da arvore de producao'


def test_produtor_e_importavel_a_partir_da_arvore():
    achado = importlib.machinery.PathFinder().find_spec('compara_extratores', [str(PIPELINE)])
    assert achado is not None and achado.origin == str(PIPELINE / 'compara_extratores.py')
