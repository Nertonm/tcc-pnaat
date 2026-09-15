#!/bin/bash
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-kfold.log
echo "inicio $(date -Is)" > "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/rig-lateral-detector-roi/dataset \
    --k 5 --imgsz 480 --epochs 150 >> "$LOG" 2>&1
echo "fim $(date -Is)" >> "$LOG"
