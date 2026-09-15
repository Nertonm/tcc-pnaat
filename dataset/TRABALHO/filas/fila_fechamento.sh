#!/bin/bash
# Cadeia de fechamento: avaliações do candidato v6 (com o p19), k-fold e evidência.
# Motivo de existir: as avaliações da fila anterior foram puladas em silêncio porque o
# caminho do peso não batia (default do diretório de modelos rodando como root).
# Aqui cada etapa confere o código de saída e FALHA ALTO se o peso/JSON não existir.
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo ${TCC_REPO:-$HOME/tcc-pnaat/github})" || exit 1
PY=./.venv/bin/python
M=${PNAAT_MODELOS:-$HOME/pnaat-modelos}
BASE=$M/ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt
LOG=$M/fila-fechamento.log
echo "inicio $(date -Is)" > "$LOG"

morre() { echo "ABORTADO: $1" >> "$LOG"; echo "ABORTADO: $1"; exit 1; }
confere() { [ -s "$1" ] || morre "arquivo ausente/vazio: $1"; }

# 0) metadados: tirar referência ao caminho errado dos pesos já movidos
$PY - <<'PY' >> "$LOG" 2>&1
import json
from pathlib import Path
for tag in ('v6a', 'v6b'):
    p = Path(f'${PNAAT_MODELOS:-$HOME/pnaat-modelos}/{tag}-lateral-detector-roi/model-meta.json')
    if not p.is_file():
        continue
    d = json.loads(p.read_text())
    def limpa(v):
        if isinstance(v, str):
            return v.replace('/root/pnaat-modelos', '${PNAAT_MODELOS:-$HOME/pnaat-modelos}')
        if isinstance(v, list):
            return [limpa(x) for x in v]
        if isinstance(v, dict):
            return {k: limpa(x) for k, x in v.items()}
        return v
    p.write_text(json.dumps(limpa(d), ensure_ascii=False, indent=1))
    print('meta corrigido:', p)
PY

W3=$M/v6a-lateral-detector-roi/runs/v6-3-rig/weights/best.pt
W4=$M/v6b-lateral-detector-roi/runs/v6-4-rig-corpo/weights/best.pt
[ -s "$W3" ] || morre "peso v6-3 ausente: $W3"
[ -s "$W4" ] || morre "peso v6-4 ausente: $W4"

# 1) listas por domínio (para a avaliação por domínio)
for d in v6-3 v6-4; do
  $PY dataset/TRABALHO/oversample_dominio.py --dataset "$M/$d-lateral-detector-roi/dataset" \
      --fator 1 --permitir-vazio >> "$LOG" 2>&1 || echo "  aviso: listas $d" >> "$LOG"
done

# 2) avaliação por domínio + tabelas de limiar
echo "=== avaliacao por dominio (v6-3) $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset "$M/v6-3-lateral-detector-roi/dataset" \
    --peso "$W3" --split test --imgsz 480 \
    --saida "$M/v6a-lateral-detector-roi/avaliacao-teste-proprio.json" >> "$LOG" 2>&1
confere "$M/v6a-lateral-detector-roi/avaliacao-teste-proprio.json"

$PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v6-3-lateral-detector-roi/dataset" --peso "$W3" \
    --split test --confs 0.05,0.15,0.30 --imgsz 480 \
    --saida "$M/v6a-lateral-detector-roi/limiares-teste.json" >> "$LOG" 2>&1
confere "$M/v6a-lateral-detector-roi/limiares-teste.json"

$PY dataset/TRABALHO/avalia_limiares.py --dataset "$M/v6-4-lateral-detector-roi/dataset" --peso "$W4" \
    --split test --confs 0.05,0.15,0.30 --imgsz 480 \
    --saida "$M/v6b-lateral-detector-roi/limiares-teste-corpo.json" >> "$LOG" 2>&1
confere "$M/v6b-lateral-detector-roi/limiares-teste-corpo.json"

# 3) evidência visual (mosaico + JSON por imagem) do candidato
echo "=== evidencia visual $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/evidencia_candidato.py --peso "$W3" --dataset "$M/v6-3-lateral-detector-roi/dataset" \
    --split test --confs 0.15,0.30 --saida "$M/v6a-lateral-detector-roi" >> "$LOG" 2>&1
confere "$M/v6a-lateral-detector-roi/evidencia-v6-3-rig-test.png"

# 4) k-fold por item do candidato (protocolo de entrega: base limpa -> ajuste fino)
echo "=== k-fold do candidato $(date -Is) ===" >> "$LOG"
$PY dataset/TRABALHO/kfold_por_item.py --dataset "$M/v6-3-lateral-detector-roi/dataset" --k 5 \
    --vista lateral --imgsz 480 --epochs 150 --tag kfcand --modelo "$BASE" 2>&1 | tail -14 >> "$LOG"

echo "fim $(date -Is)" >> "$LOG"
