#!/usr/bin/env python3
"""Simula o debounce básico do trigger de presença sem hardware.

Serve para validar abertura e fechamento antes de ligar a placa. Não reproduz warm-up, armamento,
guarda temporal, heartbeat, persistência em flash ou temporização real do `esp/main.py`.

    python3 host/simular_trigger.py --caso passagem_limpa
    python3 host/simular_trigger.py --caso todos
    python3 host/simular_trigger.py --niveis 1,1,0,0,0,0,0,0,1,1

Convencao do E18-D80NK: nivel 0 (LOW) = objeto dentro do alcance (active low).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from presence import PresenceTrigger, present_from_sensor

DEBOUNCE_MS = 20
STABLE_READS = 5
MISS_READS = 5
CASOS: dict[str, list[int]] = {
    # passagem normal: livre -> objeto -> livre
    "passagem_limpa": [1] * 6 + [0] * 10 + [1] * 10,
    # ruido: um unico pulso curto NAO pode abrir janela
    "pulso_isolado": [1] * 6 + [0] + [1] * 10,
    # duas passagens separadas: duas janelas, sem duplicar item
    "duas_passagens": [1] * 4 + [0] * 8 + [1] * 8 + [0] * 8 + [1] * 6,
    # objeto parado na frente do sensor: abre uma vez e mantem (nao reabre a cada leitura)
    "objeto_parado": [1] * 4 + [0] * 20 + [1] * 6,
    # objeto tremendo no limite do alcance: hits intercalados nao devem abrir
    "limite_instavel": [1] * 4 + [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1] + [1] * 4,
}


def simular(niveis: list[int], views=("topo", "lateral1", "lateral2"), verbose: bool = True) -> dict:
    trigger = PresenceTrigger(views=views, stable_reads=STABLE_READS, miss_reads=MISS_READS)
    eventos: list[dict] = []
    janela_aberta = False
    for i, nivel in enumerate(niveis):
        presente = present_from_sensor(nivel)
        run = trigger.update(presente)
        if run is not None:
            janela_aberta = True
            eventos.append({"i": i, "evento": "CAPTURE_WINDOW_OPEN",
                            "janela": run.item_window_id, "views": list(run.views)})
            if verbose:
                print(f"  t{i:02d} nivel={nivel} -> PRESENTE   "
                      f"CAPTURE_WINDOW_OPEN views={','.join(run.views)}")
        elif janela_aberta and not trigger.is_open:
            janela_aberta = False
            eventos.append({"i": i, "evento": "CAPTURE_WINDOW_CLOSE"})
            if verbose:
                print(f"  t{i:02d} nivel={nivel} -> livre      CAPTURE_WINDOW_CLOSE")
        elif verbose:
            estado = "PRESENTE" if presente else "livre"
            print(f"  t{i:02d} nivel={nivel} -> {estado}")
    return {
        "niveis": niveis,
        "eventos": eventos,
        "janelas_abertas": sum(1 for e in eventos if e["evento"] == "CAPTURE_WINDOW_OPEN"),
        "janelas_fechadas": sum(1 for e in eventos if e["evento"] == "CAPTURE_WINDOW_CLOSE"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--caso", choices=[*sorted(CASOS), "todos"], default="passagem_limpa")
    ap.add_argument("--niveis", help="sequencia de niveis logicos separada por virgula")
    ap.add_argument("--json", type=Path, default=None, help="salva o resultado em JSON")
    args = ap.parse_args()

    print(f"PoC-01 simulada (sem hardware): abertura: {STABLE_READS} leituras, "
          f"fechamento: {MISS_READS} leituras, amostra nominal: {DEBOUNCE_MS} ms")

    resultados: dict[str, dict] = {}
    if args.niveis:
        niveis = [int(x) for x in args.niveis.split(",")]
        print("\n== caso personalizado ==")
        resultados["personalizado"] = simular(niveis)
    else:
        nomes = sorted(CASOS) if args.caso == "todos" else [args.caso]
        for nome in nomes:
            print(f"\n== {nome} ==")
            resultados[nome] = simular(CASOS[nome])

    print("\n--- resumo ---")
    for nome, r in resultados.items():
        print(f"  {nome:<18} janelas_abertas={r['janelas_abertas']} "
              f"fechadas={r['janelas_fechadas']}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(resultados, indent=1, ensure_ascii=False))
        print("json:", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
