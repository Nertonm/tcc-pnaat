#!/bin/bash
# v4: 4 classes (normal, tampa_ausente, defeito_tampa, corpo_deformidade) no nosso dominio.
# Espera a fila v3 (mesmo GPU). Receita: ajuste fino dos pesos mistos, 480px.
# Entrega a tabela de limiar por classe — é o que sustenta "detectar com limiar baixo".
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-v4-corpo.log
BASE=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v4-lateral-detector-roi
D="$BASE/dataset"
echo "inicio $(date -Is) — aguardando fila v3" > "$LOG"
for i in $(seq 1 480); do
  grep -q "^fim " ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-v3-rig.log 2>/dev/null && break
  sleep 30
done
sleep 15
echo "=== build v4 (4 classes, phash, ROI) $(date -Is) ===" >> "$LOG"
if [ ! -f "$D/manifest.json" ]; then
  $PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio --com-corpo \
      --out "$D" >> "$LOG" 2>&1
fi
BASE_PESO=$(ls -t ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v3-lateral-detector-roi/runs/*/weights/best.pt \
            ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v2-lateral-detector-roi/runs/*/weights/best.pt \
            ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
echo "=== ajuste fino 4 classes a partir de $BASE_PESO $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v4 --roi --epochs 150 --imgsz 480 \
    --modelo "$BASE_PESO" --nome v4-rig-4classes >> "$LOG" 2>&1
echo "=== mAP por classe (val/teste) ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$D" \
    --peso "$BASE/runs/v4-rig-4classes/weights/best.pt" --split test --imgsz 480 \
    --saida "$BASE/avaliacao-teste-proprio.json" >> "$LOG" 2>&1
echo "=== tabela de limiar por classe (o trade-off do limiar baixo) ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_limiares.py --dataset "$D" \
    --peso "$BASE/runs/v4-rig-4classes/weights/best.pt" --split test \
    --confs 0.05,0.15,0.30 --imgsz 480 --saida "$BASE/limiares-teste.json" >> "$LOG" 2>&1
echo "fim $(date -Is)" >> "$LOG"
