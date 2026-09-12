# Python do projeto: venv unico na raiz do clone (preferido) ou local ao code-workspace
PY ?= $(shell if [ -x ../.venv/bin/python ]; then echo ../.venv/bin/python; elif [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
# raiz do dataset
DS ?= ../dataset
MODEL ?= patchcore

# .PHONY e obrigatorio: sem ele, alvos com nome de diretorio existente (demo/, dataset/)
# sao tratados como "up to date" e o comando nao roda.
.PHONY: test test-vision sanitizar sanitizar-apply doctor validar dataset treino clean install demo controle poc04 simular-poc01 hooks

# instala o gate neste clone (core.hooksPath e config local: precisa rodar em cada checkout)
hooks:
	git config --local core.hooksPath "$$(git rev-parse --show-toplevel)/code-workspace/scripts/git-hooks"
	@echo "gate instalado: $$(git config --get core.hooksPath)"
	@git hook run pre-commit >/dev/null 2>&1 && echo "hook responde" || echo "hook responde (sai != 0 quando ha achado)"

test:
	$(PY) -m pytest -q

# testes que exigem numpy/opencv/scipy (mesmo venv)
test-vision:
	$(PY) -m pytest tests/test_preproc.py tests/test_validar_pares.py -q

# higiene/sanitizacao (F4): sai != 0 se houver algo que nao pode ser publico
sanitizar:
	$(PY) scripts/sanitizar_repo.py

sanitizar-apply:
	$(PY) scripts/sanitizar_repo.py --apply

# checagem de ambiente/API/dados/higiene do repo
doctor:
	$(PY) scripts/doctor.py

# gate dos pares gerados (schema/bbox/mascara/isolamento)
validar:
	$(PY) scripts/validar_pares.py --pares $(DS)/gerados --origem $(DS)/origem

# valida e copia os aprovados para dataset/defective + relatorio
dataset:
	$(PY) scripts/montar_dataset.py --gerados $(DS)/gerados --origem $(DS)/origem --dest $(DS)/dataset/defective

# treina/avalia one-class no NOSSO dataset (normal vs defective)
treino:
	$(PY) scripts/treinar_dataset.py --root $(DS)/dataset --model $(MODEL)

clean:
	rm -rf .pytest_cache

install:
	python3 -m venv ../.venv
	../.venv/bin/python -m pip install --upgrade pip
	../.venv/bin/python -m pip install -e ".[dev]"

# Entrega 2 - demo da PoC: entrada -> execucao -> resultado (uma execucao, sem intervencao)
demo:
	PYTHONPATH=src $(PY) scripts/demo_poc.py --frames 3 --pausa 1.0

# gera perturbacoes de CONTROLE (nao sao defeito real) para provar reacao do modelo
controle:
	PYTHONPATH=src $(PY) scripts/gerar_perturbacao_controle.py --origem $(DS)/dataset/normal/frame_0000.jpg --tipo oclusao --dest $(DS)/controle --seed 7
	PYTHONPATH=src $(PY) scripts/gerar_perturbacao_controle.py --origem $(DS)/dataset/normal/frame_0001.jpg --tipo risco --dest $(DS)/controle --seed 11

# PoC-04 - fusao por dominio: harness de casos declarados com ground truth (sai != 0 se divergir)
poc04:
	PYTHONPATH=src $(PY) scripts/avaliar_poc04.py

# PoC-01 sem hardware: mesma logica do firmware, eventos identicos no terminal
simular-poc01:
	PYTHONPATH=src $(PY) scripts/simular_trigger.py --caso todos
