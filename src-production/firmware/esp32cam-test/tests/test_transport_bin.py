#!/usr/bin/env python3
"""Testes do transporte binario: oraculo diferencial + gates fail-closed.

O oraculo e independente: usa zlib.crc32 e um parser proprio em vez das
funcoes do modulo, de modo que um erro de implementacao nos dois lados nao
passa despercebido.
"""

from __future__ import annotations

import os
import random
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transport_bin import (
    HDR_SIZE,
    MAX_PAYLOAD,
    PAYLOAD_CRC_SIZE,
    SOF1,
    SOF2,
    TYPE_BEGIN,
    TYPE_CHUNK,
    TYPE_END,
    Decoder,
    FrameAssembler,
    Message,
    crc32,
    crc32_fast,
    encode_begin,
    encode_chunk,
    encode_end,
    encode_message,
)

CHUNK = 1024


def test_via_rapida_igual_referencia():
    """A via quente (zlib) e a referencia (tabela em Python) tem de concordar."""
    for size in (0, 1, 7, 64, 1024, 4096, 13169):
        data = os.urandom(size)
        assert crc32_fast(data) == crc32(data), f"divergem em {size}B"
        assert crc32_fast(data) == zlib.crc32(data) & 0xFFFFFFFF


def fake_jpeg(size: int = 16384, seed: int = 7) -> bytes:
    rnd = random.Random(seed)
    body = bytes(rnd.randrange(256) for _ in range(size))
    return b"\xff\xd8" + body + b"\xff\xd9"


def oracle_parse(stream: bytes) -> list[tuple[int, int, int, bytes]]:
    """Parser independente: sem reuso do estado do modulo."""
    out: list[tuple[int, int, int, bytes]] = []
    i = 0
    while i + HDR_SIZE <= len(stream):
        if stream[i] != SOF1 or stream[i + 1] != SOF2:
            i += 1
            continue
        version, mtype, _flags, event, seq, length = struct.unpack_from(
            "<BBBHIH", stream, i + 2
        )
        if version != 1 or length > MAX_PAYLOAD:
            i += 1
            continue
        end = i + HDR_SIZE + length + PAYLOAD_CRC_SIZE
        if end > len(stream):
            break
        payload = stream[i + HDR_SIZE : i + HDR_SIZE + length]
        if (
            zlib.crc32(payload) & 0xFFFFFFFF
            != struct.unpack_from("<I", stream, i + HDR_SIZE + length)[0]
        ):
            i += 1
            continue
        out.append((mtype, event, seq, payload))
        i = end
    return out


def test_crc_matches_zlib():
    for size in (0, 1, 15, 1024, 4096):
        data = os.urandom(size)
        assert crc32(data) == zlib.crc32(data) & 0xFFFFFFFF, f"crc32 difere em {size}B"


def test_round_trip_against_oracle():
    jpeg = fake_jpeg()
    event = 42
    stream = encode_begin(event, len(jpeg), crc32(jpeg))
    chunks = [jpeg[i : i + CHUNK] for i in range(0, len(jpeg), CHUNK)]
    for seq, chunk in enumerate(chunks):
        stream += encode_chunk(event, seq, chunk)
    stream += encode_end(event, crc32(jpeg))

    # oraculo independente ve as mesmas mensagens
    oracle = oracle_parse(stream)
    assert [m[0] for m in oracle] == [TYPE_BEGIN] + [TYPE_CHUNK] * len(chunks) + [
        TYPE_END
    ]

    # decoder incremental com fatias de tamanho irregular (fuzz de fronteira)
    rnd = random.Random(11)
    dec = Decoder()
    asm = FrameAssembler()
    got = None
    pos = 0
    while pos < len(stream):
        step = rnd.randrange(1, 300)
        for msg in dec.feed(stream[pos : pos + step]):
            frame = asm.feed(msg)
            if frame is not None:
                got = frame
        pos += step
    assert got == jpeg, "frame reconstruido difere do original"
    assert asm.frames_ok == 1
    assert dec.discarded_bytes == 0 and dec.bad_payload == 0 and dec.bad_header == 0


def test_corrupted_payload_is_not_published():
    jpeg = fake_jpeg(4096)
    stream = encode_begin(1, len(jpeg), crc32(jpeg))
    chunks = [jpeg[i : i + CHUNK] for i in range(0, len(jpeg), CHUNK)]
    for seq, chunk in enumerate(chunks):
        encoded = bytearray(encode_chunk(1, seq, chunk))
        if seq == 1:
            encoded[HDR_SIZE + 10] ^= 0x40  # bit virado no payload do chunk 1
        stream += bytes(encoded)
    stream += encode_end(1, crc32(jpeg))

    dec, asm = Decoder(), FrameAssembler()
    frames = [asm.feed(m) for m in dec.feed(stream)]
    assert all(f is None for f in frames), "frame corrompido foi publicado"
    assert dec.bad_payload == 1
    assert asm.frames_ok == 0


