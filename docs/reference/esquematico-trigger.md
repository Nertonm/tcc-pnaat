# Esquemático do trigger (ESP32-S3 + sensor)

O esquemático do trigger está na raiz do repositório em **`ESP32S3-Trigger.zip`**, contribuição de
Paulo Victor (commit `9fefd73`). É um projeto do simulador Wokwi, não um layout de placa
fabricado: serve como referência da ligação do sensor ao ESP32 nos resistores e pinos corretos.

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
| GPIO | pino de exemplo `5` no esquemático; **GPIO27** é o especificado no projeto |
| Serial | TX/RX no monitor serial, 115200 |

No projeto, o sensor real é o E18-D80NK (NPN active-low, 5V); a saída do módulo pode ultrapassar
3,3V, então o divisor R1/R2 (2,2k/3,3k) condiciona o nível antes do GPIO. O comentário do commit
resume: resistores adequados para uma GPIO qualquer, tensão padrão 3,3V; no código do produto o
pino é o 27.

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
