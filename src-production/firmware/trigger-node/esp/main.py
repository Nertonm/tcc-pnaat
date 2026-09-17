"""PoC-01 no ESP32 v4: trigger com E18-D80NK: log legivel, armado seguro e guarda anti-duplicacao.

Correcoes vindas da bancada (v3):
  1. ARMADO SEGURO: apos o aquecimento, so arma quando a linha fica estavel em REPOUSO (nivel 1)
     por ARM_MS continuos. Isso elimina a janela espuria no boot (a linha nasce LOW por alguns ms).
  2. GUARDA ANTI-DUPLICACAO: depois de um CLOSE, nova presenca so abre janela se (a) passou
     GUARD_MS E (b) a linha voltou ao repouso entre as duas. A guarda sozinha nao bastava: o
     mesmo objeto que continuava na frente reabria janela depois de um CLOSE por flicker. Um
     SUPPRESSED registra o motivo (guarda ou presenca_continua).
  3. LOG IDENTIFICAVEL: todas as linhas saem como `EV <evento> campo=valor ...` (nivel, n, tempos),
     tanto na serial quanto em /poc01_events.csv. O host interpreta esse formato.

Eletrica: bege = +5V, azul = GND, preto = sinal em P27 (PULL_UP). 0 = objeto, 1 = repouso.
Instalar como main.py faz o firmware iniciar sozinho a cada reset/boot.
"""
from machine import Pin
import time

PRESENCE_PIN = 27          # pino normativo; validar tensão/condicionamento no sensor físico
PINOS_CANDIDATOS = (33, 32, 25, 14, 13, 4)   # entrada com pull-up e livres na placa;
                                             # P27 fica FORA: e o proprio pino do sensor
                                             # (reportado em nivel=) e incluí-lo gerava
                                             # evento falso de "descoberta de fiacao"
CAPTURE_OUT_PIN = 26
DEBOUNCE_MS = 20
STABLE_READS = 5          # leituras LOW para abrir (5 x 20 ms = 100 ms)
MISS_READS = 5            # leituras HIGH para fechar
# CAPTURE_OUT sobe no OPEN e desce no CLOSE: o pulso dura a presenca do item.
# (Havia uma constante WINDOW_MS declarada como "largura do pulso" e nunca usada.)
WARMUP_MS = 1000          # ignora o transitorio de boot
ARM_MS = 500              # repouso continuo exigido para armar (era ARM_READS=10 x
                          # 20 ms = 200 ms, apesar do comentario dizer 500 ms)
GUARD_MS = 500            # janela morta apos cada fechamento
LOG_PATH = "poc01_events.csv"
LOG_MAX_BYTES = 65536     # o CSV vive no flash interno: sem limite, enche
nivel_de_objeto_na_linha = "nivel_de_objeto"
PING_MS = 2000            # heartbeat do nivel do sensor na serial (0 desliga)

pin = Pin(PRESENCE_PIN, Pin.IN, Pin.PULL_UP)
out = Pin(CAPTURE_OUT_PIN, Pin.OUT, value=0)
_candidatos = {n: Pin(n, Pin.IN, Pin.PULL_UP) for n in PINOS_CANDIDATOS}


def niveis_candidatos():
    return " ".join("p%s=%s" % (n, p.value()) for n, p in sorted(_candidatos.items()))


_niveis_ant = {}          # preenchido por instantaneo_pinos(), apos o armamento


def instantaneo_pinos():
    """Fotografa os pinos monitorados.

    Chamado depois do armamento: fotografar no import deixava invisivel qualquer
    mudanca de fio durante o aquecimento e o armamento (~1,5 s), o que contradiz
    a propria promessa de "descobrir a fiacao sem janela de tempo".
    """
    for n, p in _candidatos.items():
        _niveis_ant[n] = p.value()


def checar_mudanca_de_pino():
    """Loga mudanca em qualquer pino medido -- descobre fiacao sem janela de tempo."""
    for n, p in sorted(_candidatos.items()):
        v = p.value()
        antes = _niveis_ant.get(n)
        if antes is None:
            _niveis_ant[n] = v          # primeiro ciclo: so' baseline
            continue
        if v != antes:
            print("EV PINO_CHANGE p%s=%s antes=%s" % (n, v, antes))
            _niveis_ant[n] = v
_log = None
nivel_anterior = None


def log(evento, **campos):
    global _log
    partes = " ".join("%s=%s" % (k, v) for k, v in campos.items())
    print("EV %s %s" % (evento, partes))
    if _log is not None:
        try:
            if _log.tell() > LOG_MAX_BYTES:
                print("EV LOG_FAIL motivo=cheio limite=%d (log desativado)" % LOG_MAX_BYTES)
                _log.close()
                _log = None
                return
            _log.write("%d,%s,%s\n" % (time.ticks_ms(), evento, partes))
            _log.flush()
        except Exception as exc:
            avisar_falha_de_log(exc)


def abrir_log():
    global _log
    try:
        _log = open(LOG_PATH, "a")
    except Exception as exc:
        _log = None
        # falha silenciosa de log era o defeito: sem isto, o firmware prometia CSV
        # e nunca produzia, sem nenhum sinal na serial
        print("EV LOG_FAIL motivo=open erro=%s" % exc)


def avisar_falha_de_log(exc):
    global _log
    print("EV LOG_FAIL motivo=write erro=%s (log desativado)" % exc)
    _log = None


