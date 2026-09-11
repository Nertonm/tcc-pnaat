#!/usr/bin/env python3
"""Visualizador LEGIVEL do PoC-01 — passivo: le o stream do supervisor, nunca a porta serial.

A porta /dev/ttyUSB0 tem UM dono (poc01_supervisor.py), que grava ~/poc01/stream.log.
Este script so le esse arquivo. Pode ser aberto quantas vezes quiser, a qualquer momento,
inclusive durante upload de firmware — nao existe mais conflito de "multiple access on port".

    python3 poc01_watch.py                  # acompanha ao vivo
    python3 poc01_watch.py --desde-inicio    # mostra tudo o que ja passou

Ctrl-C encerra e mostra o resumo da sessao.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

BASE = Path.home() / "poc01"
STREAM = BASE / "stream.log"

LEGENDA = """\
==============================================================================
 PNAAT - PoC-01: trigger de presenca (ESP32 + E18-D80NK em GPIO33)
------------------------------------------------------------------------------
 VOCE ESTA LENDO O STREAM DO SUPERVISOR (o supervisor e o dono da porta serial).
 O QUE CADA LINHA SIGNIFICA
   estado       nivel eletrico do pino: 1 = repouso (livre), 0 = objeto a frente
   PASSAGEM #n  o sensor detectou e abriu a janela de captura do item n
   liberou      o item saiu; mostra quanto tempo ficou no campo
   DESCARTA     deteccao dentro da guarda anti-duplicacao (foi ignorada de proposito)
   AGUARDANDO   o firmware nao arma enquanto a linha estiver em nivel de objeto
                (sensor sensivel demais ou algo na frente -> ajuste o potenciometro)
------------------------------------------------------------------------------
 Como usar: passe a garrafa a ~15 cm, afaste, espere ~3 s, repita.
 Ctrl-C encerra e mostra o resumo. Para o teste com veredito: poc01_teste.py
==============================================================================
"""


def agora() -> str:
    return time.strftime("%H:%M:%S")


class Estado:
    def __init__(self) -> None:
        self.armado = False
        self.nivel: int | None = None
        self.passagens = 0
        self.duracoes: list[float] = []
        self.suprimidas = 0
        self.arm_avisos = 0


def tratar(ev: dict, st: Estado) -> None:
    nome = ev["_evento"]
    if nome == "READY":
        print(f"[{agora()}] firmware iniciou (pino {ev.get('pin')}, guarda {ev.get('guard_ms')} ms)")
    elif nome == "WARMUP_DONE":
        print(f"[{agora()}] aquecimento concluido (nivel {ev.get('nivel')})")
    elif nome == "ARMED":
        st.armado = True
        st.nivel = int(ev.get("nivel", "1"))
        print(f"[{agora()}] ARMADO — sensor em repouso. Pode passar a garrafa.")
    elif nome in ("ARM_WAIT", "ARM_TIMEOUT"):
        st.arm_avisos += 1
        if st.arm_avisos in (1, 5, 20) or st.arm_avisos % 50 == 0:
            print(f"[{agora()}] AGUARDANDO REPOUSO ({st.arm_avisos}x) — a linha esta em nivel de objeto.")
            print( "            Afaste o que estiver na frente do sensor ou reduza o alcance no potenciometro.")
    elif nome == "LEVEL":
        st.nivel = int(ev.get("nivel", "-1"))
        rotulo = "objeto a frente" if st.nivel == 0 else "livre"
        print(f"[{agora()}] estado: nivel {st.nivel} ({rotulo})")
    elif nome == "OPEN":
        st.passagens += 1
        print(f"[{agora()}] >>> PASSAGEM #{ev.get('n')} — item detectado")
    elif nome == "CLOSE":
        dur_ms = float(ev.get("dur_ms", 0))
        st.duracoes.append(dur_ms / 1000.0)
        print(f"[{agora()}]     liberou  — item #{ev.get('n')} ficou {dur_ms / 1000.0:.2f} s no campo")
    elif nome == "SUPPRESSED":
        st.suprimidas += 1
        print(f"[{agora()}]     DESCARTA — deteccao {ev.get('dt_ms')} ms dentro da guarda "
              f"(total: {st.suprimidas})")
    else:
        print(f"[{agora()}] {nome} {ev}")


def parse(linha: str) -> dict | None:
    if "EV " not in linha:
        return None
    carimbo, resto = linha.split(" EV ", 1)
    partes = resto.split()
    if not partes:
        return None
    ev = {"_evento": partes[0], "_t": carimbo.strip()}
    for item in partes[1:]:
        if "=" in item:
            k, v = item.split("=", 1)
            ev[k] = v
    return ev


def rodape(st: Estado) -> str:
    nivel = "-" if st.nivel is None else ("objeto" if st.nivel == 0 else "livre")
    ult = f"{st.duracoes[-1]:.2f}s" if st.duracoes else "-"
    return (f"estado: {nivel:<7} | passagens={st.passagens:<3} | ultima={ult:<7} | "
            f"descartadas={st.suprimidas:<3} | armado={'sim' if st.armado else 'nao'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stream", type=Path, default=STREAM)
    ap.add_argument("--desde-inicio", action="store_true")
    ap.add_argument("--sem-legenda", action="store_true")
    args = ap.parse_args()

    if not args.sem_legenda:
        print(LEGENDA)
    if not args.stream.exists():
        print(f" ERRO: stream nao existe ({args.stream}). O supervisor esta rodando?")
        print("   systemctl --user status pnaat-poc01-sup")
        return 2

    st = Estado()
    with args.stream.open() as f:
        if args.desde_inicio:
            f.seek(0)
        else:
            f.seek(f.seek(0, 2))          # comeca no fim: mostra o que acontece agora
        print(f"[{agora()}] lendo {args.stream} (passivo — nao abre a porta serial)")
        print(f"[{agora()}] {rodape(st)}")
        proximo_rodape = time.time() + 5
        try:
            while True:
                linha = f.readline()
                if linha:
                    ev = parse(linha.rstrip("\n"))
                    if ev:
                        tratar(ev, st)
                else:
                    time.sleep(0.2)
                if time.time() >= proximo_rodape:
                    print(f"[{agora()}] {rodape(st)}")
                    proximo_rodape = time.time() + 15
        except KeyboardInterrupt:
            print("\n" + "=" * 74)
            print(" RESUMO DA SESSAO")
            print("=" * 74)
            print(f" passagens detectadas  : {st.passagens}")
            print(f" deteccoes descartadas : {st.suprimidas} (bloqueadas pela guarda anti-duplicacao)")
            print(f" avisos de nao-armado  : {st.arm_avisos}")
            if st.duracoes:
                print(f" tempo no campo        : min {min(st.duracoes):.2f}s | "
                      f"mediana {statistics.median(st.duracoes):.2f}s | max {max(st.duracoes):.2f}s")
            print(" leitura: cada PASSAGEM deve ser UMA aproximacao da garrafa.")
            print(" para veredito formal (PASS/FAIL): python3 scripts/poc01_teste.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
