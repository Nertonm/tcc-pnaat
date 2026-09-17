# Replicação de ponta a ponta

Manual para levar o sistema do zero até a cadeia completa em um ambiente novo. Ele descreve os
componentes que existem neste repositório e a ordem em que são instalados e executados. Configuração
de instalação (endereços, portas, diretórios) é declarada por ambiente; não há valor pessoal no
arquivo.

## 1. Organização da cadeia

```text
sensor E18-D80NK
   -> trigger-node (ESP32 MicroPython, PRESENCE_PIN=27)
   -> ponte serial esp32cam_site.py  (dona da porta; CMD_TRIG)
   -> ESP32-CAM (uma foto por trigger, frame UART com CRC)
   -> rig_service (captura-3-cameras + série/manifest em PNAAT_SERIES_DIR)
   -> ingerir_serie.py (manifest + mapa câmera->vista)
   -> orquestracao/classificador (pacote YOLO) -> decisao/conformidade
   -> registro SQLite -> api.py -> site
```

Duas formas de executar o mesmo núcleo descrito acima:

- **Com hardware**: as rotas acima, com câmera, sensor e portas reais.
- **Sem hardware**: `make -C src-production verificar`, `test-trigger` e `test-rig` rodam a lógica
  com câmera falsa e dados isolados; `trigger-simular` reproduz os eventos do firmware sem placa.

## 2. Pré-requisitos

| Item | Uso |
|---|---|
| Linux (x86-64 ou ARM64) | Python, câmeras, ESP e serial |
| Python >= 3.11 e < 3.13 | produto, testes e ferramentas |
| ESP-IDF v5.x | compilar e gravar a ESP32-CAM |
| portas seriais identificáveis | ponte e trigger node por `by-id` |
| câmera CSI, webcam USB, ESP32-CAM | três vistas: topo, lateral1, lateral2 |
| E18-D80NK | sensor de presença do trigger |

Para a inferência YOLO e o treino, GPU com `torch`/`ultralytics` e o pacote detector em
`PNAAT_MODELOS`/`--pacote-modelo`. O pacote do entregável está publicado em
https://huggingface.co/Nerton/pnaat-modelos, com `SHA256SUMS` por pacote, então não é
preciso treinar para consumir o detector. Sem isso, a API, o registro e as rotas de
leitura ainda operam.

## 3. Clone e ambiente

```bash
git clone <url-do-repositorio> && cd tcc-pnaat
make install
```

O `make install` cria `.venv` na raiz e instala o pacote `src-production[dev,leitura,serial]`. As PoCs
foram removidas deste checkout e não são necessárias. Para treino e YOLO:

```bash
.venv/bin/python -m pip install -e "src-production[inferencia]"
```

## 4. Firmware

### 4.1 Nó de visão: ESP32-CAM

```bash
cd src-production/firmware/esp32cam-test
idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB-CAM flash monitor
```

O firmware faz uma foto por trigger (`CMD_TRIG`), standby entre fotos e frame UART com CRC. O
contrato binário e o receptor estão em `transport_bin.py`; a suíte cobre transporte, CRC, lacunas e
duplicatas (17 testes).

### 4.2 Nó de trigger: ESP32 + E18-D80NK

```bash
cd src-production/firmware/trigger-node/host
.venv/bin/python esp_tool.py upload ../esp/main.py main.py
.venv/bin/python esp_tool.py run main.py --segundos 30
```

Pinos confirmados na bancada: `PRESENCE_PIN=27`, `CAPTURE_OUT_PIN=26`. O esquemático de referência
está em `ESP32S3-Trigger.zip` (Wokwi: divisor 2,2 kΩ/3,3 kΩ, GPIO27 no projeto). A saída do sensor é
NPN active-low; use divisor de nível se medir 5 V no sinal. A lógica pura (`presence.py`) tem 5 testes.

## 5. Serviços (ordem de subida)

### 5.1 Ponte serial (rodada no nó de visão)

```bash
.venv/bin/python src-production/firmware/esp32cam-test/esp32cam_site.py \
  --porta 8094 --host 127.0.0.1 \
  --serial /dev/serial/by-id/<camera> --serial-trigger /dev/serial/by-id/<trigger>
```

A ponte é dona única das portas, lê o trigger, comanda a captura e publica status em `PNAAT_PONTE`
(default `http://127.0.0.1:8094`).

### 5.2 Serviço de rig (três câmeras, série e manifest)