def main():
    global nivel_anterior
    abrir_log()
    log("READY", pin=PRESENCE_PIN, out=CAPTURE_OUT_PIN, debounce_ms=DEBOUNCE_MS,
        stable=STABLE_READS, miss=MISS_READS, guard_ms=GUARD_MS, warmup_ms=WARMUP_MS,
        arm_ms=ARM_MS)
    print("EV PINOS %s (sensor deve ser o que responder ao objeto)" % niveis_candidatos())

    # aquecimento: descarta o transitorio de boot
    t_fim = time.ticks_add(time.ticks_ms(), WARMUP_MS)
    while time.ticks_diff(t_fim, time.ticks_ms()) > 0:
        time.sleep_ms(DEBOUNCE_MS)
    log("WARMUP_DONE", nivel=pin.value())

    # arma SOMENTE quando a linha fica estavel em REPOUSO (nivel 1) por ARM_MS.
    # Sem timeout: enquanto houver algo na frente do sensor (ou o sinal estiver preso em LOW), o
    # firmware avisa e NAO arma. O heartbeat continua saindo aqui: sem ele, um sensor morto ou mal
    # ligado deixava o no' mudo e o texto do aviso culpava o objeto (o codigo nao pode saber a causa).
    repouso_desde = None
    t_armado = None
    t_ping = time.ticks_add(time.ticks_ms(), PING_MS)
    proximo_aviso = time.ticks_add(time.ticks_ms(), 3000)
    while True:
        if pin.value() == 1:
            agora = time.ticks_ms()
            if repouso_desde is None:
                repouso_desde = agora
            if time.ticks_diff(agora, repouso_desde) >= ARM_MS:
                t_armado = repouso_desde
                break
        else:
            repouso_desde = None
            if time.ticks_diff(proximo_aviso, time.ticks_ms()) <= 0:
                log("ARM_WAIT", nivel=pin.value(), nota=nivel_de_objeto_na_linha)
                proximo_aviso = time.ticks_add(time.ticks_ms(), 5000)
        if PING_MS and time.ticks_diff(time.ticks_ms(), t_ping) >= 0:
            print("EV PING nivel=%s fase=armando %s" % (pin.value(), niveis_candidatos()))
            t_ping = time.ticks_add(time.ticks_ms(), PING_MS)
        time.sleep_ms(DEBOUNCE_MS)
    # nivel=1 e' a condicao que armou (o laco so sai com a linha em repouso):
    # reler o pino aqui podia publicar nivel=0, contradizendo o proprio armamento
    log("ARMED", nivel=1, repouso_ms=ARM_MS)
    instantaneo_pinos()

    hits = 0
    misses = 0
    aberta = False
    n = 0
    t_abertura = 0
    # inicio_repouso = primeiro instante do periodo CONTIGUO em que o sensor esta livre;
    # None = o sensor nao esta livre agora (presenca confirmada). Nova janela exige um
    # periodo livre contiguo >= GUARD_MS imediatamente antes da presenca.
    # Sentinelas: 0 e' invalida sob ticks_diff (uptime entre ~6,2 e ~12,4 dias da negativo).
    inicio_repouso = t_armado if t_armado is not None else time.ticks_ms()
    suprimidas = 0
    suprimido_ativo = False

    while True:
        nivel = pin.value()

        # debounce primeiro: LEVEL so' e' publicado quando a amostra crua ja tem
        # STABLE_READS/MISS_READS concordando (antes, um glitch de 20 ms publicava
        # "estado=objeto" sem nenhuma janela)
        if nivel == 0:
            hits += 1
            misses = 0
            confirmado = hits >= STABLE_READS
        else:
            misses += 1
            hits = 0
            confirmado = misses >= MISS_READS

        if confirmado and nivel != nivel_anterior:
            log("LEVEL", nivel=nivel, estado=("objeto" if nivel == 0 else "repouso"),
                amostras=(hits if nivel == 0 else misses))
            nivel_anterior = nivel

        agora = time.ticks_ms()
        if confirmado and nivel == 0:
            # presenca confirmada: o periodo livre terminou (isto e' o que faltava:
            # sem reiniciar o cronometro, uma presenca continua acabava satisfazendo a guarda)
            livre_ms = 0 if inicio_repouso is None else time.ticks_diff(agora, inicio_repouso)
            inicio_repouso = None
            if not aberta:
                if livre_ms < GUARD_MS:
                    suprimidas += 1
                    # uma linha por PRESENCA suprimida, nao uma a cada 100 ms: com o
                    # objeto parado na frente saiam ~50 linhas iguais enchendo o CSV
                    if not suprimido_ativo:
                        log("SUPPRESSED", n=n, motivo="guarda", suprimidas=suprimidas,
                            resta_ms=GUARD_MS - livre_ms)
                        suprimido_ativo = True
                    hits = 0
                else:
                    aberta = True
                    hits = 0
                    n += 1
                    t_abertura = agora
                    out.value(1)
                    log("OPEN", n=n, nivel=nivel, t_ms=agora, livre_ms=livre_ms)
                    suprimido_ativo = False
        elif confirmado and nivel == 1:
            if aberta:
                aberta = False
                misses = 0
                dur = time.ticks_diff(agora, t_abertura)
                out.value(0)
                # o pulso de saida dura o tempo da presenca do item
                log("CLOSE", n=n, nivel=nivel, dur_ms=dur, guard_ms=GUARD_MS)
                inicio_repouso = agora      # comeca o periodo livre
            elif inicio_repouso is None:
                inicio_repouso = agora      # sensor voltou a ficar livre
                suprimido_ativo = False

        checar_mudanca_de_pino()

        if PING_MS and time.ticks_diff(time.ticks_ms(), t_ping) >= 0:
            print("EV PING nivel=%s n=%s aberta=%s %s"
                  % (nivel, n, aberta, niveis_candidatos()))
            t_ping = time.ticks_add(time.ticks_ms(), PING_MS)

        time.sleep_ms(DEBOUNCE_MS)


main()
