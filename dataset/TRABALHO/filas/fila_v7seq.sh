#!/bin/bash
# v7 SERIALIZADO — uma rodada por vez, cada treino atrás do guardião de recursos.
# Causa: o servidor de treino travou com treinos concorrentes (2026-09-15 12:37). Aqui não há `&` de treino.
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
M=${PNAAT_MODELOS:-$HOME/pnaat-modelos}
BASE=$M/ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt
GUARD=${GUARDIAO_SCRIPT:-/tmp/guardiao_treino.sh}
LOG=$M/fila-v7seq.log
echo "inicio $(date -Is) — serializado, guardião ativo" > "$LOG"
morre() { echo "ABORTADO: $1" | tee -a "$LOG"; exit 1; }
passo() { echo "=== $* $(date -Is)" | tee -a "$LOG"; }

[ -x "$GUARD" ] || morre "guardiao ausente: $GUARD"

# 1) montagem que faltou (sozinha, sem treino junto)
passo "build v7-4 (sozinho)"
if [ ! -f "$M/v7-4-lateral-detector-roi/dataset/manifest.json" ]; then
  $PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio --com-corpo \
      --permitir-classe-ausente --out "$M/v7-4-lateral-detector-roi/dataset" --ignorar-frescor >> "$LOG" 2>&1 \
      || morre "build v7-4 falhou"
fi

# 2) preparação do braço com aumento (CPU, sem treino junto)
passo "aumento 3x do treino (copia v7-3aug)"
if [ ! -f "$M/v7-3aug-lateral-detector-roi/dataset/manifest.json" ]; then
  cp -a "$M/v7-3-lateral-detector-roi" "$M/v7-3aug-lateral-detector-roi"
  $PY dataset/TRABALHO/aumenta_offline.py --dataset "$M/v7-3aug-lateral-detector-roi/dataset" \
      --fator 3 >> "$LOG" 2>&1 || morre "aumento offline falhou"
fi

# 3) treinos: UM POR VEZ, cada um atrás do guardião
passo "treino v7a (3 classes)"
"$GUARD" $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v7a --roi --epochs 150 --imgsz 480 \
    --data /tmp/v7_3.yaml --modelo "$BASE" --nome v7a-rig >> "$LOG" 2>&1 || morre "v7a falhou"
W_A=$M/v7a-lateral-detector-roi/runs/v7a-rig/weights/best.pt
[ -s "$W_A" ] || morre "peso v7a ausente"

passo "avaliações do v7a"
$PY dataset/TRABALHO/oversample_dominio.py --dataset "$M/v7-3-lateral-detector-roi/dataset" --fator 1 --permitir-vazio >> "$LOG" 2>&1 || true
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$M/v7-3-lateral-detector-roi/dataset" --peso "$W_A" \
    --split test --imgsz 480 --saida "$M/v7a-lateral-detector-roi/avaliacao-teste.json" >> "$LOG" 2>&1 || echo "  aviso: avalia_por_dominio" >> "$LOG"
$PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v7-3-lateral-detector-roi/dataset" --peso "$W_A" \
    --split test --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/v7a-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1
$PY dataset/TRABALHO/evidencia_candidato.py --peso "$W_A" --dataset "$M/v7-3-lateral-detector-roi/dataset" \
    --split test --confs 0.15,0.30 --saida "$M/v7a-lateral-detector-roi" >> "$LOG" 2>&1
$PY dataset/TRABALHO/decisao_operacional.py --peso "$W_A" --dataset "$M/v7-3-lateral-detector-roi/dataset" \
    --split test --saida "$M/v7a-lateral-detector-roi/decisao-operacional.json" >> "$LOG" 2>&1

passo "gate fora de domínio do v7a (MVTec), argumentos corretos"
MVTEC=/srv/label-studio/corpus/benchmark/mvtec
if [ -d "$MVTEC" ] && [ -f src-production/avaliacao_ood.py ]; then
  PNAAT_PESOS="$W_A" PNAAT_CONF=0.15 PNAAT_IMGSZ=480 \
    $PY src-production/avaliacao_ood.py --mvtec "$MVTEC" --scorer scorers:v0_alarme \
    --saida "$M/v7a-lateral-detector-roi/ood-mvtec.json" >> "$LOG" 2>&1 \
    || echo "  aviso: gate OOD falhou (ver log)" >> "$LOG"
else
  echo "  aviso: MVTec ou avaliacao_ood.py ausente" >> "$LOG"
fi

passo "treino v7b (4 classes, corpo experimental)"
"$GUARD" $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v7b --roi --epochs 150 --imgsz 480 \
    --data /tmp/v7_4.yaml --modelo "$BASE" --nome v7b-rig-corpo >> "$LOG" 2>&1 || morre "v7b falhou"
W_B=$M/v7b-lateral-detector-roi/runs/v7b-rig-corpo/weights/best.pt
[ -s "$W_B" ] && $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v7-4-lateral-detector-roi/dataset" \
    --peso "$W_B" --split test --confs 0.05,0.15,0.30 --imgsz 480 \
    --saida "$M/v7b-lateral-detector-roi/limiares-teste-corpo.json" >> "$LOG" 2>&1

passo "treino v7aug (A/B do aumento offline, mesmo split)"
"$GUARD" $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v7aug --roi --epochs 150 --imgsz 480 \
    --data /tmp/v7_aug.yaml --modelo "$BASE" --nome v7aug-rig >> "$LOG" 2>&1 || morre "v7aug falhou"
W_G=$M/v7aug-lateral-detector-roi/runs/v7aug-rig/weights/best.pt
[ -s "$W_G" ] && $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v7-3aug-lateral-detector-roi/dataset" \
    --peso "$W_G" --split test --confs 0.05,0.15,0.30 --imgsz 480 \
    --saida "$M/v7aug-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1

passo "k-fold por item (métrica de aceitação, serializado internamente)"
"$GUARD" $PY dataset/TRABALHO/kfold_por_item.py --dataset "$M/v7-3-lateral-detector-roi/dataset" --k 5 \
    --vista lateral --imgsz 480 --epochs 150 --tag kfv7 --modelo "$BASE" >> "$LOG" 2>&1 || echo "  aviso: k-fold" >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
