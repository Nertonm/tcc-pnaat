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
import json
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transport_bin import Decoder, FrameAssembler  # noqa: E402

SERIAL_BAUD = 921600
ALLOWED_COMMANDS = ("CMD_CAPTURE", "CMD_STATUS", "CMD_SENSOR",
                    "CMD_TRANSPORT BIN", "CMD_TRANSPORT TEXT",
                    "CMD_TEST_FALHA_INIT")
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
    r"FRAME_INFO source=(\S+) event=(\d+) trigger_us=(-?\d+) len=(\d+) crc32=([0-9a-f]{8})"
)
END_BIN_RE = re.compile(r"FRAME_END_BIN event=(\d+) tx_us=(\d+) total_us=(\d+) chunks=(\d+)")

# Tabela de sanear logs: qualquer byte fora de 32..126 vira "." (via C, por byte)
_SANITIZE = bytes(0x2E if not (32 <= b < 127) else b for b in range(256))
TRANSPORT_RE = re.compile(r"TRANSPORT mode=(\w+)")
STATUS_RE = re.compile(r"STATUS camera=(\w+) driver=(\d+) power_en=(-?\d+) "
                       r"armed=(\d+) transport=(\w+) baud=(\d+)")


def _e_residuo(linha: bytes) -> bool:
    """Bytes que nao sao mensagem binaria nem log: o decoder os devolve como
    'text'. Se a linha e' majoritariamente nao imprimivel, nao e' log."""
    if not linha:
        return True
    ruins = sum(1 for b in linha if not (32 <= b < 127))
    return ruins / len(linha) > 0.3

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
announced: dict[int, tuple[int, int]] = {}


