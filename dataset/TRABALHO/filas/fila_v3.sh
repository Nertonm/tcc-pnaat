#!/bin/bash
# v3: melhor receita medida (ajuste fino dos pesos mistos) sobre o conjunto próprio
# ATUALIZADO (96 treino, split por item + quase-duplicata). Espera as filas em curso.
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-v3-rig.log
BASE=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v3-lateral-detector-roi
D="$BASE/dataset"
echo "inicio $(date -Is) — aguardando filas (kfold2 e v2)" > "$LOG"

for i in $(seq 1 480); do
  a=$(pgrep -cf "fila_kfold2.sh" || true); b=$(grep -c "^fim " ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-treino-v2.log 2>/dev/null || echo 0)
  [ "$a" = "0" ] && [ "$b" != "0" ] && break
  sleep 30
done
sleep 20

echo "=== re-export + trava de frescor ===" >> "$LOG"
$PY dataset/TRABALHO/exporta_anotacoes.py >> "$LOG" 2>&1
$PY dataset/TRABALHO/guarda_frescor.py >> "$LOG" 2>&1 || { echo "frescor instavel" >> "$LOG"; exit 1; }

echo "=== build v3 (somente dominio, ROI, com phash) $(date -Is) ===" >> "$LOG"
if [ ! -f "$D/manifest.json" ]; then
  $PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio --out "$D" >> "$LOG" 2>&1
fi

BASE_PESO=$(ls -t ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v2-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
[ -n "$BASE_PESO" ] || BASE_PESO=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/runs/v1-lateral-yolov8n-dominio/weights/best.pt
echo "=== ajuste fino do melhor misto ($BASE_PESO) em 480 $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v3 --roi --epochs 150 --imgsz 480 \
    --modelo "$BASE_PESO" --nome v3-rig-ajuste-fino >> "$LOG" 2>&1

echo "=== avaliacao no teste proprio do v3 ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$D" \
    --peso "$BASE/runs/v3-rig-ajuste-fino/weights/best.pt" --split test --imgsz 480 \
    --saida "$BASE/avaliacao-teste-proprio.json" >> "$LOG" 2>&1

echo "=== k-fold 5x por item no v3 ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$D" --k 5 --vista lateral --imgsz 480 \
    --epochs 150 --tag v3kfold --modelo "$BASE_PESO" 2>&1 | tail -12 >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
