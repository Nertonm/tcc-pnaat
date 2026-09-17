# Operação: gatilho, captura, inferência e registro

Este guia descreve o que está implementado na árvore atual. Ele descreve a ligação entre os serviços
presentes no repositório sem inventar integração.

## 1. As três rotas existentes

O sistema tem serviços conectados, mas cada fronteira usa contrato próprio. A ponte serial recebe o
trigger e comanda a câmera; o gateway HTTP conversa com rig e ponte; a ingestão e a inferência
persistem no SQLite. As três rotas abaixo explicam as entradas e contratos:

```text
A. Trigger -> ponte -> visão
   trigger-node (E18, GPIO27) -> esp32cam_site.py (ponte)
   -> CMD_TRIG -> ESP32-CAM (debounce 50 ms / cooldown 250 ms)
   -> uma foto -> frame UART com CRC

B. Inferência por diretório
   <capturas>/<item>/[lateral1.jpg,lateral2.jpg,topo.jpg]
   -> contrato do pacote -> YOLO -> decisão -> SQLite

C. Ingestão de série manifestada
   <serie>/manifest.json + fotos + mapa câmera->vista
   -> cópia de evidência -> artefato .npz legado -> decisão -> SQLite
```

A rota A inclui o nó de trigger e o receptor: `src-production/firmware/trigger-node/esp/main.py` lê o E18-D80NK
(GPIO27, active low), aplica debounce e abertura da janela; `esp32cam_site.py` é dona das portas
seriais, decodifica frames com `transport_bin.py`, recebe o trigger e envia `CMD_TRIG` à câmera. O
serviço de rig (`rig_service/app.py`) captura as três câmeras, grava a série com manifest e expõe as
rotas que `api.py` encaminha por `PNAAT_RIG` e `PNAAT_PONTE`. O código da cadeia está no repositório;
endereços, portas e diretório de séries são configuração da instalação.

## 2. Rota A: trigger e firmware

A rota tem dois nós de firmware, cada um no seu diretório. O código do trigger com o sensor está em
`src-production/firmware/trigger-node/`, e o nó de visão em `src-production/firmware/esp32cam-test/`.
A ponte serial (`esp32cam_site.py`) é quem religa o evento de um ao comando do outro.

### 2.1 Nó de trigger (E18-D80NK + ESP32, MicroPython)

Código: `src-production/firmware/trigger-node/esp/main.py` (firmware) e `presence.py` (máquina de estados pura,
testada). Pinos confirmados na bancada: `PRESENCE_PIN = 27` (active-low, pull-up) e
`CAPTURE_OUT_PIN = 26`. O esquemático de referência está em `ESP32S3-Trigger.zip` (Wokwi).

O nó lê o E18-D80NK a cada `DEBOUNCE_MS = 20 ms`, só arma após repouso contínuo de `ARM_MS = 500 ms`
(elimina a janela espúria do boot), abre a janela após `STABLE_READS = 5` leituras de presença,
fecha após `MISS_READS` de ausência e mantém guarda anti-duplicação de `GUARD_MS = 500 ms`. Cada
transição sai como `EV <evento> campo=valor`, também gravado em CSV no board; heartbeat do nível em
`PING_MS`. Gravação e monitor no ESP32:

```bash
cd src-production/firmware/trigger-node/host
.venv/bin/python esp_tool.py upload ../esp/main.py main.py
.venv/bin/python esp_tool.py run main.py --segundos 30
```

### 2.2 Nó de visão (ESP32-CAM, ESP-IDF)

Código: `src-production/firmware/esp32cam-test/main/main.c`. A câmera recebe um comando de captura (da ponte, via
`CMD_TRIG`, ou direto do sensor no `SENSOR_GPIO = GPIO_NUM_13`, fonte `TRIGGER_SOURCE_E18`), aplica
`DEBOUNCE_US = 50 ms` e `COOLDOWN_US = 250 ms`, acorda a câmera, captura uma imagem e publica um frame
com `event_id`, timestamp e CRC. Entre fotos, a câmera fica em standby. Onde existir a placa de
trigger dedicada, o E18 fica no nó MicroPython (GPIO27) e a ponte encaminha o evento em `CMD_TRIG`.

O transporte é UART, em texto ou binário. O formato binário usa SOF, cabeçalho, CRC16 e CRC32 do
payload. `esp32cam_site.py` (ponte) recebe o frame, atualiza o estado do enlace e disponibiliza as
operações do rig por HTTP. A suíte do firmware prova a publicação de uma foto por trigger, o descarte
de frame parcial e a compatibilidade de CRC. A ingestão de série é uma etapa distinta: recebe a série
já materializada pelo serviço de rig.

Para compilar e gravar o nó de visão:

```bash
cd src-production/firmware/esp32cam-test
idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

O uso de `/dev/ttyUSB0` é só exemplo. Na bancada, selecione a porta real por identificador estável.
A ligação elétrica do E18-D80NK com o nó de trigger está documentada em `docs/hardware.md` e no
esquemático Wokwi; consulte antes de conectar o sensor ao GPIO.

## 3. Rota B: inferência YOLO sobre uma captura materializada

Esta é a rota de operação do pacote detector. Ela exige que o serviço de captura já tenha gravado as
três imagens de um item no layout abaixo:

```text
<CAPTURA>/
  <ITEM>/
    lateral1.jpg
    lateral2.jpg
    topo.jpg
