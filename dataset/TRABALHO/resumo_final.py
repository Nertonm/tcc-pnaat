#!/usr/bin/env python3
"""Resumo das cadeias finais: v9a (tampa com rótulos corrigidos) + corpo-cls."""
import json
from pathlib import Path

M = Path(__file__).resolve().parents[2].parent.parent / 'pnaat-modelos'


def le(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


linhas = []

# --- v9a: tampa com rótulos no espaço do recorte
kf = sorted(M.glob('v9-3-lateral-detector-roi/kfold-*.json'))
if kf:
    d = le(kf[-1], {})
    linhas.append(f"tampa v9a (rótulos corrigidos) k-fold mAP50 {d.get('mAP50_media')} ± {d.get('mAP50_desvio')}")
lim = le(M / 'v9a-lateral-detector-roi/limiares-teste.json')
if lim:
    pc = lim.get('limiares', {}).get('0.15', {}).get('por_classe', {})
    if pc:
        linhas.append('tampa no teste: ' + ' · '.join(f"{k} F1 {v['f1']:.3f}" for k, v in pc.items()))
pkg = le(M / 'ENTREGA/v9a-lateral/modelo.json')
if pkg:
    linhas.append(f"peso v9a sha {str(pkg.get('sha256'))[:12]}…")

# --- corpo-cls
pkgc = le(M / 'ENTREGA/corpo-cls/modelo.json')
if pkgc:
    linhas.append(f"corpo (classificador) sha {str(pkgc.get('sha256'))[:12]}…")
for sp in ('train', 'test'):
    p = M / 'corpo-cls/dataset' / sp
    if p.is_dir():
        n = len(list(p.glob('*/*')))
        linhas.append(f"  corpo-cls {sp}: {n} recortes")

print(' · '.join(linhas) if linhas else 'sem artefatos ainda')
