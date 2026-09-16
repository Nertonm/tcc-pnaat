#!/usr/bin/env python3
"""Transporte binario enquadrado para a imagem da ESP32-CAM (lado host).

Contrato v1 (tudo little-endian):

  offset  campo      tam  descricao
  ------  ---------  ---  -------------------------------------------------
  0       SOF1       1    0xA5
  1       SOF2       1    0x5A
  2       VER        1    versao do protocolo (1)
  3       TYPE       1    1=BEGIN 2=CHUNK 3=END 4=ACK 5=NACK
  4       FLAGS      1    reservado (0)
  5       EVENT_ID   2    identificador monotonico do evento na ESP
  7       SEQ        4    sequencia da mensagem (0 no BEGIN)
  11      LEN        2    bytes de payload que seguem o cabecalho
  13      HDR_CRC16  2    CRC-16/CCITT-FALSE sobre VER..LEN (bytes 2..12)
  15      PAYLOAD    LEN
          PAYLOAD_CRC32 4 CRC-32 do payload desta mensagem

  BEGIN leva como payload 16 bytes: TOTAL_LEN (u32) + FRAME_CRC32 (u32) do JPEG
  completo + TRIGGER_US (i64, instante do trigger no relogio da ESP). O parser
  exige exatamente 16 (FrameAssembler.feed) -- implementar por um contrato de 8
  bytes rejeita todos os BEGIN. Logs ASCII da ESP convivem no mesmo fio: o parser
  sincroniza por SOF + HDR_CRC16 e descarta o que nao casa, nunca publica lixo.

  Limite conhecido do v1: EVENT_ID tem 2 bytes, mas o contador da ESP e' u32 --
  a partir de 65536 capturas o id do fio repete e dois frames diferentes passam a
  se chamar igual (a rastreabilidade foto<->evento, que a nota ext_ref usa, deixa
  de ser univoca). Um v2 precisa de EVENT_ID u32 no cabecalho.

Regras fail-closed: mensagem com CRC invalido e descartada (nao publicada);
frame so e publicado depois de todos os chunks contiguos, tamanho e CRC do JPEG
conferidos, com marcadores FF D8 / FF D9.

Caminho quente: o decoder usa zlib.crc32 (C) e bytes.find para ressincronizar;
crc32() fica como referencia independente e o teste diferencial garante que as
duas concordam. Medido no cenario sintetico do bench (frame de 13 kB + log
intercalado, fatias de 4096 B): 1,67 ms -> 0,08 ms por frame.
"""

from __future__ import annotations

import struct
import zlib
from collections import deque
from dataclasses import dataclass, field

SOF1 = 0xA5
SOF2 = 0x5A
_SOF_PAIR = bytes((SOF1, SOF2))
VERSION = 1

TYPE_BEGIN = 1
TYPE_CHUNK = 2
TYPE_END = 3
TYPE_ACK = 4
TYPE_NACK = 5

TYPE_NAMES = {
    TYPE_BEGIN: "BEGIN",
    TYPE_CHUNK: "CHUNK",
    TYPE_END: "END",
    TYPE_ACK: "ACK",
    TYPE_NACK: "NACK",
}

HDR_SIZE = 15  # SOF(2) + VER..HDR_CRC16(13)
HDR_CRC_OFFSET = 2  # CRC16 cobre de VER ate LEN
HDR_CRC_SPAN = 11  # bytes 2..12 inclusive
PAYLOAD_CRC_SIZE = 4
MAX_PAYLOAD = 4096

_CRC16_TABLE = []
for _b in range(256):
    _v = _b << 8
    for _ in range(8):
        _v = ((_v << 1) ^ 0x1021) & 0xFFFF if _v & 0x8000 else (_v << 1) & 0xFFFF
    _CRC16_TABLE.append(_v)

_CRC32_TABLE = []
for _b in range(256):
    _v = _b
    for _ in range(8):
        _v = (0xEDB88320 ^ (_v >> 1)) if _v & 1 else (_v >> 1)
    _CRC32_TABLE.append(_v)


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc = ((crc << 8) & 0xFFFF) ^ _CRC16_TABLE[((crc >> 8) ^ byte) & 0xFF]
    return crc


def crc32(data: bytes) -> int:
    """Referencia independente (tabela em Python) do CRC-32/ISO-HDLC.

    Mantida de proposito: e' o oraculo diferencial contra zlib. O caminho
    quente usa crc32_fast().
    """
    crc = 0xFFFFFFFF
    for byte in data:
        crc = _CRC32_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def crc32_fast(data: bytes) -> int:
    """Mesma especificacao, implementacao em C (zlib); usada no caminho quente."""
    return zlib.crc32(data) & 0xFFFFFFFF


