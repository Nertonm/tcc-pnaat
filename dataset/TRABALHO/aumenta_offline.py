#!/usr/bin/env python3
"""Aumento OFFLINE do split de treino — o equivalente local do "dataset version" do Roboflow.

Por que offline (e não só on-the-fly): o Roboflow documenta três razões que valem aqui —
reprodutibilidade (fica o registro de como cada imagem foi aumentada), tempo e custo de
GPU (a augmentação é CPU; on-the-fly faz a GPU esperar). Nosso caso tem um motivo extra:
o conjunto próprio é PEQUENO (67-105 imagens de treino). Multiplicar offline permite
compartilhar as mesmas cópias entre experimentos e medir o efeito isolado.

Regras que seguem o que já está provado no projeto:
  - só o split de TREINO é aumentado (val/teste continuam imagem real)
  - o split já é por ITEM antes de aumentar (senão vaza a mesma garrafa entre splits)
  - dedup por sha256 depois de gerar (o Roboflow também filtra duplicatas criadas)
  - cada cópia registra no manifest: imagem de origem, operações, seed -> auditável

Operações (escolhidas para o nosso rig, não o catálogo inteiro):
  fotométricas (não mexem na caixa): brilho ±20%, exposição ±15%, ruído leve,
  motion blur leve, re-encode JPEG 85-95
  geométricas (recalculam a caixa): flip horizontal (p=0.5), rotação ±5°
  NÃO usamos: hue forte (a cor da tampa é sinal), shear/perspectiva (câmera fixa),
  90° (rig fixo), rotação grande (a garrafa é vertical)

Uso: python aumenta_offline.py --dataset DIR --fator 3 [--ensaio]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

CLASSES = ['normal', 'tampa_ausente', 'defeito_tampa']


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def le_label(p: Path) -> list[tuple[int, float, float, float, float]]:
    out = []
    for linha in p.read_text().splitlines():
        c = linha.split()
        if len(c) == 5:
            out.append((int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4])))
    return out


def escreve_label(p: Path, caixas) -> None:
    p.write_text(''.join(f'{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n' for c, x, y, w, h in caixas))


def gira_caixa(cx, cy, w, h, graus, flip=False):
    """Rotaciona a caixa em torno do centro da imagem e devolve a bbox envolvente."""
    a = math.radians(graus)
    cos, sin = math.cos(a), math.sin(a)
    pts = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        x, y = cx + dx, cy + dy
        x -= 0.5
        y -= 0.5
        xr, yr = x * cos - y * sin, x * sin + y * cos
        xr += 0.5
        yr += 0.5
        if flip:
            xr = 1 - xr
        pts.append((xr, yr))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x1, x2 = max(0.0, min(xs)), min(1.0, max(xs))
    y1, y2 = max(0.0, min(ys)), min(1.0, max(ys))
    return ((x1 + x2) / 2, (y1 + y2) / 2, max(1e-6, x2 - x1), max(1e-6, y2 - y1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--fator', type=int, default=3, help='total de cópias por imagem (1 = nenhuma)')
    ap.add_argument('--semente', type=int, default=7)
    ap.add_argument('--ensaio', action='store_true')
    a = ap.parse_args()

    base = Path(a.dataset)
    man_path = base / 'manifest.json'
    man = json.loads(man_path.read_text())
    treino = [i for i in man['itens'] if i['split'] == 'train']
    print(f'dataset: {base}')
    print(f'imagens de treino: {len(treino)} | fator {a.fator} -> até '
          f'{len(treino) * (a.fator - 1)} cópias novas')

    hashes = {i['sha256'] for i in man['itens'] if i.get('sha256')}
    novas, duplicadas, ops_usadas = [], 0, Counter()

    for i in treino:
        origem_img = base / 'images' / 'train' / i['arquivo']
        origem_lab = base / 'labels' / 'train' / (Path(i['arquivo']).stem + '.txt')
        if not origem_img.is_file() or not origem_lab.is_file():
            continue
        caixas0 = le_label(origem_lab)
        for k in range(1, a.fator):
            rnd = random.Random(f'{a.semente}:{i["arquivo"]}:{k}')
            ops = []
            with Image.open(origem_img) as im:
                img = im.convert('RGB')
                # --- fotométricas
                if rnd.random() < 0.7:
                    f = 1 + rnd.uniform(-0.20, 0.20)
                    img = ImageEnhance.Brightness(img).enhance(f)
                    ops.append(f'brilho={f:.2f}')
                if rnd.random() < 0.5:
                    f = 1 + rnd.uniform(-0.15, 0.15)
                    img = ImageEnhance.Contrast(img).enhance(f)
                    ops.append(f'contraste={f:.2f}')
                if rnd.random() < 0.3:
                    img = img.filter(ImageFilter.GaussianBlur(radius=rnd.uniform(0.4, 1.0)))
                    ops.append('blur_leve')
                if rnd.random() < 0.3:
                    ruido = Image.effect_noise(img.size, rnd.uniform(4, 10)).convert('L')
                    img = Image.blend(img, Image.merge('RGB', (ruido, ruido, ruido)), 0.06)
                    ops.append('ruido')
                # --- geométricas (recalculam a caixa)
                flip = rnd.random() < 0.5
                graus = rnd.uniform(-5, 5) if rnd.random() < 0.6 else 0.0
                caixas = caixas0
                if flip or graus:
                    caixas = [(c, *gira_caixa(cx, cy, w, h, graus, flip)) for c, cx, cy, w, h in caixas0]
                    if flip:
                        img = img.transpose(Image.FLIP_LEFT_RIGHT)
                        ops.append('flip_h')
                    if graus:
                        img = img.rotate(graus, resample=Image.BILINEAR, expand=False,
                                         fillcolor=(0, 0, 0))
                        ops.append(f'rot={graus:.1f}')
            nome = f'aug{k}_{i["arquivo"]}'
            destino_img = base / 'images' / 'train' / nome
            destino_lab = base / 'labels' / 'train' / (Path(nome).stem + '.txt')
            if a.ensaio:
                ops_usadas.update(ops)
                continue
            qualidade = rnd.randint(85, 95)
            img.save(destino_img, format='JPEG', quality=qualidade, subsampling=0)
            escreve_label(destino_lab, caixas)
            h = sha(destino_img)
            if h in hashes:                      # dedup como o Roboflow faz
                destino_img.unlink()
                destino_lab.unlink()
                duplicadas += 1
                continue
            hashes.add(h)
            novas.append({'arquivo': nome, 'item': i['item'], 'split': 'train',
                          'classe': i['classe'], 'fonte': i['fonte'],
                          'origem': i['origem'], 'sha256': h,
                          'aumento': {'de': i['arquivo'], 'ops': ops,
                                      'seed': f'{a.semente}:{i["arquivo"]}:{k}',
                                      'jpeg': qualidade}})
            ops_usadas.update(ops)

    print(f'cópias criadas: {len(novas)} | descartadas por duplicata: {duplicadas}')
    print('operações aplicadas:', dict(ops_usadas))
    if a.ensaio:
        print('(ensaio: nada foi escrito)')
        return 0

    man['itens'].extend(novas)
    man['aumento_offline'] = {'fator': a.fator, 'semente': a.semente,
                              'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                              'criadas': len(novas), 'duplicatas_descartadas': duplicadas,
                              'ops': dict(ops_usadas)}
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1))
    print('manifest atualizado com proveniência de cada cópia')
    print('total de itens agora:', len(man['itens']),
          '| treino:', sum(1 for i in man['itens'] if i['split'] == 'train'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
