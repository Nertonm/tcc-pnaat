#!/bin/bash
# Corpo (pedido do usuário) + reconstrução da tampa com RÓTULOS CORRIGIDOS (v9).
# Serializado; cada treino atrás do guardião. Ordem: corpo primeiro (é o pedido).
set -uo pipefail
REPO="$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)"
M="$(dirname "$(dirname "$REPO")")/pnaat-modelos"
G="$REPO/dataset/TRABALHO/filas/guardiao_treino.sh"
BASE=$M/ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt
LOG=$M/fila-corpo-v9.log
export GUARDIAO_LOG=$M/guardiao.log
cd "$REPO" || exit 1
passo() { echo "=== $* $(date -Is)" | tee -a "$LOG"; }
morre() { echo "ABORTADO: $1" | tee -a "$LOG"; exit 1; }
echo "inicio $(date -Is) — corpo + v9 (rótulos corrigidos)" > "$LOG"
trap 'rc=$?; echo "[trap] encerrou rc=$rc em $(date -Is) (linha $LINENO)" >> "$LOG"' EXIT

passo "1/7 montagem do dataset de CORPO (1 classe + negativos)"
rm -rf "$M/corpo-detector-roi/dataset"
./.venv/bin/python dataset/TRABALHO/monta_corpo_detector.py >> "$LOG" 2>&1 || morre "build corpo"
CORPO=$M/corpo-detector-roi/dataset

passo "2/7 treino do detector de CORPO (yolov8n COCO, 200 ep, 480)"
bash "$G" ./.venv/bin/python dataset/TRABALHO/treina_v1.py --vista lateral --tag corpo --roi --epochs 200 \
  --imgsz 480 --data "$CORPO/data.yaml" --modelo yolov8n.pt --nome corpo-simples >> "$LOG" 2>&1
WC=$M/corpo-lateral-detector-roi/runs/corpo-simples/weights/best.pt
[ -s "$WC" ] || morre "peso do corpo ausente"

passo "3/7 avaliação do CORPO: treino x teste (1 classe)"
for sp in train test; do
  ./.venv/bin/python dataset/TRABALHO/avalia_limiares.py --dataset "$CORPO" --peso "$WC" --split "$sp" \
    --confs 0.15,0.30 --imgsz 480 --saida "$M/corpo-detector-roi/limiares-$sp.json" >> "$LOG" 2>&1
done
./.venv/bin/python - "$M" >> "$LOG" 2>&1 <<'PY'
import json, sys
from pathlib import Path
M = Path(sys.argv[1])
for nome, arq in (('TREINO (viu)', 'corpo-detector-roi/limiares-train.json'),
                  ('TESTE (não viu)', 'corpo-detector-roi/limiares-test.json')):
    p = M / arq
    if not p.is_file():
        print(f'  corpo {nome}: ausente'); continue
    d = json.loads(p.read_text())
    for conf, bloco in d['limiares'].items():
        c = bloco['por_classe'].get('corpo_deformidade', {})
        print(f"  corpo {nome} conf {conf}: F1 {c.get('f1')} (P {c.get('precisao')} R {c.get('recall')} "
              f"tp {c.get('tp')} fp {c.get('fp')} fn {c.get('fn')})")
PY

passo "4/7 pacote do detector de CORPO"
./.venv/bin/python - "$M" >> "$LOG" 2>&1 <<'PY'
import hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
M = Path(sys.argv[1])
orig = M / 'corpo-lateral-detector-roi/runs/corpo-simples/weights/best.pt'
dest = M / 'ENTREGA/corpo-detector'
dest.mkdir(parents=True, exist_ok=True)
peso = dest / 'corpo-detector.pt'
shutil.copy2(orig, peso)
def le(p):
    p = M / p
    if not p.is_file(): return {}
    d = json.loads(p.read_text())
    return {k: v['por_classe'].get('corpo_deformidade', {}).get('f1') for k, v in d['limiares'].items()}
meta = {'candidato': 'corpo-detector', 'criado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'sha256': hashlib.sha256(peso.read_bytes()).hexdigest(), 'classes': ['corpo_deformidade'],
        'imgsz_treino': 480, 'roi': 'obrigatória (preprocessamento.json)',
        'f1_treino': le('corpo-detector-roi/limiares-train.json'),
        'f1_teste': le('corpo-detector-roi/limiares-test.json'),
        'escopo': 'SÓ corpo (deformidade). Não substitui o detector de tampa: são modelos separados.',
        'ressalva': 'PoC: 40 imagens com defeito + 186 negativos; tende a memorizar o que viu.',
        'limiar_recomendado': 0.15}
(dest / 'modelo.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
with (dest / 'SHA256SUMS').open('w') as f:
    for p in sorted(dest.iterdir()):
        if p.name != 'SHA256SUMS':
            f.write(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n')
print('pacote corpo:', meta['sha256'][:16], '| teste:', meta['f1_teste'])
PY

passo "5/7 V9: remontar a tampa com os rótulos corrigidos (ROI no espaço certo)"
rm -rf "$M/v9-3-lateral-detector-roi" "$M/v9-4-lateral-detector-roi"
./.venv/bin/python dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio \
  --permitir-classe-ausente --out "$M/v9-3-lateral-detector-roi/dataset" --ignorar-frescor >> "$LOG" 2>&1 || morre "build v9-3"
V9=$M/v9-3-lateral-detector-roi/dataset
printf 'path: %s\ntrain: %s/images/train\nval: %s/images/val\ntest: %s/images/test\nnc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n' \
  "$V9" "$V9" "$V9" "$V9" > "$V9/data-3.yaml"

passo "6/7 treino v9a (tampa, rótulos corrigidos)"
bash "$G" ./.venv/bin/python dataset/TRABALHO/treina_v1.py --vista lateral --tag v9a --roi --epochs 150 \
  --imgsz 480 --data "$V9/data-3.yaml" --modelo "$BASE" --nome v9a-rig >> "$LOG" 2>&1
W9=$M/v9a-lateral-detector-roi/runs/v9a-rig/weights/best.pt
[ -s "$W9" ] || morre "peso v9a ausente"

passo "7/7 v9a: limiares + k-fold (com os rótulos corrigidos)"
./.venv/bin/python dataset/TRABALHO/avalia_limiares.py --dataset "$V9" --peso "$W9" --split test \
  --confs 0.15,0.30 --imgsz 480 --saida "$M/v9a-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1
bash "$G" ./.venv/bin/python dataset/TRABALHO/kfold_por_item.py --dataset "$V9" --k 5 --vista lateral \
  --imgsz 480 --epochs 150 --tag kfv9 --modelo "$BASE" >> "$LOG" 2>&1 || echo "  aviso: k-fold" >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
