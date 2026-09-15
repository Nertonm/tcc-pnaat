#!/bin/bash
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-kfold3.log
echo "inicio $(date -Is)" > "$LOG"
echo "=== k-fold LATERAL (5 dobras, 480, ajuste fino do misto) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v3-lateral-detector-roi/dataset \
  --k 5 --vista lateral --imgsz 480 --epochs 150 --tag kfl3 \
  --modelo "$(ls -t ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/runs/*/weights/best.pt | head -1)" 2>&1 | tail -14 >> "$LOG"
echo "=== k-fold TOPO (5 dobras, 480) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/topo-nosso-detector-roi/dataset \
  --k 5 --vista topo --imgsz 480 --epochs 200 --tag kft3 2>&1 | tail -14 >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
