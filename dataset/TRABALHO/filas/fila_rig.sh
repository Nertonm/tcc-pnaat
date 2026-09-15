#!/bin/bash
# Experimento: modelo lateral treinado SÓ com o nosso domínio (corpus/ + nosso/).
# Monta dataset próprio, treina com mais épocas (poucas imagens), avalia no teste do
# nosso domínio E no teste externo do v1 (para mostrar o outro lado do trade-off).
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-rig-only.log
BASE=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/rig-lateral-detector-roi
D="$BASE/dataset"
echo "inicio $(date -Is)" > "$LOG"

echo "=== guarda de frescor ===" >> "$LOG"
if ! $PY dataset/TRABALHO/guarda_frescor.py >> "$LOG" 2>&1; then
  echo "LS avancou — re-exportando" >> "$LOG"
  $PY dataset/TRABALHO/exporta_anotacoes.py >> "$LOG" 2>&1
  $PY dataset/TRABALHO/guarda_frescor.py >> "$LOG" 2>&1 || { echo "frescor instavel, abortando" >> "$LOG"; exit 1; }
fi

echo "=== montando dataset so-domínio $(date -Is) ===" >> "$LOG"
if [ -f "$D/manifest.json" ]; then echo "  ja existe" >> "$LOG"; else
  $PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio --out "$D" >> "$LOG" 2>&1
fi
$PY dataset/TRABALHO/oversample_dominio.py --dataset "$D" --fator 1 --permitir-vazio >> "$LOG" 2>&1

echo "=== treino so-domínio (150 epocas, patience 30) $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/treina_v1.py --vista lateral --tag rig --roi --epochs 150 \
    --nome rig-lateral-so-dominio >> "$LOG" 2>&1

peso="$BASE/runs/rig-lateral-so-dominio/weights/best.pt"
echo "=== avaliacao: teste do NOSSO dominio $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$D" --peso "$peso" --split test \
    --saida "$BASE/avaliacao-teste-proprio.json" >> "$LOG" 2>&1
echo "=== avaliacao cruzada: teste EXTERNO do v1 $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_por_dominio.py \
    --dataset ${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/dataset --peso "$peso" \
    --split test --saida "$BASE/avaliacao-teste-externo.json" >> "$LOG" 2>&1
echo "fim $(date -Is)" >> "$LOG"
