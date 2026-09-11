# venv unificado (python 3.11 com anomalib). O antigo code-workspace/.venv (3.14) esta DEPRECATED.
AI_PY ?= $(HOME)/tcc-pnaat/github/.venv/bin/python
PY ?= $(AI_PY)
# raiz do dataset
DS ?= $(HOME)/tcc-pnaat/datasets/pnaat
MODEL ?= patchcore

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
	$(AI_PY) scripts/doctor.py

# gate dos pares gerados (schema/bbox/mascara/isolamento)
validar:
	$(AI_PY) scripts/validar_pares.py --pares $(DS)/gerados --origem $(DS)/origem

# valida e copia os aprovados para dataset/defective + relatorio
dataset:
	$(AI_PY) scripts/montar_dataset.py --gerados $(DS)/gerados --origem $(DS)/origem --dest $(DS)/dataset/defective

# treina/avalia one-class no NOSSO dataset (normal vs defective)
treino:
	$(AI_PY) scripts/treinar_dataset.py --root $(DS)/dataset --model $(MODEL)

clean:
	rm -rf .pytest_cache

# DEPRECATED: cria um venv py3.14 que nao serve para anomalib. Use AI_PY.
install:
	@echo "DEPRECATED: use $(HOME)/tcc-pnaat/github/.venv (py3.11, anomalib). Nada a instalar aqui."

# Entrega 2 - demo da PoC: entrada -> execucao -> resultado (uma execucao, sem intervencao)
demo:
	PYTHONPATH=src $(AI_PY) scripts/demo_poc.py --frames 3 --pausa 1.0

# gera perturbacoes de CONTROLE (nao sao defeito real) para provar reacao do modelo
controle:
	PYTHONPATH=src $(AI_PY) scripts/gerar_perturbacao_controle.py --origem $(DS)/dataset/normal/frame_0000.jpg --tipo oclusao --dest $(DS)/controle --seed 7
	PYTHONPATH=src $(AI_PY) scripts/gerar_perturbacao_controle.py --origem $(DS)/dataset/normal/frame_0001.jpg --tipo risco --dest $(DS)/controle --seed 11

# PoC-04 - fusao por dominio: harness de casos declarados com ground truth (sai != 0 se divergir)
poc04:
	PYTHONPATH=src $(AI_PY) scripts/avaliar_poc04.py

# PoC-01 sem hardware: mesma logica do firmware, eventos identicos no terminal
simular-poc01:
	PYTHONPATH=src $(PY) scripts/simular_trigger.py --caso todos