def log(kind: str, text: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    log_lines.append(f"{stamp} [{kind}] {text}")


def publish(frame: bytes, event: int, encoding: str, extra: dict[str, object]) -> None:
    global latest, latest_meta, frames_ok, frames_text, frames_bin, crosscheck
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
            anunciado_len, anunciado_crc = esperado
            ok = (anunciado_len == len(frame) and f"{anunciado_crc:08x}" == crc)
            crosscheck = {"status": "ok" if ok else "DIVERGENTE", "event": event,
                          "anunciado_len": anunciado_len,
                          "anunciado_crc32": f"{anunciado_crc:08x}",
                          "calculado_len": len(frame)}
        latest_meta["crosscheck"] = crosscheck["status"]
        estado_cc = crosscheck["status"]
    log("FRAME", f"encoding={encoding} event={event} {len(frame)}B "
                 f"crc32={crc} crosscheck={estado_cc}")


def handle_text(data: bytes) -> None:
    """Linhas ASCII: logs e, no modo texto, o frame base64."""
    global pending_header, frames_bad, booted, transport, serial_lines
    global baud_atual, baud_pendente, baud_troca_em, camera_estado, driver_estado
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
            announced[int(info.group(2))] = (int(info.group(4)), int(info.group(5), 16))
        fim_bin = END_BIN_RE.search(text)
        if fim_bin:
            evento = int(fim_bin.group(1))
            with lock:
                if latest_meta.get("event") == evento:
                    latest_meta["tx_us"] = int(fim_bin.group(2))
                    latest_meta["total_us"] = int(fim_bin.group(3))
                    latest_meta["chunks_reportados"] = int(fim_bin.group(4))
        if "TASKS_READY" in text:
            booted = True
        # Em modo binario a linha do firmware chega colada a residuo binario
        # ("...`.TRANSPORT mode=bin"), entao a deteccao tem de ser por busca.
        modo = TRANSPORT_RE.search(text)
        if modo:
            transport = modo.group(1)
        estado_no = STATUS_RE.search(text)
        if estado_no:
            with lock:
                camera_estado = estado_no.group(1)
                driver_estado = int(estado_no.group(2))
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
    publish(frame, int(header.group(2)), "text", {
        "source": header.group(1).decode("ascii"),
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
    publish(frame, msg.event_id, "bin", {
        "source": "bin",
        "chunks": assembler.expect_seq,
        "bytes_enquadramento": 19 * mensagens,    # 15 B de cabecalho + 4 B de CRC por mensagem
    })


def serial_reader(port_name: str) -> None:
    global serial_bytes, serial_lines, serial_last_error, serial_open, booted
    global serial_port, baud_atual, baud_pendente
    while True:
        try:
            port = serial.Serial(port=None, rtscts=False, dsrdtr=False, exclusive=True)
            port.port = port_name
            port.baudrate = baud_atual
            port.timeout = 0.2
            port.dtr = False
            port.rts = False
            port.open()
            with lock:
                serial_open = True
                booted = False
                serial_port = port
            log("SERIAL", f"aberta {port_name} @ {baud_atual}")
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
        except (serial.SerialException, OSError) as exc:
            with lock:
                serial_open = False
                booted = False
                serial_last_error = repr(exc)
            log("SERIAL", f"reconectando: {exc}")
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
 header{padding:18px 22px;border-bottom:1px solid var(--regra);display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
 header h1{font-size:17px;margin:0}
 header .sub{color:var(--fraco);font-size:13px}
 main{max-width:1180px;margin:0 auto;padding:22px;display:grid;gap:18px;grid-template-columns:1.35fr 1fr}
 @media(max-width:920px){main{grid-template-columns:1fr}}
 .painel{background:var(--painel);border:1px solid var(--regra);border-radius:10px;padding:16px}
 h2{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--azul);margin:0 0 12px}
 img{width:100%;border-radius:6px;background:#000;display:block;min-height:220px;object-fit:contain}
 .botoes{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
 button{font:inherit;font-weight:600;padding:9px 14px;border-radius:8px;border:1px solid var(--regra);
        background:#202833;color:var(--texto);cursor:pointer}
 button.principal{background:var(--azul);border-color:var(--azul);color:#08111a}
 button.ativo{background:var(--verde);border-color:var(--verde);color:#08111a}
 button:disabled{opacity:.5;cursor:progress}
 dl{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin:0;font-size:13.5px}
 dt{color:var(--fraco)}
 dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
 pre{margin:12px 0 0;background:#0b0e12;border:1px solid var(--regra);border-radius:8px;padding:10px;
     height:240px;overflow:auto;font-size:12.5px;line-height:1.45;white-space:pre-wrap}
 .ok{color:var(--verde)}.aviso{color:var(--ambar)}.erro{color:var(--vermelho)}
 .barra{height:5px;border-radius:3px;background:var(--regra);overflow:hidden;margin-top:10px}
 .barra i{display:block;height:100%;width:0;background:var(--azul);transition:width .25s}
 hr{border:0;border-top:1px solid var(--regra);margin:14px 0}
</style>
<header>
  <h1>ESP32-CAM &mdash; captura sob demanda</h1>
  <span class=sub id=sub>carregando&hellip;</span>
</header>
<main>
  <section class=painel>
    <h2>Ultima captura</h2>
    <img id=foto alt='frame da ESP32-CAM'>
    <div class=botoes>
      <button class=principal id=bcap>Capturar</button>
      <button id=bref>Atualizar</button>
    </div>
    <div class=barra><i id=prog></i></div>
    <hr>
    <h2>Transporte</h2>
    <div class=botoes>
      <button id=btxt>Texto (base64)</button>
      <button id=bbin>Binario enquadrado</button>
    </div>
    <div class=botoes>
      <button id=b921>921600 baud</button>
      <button id=b1000>1 Mbps</button>
      <button id=b1500>1,5 Mbps (mais rapido; perda ocasional)</button>
      <button id=b2000>2 Mbps (corrompe: 0/6)</button>
    </div>
    <div class=nota id=nota-transp style="color:var(--fraco);font-size:13px;margin-top:8px"></div>
  </section>
  <section class=painel>
    <h2>Estado do no</h2>
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
let framesOk = 0, ocupado = false;

async function estado() {
  try {
    const j = await (await fetch('/status', {cache:'no-store'})).json();
    framesOk = j.frames_ok;
    const m = j.meta || {};
    const cc = j.crosscheck || {};
    const linhas = [
      ['serial', j.serial_open ? (j.booted ? 'aberta, firmware pronto' : 'aberta, sem boot') : 'fechada'],
      ['camera', j.camera === 'standby' ? 'standby (desligada entre fotos)' : j.camera],
      ['driver', j.driver === 0 ? 'nenhum residente' : j.driver],
      ['transporte', `${j.transport} @ ${j.baud} baud`],
      ['frames', `${j.frames_ok} (texto ${j.frames_text} / bin ${j.frames_bin})`],
      ['frames rejeitados', j.frames_bad],
      ['ultimo evento', m.event ?? '-'],
      ['ultimo encoding', m.encoding ?? '-'],
      ['tamanho', m.len ? (m.len/1024).toFixed(1) + ' kB' : '-'],
      ['crc32 (host)', m.crc32 ?? '-'],
      ['anuncio x host', cc.status ?? '-'],
      ['captura', m.capture_us ? (m.capture_us/1000).toFixed(1) + ' ms' : '-'],
      ['total do evento', m.total_us ? (m.total_us/1000).toFixed(1) + ' ms' : '-'],
      ['bytes lidos', ((j.serial_bytes||0)/1024).toFixed(0) + ' kB'],
      ['decoder', `${j.decoder.aceitas} ok, ${j.decoder.payload_ruim} payload ruim, ${j.decoder.descartados} bytes descartados`],
      ['montador', `${j.assembler.frames} frames, ${j.assembler.lacunas} lacunas, ${j.assembler.rejeitados} rejeitados`],
    ];
    $('estado').innerHTML = linhas.map(([k,v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
    $('btxt').className = j.transport === 'text' ? 'ativo' : '';
    $('bbin').className = j.transport === 'bin' ? 'ativo' : '';
    $('nota-transp').textContent = j.transport === 'bin'
      ? 'binario: ~20 B de enquadramento por chunk de 1024 B'
      : 'texto: base64 + prefixo por linha (~2,1x o JPEG na linha)';
    const cls = j.serial_open ? (j.booted ? 'ok' : 'aviso') : 'erro';
    $('sub').innerHTML = `<span class=${cls}>${j.serial_open ? (j.booted ? 'no pronto' : 'serial aberta') : 'sem serial'}</span>`
      + ` &middot; ${j.transport} &middot; ${j.frames_ok} frames`;
    if ((j.assembler.ultimo_erro || '').length) {
      $('sub').innerHTML += ` &middot; <span class=erro>${j.assembler.ultimo_erro}</span>`;
    }
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
    // O transporte e' fail-closed: frame rejeitado por CRC nao e' publicado.
    // Em vez de mostrar imagem velha, tenta uma segunda vez e diz o que houve.
    while (tentativas < 2 && !chegou) {
      tentativas += 1;
      $('bcap').textContent = tentativas === 1 ? 'capturando...' : 'recapturando...';
      $('prog').style.width = '4%';
      const antes = framesOk;
      await fetch('/capture', {method:'POST'});
      chegou = await esperar(antes);
    }
    if (!chegou) {
      $('sub').innerHTML = '<span class=erro>duas tentativas sem frame valido</span>';
    } else if (tentativas > 1) {
      $('sub').innerHTML = '<span class=aviso>frame recuperado na segunda tentativa</span>';
    }
  } finally {
    $('prog').style.width = '0';
    $('bcap').disabled = false;
    $('bcap').textContent = 'Capturar';
    ocupado = false;
    if (chegou) $('foto').src = '/frame.jpg?t=' + Date.now();
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
$('foto').src = '/frame.jpg';
estado(); log();
setInterval(estado, 2000);
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
            self._text(200, "\n".join(lines) + "\n")
            return
        if path == "/log":
            with lock:
                recent = list(log_lines)[-160:]
            self._text(200, "\n".join(recent) + ("\n" if recent else ""))
            return
        self._text(404, "rota desconhecida\n")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/capture":
            name = "CMD_CAPTURE"
        elif parsed.path == "/cmd":
            name = (parse_qs(parsed.query).get("name") or [""])[0].upper()
        elif parsed.path == "/baud":
            consulta = parse_qs(parsed.query)
            valor = (consulta.get("valor") or [""])[0]
            if not valor.isdigit() or not 9600 <= int(valor) <= 3000000:
                self._text(400, "baud invalido (9600..3000000)\n")
                return
            name = f"CMD_BAUD {int(valor)}"
            # Recuo: se o ACK chegar ilegivel (baud ruim), o host troca mesmo
            # assim no prazo — senao os dois lados ficam em taxas diferentes e o
            # enlace morre sem caminho de volta.
            global baud_pendente, baud_troca_em
            baud_pendente = int(valor)
            baud_troca_em = time.time() + 2.0
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
    ap.add_argument("--porta", type=int, default=8091)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--serial", default="/dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=SERIAL_BAUD)
    args = ap.parse_args()
    baud_atual = args.baud

    threading.Thread(target=serial_reader, args=(args.serial,), daemon=True).start()
    threading.Thread(target=poller_status, daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.porta), Handler)
    print(f"ESP32CAM_SITE http://{args.host}:{args.porta}/ serial={args.serial} baud={args.baud}",
          flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
