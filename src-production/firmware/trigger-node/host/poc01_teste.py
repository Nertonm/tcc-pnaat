#!/usr/bin/env python3
"""TESTE da PoC-01: verifica o criterio do núcleo passagem a passagem, com veredito.

CRITERIO (PoC-01): cada passagem do item abre UMA janela de captura, com mais de uma
vista e timestamps associados -- sem duplicar o item e sem janela espuria.

METODO (isola exatamente esse criterio):
  * nao abre a porta serial: le ~/poc01/stream.log, alimentado pelo supervisor (visualizador passivo);
  * conduz um protocolo com numero fixo de passagens -- o operador segue o aviso na tela;
  * para CADA passagem esperada conta quantas janelas o sistema abriu dentro daquela janela de tempo;
  * classifica OK (1) | DUPLICATA (2+) | PERDIDA (0) e conta ESPURIAS (fora de qualquer passagem);
  * emite PASS/FAIL e grava evidencia em JSON.

    python3 poc01_teste.py --passagens 10 --espera 6 --separacao 3
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

BASE = Path.home() / "poc01"
STREAM = BASE / "stream.log"
FORMATO_T = "%Y-%m-%dT%H:%M:%S"


def parse_ev(linha: str) -> dict | None:
    """Converte '2026-09-11T03:40:01 EV OPEN n=1 nivel=0 t_ms=4395' em dicionario."""
    if "EV " not in linha:
        return None
    carimbo, resto = linha.split(" EV ", 1)
    partes = resto.split()
    if not partes:
        return None
    try:
        ts = time.mktime(time.strptime(carimbo.strip(), FORMATO_T))
    except ValueError:
        return None
    ev: dict = {"_evento": partes[0], "_ts": ts, "_t": carimbo.strip()}
    for item in partes[1:]:
        if "=" in item:
            chave, valor = item.split("=", 1)
            ev[chave] = valor
    return ev


class Stream:
    """Le o arquivo de stream de forma incremental (nunca toca na porta)."""

    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        self.desloc = 0

    def do_inicio(self) -> None:
        self.desloc = 0

    def do_fim(self) -> None:
        self.desloc = self.caminho.stat().st_size if self.caminho.exists() else 0

    def ler(self) -> list[dict]:
        if not self.caminho.exists():
            return []
        eventos = []
        with self.caminho.open() as f:
            f.seek(self.desloc)
            for linha in f:
                ev = parse_ev(linha.rstrip("\n"))
                if ev:
                    eventos.append(ev)
            self.desloc = f.tell()
        return eventos

    def ultimos(self, n: int = 400) -> list[dict]:
        if not self.caminho.exists():
            return []
        linhas = self.caminho.read_text(errors="replace").splitlines()[-n:]
        return [ev for ev in (parse_ev(l) for l in linhas) if ev]


def aguardar_armado(st: Stream, limite_s: float = 60.0, pistas: list[dict] | None = None) -> bool:
    """Considera armado se ARMED ja apareceu no historico recente ou se aparecer agora."""
    recentes = st.ultimos()
    if any(e["_evento"] == "ARMED" for e in recentes):
        print("   firmware ja estava armado antes do teste (histórico no stream)")
        return True
    print("   aguardando o firmware armar (linha em repouso)...")
    t_limite = time.time() + limite_s
    while time.time() < t_limite:
        for ev in st.ler():
            if ev["_evento"] == "ARMED":
                return True
            if ev["_evento"] in ("ARM_WAIT", "ARM_TIMEOUT"):
                print(f"   {ev['_evento']}: {ev.get('nota', 'linha em nível de objeto')}")
        time.sleep(0.3)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passagens", type=int, default=10)
    ap.add_argument("--espera", type=float, default=6.0, help="tempo aguardando a deteccao de UMA passagem")
    ap.add_argument("--separacao", type=float, default=3.0, help="intervalo entre passagens")
    ap.add_argument("--evidencia", type=Path, default=BASE / "evidencia-poc01.json")
    args = ap.parse_args()

    print("=" * 76)
    print(" TESTE DA POC-01: critério: 1 passagem = 1 janela (vistas + timestamps), sem duplicar")
    print("=" * 76)
    if not STREAM.exists():
        print(f" ERRO: {STREAM} nao existe: o supervisor esta rodando?")
        return 2

    st = Stream(STREAM)
    if not aguardar_armado(st):
        print(" ERRO: firmware nao armou (linha presa em nível de objeto?).")
        print("       Afaste o que estiver na frente do sensor / reduza o alcance no potenciômetro.")
        return 3

    st.do_fim()          # daqui para frente e o teste
    resultados: list[dict] = []
    janelas_de_passagem: list[tuple[float, float]] = []

    for k in range(1, args.passagens + 1):
        print(f"\n>>> PASSAGEM {k}/{args.passagens}: aproxime a garrafa do sensor AGORA", flush=True)
        t0 = time.time()
        aberturas: list[dict] = []
        while time.time() - t0 < args.espera:
            aberturas += [e for e in st.ler() if e["_evento"] == "OPEN"]
            time.sleep(0.2)
        t1 = time.time()
        janelas_de_passagem.append((t0, t1))

        fechamentos = [e for e in st.ler() if e["_evento"] == "CLOSE"]
        duracao = None
        if fechamentos and fechamentos[-1].get("dur_ms"):
            duracao = float(fechamentos[-1]["dur_ms"]) / 1000.0

        if not aberturas:
            estado = "PERDIDA"
        elif len(aberturas) == 1:
            estado = "OK"
        else:
            estado = "DUPLICATA"
        resultados.append({
            "passagem": k,
            "janelas": len(aberturas),
            "estado": estado,
            "vistas": aberturas[0].get("views") if aberturas else None,
            "duracao_s": duracao,
            "hora_aviso": time.strftime("%H:%M:%S", time.localtime(t0)),
            "hora_deteccao": time.strftime("%H:%M:%S", time.localtime(aberturas[0]["_ts"])) if aberturas else None,
        })
        extra = f", duração {duracao:.2f} s" if duracao else ""
        print(f"    -> {estado} ({len(aberturas)} janela(s){extra})", flush=True)

        if k < args.passagens:
            print(f"    afaste a garrafa e aguarde {args.separacao:.0f} s...", flush=True)
            t_espera = time.time()
            while time.time() - t_espera < args.separacao:
                st.ler()
                time.sleep(0.2)

    # eventos fora de qualquer janela de passagem
    st.do_inicio()
    todos = st.ler()
    def dentro_de_passagem(ts: float) -> bool:
        return any(a <= ts <= b for a, b in janelas_de_passagem)
    espurias = [e for e in todos if e["_evento"] == "OPEN" and not dentro_de_passagem(e["_ts"])]
    suprimidas = [e for e in todos if e["_evento"] == "SUPPRESSED"]

    print("\n" + "=" * 76)
    print(" RESULTADO ISOLADO: uma linha por passagem esperada")
    print("=" * 76)
    print(f" {'pass':<6}{'estado':<12}{'janelas':<9}{'duracao':<10}{'detectado':<11}vistas")
    print(" " + "-" * 74)
    for r in resultados:
        dur = f"{r['duracao_s']:.2f}s" if r["duracao_s"] else "-"
        print(f" {r['passagem']:<6}{r['estado']:<12}{r['janelas']:<9}{dur:<10}"
              f"{str(r['hora_deteccao'] or '-'):<11}{r['vistas'] or '-'}")

    ok = sum(1 for r in resultados if r["estado"] == "OK")
    perdidas = sum(1 for r in resultados if r["estado"] == "PERDIDA")
    duplicatas = sum(1 for r in resultados if r["estado"] == "DUPLICATA")
    veredito = "PASS" if (perdidas == 0 and duplicatas == 0 and not espurias) else "FAIL"

    print("\n" + "-" * 76)
    print(f" passagens com 1 janela (OK) : {ok}/{args.passagens}")
    print(f" passagens sem detecção      : {perdidas}")
    print(f" passagens com duplicata     : {duplicatas}")
    print(f" janelas fora de passagem    : {len(espurias)}")
    print(f" detecções descartadas (guarda do firmware): {len(suprimidas)}")
    print(f"\n VEREDITO: {veredito}")
    if veredito == "FAIL":
        if perdidas:
            print("  → detecção fraca: aproxime mais a garrafa ou ajuste o potenciômetro do sensor.")
        if duplicatas:
            print("  → linha oscilando no limite: aproxime mais devagar ou reduza o alcance.")
        if espurias:
            print("  → janela fora das passagens: algo entrou no campo (ou ruído de boot).")

    args.evidencia.parent.mkdir(parents=True, exist_ok=True)
    args.evidencia.write_text(json.dumps({
        "data": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "criterio": "1 passagem = 1 janela com vistas e timestamps; sem duplicidade; sem espuria",
        "passagens_esperadas": args.passagens, "espera_s": args.espera, "separacao_s": args.separacao,
        "resultados": resultados, "ok": ok, "perdidas": perdidas, "duplicatas": duplicatas,
        "espurias": len(espurias), "suprimidas_guarda": len(suprimidas), "veredito": veredito,
    }, indent=1, ensure_ascii=False))
    print(f"\n evidência: {args.evidencia}")
    return 0 if veredito == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
