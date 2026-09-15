#!/usr/bin/env python3
"""Camada de decisão operacional: limiar POR CLASSE + regra do silêncio.

Problema que isto resolve (medido hoje): 4 de 9 imagens "sem tampa" não recebiam caixa
nenhuma acima do limiar — o modelo não dizia "normal", ele ficava CALADO, e silêncio não
pode ser tratado como "normal" numa linha de inspeção.

Regra:
  - inferência com conf baixo (0.05) para ver tudo que o modelo oferece
  - a decisão por imagem usa o limiar DA CLASSE (tabela medida), não um limiar global
  - se nada passa -> decisão = REVISAR (nem normal, nem defeito)
Saída: decisão por imagem + contagem + confusão contra a verdade.

Uso: python decisao_operacional.py --peso W --dataset DIR [--split test] [--limiares ...]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from ultralytics import YOLO


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--peso', required=True)
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--split', default='test')
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--conf-baixa', type=float, default=0.05)
    ap.add_argument('--limiares', default='normal=0.30,tampa_ausente=0.15,defeito_tampa=0.30,deformidade=0.60',
                    help='limiar por classe, escolhido em VALIDAÇÃO')
    ap.add_argument('--saida', default=None)
    a = ap.parse_args()

    limiares = {}
    for parte in a.limiares.split(','):
        k, _, v = parte.partition('=')
        limiares[k.strip()] = float(v)

    base = Path(a.dataset)
    imagens = sorted(p for p in (base / 'images' / a.split).iterdir()
                     if p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
    labels = base / 'labels' / a.split
    modelo = YOLO(a.peso)

    verdade, decisao, detalhe = {}, {}, []
    for img in imagens:
        lab = labels / (img.stem + '.txt')
        ids = []
        if lab.is_file():
            ids = [int(l.split()[0]) for l in lab.read_text().splitlines() if l.split()]
        vt = modelo.predict(str(img), imgsz=a.imgsz, conf=a.conf_baixa, verbose=False)[0]
        nomes = vt.names or {}
        cand = []
        if vt.boxes is not None and len(vt.boxes):
            for b, c, k in zip(vt.boxes.xyxy.cpu().numpy(), vt.boxes.conf.cpu().numpy(),
                               vt.boxes.cls.cpu().numpy().astype(int)):
                cand.append((float(c), nomes.get(int(k), str(k))))
        cand.sort(reverse=True)
        # limiar por classe: primeira caixa cuja classe passa o SEU limiar
        escolhida = next((cl for c, cl in cand if c >= limiares.get(cl, 1.0)), None)
        decisao[img.name] = escolhida or 'REVISAR'
        # verdade = classe majoritária das caixas anotadas
        verdade[img.name] = nomes.get(Counter(ids).most_common(1)[0][0], 'sem_caixa') if ids else 'sem_caixa'
        detalhe.append({'imagem': img.name, 'verdade': verdade[img.name], 'decisao': decisao[img.name],
                        'candidatas': [{'classe': cl, 'conf': round(c, 3)} for c, cl in cand[:3]]})

    confusao = defaultdict(Counter)
    for nome, d in decisao.items():
        confusao[verdade[nome]][d] += 1
    acertos = sum(1 for n in decisao if decisao[n] == verdade[n])
    revisar = sum(1 for n in decisao if decisao[n] == 'REVISAR')
    ignorados = sum(1 for n in decisao if verdade[n] == 'REVISAR')

    res = {'peso': a.peso, 'dataset': str(base), 'split': a.split, 'limiares': limiares,
           'conf_baixa': a.conf_baixa, 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'total': len(imagens), 'acertos': acertos, 'revisar': revisar,
           'acuracia_bruta': round(acertos / len(imagens), 4) if imagens else 0,
           'acuracia_sem_revisar': round(acertos / max(1, len(imagens) - revisar), 4),
           'confusao': {k: dict(v) for k, v in confusao.items()}, 'por_imagem': detalhe}
    print(f"total {len(imagens)} | acertos {acertos} ({res['acuracia_bruta']:.3f}) | REVISAR {revisar} "
          f"| acurácia sem os de revisão {res['acuracia_sem_revisar']:.3f}")
    for vt in sorted(confusao):
        print(f"  verdade {vt:16s} -> {dict(confusao[vt])}")
    destino = Path(a.saida) if a.saida else base.parent / f'decisao-operacional-{a.split}.json'
    destino.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print('gravado:', destino)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
