# venv padrão na raiz do code-workspace
PY ?= .venv/bin/python
# raiz do dataset
DS ?= ../dataset
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
	python3 -m venv .venv
	.venv/bin/pip install -e . pytest numpy scipy opencv-python Pillow

# Entrega 2 - demo da PoC: entrada -> execucao -> resultado (uma execucao, sem intervencao)
demo:
	PYTHONPATH=src $(PY) scripts/demo_poc.py --frames 3 --pausa 1.0

# gera perturbacoes de CONTROLE (nao sao defeito real) para provar reacao do modelo
controle:
	PYTHONPATH=src $(PY) scripts/gerar_perturbacao_controle.py --origem $(DS)/dataset/normal/frame_0000.jpg --tipo oclusao --dest $(DS)/controle --seed 7
	PYTHONPATH=src $(PY) scripts/gerar_perturbacao_controle.py --origem $(DS)/dataset/normal/frame_0001.jpg --tipo risco --dest $(DS)/controle --seed 11

# PoC-01 sem hardware: mesma logica do firmware, eventos identicos no terminal
simular-poc01:
	PYTHONPATH=src $(PY) scripts/simular_trigger.py --caso todos
