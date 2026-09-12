# Python do projeto: venv unico da raiz do clone (o mesmo usado pelo resto do repo)
PY ?= $(shell if [ -x ../.venv/bin/python ]; then echo ../.venv/bin/python; else echo python3; fi)

.PHONY: test instalacao limpar

test:
	$(PY) -m pytest -q

instalacao:
	$(PY) -m pip install -e ".[dev]"

limpar:
	rm -rf .pytest_cache
