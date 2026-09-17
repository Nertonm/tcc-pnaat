# Atalhos da ENTREGA. Cada alvo delega para a arvore certa: nada de logica nova aqui.
# O venv e unico, na raiz do clone.
PY      ?= .venv/bin/python

.PHONY: install verificar lint

# Instalacao reproduzivel (idempotente): venv da raiz + o pacote do produto.
install:
	@test -x "$(PY)" || { \
	  if command -v uv >/dev/null 2>&1; then uv venv --python 3.11 .venv; \
	  elif command -v python3.11 >/dev/null 2>&1; then python3.11 -m venv .venv; \
	  elif command -v python3.12 >/dev/null 2>&1; then python3.12 -m venv .venv; \
	  else echo "erro: o pacote exige Python >=3.11 e <3.13; instale python3.11/3.12 ou uv (uv venv --python 3.11 .venv)"; exit 1; fi; \
	}
	"$(PY)" -m pip install --upgrade pip
	"$(PY)" -m pip install -e "src-production[dev,leitura,serial]"

# O que "pronto" significa nesta entrega: produto + firmware.
verificar:
	make -C src-production verificar

lint:
	make -C src-production lint
