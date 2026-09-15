#!/usr/bin/env bash
# A/B do BLUR sobre o dataset CORRIGIDO (v9) — o teste anterior rodou com os rótulos deslocados
# e por isso não valia. Aqui: 3x aumento no treino (agora com blur calibrado) -> treina ->
# avalia no MESMO teste do v9a -> comparação justa.
set -uo pipefail
REPO="$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)"
M="$(dirname "$(dirname "$REPO")")/pnaat-modelos"
G="$REPO/dataset/TRABALHO/filas/guardiao_treino.sh"
BASE=$M/ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt
LOG=$M/fila-blur.log
export GUARDIAO_LOG=$M/guardiao.log
cd "$REPO" || exit 1
passo() { echo "=== $* $(date -Is)" | tee -a "$LOG"; }
echo "inicio $(date -Is) — A/B do blur (dataset v9 corrigido)" > "$LOG"
trap 'rc=$?; echo "[trap] encerrou rc=$rc em $(date -Is) (linha $LINENO)" >> "$LOG"' EXIT

passo "aguarda as cadeias em curso (corpo-cls e v9-fecha)"
for i in $(seq 1 160); do
  grep -q "^fim " $M/fila-corpo-cls.log 2>/dev/null && grep -q "^fim " $M/fila-v9-fecha.log 2>/dev/null && break
  sleep 30
done
sleep 15

passo "1/5 cópia do v9 + aumento 3x com o blur calibrado"
rm -rf "$M/v9-3aug-lateral-detector-roi"
cp -a "$M/v9-3-lateral-detector-roi" "$M/v9-3aug-lateral-detector-roi"
./.venv/bin/python dataset/TRABALHO/aumenta_offline.py \
  --dataset "$M/v9-3aug-lateral-detector-roi/dataset" --fator 3 >> "$LOG" 2>&1 || { echo "ABORTADO: aumento" >> "$LOG"; exit 1; }
D="$M/v9-3aug-lateral-detector-roi/dataset"
printf 'path: %s\ntrain: %s/images/train\nval: %s/images/val\ntest: %s/images/test\nnc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n' \
  "$D" "$D" "$D" "$D" > "$D/data-3.yaml"
grep -aE "operacoes aplicadas|total de itens" "$LOG" | tail -2 | cut -c1-200

passo "2/5 treino com blur (mesma base limpa, 480, 150 épocas)"
bash "$G" ./.venv/bin/python dataset/TRABALHO/treina_v1.py --vista lateral --tag v9blur --roi --epochs 150 \
  --imgsz 480 --data "$D/data-3.yaml" --modelo "$BASE" --nome v9blur-rig >> "$LOG" 2>&1
W=$M/v9blur-lateral-detector-roi/runs/v9blur-rig/weights/best.pt
[ -s "$W" ] || { echo "ABORTADO: peso ausente" >> "$LOG"; exit 1; }

passo "3/5 avaliação no MESMO teste do v9a (comparação justa)"
./.venv/bin/python dataset/TRABALHO/avalia_limiares.py --dataset "$M/v9-3-lateral-detector-roi/dataset" \
  --peso "$W" --split test --confs 0.15,0.30 --imgsz 480 \
  --saida "$M/v9blur-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1

passo "4/5 comparação com e sem blur (classe a classe)"
./.venv/bin/python - "$M" >> "$LOG" 2>&1 <<'PY'
import json, sys
from pathlib import Path
M = Path(sys.argv[1])
def ler(p):
    p = M / p
    if not p.is_file(): return {}
    d = json.loads(p.read_text())
    return {k: {c: round(v['f1'], 3) for c, v in b['por_classe'].items()}
            for k, b in d['limiares'].items()}
sem = ler('v9a-lateral-detector-roi/limiares-teste.json')
com = ler('v9blur-lateral-detector-roi/limiares-teste.json')
print('  CONF   classe            SEM blur   COM blur')
for conf in ('0.15', '0.3'):
    for cls in ('normal', 'tampa_ausente', 'defeito_tampa'):
        a = sem.get(conf, {}).get(cls); b = com.get(conf, {}).get(cls)
        if a is None and b is None: continue
        marca = ''
        if a is not None and b is not None:
            marca = '  <- melhor' if b > a + 0.02 else ('  <- pior' if b < a - 0.02 else '')
        print(f'  {conf:5s}  {cls:16s} {str(a):>9s} {str(b):>10s}{marca}')
PY

passo "5/5 k-fold do braço com blur (aceitação do A/B)"
bash "$G" ./.venv/bin/python dataset/TRABALHO/kfold_por_item.py --dataset "$D" --k 5 --vista lateral \
  --imgsz 480 --epochs 150 --tag kfblur --modelo "$BASE" >> "$LOG" 2>&1 || echo "  aviso: k-fold" >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