```bash
export PNAAT_SERIES_DIR=/caminho/das/series/series-3-cameras   # obrigatório
export PNAAT_PONTE=http://127.0.0.1:8094                        # ponte acima
.venv/bin/python src-production/rig_service/app.py --porta 8090
```

Rotas principais do rig: `/estado`, `/dataset-series`, `/historico`,
`/teste-trigger-3-cameras`, `/configurar-delay`, `/capturar-3-cameras` e
`/series-3-cameras/<serie>/<arquivo>`. A captura grava a série com `manifest.json` e os JPEGs das
três câmeras em `PNAAT_SERIES_DIR`.

### 5.3 Gateway da API e site

```bash
export PNAAT_RIG=http://127.0.0.1:8090
export PNAAT_PONTE=http://127.0.0.1:8094
.venv/bin/python src-production/api.py --db hub.db --porta 8080 --host 127.0.0.1
```

O gateway expõe as rotas de consulta e as operações de rig/ponte; bind fora do loopback exige token
Bearer. O site é servido na mesma origem.

## 6. Ciclo de ponta a ponta

1. O item passa pelo E18-D80NK; o trigger-node abre a janela e publica `CAPTURE_WINDOW_OPEN`.
2. A ponte recebe o trigger, envia `CMD_TRIG` à ESP32-CAM e guarda o frame.
3. O operador (ou o autômato da instalação) pede `POST /api/rig/captura`; o rig grava a série
   `series-3-cameras/<serie>/` com `manifest.json`.
4. A série é importada para o registro:

```bash
.venv/bin/python src-production/ingerir_serie.py \
  --serie "$PNAAT_SERIES_DIR/<serie>" --lote L1 --db hub.db \
  --roi 0.0 0.0 1.0 1.0 \
  --mapa csi=topo,usb=lateral2,espcam=lateral1 \
  --janela-ms 2000 --alinhamento declarado
```

5. `orquestracao.executar()` roda a única cadeia de decisão: pré-processamento, classificador por
   domínio, conformidade e registro idempotente por `item_id`.
6. O site/API consultam o SQLite; o operador pode registrar correção append-only.

O mapa `camera -> vista` é dado da instalação e não tem default; trocar a ordem das laterais muda a
decisão, por isso é sempre declarado.

## 7. Verificação

| O quê | Comando | Esperado |
|---|---|---|
| Produto e firmware | `make -C src-production verificar` | 506 + 4 skip no produto, 17 no firmware |
| Lint | `make -C src-production lint` | `All checks passed!` |
| Trigger (lógica pura) | `make -C src-production test-trigger` | 5 passed |
| Trigger (simulador) | `make -C src-production trigger-simular` | janelas esperadas por caso |
| Rig (câmera falsa) | `make -C src-production test-rig` | `teste das rotas: 24 ok, 0 falha` |
| Rig (bordas) | `python src-production/rig_service/testes_edge.py` | `49 ok, 0 falha` |
| API | `curl http://127.0.0.1:8080/api/health` | JSON 200 |
| Rig | `curl http://127.0.0.1:8090/estado` | JSON com estado da captura |
| Ponte | `curl http://127.0.0.1:8094/status` | JSON com serial/frames |

## 8. Dados externos que não viajam no repositório

| Artefato | Para quê | Como apontar |
|---|---|---|
| `PNAAT_SERIES_DIR` | séries do rig e manifest | obrigatório no serviço de rig |
| `PNAAT_MODELOS` | pesos, runs e datasets de treino | usado pelos alvos `treino-*` e `pacote` |
| pacote detector | inferência YOLO | `make smoke-detector PACOTE=...` ou `orquestracao.py --pacote-modelo` |
| export do Label Studio | criação do dataset | consumido por `monta_v1_detector.py` |

Esses valores são dados do ambiente de instalação. O repositório guarda o código, o contrato, o
índice (`models/INDEX.csv`) e as amostras de método; peso e acervo bruto ficam fora por política, e
os pacotes de modelo do entregável estão publicados em https://huggingface.co/Nerton/pnaat-modelos.

## 9. Limites de ambiente

- Sem o pacote YOLO, a API, o registro e o site continuam funcionando; itens sem medida ficam
  `inconclusivo` na conformidade.
- Sem as câmeras e o sensor, `test-rig` e `trigger-simular` provam as rotas e a lógica sem hardware;
  validação física (níveis elétricos, debounce, cooldown) é trabalho de bancada, não ausência de
  código.

## 10. Docker

