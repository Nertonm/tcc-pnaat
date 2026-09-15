#!/bin/bash
# Experimento de resolução no modelo só-domínio: 480 e 640 contra o baseline 320.
# Motivo: as imagens agora são recortes de ROI; 320 pode estar comprimindo a tampa
# (mAP50-95 0.395 denuncia caixa frouxa). Avalia sempre no MESMO teste (23 imagens).
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-rig-resolucao.log
BASE=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/rig-lateral-detector-roi
D="$BASE/dataset"
echo "inicio $(date -Is)" > "$LOG"
for sz in 480 640; do
  echo "=== treino so-dominio imgsz=$sz $(date -Is) ===" >> "$LOG"
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag rig --roi --epochs 150 \
      --imgsz $sz --nome rig-lateral-so-dominio-$sz >> "$LOG" 2>&1
  echo "=== avaliacao imgsz=$sz no teste do nosso dominio ===" >> "$LOG"
  $PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$D" \
      --peso "$BASE/runs/rig-lateral-so-dominio-$sz/weights/best.pt" --split test \
      --imgsz $sz --saida "$BASE/avaliacao-teste-proprio-$sz.json" >> "$LOG" 2>&1
done
echo "fim $(date -Is)" >> "$LOG"
