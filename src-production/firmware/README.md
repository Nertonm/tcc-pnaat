# Firmware do nó de visão e do nó de trigger

O produto carrega dois nós de firmware, ambos com o código no repositório:

| Nó | Caminho | Papel |
|---|---|---|
| Visão (ESP32-CAM) | `esp32cam-test/` | uma foto por trigger, câmera em standby entre fotos, transporte binário enquadrado; receptor `esp32cam_site.py` é dono único da porta serial |
| Trigger (ESP32 + E18-D80NK) | `trigger-node/` | sensor de presença com debounce, arming seguro e guarda anti-duplicação; MicroPython com lane de host |

A integração de ponta a ponta tem código nesta árvore: o sensor dispara o nó de trigger, a ponte
`esp32cam_site.py` recebe o enlace e comanda o nó de visão, e o gateway `api.py` conecta rig e ponte
ao registro. O que permanece configuração de instalação são os endereços (`PNAAT_RIG`, `PNAAT_PONTE`)
e a topologia das portas; não é código ausente.

## Objetivo do nó de visão

A ESP32-CAM deve cumprir somente estas responsabilidades:

1. observar o sensor de presença/trigger;
2. registrar o instante do disparo;
3. acordar a câmera e capturar um JPEG sob demanda;
4. entregar o JPEG e os metadados ao Pi por uma interface confiável;
5. voltar ao estado de baixo consumo após a captura.

O Pi é o dono do pipeline de visão, persistência, decisão e reação operacional. A ESP não deve
classificar defeitos nem decidir aprovação/reprovação.

## Fluxo

```text
sensor -> GPIO/IRQ -> fila FreeRTOS -> tarefa de captura
                                      |
                                      v
                              JPEG + metadados
                                      |
                                      v
                         UART/USB -> receptor no Pi
                                      |
                                      v
                 validação -> item capturado -> visão -> registro
```

A ISR deve ser mínima: timestamp, origem e envio para a fila com `xQueueSendFromISR`. Wake-up,
captura, codificação, transmissão e qualquer I/O ficam em tasks FreeRTOS. Um trigger não deve
executar lógica pesada dentro da ISR.

## Transporte implementado (v1)

Dois modos, alternáveis em runtime por `CMD_TRANSPORT TEXT|BIN`:

- `text`: linhas delimitadas com payload base64, no formato de texto legado;
- `bin`: enquadramento binário, com cabeçalho, payload e CRC por mensagem.

```text
SOF A5 5A | VER | TYPE | FLAGS | EVENT u16 | SEQ u32 | LEN u16 | CRC16(VER..LEN) | payload | CRC32(payload)
TYPE: 1=BEGIN 2=CHUNK 3=END 4=ACK 5=NACK        (tudo little-endian)
BEGIN: payload de 16 B (total_len u32, frame_crc32 u32, trigger_us i64)
CHUNK: payload de até 1024 B                    END: payload de 4 B (frame_crc32)
```

Logs ASCII convivem com as mensagens no mesmo fio: o receptor demuxa por enquadramento
(SOF + CRC16 do cabeçalho) e trata o resto como texto. Não há flag de modo no receptor.

Medido no fio, mesma placa e mesmas condições (frame de ~13 kB):

| modo | bytes na linha | fator sobre o JPEG | tempo na linha |
|---|---|---|---|
| texto base64 @ 921600 | 27.233 | 2,15x | 292 ms |
| binário @ 921600 | 14.921 | 1,13x | 191 ms |
| binário @ 1,5 Mbps | — | — | 145 ms |

Além do bloco binário, o firmware imprime `FRAME_INFO ... len= crc32=` em ASCII: o host recalcula
o CRC-32 do frame montado com `zlib` e compara. Duas implementações independentes concordando
separa erro de enlace de erro de implementação de CRC.

## Contrato congelado

```text
PROTOCOL_VERSION = 1
TRANSPORT = UART_USB (console e imagem no mesmo fio, demux por enquadramento)
TRIGGER_GPIO = 13 (E18-D80NK, active-low, borda de descida)
TRIGGER_ELECTRICAL_MODE = active-low, pull-up interno; níveis do sensor real ainda não medidos
FRAME_ENCODING = binário (texto mantido por compatibilidade)
FRAME_MAX_BYTES = 1024 B por chunk, 4096 B por mensagem, 4 MiB por frame no host
FRAME_TIMEOUT_MS = 25 s por foto no host (declarado no contrato; o enforcement de timeout ainda não está no receptor) (evento completo medido em ~1,4 s)
RETRY_POLICY = fail-closed: frame rejeitado não é publicado e o host tenta uma segunda captura
PERSISTENCE_POLICY = o host serve o último frame válido; o registro canônico é do pipeline do Pi
```

