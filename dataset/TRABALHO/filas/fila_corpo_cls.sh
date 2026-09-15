#!/usr/bin/env bash
# Modelo de CORPO, formulação certa: CLASSIFICADOR na região do corpo (o rig é fixo; localizar é
# desnecessário e foi o que fez o detector colapsar com 40 positivos contra 186 negativos).
#
# Recorta a caixa `corpo_regiao` anotada (+ margem) -> deformado x normal -> yolov8n-cls.
# Split por item. Espera a cadeia anterior terminar (não disputa a GPU).
set -uo pipefail
REPO="$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)"
M="$(dirname "$(dirname "$REPO")")/pnaat-modelos"
G="$REPO/dataset/TRABALHO/filas/guardiao_treino.sh"
LOG=$M/fila-corpo-cls.log
export GUARDIAO_LOG=$M/guardiao.log
cd "$REPO" || exit 1
passo() { echo "=== $* $(date -Is)" | tee -a "$LOG"; }
echo "inicio $(date -Is) — corpo como classificação" > "$LOG"
trap 'rc=$?; echo "[trap] encerrou rc=$rc em $(date -Is) (linha $LINENO)" >> "$LOG"' EXIT

passo "espera a cadeia corpo+v9 terminar"
for i in $(seq 1 120); do
  grep -q "^fim " $M/fila-corpo-v9.log 2>/dev/null && break
  sleep 30
done

passo "1/4 monta o conjunto de recortes do corpo (deformado x normal)"
./.venv/bin/python - "$M" "$REPO" >> "$LOG" 2>&1 <<'PY'
import csv, hashlib, json, shutil, sys
from collections import Counter
from pathlib import Path
from PIL import Image
M, G = Path(sys.argv[1]), Path(sys.argv[2])
DS = G / 'dataset'
RAIZES = (DS, G, Path('/srv/label-studio/corpus'), Path('/srv/label-studio'))
roi = {c: v['roi_normalizada'] for c, v in json.loads((DS / 'TRABALHO/roi-por-camera.json').read_text())['cameras'].items() if v.get('roi_normalizada')}
OUT = M / 'corpo-cls/dataset'
if OUT.exists():
    shutil.rmtree(OUT)
def resolve(rel):
    for r in RAIZES:
        c = r / rel
        if c.is_file():
            return c
    return None
itens = {}
with open(DS / 'TRABALHO/anotacoes-ls.csv', newline='', encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        if r['valido'] != 'sim' or r['vista'] != 'lateral':
            continue
        caixas = json.loads(r['caixas'] or '[]')
        reg = next((b for b in caixas if b.get('rotulo') == 'corpo_regiao'), None)
        if not reg:
            continue
        tem_def = any(b.get('rotulo') == 'corpo_deformidade' for b in caixas)
        itens[r['imagem']] = {'reg': reg, 'def': tem_def}
contagem = Counter()
for rel, d in sorted(itens.items()):
    src = resolve(rel)
    if src is None:
        continue
    cam = next((c for c in ('csi', 'usb', 'espcam') if c in rel), 'rig')
    rr = roi.get(cam) or {'x': 0.0, 'y': 0.0, 'w': 1.0, 'h': 1.0}
    item = f'img:{rel}'
    h = int(hashlib.sha256(f'7:{item}'.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    sp = 'train' if h < 0.70 else ('val' if h < 0.85 else 'test')
    cls = 'deformado' if d['def'] else 'normal'
    with Image.open(src) as im:
        L, A = im.size
        x0 = int(rr['x'] * L); y0 = int(rr['y'] * A)
        w = int(rr['w'] * L); hh = int(rr['h'] * A)
        crop = im.crop((x0, y0, x0 + w, y0 + hh))
        bx = float(d['reg']['x']) / 100 * w
        by = float(d['reg']['y']) / 100 * hh
        bw = float(d['reg']['width']) / 100 * w
        bh = float(d['reg']['height']) / 100 * hh
        mg = 0.15
        rec = crop.crop((max(0, int(bx - bw * mg)), max(0, int(by - bh * mg)),
                         min(w, int(bx + bw * (1 + mg))), min(hh, int(by + bh * (1 + mg)))))
        destino = OUT / sp / cls
        destino.mkdir(parents=True, exist_ok=True)
        rec.save(destino / f"{hashlib.sha1(rel.encode()).hexdigest()[:8]}__{src.name}", quality=95)
        contagem[f'{sp}/{cls}'] += 1
print('  recortes por split/classe:', dict(contagem), '| total', sum(contagem.values()))
PY

passo "2/4 treino do classificador de corpo (yolov8n-cls, 120 épocas, 224px)"
bash "$G" ./.venv/bin/python - "$M" >> "$LOG" 2>&1 <<'PY'
import sys
from pathlib import Path
from ultralytics import YOLO
M = Path(sys.argv[1])
m = YOLO('yolov8n-cls.pt')
r = m.train(data=str(M / 'corpo-cls/dataset'), epochs=120, imgsz=224, batch=16, workers=2,
            project=str(M / 'corpo-cls/runs'), name='corpo-cls', exist_ok=True, seed=7)
print('treino concluído:', r.save_dir if hasattr(r, 'save_dir') else '')
PY

passo "3/4 avaliação: acurácia por split (o que ele viu x não viu)"
bash "$G" ./.venv/bin/python - "$M" >> "$LOG" 2>&1 <<'PY'
import sys
from pathlib import Path
from ultralytics import YOLO
M = Path(sys.argv[1])
peso = M / 'corpo-cls/runs/corpo-cls/weights/best.pt'
m = YOLO(str(peso))
for sp in ('train', 'test'):
    d = M / 'corpo-cls/dataset' / sp
    if not d.is_dir():
        continue
    r = m.val(data=str(M / 'corpo-cls/dataset'), split=sp, imgsz=224, verbose=False)
    top1 = getattr(r, 'top1', None)
    print(f'  corpo-cls {sp}: top1 {top1:.3f}' if top1 is not None else f'  corpo-cls {sp}: {r}')
PY

passo "4/4 pacote do classificador de corpo"
./.venv/bin/python - "$M" >> "$LOG" 2>&1 <<'PY'
import hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
M = Path(sys.argv[1])
orig = M / 'corpo-cls/runs/corpo-cls/weights/best.pt'
dest = M / 'ENTREGA/corpo-cls'
dest.mkdir(parents=True, exist_ok=True)
peso = dest / 'corpo-cls.pt'
shutil.copy2(orig, peso)
meta = {'candidato': 'corpo-cls', 'tipo': 'classificador (não detector)',
        'criado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'sha256': hashlib.sha256(peso.read_bytes()).hexdigest(),
        'classes': ['deformado', 'normal'],
        'entrada': 'recorte da caixa corpo_regiao + 15% de margem (rig fixo: a região é sempre a mesma)',
        'por_que_classificador': 'o detector colapsou (40 positivos x 186 negativos = prever nada era o ótimo fácil); '
                                 'com a região fixa, classificar é o problema certo',
        'escopo': 'SÓ corpo. Modelo separado do detector de tampa.',
        'ressalva': 'PoC com 40 imagens deformadas: tende a memorizar o que viu; medir generalização exige mais dado'}
(dest / 'modelo.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
with (dest / 'SHA256SUMS').open('w') as f:
    for p in sorted(dest.iterdir()):
        if p.name != 'SHA256SUMS':
            f.write(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n')
print('pacote corpo-cls:', meta['sha256'][:16])
PY
echo "fim $(date -Is)" >> "$LOG"
