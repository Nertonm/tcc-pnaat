"""Monitor cru: imprime somente mudancas no nivel do GPIO27 do ESP32.

Roda no ESP via esp_tool.py; nao aplica debounce nem interpreta LOW/HIGH.
"""
from machine import Pin
import time

PIN = 27
entrada = Pin(PIN, Pin.IN, Pin.PULL_UP)
ultimo = entrada.value()
print("GPIO_CHANGE_START pin=%d nivel=%d" % (PIN, ultimo))
while True:
    nivel = entrada.value()
    if nivel != ultimo:
        print("GPIO_CHANGE pin=%d nivel=%d" % (PIN, nivel))
        ultimo = nivel
    time.sleep_ms(10)
