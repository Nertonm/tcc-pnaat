#!/bin/bash
# Orquestrador: avaliação SEM CONTAMINAÇÃO + frentes paralelas (2026-09-15)
#
# Motivo: auditoria achou que os pesos-base (v1/v2/v0) já viram imagens do teste do v3
# (12 de 18). Nenhum peso existente é limpo. Aqui:
#   1) pré-treino EXTERNO PURO (base limpa, sem nenhuma imagem nossa)
#   2) ajuste fino dessa base no nosso treino (3 classes)      -> candidato lateral
#   3) ajuste fino dessa base no nosso treino (4 classes, corpo) -> candidato corpo
#   4) ajuste fino da base KMITL no nosso topo                  -> candidato topo
#   5) k-fold CORRIGIDO por item (listas separadas, disjunção verificada)
#   6) avaliação por domínio + tabela de limiar
set -uo pipefail
cd ${TCC_REPO:-$HOME/tcc-pnaat/github} || exit 1
PY=./.venv/bin/python
M=${PNAAT_MODELOS:-$HOME/pnaat-modelos}
V3=$M/v3-lateral-detector-roi
LOG=$M/fila-limpa.log
echo "inicio $(date -Is)" > "$LOG"

# ---------- 0) lista externa pura ----------
$PY - <<'PY' >> "$LOG" 2>&1
import json
from pathlib import Path
v1 = json.loads(Path('${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/dataset/manifest.json').read_text())
base = Path('${PNAAT_MODELOS:-$HOME/pnaat-modelos}/v1-lateral-detector-roi/dataset')
ext = [str(base / 'images' / i['split'] / i['arquivo']) for i in v1['itens']
       if i['origem'].startswith('externo') and i['split'] == 'train']
nossas = [l for l in ext if 'corpus' in l or 'nosso' in l]
assert not nossas, nossas[:3]
Path('${PNAAT_MODELOS:-$HOME/pnaat-modelos}/ext-treino.txt').write_text('\n'.join(sorted(ext)) + '\n')
print('lista externa pura:', len(ext), 'imagens | imagens nossas no meio:', len(nossas))
PY

printf 'path: %s\n' "$M/v1-lateral-detector-roi/dataset" > /tmp/ext.yaml
printf 'train: %s\n' "$M/ext-treino.txt" >> /tmp/ext.yaml
printf 'val: %s\n' "$M/v1-lateral-detector-roi/dataset/val-externo.txt" >> /tmp/ext.yaml
printf 'nc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n' >> /tmp/ext.yaml

# yaml do ajuste fino no nosso domínio (3 classes) a partir do v3
printf 'path: %s\n' "$V3/dataset" > /tmp/rig3.yaml
printf 'train: %s\n' "$V3/dataset/images/train" >> /tmp/rig3.yaml
printf 'val: %s\n' "$V3/dataset/images/val" >> /tmp/rig3.yaml
printf 'nc: 3\nnames: [normal, tampa_ausente, defeito_tampa]\n' >> /tmp/rig3.yaml

# ---------- builds (CPU) que não dependem do GPU ----------
echo "=== build topo do nosso dominio (gate adaptativo) $(date -Is) ===" >> "$LOG"
if [ ! -f "$M/v3-topo-detector-roi/dataset/manifest.json" ]; then
  $PY dataset/TRABALHO/monta_v1_detector.py --vista topo --roi --somente-dominio \
      --permitir-classe-ausente --out "$M/v3-topo-detector-roi/dataset" --ignorar-frescor >> "$LOG" 2>&1
fi
echo "=== build v4 (4 classes, corpo_deformidade) $(date -Is) ===" >> "$LOG"
if [ ! -f "$M/v4-lateral-detector-roi/dataset/manifest.json" ]; then
  $PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio --com-corpo \
      --permitir-classe-ausente --out "$M/v4-lateral-detector-roi/dataset" --ignorar-frescor >> "$LOG" 2>&1
fi

# ---------- 1) pré-treino externo puro (base limpa) ----------
echo "=== PRE-TREINO EXTERNO PURO $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/treina_v1.py --vista lateral --tag ext --roi --epochs 60 --imgsz 480 \
    --data /tmp/ext.yaml --modelo yolov8n.pt --nome ext-pretreino >> "$LOG" 2>&1
