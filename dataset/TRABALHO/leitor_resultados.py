#!/usr/bin/env python3
"""Leitor compacto dos JSONs de avaliação/limiar (uso: leitor.py arquivo [...])."""
import json
import sys
from pathlib import Path


def mostra(p: Path) -> None:
    print('===', p.name, f'({p.parent.parent.name})')
    d = json.loads(p.read_text())
    for chave in ('por_dominio', 'dominios'):
        for dom, v in (d.get(chave) or {}).items():
            if not isinstance(v, dict):
                continue
            imgs = v.get('imagens') or v.get('n_imagens')
            if not imgs:
                continue
            m = v.get('metricas') or v      # o gravador aninha as metricas em 'metricas'

            def _g(*chaves):
                for c in chaves:
                    if c in m:
                        return m[c]
                return 0.0
            print(f"  {dom}: {imgs} imgs  P={_g('precision(B)', 'precision'):.3f} "
                  f"R={_g('recall(B)', 'recall'):.3f} mAP50={_g('mAP50(B)', 'mAP50'):.3f} "
                  f"mAP50-95={_g('mAP50-95(B)', 'mAP50-95'):.3f}")
            for c, cv in (v.get('por_classe') or {}).items():
                if isinstance(cv, dict):
                    print(f"     {c:16s} mAP50={cv.get('mAP50', 0):.3f} mAP50-95={cv.get('mAP50-95', 0):.3f}")
                else:
                    print(f"     {c:16s} {cv}")
    for conf, v in (d.get('limiares') or {}).items():
        print(f"  limiar {conf}: F1 macro={v.get('f1_macro')}")
        for c, cv in (v.get('por_classe') or {}).items():
            print(f"     {c:16s} tp={cv['tp']:3d} fp={cv['fp']:3d} fn={cv['fn']:3d} "
                  f"P={cv['precisao']:.3f} R={cv['recall']:.3f} F1={cv['f1']:.3f}")
    for conf, v in (d.get('por_limiar') or {}).items():
        print(f"  decisao limiar {conf}: acuracia {v.get('acertos')}/{v.get('total')} = {v.get('acuracia')}")
        for vt, preds in (v.get('confusao') or {}).items():
            print(f"     verdade {vt:16s} -> {preds}")
    if d.get('metricas_val'):
        print('  val:', {k: round(v, 4) for k, v in d['metricas_val'].items()})


for arg in sys.argv[1:]:
    p = Path(arg)
    if p.is_file():
        mostra(p)
    else:
        print('(ausente)', arg)
