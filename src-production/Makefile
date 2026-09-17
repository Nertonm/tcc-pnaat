# Python do projeto: venv unico da raiz do clone (o mesmo usado pelo resto do repo)
APP := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
RAIZ_REPO := $(shell p="$(APP)"; while [ ! -d "$$p/docs" ] || [ ! -d "$$p/dataset" ]; do [ "$$p" != / ] || exit 1; p=$$(dirname "$$p"); done; printf '%s' "$$p")
ifeq ($(RAIZ_REPO),)
$(error raiz com docs e dataset nao encontrada)
endif
PY ?= $(RAIZ_REPO)/.venv/bin/python
ifeq ($(shell command -v "$(PY)" 2>/dev/null),)
$(error Python indisponivel: $(PY); defina PY explicitamente ou prepare a .venv da raiz)
endif
export RAIZ_REPO

.PHONY: test instalacao limpar
.PHONY: treino-dataset treino-run treino-avalia treino-kfold checa-modelos
.PHONY: contrato pacote smoke-detector test-firmware verificar
.PHONY: auditar-dataset treino-corpo-dataset treino-corpo-run treino-run-seguro
.PHONY: indice-modelos lint test-trigger trigger-simular test-rig rig-serve

test:
	$(PY) -m pytest -q

instalacao:
	$(PY) -m pip install -e ".[dev]"

limpar:
	rm -rf .pytest_cache

# ---------------------------------------------------------------------------
# Pipeline de treino (PNAAT). Codigo em treino/, contrato em treino/contrato/.
#
# Contrato de caminhos (o mesmo que os scripts usam):
#   PNAAT_MODELOS  pesos, runs, datasets derivados. Default: irmao do diretorio pai do clone.
#   PNAAT_DADOS    dados fora do repo (datasets/, det_runs/, modelos/ antigos).
#                  Default: diretorio pai do clone.
# Os dois vem do ambiente quando existem; o default nunca usa nome de usuario.
# ---------------------------------------------------------------------------
TREINO   := $(APP)/treino
CONTRATO := $(TREINO)/contrato

PNAAT_DADOS   ?= $(abspath $(RAIZ_REPO)/..)
PNAAT_MODELOS ?= $(abspath $(RAIZ_REPO)/../../pnaat-modelos)
export PNAAT_DADOS
export PNAAT_MODELOS

TAG    ?= v10
VISTA  ?= lateral
SPLIT  ?= test
K      ?= 5
IMGSZ  ?= 480
EPOCHS ?= 150
CONFS  ?= 0.05,0.15,0.30

DATASET ?= $(PNAAT_MODELOS)/$(TAG)-$(VISTA)-detector-roi/dataset
PESO    ?= $(PNAAT_MODELOS)/$(TAG)-$(VISTA)-detector-roi/runs/$(TAG)-rig/weights/best.pt

checa-modelos:
	@if [ ! -d "$(PNAAT_MODELOS)" ]; then \
	  echo "erro: PNAAT_MODELOS nao existe: $(PNAAT_MODELOS)"; \
	  echo "defina o diretorio de pesos e datasets, por exemplo:"; \
	  echo "  make treino-run PNAAT_MODELOS=/caminho/para/pnaat-modelos"; \
	  exit 1; \
	fi

# Monta o dataset do nosso dominio: split por item, quase-duplicata e ROI opcional.
treino-dataset: checa-modelos
	$(PY) $(TREINO)/monta_v1_detector.py --vista $(VISTA) --roi --somente-dominio \
	  --out "$(DATASET)"

# Treina a partir do dataset montado acima. Args versionados: $(CONTRATO)/treino-v1-args.yaml
treino-run: checa-modelos
	$(PY) $(TREINO)/treina_v1.py --vista $(VISTA) --tag $(TAG) --roi --epochs $(EPOCHS) \
	  --imgsz $(IMGSZ) --data "$(DATASET)/data.yaml" --nome $(TAG)-rig

# Avalia o candidato: mAP por dominio e classe, depois P/R/F1 por limiar de confianca.
treino-avalia: checa-modelos
	$(PY) $(TREINO)/avalia_por_dominio.py --dataset "$(DATASET)" --peso "$(PESO)" \
	  --split $(SPLIT) --imgsz $(IMGSZ)
	$(PY) $(TREINO)/avalia_limiares.py --dataset "$(DATASET)" --peso "$(PESO)" \
	  --split $(SPLIT) --confs $(CONFS) --imgsz $(IMGSZ)

# Auditoria adversarial do dataset MONTADO: integridade, split por item, imagem repetida,
# rotulos, k-fold e quase-duplicata (dHash) cruzando splits. Sai != 0 quando acha vazamento.
auditar-dataset:
	$(PY) $(TREINO)/auditoria_dataset.py --dataset "$(DATASET)" $(if $(KFOLD),--kfold "$(KFOLD)",)

# Frente CORPO: monta o dataset (uma classe corpo_deformidade + negativos) e treina.
treino-corpo-dataset:
	$(PY) $(TREINO)/monta_corpo_detector.py

treino-corpo-run:
	$(PY) $(TREINO)/treina_corpo.py

