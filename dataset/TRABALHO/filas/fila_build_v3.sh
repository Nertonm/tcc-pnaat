#!/bin/bash
# Constrói os datasets do nosso domínio COM a correção de quase-duplicata e roda os
# k-folds em cima deles. CPU-only na construção; o treino das dobras usa GPU (junto
# com as filas de treino, são jobs pequenos).
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-build-v3.log
echo "inicio $(date -Is)" > "$LOG"

for v in lateral topo; do
  D="${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v3-$v-detector-roi/dataset"
  echo "=== build v3 $v $(date -Is) ===" >> "$LOG"
  if [ -f "$D/manifest.json" ]; then echo "  ja existe" >> "$LOG"; else
    $PY dataset/TRABALHO/monta_v1_detector.py --vista $v --roi --somente-dominio --out "$D" \
        --ignorar-frescor >> "$LOG" 2>&1
  fi
  tail -8 "$LOG"
done
echo "=== k-fold LATERAL (5 dobras) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v3-lateral-detector-roi/dataset \
  --k 5 --vista lateral --imgsz 480 --epochs 150 --tag kfl4 \
  --modelo "$(ls -t ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/runs/*/weights/best.pt | head -1)" 2>&1 | tail -14 >> "$LOG"
echo "=== k-fold TOPO (5 dobras) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v3-topo-detector-roi/dataset \
  --k 5 --vista topo --imgsz 480 --epochs 200 --tag kft4 2>&1 | tail -14 >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
