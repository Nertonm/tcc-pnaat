#!/usr/bin/env python3
"""Escopo do sensor PoC-01: mostra ao vivo COMO o sensor esta captando (1 bit + taxa de oscilacao).

O E18-D80NK entrega apenas 1 bit (LOW = detectou). O que se ve aqui:
  * o nivel atual e a faixa dos ultimos segundos (cada coluna = 0,5 s);
  * a TAXA DE BORDAS (oscilacoes/s): perto do limiar do potenciometro a linha pisca muito;
    com o alcance bem ajustado, ela fica estavel em repouso ate o item entrar;
  * tempo em deteccao (%), janelas, descartes da guarda e se o firmware esta armado.

Le o stream do supervisor (passivo, nunca abre a porta).

    python3 poc01_escopo.py [--janela 40] [--intervalo 1.0]
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import deque
from pathlib import Path

BASE = Path.home() / "poc01"
STREAM = BASE / "stream.log"
BLOCO = "="           # 1 bit: deteccao
VAZIO = "-"           # 1 bit: repouso


def parse(linha: str) -> dict | None:
    if "EV " not in linha:
        return None
    carimbo, resto = linha.split(" EV ", 1)
    partes = resto.split()
    if not partes:
        return None
    try:
        ts = time.mktime(time.strptime(carimbo.strip(), "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None
    ev = {"_evento": partes[0], "_ts": ts}
    for item in partes[1:]:
        if "=" in item:
            k, v = item.split("=", 1)
            ev[k] = v
    return ev


class Escopo:
    def __init__(self, janela_s: float, passo_s: float = 0.5) -> None:
        self.passo = passo_s
        self.n = int(janela_s / passo_s)
        self.hist: deque[str] = deque([VAZIO] * self.n, maxlen=self.n)
        self.nivel: int | None = None
        self.armado = False
        self.janelas = 0
        self.descartes = 0
        self.ultimo = ""
        self.bordas: deque[float] = deque(maxlen=600)
        self.t_ultimo_passo = time.time()
        self.t_ultimo_evento = time.time()
        self.arm_avisos = 0

    def aplicar(self, ev: dict) -> None:
        nome = ev["_evento"]
        self.ultimo = nome
        self.t_ultimo_evento = time.time()
        # o nivel vem em QUALQUER evento que o carregue (LEVEL, ARMED, OPEN, CLOSE, ARM_WAIT...):
        # assim a tela nunca fica "sem leitura" so porque a linha nao mudou de estado.
        if "nivel" in ev:
            try:
                self.nivel = int(ev["nivel"])
            except ValueError:
                pass
        if nome == "ARMED":
            self.armado = True
        elif nome == "ARM_WAIT":
            self.arm_avisos += 1
        elif nome == "LEVEL":
            self.bordas.append(ev["_ts"])
        elif nome == "OPEN":
            self.janelas += 1
        elif nome == "SUPPRESSED":
            self.descartes += 1

    def avancar(self) -> None:
        while time.time() - self.t_ultimo_passo >= self.passo:
            self.t_ultimo_passo += self.passo
            self.hist.append(BLOCO if self.nivel == 0 else VAZIO)

    def taxa_bordas(self, segundos: float = 10.0) -> float:
        agora = time.time()
        recentes = [t for t in self.bordas if agora - t <= segundos]
        return len(recentes) / segundos

    def em_deteccao(self) -> float:
        return 100.0 * sum(1 for c in self.hist if c == BLOCO) / len(self.hist)

    def render(self, intervalo: float) -> str:
        estado = "objeto/baixo" if self.nivel == 0 else ("repouso/alto" if self.nivel == 1 else "sem leitura")
        idade = time.time() - self.t_ultimo_evento
        aviso = "" if idade < 5 else f"  [sem eventos há {idade:.0f}s]"
        return (
            f"{time.strftime('%H:%M:%S')} nivel={self.nivel if self.nivel is not None else '-'} "
            f"({estado}) | armado={'sim' if self.armado else 'NAO'} | bordas={self.taxa_bordas(10):.1f}/s | "
            f"em deteccao={self.em_deteccao():.0f}% | janelas={self.janelas} descartes={self.descartes}\n"
            f"  |{''.join(self.hist)}|  ultimo={self.ultimo}{aviso}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stream", type=Path, default=STREAM)
    ap.add_argument("--janela", type=float, default=20.0, help="segundos visiveis (cada coluna = 0,5 s)")
    ap.add_argument("--intervalo", type=float, default=1.0, help="atualizacao em segundos")
    args = ap.parse_args()

    if not args.stream.exists():
        print(f"ERRO: {args.stream} nao existe. O supervisor esta rodando?")
        return 2

    print("=" * 78)
    print(" ESCOPO DO SENSOR: como o E18-D80NK esta captando (o modulo projeto bit)")
    print(" " + "=" * 76)
    print("   '=' = o sensor esta DETECTANDO (nivel baixo)     '-' = repouso (nivel alto)")
    print("   'bordas/s' alto = linha oscilando = potenciometro no limite (sensivel demais)")
    print("   'armado=NAO' com nivel=0 = ha algo no campo ou alcance grande demais")
    print("=" * 78)

    esc = Escopo(args.janela)
    # semeia o estado com o historico recente: sem isso a tela comeca "sem leitura" quando o
    # firmware so loga a cada 5 s (o nivel nao mudou, entao nada novo chega).
    historico = args.stream.read_text(errors="replace").splitlines()[-300:]
    for linha in historico:
        ev = parse(linha)
        if ev:
            esc.aplicar(ev)
    print(f"(estado inicial lido de {len(historico)} linhas do stream)")

    with args.stream.open() as f:
        f.seek(f.seek(0, 2))
        proximo = time.time()
        try:
            while True:
                linha = f.readline()
                if linha:
                    ev = parse(linha.rstrip("\n"))
                    if ev:
                        esc.aplicar(ev)
                else:
                    time.sleep(0.1)
                esc.avancar()
                if time.time() >= proximo:
                    print(esc.render(args.intervalo), flush=True)
                    proximo = time.time() + args.intervalo
        except KeyboardInterrupt:
            print("\nresumo: janelas=%d descartes=%d avisos_de_nao_armado=%d"
                  % (esc.janelas, esc.descartes, esc.arm_avisos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
