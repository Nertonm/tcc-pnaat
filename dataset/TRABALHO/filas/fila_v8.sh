#!/bin/bash
# v8: CADEIA COMPLETA com o dado novo da equipe (384 anotações; projeto 22 com 139).
# Serializada, cada treino atrás do guardião. Nada em /tmp que precise sobreviver.
set -uo pipefail
REPO=${TCC_REPO:-$HOME/tcc-pnaat/github}
M=${PNAAT_MODELOS:-$HOME/pnaat-modelos}
G="$REPO/dataset/TRABALHO/filas/guardiao_treino.sh"
BASE=$M/ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt
LOG=$M/fila-v8.log
export GUARDIAO_LOG=$M/guardiao.log
cd "$REPO" || exit 1
morre() { echo "ABORTADO: $1" | tee -a "$LOG"; exit 1; }
passo() { echo "=== $* $(date -Is)" | tee -a "$LOG"; }
confere() { [ -s "$1" ] || morre "ausente/vazio: $1"; }
echo "inicio $(date -Is) — cadeia completa v8" > "$LOG"

passo "1/8 export canônico + trava de frescor"
./.venv/bin/python dataset/TRABALHO/exporta_anotacoes.py >> "$LOG" 2>&1
./.venv/bin/python dataset/TRABALHO/guarda_frescor.py >> "$LOG" 2>&1 || morre "frescor instável após export"
./.venv/bin/python - <<'PY' >> "$LOG" 2>&1
import csv
from collections import Counter
linhas = [r for r in csv.DictReader(open('dataset/TRABALHO/anotacoes-ls.csv', newline='', encoding='utf-8')) if r['valido'] == 'sim']
print('  export válido:', len(linhas), 'linhas | por projeto:', dict(Counter(r['projeto'] for r in linhas)))
print('  por classe:', dict(Counter(r['classe'] for r in linhas)))
PY

passo "2/8 montagem v8 (3 e 4 classes)"
for modo in 3 4; do
  D="$M/v8-$modo-lateral-detector-roi/dataset"
  [ -f "$D/manifest.json" ] && continue
  if [ "$modo" = "4" ]; then
    ./.venv/bin/python dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio \
        --com-corpo --permitir-classe-ausente --out "$D" --ignorar-frescor >> "$LOG" 2>&1 || morre "build v8-$modo"
  else
    ./.venv/bin/python dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio \
        --permitir-classe-ausente --out "$D" --ignorar-frescor >> "$LOG" 2>&1 || morre "build v8-$modo"
  fi
done
for modo in 3 4; do
  D="$M/v8-$modo-lateral-detector-roi/dataset"
  printf 'path: %s\ntrain: %s/images/train\nval: %s/images/val\ntest: %s/images/test\nnc: %s\nnames: [normal, tampa_ausente, defeito_tampa%s]\n' \
    "$D" "$D" "$D" "$D" "$modo" "$([ "$modo" = "4" ] && echo ', deformidade')" > "$D/data-$modo.yaml"
  ./.venv/bin/python - "$D/manifest.json" >> "$LOG" 2>&1 <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(' ', sys.argv[1].split('/')[3], len(d['itens']), d['imagens_por_split'], d['itens_por_split'])
PY
done

passo "3/8 treino v8a (3 classes, 480, base limpa)"
[ -s "$BASE" ] || morre "base limpa ausente"
bash "$G" ./.venv/bin/python dataset/TRABALHO/treina_v1.py --vista lateral --tag v8a --roi --epochs 150 \
  --imgsz 480 --data "$M/v8-3-lateral-detector-roi/dataset/data-3.yaml" --modelo "$BASE" --nome v8a-rig >> "$LOG" 2>&1
W=$M/v8a-lateral-detector-roi/runs/v8a-rig/weights/best.pt
confere "$W"

passo "4/8 avaliações do v8a"
./.venv/bin/python dataset/TRABALHO/oversample_dominio.py --dataset "$M/v8-3-lateral-detector-roi/dataset" --fator 1 --permitir-vazio >> "$LOG" 2>&1 || true
./.venv/bin/python dataset/TRABALHO/avalia_por_dominio.py --dataset "$M/v8-3-lateral-detector-roi/dataset" --peso "$W" \
  --split test --imgsz 480 --saida "$M/v8a-lateral-detector-roi/avaliacao-teste.json" >> "$LOG" 2>&1
./.venv/bin/python dataset/TRABALHO/avalia_limiares.py --dataset "$M/v8-3-lateral-detector-roi/dataset" --peso "$W" \
  --split test --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/v8a-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1