A composição em `docker/` empacota os três serviços em uma imagem única (base `python:3.11-slim`,
pacote `src-production[dev,leitura,serial,inferencia]` + repositório inteiro). Build a partir da
raiz do repositório (contexto `..`); o `.dockerignore` da raiz exclui `.venv`, `dataset`, `models`
e `.git` da imagem.

```bash
docker compose -f docker/docker-compose.yml build   # imagem tcc-pnaat:local (torch/ultralytics: build pesado)
export PNAAT_API_TOKEN='troque-este-token'
docker compose -f docker/docker-compose.yml up -d
curl -H 'Authorization: Bearer troque-este-token' http://127.0.0.1:8080/api/health
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f api
```

Serviços:

| Serviço | Comando no container | Porta | Exigência |
|---|---|---|---|
| `api` | `python src-production/api.py --db /data/hub.db --porta 8080 --host 0.0.0.0` | 8080 | nenhuma: sobe sem hardware (núcleo) |
| `rig` | `python src-production/rig_service/app.py --porta 8090` | 8090 | `PNAAT_SERIES_DIR`; câmeras opcionais |
| `ponte` | `python src-production/firmware/esp32cam-test/esp32cam_site.py --porta 8094 --serial /dev/ttyUSB0 --serial-trigger /dev/ttyUSB1` | 8094 | devices `/dev/ttyUSB*` reais |

Variáveis de instalação (compose):

| Variável | Serviço | Padrão | Uso |
|---|---|---|---|
| `PNAAT_SERIES_DIR_HOST` | rig | `./series` (cria `docker/series/`) | bind do diretório de séries do host em `/series` |
| `PONTE_SERIAL_CAM` | ponte | `/dev/ttyUSB0` | device da ESP32-CAM |
| `PONTE_SERIAL_TRIGGER` | ponte | `/dev/ttyUSB1` | device do trigger-node |
| `PNAAT_API_TOKEN` | api | obrigatório, sem padrão | Bearer token; a API recusa bind fora do loopback sem token (api.py:1373) |

O `hub.db` vive no volume nomeado `hub-db` (montado em `/data`, pré-criado com o dono do usuário
não-root `app`, uid 1000, igual ao uid do nerton no host). Healthchecks por `urllib` (sem curl na
imagem): `api` → `/api/health`, `rig` → `/estado`, `ponte` → `/status`.

Limites: `ponte` e `rig` exigem devices reais (seriais das ESPs e câmeras). Sem eles os serviços
sobem, mas ficam degradados (a ponte serve `/status` com serial fechada). Sem hardware, só o `api`
é útil; para validar a lógica inteira sem placa use os alvos da seção 7.

## 11. Flash das duas ESPs

Comandos prontos (rodando da raiz do repositório):

```bash
# ESP32-CAM (nó de visão): exporte o ESP-IDF antes (source $IDF_PATH/export.sh)
make -C src-production/firmware flash-cam PORTA_CAM=/dev/serial/by-id/<ESP32-CAM>
#   equivalente: cd src-production/firmware/esp32cam-test &&
#     idf.py set-target esp32 && idf.py build && idf.py -p "$PORTA_CAM" flash monitor

# ESP32 (nó de trigger, MicroPython): usa o .venv da raiz e o esp_tool.py
make -C src-production/firmware flash-trigger PORTA_TRIGGER=/dev/serial/by-id/<ESP32-trigger>
#   equivalente: cd src-production/firmware &&
#     ../../.venv/bin/python trigger-node/host/esp_tool.py --porta "$PORTA_TRIGGER" \
#     upload trigger-node/esp/main.py main.py
```

Prefira `/dev/serial/by-id/...` (estável entre reboots) ao `/dev/ttyUSBn`. Exemplos:
`/dev/serial/by-id/usb-Silicon_Labs_CP210x_USB_to_UART_Bridge_<id>` na ESP32-CAM e
`/dev/serial/by-id/usb-1a86_USB_Serial_<id>` no ESP32 do trigger. Antes de gravar, identifique
cada placa (`ls -l /dev/serial/by-id/`); trocar as duas portas grava o firmware no lugar errado.

Confirmação no fio após o flash: a ESP32-CAM imprime `BOOT_TEST firmware=esp32cam_test
sensor_gpio=13 active=LOW`; o trigger imprime `EV READY pin=27 out=26` seguido de `EV PING`
a cada 2 s.

Pinos confirmados na bancada (código `src-production/firmware/trigger-node/esp/main.py`):
`PRESENCE_PIN = 27` (linha 19, sinal do E18-D80NK, entrada com pull-up, active-low) e
`CAPTURE_OUT_PIN = 26` (linha 24, saída "capturando").
