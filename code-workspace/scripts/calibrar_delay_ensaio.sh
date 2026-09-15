#!/bin/bash
# Ensaio de INTEGRACAO do caminho de bancada SEM hardware, com log ISOLADO.
#
#   eventos -> log de ensaio proprio (mesmo formato do supervisor, sem poluir o log real)
#   quadros -> camera sintetica (verdade conhecida injetada)
#
# Cobre: vista viavel, segunda vista (acumula no delay.json), caso INFEASIVEL
# (janela menor que o atraso -> tem de reprovar) e o consumo fail-closed pelo capturador.
#
#   make calibrar-delay-integracao
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PY="${RAIZ}/../.venv/bin/python"
LOG="${HOME}/poc03/log-ensaio.log"
DELAY="${HOME}/poc03/delay.json"
mkdir -p "${HOME}/poc03"
cd "$RAIZ"

duas_passagens() {
    : > "$LOG"
    printf '%s\n' "$(date +%Y-%m-%dT%H:%M:%S) EV OPEN n=1 nivel=0 t_ms=1000" \
                  "$(date +%Y-%m-%dT%H:%M:%S) EV OPEN n=2 nivel=0 t_ms=2000" >> "$LOG"
    echo "log de ensaio: $(wc -l < "$LOG") passagens em $LOG"
}

echo "=== 1) vista topo: d=150 mm, janela 2,0 s (cobre tau*=1,50 s) ==="
duas_passagens
"$PY" scripts/calibrar_delay_trigger.py --fonte log --log "$LOG" --camera-modo simulado \
    --desde-inicio --distancia-mm 150 --passagens 2 --janela 2.0 --aplicar --vista topo 2>&1 | tail -10

echo
echo "=== 2) vista lateral1: d=220 mm, janela 2,6 s (cobre tau*=2,20 s) ==="
duas_passagens
"$PY" scripts/calibrar_delay_trigger.py --fonte log --log "$LOG" --camera-modo simulado \
    --desde-inicio --distancia-mm 220 --sim-distancia 220 --passagens 2 --janela 2.6 \
    --aplicar --vista lateral1 2>&1 | tail -10

echo
echo "=== 3) CASO INFEASIVEL: d=300 mm com janela de 1,2 s (nao cobre tau*) ==="
duas_passagens
set +e
"$PY" scripts/calibrar_delay_trigger.py --fonte log --log "$LOG" --camera-modo simulado \
    --desde-inicio --distancia-mm 300 --sim-distancia 300 --passagens 2 --janela 1.2 \
    --aplicar --vista topo 2>&1 | tail -6
echo "exit_caso_infeasivel=$? (esperado: != 0)"
set -e

echo
echo "=== 4) delay.json acumulado (uma vista nao apaga a outra) ==="
"$PY" - "$DELAY" <<'PYEOF'
import json
import sys
d = json.load(open(sys.argv[1]))
for vista, v in sorted(d["vistas"].items()):
    print(f"  {vista}: tau={v['tau_s'] * 1000:7.1f} ms  d={v['distancia_mm']:5.0f} mm  "
          f"v={v['velocidade_mm_s']:6.1f} mm/s  k={v['escala_mm_por_px']:.4f} mm/px  "
          f"{v['n_amostras']} amostras em {v.get('passagens_com_amostra', '?')} passagem(ns)")
PYEOF

echo
echo "=== 5) consumo pelo capturador (fail-closed em vista nao calibrada) ==="
"$PY" - "$DELAY" <<'PYEOF'
import sys
sys.path.insert(0, "src")
from pocs.expansao_sincronizacao.delay import carrega_delay, tau_da_vista

d = carrega_delay(sys.argv[1])
for vista in ("topo", "lateral1"):
    print(f"  {vista}: {tau_da_vista(d, vista) * 1000:.1f} ms")
try:
    tau_da_vista(d, "lateral2")
except KeyError as exc:
    print(f"  lateral2 nao calibrada -> {exc}")
PYEOF
