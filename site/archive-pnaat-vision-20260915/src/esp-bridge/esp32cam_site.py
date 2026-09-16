#!/usr/bin/env python3
"""Site de captura da ESP32-CAM (dona unica da porta serial).

Dois canais no mesmo fio, separados por enquadramento e nao por heuristica:
  - mensagens binarias (transporte v1, ver transport_bin.py) quando o firmware
    esta em modo bin;
  - linhas ASCII (logs e, no modo texto, os FRAME_BEGIN/FRAME_DATA/FRAME_END).
O Decoder devolve os trechos descartados em ordem, entao os logs continuam
legiveis e o parser nunca publica imagem sem CRC e marcadores validados.

Oracolo entre implementacoes: o firmware anuncia `FRAME_INFO ... crc32=XXXXXXXX`
em ASCII e o host recalcula o CRC-32 do frame montado com zlib; divergencia
indica erro de implementacao de CRC, nao corrupcao de enlace.

Uso: python3 esp32cam_site.py [--porta 8091] [--host 0.0.0.0] [--serial /dev/ttyUSB0]
"""
from __future__ import annotations

import argparse
import base64
import binascii
import heapq
import json
import os
import os
import re
import sys
import threading
import time
import zlib
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Full, Queue
from urllib.parse import parse_qs, urlparse

import serial
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transport_bin import Decoder, FrameAssembler  # noqa: E402

SERIAL_BAUD = 921600
ALLOWED_COMMANDS = ("CMD_CAPTURE", "CMD_STATUS", "CMD_SENSOR",
                    "CMD_TRANSPORT BIN", "CMD_TRANSPORT TEXT",
                    "CMD_TEST_FALHA_INIT", "CMD_TRIG_NEXT")
EV_OPEN_RE = re.compile(r"EV OPEN n=(\d+)")
EV_ARMED_RE = re.compile(r"EV ARMED")
EV_WARMUP_RE = re.compile(r"EV (READY|WARMUP_DONE)")
EV_ARM_WAIT_RE = re.compile(r"EV ARM_WAIT")
EV_NEUTRO_RE = re.compile(r"EV (LEVEL|CLOSE|SUPPRESSED|PING)")
EV_PING_RE = re.compile(r"EV PING nivel=(\d+)")
PINOS_PING_RE = re.compile(r"p(\d+)=(\d)")
EV_READY_PIN_RE = re.compile(r"EV READY pin=(\d+)")
PINO_CHANGE_RE = re.compile(r"EV PINO_CHANGE p(\d+)=(\d) antes=(\d)")
EXT_REF_RE = re.compile(r"ext_ref=(\d+)")
TRIG_ACCEPTED_RE = re.compile(r"TRIGGER_ACCEPTED source=(\S+) event=(\d+) ext_ref=(\d+)")
TRIGGER_BAUD = 115200
TRIGGER_DELAY_MS = 1000
trigger_delay_ms = TRIGGER_DELAY_MS
ROTACAO_ESP = 180   # sensor do ESP-CAM montado invertido
trigger_delay_saved_at = time.time()
last_delay_test = {}
ALLOWED_PREFIXES = ("CMD_BAUD ",)
BAUD_ACK_RE = re.compile(r"BAUD_ACK ok=1 de=(\d+) para=(\d+)")
BAUD_ATIVO_RE = re.compile(r"BAUD_ATIVO (\d+)")

BEGIN_RE = re.compile(
    rb"FRAME_BEGIN v=1 encoding=base64 source=([a-z0-9_]+) event=(\d+) trigger_us=(\d+) "
    rb"len=(\d+) crc32=([0-9a-f]+) wake_us=(\d+) warmup_us=(\d+) capture_us=(\d+)"
)
DATA_RE = re.compile(rb"FRAME_DATA event=(\d+) seq=(\d+) data=([A-Za-z0-9+/=]+)")
END_RE = re.compile(rb"FRAME_END event=(\d+) tx_us=(\d+) total_us=(\d+)")
INFO_RE = re.compile(
    r"FRAME_INFO source=(\S+) event=(\d+) ext_ref=(\d+) trigger_us=(-?\d+) "
    r"len=(\d+) crc32=([0-9a-f]{8})"
)
END_BIN_RE = re.compile(r"FRAME_END_BIN event=(\d+) tx_us=(\d+) total_us=(\d+) chunks=(\d+)")

# Tabela de sanear logs: qualquer byte fora de 32..126 vira "." (via C, por byte)
_SANITIZE = bytes(0x2E if not (32 <= b < 127) else b for b in range(256))
TRANSPORT_RE = re.compile(r"TRANSPORT mode=(\w+)")
STATUS_RE = re.compile(r"STATUS camera=(\w+) driver=(\d+) power_en=(-?\d+) "
                       r"armed=(\d+) transport=(\w+) baud=(\d+)")
TRIGGER_RE = re.compile(r"TRIGGER_ACCEPTED")
CAMERA_OFF_RE = re.compile(r"CAMERA_OFF[^\n]*motivo=(\w+)|CAMERA_OFF boot=1")


def _e_residuo(linha: bytes) -> bool:
    """Bytes que nao sao mensagem binaria nem log: o decoder os devolve como
    'text'. Se a linha e' majoritariamente nao imprimivel, nao e' log."""
    if not linha:
        return True
    ruins = sum(1 for b in linha if not (32 <= b < 127))
    return ruins / len(linha) > 0.2

lock = threading.Lock()
latest: bytes | None = None
latest_meta: dict[str, object] = {}
frames_ok = 0
frames_bad = 0
frames_text = 0
frames_bin = 0
serial_bytes = 0
serial_printed = 0
serial_lines = 0
serial_last_error = ""
serial_open = False
booted = False
transport = "desconhecido"
camera_estado = "desconhecido"
driver_estado = -1
trigger_porta = None                # dona unica da porta do no de trigger
trigger_aberta = False
trigger_erro = ""
trigger_estado = "desconhecido"     # warmup | armando | armado
trigger_ultimo_n = None
trigger_ultimo_em = 0.0
trigger_total = 0
trigger_linhas: deque[str] = deque(maxlen=200)
trigger_pendente: int | None = None   # ext_ref pedido, aguardando a foto
sensor_nivel: int | None = None       # ultimo nivel lido no sensor (PING)
pino_sensor = 27          # atualizado pelo `pin=` do EV READY do firmware
TOKEN = ""                # --token: exige token nos POST destrutivos
sensor_em = 0.0
pinos_vistos: dict[int, int] = {}     # varredura de pinos do heartbeat
pareamento: dict[str, object] = {"status": "sem dado"}
transport_desejado: str | None = "bin"   # modo que o site quer (reaplicado se a camera reiniciar)
# A camera reinicia ao abrir a porta e volta ao modo de boot (texto). Sem isso o site
# roda em texto (2x de bytes na linha) sem o operador perceber.
capturas_dir: Path | None = None      # None = nao grava
capturas_total = 0
capturas_bytes = 0
captura_ultima: dict[str, object] = {}
latencias: deque[dict[str, object]] = deque(maxlen=30)
latencia_pendente: dict[str, float] = {}
delay_ultimo: dict[str, object] = {}
delay_serie_ativa = False
eventos_ui: deque[dict[str, object]] = deque(maxlen=40)   # linha do tempo do painel


