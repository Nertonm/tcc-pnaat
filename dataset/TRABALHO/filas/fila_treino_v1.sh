#!/bin/bash
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-treino-v1.log
echo "inicio $(date -Is)" > "$LOG"
for v in lateral topo; do
  d="${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-$v-detector-roi/dataset"
  base="${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-$v-detector-roi"
  echo "=== $v: treino 60 epocas (dataset com ROI) $(date -Is) ===" >> "$LOG"
  $PY dataset/TRABALHO/treina_v1.py --vista "$v" --roi --oversampled >> "$LOG" 2>&1
  peso="$base/runs/v1-$v-yolov8n-dominio/weights/best.pt"
  echo "=== $v: avaliacao por dominio no teste $(date -Is) ===" >> "$LOG"
  $PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$d" --peso "$peso" --split test \
      --saida "$base/avaliacao-por-dominio-test.json" >> "$LOG" 2>&1
done
echo "fim $(date -Is)" >> "$LOG"
