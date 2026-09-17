#!/usr/bin/env python3
"""Ferramenta host para o ESP32 do PoC-01 (raw REPL via pyserial; nao usa mpremote).

Por que existe: nesta placa o mpremote nao entra em raw REPL (a sequencia de reset dele nao
colabora) e a leitura por `exec` no raw REPL corrompe bytes. Esta ferramenta controla DTR/RTS
explicitamente e usa base64 em chunks, com verificacao de sha256 no board.

Uso:
    python3 esp_tool.py ls
    python3 esp_tool.py upload <local> [destino]
    python3 esp_tool.py pull <remoto> <local>
    python3 esp_tool.py rm <remoto>
    python3 esp_tool.py run <remoto> [--segundos N]      # executa e transmite a saida
    python3 esp_tool.py reset
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import sys
import time
from pathlib import Path

import serial

PORTA = os.environ.get("PNAAT_PORTA", "/dev/ttyUSB0")
CHUNK = 512
#: mesmo diretorio que o supervisor usa (poc01_supervisor.py) para soltar a porta
PAUSA = Path(os.environ.get("PNAAT_DIR", str(Path.home() / "poc01"))) / "PAUSA"


def pausar_supervisor() -> None:
    """Cede a porta ao supervisor: cria PAUSA, ele solta /dev/ttyUSB0 em ~0.5 s.

    Sem isso, dois processos leem a mesma serial e o stream perde dados
    ("multiple access on port"). Nunca matar o supervisor nem o terminal do usuario.
    """
    try:
        PAUSA.parent.mkdir(parents=True, exist_ok=True)
        PAUSA.touch()
        print(f"[esp_tool] supervisor pausado ({PAUSA}); aguardando ele soltar a porta...")
        time.sleep(1.5)
    except Exception as e:
        print("[esp_tool] aviso: nao consegui pausar o supervisor:", str(e)[:80])


def retomar_supervisor() -> None:
    try:
        PAUSA.unlink()
        print("[esp_tool] supervisor retomado.")
    except FileNotFoundError:
        pass


class Esp:
    def __init__(self, porta: str = PORTA):
        self.ser = serial.Serial(porta, 115200, timeout=0.3, rtscts=False, dsrdtr=False)
        self.ser.setDTR(False)
        self.ser.setRTS(False)
        time.sleep(0.4)

    def fechar(self) -> None:
        self.ser.close()

    def _ler(self, segundos: float = 1.0) -> str:
        fim = time.time() + segundos
        dados = b""
        while time.time() < fim:
            dados += self.ser.read(4096)
        return dados.decode("utf-8", errors="replace")

    def raw(self, tentativas: int = 6) -> None:
        """Entra em raw REPL de forma robusta.

        Com firmware rodando sozinho como main.py, o Ctrl-C precisa interromper o loop antes de
        o Ctrl-A fazer efeito: por isso varias tentativas, cada uma com 3 Ctrl-C.
        """
        ultimo = ""
        for _i in range(tentativas):
            self.ser.write(b"\x03\x03\x03")
            time.sleep(0.4)
            self.ser.reset_input_buffer()
            self.ser.write(b"\x01")
            time.sleep(0.4)
            resp = self._ler(0.8)
            ultimo = resp
            if "raw REPL" in resp:
                return
            if ">>>" in resp:
                continue
        raise RuntimeError(f"nao entrou em raw REPL apos {tentativas} tentativas: {ultimo[:160]!r}")

    def saida_raw(self) -> None:
        self.ser.write(b"\x02")
        time.sleep(0.2)

    def exec(self, codigo: str, espera: float = 1.2) -> tuple[str, str]:
        self.ser.write(codigo.encode() + b"\x04")
        time.sleep(espera)
        resp = self._ler(espera)
        partes = resp.split("\x04")
        saida = partes[0].replace("OK", "", 1).strip()
        erro = partes[1].strip() if len(partes) > 1 else ""
        return saida, erro

    def soft_reset(self) -> str:
        self.ser.write(b"\x04")
        return self._ler(2.0)


def cmd_ls(esp: Esp) -> int:
    esp.raw()
    saida, erro = esp.exec("import os; print(sorted(os.listdir()))")
    print("arquivos no board:", saida or "(vazio)", erro[:200])
    esp.saida_raw()
    return 0


def cmd_rm(esp: Esp, remoto: str) -> int:
    esp.raw()
    _, erro = esp.exec(f"import os\nos.remove('{remoto}') if '{remoto}' in os.listdir() else None")
    print("rm", remoto, "| erro:", erro[:200] or "ok")
    esp.saida_raw()
    return 0


def cmd_upload(esp: Esp, local: Path, destino: str) -> int:
    conteudo = local.read_bytes()
    sha_local = hashlib.sha256(conteudo).hexdigest()
    esp.raw()
    esp.exec("import ubinascii")
    esp.exec(f"f=open('{destino}','wb')")
    b64 = base64.b64encode(conteudo).decode()
    for i in range(0, len(b64), CHUNK):
        parte = b64[i:i + CHUNK]
        _, erro = esp.exec(f"f.write(ubinascii.a2b_base64('{parte}'))", espera=0.35)
        if erro.strip():
            print("ERRO no chunk", i, erro[:200])
            return 1
    esp.exec("f.close()")
    saida, erro = esp.exec(
        "import hashlib, ubinascii\n"
        f"d=open('{destino}','rb').read()\n"
        "print(len(d), ubinascii.hexlify(hashlib.sha256(d).digest()).decode())",
        espera=2.0,
    )
    esp.saida_raw()
    print(f"upload {local.name} -> {destino}: {saida}")
    if erro.strip():
        print("erro:", erro[:200])
        return 1
    ok = sha_local in saida and str(len(conteudo)) in saida
    print("VERIFICACAO:", "OK (tamanho + sha256)" if ok else "DIVERGE")
    return 0 if ok else 1


def cmd_pull(esp: Esp, remoto: str, local: Path) -> int:
    esp.raw()
    esp.exec("import ubinascii")
    saida, erro = esp.exec(
        f"d=open('{remoto}','rb').read()\n"
        "import ubinascii\n"
        "print(ubinascii.b2a_base64(d).decode())",
        espera=3.0,
    )
    esp.saida_raw()
    if erro.strip():
        print("erro ao ler:", erro[:200])
        return 1
    b64 = "".join(linha.strip() for linha in saida.splitlines() if linha.strip())
    try:
        dados = base64.b64decode(b64)
    except Exception as e:
        print("base64 invalido:", e, "| inicio:", b64[:80])
        return 1
    local.write_bytes(dados)
    print(f"pull {remoto} -> {local} ({len(dados)} bytes, sha256 {hashlib.sha256(dados).hexdigest()[:16]})")
    return 0


def cmd_run(esp: Esp, remoto: str, segundos: int) -> int:
    esp.raw()
    print(f"executando {remoto} por {segundos}s (Ctrl-C no fim)", flush=True)
    esp.ser.write(f"exec(open('{remoto}').read())\r\n".encode() + b"\x04")
    fim = time.time() + segundos
    buffer = ""
    eventos = 0
    while time.time() < fim:
        dados = esp.ser.read(4096).decode("utf-8", errors="replace")
        if not dados:
            continue
        buffer += dados
        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            linha = linha.strip().replace("\r", "")
            if not linha or linha == "OK":
                continue
            print(f"[{time.strftime('%H:%M:%S')}] {linha[:130]}", flush=True)
            if "CAPTURE_WINDOW" in linha:
                eventos += 1
    esp.ser.write(b"\x03\x03")
    time.sleep(0.5)
    esp.saida_raw()
    print(f"\nRESUMO serial: {eventos} linha(s) CAPTURE_WINDOW_*")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", default=PORTA)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ls")
    p_up = sub.add_parser("upload")
    p_up.add_argument("local", type=Path)
    p_up.add_argument("destino", nargs="?")
    p_pull = sub.add_parser("pull")
    p_pull.add_argument("remoto")
    p_pull.add_argument("local", type=Path)
    p_rm = sub.add_parser("rm")
    p_rm.add_argument("remoto")
    p_run = sub.add_parser("run")
    p_run.add_argument("remoto")
    p_run.add_argument("--segundos", type=int, default=60)
    sub.add_parser("reset")
    args = ap.parse_args()

    usa_porta = args.cmd in {"ls", "upload", "pull", "rm", "run", "reset"}
    if usa_porta:
        pausar_supervisor()

    try:
        esp = Esp(args.porta)
    except Exception as e:
        print("nao consegui abrir a porta:", e)
        if usa_porta:
            retomar_supervisor()
        return 2

    try:
        if args.cmd == "ls":
            return cmd_ls(esp)
        if args.cmd == "upload":
            return cmd_upload(esp, args.local, args.destino or args.local.name)
        if args.cmd == "pull":
            return cmd_pull(esp, args.remoto, args.local)
        if args.cmd == "rm":
            return cmd_rm(esp, args.remoto)
        if args.cmd == "run":
            return cmd_run(esp, args.remoto, args.segundos)
        if args.cmd == "reset":
            esp.raw()
            print("soft reset:", esp.soft_reset()[:200])
            return 0
    finally:
        esp.fechar()
        if usa_porta:
            retomar_supervisor()
    return 0


if __name__ == "__main__":
    sys.exit(main())
