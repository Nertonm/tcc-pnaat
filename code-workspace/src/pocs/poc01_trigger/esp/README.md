# PoC-01 — Trigger de presença (E18-D80NK) no ESP32

## Objetivo

Validar que a detecção de presença abre uma janela de captura que cobre o mesmo
item em mais de uma vista (PoC-01). Foco: visibilidade e rastreabilidade; sem
atuação física e sem controle da esteira.

## Sensor

- **E18-D80NK**: sensor IR difuso (emissor + receptor), saída digital NPN NO.
- Lógica da saída: **LOW = objeto dentro do alcance** (active low); HIGH fora.
- Tensão de alimentação do sensor: VCC 5V; a saída segue esse nível, então NÃO
  ligue o sinal direto em pino de 3.3V sem divificar (divisor de tensão ou módulo
  de lógica/level shifter).

## Fiação (sensor → ESP32)

| Sensor E18-D80NK | ESP32                           |
|------------------|---------------------------------|
| Marrom (VCC)     | fonte 5V (mesma referência GND) |
| Azul (GND)       | GND                             |
| Preto (Sinal)    | GPIO (com divisor/level shifter) |

Pinos no código: `PRESENCE_PIN` (entrada, pull-up) e `CAPTURE_OUT_PIN` (GPIO
opcional de saída, usado como sinal de "capturando" para LED/release em teste).

## Como funciona (lógica)

1. Lê o sinal do sensor a cada `DEBOUNCE_MS`.
2. Converte nível em presença: `present = (level == 0)` (active low).
3. **Debounce**: só considera presença estável depois de `STABLE_READS` leituras
   consecutivas de presença; um pulso isolado (ruído/reflexo) não abre a janela.
4. **Janela de captura**: ao estabilizar, abre a janela com as vistas definidas
   (`VIEWS`) por `WINDOW_MS`, e aciona a saída `CAPTURE_OUT_PIN`.
5. **Fechamento**: após `MISS_READS` leituras estáveis de ausência, fecha a janela
   e volta a aguardar uma nova borda de subida.

Relação com o código de desktop: `src/pocs/poc01_trigger/presence.py` é a lógica
pura (testada por pytest, agnóstica de hardware). `esp/main.py` é a mesma lógica
sem dependência de `dataclasses`, rodando em MicroPython no ESP32.

## Testar no ESP32 (hardware)

1. Grave MicroPython no ESP32.
2. Copie `esp/main.py` como `main.py` no dispositivo (Thonny, `ampy` ou `mpremote`).
3. Ajuste `PRESENCE_PIN`/pinos se necessário.
4. Suba com o monitor serial. Aproxime um objeto da frente do sensor: deve sair
   `CAPTURE_WINDOW_OPEN views=topo,lateral1,lateral2`; afaste até sair
   `CAPTURE_WINDOW_CLOSE`.
5. O LED/relé em `CAPTURE_OUT_PIN` liga durante a janela.

## Testar em desktop (CI, sem hardware)

```
cd code-workspace
make test        # inclui tests/test_trigger.py
```

O teste cobre: abertura após debounce, pulso isolado não abre e fechamento após
ausência estável, além da conversão `present_from_sensor` (LOW = presente).

## Critério de passagem (da Entrega 1)

A `PoC-01` passa se o evento de presença abre a janela para mais de uma vista por
item, sem duplicidade, com identidade e timestamps associados.