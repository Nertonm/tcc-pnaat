# ESP32-CAM: draft de integração com o Pi

Este diretório contém o firmware de bancada preservado como referência para a integração da
visão embarcada do TCC. Ele não é um release de produção e não deve ser instalado novamente
sem confirmar o hardware, a interface elétrica do trigger e o contrato com o Pi.

## Objetivo da integração

A ESP32-CAM deve cumprir somente estas responsabilidades:

1. observar o sensor de presença/trigger;
2. registrar o instante do disparo;
3. acordar a câmera e capturar um JPEG sob demanda;
4. entregar o JPEG e os metadados ao Pi por uma interface confiável;
5. voltar ao estado de baixo consumo após a captura.

O Pi é o dono do pipeline de visão, persistência, decisão e reação operacional. A ESP não deve
classificar defeitos nem decidir aprovação/reprovação.

## Fluxo desejado

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

## Saída atual do draft

A referência de bancada usa UART a 921600 baud e linhas delimitadas. Um frame válido tem este
formato:

```text
FRAME_BEGIN v=1 encoding=base64 source=e18_d80nk event=17 trigger_us=123456789 len=8451 crc32=32a1bc09 wake_us=98135 warmup_us=30000 capture_us=27974
FRAME_DATA event=17 seq=0 data=<base64>
FRAME_DATA event=17 seq=1 data=<base64>
...
FRAME_END event=17 tx_us=195071 total_us=352323
```

Detalhes do contrato atual:

- `v`: versão do protocolo;
- `encoding`: codificação do payload (`base64` no draft);
- `source`: `e18_d80nk` para trigger físico; `usb_command` somente para ensaio;
- `event`: identificador monotônico do evento na ESP;
- `trigger_us`: timestamp monotônico capturado na origem;
- `len`: tamanho JPEG após decodificação;
- `crc32`: CRC-32 do JPEG bruto, em hexadecimal minúsculo;
- `wake_us`, `warmup_us`, `capture_us`: métricas de captura;
- `seq`: sequência começando em zero, sem lacunas ou duplicatas;
- `FRAME_END`: encerra o frame e informa transmissão e tempo total;
- JPEG obrigatório: marcador inicial `FF D8` e final `FF D9`.

O draft divide o JPEG em blocos pequenos e codifica cada bloco em base64 para simplificar a
inspeção serial. Isso não é a forma final preferida: o contrato de produção deve avaliar payload
binário enquadrado para remover o overhead de aproximadamente 33% e reduzir a latência.

## Contrato de produção a definir

Antes de integrar no pipeline, substituir ou congelar explicitamente estes placeholders:

```text
PROTOCOL_VERSION = <versão escolhida>
TRANSPORT = <UART_USB | outra interface validada>
TRIGGER_GPIO = <GPIO confirmado no esquemático e na placa>
TRIGGER_ELECTRICAL_MODE = <nível, pull-up/pull-down, open-collector ou interface>
FRAME_ENCODING = <binário preferencialmente; base64 apenas se mantido por decisão>
FRAME_MAX_BYTES = <limite validado no Pi e na ESP>
FRAME_TIMEOUT_MS = <timeout medido com margem>
RETRY_POLICY = <retry, descarte ou reenvio solicitado pelo Pi>
PERSISTENCE_POLICY = <quando o Pi grava o JPEG e seus metadados>
```

O contrato final deve ter cabeçalho com magic, versão, tipo de mensagem, `event_id`, timestamp,
tamanho, sequência e CRC. O Pi deve poder distinguir pelo menos `TRIGGER`, `FRAME_BEGIN`,
`FRAME_DATA`, `FRAME_END`, `ACK`, `NACK` e `ERROR`.

## Como o Pi deve receber

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
7. decodificar base64 com validação estrita enquanto o draft existir;
8. verificar tamanho real, `FF D8`, `FF D9` e CRC-32 antes de publicar;
9. publicar o frame somente depois de todas as validações;
10. preservar `event_id`, origem, timestamp, métricas e motivo de falha;
11. nunca substituir silenciosamente um frame válido por um frame parcial ou antigo;
12. responder `ACK` apenas após validação e `NACK` com motivo fechado quando rejeitar.

O estado `latest frame` é uma conveniência de visualização, não o registro canônico. O Pi deve
persistir ou encaminhar o evento de forma idempotente, usando `event_id` e a identidade do rig.

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
- origem `usb_command`: aceitar somente em modo de ensaio explicitamente habilitado;
- timestamp fora da janela: preservar a imagem, mas marcar `timestamp_divergente`;
- qualidade insuficiente: não enviar para decisão como se fosse evidência adequada;
- falha do modelo ou do registro: manter o evento e retornar `inconclusivo`.

## Trigger e pinos

O draft histórico usa E18 em GPIO13, active-low, com interrupção na borda de descida. Isso é
apenas uma hipótese de integração até confirmar a placa e a interface elétrica.

Não ligar diretamente uma saída de sensor alimentada em tensão superior ao limite do ESP32. Antes
do hardware real, confirmar se a saída é open-collector/NPN, usar a referência de 3,3 V adequada,
GND comum e proteção de nível quando necessário.

GPIO4 foi usado somente em um ensaio de bancada e não faz parte do trigger de produção. Não
reativar gerador de sinal ou LED de teste na versão integrada.

## Critérios de aceite da integração

- [ ] pinout e níveis elétricos medidos no hardware real;
- [ ] trigger físico produz exatamente um evento, com debounce e cooldown medidos;
- [ ] nenhum evento é perdido silenciosamente quando a captura está ocupada;
- [ ] JPEG válido chega ao Pi com tamanho, sequência e CRC conferidos;
- [ ] frame parcial nunca chega ao classificador;
- [ ] timeout, duplicata, CRC inválido e origem não autorizada são observáveis;
- [ ] o Pi registra evento sem captura e captura sem decisão;
- [ ] item duplicado é idempotente;
- [ ] corrente e temperatura em idle, wake e captura foram medidas;
- [ ] canário real passa antes de criar deployment persistente.

## Referências do scaffold

- `esp32cam-test/main/main.c`: implementação de bancada da câmera, IRQ, fila e transporte;
- `esp32cam-test/usb_stream_bridge.py`: bridge experimental serial para visualização local.

Esses arquivos são material de trabalho. O código só se torna integração quando os placeholders
acima forem preenchidos, o receptor do Pi for conectado ao pipeline e os critérios de aceite forem
verificados no hardware real.
