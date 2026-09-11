"""PoC-01 no ESP32 v4: trigger com E18-D80NK: log legivel, armado seguro e guarda anti-duplicacao.

Correcoes vindas da bancada (v3):
  1. ARMADO SEGURO: apos o aquecimento, so arma quando a linha fica estavel em REPOUSO (nivel 1)
     por ARM_READS leituras. Isso elimina a janela espuria no boot (a linha nasce LOW por alguns ms).
  2. GUARDA ANTI-DUPLICACAO: depois de um CLOSE, nova deteccao so abre janela se passou GUARD_MS.
     Deteccao dentro da guarda e registrada como SUPPRESSED (prova que a duplicata foi bloqueada,
     em vez de simplesmente nao acontecer nada).
  3. LOG IDENTIFICAVEL: todas as linhas saem como `EV <evento> campo=valor ...` (nivel, n, tempos),
     tanto na serial quanto em /poc01_events.csv. O host interpreta esse formato.

Eletrica: bege = +5V, azul = GND, preto = sinal em P27 (PULL_UP). 0 = objeto, 1 = repouso.
Instalar como main.py faz o firmware iniciar sozinho a cada reset/boot.
"""
from machine import Pin, reset
import time

PRESENCE_PIN = 33
CAPTURE_OUT_PIN = 26
DEBOUNCE_MS = 20
STABLE_READS = 5          # leituras LOW para abrir
MISS_READS = 5            # leituras HIGH para fechar
WINDOW_MS = 50            # largura do pulso em CAPTURE_OUT
WARMUP_MS = 1000          # ignora o transitorio de boot
ARM_READS = 10            # leituras HIGH estaveis para armar (500 ms)
GUARD_MS = 500            # janela morta apos cada fechamento
LOG_PATH = "poc01_events.csv"

pin = Pin(PRESENCE_PIN, Pin.IN, Pin.PULL_UP)
out = Pin(CAPTURE_OUT_PIN, Pin.OUT, value=0)
_log = None
nivel_anterior = None


def log(evento, **campos):
    partes = " ".join("%s=%s" % (k, v) for k, v in campos.items())
    print("EV %s %s" % (evento, partes))
    if _log is not None:
        try:
            _log.write("%d,%s,%s\n" % (time.ticks_ms(), evento, partes))
            _log.flush()
        except Exception:
            pass


def abrir_log():
    global _log
    try:
        _log = open(LOG_PATH, "a")
    except Exception:
        _log = None


def main():
    global nivel_anterior
    abrir_log()
    log("READY", pin=PRESENCE_PIN, out=CAPTURE_OUT_PIN, debounce_ms=DEBOUNCE_MS,
        stable=STABLE_READS, miss=MISS_READS, guard_ms=GUARD_MS, warmup_ms=WARMUP_MS)

    # aquecimento: descarta o transitorio de boot
    t_fim = time.ticks_add(time.ticks_ms(), WARMUP_MS)
    while time.ticks_diff(t_fim, time.ticks_ms()) > 0:
        time.sleep_ms(DEBOUNCE_MS)
    log("WARMUP_DONE", nivel=pin.value())

    # arma SOMENTE quando a linha esta estavel em REPOUSO (nivel 1).
    # Sem timeout: enquanto houver algo na frente do sensor (ou a saida estiver presa em LOW),
    # o firmware avisa e NAO arma -- era isso que gerava a "janela espuria" no boot.
    iguais = 0
    proximo_aviso = time.ticks_add(time.ticks_ms(), 3000)
    while iguais < ARM_READS:
        if pin.value() == 1:
            iguais += 1
        else:
            iguais = 0
            if time.ticks_diff(proximo_aviso, time.ticks_ms()) <= 0:
                log("ARM_WAIT", nivel=pin.value(),
                    nota="linha em nivel de objeto: afaste o que estiver na frente do sensor")
                proximo_aviso = time.ticks_add(time.ticks_ms(), 5000)
        time.sleep_ms(DEBOUNCE_MS)
    log("ARMED", nivel=pin.value(), iguais_estaveis=iguais)

    hits = 0
    misses = 0
    aberta = False
    n = 0
    t_abertura = 0
    guarda_ate = 0
    suprimidas = 0

    while True:
        nivel = pin.value()
        if nivel != nivel_anterior:
            log("LEVEL", nivel=nivel, estado=("objeto" if nivel == 0 else "repouso"))
            nivel_anterior = nivel

        if nivel == 0:
            hits += 1
            misses = 0
            if not aberta and hits >= STABLE_READS:
                agora = time.ticks_ms()
                if time.ticks_diff(agora, guarda_ate) < 0:
                    suprimidas += 1
                    log("SUPPRESSED", n=n, dt_ms=time.ticks_diff(agora, guarda_ate) * -1,
                        guard_ms=GUARD_MS, suprimidas=suprimidas)
                    hits = 0
                else:
                    aberta = True
                    hits = 0
                    n += 1
                    t_abertura = agora
                    out.value(1)
                    log("OPEN", n=n, nivel=nivel, t_ms=agora)
        else:
            misses += 1
            hits = 0
            if aberta and misses >= MISS_READS:
                aberta = False
                misses = 0
                agora = time.ticks_ms()
                dur = time.ticks_diff(agora, t_abertura)
                guarda_ate = time.ticks_add(agora, GUARD_MS)
                out.value(0)
                log("CLOSE", n=n, nivel=nivel, dur_ms=dur, guarda_ate=guarda_ate)

        time.sleep_ms(DEBOUNCE_MS)


main()