def encode_message(
    msg_type: int, event_id: int, seq: int, payload: bytes = b"", flags: int = 0
) -> bytes:
    """Codifica uma mensagem. Usado pelo encoder da ESP e pelos testes."""
    if not 0 <= len(payload) <= MAX_PAYLOAD:
        raise ValueError(f"payload fora de [0,{MAX_PAYLOAD}]: {len(payload)}")
    core = struct.pack(
        "<BBBHIH",
        VERSION,
        msg_type,
        flags & 0xFF,
        event_id & 0xFFFF,
        seq & 0xFFFFFFFF,
        len(payload),
    )
    header = bytes([SOF1, SOF2]) + core + struct.pack("<H", crc16(core))
    return header + payload + struct.pack("<I", crc32_fast(payload))


def encode_begin(
    event_id: int, total_len: int, frame_crc32: int, trigger_us: int = 0
) -> bytes:
    return encode_message(
        TYPE_BEGIN, event_id, 0, struct.pack("<IIq", total_len, frame_crc32, trigger_us)
    )


def encode_chunk(event_id: int, seq: int, chunk: bytes) -> bytes:
    return encode_message(TYPE_CHUNK, event_id, seq, chunk)


def encode_end(event_id: int, frame_crc32: int) -> bytes:
    return encode_message(TYPE_END, event_id, 0, struct.pack("<I", frame_crc32))


@dataclass(frozen=True)
class Message:
    type: int
    event_id: int
    seq: int
    payload: bytes

    @property
    def type_name(self) -> str:
        return TYPE_NAMES.get(self.type, f"?{self.type}")


@dataclass
class Decoder:
    """Parser incremental: aceita bytes de qualquer tamanho e emite mensagens.

    Sincroniza por SOF + CRC16 do cabecalho. Bytes que nao casam (logs ASCII,
    ruido de boot, mensagem truncada) sao descartados sem publicar nada.
    """

    buffer: bytearray = field(default_factory=bytearray)
    discarded_bytes: int = 0
    bad_header: int = 0
    bad_payload: int = 0
    accepted: int = 0
    unsupported_version: int = 0
    _drop: bytearray = field(default_factory=bytearray)

    def feed(self, data: bytes) -> list[Message]:
        return [ev[1] for ev in self.feed_ex(data) if ev[0] == "msg"]

    def feed_ex(self, data: bytes) -> list[tuple[str, object]]:
        """Como feed(), mas devolve tambem os trechos descartados em ordem.

        Cada entrada e' ("msg", Message) ou ("text", bytes). Os trechos "text"
        sao exatamente os bytes que nao eram mensagem (logs ASCII da ESP), o
        que permite consumir os dois canais do mesmo fio sem heuristica de modo.
        """
        self.buffer.extend(data)
        out: list[tuple[str, object]] = []
        while True:
            status, payload = self._step()
            if status == "need":
                self._flush_drop(out)
                return out
            if status == "msg":
                self._flush_drop(out)
                out.append(("msg", payload))
            # "skip": bytes ja foram acumulados no trecho descartado

    def _flush_drop(self, out: list[tuple[str, object]]) -> None:
        if self._drop:
            out.append(("text", bytes(self._drop)))
            self._drop.clear()

    def _resync(self) -> int:
        """Quantos bytes descartar ate o proximo SOF plausivel.

        Usa bytes.find (C) em vez de varrer byte a byte em Python: com log
        ASCII intercalado isso aparece no perfil. Preserva um 0xA5 final, que
        pode ser o primeiro byte de um cabecalho ainda incompleto.
        """
        buf = self.buffer
        idx = buf.find(_SOF_PAIR)
        if idx >= 0:
            return idx
        if buf and buf[-1] == SOF1:
            return len(buf) - 1
        return len(buf)

    def _discard(self, count: int) -> None:
        """Remove bytes do inicio do buffer e guarda-os no trecho 'text'."""
        self._drop.extend(self.buffer[:count])
        del self.buffer[:count]
        self.discarded_bytes += count

    def _step(self) -> tuple[str, Message | None]:
        """Um passo: ("msg", m) entregou, ("skip", None) descartou e continua,
        ("need", None) faltam bytes."""
        buf = self.buffer
        if len(buf) < HDR_SIZE:
            return ("need", None)
        if not (buf[0] == SOF1 and buf[1] == SOF2):
            drop = self._resync()
            if drop <= 0:
                return ("need", None)
            self._discard(drop)
            return ("skip", None)
        core = bytes(buf[HDR_CRC_OFFSET : HDR_CRC_OFFSET + HDR_CRC_SPAN])
        want = struct.unpack_from("<H", buf, HDR_CRC_OFFSET + HDR_CRC_SPAN)[0]
        if crc16(core) != want:
            self._discard(1)
            self.bad_header += 1
            return ("skip", None)
        version, msg_type, _flags, event_id, seq, length = struct.unpack_from(
            "<BBBHIH", buf, 2
        )
        if version != VERSION:
            self._discard(1)
            self.unsupported_version += 1
            return ("skip", None)
        if length > MAX_PAYLOAD:
            self._discard(1)
            self.bad_header += 1
            return ("skip", None)
        total = HDR_SIZE + length + PAYLOAD_CRC_SIZE
        if len(buf) < total:
            return ("need", None)
        payload = bytes(buf[HDR_SIZE : HDR_SIZE + length])
        got_crc = struct.unpack_from("<I", buf, HDR_SIZE + length)[0]
        del buf[:total]
        if crc32_fast(payload) != got_crc:
            self.bad_payload += 1
            return ("skip", None)
        self.accepted += 1
        return ("msg", Message(msg_type, event_id, seq, payload))