def test_corrupted_header_resyncs_to_next_message():
    jpeg = fake_jpeg(2048)
    good = encode_chunk(7, 0, jpeg)
    broken = bytearray(good)
    broken[4] ^= 0xFF  # corrompe TYPE/FLAGS dentro do CRC16
    stream = bytes(broken) + good
    dec = Decoder()
    msgs = dec.feed(stream)
    assert len(msgs) == 1 and msgs[0].payload == jpeg, "nao ressincronizou"
    assert dec.bad_header >= 1


def test_ascii_logs_interleaved_do_not_break_framing():
    jpeg = fake_jpeg(3000)
    stream = b""
    stream += b"I (1204) esp32cam_test: READY sensor=1 camera=0\r\n"
    stream += encode_begin(9, len(jpeg), crc32(jpeg))
    for seq, off in enumerate(range(0, len(jpeg), CHUNK)):
        stream += encode_chunk(9, seq, jpeg[off : off + CHUNK])
        stream += b"TRIGGER_ACCEPTED source=e18_d80nk event=9\r\n"
    stream += encode_end(9, crc32(jpeg))
    stream += b"CAMERA_OFF event=9 power_en=-1 deinit=0x0 ledc_stop=0x0\r\n"

    dec, asm = Decoder(), FrameAssembler()
    got = None
    for msg in dec.feed(stream):
        frame = asm.feed(msg)
        if frame is not None:
            got = frame
    assert got == jpeg
    assert dec.discarded_bytes > 0, "logs deveriam ter sido descartados"


def test_lost_chunk_blocks_frame():
    jpeg = fake_jpeg(4096)
    stream = encode_begin(3, len(jpeg), crc32(jpeg))
    chunks = [jpeg[i : i + CHUNK] for i in range(0, len(jpeg), CHUNK)]
    for seq, chunk in enumerate(chunks):
        if seq == 1:
            continue
        stream += encode_chunk(3, seq, chunk)
    stream += encode_end(3, crc32(jpeg))

    dec, asm = Decoder(), FrameAssembler()
    frames = [asm.feed(m) for m in dec.feed(stream)]
    assert all(f is None for f in frames), "frame incompleto foi publicado"
    assert asm.gaps == 1 and asm.frames_ok == 0
    assert any("lacuna" in e for e in asm.events), (
        f"lacuna nao registrada: {asm.events}"
    )


def test_duplicate_chunk_is_tolerated():
    jpeg = fake_jpeg(3000)
    stream = encode_begin(5, len(jpeg), crc32(jpeg))
    chunks = [jpeg[i : i + CHUNK] for i in range(0, len(jpeg), CHUNK)]
    for seq, chunk in enumerate(chunks):
        stream += encode_chunk(5, seq, chunk)
        if seq == 0:
            stream += encode_chunk(5, seq, chunk)  # reenvio duplicado
    stream += encode_end(5, crc32(jpeg))

    dec, asm = Decoder(), FrameAssembler()
    got = None
    for msg in dec.feed(stream):
        frame = asm.feed(msg)
        if frame is not None:
            got = frame
    assert got == jpeg
    assert asm.duplicates == 1 and asm.frames_ok == 1


def test_truncated_header_then_valid_stream():
    jpeg = fake_jpeg(1500)
    valid = (
        encode_begin(2, len(jpeg), crc32(jpeg))
        + encode_chunk(2, 0, jpeg)
        + encode_end(2, crc32(jpeg))
    )
    partial = valid[:9]
    dec, asm = Decoder(), FrameAssembler()
    got = None
    for msg in dec.feed(partial + valid):
        frame = asm.feed(msg)
        if frame is not None:
            got = frame
    assert got == jpeg, "stream apos cabecalho truncado nao foi recuperado"


def test_jpeg_marker_gate():
    body = b"\x00" * 512
    stream = (
        encode_begin(4, len(body), crc32(body))
        + encode_chunk(4, 0, body)
        + encode_end(4, crc32(body))
    )
    dec, asm = Decoder(), FrameAssembler()
    frames = [asm.feed(m) for m in dec.feed(stream)]
    assert all(f is None for f in frames)
    assert asm.frames_ok == 0 and "JPEG" in asm.last_error


def test_total_len_mismatch_rejected():
    jpeg = fake_jpeg(800)
    stream = (
        encode_begin(6, len(jpeg) + 10, crc32(jpeg))
        + encode_chunk(6, 0, jpeg)
        + encode_end(6, crc32(jpeg))
    )
    dec, asm = Decoder(), FrameAssembler()
    frames = [asm.feed(m) for m in dec.feed(stream)]
    assert all(f is None for f in frames)
    assert "tamanho divergente" in asm.last_error


