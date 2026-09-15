#!/usr/bin/env python3
"""Mede a acurácia do modelo de TOPO (treinado só com KMITL) nas NOSSAS capturas de topo.

Entrada: anotações humanas do export canônico com vista=topo (as capturas do CSI do
capturas do rig anotadas no projeto 14). Verdade = classe anotada; predição = caixa de maior
confiança do modelo. Mapeamento de classes do modelo: tampa_presente -> normal.

Testa duas formas de entrada, porque o modelo foi treinado em frame inteiro do KMITL
e o nosso pipeline usa recorte de ROI:
  --roi crop  : recorta a ROI da câmera csi (como no deploy)
  --roi cheio : frame inteiro (como o modelo viu no treino)

Uso: python avalia_topo_nossas.py [--roi crop|cheio|ambos] [--conf 0.05] [--saida arq.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

G = Path(__file__).resolve().parents[2]
CSV = G / 'dataset/TRABALHO/anotacoes-ls.csv'
MODELOS = os.environ.get('PNAAT_MODELOS') or str(Path.home() / 'pnaat-modelos')
PESO_PADRAO = Path(MODELOS) / 'v0-top-detector/weights/best.pt'
ROI_JSON = G / 'dataset/TRABALHO/roi-por-camera.json'
RAIZES = (G / 'dataset', Path('/srv/label-studio/corpus'), Path('/srv/label-studio'))
EXCLUI = {'excluir_do_treino', 'imagem_ruim'}
MAPA = {'tampa_presente': 'normal', 'normal': 'normal', 'tampa_ausente': 'tampa_ausente'}


def resolve(rel: str):
    for raiz in RAIZES:
        c = raiz / rel
        if c.is_file():
            return c
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--peso', default=str(PESO_PADRAO))
    ap.add_argument('--roi', choices=['crop', 'cheio', 'ambos'], default='ambos')
    ap.add_argument('--conf', type=float, default=0.05)
    ap.add_argument('--imgsz', type=int, default=320)
    ap.add_argument('--saida', default=str(Path(MODELOS) / 'v0-top-detector/avaliacao-nossas-capturas.json'))
    a = ap.parse_args()

    roi = json.loads(ROI_JSON.read_text())['cameras']['csi']['roi_normalizada'] if ROI_JSON.is_file() else None

    linhas = []
    with CSV.open(newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if (r.get('valido') or '') != 'sim' or (r.get('vista') or '') != 'topo':
                continue
            coher = {c.strip() for c in (r.get('coerencia') or '').split(';') if c.strip()}
            if coher & EXCLUI:
                continue
            caminho = resolve((r.get('imagem') or '').strip())
            if caminho is None:
                continue
            linhas.append({'arquivo': str(caminho), 'classe': r['classe'],
                           'caixas': json.loads(r.get('caixas') or '[]'), 'origem': r['imagem']})
    print(f'nossas capturas de topo com rotulo humano: {len(linhas)}')
    print('  classes:', dict(Counter(l["classe"] for l in linhas)))

    from PIL import Image
    from ultralytics import YOLO
    modelo = YOLO(a.peso)
    print('modelo:', a.peso, '| classes:', modelo.names)

    modos = ['crop', 'cheio'] if a.roi == 'ambos' else [a.roi]
    resultado = {'peso': a.peso, 'conf': a.conf, 'imgsz': a.imgsz,
                 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                 'n_imagens': len(linhas), 'modos': {}}

    for modo in modos:
        confusao = Counter()
        sem_deteccao = 0
        acertos = 0
        duvidosas = []
        for l in linhas:
            with Image.open(l['arquivo']) as im:
                img = im.convert('RGB')
                if modo == 'crop' and roi:
                    L, A = img.size
                    img = img.crop((int(roi['x'] * L), int(roi['y'] * A),
                                    int((roi['x'] + roi['w']) * L), int((roi['y'] + roi['h']) * A)))
                pred = modelo.predict(img, imgsz=a.imgsz, conf=a.conf, verbose=False)[0]
            if pred.boxes is None or len(pred.boxes) == 0:
                sem_deteccao += 1
                confusao[(l['classe'], 'sem_deteccao')] += 1
                if len(duvidosas) < 5:
                    duvidosas.append({'origem': l['origem'], 'real': l['classe'], 'pred': 'sem_deteccao'})
                continue
            confs = pred.boxes.conf.cpu().numpy()
            k = int(confs.argmax())
            nome = modelo.names[int(pred.boxes.cls.cpu().numpy()[k])]
            previsto = MAPA.get(nome, nome)
            confusao[(l['classe'], previsto)] += 1
            if previsto == l['classe']:
                acertos += 1
            elif len(duvidosas) < 5:
                duvidosas.append({'origem': l['origem'], 'real': l['classe'],
                                  'pred': previsto, 'conf': float(confs[k])})
        resultado['modos'][modo] = {
            'acuracia': round(acertos / len(linhas), 4) if linhas else None,
            'acertos': acertos, 'total': len(linhas),
            'sem_deteccao': sem_deteccao,
            'confusao': {f'{r}->{p}': n for (r, p), n in sorted(confusao.items())},
            'exemplos_errados': duvidosas}
        print(f"\n--- entrada: {modo} ---")
        print(f"  acurácia: {resultado['modos'][modo]['acuracia']} "
              f"({acertos}/{len(linhas)}) | sem detecção: {sem_deteccao}")
        print('  confusão:', resultado['modos'][modo]['confusao'])

    Path(a.saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=1))
    print('\ngravado:', a.saida)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
