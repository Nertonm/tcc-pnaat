#!/bin/bash
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-kfold2.log
echo "inicio $(date -Is)" > "$LOG"
echo "=== k-fold LATERAL so-dominio (5 dobras, 480) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/rig-lateral-detector-roi/dataset \
    --k 5 --vista lateral --imgsz 480 --epochs 150 --tag kfoldlat 2>&1 | tail -14 >> "$LOG"
echo "=== k-fold TOPO so-dominio (5 dobras, 480) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/topo-nosso-detector-roi/dataset \
    --k 5 --vista topo --imgsz 480 --epochs 200 --tag kfoldtopo 2>&1 | tail -14 >> "$LOG"
echo "=== k-fold TOPO ajustado do KMITL (5 dobras, 480) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/topo-nosso-detector-roi/dataset \
    --k 5 --vista topo --imgsz 480 --epochs 200 --tag kfoldtopoft \
    --modelo ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v0-top-detector/weights/best.pt 2>&1 | tail -14 >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