```

`CAPTURA` é a pasta pai de `<ITEM>`, não a pasta do item. A orquestração lê o `mtime` das fotos,
confere janela temporal e alinhamento declarado. Sem `--janela`, nenhuma vista é utilizável. Arquivo
duplicado para a mesma vista, ou bytes repetidos entre vistas, também excluem a vista da decisão.

O pacote precisa conter peso, contrato de pré-processamento, metadados, manifesto e `SHA256SUMS`.
Antes de carregar YOLO, `pacote_detector.py` confere o inventário e `preparo_detector.py` confere o
fingerprint, a orientação, a ROI, as classes, `imgsz` e os limiares. O recorte usado no runtime vem do
contrato, não de argumento livre.

```bash
make -C src-production smoke-detector   PACOTE=/caminho/pacote-detector   CAPTURA=/caminho/capturas   ITEM=ITM-001   DB=/caminho/hub.db   JANELA=0.4   ALINHAMENTO=declarado   EQUIPAMENTO=rig   LOCALIZACAO=bancada
```

Esse comando escreve no SQLite. Use um banco descartável ao aprender ou testar. O pacote lateral decide
apenas o domínio `tampa` nas vistas laterais; para `corpo`, o classificador retorna sem medida. O
detector de topo existe no acervo (`*-topo-detector-roi`) e atua como check dimensional. A conformidade
mantém o item como `inconclusivo` quando falta medida exigida; ela não transforma falta de evidência em
aprovação. Um defeito de tampa pode, contudo, reprovar o item.

## 4. Rota C: ingestão de série do rig

`ingerir_serie.py` recebe uma série já pronta com `manifest.json`. O manifest identifica as fotos e o
mapa `camera -> vista` associa cada câmera a `lateral1`, `lateral2` ou `topo`. O mapa é obrigatório e
pertence à instalação, porque trocar uma lateral altera a decisão.

```bash
.venv/bin/python src-production/ingerir_serie.py   --serie /caminho/serie   --lote L1   --db /caminho/hub.db   --roi 0.0 0.0 1.0 1.0   --mapa csi=topo,usb=lateral2,espcam=lateral1   --janela-ms 2000   --alinhamento declarado
```

A ingestão copia evidências, reserva `item_id`, executa a decisão e registra a transação. Se existir um
evento de gatilho já persistido, `--gatilho-id` cria o vínculo depois da ingestão. O vínculo é único:
um gatilho não pode apontar para dois itens.

Esta rota usa o artefato `.npz` legado indicado por `--modelo`; ela não aceita `--pacote-modelo` e não
carrega YOLO. Não a apresente como equivalente ao comando `smoke-detector`.

## 5. Registro de gatilho e API

Há dois meios de gravar um `evento_gatilho`: `fonte_gatilho.py`, que valida um CSV inteiro antes de
gravar, e `POST /api/gatilho`, que valida timestamp, estado e tipos. Ambos só persistem o evento. Eles
não acionam captura, ingestão ou inferência.

A API e o site podem ser usados com um banco local:

```bash
.venv/bin/python src-production/api.py --db hub.db --porta 8080 --host 127.0.0.1
```

Bind fora do loopback requer token. Endereços do serviço de câmera, ponte serial e adaptador de modelo
são configurados por ambiente; eles não fazem parte do clone nem devem ser publicados na documentação.

## 6. Decisão e banco

`orquestracao.executar()` prepara as vistas decisórias, chama o classificador por domínio e passa as
medidas para `decisao.py` e `conformidade.py`. A regra é fail-closed:

- sem evidência utilizável, o resultado é `inconclusivo`;
- `normal` não apaga um defeito mais confiante;
- qualquer defeito confirmado reprova;
- a vista de topo não aprova um item;
- `Registro.registrar()` é idempotente por `item_id` e recusa evidência divergente para o mesmo item.

O registro SQLite guarda item, inspeções por vista, gatilhos e evidências na mesma transação. Falha ao
gravar evidência causa rollback; o dashboard lê esse banco, não uma cópia de estado em memória.

## 7. Verificar o que foi instalado

A suíte do produto cobre esses serviços no nível de rota e lógica:

```bash
make -C src-production verificar
make -C src-production lint
make -C src-production test-trigger
make -C src-production trigger-simular
make -C src-production test-rig
```

O manual completo com pré-requisitos, firmware, serviços na ordem e ciclo de ponta a ponta está em
`docs/replicacao-ponta-a-ponta.md`.

### Sem hardware: banco local e API

```bash
make -C src-production verificar
make -C src-production lint
```

Sem câmera, sem peso e sem dado externo, a API ainda sobe contra um banco local. Em banco novo, o
`/api/health` cria o schema; o site serve os dados que estiverem no banco.

```bash
.venv/bin/python src-production/api.py --db hub.db --porta 8080 --host 127.0.0.1
```

Não existe alvo de demonstração nesta entrega. Os números de itens e estados só aparecem depois de uma
ingestão (rota C) ou de uma inferência por diretório (rota B) gravadas no mesmo banco.

## 8. Fonte de cada afirmação

| Assunto | Código ou documento |
|---|---|
| Firmware, trigger e frame serial | `src-production/firmware/esp32cam-test/` e `docs/hardware.md` |
| Captura por diretório e janela | `src-production/captura.py`, `src-production/orquestracao.py` |
| Série manifestada | `src-production/ingerir_serie.py`, `src-production/mapeamento_rig.py` |
| Pacote, contrato e YOLO | `src-production/pacote_detector.py`, `preparo_detector.py`, `classificador_yolo.py` |
| Decisão e persistência | `src-production/decisao.py`, `conformidade.py`, `registro.py` |
| Dataset e treino | `dataset/README.md`, `src-production/treino/README.md` |
| CAD e limites de fabricação | `cad-produto/README.md`, `docs/hardware.md` |
