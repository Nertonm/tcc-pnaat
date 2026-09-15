#!/bin/bash
# Experimento de transferência: começar dos pesos do v1 (treinado 98% no externo) e
# AJUSTAR só no nosso domínio. É a receita clássica (pré-treino amplo -> ajuste fino
# no alvo) e deve bater o "só-domínio do zero" se o pré-treino ajudar de fato.
# Espera a fila de resolução terminar para não sobrecarregar a GPU.
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-finetune-rig.log
BASE=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/rig-lateral-detector-roi
D="$BASE/dataset"
V1=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/runs/v1-lateral-yolov8n-dominio/weights/best.pt
echo "inicio $(date -Is) — aguardando a fila de resolucao" > "$LOG"

for i in $(seq 1 240); do
  pgrep -f "fila_rig_res.sh" >/dev/null || break
  sleep 30
done
sleep 20
[ -f "$V1" ] || { echo "pesos do v1 ausentes: $V1" >> "$LOG"; exit 1; }

echo "=== ajuste fino no nosso dominio (base = v1 misto) $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/treina_v1.py --vista lateral --tag rig --roi --epochs 120 \
    --imgsz 480 --modelo "$V1" --nome rig-lateral-finetune-do-v1 >> "$LOG" 2>&1

echo "=== avaliacao no teste do nosso dominio ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$D" \
    --peso "$BASE/runs/rig-lateral-finetune-do-v1/weights/best.pt" --split test --imgsz 480 \
    --saida "$BASE/avaliacao-teste-proprio-finetune.json" >> "$LOG" 2>&1

echo "=== avaliacao cruzada no teste externo do v1 ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_por_dominio.py \
    --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/dataset \
    --peso "$BASE/runs/rig-lateral-finetune-do-v1/weights/best.pt" --split test --imgsz 480 \
    --saida "$BASE/avaliacao-teste-externo-finetune.json" >> "$LOG" 2>&1
echo "fim $(date -Is)" >> "$LOG"