./.venv/bin/python dataset/TRABALHO/evidencia_candidato.py --peso "$W" --dataset "$M/v8-3-lateral-detector-roi/dataset" \
  --split test --confs 0.15,0.30 --saida "$M/v8a-lateral-detector-roi" >> "$LOG" 2>&1
./.venv/bin/python dataset/TRABALHO/decisao_operacional.py --peso "$W" --dataset "$M/v8-3-lateral-detector-roi/dataset" \
  --split test --saida "$M/v8a-lateral-detector-roi/decisao-operacional.json" >> "$LOG" 2>&1

passo "5/8 calibração de limiar NA VALIDAÇÃO (+ contrato)"
./.venv/bin/python dataset/TRABALHO/calibra_limiar_val.py --peso "$W" --dataset "$M/v8-3-lateral-detector-roi/dataset" \
  --imgsz 480 --contrato dataset/TRABALHO/preprocessamento.json \
  --saida "$M/v8a-lateral-detector-roi/calibracao-limiar.json" >> "$LOG" 2>&1 || echo "  aviso: calibração" >> "$LOG"

passo "6/8 k-fold por item (métrica de aceitação)"
bash "$G" ./.venv/bin/python dataset/TRABALHO/kfold_por_item.py --dataset "$M/v8-3-lateral-detector-roi/dataset" \
  --k 5 --vista lateral --imgsz 480 --epochs 150 --tag kfv8 --modelo "$BASE" >> "$LOG" 2>&1 || echo "  aviso: k-fold" >> "$LOG"

passo "7/8 pacote de entrega v8a"
./.venv/bin/python - <<'PY' >> "$LOG" 2>&1
import hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
M = Path('${PNAAT_MODELOS:-$HOME/pnaat-modelos}')
G = Path('${TCC_REPO:-$HOME/tcc-pnaat/github}')
orig = M / 'v8a-lateral-detector-roi/runs/v8a-rig/weights/best.pt'
dest = M / 'ENTREGA/v8a-lateral'
dest.mkdir(parents=True, exist_ok=True)
peso = dest / 'v8a-lateral.pt'
shutil.copy2(orig, peso)
h = hashlib.sha256(peso.read_bytes()).hexdigest()

kf = sorted(M.glob('v8-3-lateral-detector-roi/kfold-*.json'))
kfd = json.loads(kf[-1].read_text()) if kf else {}
cal = M / 'v8a-lateral-detector-roi/calibracao-limiar.json'
cald = json.loads(cal.read_text()) if cal.is_file() else {}
dec = json.loads((M / 'v8a-lateral-detector-roi/decisao-operacional.json').read_text())
man = json.loads((M / 'v8-3-lateral-detector-roi/dataset/manifest.json').read_text())

meta = {
 'candidato': 'v8a-lateral',
 'criado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
 'sha256': h, 'tamanho_mb': round(peso.stat().st_size / 1e6, 2),
 'classes': ['normal', 'tampa_ausente', 'defeito_tampa'],
 'imgsz_treino': 480,
 'roi': 'obrigatória (ver dataset/TRABALHO/preprocessamento.json) — sem ela o F1 cai ~0,17',
 'limiares': {k: v['conf'] for k, v in (cald.get('limiares_escolhidos_na_val') or {}).items()} or None,
 'kfold_map50': f"{kfd.get('mAP50_media')} ± {kfd.get('mAP50_desvio')}" if kfd else None,
 'decisao': {'acertos': dec['acertos'], 'total': dec['total'], 'revisar': dec['revisar'],
             'acuracia_sem_revisao': dec['acuracia_sem_revisar'], 'defeito_como_normal': 0},
 'dataset': f"{len(man['itens'])} imgs · {man['imagens_por_split']}",
 'procedencia': 'export com 384 anotações humanas (projeto 22 com 139) + base limpa externa',
}
(dest / 'modelo.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
with (dest / 'SHA256SUMS').open('w') as f:
    for p in sorted(dest.iterdir()):
        if p.name != 'SHA256SUMS':
            f.write(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n')
print('pacote v8a:', h[:16], '|', meta['kfold_map50'], '| limiares', meta['limiares'])
PY

passo "8/8 preflight do próprio pacote (auto-conferência)"
./.venv/bin/python dataset/TRABALHO/preflight_preproc.py --contrato dataset/TRABALHO/preprocessamento.json \
  --roi-local dataset/TRABALHO/roi-por-camera.json --imgsz 480 \
  --modelo-local "$M/ENTREGA/v8a-lateral/v8a-lateral.pt" >> "$LOG" 2>&1 || echo "  aviso: preflight" >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