# Treino com a porta de recursos (uma rodada por vez na GPU, com watchdog).
treino-run-seguro: checa-modelos
	$(TREINO)/guardiao_treino.sh $(PY) $(TREINO)/treina_v1.py --vista $(VISTA) --tag $(TAG) \
	  --roi --epochs $(EPOCHS) --imgsz $(IMGSZ) --data "$(DATASET)/data.yaml" --nome $(TAG)-rig

# Metrica de aceitacao: k-fold por item, com listas de treino e validacao disjuntas.
treino-kfold: checa-modelos
	$(PY) $(TREINO)/kfold_por_item.py --dataset "$(DATASET)" --k $(K) --vista $(VISTA) \
	  --imgsz $(IMGSZ) --epochs $(EPOCHS) --tag $(TAG)kf

# ---------------------------------------------------------------------------
# Pacote do detector: o elo entre treinar e inferir.
#
#   make pacote  PESO=... PACOTE=<dir>          empacota (dry-run; --apply grava)
#   make smoke-detector PACOTE=... CAPTURA=... ITEM=... DB=... JANELA=... \\
#       ALINHAMENTO=... EQUIPAMENTO=... LOCALIZACAO=...   roda a cadeia com o pacote (decisao real)
#
# O pacote NAO promove nada: quem sobe servico e decisao humana.
# ---------------------------------------------------------------------------
# NADA aqui tem default: pacote, captura, item, banco, janela, alinhamento e identidade do rig
# sao dado da instalacao. Default pre-programado faz o alvo falhar longe da causa -- ou rodar
# no lugar errado.
PACOTE   ?=
CAPTURA  ?=
ITEM        ?=
DB          ?=
JANELA      ?=
# o rig/operador DECLARA o posicionamento; sem atestado, nada e utilizavel (fail-closed)
ALINHAMENTO ?=
EQUIPAMENTO ?=
LOCALIZACAO ?=

pacote: checa-modelos
	$(PY) $(TREINO)/pacote_entrega.py --peso "$(PESO)" \
	  --contrato "$(CONTRATO)/preprocessamento.json" \
	  --metadados-treino "$(PNAAT_MODELOS)/$(TAG)-$(VISTA)-detector-roi/model-meta.json" \
	  --saida "$(PACOTE)" $(if $(APLICAR),--apply,)

exige-pacote:
	@faltando=""; \
	for par in "PACOTE=$(PACOTE)" "CAPTURA=$(CAPTURA)" "ITEM=$(ITEM)" "DB=$(DB)" \
	           "JANELA=$(JANELA)" "ALINHAMENTO=$(ALINHAMENTO)" \
	           "EQUIPAMENTO=$(EQUIPAMENTO)" "LOCALIZACAO=$(LOCALIZACAO)"; do \
	  [ -n "$${par#*=}" ] || faltando="$$faltando $${par%%=*}"; \
	done; \
	if [ -n "$$faltando" ]; then \
	  echo "erro: declare$$faltando (nada e pre-programado nesta arvore)"; \
	  echo "  make smoke-detector PACOTE=<dir> CAPTURA=<dir> ITEM=<id> DB=<arquivo> \\"; \
	  echo "      JANELA=<segundos> ALINHAMENTO=<declarado|nao_verificado> \\"; \
	  echo "      EQUIPAMENTO=<nome> LOCALIZACAO=<nome>"; \
	  exit 1; \
	fi

# Execucao da cadeia com o pacote. Contrato NAO calibrado no imgsz de treino e recusado aqui: e o
# caminho de operacao, e operacao nao decide com limiar provisorio.
smoke-detector: exige-pacote
	$(PY) $(APP)/orquestracao.py --captura "$(CAPTURA)" --item "$(ITEM)" --db "$(DB)" \
	  --pacote-modelo "$(PACOTE)" --janela $(JANELA) --alinhamento $(ALINHAMENTO) \
	  --equipamento "$(EQUIPAMENTO)" --localizacao "$(LOCALIZACAO)"

# Suite do firmware (o gate do repositorio ja roda este caminho; aqui fica no alvo do produto).
test-firmware:
	$(PY) -m pytest -q $(APP)/firmware/esp32cam-test/tests

# O que "esta pronto" significa nesta arvore: produto + firmware.
verificar: test test-firmware
	@echo "produto e firmware verificados"

# Recolhe os pesos treinados no acervo canonico e regenera models/INDEX.csv.
# PNAAT_MODELOS aponta o diretorio dos runs (default em treino/caminhos.py).
indice-modelos:
	$(PY) $(TREINO)/recolhe_modelos.py

# Regras de correcao e estilo (config em pyproject.toml). Requer ruff no ambiente.
lint:
	$(PY) -m ruff check .


# No de trigger/sensor (portado do canonico): logica pura e simulador sem hardware.
test-trigger:
	$(PY) -m pytest -q $(APP)/firmware/trigger-node/tests

trigger-simular:
	$(PY) $(APP)/firmware/trigger-node/host/simular_trigger.py --caso todos


# Servico de rig (captura-3-cameras/serie/manifest), portado do canonico.
# Exige PNAAT_SERIES_DIR no ambiente; a ponte e descoberta por PNAAT_PONTE (default 127.0.0.1:8094).
test-rig:
	cd $(APP)/rig_service && $(RAIZ_REPO)/.venv/bin/python test_rotas.py

rig-serve:
	cd $(APP)/rig_service && PYTHONPATH=. $(RAIZ_REPO)/.venv/bin/python app.py --porta $${PORTA:-8090}
