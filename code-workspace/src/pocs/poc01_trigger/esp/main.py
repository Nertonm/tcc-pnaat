"""PoC-01 no ESP32: trigger de presenca com E18-D80NK + janela multi-view.

E18-D80NK: IR difuso, saida digital NPN NO. LOW = objeto dentro do alcance.
Liga: marrom = VCC (5V), azul = GND, preto = sinal (nao usa 3.3V direto sem
divisor de nivel/logic level, pois a saida do sensor segue o VCC de 5V).

Teste em serial: flash este arquivo como main.py no ESP32 com MicroPython e
acompanhe a saída (CAPTURE_WINDOW_OPEN / CAPTURE_WINDOW_CLOSE) enquanto
aproxima/afasta o objeto da frente do sensor.
"""
from machine import Pin
import time

# --- configuracao ---
PRESENCE_PIN = 12          # GPIO do sinal do E18-D80NK
CAPTURE_OUT_PIN = 16       # GPIO opcional: sinal de "capturando" (led/relay)
DEBOUNCE_MS = 20           # intervalo entre leituras (ms)
STABLE_READS = 5           # leituras estaveis de presenca para abrir janela
MISS_READS = 5             # leituras estaveis de ausencia para fechar janela
WINDOW_MS = 50             # duracao da janela de captura multi-view (ms)
VIEWS = ("topo", "lateral1", "lateral2")

pin = Pin(PRESENCE_PIN, Pin.IN, Pin.PULL_UP)
out = Pin(CAPTURE_OUT_PIN, Pin.OUT, value=0)


def read_present():
    # E18-D80NK: nivel baixo = objeto detectado (active low)
    return pin.value() == 0


def setup_logging():
    print("POC01_READY pin=%d debounce_ms=%d stable=%d miss=%d window_ms=%d"
          % (PRESENCE_PIN, DEBOUNCE_MS, STABLE_READS, MISS_READS, WINDOW_MS))


def main():
    hits = 0
    misses = 0
    window_open = False

    while True:
        if read_present():
            hits += 1
            misses = 0
            if not window_open and hits >= STABLE_READS:
                window_open = True
                hits = 0
                print("CAPTURE_WINDOW_OPEN views=" + ",".join(VIEWS))
                out.value(1)
                time.sleep_ms(WINDOW_MS)
                out.value(0)
                time.sleep_ms(WINDOW_MS)  # guarda entre janelas
        else:
            misses += 1
            hits = 0
            if window_open and misses >= MISS_READS:
                window_open = False
                misses = 0
                print("CAPTURE_WINDOW_CLOSE")

        time.sleep_ms(DEBOUNCE_MS)


if __name__ == "__main__":
    setup_logging()
    main()