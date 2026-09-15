#!/bin/bash
# v7: colheita do rótulo novo + melhorias medidas.
#   1) re-export + trava de frescor
#   2) build v7 (3 e 4 classes) com o rótulo mais novo
#   3) tres braços de treino, mesma base limpa:
#        v7a  3 classes            (candidato)
#        v7b  4 classes c/ corpo   (deformidade experimental)
#        v7aug 3 classes com aumento offline 3x no treino (A/B contra v7a, MESMO split)
#   4) avaliacoes por dominio, tabelas de limiar, evidencia visual
#   5) gate fora de dominio (MVTec) no candidato
#   6) k-fold por item do protocolo de entrega (metrica de aceitacao)
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
M=${PNAAT_MODELOS:-$HOME/pnaat-modelos}
BASE=$M/ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt
LOG=$M/fila-v7.log
echo "inicio $(date -Is)" > "$LOG"
morre() { echo "ABORTADO: $1" | tee -a "$LOG"; exit 1; }

echo "=== export + frescor $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/exporta_anotacoes.py >> "$LOG" 2>&1
$PY dataset/TRABALHO/guarda_frescor.py >> "$LOG" 2>&1 || morre "frescor instavel"

echo "=== build v7 $(date -Is) ===" >> "$LOG"
for modo in 3 4; do
  D="$M/v7-$modo-lateral-detector-roi/dataset"
  [ -f "$D/manifest.json" ] && continue
  if [ "$modo" = "4" ]; then
    $PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio --com-corpo \
        --permitir-classe-ausente --out "$D" --ignorar-frescor >> "$LOG" 2>&1
  else
    $PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio \
        --permitir-classe-ausente --out "$D" --ignorar-frescor >> "$LOG" 2>&1
  fi
done
$PY - <<'PY' >> "$LOG" 2>&1
import json
from pathlib import Path
for modo in (3, 4):
    p = Path(f'${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v7-{modo}-lateral-detector-roi/dataset/manifest.json')
    if p.is_file():
        d = json.loads(p.read_text())
        print(f'v7-{modo}: {len(d["itens"])} imgs', d['imagens_por_split'], d['itens_por_split'])
PY

echo "=== copia para o A/B de aumento + aumento 3x no treino ===" >> "$LOG"
if [ ! -d "$M/v7-3aug-lateral-detector-roi/dataset" ]; then
  cp -a "$M/v7-3-lateral-detector-roi" "$M/v7-3aug-lateral-detector-roi"
  $PY dataset/TRABALHO/aumenta_offline.py --dataset "$M/v7-3aug-lateral-detector-roi/dataset" \
      --fator 3 >> "$LOG" 2>&1 || echo "  aviso: aumento falhou" >> "$LOG"
fi

echo "=== treinos (paralelo) $(date -Is) ===" >> "$LOG"
(
  printf 'path: %s\ntrain: %s\nval: %s\nnc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n' \
    "$M/v7-3-lateral-detector-roi/dataset" "$M/v7-3-lateral-detector-roi/dataset/images/train" \
    "$M/v7-3-lateral-detector-roi/dataset/images/val" > /tmp/v7_3.yaml
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v7a --roi --epochs 150 --imgsz 480 \
     --data /tmp/v7_3.yaml --modelo "$BASE" --nome v7a-rig >> "$M/fila-v7a.log" 2>&1
  echo "v7a ok $(date -Is)" >> "$LOG"
) &
(
  printf 'path: %s\ntrain: %s\nval: %s\nnc: 4\nnames: [normal, tampa_ausente, defeito_tampa, deformidade]\n' \
    "$M/v7-4-lateral-detector-roi/dataset" "$M/v7-4-lateral-detector-roi/dataset/images/train" \
    "$M/v7-4-lateral-detector-roi/dataset/images/val" > /tmp/v7_4.yaml
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v7b --roi --epochs 150 --imgsz 480 \
     --data /tmp/v7_4.yaml --modelo "$BASE" --nome v7b-rig-corpo >> "$M/fila-v7b.log" 2>&1
  echo "v7b ok $(date -Is)" >> "$LOG"
) &
(
  printf 'path: %s\ntrain: %s\nval: %s\nnc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n' \
    "$M/v7-3aug-lateral-detector-roi/dataset" "$M/v7-3aug-lateral-detector-roi/dataset/images/train" \
    "$M/v7-3aug-lateral-detector-roi/dataset/images/val" > /tmp/v7_aug.yaml
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v7aug --roi --epochs 150 --imgsz 480 \
     --data /tmp/v7_aug.yaml --modelo "$BASE" --nome v7aug-rig >> "$M/fila-v7aug.log" 2>&1
  echo "v7aug ok $(date -Is)" >> "$LOG"
) &
wait

W_A=$M/v7a-lateral-detector-roi/runs/v7a-rig/weights/best.pt
W_B=$M/v7b-lateral-detector-roi/runs/v7b-rig-corpo/weights/best.pt
W_G=$M/v7aug-lateral-detector-roi/runs/v7aug-rig/weights/best.pt
[ -s "$W_A" ] || morre "peso v7a ausente"

echo "=== avaliacoes $(date -Is) ===" >> "$LOG"
for d in v7-3 v7-4; do
  $PY dataset/TRABALHO/oversample_dominio.py --dataset "$M/$d-lateral-detector-roi/dataset" \
      --fator 1 --permitir-vazio >> "$LOG" 2>&1 || true
done
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$M/v7-3-lateral-detector-roi/dataset" --peso "$W_A" \
    --split test --imgsz 480 --saida "$M/v7a-lateral-detector-roi/avaliacao-teste.json" >> "$LOG" 2>&1
$PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v7-3-lateral-detector-roi/dataset" --peso "$W_A" \
    --split test --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/v7a-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1
[ -s "$W_G" ] && $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v7-3aug-lateral-detector-roi/dataset" \
    --peso "$W_G" --split test --confs 0.05,0.15,0.30 --imgsz 480 \
    --saida "$M/v7aug-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1
[ -s "$W_B" ] && $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v7-4-lateral-detector-roi/dataset" \
    --peso "$W_B" --split test --confs 0.05,0.15,0.30 --imgsz 480 \
    --saida "$M/v7b-lateral-detector-roi/limiares-teste-corpo.json" >> "$LOG" 2>&1
$PY dataset/TRABALHO/evidencia_candidato.py --peso "$W_A" --dataset "$M/v7-3-lateral-detector-roi/dataset" \
    --split test --confs 0.15,0.30 --saida "$M/v7a-lateral-detector-roi" >> "$LOG" 2>&1

echo "=== gate fora de dominio (MVTec) no candidato $(date -Is) ===" >> "$LOG"
if [ -f src-production/avaliacao_ood.py ]; then
  $PY src-production/avaliacao_ood.py --peso "$W_A" --saida "$M/v7a-lateral-detector-roi/ood-mvtec.json" \
      >> "$LOG" 2>&1 || echo "  aviso: gate OOD falhou (ver log)" >> "$LOG"
fi

echo "=== k-fold por item (metrica de aceitacao) $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$M/v7-3-lateral-detector-roi/dataset" --k 5 \
    --vista lateral --imgsz 480 --epochs 150 --tag kfv7 --modelo "$BASE" 2>&1 | tail -14 >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
