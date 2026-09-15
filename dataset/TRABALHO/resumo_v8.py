#!/usr/bin/env python3
"""Resumo de uma linha da cadeia v8 (roda no host de treino; o vigia chama por ssh).

Silêncio quando não terminou: quem decide é o vigia, aqui só se lê o que existe.
"""
import json
from pathlib import Path

M = Path(__file__).resolve().parents[2].parent.parent / "pnaat-modelos"


def carrega(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


kf = sorted(M.glob('v8-3-lateral-detector-roi/kfold-*.json'))
cal = carrega(M / 'v8a-lateral-detector-roi/calibracao-limiar.json', {})
dec = carrega(M / 'v8a-lateral-detector-roi/decisao-operacional.json', {})
pkg = carrega(M / 'ENTREGA/v8a-lateral/modelo.json', {})

partes = []
if kf:
    d = carrega(kf[-1], {})
    partes.append(f"k-fold mAP50 {d.get('mAP50_media')} ± {d.get('mAP50_desvio')} "
                  f"[{d.get('mAP50_min')}–{d.get('mAP50_max')}]")
if pkg:
    partes.append(f"peso sha {str(pkg.get('sha256'))[:12]}…")
if cal.get('limiares_escolhidos_na_val'):
    lim = ', '.join(f"{k} {v['conf']}" for k, v in cal['limiares_escolhidos_na_val'].items())
    partes.append(f"limiares (val): {lim}")
if dec:
    partes.append(f"decisão {dec.get('acertos')}/{dec.get('total')} · {dec.get('revisar')} em revisão "
                  f"· acurácia s/ revisão {dec.get('acuracia_sem_revisar')}")
print(' · '.join(partes) if partes else 'cadeia terminou, sem artefatos lidos')
