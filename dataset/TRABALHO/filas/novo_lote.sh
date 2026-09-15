#!/usr/bin/env bash
# novo_lote.sh — execução completa para um LOTE NOVO de anotações da equipe.
#
# NÃO roda sozinho. Disparar UMA vez, quando a equipe fechar um lote no Label Studio.
#
#   uso:  bash dataset/TRABALHO/filas/novo_lote.sh <TAG> [--kfold]
#   ex.:  bash dataset/TRABALHO/filas/novo_lote.sh v10 --kfold
#
# Preparado em 2026-09-15. As flags abaixo foram conferidas contra o argparse de cada script
# (não são inventadas): monta_v1_detector --vista/--out/--com-corpo; aumenta_offline
# --dataset/--fator/--semente; avalia_limiares --dataset/--peso/--split/--confs;
# calibra_limiar_val --peso/--dataset/--imgsz/--contrato; kfold_por_item --dataset/--k/--imgsz/--epochs.
#
# NÃO sobe inferência. Quem sobe é o operador, depois, ciente.
# O que garante que este lote não é o de ontem: o teste de FRESCOR do export (passo 1) e o
# teste de FRESCOR do dataset (o monta registra a origem de cada item no manifest).
set -uo pipefail

TAG="${1:-}"; KFOLD=0
for a in "${@:2}"; do case "$a" in --kfold) KFOLD=1 ;; *) echo "arg desconhecido: $a" >&2; exit 2 ;; esac; done
[ -n "$TAG" ] || { echo "uso: bash $0 <TAG> [--kfold]" >&2; exit 2; }

REPO="$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)"
M="$(dirname "$(dirname "$REPO")")/pnaat-modelos"
DS="$REPO/dataset/TRABALHO"
G="$DS/filas/guardiao_treino.sh"
DIR="$M/$TAG-lateral-detector-roi/dataset"
LOG="$M/novo-lote-$TAG.log"
SELO="$M/ENTREGA/$TAG-lateral"
HZ="${LOTE_HZ:-2}"
export GUARDIAO_LOG="$M/guardiao.log"
cd "$REPO" || exit 1

exec > >(tee -a "$LOG") 2>&1
echo "=== LOTE $TAG · inicio $(date -Is) · kfold=$KFOLD · frescor<=${HZ}h"
trap 'rc=$?; echo "[trap] encerrou rc=$rc em $(date -Is)"' EXIT
mkdir -p "$M"

# 1. export + frescor ---------------------------------------------------------------------
echo "=== 1/7 export do Label Studio"
./.venv/bin/python "$DS/exporta_anotacoes.py" 2>&1 | tail -3 || { echo "ABORTA: export falhou"; exit 1; }
FRESCO=$(find "$DS/export" -name '*.json' -newermt "-$HZ hours" 2>/dev/null | head -1)
[ -n "$FRESCO" ] || { echo "ABORTA: nenhum export com menos de ${HZ}h — a equipe publicou o lote?"; exit 3; }
echo "  fresco: $(basename "$FRESCO")"

# 2. monta (rótulos no espaço do recorte) --------------------------------------------------
echo "=== 2/7 monta dataset em $DIR"
./.venv/bin/python "$DS/monta_v1_detector.py" --vista lateral --out "$DIR" --com-corpo 2>&1 | tail -6 \
  || { echo "ABORTA: monta falhou"; exit 1; }
[ -f "$DIR/manifest.json" ] || { echo "ABORTA: manifest ausente"; exit 1; }

# 3. aumenta 3x com blur calibrado (só o treino) ------------------------------------------
echo "=== 3/7 aumenta 3x com blur calibrado"
./.venv/bin/python "$DS/aumenta_offline.py" --dataset "$DIR/train" --fator 3 --semente 7 2>&1 | tail -4 \
  || { echo "ABORTA: aumento falhou"; exit 1; }

# 4. treino sob guardião ------------------------------------------------------------------
echo "=== 4/7 treino (guardião: temp GPU, RAM, swap, disco)"
nice -n 10 bash "$G" ./.venv/bin/yolo detect train \
  data="$DIR/data.yaml" epochs=120 imgsz=480 batch=16 \
  project="$M/$TAG-lateral-detector-roi/runs" name="$TAG-rig" exist_ok=True seed=7 workers=2 \
  2>&1 | tail -8 || { echo "ABORTA: treino falhou"; exit 1; }
PESO="$M/$TAG-lateral-detector-roi/runs/$TAG-rig/weights/best.pt"
[ -f "$PESO" ] || { echo "ABORTA: sem peso em $PESO"; exit 1; }

# 5. limiares na VALIDAÇÃO, F1 por classe no TESTE ----------------------------------------
echo "=== 5/7 calibra limiares (val) + F1 por classe (teste)"
./.venv/bin/python "$DS/calibra_limiar_val.py" --peso "$PESO" --dataset "$DIR" \
  --contrato "$DS/preprocessamento.json" 2>&1 | tail -5
./.venv/bin/python "$DS/avalia_limiares.py" --dataset "$DIR" --peso "$PESO" --split test 2>&1 | tail -14

# 6. k-fold por item ---------------------------------------------------------------------
if [ "$KFOLD" = 1 ]; then
  echo "=== 6/7 k-fold por item"
  ./.venv/bin/python "$DS/kfold_por_item.py" --dataset "$DIR" --k 5 --imgsz 480 2>&1 | tail -12
else
  echo "=== 6/7 k-fold PULADO (sem --kfold) — sem ele não há barra de erro para o lote"
fi

# 7. empacota ----------------------------------------------------------------------------
echo "=== 7/7 pacote"
mkdir -p "$SELO"; cp -a "$PESO" "$SELO/$TAG-lateral.pt"
( cd "$SELO" && sha256sum ./* > SHA256SUMS )
echo "=== LOTE $TAG pronto em $SELO · $(date -Is)"
echo "Produção é passo de OPERADOR: trocar o MODEL_NAME da unit pnaat-v0-yolo e reiniciar."
# envio para o alvo (arquivos, sem subir servico): alvo vem do ambiente, nao do repo
echo "Envio ao alvo (defina ACEROLA_MODELOS no ambiente):"
echo "  scp $SELO/$TAG-lateral.pt <alvo>:$ACEROLA_MODELOS/"
