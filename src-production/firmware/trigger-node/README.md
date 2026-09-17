# Nó de trigger: E18-D80NK + ESP32 (MicroPython)

Nó de presença portado do canônico para o produto. O sensor IR difuso E18-D80NK detecta o item e o
firmware abre a janela de captura multi-view, sem duplicar e sem janela espúria.

## Firmware no ESP32

- `esp/main.py` — MicroPython: leitura do sensor com debounce, arming somente em repouso, guarda
  anti-duplicação, log `EV ...` e CSV no board.
- Pinos (fiação confirmada na bancada): `PRESENCE_PIN = 27` (pull-up, active low), `CAPTURE_OUT_PIN = 26`.
- Documento do sensor: `esp/README.md` (fiação bege=+5V, preto=sinal, azul=GND; nivel 5V exige
  divisor ou level shifter antes de pino 3.3V).
- Gravação no board: `host/esp_tool.py upload esp/main.py main.py` (raw REPL, com sha256 no board).

## Lógica pura e simulador

- `presence.py` — mesma máquina de estados, sem hardware, testada por pytest.
- `host/simular_trigger.py --caso todos` — fluxo sem hardware, mesmos eventos do firmware.

## Lane de host (porta serial)

| Script | Papel |
|---|---|
| `host/poc01_supervisor.py` | dono único da porta serial; republica em `~/poc01/stream.log`; solta com `~/poc01/PAUSA` |
| `host/poc01_escopo.py` | escopo ao vivo do bit e taxa de bordas |
| `host/poc01_teste.py` | harness com N passagens e veredito PASS/FAIL |
| `host/poc01_watch.py` | visualizador passivo do stream |
| `host/esp_tool.py` | upload/pull/rm/run no board via raw REPL |

## Verificação

```bash
make -C src-production test-trigger       # pytest da lógica pura
make -C src-production trigger-simular    # simulador sem hardware
```
