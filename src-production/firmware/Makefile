# Flash do firmware do tcc-pnaat (nó de visão ESP32-CAM e nó de trigger ESP32).
# Rode da raiz do repositório com `make -C src-production/firmware <alvo>` ou direto na pasta.
#
#   make help                lista os alvos (default)
#   make flash-cam           ESP32-CAM: idf.py set-target esp32 + build + flash monitor
#   make flash-trigger       ESP32: upload MicroPython do trigger-node via esp_tool.py (venv)
#
# Variáveis:
#   PORTA_CAM      porta serial da ESP32-CAM (default placeholder; use /dev/serial/by-id/...)
#   PORTA_TRIGGER  porta serial do ESP32 do trigger (idem)
#   VENV           python do venv da raiz (default ../../.venv, criado por `make install`)

VENV          ?= ../../.venv
ESP32CAM_DIR  ?= esp32cam-test
ESP_TOOL      ?= trigger-node/host/esp_tool.py
TRIGGER_MAIN  ?= trigger-node/esp/main.py

# Prefira /dev/serial/by-id/... (estável entre reboots) ao /dev/ttyUSBn:
#   PORTA_CAM     ex.: /dev/serial/by-id/usb-Silicon_Labs_CP210x_USB_to_UART_Bridge_<id>
#   PORTA_TRIGGER ex.: /dev/serial/by-id/usb-1a86_USB_Serial_<id>
PORTA_CAM     ?= /dev/serial/by-id/ESP32-CAM
PORTA_TRIGGER ?= /dev/serial/by-id/ESP32-Trigger

AZUL  := \033[34m
VERDE := \033[32m
CINZA := \033[90m
FIM   := \033[0m

.PHONY: help flash-cam flash-trigger

help:               ## lista os alvos de flash
	@printf "%b\n" "$(AZUL)== Flash do firmware (tcc-pnaat) ==$(FIM)"
	@printf "%b\n" "$(VERDE)  make flash-cam$(FIM)      $(CINZA)ESP32-CAM: idf.py set-target esp32 + build + flash monitor em PORTA_CAM$(FIM)"
	@printf "%b\n" "$(VERDE)  make flash-trigger$(FIM)  $(CINZA)ESP32: upload trigger-node/esp/main.py -> main.py em PORTA_TRIGGER$(FIM)"
	@printf "%b\n" "$(CINZA)  PORTA_CAM=$(PORTA_CAM)  PORTA_TRIGGER=$(PORTA_TRIGGER)$(FIM)"

flash-cam:          ## grava e monitora a ESP32-CAM (exige ESP-IDF exportado: source $$IDF_PATH/export.sh)
	cd $(ESP32CAM_DIR) && idf.py set-target esp32 && idf.py build && idf.py -p $(PORTA_CAM) flash monitor

flash-trigger:      ## sobe o MicroPython do trigger (usa o venv da raiz e o esp_tool.py)
	$(VENV)/bin/python $(ESP_TOOL) --porta $(PORTA_TRIGGER) upload $(TRIGGER_MAIN) main.py