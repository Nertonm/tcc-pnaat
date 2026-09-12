"""Monitor cru de uma entrada GPIO no ESP32 (MicroPython).

Uso no host:
  python scripts/esp_tool.py upload scripts/poc01_gpio_monitor.py gpio_monitor.py
  python scripts/esp_tool.py run gpio_monitor.py --segundos 30

Nao aplica debounce nem interpreta LOW/HIGH: mostra o nivel eletrico lido diretamente.
"""
from machine import Pin
import sys
import time

PIN = 27
if len(sys.argv) > 1:
    try:
        PIN = int(sys.argv[1])
    except ValueError:
        pass

entrada = Pin(PIN, Pin.IN, Pin.PULL_UP)
print("GPIO_RAW_START pin=%d pullup=1" % PIN)
ultimo = None
inicio = time.ticks_ms()
while True:
    agora = time.ticks_ms()
    nivel = entrada.value()
    if nivel != ultimo:
        print("GPIO_RAW_CHANGE pin=%d nivel=%d t_ms=%d" %
              (PIN, nivel, time.ticks_diff(agora, inicio)))
        ultimo = nivel
    else:
        print("GPIO_RAW pin=%d nivel=%d t_ms=%d" %
              (PIN, nivel, time.ticks_diff(agora, inicio)))
    time.sleep_ms(250)