@dataclass
class FrameAssembler:
    """Reconstroi o JPEG a partir de BEGIN/CHUNK/END, com gates fail-closed."""

    chunk_size: int = 1024
    frame: bytearray | None = None
    total_len: int = 0
    frame_crc32: int = 0
    event_id: int = 0
    expect_seq: int = 0
    gaps: int = 0
    duplicates: int = 0
    rejected: int = 0
    frames_ok: int = 0
    last_error: str = ""
    events: deque[str] = field(default_factory=lambda: deque(maxlen=50))

    def _note(self, text: str) -> None:
        self.last_error = text
        self.events.append(text)

    def feed(self, msg: Message) -> bytes | None:
        if msg.type == TYPE_BEGIN:
            if len(msg.payload) != 16:
                self.rejected += 1
                self._note(f"BEGIN com payload de {len(msg.payload)} bytes")
                return None
            self.total_len, self.frame_crc32, _trigger = struct.unpack(
                "<IIq", msg.payload
            )
            if not 0 < self.total_len <= 4 * 1024 * 1024:
                self.rejected += 1
                self._note(f"BEGIN com total_len invalido: {self.total_len}")
                self.frame = None
                return None
            self.frame = bytearray()
            self.event_id = msg.event_id
            self.expect_seq = 0
            return None

        if msg.type == TYPE_CHUNK:
            if self.frame is None:
                self.rejected += 1
                self._note("CHUNK sem BEGIN")
                return None
            if msg.event_id != self.event_id:
                self.rejected += 1
                self._note(
                    f"CHUNK de evento {msg.event_id} dentro do evento {self.event_id}"
                )
                return None
            if msg.seq < self.expect_seq:
                self.duplicates += 1
                self._note(f"CHUNK duplicado seq={msg.seq}")
                return None
            if msg.seq > self.expect_seq:
                self.gaps += 1
                self._note(f"lacuna: esperado seq={self.expect_seq}, veio {msg.seq}")
                self.frame = None
                return None
            if len(self.frame) + len(msg.payload) > self.total_len:
                self.rejected += 1
                self._note(
                    f"CHUNK excede total_len: {len(self.frame) + len(msg.payload)} > {self.total_len}"
                )
                self.frame = None
                return None
            self.frame.extend(msg.payload)
            self.expect_seq += 1
            return None

        if msg.type == TYPE_END:
            if self.frame is None:
                self.rejected += 1
                self._note("END sem frame montado")
                return None
            if msg.event_id != self.event_id:
                # END de outro evento rotularia a foto errada
                self.rejected += 1
                self._note(
                    f"END do evento {msg.event_id} dentro do evento {self.event_id}"
                )
                self.frame = None
                return None
            if msg.seq != 0:
                self.rejected += 1
                self._note(f"END com seq invalida: {msg.seq}")
                self.frame = None
                return None
            if len(msg.payload) != 4:
                self.rejected += 1
                self._note(f"END com payload de {len(msg.payload)} bytes; esperado 4")
                self.frame = None
                return None
            end_crc32 = struct.unpack("<I", msg.payload)[0]
            if end_crc32 != self.frame_crc32:
                self.rejected += 1
                self._note("CRC-32 do END diverge do BEGIN")
                self.frame = None
                return None
            frame = bytes(self.frame)
            self.frame = None
            if len(frame) != self.total_len:
                self.rejected += 1
                self._note(f"tamanho divergente: {len(frame)} != {self.total_len}")
                return None
            if crc32_fast(frame) != self.frame_crc32:
                self.rejected += 1
                self._note("CRC-32 do frame divergente")
                return None
            if not (frame[:2] == b"\xff\xd8" and frame[-2:] == b"\xff\xd9"):
                self.rejected += 1
                self._note("frame sem marcadores JPEG")
                return None
            self.frames_ok += 1
            self.last_error = ""
            return frame

        self.rejected += 1
        self._note(f"mensagem inesperada: {msg.type_name}")
        return None