def evento(tipo: str, texto: str, **campos: object) -> None:
    """Evento visivel no painel, com horario. A UI le isto em /status."""
    with lock:
        eventos_ui.appendleft({"t": time.strftime("%H:%M:%S"), "tipo": tipo,
                               "texto": texto, **campos})
NOME_SEGURO = re.compile(r"^[A-Za-z0-9._-]{1,120}$")
crosscheck: dict[str, object] = {"status": "sem dado"}
started_at = time.time()
log_lines: deque[str] = deque(maxlen=400)
command_queue: Queue[bytes] = Queue(maxsize=4)
decoder = Decoder()
assembler = FrameAssembler()
serial_port = None                 # dona do /dev/ttyUSB0 durante a sessao
baud_atual = SERIAL_BAUD
baud_pendente: int | None = None
baud_troca_em = 0.0
# Nao persistir o baud negociado: medido que o ESP reinicia a cada abertura da
# porta (BOOT_TEST sai logo depois de "aberta ... @ 921600"), entao os dois lados
# sempre se reencontram no baud de boot. Guardar a taxa alta faria o site abrir
# em 1,5 Mbps contra um device que acabou de subir em 921600, matando o enlace.

# estado do canal texto (linhas)
text_buf = bytearray()
pending_header: re.Match[bytes] | None = None
pending_chunks: dict[int, bytes] = {}
announced: dict[int, tuple[int, int, int]] = {}   # evento -> (len, crc32, ext_ref)
ext_ref_por_evento: dict[int, int] = {}           # aprende pelo TRIGGER_ACCEPTED
ANUNCIOS_MAX = 256      # o dict por evento nao pode crescer sem limite
trigger_times: dict[int, float] = {}


