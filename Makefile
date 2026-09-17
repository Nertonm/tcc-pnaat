# Atalhos da ENTREGA. Cada alvo delega para a arvore certa: nada de logica nova aqui.
# O venv e unico, na raiz do clone.
PY      ?= .venv/bin/python

.PHONY: install verificar lint

# Instalacao reproduzivel (idempotente): venv da raiz + o pacote do produto.
install:
	@test -x "$(PY)" || python3 -m venv .venv
	"$(PY)" -m pip install --upgrade pip
	"$(PY)" -m pip install -e "src-production[dev,leitura,serial]"

# O que "pronto" significa nesta entrega: produto + firmware.
verificar:
	make -C src-production verificar

lint:
	make -C src-production lint
