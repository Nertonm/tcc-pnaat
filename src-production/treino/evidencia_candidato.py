#!/usr/bin/env python3
"""Evidência do candidato: predições + decisão por imagem + mosaico visual.

Para a entrega, métrica agregada não basta: a banca quer ver comportamento. Este script
roda o modelo no split de teste, toma a decisão por imagem (caixa de maior confiança),
compara com a classe anotada e grava:
  - JSON com predição por imagem (classe, confiança, caixa) e a matriz de confusão
  - PNG com o mosaico: imagem + caixas preditas + rótulo verdadeiro x predito
  - tabela de acurácia por limiar de confiança (a decisão muda conforme o limiar)

Uso: python evidencia_candidato.py --peso W --dataset DIR --split test [--confs 0.15,0.30]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw
from ultralytics import YOLO


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--peso', required=True)
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--split', default='test')
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--confs', default='0.15,0.30')
    ap.add_argument('--saida', default=None)
    ap.add_argument('--max-lado', type=int, default=6)
    a = ap.parse_args()

    base = Path(a.dataset)
    nomes = []
    for linha in (base / 'data.yaml').read_text().splitlines():
        if linha.startswith('names:'):
            nomes = [x.strip().strip("'\"") for x in linha.split(':', 1)[1].strip().strip('[]').split(',')]

    imagens = sorted(p for p in (base / 'images' / a.split).iterdir()
                     if p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
    labels = base / 'labels' / a.split
    modelo = YOLO(a.peso)
    confs = [float(c) for c in a.confs.split(',')]

    # classe verdadeira por imagem = classe da 1a caixa (o montador grava uma classe por item)
    verdade = {}
    for img in imagens:
        lab = labels / (img.stem + '.txt')
        if lab.is_file():
            ids = [int(l.split()[0]) for l in lab.read_text().splitlines() if l.split()]
            verdade[img.name] = nomes[Counter(ids).most_common(1)[0][0]] if ids else 'sem_caixa'
        else:
            verdade[img.name] = 'sem_caixa'

    resultado = {'peso': a.peso, 'dataset': str(base), 'split': a.split,
                 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                 'imagens': len(imagens), 'por_limiar': {}, 'predicoes': []}

    for conf in confs:
        acertos, confusao = 0, defaultdict(Counter)
        for img in imagens:
            p = modelo.predict(str(img), imgsz=a.imgsz, conf=conf, verbose=False)[0]
            caixas = []
            if p.boxes is not None and len(p.boxes):
                xy = p.boxes.xyxy.cpu().numpy()
                cl = p.boxes.cls.cpu().numpy().astype(int)
                cf = p.boxes.conf.cpu().numpy()
                ordem = cf.argsort()[::-1]
                for i in ordem:
                    caixas.append({'classe': nomes[int(cl[i])], 'conf': round(float(cf[i]), 3),
                                   'box': [round(float(v), 1) for v in xy[i]]})
            predito = caixas[0]['classe'] if caixas else 'sem_deteccao'
            vt = verdade[img.name]
            confusao[vt][predito] += 1
            if predito == vt:
                acertos += 1
            if conf == confs[0]:
                resultado['predicoes'].append({'imagem': img.name, 'verdade': vt,
                                               'predito': predito, 'caixas': caixas})
        resultado['por_limiar'][str(conf)] = {
            'acuracia': round(acertos / len(imagens), 4) if imagens else 0,
            'acertos': acertos, 'total': len(imagens),
            'confusao': {k: dict(v) for k, v in confusao.items()},
            'sem_deteccao': sum(1 for i in resultado['predicoes']
                                if i['predito'] == 'sem_deteccao') if conf == confs[0] else None}
        print(f'--- limiar {conf}: acurácia {acertos}/{len(imagens)} = {acertos/max(1,len(imagens)):.3f}')
        for vt in sorted(confusao):
            print(f'    verdade {vt:16s} -> {dict(confusao[vt])}')

    # mosaico visual
    destino = Path(a.saida) if a.saida else base.parent
    destino.mkdir(parents=True, exist_ok=True)
    cols = min(a.max_lado, max(1, len(imagens)))
    linhas = (len(imagens) + cols - 1) // cols
    lado = 320
    mosaico = Image.new('RGB', (cols * lado, linhas * (lado + 22)), (18, 18, 20))
    dr = ImageDraw.Draw(mosaico)
    pred_por_nome = {x['imagem']: x for x in resultado['predicoes']}
    for k, img in enumerate(imagens):
        cx, cy = (k % cols) * lado, (k // cols) * (lado + 22)
        with Image.open(img) as im:
            im = im.convert('RGB')
            im.thumbnail((lado, lado))
            mosaico.paste(im, (cx + (lado - im.width) // 2, cy))
        pr = pred_por_nome.get(img.name, {})
        vt, pd = pr.get('verdade', '?'), pr.get('predito', '?')
        cor = (90, 220, 120) if vt == pd else (240, 90, 90)
        dr.rectangle([cx, cy + lado, cx + lado - 1, cy + lado + 21], fill=(28, 28, 32))
        dr.text((cx + 4, cy + lado + 5), f'{vt} -> {pd}'[:34], fill=cor)
        for c in pr.get('caixas', [])[:3]:
            x1, y1, x2, y2 = c['box']
            # a caixa está nas coordenadas da imagem original; reescala para o thumb
            with Image.open(img) as im0:
                L0, A0 = im0.size
            esc = min(lado / L0, lado / A0)
            ox = cx + (lado - int(L0 * esc)) // 2
            oy = cy + (lado - int(A0 * esc)) // 2
            dr.rectangle([ox + x1 * esc, oy + y1 * esc, ox + x2 * esc, oy + y2 * esc],
                         outline=cor, width=2)
    png = destino / f'evidencia-{Path(a.peso).parent.parent.name}-{a.split}.png'
    mosaico.save(png)

    js = destino / f'evidencia-{Path(a.peso).parent.parent.name}-{a.split}.json'
    js.write_text(json.dumps(resultado, ensure_ascii=False, indent=1))
    print('\nmosaico:', png)
    print('json   :', js)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