Estados observáveis no fio: `CAMERA_OFF boot=1` e `CAMERA_OFF motivo=fim_da_captura|falha_init|fim_do_teste`,
`STATUS camera=standby|ativa driver=0|1 transport=bin|text baud=`, `SENSOR_TEST pwdn=0|1 detect=`,
`FRAME_INFO`, `FRAME_END_BIN`.

## Energia da câmera

Entre fotos o firmware: desinicializa o driver, assere `PWDN` (standby do sensor), para o XCLK
(`ledc_stop` + pino em entrada com pull-down) e desliga a chave de carga quando ela existe.

Verificado funcionalmente: com `PWDN` alto o sensor **não responde** na detecção, e `STATUS`
reporta `camera=standby driver=0`. Atenção: isso é standby, não corte de 3V3; o módulo segue
alimentado. Corte real exige chave de carga no rail da câmera; o firmware já tem o caminho
pronto em `CAM_POWER_GPIO` (-1 = ausente nesta placa).

Comandos: `CMD_CAPTURE`, `CMD_STATUS`, `CMD_SENSOR` (teste A/B de energia), `CMD_TRANSPORT TEXT|BIN`,
`CMD_BAUD <n>`, `CMD_TEST_FALHA_INIT` (diagnóstico: força a próxima captura a falhar na init).

## Como o Pi recebe

O receptor do Pi deve ser uma única dona lógica da porta serial. Nenhuma thread HTTP deve escrever
diretamente na UART enquanto outra thread lê. Comandos devem entrar em uma fila de comandos, e a
thread responsável pela serial deve serializar leitura e escrita.

Máquina de estados mínima do receptor:

```text
IDLE
  -> HEADER_RECEIVED       ao receber FRAME_BEGIN válido
HEADER_RECEIVED
  -> RECEIVING              ao aceitar o primeiro chunk
  -> IDLE + erro            se header inválido ou timeout
RECEIVING
  -> COMPLETE               ao receber todos os chunks esperados e FRAME_END
  -> IDLE + erro            se seq faltar, duplicar, exceder limite ou timeout
COMPLETE
  -> VALIDATED              após tamanho, JPEG e CRC passarem
VALIDATED
  -> PUBLISHED              somente após disponibilizar uma cópia imutável ao pipeline do Pi
```

Regras obrigatórias no Pi:

1. ao receber `FRAME_BEGIN`, abandonar o frame parcialmente aberto anterior e registrar o motivo;
2. validar versão, origem permitida, `event_id`, tamanho máximo e campos numéricos;
3. aceitar chunks somente do `event_id` atual;
4. exigir sequência contígua, sem lacuna e sem duplicata;
5. aplicar timeout tanto entre chunks quanto para o frame inteiro;
6. limitar memória antes de alocar o payload anunciado;
7. decodificar base64 com validação estrita enquanto o modo texto existir;
8. verificar tamanho real, `FF D8`, `FF D9` e CRC-32 antes de publicar;
9. publicar o frame somente depois de todas as validações;
10. preservar `event_id`, origem, timestamp, métricas e motivo de falha;
11. nunca substituir silenciosamente um frame válido por um frame parcial ou antigo;
12. responder `ACK` apenas após validação e `NACK` com motivo fechado quando rejeitar (regra declarada; o receptor atual ainda não emite ACK/NACK, o descarte é pelo CRC/fechamento).

O estado `latest frame` é uma conveniência de visualização, não o registro canônico. O Pi deve
persistir ou encaminhar o evento de forma idempotente, usando `event_id` e a identidade do rig.

Receptor implementado: `esp32cam-test/transport_bin.py` (decoder + montador com os gates) e
`esp32cam-test/esp32cam_site.py` (dona única da porta, site de captura). Testes em
`esp32cam-test/tests/test_transport_bin.py`.

## Como o Pi deve reagir

Para `source=e18_d80nk` e frame validado:

1. registrar o evento de trigger, mesmo que a captura falhe;
2. associar o JPEG ao evento e gerar o `item_id` no lado do Pi;
3. verificar timestamp e janela temporal do rig;
4. validar legibilidade, resolução e enquadramento;
5. encaminhar a imagem para o pipeline de visão;
6. executar classificação por vista e fusão por domínio;
7. registrar decisão, confiança, evidências, hash do JPEG e métricas;
8. responder ao operador com `normal`, `defeito` ou `inconclusivo` conforme as regras do pipeline.

Reações fail-closed:

