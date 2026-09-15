#!/bin/bash
# Fila v1.2 — só roda DEPOIS que a fila do v1 terminar (mesmo dataloader/GPU, sem paralelismo).
# 1. espera a fila v1 fechar
# 2. trava de frescor: se o LS avançou, re-exporta e confere de novo
# 3. monta os datasets v2 (com o rótulo humano novo) em pasta própria — o v1 fica intacto
# 4. super-amostragem do domínio + treino v2 (--tag v2) + avaliação por domínio
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
LOG1=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-treino-v1.log
LOG=${PNAAT_MODELOS:-$HOME/pnaat-modelos}/fila-treino-v2.log
echo "v1.2: aguardando a fila do v1 terminar $(date -Is)" > "$LOG"

for i in $(seq 1 720); do
  grep -q "^fim " "$LOG1" 2>/dev/null && break
  sleep 30
done
grep -q "^fim " "$LOG1" 2>/dev/null || { echo "v1 nao terminou em 6h — abortando" >> "$LOG"; exit 1; }
echo "v1 concluido $(date -Is)" >> "$LOG"

# trava de frescor (com uma re-exportação automática se estiver velho)
for tentativa in 1 2 3; do
  if $PY dataset/TRABALHO/guarda_frescor.py >> "$LOG" 2>&1; then
    echo "frescor OK (tentativa $tentativa)" >> "$LOG"
    break
  fi
  echo "LS avancou — re-exportando ($tentativa)" >> "$LOG"
  $PY dataset/TRABALHO/exporta_anotacoes.py >> "$LOG" 2>&1
  if [ "$tentativa" = 3 ]; then echo "nao consegui frescor estavel — abortando" >> "$LOG"; exit 1; fi
done

for v in lateral topo; do
  saida="${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v2-$v-detector-roi/dataset"
  echo "=== $v: montando v2 em $saida $(date -Is) ===" >> "$LOG"
  if [ -d "$saida" ]; then echo "  saida ja existe, pulando build" >> "$LOG"; else
    $PY dataset/TRABALHO/monta_v1_detector.py --vista "$v" --roi --out "$saida" >> "$LOG" 2>&1 || {
      echo "  build falhou (trava de frescor?) — abortando $v" >> "$LOG"; continue; }
  fi
  $PY dataset/TRABALHO/oversample_dominio.py --dataset "$saida" --fator 5 >> "$LOG" 2>&1
  echo "=== $v: treino v2 (60 epocas) $(date -Is) ===" >> "$LOG"
  $PY dataset/TRABALHO/treina_v1.py --vista "$v" --tag v2 --roi --oversampled >> "$LOG" 2>&1
  peso="${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v2-$v-detector-roi/runs/v2-$v-yolov8n-dominio/weights/best.pt"
  echo "=== $v: avaliacao por dominio v2 $(date -Is) ===" >> "$LOG"
  $PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$saida" --peso "$peso" --split test \
      --saida "${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v2-$v-detector-roi/avaliacao-por-dominio-test.json" >> "$LOG" 2>&1
done
echo "fim $(date -Is)" >> "$LOG"
