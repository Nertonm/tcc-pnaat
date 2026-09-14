#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import re
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Full, Queue

import serial

SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 921600
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8091

BEGIN_RE = re.compile(
    rb"FRAME_BEGIN v=1 encoding=base64 source=([a-z0-9_]+) event=(\d+) trigger_us=(\d+) "
    rb"len=(\d+) crc32=([0-9a-f]+) wake_us=(\d+) warmup_us=(\d+) capture_us=(\d+)"
)
DATA_RE = re.compile(rb"FRAME_DATA event=(\d+) seq=(\d+) data=([A-Za-z0-9+/=]+)")
END_RE = re.compile(rb"FRAME_END event=(\d+) tx_us=(\d+) total_us=(\d+)")

state_lock = threading.Lock()
latest: bytes | None = None
latest_meta: dict[str, int] = {}
frames_ok = 0
frames_bad = 0
serial_bytes = 0
serial_lines = 0
serial_last_error = ""
serial_port: serial.Serial | None = None
serial_port_lock = threading.Lock()
command_queue: Queue[bytes] = Queue(maxsize=1)
history: deque[tuple[float, bytes]] = deque(maxlen=4)


def publish_frame(header: re.Match[bytes], chunks: dict[int, bytes], end: re.Match[bytes]) -> None:
    global latest, latest_meta, frames_ok, frames_bad
    try:
        expected_len = int(header.group(4))
        expected_crc = int(header.group(5), 16)
        frame = base64.b64decode(b"".join(chunks[i] for i in sorted(chunks)), validate=True)
        actual_crc = binascii.crc32(frame) & 0xFFFFFFFF
        if (len(frame) != expected_len or frame[:2] != b"\xff\xd8"
                or frame[-2:] != b"\xff\xd9" or actual_crc != expected_crc):
            raise ValueError("frame gate failed")
        meta = {
            "source": header.group(1).decode("ascii"),
            "event": int(header.group(2)),
            "trigger_us": int(header.group(3)),
            "len": expected_len,
            "crc32": actual_crc,
            "wake_us": int(header.group(6)),
            "warmup_us": int(header.group(7)),
            "capture_us": int(header.group(8)),
            "tx_us": int(end.group(2)),
            "total_us": int(end.group(3)),
        }
    except (ValueError, KeyError, binascii.Error):
        with state_lock:
            frames_bad += 1
        return
    with state_lock:
        latest = frame
        latest_meta = meta
        frames_ok += 1
        history.append((time.monotonic(), frame))


def serial_reader() -> None:
    global serial_bytes, serial_lines, serial_last_error, serial_port
    while True:
        try:
            port = serial.Serial(port=None, rtscts=False, dsrdtr=False, exclusive=True)
            port.port = SERIAL_PORT
            port.baudrate = SERIAL_BAUD
            port.timeout = 1
            port.dtr = False
            port.rts = False
            port.open()
            with serial_port_lock:
                serial_port = port
            try:
                pending_header: re.Match[bytes] | None = None
                chunks: dict[int, bytes] = {}
                while True:
                    try:
                        port.write(command_queue.get_nowait())
                        port.flush()
                    except Empty:
                        pass
                    line = port.readline().strip()
                    serial_bytes += len(line)
                    serial_lines += 1
                    if not line:
                        continue
                    begin = BEGIN_RE.search(line)
                    if begin:
                        pending_header = begin
                        chunks = {}
                        continue
                    if pending_header is None:
                        continue
                    data = DATA_RE.fullmatch(line)
                    if data and int(data.group(1)) == int(pending_header.group(2)):
                        chunks[int(data.group(2))] = data.group(3)
                        continue
                    end = END_RE.fullmatch(line)
                    if end and int(end.group(1)) == int(pending_header.group(2)):
                        publish_frame(pending_header, chunks, end)
                        pending_header = None
                        chunks = {}
            finally:
                with serial_port_lock:
                    serial_port = None
                port.close()
        except (serial.SerialException, OSError) as exc:
            serial_last_error = repr(exc)
            print(f"serial reconnect: {exc}", flush=True)
            time.sleep(1)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        print(fmt % args, flush=True)

    def _send_text(self, status: int, body: str) -> None:
        payload = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        if self.path != "/capture":
            self.send_error(404)
            return
        with serial_port_lock:
            if serial_port is None or not serial_port.is_open:
                self._send_text(503, "serial unavailable\n")
                return
            try:
                command_queue.put_nowait(b"CMD_CAPTURE\n")
            except Full:
                self._send_text(429, "capture already queued\n")
                return
        self._send_text(202, "capture queued\n")

    def do_GET(self) -> None:
        if self.path == "/":
            body = ("<!doctype html><meta name=viewport content='width=device-width'>"
                    "<title>ESP32-CAM USB</title><h1>ESP32-CAM USB</h1>"
                    "<button onclick=shot()>Capturar</button>"
                    "<a href='/health'>Health</a><p id=s>Pronto</p>"
                    "<img id=i style='max-width:100%;height:auto'>"
                    "<script>async function health(){let r=await fetch('/health');return (await r.text()).match(/frames_ok=(\\d+)/)[1]}"
                    "async function shot(){s.textContent='capturando...';let before=await health();"
                    "let r=await fetch('/capture',{method:'POST'});if(!r.ok){s.textContent=await r.text();return}"
                    "for(let n=0;n<40;n++){await new Promise(x=>setTimeout(x,100));"
                    "if((await health())>before){s.textContent='captura concluída';"
                    "i.src='/capture?t='+Date.now();return}}s.textContent='timeout'}"
                    "i.src='/capture';</script>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/capture"):
            with state_lock:
                frame = latest
            if frame is None:
                self.send_error(503, "no valid frame yet")
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
            return
        if self.path == "/health":
            with state_lock:
                meta = dict(latest_meta)
                ok = frames_ok
                bad = frames_bad
                received_bytes = serial_bytes
                received_lines = serial_lines
                last_error = serial_last_error
            body = (f"frames_ok={ok}\nframes_bad={bad}\nserial_bytes={received_bytes}\n"
                    f"serial_lines={received_lines}\nserial_last_error={last_error}\nmeta={meta}\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)


if __name__ == "__main__":
    threading.Thread(target=serial_reader, daemon=True).start()
    server = ThreadingHTTPServer((HTTP_HOST, HTTP_PORT), Handler)
    print(f"USB_STREAM_READY http://{HTTP_HOST}:{HTTP_PORT}/ serial={SERIAL_PORT}", flush=True)
    server.serve_forever()