- trigger sem JPEG: registrar `inconclusivo` ou evento sem captura, nunca fingir normalidade;
- JPEG inválido/CRC incorreto: descartar como evidência, registrar `frame_invalido`;
- timeout: registrar `timeout_captura` com `event_id`;
- evento duplicado: não gerar segundo item; registrar duplicata;
- origem `usb_command`: aceitar somente em modo de bancada explicitamente habilitado;
- timestamp fora da janela: preservar a imagem, mas marcar `timestamp_divergente`;
- qualidade insuficiente: não enviar para decisão como se fosse evidência adequada;
- falha do modelo ou do registro: manter o evento e retornar `inconclusivo`.

## Trigger e pinos

O nó de visão (ESP32-CAM) usa o E18-D80NK no GPIO13 active-low, borda de descida, como comando de
captura interno. O nó de trigger dedicado (MicroPython) usa `PRESENCE_PIN = 27` (fiação confirmada
na bancada; o docstring sempre disse P27) e `CAPTURE_OUT_PIN = 26`, com divisor de nível na saída
5V do sensor antes do pino 3,3V.

O sensor E18-D80NK é saída digital aberta (NPN): LOW = objeto dentro do alcance. Alimentação 5V;
verifique a tensão real na saída antes de ligar direto ao GPIO. GND comum entre sensor, ESP32 e host
é obrigatório. GPIO4 foi usado apenas num experimento de bancada e não faz parte do trigger.

## Critérios de aceite da integração

Verificados nesta bancada:

- [x] `PWDN` confirmado funcionalmente: `PWDN` alto → sensor não responde (`SENSOR_TEST pwdn=1 detect=0`);
- [x] uma foto por trigger: 3 triggers → exatamente 3 fotos; nenhuma foto em 15 s de ociosidade;
- [x] JPEG válido com tamanho, sequência e CRC conferidos (CRC do firmware x `zlib` no host = ok);
- [x] frame parcial ou corrompido nunca é publicado (CRC por mensagem, CRC do frame, tamanho e
      marcadores `FF D8`/`FF D9`); lacuna de chunk bloqueia o frame e é registrada;
- [x] standby em todos os caminhos (fim de captura, falha de init e fim do teste de energia);
- [x] timeout, duplicata e CRC inválido observáveis no host (contadores e eventos).

Pendentes:

- [ ] níveis elétricos do sensor de presença real e trigger físico medido (hoje só comando de bancada);
- [ ] debounce (50 ms) e cooldown (250 ms) medidos com o E18-D80NK;
- [ ] origem não autorizada: o firmware aceita o comando de bancada sempre; falta gate de modo;
- [ ] corrente e temperatura em idle, wake e captura (não medidos; exige instrumentação);
- [ ] o Pi registrar evento sem captura e captura sem decisão (integração com o pipeline);
- [ ] idempotência de item duplicado no registro canônico;
- [ ] canário em deployment persistente (hoje roda em sessão `tmux`, não como serviço).

## Referências do scaffold

- `esp32cam-test/main/main.c`: firmware (IRQ na fila, uma foto por trigger, standby, transporte);
- `esp32cam-test/transport_bin.py`: contrato binário e receptor (decoder + montador com gates);
- `esp32cam-test/tests/test_transport_bin.py`: testes do transporte (oráculo diferencial e gates);
- `esp32cam-test/esp32cam_site.py`: site de captura; dona única da porta serial;
- `esp32cam-test/usb_stream_bridge.py`: bridge antiga de visualização local, superada pelo site;
- componente `esp32-camera` (v2.1.7): restaurado pelo gerenciador de componentes do ESP-IDF a partir
  de `idf_component.yml` + `dependencies.lock`; nao e versionado.

## Nó de trigger (Sensor E18-D80NK + ESP32 MicroPython)

Portado do canônico para o produto em `trigger-node/`: `esp/main.py` (firmware), `presence.py`
(lógica pura testada), `host/` (supervisor da porta serial, escopo, harness, watch, esp_tool e
simulador) e `tests/test_trigger.py`.

```bash
make -C src-production test-trigger       # lógica pura (5 testes)
make -C src-production trigger-simular    # simulador sem hardware, mesmos eventos do firmware
PYTHONPATH=src-production/firmware/trigger-node .venv/bin/python \
  src-production/firmware/trigger-node/host/poc01_teste.py --passagens 10 --espera 6 --separacao 3
```

Pinos confirmados na bancada no `esp/main.py`: `PRESENCE_PIN = 27`, `CAPTURE_OUT_PIN = 26`. A fiação
detalhada está em `trigger-node/esp/README.md`. A divergência entre a versão GPIO33 das cópias
antigas e a GPIO27 do canônico foi resolvida na bancada: fica registrada GPIO27.
