# Esquemático do trigger (ESP32-S3 + sensor)

O projeto Wokwi original está na raiz em **`ESP32S3-Trigger.zip`**, contribuição de Paulo Victor
(commit `9fefd73`). Ele é uma referência histórica de protoboard, não um layout fabricável nem a
fonte normativa da ligação: usa um PIR genérico e seu `diagram.json` não materializa a ligação ao
GPIO27 adotado pelo firmware. O esquemático de interligação atualizado é
`docs/diagramas/interligacao-eletrica.mmd`; a pinagem normativa e o procedimento de medição estão em
`docs/hardware.md`, seção 2.

## O que o zip contém

| Arquivo | Papel |
|---|---|
| `wokwi-project.txt` | metadados do projeto Wokwi (id `475343904586369025`) |
| `sketch.ino` | esqueleto Arduino do ESP32-S3 (exemplo de inicialização) |
| `diagram.json` | o circuito: ESP32-S3 DevKitC-1, protoboard, divisor e sensor |

Reproduzir online: https://wokwi.com/projects/475343904586369025 (ou importar o zip em
`https://wokwi.com/projects/new/esp32-s3`).

## Ligações do diagrama

| Elemento | Ligação |
|---|---|
| ESP32-S3 DevKitC-1 | alimentação 3V3 e GND à protoboard |
| Sensor genérico (PIR simula o trigger) | VCC em 5V, GND comum, saída `OUT` no divisor |
| Resistor R1 de 2,2 kΩ | entre a saída do sensor e o GPIO (redução de nível) |
| Resistor R2 de 3,3 kΩ | do GPIO para GND (pull de referência) |
| GPIO | o arquivo histórico não fecha a ligação ao GPIO de produção; **GPIO27** é o pino do firmware |
| Serial | TX/RX no monitor serial, 115200 |

No produto, o sensor real é o E18-D80NK (NPN active-low, 5 V). R1/R2 só deve ser usado se a medição
do sinal livre indicar tensão acima de 3,3 V; para saída open-collector pura, usa-se GPIO27
diretamente com pull-up para 3,3 V.

## Relação com o firmware

O firmware MicroPython do nó de trigger (`src-production/firmware/trigger-node/esp/main.py`)
implementa a leitura do E18-D80NK com `PRESENCE_PIN = 27` e `CAPTURE_OUT_PIN = 26`, debounce de
20 ms, arming de 500 ms e guarda anti-duplicação de 500 ms. O esquemático documenta a montagem
física que esse firmware espera; a medição elétrica final (níveis reais de saída, divisor) é
validação de bancada pendente.

## Status

- Esquemático de referência: simula o trigger com sensor genérico (não é o E18 real no circuito).
- O firmware correspondente está versionado e testado (5 testes da lógica pura).
- Validação elétrica com o sensor físico real: pendência de bancada (ver `docs/hardware.md`).
