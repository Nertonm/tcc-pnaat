#!/usr/bin/env python3
"""Monta o dataset v1 com SPLIT POR ITEM (bloqueio que impedia treinar direito).

Problema que isto resolve: frames vizinhos são a MESMA garrafa. Se o split é por
imagem, cópias da mesma peça caem em treino e validação e a métrica vira ficção.
Aqui cada imagem recebe uma CHAVE DE ITEM e a chave inteira vai para um único
split (treino OU validação OU teste).

Chave de item (regra documentada, determinística):
  1. corpus/<...>/<serie>/arquivo.jpg        -> a série inteira (um evento de captura = um item)
  2. arquivo com contador no fim do nome     -> "prefixo" (frames do mesmo vídeo/sequência)
     ex.: frame_0013.jpg, 20260914-172755_trig0710_evt0002.jpg -> o trig/vídeo, não o frame
  3. sem contador                            -> o próprio arquivo (item independente)

Fontes do v1:
  - rótulos humanos do export canônico (dataset/TRABALHO/anotacoes-ls.csv), válidos e
    NÃO marcados como excluir_do_treino/imagem_ruim
  - rótulos de origem das fontes externas com caixa (mesmas do v0: sdp, joren, lte35)

Saída: <OUT>/dataset (images/{train,val,test} + labels/...) + data.yaml +
manifest.json (com o item de cada imagem) + recibo. Recusa gravar se OUT existe.

Uso:
  python monta_v1_detector.py --vista lateral [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from caminhos import RAIZ_REPO, PIPELINE, CONTRATO, PNAAT_MODELOS

G = RAIZ_REPO
DS = G / 'dataset'
MODELOS = str(PNAAT_MODELOS)
CSV_HUMANO = DS / 'TRABALHO' / 'anotacoes-ls.csv'
CLASSES = ['normal', 'tampa_ausente', 'defeito_tampa']
CLASSES_4 = ['normal', 'tampa_ausente', 'defeito_tampa', 'deformidade']
FONTES = {
    'bottle_cap_sdp-3v0vj-qzaan': {'good_cap': 'normal', 'no_cap': 'tampa_ausente',
                                   'misplaced_cap': 'defeito_tampa', 'damaged_cap': 'defeito_tampa',
                                   'open_cap': 'defeito_tampa', 'wet_cap': 'normal'},
    'dataset-joren-newest-a4vuy': {'Good Cap': 'normal', 'No Cap': 'tampa_ausente',
                                   'Loose Cap': 'defeito_tampa', 'Broken Cap': 'defeito_tampa'},
    'bottle-lte35-abhgw': {'Closed': 'normal', 'Missing cap': 'tampa_ausente',
                           'Unclosed': 'defeito_tampa'},
}
CONTADOR = re.compile(r'^(?P<prefixo>.*?)[_-]?(?P<numero>\d{2,4})$')
RAIZES = (DS, Path('/srv/label-studio/corpus'), Path('/srv/label-studio'))
ROI_JSON = CONTRATO / 'roi-por-camera.json'
from roi_por_camera import camera_do_caminho


LS_MEDIA = Path('/srv/label-studio/data/media/upload')


def resolve(rel: str) -> Path | None:
    # caminho de mídia do Label Studio: /data/upload/<id>/<nome> (o arquivo em disco tem uuid antes do nome)
    if rel.startswith('/data/upload/'):
        partes = rel.split('/')
        if len(partes) >= 5:
            pasta = LS_MEDIA / partes[3]
            alvo = partes[-1]
            if pasta.is_dir():
                exato = pasta / alvo
                if exato.is_file():
                    return exato
                for cand in pasta.iterdir():
                    if cand.name.endswith('-' + alvo) or cand.name == alvo:
                        return cand
        return None
    for raiz in RAIZES:
        cand = raiz / rel
        if cand.is_file():
            return cand
    return None
EXCLUI = {'excluir_do_treino', 'imagem_ruim'}
PROPORCAO = {'train': 0.70, 'val': 0.15, 'test': 0.15}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def chave_de_item(rel: str) -> str:
    """Regra de agrupamento documentada no topo do arquivo."""
    p = Path(rel)
    partes = p.parts
    if partes and partes[0] == 'corpus' and len(partes) >= 4:
        # mesmo evento de captura entre câmeras = MESMO item (a pasta difere só pela câmera)
        return 'evento:' + '/'.join(partes[:2] + (partes[-2],))
    if partes and partes[0] in ('dataset', 'nosso', 'externo') and len(partes) >= 3:
        nome = p.stem
        m = CONTADOR.match(nome)
        if m and m.group('numero'):
            base = str(p.parent)
            return f'seq:{base}:{m.group("prefixo")}'
    return 'img:' + rel                                   # 3) item independente


def split_do_item(item: str) -> str:
    """Sorteio determinístico do ITEM (nunca da imagem); reprodutível e auditável."""
    h = int(hashlib.sha256(item.encode()).hexdigest()[:8], 16) % 10_000 / 10_000
    if h < PROPORCAO['train']:
        return 'train'
    if h < PROPORCAO['train'] + PROPORCAO['val']:
        return 'val'
    return 'test'


def nomes_yaml(yaml: Path) -> list[str]:
    t = yaml.read_text(errors='ignore')
    r = t.split('names:', 1)[1].strip()
    if r.startswith('['):
        return [x.strip().strip("'\"") for x in r.strip('[]').split(',')]
    out = []
    for linha in r.splitlines():
        if linha.strip().startswith('-'):
            out.append(linha.strip()[1:].strip().strip("'\""))
        elif ':' in linha:                       # formato '0: nome'
            out.append(linha.split(':', 1)[1].split('#')[0].strip().strip("'\""))
    return out


def caixas_yolo(lab: Path, mapa: dict[int, int]) -> list[tuple[int, float, float, float, float]]:
    out = []
    for linha in lab.read_text(errors='ignore').splitlines():
        p = linha.split()
        if len(p) < 5:
            continue
        try:
            cid = int(float(p[0]))
            vals = [float(x) for x in p[1:]]
        except ValueError:
            continue
        if cid not in mapa:
            continue
        if len(vals) >= 6 and len(vals) % 2 == 0:
            xs, ys = vals[0::2], vals[1::2]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            w, h = max(xs) - min(xs), max(ys) - min(ys)
        elif len(vals) == 4:
            cx, cy, w, h = vals
        else:
            continue
        if w > 1e-6 and h > 1e-6:
            out.append((mapa[cid], cx, cy, w, h))
    return out


def caixas_no_recorte(caixas, tamanho, recorte):
    """Intersecciona esquinas com o MESMO retângulo inteiro usado pelo PIL."""
    import math
    L, A = tamanho
    x1, y1, x2, y2 = recorte
    if x2 <= x1 or y2 <= y1:
        raise ValueError('ROI vazia')
    out = []
    for c, cx, cy, w, h in caixas:
        if not all(math.isfinite(v) for v in (cx, cy, w, h)) or w <= 0 or h <= 0:
            raise ValueError('box fonte invalida')
        left, right = max(x1, (cx-w/2)*L), min(x2, (cx+w/2)*L)
        top, bottom = max(y1, (cy-h/2)*A), min(y2, (cy+h/2)*A)
        if right <= left or bottom <= top:
            continue
        out.append((c, ((left+right)/2-x1)/(x2-x1), ((top+bottom)/2-y1)/(y2-y1),
                    (right-left)/(x2-x1), (bottom-top)/(y2-y1)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--vista', default='lateral', choices=['lateral', 'topo'])
    ap.add_argument('--dry-run', action='store_true',
                    help='confere os gates e NAO escreve nada')
    ap.add_argument('--out', default=None)
    ap.add_argument('--com-corpo', action='store_true',
                    help='inclui corpo_deformidade como 4a classe (limiar baixo, poucos exemplos)')
    ap.add_argument('--sem-phash', action='store_true',
                    help='desliga o agrupamento por quase-duplicata')
    ap.add_argument('--somente-dominio', action='store_true',
                    help='usa APENAS imagens do nosso dominio (corpus/ e nosso/)')
    ap.add_argument('--permitir-classe-ausente', action='store_true',
                    help='rebaixa o gate de presenca de classe a aviso (vistas com menos classes)')
    ap.add_argument('--ignorar-frescor', action='store_true',
                    help='monta mesmo se o LS avancou desde o export (nao recomendado)')
    ap.add_argument('--roi', action='store_true',
                    help='recorta a ROI da câmera (treino igual à inferência)')
    a = ap.parse_args()

    if not a.ignorar_frescor:
        import subprocess as _sp
        _guarda = _sp.run([sys.executable, str(PIPELINE / 'guarda_frescor.py')],
                          capture_output=True, text=True)
        print(_guarda.stdout.strip())
        if _guarda.returncode != 0:
            print('ABORTADO pela trava de frescor: o Label Studio avancou desde o export '
                  '(rode src-production/treino/exporta_anotacoes.py e tente de novo)')
            return 4
    OUT = Path(a.out or (f'{MODELOS}/v1-{a.vista}-detector'
                         + ('-roi' if a.roi else '') + '/dataset'))
    roi = {}
    if a.roi:
        import json as _json
        dados = _json.loads(ROI_JSON.read_text())
        roi = {c: v['roi_normalizada'] for c, v in dados['cameras'].items() if v.get('roi_normalizada')}
        print('ROI carregada para:', ', '.join(sorted(roi)))
    classes = CLASSES_4 if a.com_corpo else CLASSES
    # espelho do índice de classe usado nos labels
    MAPA_CAIXA = {'tampa': 0, 'tampa_ausente': 1, 'tampa_alterada': 2, 'corpo_deformidade': 3}
    itens: list[dict] = []          # {rel, classe, caixas, item, fonte}

    # ---- rótulos humanos do export canônico
    n_humano = 0
    if CSV_HUMANO.is_file():
        for r in csv.DictReader(CSV_HUMANO.open(newline='', encoding='utf-8')):
            if (r.get('valido') or '') != 'sim':
                continue
            if (r.get('vista') or '') != a.vista:
                continue
            coher = {c.strip() for c in (r.get('coerencia') or '').split(';') if c.strip()}
            if coher & EXCLUI:
                continue
            classe = (r.get('classe') or '').strip()
            # 'deformidade' e aceita nas DUAS montagens: com --com-corpo a caixa de corpo entra;
            # sem, a imagem ainda contribui com as caixas de tampa (antes era descartada em silencio)
            if classe not in (set(classes) | {'deformidade'}):
                continue
            rel = (r.get('imagem') or '').strip()
            if not rel or resolve(rel) is None:
                continue
            try:
                caixas = json.loads(r.get('caixas') or '[]')
            except ValueError:
                continue
            boxes = []
            aceitos = ('tampa', 'tampa_alterada', 'tampa_ausente') + \
                      (('corpo_deformidade',) if a.com_corpo else ())
            for b in caixas:
                rot = b.get('rotulo', '')
                if rot not in aceitos:
                    continue
                idx = MAPA_CAIXA[rot]
                boxes.append((idx, float(b['x']) / 100 + float(b['width']) / 200,
                              float(b['y']) / 100 + float(b['height']) / 200,
                              float(b['width']) / 100, float(b['height']) / 100))
            if not boxes:
                continue
            itens.append({'rel': rel, 'caixas': boxes, 'classe': classe,
                          'item': chave_de_item(rel), 'fonte': 'humano'})
            n_humano += 1

    # ---- rótulos de origem das fontes externas
    n_fonte = 0
    for proj, mapa in FONTES.items():
        base = DS / 'externo' / proj
        if not base.is_dir():
            continue
        names = nomes_yaml(base / 'data.yaml')
        mapidx = {i: CLASSES.index(dst) for i, n in enumerate(names) if (dst := mapa.get(n))}
        for split in ('train', 'valid', 'test'):
            di, dl = base / split / 'images', base / split / 'labels'
            if not di.is_dir():
                continue
            for img in sorted(di.iterdir()):
                if img.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
                    continue
                lab = dl / (img.stem + '.txt')
                if not lab.is_file():
                    continue
                boxes = caixas_yolo(lab, mapidx)
                if not boxes:
                    continue
                rel = str(img.relative_to(DS))
                classe = CLASSES[Counter(b[0] for b in boxes).most_common(1)[0][0]]
                itens.append({'rel': rel, 'caixas': boxes, 'classe': classe,
                              'item': chave_de_item(rel), 'fonte': proj})
                n_fonte += 1

    ids = {i['rel'] for i in itens}
    itens = [i for i in itens if i['rel'] in ids]
    print(f'itens coletados: {len(itens)} (humano={n_humano} fonte={n_fonte})')

    # dedup por imagem (mesmo arquivo em duas fontes: fica o humano)
    por_rel: dict[str, dict] = {}
    for i in itens:
        atual = por_rel.get(i['rel'])
        if atual is None or (atual['fonte'] != 'humano' and i['fonte'] == 'humano'):
            por_rel[i['rel']] = i
    itens = list(por_rel.values())
    print('imagens distintas:', len(itens))

    # ---- quase-duplicata: mesma garrafa/frame em séries diferentes tem de cair no MESMO split
    if not a.sem_phash:
        def _dhash(caminho, tam=8):
            try:
                from PIL import Image
                with Image.open(caminho) as im:
                    g = im.convert('L').resize((tam + 1, tam))
                    px = list(g.getdata())
            except Exception:
                return None
            bits = 0
            for lin in range(tam):
                for col in range(tam):
                    bits = (bits << 1) | (1 if px[lin * (tam + 1) + col] > px[lin * (tam + 1) + col + 1] else 0)
            return f'{bits:0{tam * tam // 4}x}'

        pai = {}

        def _find(x):
            pai.setdefault(x, x)
            while pai[x] != x:
                pai[x] = pai[pai[x]]
                x = pai[x]
            return x

        def _une(a, b):
            ra, rb = _find(a), _find(b)
            if ra != rb:
                pai[rb] = ra

        por_hash = defaultdict(list)
        for i in itens:
            caminho = resolve(i['rel'])
            h = _dhash(caminho) if caminho else None
            if h:
                por_hash[h].append(i['item'])
        juntos = 0
        for h, lista in por_hash.items():
            for outro in lista[1:]:
                if _find(lista[0]) != _find(outro):
                    juntos += 1
                _une(lista[0], outro)
        if juntos:
            print(f'quase-duplicata: {juntos} itens agrupados por hash perceptual (mesmo destino de split)')
        for i in itens:
            i['item'] = _find(i['item'])

    if a.somente_dominio:
        antes = len(itens)
        itens = [i for i in itens if i['rel'].startswith(('corpus', 'nosso', '/data/upload/'))]
        print(f'somente dominio proprio: {len(itens)} de {antes} imagens')

    # ---- split por ITEM
    itens_por_chave = defaultdict(list)
    for i in itens:
        itens_por_chave[i['item']].append(i)
    for chave, grupo in itens_por_chave.items():
        destino = split_do_item(chave)
        for i in grupo:
            i['split'] = destino
    print(f'itens (garrafas/séries): {len(itens_por_chave)}')

    # ---- gates ANTES de escrever
    falhas = []
    for chave, grupo in itens_por_chave.items():
        splits = {i['split'] for i in grupo}
        if len(splits) > 1:
            falhas.append(f'item {chave} em vários splits: {splits}')
    resumo = Counter((i['split'], i['classe']) for i in itens)
    resumo_img = Counter(i['split'] for i in itens)
    resumo_item = Counter(next(iter({i['split'] for i in g})) for g in itens_por_chave.values())
    print('imagens por split:', dict(resumo_img))
    print('itens por split  :', dict(resumo_item))
    for split in ('train', 'val', 'test'):
        print(f'  {split}: ' + ' · '.join(f'{c}={resumo[(split, c)]}' for c in CLASSES))
    for classe in CLASSES:
        if resumo[('val', classe)] == 0 or resumo[('test', classe)] == 0:
            falhas.append(f'classe {classe} ausente em val ou test (val={resumo[("val", classe)]}, '
                          f'test={resumo[("test", classe)]})')
    if falhas:
        print('\nGATES REPROVARAM:')
        for f in falhas:
            print('  -', f)
        if not a.dry_run:
            if a.permitir_classe_ausente:
                print('  (--permitir-classe-ausente: seguindo com aviso)')
            else:
                return 3
    if a.dry_run:
        print('\n(dry-run: nada foi escrito)')
        return 0
    if OUT.exists():
        print('ABORT: saída já existe:', OUT)
        return 2

    # Reserva exclusiva: uma segunda montagem nunca escreve neste dataset.
    OUT = OUT.resolve()
    OUT.mkdir(parents=True, exist_ok=False)
    # ---- grava
    for sub in ('images/train', 'images/val', 'images/test', 'labels/train', 'labels/val', 'labels/test'):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    manifesto = []
    for i in itens:
        src = resolve(i['rel'])
        if src is None:
            continue
        # sufixo com hash da origem: sem isso o mesmo nome de arquivo em splits
        # diferentes da mesma fonte sobrescreve (perda silenciosa de imagem)
        sufixo = hashlib.sha1(i['rel'].encode()).hexdigest()[:8]
        nome = (('humano__' if i['fonte'] == 'humano' else f'{i["fonte"][:12]}__')
                + sufixo + '__' + src.name)
        destino = OUT / 'images' / i['split'] / nome
        caixa = roi.get(camera_do_caminho(i['rel'])) if roi else None
        from PIL import Image
        with Image.open(src) as im:
            L, A = im.size
            recorte = (0, 0, L, A)
            if caixa:
                x, y = max(0, int(caixa['x'] * L)), max(0, int(caixa['y'] * A))
                recorte = (x, y, min(L, int((caixa['x'] + caixa['w']) * L)),
                           min(A, int((caixa['y'] + caixa['h']) * A)))
            caixas_saida = caixas_no_recorte(i['caixas'], (L, A), recorte)
            if caixa:
                im.crop(recorte).convert('RGB').save(destino, format='JPEG', quality=95, subsampling=0)
            else:
                shutil.copy2(src, destino)
        (OUT / 'labels' / i['split'] / (Path(nome).stem + '.txt')).write_text(
            ''.join(f'{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n' for c, cx, cy, w, h in caixas_saida))
        manifesto.append({'arquivo': nome, 'item': i['item'], 'split': i['split'],
                          'classe': i['classe'], 'fonte': i['fonte'], 'origem': i['rel'],
                          'sha256': sha256(src), 'sha256_fonte': sha256(src),
                          'sha256_derivado': sha256(destino), 'recorte_pixels': recorte})
    (OUT / 'data.yaml').write_text(
        f'path: {OUT}\ntrain: images/train\nval: images/val\ntest: images/test\n'
        f'nc: {len(classes)}\nnames: {classes}\n')
    (OUT / 'manifest.json').write_text(json.dumps({
        'vista': a.vista, 'classes': classes,
        'preprocessamento': {'roi': bool(a.roi), 'roi_sha256': sha256(ROI_JSON) if a.roi else None}, 'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'proporcao': PROPORCAO, 'imagens_por_split': dict(resumo_img), 'itens_por_split': dict(resumo_item),
        'por_split_classe': {f'{s}/{c}': n for (s, c), n in sorted(resumo.items())},
        'itens': manifesto}, ensure_ascii=False, indent=1))
    from validacao_dataset import validar_dataset
    validar_dataset(OUT / 'data.yaml')
    print('saída:', OUT)
    print('manifest sha256:', sha256(OUT / 'manifest.json')[:16])
    return 0


if __name__ == '__main__':
    sys.exit(main())
