#!/bin/bash
# Cadeia FINAL: datasets com o p19 incluído (o dado que a equipe subiu hoje) + treino limpo.
# Espera o orquestrador atual (fila_limpa.sh) terminar para não disputar GPU.
#   1) build v6: 3 classes (tampa) e 4 classes (com corpo_deformidade), ROI + phash
#   2) ajuste fino dos dois a partir da MESMA base limpa (pré-treino externo puro)
#   3) avaliação por domínio + tabela de limiar por classe
#   4) k-fold corrigido por item (listas separadas, disjunção verificada) com a base limpa
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
M=${PNAAT_MODELOS:-$HOME/pnaat-modelos}
LOG=$M/fila-final.log
echo "inicio $(date -Is) — aguardando fila_limpa" > "$LOG"
for i in $(seq 1 960); do
  pgrep -f "fila_limpa.sh" >/dev/null || break
  sleep 30
done
sleep 10
echo "=== builds v6 (com p19) $(date -Is) ===" >> "$LOG"
for modo in 3 4; do
  D="$M/v6-$modo-lateral-detector-roi/dataset"
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
    p = Path(f'${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v6-{modo}-lateral-detector-roi/dataset/manifest.json')
    if p.is_file():
        d = json.loads(p.read_text())
        print(f'v6-{modo}: {len(d["itens"])} imgs', d['imagens_por_split'], d['itens_por_split'], d.get('por_split_classe'))
PY

EXT_PESO=$(ls -t "$M"/ext-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
echo "base limpa: ${EXT_PESO:-AUSENTE}" >> "$LOG"
[ -n "$EXT_PESO" ] || { echo "sem base limpa" >> "$LOG"; exit 1; }

echo "=== ajustes finos finais (paralelo) $(date -Is) ===" >> "$LOG"
(
  printf 'path: %s\ntrain: %s\nval: %s\nnc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n' \
    "$M/v6-3-lateral-detector-roi/dataset" "$M/v6-3-lateral-detector-roi/dataset/images/train" \
    "$M/v6-3-lateral-detector-roi/dataset/images/val" > /tmp/v6_3.yaml
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v6a --roi --epochs 150 --imgsz 480 \
     --data /tmp/v6_3.yaml --modelo "$EXT_PESO" --nome v6-3-rig >> "$M/fila-final-3.log" 2>&1
  echo "v6 3 classes ok" >> "$LOG"
) &
(
  printf 'path: %s\ntrain: %s\nval: %s\nnc: 4\nnames: [normal, tampa_ausente, defeito_tampa, deformidade]\n' \
    "$M/v6-4-lateral-detector-roi/dataset" "$M/v6-4-lateral-detector-roi/dataset/images/train" \
    "$M/v6-4-lateral-detector-roi/dataset/images/val" > /tmp/v6_4.yaml
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v6b --roi --epochs 150 --imgsz 480 \
     --data /tmp/v6_4.yaml --modelo "$EXT_PESO" --nome v6-4-rig-corpo >> "$M/fila-final-4.log" 2>&1
  echo "v6 4 classes ok" >> "$LOG"
) &
wait

echo "=== avaliacoes $(date -Is) ===" >> "$LOG"
P3=$(ls -t "$M"/v6a-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
P4=$(ls -t "$M"/v6b-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
if [ -n "$P3" ]; then
  $PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$M/v6-3-lateral-detector-roi/dataset" \
     --peso "$P3" --split test --imgsz 480 --saida "$M/v6a-lateral-detector-roi/avaliacao-teste-limpo.json" >> "$LOG" 2>&1
  $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v6-3-lateral-detector-roi/dataset" --peso "$P3" \
     --split test --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/v6a-lateral-detector-roi/limiares-teste-limpo.json" >> "$LOG" 2>&1
fi
if [ -n "$P4" ]; then
  $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v6-4-lateral-detector-roi/dataset" --peso "$P4" \
     --split test --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/v6b-lateral-detector-roi/limiares-teste-corpo.json" >> "$LOG" 2>&1
fi

echo "=== k-fold corrigido (base limpa) $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$M/v6-3-lateral-detector-roi/dataset" --k 5 \
   --vista lateral --imgsz 480 --epochs 150 --tag kfv6 --modelo "$EXT_PESO" 2>&1 | tail -14 >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