def log(kind: str, text: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    log_lines.append(f"{stamp} [{kind}] {text}")


def publish(frame: bytes, event: int, encoding: str, extra: dict[str, object]) -> None:
    global latest, latest_meta, frames_ok, frames_text, frames_bin, crosscheck, trigger_pendente
    crc = f"{zlib.crc32(frame) & 0xFFFFFFFF:08x}"
    with lock:
        latest = frame
        latest_meta = {"event": event, "len": len(frame), "encoding": encoding,
                       "crc32": crc, "received_at": time.time(), **extra}
        frames_ok += 1
        if encoding == "bin":
            frames_bin += 1
        else:
            frames_text += 1
        esperado = announced.get(event)
        if esperado is None:
            crosscheck = {"status": "sem anuncio", "event": event}
        else:
            anunciado_len, anunciado_crc, _anunciado_ref = esperado
            ok = (anunciado_len == len(frame) and f"{anunciado_crc:08x}" == crc)
            crosscheck = {"status": "ok" if ok else "DIVERGENTE", "event": event,
                          "anunciado_len": anunciado_len,
                          "anunciado_crc32": f"{anunciado_crc:08x}",
                          "calculado_len": len(frame)}
        latest_meta["crosscheck"] = crosscheck["status"]
        estado_cc = crosscheck["status"]
        meta_publicado = dict(latest_meta)
    log("FRAME", f"encoding={encoding} event={event} {len(frame)}B "
                 f"crc32={crc} crosscheck={estado_cc}")
    evento("foto", f"foto publicada ({len(frame)} B, evento {event}, {encoding})",
           ext_ref=int(extra.get("ext_ref") or 0), evento_id=event)
    with lock:
        # so mede delay quando o frame veio de um trigger DE VERDADE: uma captura
        # manual publicada depois herda o t_sensor do trigger anterior e fabricava
        # a metrica (medido: 7630 ms para um frame sem trigger).
        ref_frame_atual = int(extra.get("ext_ref") or 0)
        mede = bool(latencia_pendente) and ref_frame_atual != 0 and \
            latencia_pendente.get("ref") == ref_frame_atual
        if mede:
            latencia_pendente["t_foto"] = time.time()
            total = latencia_pendente["t_foto"] - latencia_pendente["t_sensor"]
            if total < 30:      # descarta par sem relacao (teste manual antigo)
                delay_ultimo.update({
                    "evento": event,
                    "ext_ref": int(extra.get("ext_ref") or 0),
                    "sensor_comando_ms": round(
                        (latencia_pendente["t_comando"] - latencia_pendente["t_sensor"]) * 1000),
                    "comando_foto_ms": round(
                        (latencia_pendente["t_foto"] - latencia_pendente["t_comando"]) * 1000),
                    "sensor_foto_ms": round(total * 1000),
                    "camera_total_ms": round(int(extra.get("total_us") or 0) / 1000),
                    "camera_linha_ms": round(int(extra.get("tx_us") or 0) / 1000),
                    "em": time.time(),
                })
                latencias.append(dict(delay_ultimo))
                # os tempos internos da camera chegam depois (FRAME_END_BIN): nao
                # imprimir zero aqui, que era lido como "a camera nao gastou tempo"
                log("DELAY", f"sensor->foto {delay_ultimo['sensor_foto_ms']} ms "
                             f"(comando->foto {delay_ultimo['comando_foto_ms']} ms; "
                             f"tempos da camera em /status)")
        # a foto chegou: o pendente cumpriu o papel (nao pode ficar "aguardando" para sempre)
        trigger_pendente = None
    gravar_captura(frame, meta_publicado)
    ext_ref_callback = int(meta_publicado.get("ext_ref") or 0)
    if ext_ref_callback:
        threading.Thread(target=notificar_captura_trigger,
                         args=(event, ext_ref_callback), daemon=True).start()


def notificar_captura_trigger(event: int, ext_ref: int) -> None:
    """Entrega o frame validado ao site do Acerola para fechar a serie de 3."""
    if not ext_ref:
        return
    import urllib.parse
    import urllib.request
    trigger_em = trigger_times.pop(ext_ref, time.time())
    query = urllib.parse.urlencode({"trigger_n": ext_ref, "trigger_em": repr(trigger_em)})
    try:
        with urllib.request.urlopen("http://127.0.0.1:8090/capturar-trigger?" + query,
                                   timeout=35) as resp:
            body = resp.read(512).decode("utf-8", "replace")
        log("TRIPLA", f"trigger n={ext_ref} serie retornou: {body[:240]}")
    except Exception as exc:
        log("TRIPLA", f"falha ao salvar foto do trigger n={ext_ref}: {exc}")


def gravar_captura(frame: bytes, meta: dict[str, object]) -> None:
    """Grava o JPEG do trigger e a linha de indice, com a referencia no nome.

    O I/O de disco fica FORA do lock global: mante-lo dentro travava /status,
    /frame.jpg e /log (e o proprio painel) enquanto o arquivo era escrito.
    """
    global capturas_total, capturas_bytes, captura_ultima
    if capturas_dir is None:
        return
    try:
        capturas_dir.mkdir(parents=True, exist_ok=True)
        ref = int(meta.get("ext_ref") or 0)
        event = int(meta.get("event") or 0)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        with lock:
            if (capturas_dir / f"{stamp}_trig{ref:04d}_evt{event:04d}.jpg").exists():
                stamp = f"{stamp}_{int(time.time()*1000)%1000:03d}"
            nome = f"{stamp}_trig{ref:04d}_evt{event:04d}.jpg"
            capturas_total += 1
            capturas_bytes += len(frame)
        caminho = capturas_dir / nome
        # orientação na origem: sensor do ESP-CAM montado invertido (180°)
        from io import BytesIO
        with Image.open(BytesIO(frame)) as _im:
            _buf = BytesIO()
            _im.rotate(ROTACAO_ESP, expand=True).save(_buf, format='JPEG', quality=95, subsampling=0)
        caminho.write_bytes(_buf.getvalue())            # I/O fora do lock, já orientado
        registro = {
            "arquivo": nome,
            "hora": time.strftime("%H:%M:%S"),
            "bytes": len(frame),
            "ext_ref": ref,
            "evento": event,
            "trigger_em": trigger_ultimo_em,
            "gravado_em": time.time(),
            "crc32": meta.get("crc32"),
            "crosscheck": meta.get("crosscheck"),
        }
        with lock:
            captura_ultima = dict(registro)
            if "t_foto" in latencia_pendente and "t_gravado" not in latencia_pendente:
                latencia_pendente["t_gravado"] = registro["gravado_em"]
                delay_ultimo["foto_arquivo_ms"] = round(
                    (registro["gravado_em"] - latencia_pendente["t_foto"]) * 1000)
                delay_ultimo["total_arquivo_ms"] = round(
                    (registro["gravado_em"] - latencia_pendente["t_sensor"]) * 1000)
        with (capturas_dir / "indice.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(registro, ensure_ascii=False) + "\n")   # I/O fora do lock
        log("CAPTURA", f"{nome} ({len(frame)} B) trigger n={ref} evento={event}")
        evento("arquivo", f"gravada {nome}", ext_ref=ref)
    except OSError as exc:
        log("CAPTURA", f"falha ao gravar: {exc}")


def handle_text(data: bytes) -> None:
    """Linhas ASCII: logs e, no modo texto, o frame base64."""
    global pending_header, frames_bad, booted, transport, serial_lines
    global baud_atual, baud_pendente, baud_troca_em, camera_estado, driver_estado
    global pareamento, trigger_pendente
    text_buf.extend(data)
    while True:
        idx = text_buf.find(b"\n")
        if idx < 0:
            if len(text_buf) > 8192:      # linha absurda: descarta
                text_buf.clear()
            return
        line = bytes(text_buf[:idx]).strip(b"\r")
        del text_buf[:idx + 1]
        if not line:
            continue
        begin = BEGIN_RE.search(line)
        if begin:
            pending_header = begin
            pending_chunks.clear()
            continue
        if pending_header is not None:
            data_m = DATA_RE.fullmatch(line)
            if data_m and int(data_m.group(1)) == int(pending_header.group(2)):
                pending_chunks[int(data_m.group(2))] = data_m.group(3)
                continue
            end_m = END_RE.fullmatch(line)
            if end_m and int(end_m.group(1)) == int(pending_header.group(2)):
                publish_text_frame(pending_header, pending_chunks, end_m)
                pending_header = None
                pending_chunks.clear()
                continue
        text = line.translate(_SANITIZE).decode("ascii", "replace").strip()
        if not text:
            continue
        serial_lines += 1
        info = INFO_RE.search(text)
        if info:
            announced[int(info.group(2))] = (int(info.group(5)), int(info.group(6), 16),
                                             int(info.group(3)))
            ref_frame = int(info.group(3))
            if ref_frame:
                with lock:
                    pareamento = {
                        "status": "casa" if trigger_pendente == ref_frame else "divergente",
                        "ext_ref": ref_frame,
                        "trigger_n": trigger_pendente,
                        "trigger_em": trigger_ultimo_em,
                        "frame_em": time.time(),
                    }
                log("PONTE", f"photo ext_ref={ref_frame} casa com trigger "
                             f"n={trigger_pendente} ({pareamento['status']})")
            while len(announced) > ANUNCIOS_MAX:
                announced.pop(next(iter(announced)))   # descarta o mais antigo
        fim_bin = END_BIN_RE.search(text)
        if fim_bin:
            evento = int(fim_bin.group(1))
            with lock:
                if latest_meta.get("event") == evento:
                    latest_meta["tx_us"] = int(fim_bin.group(2))
                    latest_meta["total_us"] = int(fim_bin.group(3))
                    latest_meta["chunks_reportados"] = int(fim_bin.group(4))
                    if delay_ultimo.get("evento") == evento and "t_foto" in latencia_pendente:
                        delay_ultimo["camera_total_ms"] = round(int(fim_bin.group(3)) / 1000)
                        delay_ultimo["camera_linha_ms"] = round(int(fim_bin.group(2)) / 1000)
                        if latencias:
                            latencias[-1].update({
                                "camera_total_ms": delay_ultimo["camera_total_ms"],
                                "camera_linha_ms": delay_ultimo["camera_linha_ms"],
                            })
        if "TASKS_READY" in text:
            booted = True
        # Em modo binario a linha do firmware chega colada a residuo binario
        # ("...`.TRANSPORT mode=bin"), entao a deteccao tem de ser por busca.
        modo = TRANSPORT_RE.search(text)
        if modo:
            transport = modo.group(1)
            if transport_desejado and transport != transport_desejado:
                # a camera reiniciou e voltou ao modo de boot: reaplica o escolhido
                try:
                    command_queue.put_nowait(
                        f"CMD_TRANSPORT {transport_desejado.upper()}".encode() + bytes([10]))
                    log("ESP", f"transporte reaplicado: {transport_desejado}")
                except Full:
                    pass
        estado_no = STATUS_RE.search(text)
        if estado_no:
            with lock:
                camera_estado = estado_no.group(1)
                driver_estado = int(estado_no.group(2))
        # Eventos do firmware dao o estado na hora; o STATUS so confirma depois.
        if TRIGGER_RE.search(text):
            camera_estado = "ativa"
            driver_estado = 1
            aceito = TRIG_ACCEPTED_RE.search(text)
            if aceito:
                ext_ref_por_evento[int(aceito.group(2))] = int(aceito.group(3))
                while len(ext_ref_por_evento) > 256:
                    ext_ref_por_evento.pop(next(iter(ext_ref_por_evento)))
        off = CAMERA_OFF_RE.search(text)
        if off:
            camera_estado = "standby"
            driver_estado = 0
        ack = BAUD_ACK_RE.search(text)
        if ack:
            baud_pendente = int(ack.group(2))
            baud_troca_em = time.time() + 0.4      # deixa o ACK sair no baud antigo
        ativo = BAUD_ATIVO_RE.search(text)
        if ativo:
            baud_atual = int(ativo.group(1))
        # Residuo binario nao e' log: descarta em vez de poluir o painel.
        if info or modo or ack or ativo or not _e_residuo(line):
            log("ESP", text[:240])


def publish_text_frame(header: re.Match[bytes], chunks: dict[int, bytes], end: re.Match[bytes]) -> None:
    global frames_bad
    try:
        expected_len = int(header.group(4))
        expected_crc = int(header.group(5), 16)
        frame = base64.b64decode(b"".join(chunks[i] for i in sorted(chunks)), validate=True)
        actual_crc = binascii.crc32(frame) & 0xFFFFFFFF
        if (len(frame) != expected_len or frame[:2] != b"\xff\xd8"
                or frame[-2:] != b"\xff\xd9" or actual_crc != expected_crc):
            raise ValueError("gate do frame texto falhou")
    except (ValueError, KeyError, binascii.Error) as exc:
        with lock:
            frames_bad += 1
        log("FRAME", f"frame texto rejeitado: {exc}")
        return
    with lock:
        anuncio = announced.get(int(header.group(2)))
        ref_texto = anuncio[2] if anuncio else ext_ref_por_evento.get(int(header.group(2)), 0)
    publish(frame, int(header.group(2)), "text", {
        "source": header.group(1).decode("ascii"),
        "ext_ref": ref_texto,
        "trigger_us": int(header.group(3)),
        "warmup_us": int(header.group(7)),
        "capture_us": int(header.group(8)),
        "tx_us": int(end.group(2)),
        "total_us": int(end.group(3)),
    })


def handle_message(msg) -> None:
    frame = assembler.feed(msg)
    if frame is None:
        return
    mensagens = assembler.expect_seq + 2          # BEGIN + chunks + END
    evento_frame = assembler.event_id             # evento do frame montado, nao o da mensagem
    with lock:
        anuncio = announced.get(evento_frame)
        ext_ref = anuncio[2] if anuncio else ext_ref_por_evento.get(evento_frame, 0)
    publish(frame, evento_frame, "bin", {
        "source": "bin",
        "ext_ref": ext_ref,
        "chunks": assembler.expect_seq,
        "bytes_enquadramento": 19 * mensagens,    # 15 B de cabecalho + 4 B de CRC por mensagem
    })


def disparar_camera(ref: int) -> None:
    """Evento do sensor -> espera configurada -> comando da ESP-CAM."""
    global trigger_pendente, trigger_delay_ms
    with lock:
        pronto = serial_open
    if not pronto:
        log("TRIG", f"trigger n={ref} sem no de camera disponivel")
        return
    with lock:
        latencia_pendente.clear()
        latencia_pendente["ref"] = ref
        latencia_pendente["t_sensor"] = trigger_ultimo_em or time.time()
        latencia_pendente["t_comando"] = time.time()
    trigger_times[ref] = trigger_ultimo_em or time.time()
    time.sleep(max(0, trigger_delay_ms) / 1000.0)
    try:
        command_queue.put_nowait(b"CMD_TRIG " + str(ref).encode() + bytes([10]))
    except Full:
        # nao deixar pendente armado para um trigger que nunca foi pedido
        with lock:
            latencia_pendente.clear()
        log("TRIG", f"fila do no de camera cheia, trigger n={ref} perdido")
        return
    trigger_pendente = ref
    log("PONTE", f"trigger n={ref} -> CMD_TRIG {ref} no no da camera")
    evento("trigger", f"trigger n={ref} recebido, comando enviado a camera", ext_ref=ref)


def registrar_trigger(ref: int, em: float) -> None:
    """Contabiliza um trigger sob o lock.

    Antes eram tres atribuicoes soltas no thread do trigger, fora do lock: com
    /simular ou /medir rodando junto, `trigger_total += 1` se perdia e o painel
    subnotificava o numero de triggers (justamente o dado do experimento).
    """
    global trigger_total, trigger_ultimo_n, trigger_ultimo_em
    with lock:
        trigger_total += 1
        trigger_ultimo_n = ref
        trigger_ultimo_em = em


def trigger_reader(port_name: str, baud: int) -> None:
    """Dona unica da porta do no de trigger (MicroPython da PoC-01)."""
    global trigger_aberta, trigger_erro, trigger_estado, trigger_ultimo_n
    global trigger_ultimo_em, trigger_total, trigger_porta, sensor_nivel, sensor_em, pinos_vistos
    global pino_sensor
    while True:
        try:
            port = serial.Serial(port=None, rtscts=False, dsrdtr=False, exclusive=True)
            port.port = port_name
            port.baudrate = baud
            port.timeout = 0.2
            port.dtr = False
            port.rts = False           # nao resetar a placa ao abrir
            port.open()
            with lock:
                trigger_aberta = True
                trigger_porta = port
                trigger_erro = ""
            log("TRIG", f"porta aberta {port_name} @ {baud}")
            buf = bytearray()
            while True:
                pedaco = port.read(1024)
                if not pedaco:
                    continue
                buf.extend(pedaco)
                while True:
                    fim = buf.find(b"\n")
                    if fim < 0:
                        if len(buf) > 4096:
                            buf.clear()
                        break
                    linha = bytes(buf[:fim]).strip(b"\r")
                    del buf[:fim + 1]
                    if not linha:
                        continue
                    texto = linha.translate(_SANITIZE).decode("ascii", "replace").strip()
                    if not texto:
                        continue
                    with lock:
                        trigger_linhas.append(texto)
                    mudanca = PINO_CHANGE_RE.search(texto)
                    if mudanca:
                        pino, agora, antes_p = mudanca.group(1), mudanca.group(2), mudanca.group(3)
                        evento("pino", "pino p%s saiu de %s para %s (medicao de fiacao)"
                               % (pino, antes_p, agora))
                    pronto = EV_READY_PIN_RE.search(texto)
                    if pronto:
                        pino_sensor = int(pronto.group(1))
                    ping = EV_PING_RE.search(texto)
                    if ping:
                        sensor_nivel = int(ping.group(1))
                        sensor_em = time.time()
                        pinos_vistos = {int(n): int(v) for n, v in PINOS_PING_RE.findall(texto)}
                        outros = {p: v for p, v in pinos_vistos.items()
                                  if v == 0 and p != pino_sensor}
                        if sensor_nivel == 1 and outros:
                            # o pino vem do EV READY do proprio firmware: trocar
                            # PRESENCE_PIN nao pode deixar esta dica mentindo
                            log("DICA", "pino(s) em nivel de objeto %s mas o firmware le P%s "
                                        "-- sensor pode estar em outro pino"
                                        % (sorted(outros), pino_sensor))
                    else:
                        log("TRIG", texto[:240])
                    aberto = EV_OPEN_RE.search(texto)
                    if aberto:
                        n = int(aberto.group(1))
                        evento("sensor", f"sensor detectou objeto (n={n})", ext_ref=n)
                        trigger_estado = "armado"
                        registrar_trigger(n, time.time())
                        threading.Thread(target=disparar_camera, args=(n,),
                                         name="trigger-delay", daemon=True).start()
                    elif EV_ARMED_RE.search(texto):
                        trigger_estado = "armado"
                    elif EV_ARM_WAIT_RE.search(texto):
                        trigger_estado = "aguardando_objeto"
                    elif EV_WARMUP_RE.search(texto):
                        trigger_estado = "warmup"
                    elif EV_NEUTRO_RE.search(texto):
                        pass          # evento de nivel/guarda nao muda o estado
        except Exception as exc:
            with lock:
                trigger_aberta = False
                trigger_erro = repr(exc)
            log("TRIG", f"reconectando apos {type(exc).__name__}: {exc}")
            time.sleep(1)


def serial_reader(port_name: str) -> None:
    global serial_bytes, serial_lines, serial_last_error, serial_open, booted
    global serial_port, baud_atual, baud_pendente
    while True:
        try:
            port = serial.Serial(port=None, rtscts=False, dsrdtr=False, exclusive=True)
            port.port = port_name
            # O ESP reinicia quando a porta e' aberta e volta ao baud de boot:
            # reabrir na taxa negociada deixaria o enlace mudo (serial_open=True,
            # nenhum byte) sem nenhum aviso no painel.
            port.baudrate = SERIAL_BAUD
            baud_atual = SERIAL_BAUD
            port.timeout = 0.2
            port.dtr = False
            port.rts = False
            port.open()
            with lock:
                serial_open = True
                booted = False
                serial_port = port
            log("SERIAL", f"aberta {port_name} @ {baud_atual} (baud de boot)")
            while True:
                try:
                    port.write(command_queue.get_nowait())
                    port.flush()
                except Empty:
                    pass
                if baud_pendente is not None and time.time() >= baud_troca_em:
                    novo = baud_pendente
                    baud_pendente = None
                    try:
                        port.baudrate = novo
                        baud_atual = novo
                        log("SERIAL", f"host trocou para {novo} baud")
                    except (serial.SerialException, ValueError, OSError) as exc:
                        log("SERIAL", f"falha ao trocar baud: {exc}")
                chunk = port.read(4096)
                if not chunk:
                    continue
                with lock:
                    serial_bytes += len(chunk)
                for kind, payload in decoder.feed_ex(chunk):
                    if kind == "text":
                        handle_text(payload)          # type: ignore[arg-type]
                    else:
                        handle_message(payload)
        except Exception as exc:          # qualquer falha de parse nao pode
            with lock:                     # matar a thread em silencio
                serial_open = False
                booted = False
                serial_last_error = repr(exc)
            log("SERIAL", f"reconectando apos {type(exc).__name__}: {exc}")
            time.sleep(1)


def snapshot() -> dict[str, object]:
    with lock:
        return {
            "serial_open": serial_open,
            "serial_last_error": serial_last_error,
            "serial_bytes": serial_bytes,
            "serial_lines": serial_lines,
            "frames_ok": frames_ok,
            "frames_bad": frames_bad,
            "frames_text": frames_text,
            "frames_bin": frames_bin,
            "meta": dict(latest_meta),
            "has_frame": latest is not None,
            "booted": booted,
            "transport": transport,
            "camera": camera_estado,
            "driver": driver_estado,
            "sensor": {"nivel": sensor_nivel, "idade_s": round(time.time() - sensor_em, 1)
                                if sensor_em else None,
                       "pinos": dict(sorted(pinos_vistos.items()))},
            "trigger": {
                "delay_ms": trigger_delay_ms,
                "delay_saved_at": trigger_delay_saved_at,
                "last_delay_test": dict(last_delay_test),
                "aberta": trigger_aberta,
                "erro": trigger_erro,
                "estado": trigger_estado,
                "ultimo_n": trigger_ultimo_n,
                "ultimo_em": trigger_ultimo_em,
                "total": trigger_total,
                "aguardando": trigger_pendente,
            },
            "pareamento": dict(pareamento),
            "eventos": list(eventos_ui),
            "foto_em": latest_meta.get("received_at"),
            "foto_evento": latest_meta.get("event"),
            "delay": {
                "ultimo": dict(delay_ultimo),
                "n": len(latencias),
                "media_ms": round(sum(int(x["sensor_foto_ms"]) for x in latencias) / len(latencias))
                            if latencias else None,
                "min_ms": min((int(x["sensor_foto_ms"]) for x in latencias), default=None),
                "max_ms": max((int(x["sensor_foto_ms"]) for x in latencias), default=None),
                "media_camera_ms": round(sum(int(x.get("camera_total_ms") or 0) for x in latencias) / len(latencias))
                                   if latencias else None,
                "serie_ativa": delay_serie_ativa,
            },
            "capturas": {
                "dir": str(capturas_dir) if capturas_dir else None,
                "total": capturas_total,
                "bytes_sessao": capturas_bytes,
                "ultima": dict(captura_ultima),
            },
            "baud": baud_atual,
            "decoder": {"aceitas": decoder.accepted, "descartados": decoder.discarded_bytes,
                        "hdr_ruim": decoder.bad_header, "payload_ruim": decoder.bad_payload,
                        "buffer": len(decoder.buffer)},
            "assembler": {"frames": assembler.frames_ok, "lacunas": assembler.gaps,
                          "duplicados": assembler.duplicates, "rejeitados": assembler.rejected,
                          "ultimo_erro": assembler.last_error},
            "crosscheck": dict(crosscheck),
            "uptime_s": round(time.time() - started_at, 1),
        }


PAGE = """<!doctype html>
<meta name=viewport content='width=device-width,initial-scale=1'>
<title>ESP32-CAM | captura</title>
<style>
 :root{--fundo:#0f1216;--painel:#171c22;--regra:#2a323c;--texto:#e8edf3;--fraco:#8b98a7;
       --azul:#5aa9e6;--verde:#57cc99;--ambar:#f2b544;--vermelho:#e5646e}
 *{box-sizing:border-box}
 body{margin:0;background:var(--fundo);color:var(--texto);font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif}
 header{padding:16px 22px;border-bottom:1px solid var(--regra);display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
 header h1{font-size:17px;margin:0}
 header .sub{color:var(--fraco);font-size:13px}
 main{max-width:1240px;margin:0 auto;padding:20px;display:grid;gap:18px;grid-template-columns:1.4fr 1fr}
 @media(max-width:940px){main{grid-template-columns:1fr}}
 .painel{background:var(--painel);border:1px solid var(--regra);border-radius:10px;padding:16px}
 h2{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--azul);margin:0 0 12px}
 .videobox{position:relative}
 img{width:100%;border-radius:6px;background:#000;display:block;min-height:220px;object-fit:contain;
     transition:box-shadow .25s}
 img.nova{box-shadow:0 0 0 3px var(--verde)}
 #momento{margin-top:10px;font-size:14px;font-variant-numeric:tabular-nums}
 #momento b{color:var(--verde)}
 #momento .fraco{color:var(--fraco)}
 .botoes{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
 button{font:inherit;font-weight:600;padding:9px 14px;border-radius:8px;border:1px solid var(--regra);
        background:#202833;color:var(--texto);cursor:pointer}
 button.principal{background:var(--azul);border-color:var(--azul);color:#08111a}
 button.ativo{background:var(--verde);border-color:var(--verde);color:#08111a}
 button:disabled{opacity:.5;cursor:progress}
 dl{display:grid;grid-template-columns:auto 1fr;gap:5px 14px;margin:0;font-size:13.5px}
 dt{color:var(--fraco)}
 dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
 #eventos{list-style:none;margin:0;padding:0;max-height:230px;overflow:auto;font-size:13px}
 #eventos li{display:flex;gap:10px;padding:3px 0;border-bottom:1px solid #1f262e}
 #eventos .h{color:var(--fraco);font-variant-numeric:tabular-nums}
 #eventos .sensor{color:var(--ambar)} #eventos .foto{color:var(--verde)} #eventos .arquivo{color:var(--azul)}
 pre{margin:12px 0 0;background:#0b0e12;border:1px solid var(--regra);border-radius:8px;padding:10px;
     height:170px;overflow:auto;font-size:12.5px;line-height:1.45;white-space:pre-wrap}
 .ok{color:var(--verde)}.aviso{color:var(--ambar)}.erro{color:var(--vermelho)}
 .barra{height:5px;border-radius:3px;background:var(--regra);overflow:hidden;margin-top:10px}
 .barra i{display:block;height:100%;width:0;background:var(--azul);transition:width .25s}
 hr{border:0;border-top:1px solid var(--regra);margin:14px 0}
</style>
<header>
  <h1>ESP32-CAM &mdash; captura por trigger</h1>
  <span class=sub id=sub>carregando&hellip;</span>
  <span class=sub style='margin-left:auto'>v17</span>
</header>
<main>
  <section class=painel>
    <h2>Ultima captura</h2>
    <div class=videobox><img id=foto alt='frame da ESP32-CAM'></div>
    <div id=momento>sem captura ainda &mdash; passe um objeto no sensor ou clique em Capturar</div>
    <div class=botoes>
      <button class=principal id=bcap>Capturar agora</button>
      <button id=bref>Atualizar</button>
      <button id=bmedir>Medir delay (5x)</button>
    </div>
    <div class=barra><i id=prog></i></div>
    <hr>
    <h2>Transporte e taxa</h2>
    <div class=botoes>
      <button id=btxt>Texto (base64)</button>
      <button id=bbin>Binario</button>
    </div>
    <div class=botoes>
      <button id=b921>921600</button>
      <button id=b1000>1 Mbps</button>
      <button id=b1500>1,5 Mbps</button>
      <button id=b2000>2 Mbps (corrompe)</button>
    </div>
    <div id=nota-transp style="color:var(--fraco);font-size:13px;margin-top:8px"></div>
  </section>
  <section class=painel>
    <h2>Linha do tempo</h2>
    <ul id=eventos><li><span class=h>--:--:--</span> aguardando eventos</li></ul>
    <hr>
    <h2>Estado</h2>
    <dl id=estado></dl>
    <div class=botoes>
      <button id=bstatus>Pedir status</button>
      <button id=bsensor>Testar energia</button>
    </div>
    <pre id=log>aguardando log&hellip;</pre>
  </section>
</main>
<script>
const $ = (id) => document.getElementById(id);
let framesOk = -1, capturasVistas = -1, ocupado = false;

function momento(j) {
  const c = (j.capturas && j.capturas.ultima) || {};
  const d = (j.delay && j.delay.ultimo) || {};
  if (!c.arquivo) return 'sem captura ainda &mdash; passe um objeto no sensor ou clique em Capturar agora';
  const hora = c.hora || '--:--:--';
  const partes = [`capturada <b>${hora}</b>`];
  if (d.ext_ref) partes.push(`trigger <b>n=${d.ext_ref}</b>`);
  if (d.sensor_foto_ms != null) partes.push(`delay <b>${d.sensor_foto_ms} ms</b>`);
  partes.push(`<span class=fraco>${c.arquivo} (${((c.bytes||0)/1024).toFixed(1)} kB)</span>`);
  return partes.join(' &middot; ');
}

function timeline(j) {
  const ev = j.eventos || [];
  if (!ev.length) { $('eventos').innerHTML = '<li><span class=h>--:--:--</span> aguardando eventos</li>'; return; }
  $('eventos').innerHTML = ev.map(e =>
    `<li><span class=h>${e.t}</span><span class=${e.tipo}>${e.texto}</span></li>`).join('');
}

async function estado() {
  try {
    const j = await (await fetch('/status', {cache:'no-store'})).json();
    // foto nova? entao mostra, mesmo que ninguem tenha clicado em nada
    const total = (j.capturas && j.capturas.total) || 0;
    if (framesOk !== -1 && (j.frames_ok > framesOk || total > capturasVistas)) {
      const img = $('foto');
      img.src = '/frame.jpg?t=' + Date.now();
      img.classList.add('nova');
      setTimeout(() => img.classList.remove('nova'), 900);
    }
    framesOk = j.frames_ok;
    capturasVistas = total;
    $('momento').innerHTML = momento(j);
    timeline(j);

    const m = j.meta || {}, d = j.delay || {};
    const linhas = [
      ['sensor (E18 no outro ESP)', j.sensor.nivel == null ? 'sem leitura ainda'
        : (j.sensor.nivel === 0 ? `OBJETO detectado (nivel 0, ha ${j.sensor.idade_s}s)`
                                : `repouso (nivel 1, ha ${j.sensor.idade_s}s)`)],
      ['  pinos medidos', Object.entries(j.sensor.pinos || {}).map(([k,v]) => `${k}=${v}`).join('  ')],
      ['no de trigger', j.trigger.aberta ? `${j.trigger.estado} (ultimo n=${j.trigger.ultimo_n ?? '-'}, ${j.trigger.total} eventos)` : 'porta fechada'],
      ['camera', j.camera === 'standby' ? 'standby (desligada entre fotos)' : j.camera],
      ['transporte', `${j.transport} @ ${j.baud} baud`],
      ['frames', `${j.frames_ok} (texto ${j.frames_text} / bin ${j.frames_bin})`],
      ['delay sensor->foto', d.n ? `${d.media_ms} ms medio (min ${d.min_ms} / max ${d.max_ms}, n=${d.n})` : '-'],
      ['  ultimo: comando->foto', d.ultimo && d.ultimo.comando_foto_ms != null ? `${d.ultimo.comando_foto_ms} ms` : '-'],
      ['  ultimo: foto->arquivo', d.ultimo && d.ultimo.foto_arquivo_ms != null ? `${d.ultimo.foto_arquivo_ms} ms` : '-'],
      ['  camera interna', d.ultimo && d.ultimo.camera_total_ms ? `${d.ultimo.camera_total_ms} ms (linha ${d.ultimo.camera_linha_ms} ms)` : '-'],
      ['pareamento', j.pareamento && j.pareamento.status ? `${j.pareamento.status} (trigger n=${j.pareamento.trigger_n ?? '-'} -> ext_ref=${j.pareamento.ext_ref ?? '-'})` : 'sem dado'],
      ['capturas em disco', j.capturas.total ? `${j.capturas.total} em ${j.capturas.dir}` : 'nenhuma ainda'],
      ['ultimo frame', m.event != null ? `evento ${m.event}, ${((m.len||0)/1024).toFixed(1)} kB, crc ${m.crc32||'-'}, ${m.crosscheck||'-'}` : '-'],
    ];
    $('estado').innerHTML = linhas.map(([k,v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
    $('btxt').className = j.transport === 'text' ? 'ativo' : '';
    $('bbin').className = j.transport === 'bin' ? 'ativo' : '';
    const cls = j.serial_open ? (j.booted ? 'ok' : 'aviso') : 'erro';
    $('sub').innerHTML = `<span class=${cls}>${j.serial_open ? (j.booted ? 'camera pronta' : 'serial aberta') : 'sem serial'}</span>`
      + ` &middot; ${j.transport} &middot; ${j.frames_ok} fotos &middot; trigger ${j.trigger.estado}`
      + ` &middot; sensor ${j.sensor.nivel == null ? '?' : (j.sensor.nivel === 0 ? 'OBJETO' : 'repouso')}`
      + (j.serial_last_error ? ` &middot; <span class=erro>${j.serial_last_error}</span>` : '');
  } catch (e) {
    $('sub').innerHTML = '<span class=erro>site fora do ar</span>';
  }
}

async function log() {
  try {
    const t = await (await fetch('/log', {cache:'no-store'})).text();
    const pre = $('log');
    const fim = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 30;
    pre.textContent = t || 'sem linhas';
    if (fim) pre.scrollTop = pre.scrollHeight;
  } catch (e) {}
}

function esperar(antes) {
  return new Promise((resolve) => {
    let n = 0;
    const t = setInterval(async () => {
      n += 1;
      $('prog').style.width = Math.min(100, n * 8) + '%';
      try {
        const j = await (await fetch('/status', {cache:'no-store'})).json();
        if (j.frames_ok > antes) { clearInterval(t); resolve(true); return; }
        if (j.serial_open === false) { clearInterval(t); resolve(false); return; }
      } catch (e) {}
      if (n > 40) { clearInterval(t); resolve(false); }
    }, 250);
  });
}

async function capturar() {
  if (ocupado) return;
  ocupado = true;
  $('bcap').disabled = true;
  let chegou = false, tentativas = 0;
  try {
    while (tentativas < 2 && !chegou) {
      tentativas += 1;
      $('bcap').textContent = tentativas === 1 ? 'capturando...' : 'recapturando...';
      $('prog').style.width = '4%';
      const antes = framesOk;
      await fetch('/capture', {method:'POST'});
      chegou = await esperar(antes);
    }
    if (!chegou) $('sub').innerHTML = '<span class=erro>duas tentativas sem frame valido</span>';
  } finally {
    $('prog').style.width = '0';
    $('bcap').disabled = false;
    $('bcap').textContent = 'Capturar agora';
    ocupado = false;
    estado(); log();
  }
}

async function comando(nome) {
  try { await fetch('/cmd?name=' + encodeURIComponent(nome), {method:'POST'}); } catch (e) {}
  setTimeout(() => { log(); estado(); }, 700);
}

$('bcap').onclick = capturar;
$('bref').onclick = () => { $('foto').src = '/frame.jpg?t=' + Date.now(); estado(); log(); };
$('bstatus').onclick = () => comando('CMD_STATUS');
$('bsensor').onclick = () => comando('CMD_SENSOR');
$('btxt').onclick = () => comando('CMD_TRANSPORT TEXT');
$('bbin').onclick = () => comando('CMD_TRANSPORT BIN');
async function trocarBaud(valor) {
  try { await fetch('/baud?valor=' + valor, {method:'POST'}); } catch (e) {}
  setTimeout(() => { log(); estado(); }, 1500);
}
$('b921').onclick = () => trocarBaud(921600);
$('b1000').onclick = () => trocarBaud(1000000);
$('b1500').onclick = () => trocarBaud(1500000);
$('b2000').onclick = () => trocarBaud(2000000);
async function medirDelay() {
  $('bmedir').disabled = true; $('bmedir').textContent = 'medindo...';
  try { await fetch('/medir?n=5', {method:'POST'}); } catch (e) {}
  setTimeout(() => { $('bmedir').disabled = false; $('bmedir').textContent = 'Medir delay (5x)'; estado(); log(); }, 22000);
}
$('bmedir').onclick = medirDelay;
let tentativasImagem = 0;
$('foto').onerror = () => {
  if (tentativasImagem++ < 3) setTimeout(() => { $('foto').src = '/frame.jpg?t=' + Date.now(); }, 2000);
};
$('foto').src = '/frame.jpg';
estado(); log();
setInterval(estado, 1000);
setInterval(log, 1500);
</script>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "esp32cam-site/3.0"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _text(self, status: int, text: str) -> None:
        self._send(status, text.encode("utf-8"), "text/plain; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path in ("/frame.jpg", "/capture"):
            with lock:
                frame = latest
            if frame is None:
                self._text(503, "sem frame valido ainda\n")
                return
            self._send(200, frame, "image/jpeg")
            return
        if path == "/status":
            self._send(200, json.dumps(snapshot(), ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
            return
        if path == "/health":
            snap = snapshot()
            lines = [f"{k}={snap[k]}" for k in
                     ("frames_ok", "frames_bad", "frames_text", "frames_bin",
                      "serial_bytes", "serial_open", "booted", "transport")]
            # o caminho binario nao usa frames_bad: sem estes, um monitor de
            # /health via frames_bad=0 num enlace que esta perdendo frames
            for k in ("lacunas", "rejeitados", "duplicados"):
                lines.append(f"assembler_{k}={snap['assembler'][k]}")
            lines.append(f"payload_ruim={snap['decoder']['payload_ruim']}")
            lines.append(f"hdr_ruim={snap['decoder']['hdr_ruim']}")
            # evidencia em disco: sem isto um monitor nao ve' que a gravacao parou
            # rotulo da SESSAO: o disco pode ter capturas de execucoes anteriores
            # (/capturas mostra o total real do diretorio)
            lines.append(f"capturas_sessao={snap['capturas']['total']}")
            lines.append(f"capturas_bytes_sessao={snap['capturas']['bytes_sessao']}")
            self._text(200, "\n".join(lines) + "\n")
            return
        if path == "/capturas":
            if capturas_dir is None:
                self._text(404, "gravacao desativada\n")
                return
            # 30 mais novos sem ordenar o diretorio inteiro: com centenas de
            # capturas a listagem antiga fazia O(n log n) + n syscalls por request
            entradas = [e for e in os.scandir(capturas_dir)
                        if e.name.endswith(".jpg") and e.is_file()]
            novos = heapq.nlargest(30, entradas, key=lambda e: e.stat().st_mtime)
            linhas = [f"{e.name}  {e.stat().st_size} B" for e in novos]
            corpo = "\n".join(linhas) or "nenhuma captura ainda"
            corpo += f"\n-- {len(entradas)} capturas no total"
            self._text(200, corpo + "\n")
            return
        if path.startswith("/capturas/"):
            nome = path.split("/", 2)[2]
            if capturas_dir is None or not NOME_SEGURO.match(nome) or not nome.endswith(".jpg"):
                self._text(400, "nome invalido\n")
                return
            alvo = (capturas_dir / nome).resolve()
            if capturas_dir.resolve() not in alvo.parents or not alvo.is_file():
                self._text(404, "captura nao encontrada\n")
                return
            self._send(200, alvo.read_bytes(), "image/jpeg")
            return
        if path == "/log":
            with lock:
                recent = list(log_lines)[-160:]
            self._text(200, "\n".join(recent) + ("\n" if recent else ""))
            return
        self._text(404, "rota desconhecida\n")

    def _autorizado(self, parsed) -> bool:
        """Token opcional para os POST destrutivos (captura, comando, baud).

        Sem --token o comportamento e' o de antes (LAN aberta): o aviso sai no
        boot para isso ser uma decisao visivel, nao um esquecimento.
        """
        if not TOKEN:
            return True
        cabecalho = self.headers.get("X-Token") or ""
        query = (parse_qs(parsed.query).get("token") or [""])[0]
        return cabecalho == TOKEN or query == TOKEN

    def do_POST(self) -> None:
        global trigger_delay_ms, trigger_delay_saved_at
        global trigger_ultimo_n, trigger_ultimo_em, trigger_total, transport_desejado
        global baud_pendente, baud_troca_em
        agendar_baud: int | None = None
        parsed = urlparse(self.path)
        if not self._autorizado(parsed):
            self._text(401, "token ausente ou invalido\n")
            return
        if parsed.path == "/capture":
            name = "CMD_CAPTURE"
        elif parsed.path == "/cmd":
            name = (parse_qs(parsed.query).get("name") or [""])[0].upper()
            # o firmware quebra comandos por 0x0A: uma quebra de linha na URL
            # executa um segundo comando (injecao). Rejeita antes de qualquer coisa.
            if "\n" in name or "\r" in name:
                self._text(400, "comando com quebra de linha\n")
                return
            if name.startswith("CMD_TRANSPORT "):
                escolha = name.split(" ", 1)[1].lower()
                if escolha not in ("text", "bin"):
                    self._text(400, "transporte invalido (text|bin)\n")
                    return
                transport_desejado = escolha
            if name.startswith("CMD_BAUD ") and not re.fullmatch(r"CMD_BAUD \d{4,7}", name):
                self._text(400, "CMD_BAUD exige numero de 4 a 7 digitos\n")
                return
        elif parsed.path == "/medir":
            consulta = parse_qs(parsed.query)
            n = int((consulta.get("n") or ["5"])[0]) if (consulta.get("n") or ["5"])[0].isdigit() else 5
            n = max(1, min(n, 10))
            threading.Thread(target=serie_medicao, args=(n,), daemon=True).start()
            self._text(202, f"serie de {n} disparos iniciada\n")
            return
        elif parsed.path == "/simular":
            consulta = parse_qs(parsed.query)
            n = (consulta.get("n") or [""])[0]
            if not n.isdigit():
                self._text(400, "informe n=<numero>\n")
                return
            ref = int(n)
            with lock:
                trigger_ultimo_n = ref
                trigger_ultimo_em = time.time()
                trigger_total += 1
            log("TRIG", f"EV OPEN n={ref} (simulado na bancada)")
            evento("sensor", f"trigger simulado n={ref} (bancada)", ext_ref=ref)
            disparar_camera(ref)
            self._text(202, f"trigger simulado n={ref}\n")
            return
        elif parsed.path == "/teste-delay":
            global last_delay_test
            inicio_epoch = time.time()
            inicio = time.monotonic()
            time.sleep(max(0, trigger_delay_ms) / 1000.0)
            fim_epoch = time.time()
            medido = round((time.monotonic() - inicio) * 1000)
            last_delay_test = {"configurado_ms": trigger_delay_ms,
                               "inicio_epoch": inicio_epoch, "fim_epoch": fim_epoch,
                               "medido_ms": medido}
            self._text(200, f"TRIGGER_DELAY_TEST configurado={trigger_delay_ms} medido={medido} inicio={inicio_epoch:.3f} fim={fim_epoch:.3f}\n")
        elif parsed.path == "/delay":
            raw = (parse_qs(parsed.query).get("ms") or [""])[0]
            try:
                novo_delay = int(raw)
                if not 0 <= novo_delay <= 30000:
                    raise ValueError
            except ValueError:
                self._text(400, "delay invalido (0..30000 ms)\n")
                return
            trigger_delay_ms = novo_delay
            trigger_delay_saved_at = time.time()
            self._text(202, f"TRIGGER_DELAY_MS {novo_delay} saved_at={trigger_delay_saved_at:.3f}\n")
        elif parsed.path == "/baud":
            consulta = parse_qs(parsed.query)
            valor = (consulta.get("valor") or [""])[0]
            if not valor.isdigit() or not 9600 <= int(valor) <= 3000000:
                self._text(400, "baud invalido (9600..3000000)\n")
                return
            name = f"CMD_BAUD {int(valor)}"
            agendar_baud = int(valor)
        else:
            self._text(404, "rota desconhecida\n")
            return
        if name not in ALLOWED_COMMANDS and not name.startswith(ALLOWED_PREFIXES):
            self._text(400, f"comando nao permitido: {name!r}\n")
            return
        with lock:
            ready = serial_open
        if not ready:
            self._text(503, "serial indisponivel\n")
            return
        try:
            command_queue.put_nowait(name.encode("ascii") + bytes([10]))
        except Full:
            self._text(429, "fila de comandos cheia\n")
            return
        self._text(202, f"{name} enfileirado\n")
        if agendar_baud is not None:
            # So depois do comando entrar na fila: o recuo (trocar mesmo com ACK
            # ilegivel) existe para nao deixar os dois lados em taxas diferentes,
            # mas nao pode agendar uma troca que a camera nunca recebeu.
            baud_pendente = agendar_baud
            baud_troca_em = time.time() + 2.0


def serie_medicao(n: int) -> None:
    """Dispara N triggers sinteticos espacados para medir o delay (bancada)."""
    global delay_serie_ativa, trigger_ultimo_n, trigger_ultimo_em, trigger_total
    with lock:
        if delay_serie_ativa:
            log("DELAY", "serie de medicao ja em andamento; pedido ignorado")
            return
        delay_serie_ativa = True
    log("DELAY", f"serie de medicao iniciada ({n} disparos)")
    try:
        for i in range(n):
            with lock:
                ref = 9000 + i
                trigger_ultimo_n = ref
                trigger_ultimo_em = time.time()
                trigger_total += 1
            disparar_camera(ref)
            time.sleep(4.0)
    finally:
        with lock:
            delay_serie_ativa = False
        with lock:
            if latencias:
                ultimos = list(latencias)[-n:]
                media = sum(int(x["sensor_foto_ms"]) for x in ultimos) / len(ultimos)
                log("DELAY", f"serie concluida: media {media:.0f} ms em {len(ultimos)} disparos")
            else:
                log("DELAY", "serie concluida sem amostras")


def poller_status() -> None:
    """Status periodico: o painel precisa mostrar standby sem o usuario clicar,
    e o estado so muda quando o firmware responde a um CMD_STATUS."""
    while True:
        time.sleep(8)
        with lock:
            pronto = serial_open
        if pronto:
            try:
                command_queue.put_nowait(b"CMD_STATUS" + bytes([10]))
            except Full:
                pass


def main() -> None:
    global baud_atual
    ap = argparse.ArgumentParser()
    # 8091 passou a ser do container label-studio (docker-proxy)
    ap.add_argument("--porta", type=int, default=8094)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--serial", default="/dev/ttyUSB0")
    ap.add_argument("--serial-trigger", default="/dev/ttyUSB1")
    ap.add_argument("--baud-trigger", type=int, default=TRIGGER_BAUD)
    ap.add_argument("--capturas", default=str(Path.home() / "pnaat-capturas"),
                    help="diretorio das fotos gravadas (vazio desliga a gravacao)")
    ap.add_argument("--sem-trigger", action="store_true",
                    help="roda so com o no da camera (sem a ponte do trigger)")
    ap.add_argument("--baud", type=int, default=SERIAL_BAUD)
    ap.add_argument("--token", default="",
                    help="exige ?token= ou X-Token nos POST destrutivos")
    args = ap.parse_args()
    baud_atual = args.baud
    global capturas_dir, TOKEN
    capturas_dir = Path(args.capturas).expanduser() if args.capturas else None
    TOKEN = args.token
    if not TOKEN and args.host in ("0.0.0.0", ""):
        print("AVISO: /capture /cmd /simular /baud aceitam POST de qualquer host da rede; "
              "use --token para exigir X-Token")

    threading.Thread(target=serial_reader, args=(args.serial,), daemon=True).start()
    threading.Thread(target=poller_status, daemon=True).start()
    if not args.sem_trigger:
        threading.Thread(target=trigger_reader,
                         args=(args.serial_trigger, args.baud_trigger), daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.porta), Handler)
    print(f"ESP32CAM_SITE http://{args.host}:{args.porta}/ camera={args.serial}@{args.baud} "
          f"trigger={'off' if args.sem_trigger else args.serial_trigger + '@' + str(args.baud_trigger)}",
          flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
