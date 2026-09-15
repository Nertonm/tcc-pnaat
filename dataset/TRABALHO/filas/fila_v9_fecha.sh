#!/usr/bin/env bash
# Fecha o v9: pacote + contrato + k-fold (com o guardião já ajustado).
set -uo pipefail
REPO="$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)"
M="$(dirname "$(dirname "$REPO")")/pnaat-modelos"
G="$REPO/dataset/TRABALHO/filas/guardiao_treino.sh"
BASE=$M/ext-lateral-detector-roi/runs/ext-pretreino/weights/best.pt
LOG=$M/fila-v9-fecha.log
export GUARDIAO_LOG=$M/guardiao.log
cd "$REPO" || exit 1
passo() { echo "=== $* $(date -Is)" | tee -a "$LOG"; }
echo "inicio $(date -Is)" > "$LOG"
trap 'rc=$?; echo "[trap] encerrou rc=$rc em $(date -Is) (linha $LINENO)" >> "$LOG"' EXIT

# espera o classificador de corpo sair da frente (serialização)
passo "aguarda o classificador de corpo"
for i in $(seq 1 120); do
  grep -q "^fim " $M/fila-corpo-cls.log 2>/dev/null && break
  sleep 30
done
sleep 15

passo "1/4 pacote v9a (tampa, rótulos corrigidos)"
./.venv/bin/python - "$M" "$REPO" >> "$LOG" 2>&1 <<'PY'
import hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
M, G = Path(sys.argv[1]), Path(sys.argv[2])
orig = M / 'v9a-lateral-detector-roi/runs/v9a-rig/weights/best.pt'
dest = M / 'ENTREGA/v9a-lateral'
dest.mkdir(parents=True, exist_ok=True)
peso = dest / 'v9a-lateral.pt'
shutil.copy2(orig, peso)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
lim = json.loads((M / 'v9a-lateral-detector-roi/limiares-teste.json').read_text())
pc = lim['limiares']['0.30']['por_classe']
meta = {'candidato': 'v9a-lateral',
        'criado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'sha256': sha(peso), 'tamanho_mb': round(peso.stat().st_size / 1e6, 2),
        'classes': ['normal', 'tampa_ausente', 'defeito_tampa'],
        'imgsz_treino': 480,
        'correcao': 'rótulos agora no espaço do recorte (a montagem anterior gravava no espaço do '
                    'quadro inteiro: caixas deslocadas). Medido: defeito_tampa F1 0,400 -> 0,923',
        'f1_teste_conf_0.30': {k: v['f1'] for k, v in pc.items()},
        'roi': 'obrigatória (preprocessamento.json)'}
(dest / 'modelo.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
with (dest / 'SHA256SUMS').open('w') as f:
    for p in sorted(dest.iterdir()):
        if p.name != 'SHA256SUMS':
            f.write(f'{sha(p)}  {p.name}\n')
print('pacote v9a:', meta['sha256'][:16], '|', meta['f1_teste_conf_0.30'])
PY

passo "2/4 contrato aponta para o v9a"
./.venv/bin/python - "$M" "$REPO" >> "$LOG" 2>&1 <<'PY'
import hashlib, json, sys
from pathlib import Path
M, G = Path(sys.argv[1]), Path(sys.argv[2])
c = json.loads((G / 'dataset/TRABALHO/preprocessamento.json').read_text())
p = M / 'ENTREGA/v9a-lateral/v9a-lateral.pt'
c['modelo'] = {'arquivo': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
               'tamanho_bytes': p.stat().st_size, 'candidato': 'v9a-lateral'}
(G / 'dataset/TRABALHO/preprocessamento.json').write_text(json.dumps(c, ensure_ascii=False, indent=1))
print('contrato ->', c['modelo']['arquivo'], c['modelo']['sha256'][:16])
PY

passo "3/4 preflight do v9a"
./.venv/bin/python dataset/TRABALHO/preflight_preproc.py --contrato dataset/TRABALHO/preprocessamento.json \
  --roi-local dataset/TRABALHO/roi-por-camera.json --imgsz 480 \
  --modelo-local "$M/ENTREGA/v9a-lateral/v9a-lateral.pt" >> "$LOG" 2>&1 || echo "  aviso: preflight" >> "$LOG"

passo "4/4 k-fold do v9 (métrica de aceitação com os rótulos corrigidos)"
bash "$G" ./.venv/bin/python dataset/TRABALHO/kfold_por_item.py --dataset "$M/v9-3-lateral-detector-roi/dataset" \
  --k 5 --vista lateral --imgsz 480 --epochs 150 --tag kfv9b --modelo "$BASE" >> "$LOG" 2>&1 \
  || echo "  aviso: k-fold" >> "$LOG"
echo "fim $(date -Is)" >> "$LOG"
