#!/usr/bin/env bash
# Gate deterministico de commit do TCC PNAAT (versionado, nao mora em /tmp).
# Roda: (1) suite de testes  (2) sanitizador de higiene  (3) midia no staging.
# Padrao: BLOQUEIA. Escape consciente e auditavel: PNAAT_HOOK_BYPASS=1
# Uso: code-workspace/scripts/commit_gate.sh      exit 0 = liberado; !=0 = bloqueado
set -uo pipefail

RAIZ="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CW="$RAIZ/code-workspace"
PY="${AI_PY:-$RAIZ/.venv/bin/python}"
[ -x "$PY" ] || PY="$(command -v python3)"
falhas=0

echo "[gate] (1/4) suite de testes"
( cd "$CW" && "$PY" -m pytest -q ) || { echo "[gate] FALHA nos testes"; falhas=1; }

echo "[gate] (2/4) suite do firmware ESP32-CAM"
( cd "$RAIZ" && "$PY" -m pytest -q src-production/firmware/esp32cam-test/tests ) || { echo "[gate] FALHA nos testes do firmware"; falhas=1; }

echo "[gate] (3/4) sanitizador de higiene"
"$PY" "$CW/scripts/sanitizar_repo.py" || { echo "[gate] FALHA na sanitizacao"; falhas=1; }

echo "[gate] (4/4) midia no staging"
MIDIA_PAT='\.(jpg|jpeg|png|bmp|webp|mp4|mov|stl|step|FCStd|3mf)$'
# Excecao: TODAS as imagens dentro de dataset/ sao versionadas de proposito.
# Video, CAD e qualquer midia fora de dataset/ continuam bloqueados.
MIDIA_PERMITIDA='^dataset/.*\.(jpg|jpeg|png|bmp|webp|heic|gif)$'
midia_lista=$(git diff --cached --name-only --diff-filter=ACM | grep -iE "$MIDIA_PAT" | grep -vE "$MIDIA_PERMITIDA" || true)
midia=$(printf '%s\n' "$midia_lista" | grep -c . || true)
if [ "${midia:-0}" -gt 0 ]; then
  echo "[gate] FALHA: $midia arquivo(s) de midia no staging (midia fora do git)"
  printf '%s\n' "$midia_lista" | head -5
  falhas=1
fi

if [ "$falhas" -ne 0 ]; then
  if [ "${PNAAT_HOOK_BYPASS:-0}" = "1" ]; then
    echo "[gate] BLOQUEADO, mas PNAAT_HOOK_BYPASS=1 -> passando. Registre o motivo no commit." >&2
    exit 0
  fi
  echo "[gate] COMMIT BLOQUEADO. Corrija os itens acima." >&2
  exit 1
fi
echo "[gate] ok"
exit 0
