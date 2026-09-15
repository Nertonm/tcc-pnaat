#!/usr/bin/env python3
"""PREFLIGHT DE PRÉ-PROCESSAMENTO — falha alto quando o consumidor diverge do contrato.

Roda onde o consumidor vive (capture, detector, site). Compara o que ELE vai fazer com o que o
CONTRATO manda e sai != 0 na divergência. É a diferença entre "copiei o arquivo" (resolve hoje,
quebra na próxima mudança) e "o gate não deixa passar" (resolve a classe).

Uso:
  preflight_preproc.py --contrato <preprocessamento.json> --roi-local <roi.json do consumidor>
                       [--imgsz 480] [--rotacao usb=90,espcam=180]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def fingerprint(roi: dict, rot: dict, imgsz: int, classes: list[str], regra: str,
                modelo_sha256: str | None, letterbox: bool = True) -> str:
    canonico = {'roi_por_camera': roi, 'rotacao_graus': rot, 'imgsz_treino': imgsz,
                'letterbox': letterbox, 'classes': classes, 'regra_decisao': regra,
                'modelo_sha256': modelo_sha256}
    return hashlib.sha256(json.dumps(canonico, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--contrato', required=True)
    ap.add_argument('--roi-local', help='roi.json que o consumidor vai realmente usar')
    ap.add_argument('--imgsz', type=int)
    ap.add_argument('--rotacao', help='ex.: usb=90,espcam=180')
    ap.add_argument('--modelo-local', help='.pt que o consumidor vai carregar (conferido por sha)')
    a = ap.parse_args()

    c = json.loads(Path(a.contrato).read_text())
    falhas, avisos = [], []

    # 1) ROI
    if a.roi_local:
        loc = json.loads(Path(a.roi_local).read_text())
        roi_loc = {k: v.get('roi_normalizada') for k, v in (loc.get('cameras') or {}).items()}
        for cam, valor in (c['roi_por_camera'] or {}).items():
            if cam not in roi_loc:
                avisos.append(f'ROI: câmera {cam} ausente no consumidor')
                continue
            if roi_loc[cam] != valor:
                falhas.append(f'ROI divergente em {cam}: contrato {valor} x consumidor {roi_loc[cam]}')
    else:
        avisos.append('ROI: não informada (não conferida)')

    # 2) rotação
    if a.rotacao:
        rot_loc = {}
        for parte in a.rotacao.split(','):
            k, _, v = parte.partition('=')
            rot_loc[k.strip()] = int(v)
        for cam, graus in (c['rotacao_graus'] or {}).items():
            if cam in rot_loc and rot_loc[cam] != graus:
                falhas.append(f'rotação divergente em {cam}: contrato {graus}° x consumidor {rot_loc[cam]}°')

    # 3) imgsz x limiar calibrado
    if a.imgsz:
        if a.imgsz != c['imgsz_treino']:
            avisos.append(f'imgsz {a.imgsz} != imgsz de treino {c["imgsz_treino"]}')
        lim = (c['limiares_por_imgsz'] or {}).get(str(a.imgsz))
        if not lim:
            falhas.append(f'imgsz {a.imgsz}: sem limiar no contrato (não calibrado neste tamanho)')
        elif not lim.get('calibrado', False):
            falhas.append(f'imgsz {a.imgsz}: limiar marcado como NÃO calibrado — recalibrar antes de usar')

    # 4) modelo (sha)
    if a.modelo_local:
        h = hashlib.sha256(Path(a.modelo_local).read_bytes()).hexdigest()
        if c['modelo'].get('sha256') and h != c['modelo']['sha256']:
            falhas.append(f'modelo divergente: contrato {c["modelo"]["sha256"][:16]}… x consumidor {h[:16]}…')

    print(f"contrato: {c['nome']} v{c['versao']} · fingerprint {c['fingerprint'][:24]}…")
    for x in avisos:
        print(f'  AVISO  {x}')
    for x in falhas:
        print(f'  FALHA  {x}')
    if falhas:
        print(f'\nRESULTADO: DIVERGENTE ({len(falhas)} falha(s)) — não roda assim')
        return 1
    print('\nRESULTADO: CONFORME')
    return 0


if __name__ == '__main__':
    sys.exit(main())
