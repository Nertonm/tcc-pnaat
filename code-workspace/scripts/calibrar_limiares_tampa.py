"""Calibracao empirica de um limiar da tampa (D-24): deriva o limiar de medicoes rotuladas.

Disciplina exigida por D-24:
  - limiar sem fonte primaria so vale se houver **validacao empirica registrada** (protocolo, n, resultado);
  - o n minimo e exigido: sem amostra suficiente o script **nao emite** limiar (evita numero inventado);
  - a saida carrega a procedencia (hash do CSV, n por classe, data, metodo).

Metodo: varredura de candidatos (pontos medios entre valores ordenados); escolhe o que maximiza o indice
de Youden (sens + espec - 1); empate -> maior margem (ponto medio do intervalo sem sobreposicao).

Uso:
  python scripts/calibrar_limiares_tampa.py --medicoes m.csv --coluna tilt_graus --pos mal_rosqueada \
      --saida limiares_tampa.json [--n-min 20]
  m.csv: item_id,classe,<coluna>          classe em {normal, mal_rosqueada}
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path

Z95 = 1.959963984540054


def wilson(k: int, n: int, limite: str = "lb", z: float = Z95) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    z2 = z * z
    c = p + z2 / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, (c - m) / (1 + z2 / n)) if limite == "lb" else min(1.0, (c + m) / (1 + z2 / n))


def estat(valores: list[float]) -> dict:
    if not valores:
        return {"n": 0}
    s = sorted(valores)
    n = len(s)
    media = sum(s) / n
    var = sum((x - media) ** 2 for x in s) / (n - 1) if n > 1 else 0.0

    def p(q: float) -> float:
        if n == 1:
            return s[0]
        i = q * (n - 1)
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        return s[lo] + (s[hi] - s[lo]) * (i - lo)

    return {"n": n, "media": media, "desvio": math.sqrt(var), "min": s[0], "max": s[-1],
            "p2_5": p(0.025), "p97_5": p(0.975)}


def candidatos(a: list[float], b: list[float]) -> list[float]:
    """Pontos medios entre valores ordenados distintos das duas classes (determinístico)."""
    vals = sorted(set(a) | set(b))
    return [(x + y) / 2 for x, y in zip(vals, vals[1:])] or [vals[0]]


def avaliar_limiar(limiar: float, defeito: list[float], normal: list[float], maior_e_pior: bool = True):
    def positivo(x):
        return x >= limiar if maior_e_pior else x <= limiar
    tp = sum(1 for x in defeito if positivo(x))
    fn = len(defeito) - tp
    fp = sum(1 for x in normal if positivo(x))
    tn = len(normal) - fp
    sens = tp / len(defeito) if defeito else 0.0
    espec = tn / len(normal) if normal else 0.0
    return {"limiar": limiar, "tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "sensibilidade": sens, "especificidade": espec, "youden": sens + espec - 1}


def calibrar(defeito: list[float], normal: list[float], n_min: int = 20,
             maior_e_pior: bool = True) -> dict:
    if len(defeito) < n_min or len(normal) < n_min:
        return {"status": "AMOSTRA_INSUFICIENTE",
                "n_defeito": len(defeito), "n_normal": len(normal), "n_min": n_min,
                "motivo": "D-24 exige n declarado; abaixo de n_min nao se emite limiar",
                "faltam": max(0, n_min - len(defeito)) + max(0, n_min - len(normal))}
    aval = [avaliar_limiar(c, defeito, normal, maior_e_pior) for c in candidatos(defeito, normal)]
    melhor_j = max(a["youden"] for a in aval)
    empatados = [a for a in aval if abs(a["youden"] - melhor_j) < 1e-12]
    # desempate: maior margem = mais distante dos dois extremos vizinhos
    def margem(a):
        d_min = min((abs(x - a["limiar"]) for x in defeito), default=0.0)
        n_min_ = min((abs(x - a["limiar"]) for x in normal), default=0.0)
        return -min(d_min, n_min_)
    escolhido = sorted(empatados, key=lambda a: (margem(a), a["limiar"]))[0]

    # zona cinzenta: intervalo de sobreposicao (onde as duas classes coexistem)
    if maior_e_pior:
        sobrepoe = bool(defeito and normal and max(normal) > min(defeito))
        lo, hi = (min(defeito), max(normal)) if sobrepoe else (None, None)
    else:
        sobrepoe = bool(defeito and normal and min(normal) < max(defeito))
        lo, hi = (max(defeito), min(normal)) if sobrepoe else (None, None)

    est_d, est_n = estat(defeito), estat(normal)
    escolhido.update({
        "status": "CALIBRADO",
        "regra": "medida >= limiar => defeito" if maior_e_pior else "medida <= limiar => defeito",
        "metodo": "Youden J com desempate por margem (varredura determinista)",
        "n_defeito": len(defeito), "n_normal": len(normal),
        "sensibilidade_lb95": wilson(escolhido["tp"], len(defeito), "lb"),
        "especificidade_lb95": wilson(escolhido["tn"], len(normal), "lb"),
        "estat_defeito": est_d, "estat_normal": est_n,
        "zona_cinzenta": [lo, hi] if sobrepoe else None,
        "sobreposicao": sobrepoe,
        "procedencia": "calibracao empirica no conjunto proprio (D-24b)",
    })
    return escolhido


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Calibra um limiar da tampa a partir de medicoes rotuladas")
    ap.add_argument("--medicoes", required=True)
    ap.add_argument("--coluna", required=True)
    ap.add_argument("--coluna-classe", default="classe")
    ap.add_argument("--pos", default="mal_rosqueada", help="valor da coluna de classe considerado defeito")
    ap.add_argument("--neg", default="normal")
    ap.add_argument("--n-min", type=int, default=20)
    ap.add_argument("--menor-e-pior", action="store_true", help="para medidas em que menor valor = defeito")
    ap.add_argument("--saida", default=None)
    a = ap.parse_args(argv)

    p = Path(a.medicoes)
    defeito, normal = [], []
    with p.open(newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            try:
                v = float(linha[a.coluna])
            except (KeyError, TypeError, ValueError):
                continue
            c = (linha.get(a.coluna_classe) or "").strip()
            (defeito if c == a.pos else normal if c == a.neg else []).append(v)

    r = calibrar(defeito, normal, a.n_min, maior_e_pior=not a.menor_e_pior)
    r["medida"] = a.coluna
    r["entrada"] = str(p)
    r["sha256_entrada"] = hashlib.sha256(p.read_bytes()).hexdigest()
    r["data"] = datetime.now().isoformat(timespec="seconds")
    if a.saida and r.get("status") == "CALIBRADO":
        Path(a.saida).write_text(json.dumps(r, indent=1, ensure_ascii=False))
        print("limiares gravados em", a.saida)
    print(json.dumps(r, indent=1, ensure_ascii=False))
    return 0 if r.get("status") == "CALIBRADO" else 2


if __name__ == "__main__":
    sys.exit(main())