EXT_PESO=$(ls -t "$M"/ext-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
echo "BASE LIMPA: ${EXT_PESO:-AUSENTE}" >> "$LOG"
[ -n "$EXT_PESO" ] || { echo "sem base limpa — abortando" >> "$LOG"; exit 1; }

# ---------- 2) três ajustes finos em PARALELO ----------
echo "=== ajustes finos em paralelo $(date -Is) ===" >> "$LOG"
(
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v5 --roi --epochs 150 --imgsz 480 \
     --data /tmp/rig3.yaml --modelo "$EXT_PESO" --nome v5-rig-limpo >> "$M/fila-limpa-v5.log" 2>&1
  echo "v5 ok" >> "$LOG"
) &
(
  printf 'nc: 4\nnames: [normal, tampa_ausente, defeito_tampa, deformidade]\n' > /tmp/rig4.yaml
  printf 'path: %s\ntrain: %s\ntest: %s\n' "$M/v4-lateral-detector-roi/dataset" \
     "$M/v4-lateral-detector-roi/dataset/images/train" "$M/v4-lateral-detector-roi/dataset/images/test" >> /tmp/rig4.yaml
  printf 'val: %s\n' "$M/v4-lateral-detector-roi/dataset/images/val" >> /tmp/rig4.yaml
  $PY dataset/TRABALHO/treina_v1.py --vista lateral --tag v4 --roi --epochs 150 --imgsz 480 \
     --data /tmp/rig4.yaml --modelo "$EXT_PESO" --nome v4-rig-corpo >> "$M/fila-limpa-v4.log" 2>&1
  echo "v4 ok" >> "$LOG"
) &
(
  TOPO_YAML=/tmp/toporig.yaml
  printf 'path: %s\ntrain: %s\nval: %s\nnc: 2\nnames: [normal, tampa_ausente]\n' \
     "$M/v3-topo-detector-roi/dataset" "$M/v3-topo-detector-roi/dataset/images/train" \
     "$M/v3-topo-detector-roi/dataset/images/val" > $TOPO_YAML
  KMITL=$(ls -t "$M"/v0-top-detector/weights/*.pt 2>/dev/null | head -1)
  $PY dataset/TRABALHO/treina_v1.py --vista topo --tag t5 --roi --epochs 200 --imgsz 480 \
     --data $TOPO_YAML --modelo "$KMITL" --nome t5-topo-limpo >> "$M/fila-limpa-topo.log" 2>&1
  echo "topo ok (base $KMITL)" >> "$LOG"
) &
wait

# ---------- 3) avaliações + k-fold corrigido ----------
echo "=== avaliacoes $(date -Is) ===" >> "$LOG"
V5_PESO=$(ls -t "$M"/v5-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
V4_PESO=$(ls -t "$M"/v4-lateral-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)
T5_PESO=$(ls -t "$M"/t5-topo-detector-roi/runs/*/weights/best.pt 2>/dev/null | head -1)

if [ -n "$V5_PESO" ]; then
  $PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$V3/dataset" --peso "$V5_PESO" \
     --split test --imgsz 480 --saida "$M/v5-lateral-detector-roi/avaliacao-teste-limpo.json" >> "$LOG" 2>&1
  $PY dataset/TRABALHO/avalia_limiares.py --dataset "$V3/dataset" --peso "$V5_PESO" --split test \
     --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/v5-lateral-detector-roi/limiares-teste-limpo.json" >> "$LOG" 2>&1
fi
if [ -n "$V4_PESO" ]; then
  $PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$M/v4-lateral-detector-roi/dataset" \
     --peso "$V4_PESO" --split test --imgsz 480 --saida "$M/v4-lateral-detector-roi/avaliacao-teste-4classes.json" >> "$LOG" 2>&1
  $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v4-lateral-detector-roi/dataset" --peso "$V4_PESO" \
     --split test --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/v4-lateral-detector-roi/limiares-teste-4classes.json" >> "$LOG" 2>&1
fi
if [ -n "$T5_PESO" ]; then
  $PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v3-topo-detector-roi/dataset" --peso "$T5_PESO" \
     --split test --confs 0.05,0.15,0.30 --imgsz 480 --saida "$M/t5-topo-detector-roi/limiares-teste.json" >> "$LOG" 2>&1
fi

echo "=== k-fold CORRIGIDO: lateral (base limpa) $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$V3/dataset" --k 5 --vista lateral \
   --imgsz 480 --epochs 150 --tag kflimpo --modelo "$EXT_PESO" 2>&1 | tail -12 >> "$LOG"

echo "=== k-fold CORRIGIDO: topo (base KMITL) ===" >> "$LOG"
KMITL=$(ls -t "$M"/v0-top-detector/weights/*.pt 2>/dev/null | head -1)
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$M/v3-topo-detector-roi/dataset" --k 5 --vista topo \
   --imgsz 480 --epochs 200 --tag kftlimpo --modelo "$KMITL" 2>&1 | tail -12 >> "$LOG"

echo "fim $(date -Is)" >> "$LOG"
