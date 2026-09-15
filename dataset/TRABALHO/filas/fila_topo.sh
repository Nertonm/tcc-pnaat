#!/bin/bash
# Topo: nosso domínio. Mede as duas receitas com k-fold por item (o teste de 40 é pouco).
#  a) do zero (yolov8n)
#  b) ajuste fino a partir do v0-topo (KMITL)
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-topo.log
BASE=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/topo-nosso-detector-roi
D="$BASE/dataset"
V0TOP=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v0-top-detector/weights/best.pt
echo "inicio $(date -Is)" > "$LOG"

if ! $PY dataset/TRABALHO/guarda_frescor.py >> "$LOG" 2>&1; then
  $PY dataset/TRABALHO/exporta_anotacoes.py >> "$LOG" 2>&1
fi
if [ ! -f "$D/manifest.json" ]; then
  echo "=== montando dataset de topo (so nosso dominio) ===" >> "$LOG"
  $PY dataset/TRABALHO/monta_v1_detector.py --vista topo --roi --somente-dominio --out "$D" >> "$LOG" 2>&1
fi
echo "=== k-fold: topo DO ZERO ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$D" --k 5 --imgsz 480 --epochs 200 \
    --vista topo --tag kfoldzero 2>&1 | tail -12 >> "$LOG"
echo "=== k-fold: topo AJUSTADO do KMITL ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$D" --k 5 --imgsz 480 --epochs 200 \
    --vista topo --tag kfoldft --modelo "$V0TOP" 2>&1 | tail -12 >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
