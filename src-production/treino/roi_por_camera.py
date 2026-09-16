#!/usr/bin/env python3
"""Deriva a ROI por câmera a partir das CAIXAS JÁ ANOTADAS (não de chute).

Por que: a resolução efetiva da tampa depende de quantos pixels ela ocupa na
entrada do modelo. Recortar a faixa onde a garrafa sempre aparece (ROI fixa, o rig
é fixo) sobe a resolução efetiva e corta compute; é o ganho mais barato que temos
(ver docs/reference/augmentacao-e-preprocessing-pnaat.md §6).

Saída: roi-por-camera.json com, por câmera, o retângulo normalizado (0-1) e o
retângulo em pixel na resolução nativa. Gate: a ROI tem de conter >= 95% das
caixas anotadas daquela câmera; senão ela está errada e o script reprova.

Uso: python roi_por_camera.py [--margem 0.12] [--csv ...]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import os as _os
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, CONTRATO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, CONTRATO

CSV = _RAIZ_REPO / 'dataset/TRABALHO/anotacoes-ls.csv'
SAIDA = CONTRATO / 'roi-por-camera.json'
RESOLUCOES = {                      # resolução nativa conhecida por câmera
    'csi': (1296, 972),
    'usb': (720, 1280),             # rotacionada 90° no fluxo de captura
    'espcam': (640, 480),
    'rig': (1296, 972),
}
EXCLUI = {'excluir_do_treino', 'imagem_ruim'}


def camera_do_caminho(rel: str) -> str:
    p = Path(rel)
    partes = p.parts
    if partes and partes[0] == 'corpus' and len(partes) >= 3:
        direto = partes[2]
        if direto in RESOLUCOES:
            return direto
        # O nome do diretorio de captura carrega o host de origem, que nao entra no repo
        # publico: vem do ambiente, com default neutro. A camera nao muda, so o prefixo.
        prefixos_espcam = ('espcam', _os.environ.get('PNAAT_DIR_ESPCAM_BANCADA', 'espcam-bancada'))
        prefixos_misto = (_os.environ.get('PNAAT_DIR_CORPUS_MISTO', 'capturas-corpus'),
                          _os.environ.get('PNAAT_DIR_CORPUS_MISTO_CURTO', 'corpus-multiuso'))
        if direto.startswith(prefixos_espcam):
            return 'espcam'
        if direto.startswith(prefixos_misto):
            return 'mista'      # corpus multiuso: csi+usb+espcam na mesma raiz
    if partes and partes[0] == 'dataset' and len(partes) >= 2:
        return 'rig' if partes[1] == 'nosso' else partes[1]
    if partes and partes[0] == 'nosso':
        return 'rig'                       # o CSV do export usa caminho relativo a dataset/
    return 'desconhecida'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--margem', type=float, default=0.12, help='folga relativa ao lado da imagem')
    ap.add_argument('--csv', default=str(CSV))
    ap.add_argument('--vista', default='lateral', choices=('lateral', 'topo'),
                    help='a ROI do recorte e POR VISTA: misturar vistas no mesmo envelope satura'
                         ' o retangulo (foi o defeito medido em 2026-09-16)')
    ap.add_argument('--saida', type=Path, default=SAIDA)
    ap.add_argument('--permitir-saturacao', action='store_true',
                    help='aceita ROI que cobre o quadro inteiro (so quando for o caso legitimo)')
    a = ap.parse_args()

    por_camera = defaultdict(list)
    with Path(a.csv).open(newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if (r.get('valido') or '') != 'sim':
                continue
            if (r.get('vista') or '') != a.vista:
                continue                      # a ROI do recorte e por vista
            coher = {c.strip() for c in (r.get('coerencia') or '').split(';') if c.strip()}
            if coher & EXCLUI:
                continue
            try:
                caixas = json.loads(r.get('caixas') or '[]')
            except ValueError:
                continue
            cam = camera_do_caminho((r.get('imagem') or '').strip())
            for b in caixas:
                if b.get('rotulo') not in ('tampa', 'tampa_alterada', 'tampa_ausente'):
                    continue
                x, y = float(b['x']) / 100, float(b['y']) / 100
                w, h = float(b['width']) / 100, float(b['height']) / 100
                por_camera[cam].append((x, y, x + w, y + h))

    relatorio = {'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                 'margem': a.margem, 'fonte': str(a.csv), 'cameras': {}}
    reprovou = False
    for cam, caixas in sorted(por_camera.items()):
        if not caixas:
            continue
        x1 = max(0.0, min(c[0] for c in caixas) - a.margem)
        y1 = max(0.0, min(c[1] for c in caixas) - a.margem)
        x2 = min(1.0, max(c[2] for c in caixas) + a.margem)
        y2 = min(1.0, max(c[3] for c in caixas) + a.margem)
        dentro = sum(1 for c in caixas if c[0] >= x1 and c[1] >= y1 and c[2] <= x2 and c[3] <= y2)
        cobertura = dentro / len(caixas)
        largura, altura = RESOLUCOES.get(cam, (0, 0))
        entrada = {'caixas': len(caixas), 'cobertura': round(cobertura, 4),
                   'roi_normalizada': {'x': round(x1, 4), 'y': round(y1, 4),
                                       'w': round(x2 - x1, 4), 'h': round(y2 - y1, 4)}}
        if largura:
            entrada['roi_pixel'] = {'x': int(round(x1 * largura)), 'y': int(round(y1 * altura)),
                                    'w': int(round((x2 - x1) * largura)),
                                    'h': int(round((y2 - y1) * altura)),
                                    'resolucao_origem': [largura, altura]}
            # ganho de resolução efetiva se a entrada do modelo for 320
            area_roi = (x2 - x1) * (y2 - y1)
            entrada['ganho_escala_em_320'] = round(1 / max(area_roi, 1e-6) ** 0.5, 2)
            entrada['fracao_da_imagem'] = round(area_roi, 4)
        relatorio['cameras'][cam] = entrada
        saturada = (x2 - x1) >= 0.98 and (y2 - y1) >= 0.98
        status = 'SATURACAO' if saturada else ('OK' if cobertura >= 0.95 else 'REPROVA')
        if cobertura < 0.95:
            reprovou = True
        if saturada:
            entrada['saturada'] = True
            reprovou = reprovou or not a.permitir_saturacao
        print(f'{cam:10s} caixas={len(caixas):4d} cobertura={cobertura:.3f} {status} '
              f'roi={entrada["roi_normalizada"]} ' + (f'px={entrada["roi_pixel"]}' if largura else ''))

    if reprovou:
        print('\nGATE REPROVOU: ROI que nao cobre 95% das caixas, ou retangulo SATURADO '
              '(quadro inteiro). Saturar quase sempre significa caixa de OUTRA vista no mesmo '
              'envelope -- conferir --vista antes de aumentar margem.')
        return 3
    a.saida.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1))
    print('\ngravado:', a.saida)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
