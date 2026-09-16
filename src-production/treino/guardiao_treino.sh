#!/bin/bash
# guardiao_treino.sh: porta de recursos antes/depois de UM treino no servidor de treino.
#
# Motivo: o servidor de treino travou em 2026-09-15 12:37 com 3-5 treinos concorrentes + 2 montagens
# de dataset + k-fold (load ~9 numa maquina de 8 threads, 15G de RAM, GPU 6G). A convencao
# do repo ja dizia "uma GPU/rodada": foi violada. Este guardiao passa a ser obrigatorio.
#
# Uso: guardiao_treino.sh <comando...>
#   aplica: gate de RAM/swap/load/GPU/disco, limite de threads, nice/ionice, log de estado,
#   watchdog que ABORTA o treino se a RAM disponivel cair abaixo do minimo ou o swap crescer.
set -uo pipefail

RAIZ="$(dirname "$(readlink -f "$0")")"
while [ ! -d "$RAIZ/docs" ] || [ ! -d "$RAIZ/dataset" ]; do
  [ "$RAIZ" != / ] || { printf "%s\n" "erro: raiz com docs e dataset nao encontrada" >&2; exit 1; }
  RAIZ="$(dirname "$RAIZ")"
done
MP="${PNAAT_MODELOS:-$(dirname "$(dirname "$RAIZ")")/pnaat-modelos}"

RAM_MIN_MB=${RAM_MIN_MB:-4000}          # RAM disponivel minima para iniciar
RAM_ABORTA_MB=${RAM_ABORTA_MB:-1500}    # se cair disso durante a rodada, mata
SWAP_ABORTA_MB=${SWAP_ABORTA_MB:-2048}  # swap usado maximo tolerado
LOAD_MAX=${LOAD_MAX:-5.0}
DISCO_MIN_GB=${DISCO_MIN_GB:-50}
TEMP_MAX=${TEMP_MAX:-80}        # bloqueia iniciar acima disso (GPU)
TEMP_ABORTA=${TEMP_ABORTA:-88}   # mata a rodada se passar disso
ESPERA_S=${ESPERA_S:-60}
MAX_ESPERAS=${MAX_ESPERAS:-20}          # ~20 min esperando a maquina liberar
LOG=${GUARDIAO_LOG:-$MP/guardiao.log}

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date -Is)] $*" | tee -a "$LOG"; }

ram_disp() { awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo; }
swap_usado() { awk '/SwapTotal|SwapFree/ {if ($1=="SwapTotal:") t=$2; if ($1=="SwapFree:") f=$2} END {print int((t-f)/1024)}' /proc/meminfo; }
carga() { awk '{print $1}' /proc/loadavg; }

gate() {
  local ram sw ld gpu_uso disco
  ram=$(ram_disp); sw=$(swap_usado); ld=$(carga)
  # barra apenas TREINO na GPU; outros consumidores (serviço de inferência legado) são registrados
  gpu_todos=$(nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader 2>/dev/null || true)
  gpu_uso=$(printf '%s\n' "$gpu_todos" | grep -icE 'treina|kfold|monta|yolo' || true)
  gpu_vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | tr -dc '0-9')
  gpu_temp=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null | tr -dc '0-9')
  [ -n "$gpu_temp" ] || gpu_temp=0
  disco=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
  log "estado: RAM disp ${ram}MB | swap ${sw}MB | load ${ld} | treinos na GPU ${gpu_uso} (VRAM ${gpu_vram}MiB, ${gpu_temp}C) | disco livre ${disco}G"
  if [ "$gpu_uso" != "0" ]; then log "BLOQUEADO: ja existe treino na GPU (uma rodada por vez)"; return 1; fi
  if [ "$ram" -lt "$RAM_MIN_MB" ]; then log "BLOQUEADO: RAM disponivel ${ram}MB < ${RAM_MIN_MB}MB"; return 1; fi
  if [ "$ld" -gt "$LOAD_MAX" ] 2>/dev/null; then
    awk -v l="$ld" -v m="$LOAD_MAX" 'BEGIN{exit !(l>m)}' && { log "BLOQUEADO: load ${ld} > ${LOAD_MAX}"; return 1; }
  fi
  if [ "$disco" -lt "$DISCO_MIN_GB" ]; then log "BLOQUEADO: disco livre ${disco}G < ${DISCO_MIN_GB}G"; return 1; fi
  if [ "$sw" -gt "$SWAP_ABORTA_MB" ]; then log "BLOQUEADO: swap ja em ${sw}MB"; return 1; fi
  if [ "$gpu_temp" -gt "$TEMP_MAX" ] 2>/dev/null; then
    log "BLOQUEADO: GPU a ${gpu_temp}C (limite ${TEMP_MAX}C)"; return 1
  fi
  return 0
}

i=0
while ! gate; do
  i=$((i+1))
  [ "$i" -ge "$MAX_ESPERAS" ] && { log "ABORTADO: maquina nao liberou em $((MAX_ESPERAS*ESPERA_S))s"; exit 3; }
  sleep "$ESPERA_S"
done

log "LIBERADO: iniciando comando: $*"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export MKL_NUM_THREADS="${OMP_NUM_THREADS}"
nice -n 10 ionice -c2 -n7 "$@" &
PID=$!

# watchdog: aborta se a maquina entrar em aperto
while kill -0 "$PID" 2>/dev/null; do
  sleep 60
  ram=$(ram_disp); sw=$(swap_usado)
  t_gpu=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null | tr -dc '0-9')
  if [ -n "$t_gpu" ] && [ "$t_gpu" -gt "$TEMP_ABORTA" ] 2>/dev/null; then
    log "WATCHDOG: GPU a ${t_gpu}C (limite ${TEMP_ABORTA}C) -> matando para proteger o hardware"
    kill -TERM "$PID" 2>/dev/null; sleep 10; kill -KILL "$PID" 2>/dev/null; wait "$PID" 2>/dev/null
    exit 5
  fi
  # swap alto SOZINHO não é aperto: exige também RAM disponível baixa (senão é falso positivo;
  # foi o que abortou um k-fold com 6,6 GB de RAM livre em 2026-09-15)
  if [ "$ram" -lt "$RAM_ABORTA_MB" ] || { [ "$sw" -gt "$SWAP_ABORTA_MB" ] && [ "$ram" -lt 4000 ]; }; then
    log "WATCHDOG: RAM ${ram}MB / swap ${sw}MB -> matando o treino para proteger a maquina"
    kill -TERM "$PID" 2>/dev/null; sleep 10; kill -KILL "$PID" 2>/dev/null
    wait "$PID" 2>/dev/null
    log "ABORTADO pelo watchdog"
    exit 4
  fi
done
wait "$PID"; RC=$?
log "terminado (rc=$RC): $*"
exit "$RC"