def test_wire_cost_improves_over_text_baseline():
    """Compara com o baseline medido no fio: 33.690 B para um JPEG de 16.155 B."""
    jpeg = fake_jpeg(16155)
    chunks = [jpeg[i : i + CHUNK] for i in range(0, len(jpeg), CHUNK)]
    wire = len(encode_begin(1, len(jpeg), crc32(jpeg)))
    wire += sum(len(encode_chunk(1, s, c)) for s, c in enumerate(chunks))
    wire += len(encode_end(1, crc32(jpeg)))
    baseline = 33690
    fator = wire / len(jpeg)
    ganho = (1 - wire / baseline) * 100
    print(
        f"binario: {wire} B para {len(jpeg)} B de JPEG ({fator:.2f}x), "
        f"texto medido: {baseline} B ({baseline / len(jpeg):.2f}x), ganho {ganho:.0f}%"
    )
    assert fator < 1.05, f"sobrecarga binaria alta: {fator:.3f}x"
    assert ganho > 45, f"ganho insuficiente: {ganho:.0f}%"


def test_feed_ex_separates_channels_in_order():
    jpeg = fake_jpeg(3000)
    chunks = [jpeg[i : i + CHUNK] for i in range(0, len(jpeg), CHUNK)]
    log_a = b"READY sensor=1 camera=0 mode=irq_on_demand\r\n"
    log_b = b"TRIGGER_ACCEPTED source=e18_d80nk event=9\r\n"
    log_c = b"CAMERA_OFF event=9 power_en=-1 deinit=0x0 ledc_stop=0x0\r\n"

    stream = log_a + encode_begin(9, len(jpeg), crc32(jpeg))
    for seq, chunk in enumerate(chunks):
        stream += encode_chunk(9, seq, chunk) + log_b
    stream += encode_end(9, crc32(jpeg)) + log_c

    dec, asm = Decoder(), FrameAssembler()
    text = bytearray()
    frames: list[bytes] = []
    tipos: list[str] = []
    for kind, payload in dec.feed_ex(stream):
        tipos.append(kind)
        if kind == "text":
            text.extend(payload)
        else:
            frame = asm.feed(payload)
            if frame is not None:
                frames.append(frame)

    assert frames == [jpeg], "frame nao reconstruido pelo canal binario"
    esperado = log_a + log_b * len(chunks) + log_c
    assert bytes(text) == esperado, "canal de texto nao reconstruiu os logs na ordem"
    assert tipos[0] == "text" and tipos[-1] == "text"


def test_eventos_do_montador_tem_limite():
    """Vazamento lento: processo longo nao pode acumular eventos sem limite."""
    asm = FrameAssembler()
    for _ in range(200):
        asm.feed(Message(TYPE_CHUNK, 1, 0, b"x"))  # CHUNK sem BEGIN: rejeitado
    assert asm.rejected >= 200
    assert len(asm.events) <= 50, f"eventos acumulados: {len(asm.events)}"


def test_payload_limit_enforced():
    try:
        encode_message(TYPE_CHUNK, 1, 0, b"x" * (MAX_PAYLOAD + 1))
    except ValueError:
        return
    raise AssertionError("payload acima do limite foi aceito")


def test_end_exige_evento_sequencia_payload_e_crc_consistentes():
    jpeg = fake_jpeg(300)
    asm = FrameAssembler()
    asm.feed(Message(TYPE_BEGIN, 7, 0, struct.pack("<IIq", len(jpeg), crc32(jpeg), 0)))
    asm.feed(Message(TYPE_CHUNK, 7, 0, jpeg))
    assert asm.feed(Message(TYPE_END, 7, 1, struct.pack("<I", crc32(jpeg)))) is None
    assert asm.rejected == 1

    asm.feed(Message(TYPE_BEGIN, 7, 0, struct.pack("<IIq", len(jpeg), crc32(jpeg), 0)))
    asm.feed(Message(TYPE_CHUNK, 7, 0, jpeg))
    assert asm.feed(Message(TYPE_END, 7, 0, b"")) is None
    assert asm.rejected == 2

    asm.feed(Message(TYPE_BEGIN, 7, 0, struct.pack("<IIq", len(jpeg), crc32(jpeg), 0)))
    asm.feed(Message(TYPE_CHUNK, 7, 0, jpeg))
    assert asm.feed(Message(TYPE_END, 7, 0, struct.pack("<I", crc32(jpeg) ^ 1))) is None
    assert asm.rejected == 3


def test_chunk_nao_pode_exceder_total_len():
    asm = FrameAssembler()
    asm.feed(Message(TYPE_BEGIN, 9, 0, struct.pack("<IIq", 1, crc32(b"x"), 0)))
    assert asm.feed(Message(TYPE_CHUNK, 9, 0, b"xx")) is None
    assert asm.rejected == 1
    assert asm.frame is None


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    print("FALHAS:", failures)
    sys.exit(1 if failures else 0)
