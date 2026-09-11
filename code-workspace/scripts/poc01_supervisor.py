#!/usr/bin/env python3
"""Dono unico da porta serial do PoC-01: le o ESP32 e republica num arquivo de stream.

POR QUE EXISTE (licao de metodo): a porta serial e um recurso exclusivo. Antes, o upload do
firmware exigia parar o visualizador -> a janela de quem estava acompanhando morria. Aqui:
  * ESTE processo e o unico que abre /dev/ttyUSB0;
  * ele escreve tudo em ~/poc01/stream.log (append, com carimbo do host);
  * qualquer visualizador (tail -f, harness de teste) le o ARQUIVO, nunca a porta;
  * se existir ~/poc01/PAUSA, ele solta a porta (upload grava sem matar ninguem) e volta sozinho.

Rodar como unidade do usuario:
    systemd-run --user --unit=pnaat-poc01-sup --collect \
      $HOME/tcc-pnaat/github/.venv/bin/python .../poc01_supervisor.py
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import serial

PORTA = os.environ.get("PNAAT_PORTA", "/dev/ttyUSB0")
BASE = Path(os.environ.get("PNAAT_DIR", str(Path.home() / "poc01")))
STREAM = BASE / "stream.log"
PAUSA = BASE / "PAUSA"
LIMITE_BYTES = 5 * 1024 * 1024


def registrar(texto: str) -> None:
    try:
        with STREAM.open("a") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), texto))
        if STREAM.stat().st_size > LIMITE_BYTES:
            STREAM.replace(BASE / "stream.1.log")
    except Exception:
        pass


def main() -> int:
    BASE.mkdir(parents=True, exist_ok=True)
    print(f"supervisor: porta={PORTA} stream={STREAM} pausa={PAUSA}", flush=True)
    registrar("# supervisor iniciado")
    ser = None
    while True:
        if PAUSA.exists():
            if ser is not None:
                ser.close()
                ser = None
                registrar("# porta liberada para upload (PAUSA)")
            time.sleep(0.4)
            continue
        if ser is None:
            try:
                ser = serial.Serial(PORTA, 115200, timeout=0.5)
                ser.setDTR(False)   # nao resetar o board
                ser.setRTS(False)
                registrar("# porta aberta")
            except Exception as e:
                registrar(f"# porta indisponivel: {str(e)[:80]}")
                time.sleep(2)
                continue
        try:
            dados = ser.read(4096).decode("utf-8", errors="replace")
            if dados:
                for linha in dados.replace("\r", "").split("\n"):
                    if linha.strip():
                        registrar(linha.strip())
        except Exception as e:
            registrar(f"# erro de leitura: {str(e)[:80]}")
            try:
                ser.close()
            except Exception:
                pass
            ser = None
            time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
