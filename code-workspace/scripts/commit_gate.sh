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

echo "[gate] (1/5) suite de testes (code-workspace)"
( cd "$CW" && "$PY" -m pytest -q ) || { echo "[gate] FALHA nos testes"; falhas=1; }

echo "[gate] (2/5) suite do firmware ESP32-CAM"
( cd "$RAIZ" && "$PY" -m pytest -q src-production/firmware/esp32cam-test/tests ) || { echo "[gate] FALHA nos testes do firmware"; falhas=1; }
# A suite do PRODUTO: rodar de dentro de src-production respeita o testpaths=[tests] do pyproject
# (rodar `pytest src-production` de fora recolheria revisar/tests junto).
echo "[gate] (3/6) suite do produto (src-production)"
( cd "$RAIZ/src-production" && "$PY" -m pytest -q ) || { echo "[gate] FALHA nos testes de src-production"; falhas=1; }

# Regras F (nome indefinido, import morto, variavel nao usada) sao as que pegam o erro que passou
# verde uma vez: `NameError` em teste nao executado. Sem ruff instalado o passo avisa e nao finge.
echo "[gate] (4/6) regras de correcao (ruff -F)"
if "$PY" -c "import ruff" >/dev/null 2>&1; then
  ( cd "$RAIZ/src-production" && "$PY" -m ruff check --select F . ) \
    || { echo "[gate] FALHA nas regras F do ruff"; falhas=1; }
else
  echo "[gate] aviso: ruff ausente no ambiente (instale o extra dev) -- regras F NAO conferidas" >&2
fi

echo "[gate] (5/6) sanitizador de higiene"
"$PY" "$CW/scripts/sanitizar_repo.py" || { echo "[gate] FALHA na sanitizacao"; falhas=1; }

echo "[gate] (6/6) midia no staging"
# Regra unica em code-workspace/scripts/politica_midia.py. NAO repetir regex aqui:
# duplicar a expressao foi o que fez os tres guardas divergirem no passado.
midia_lista=$(git diff --cached --name-only --diff-filter=ACM | "$PY" "$CW/scripts/politica_midia.py" --bloqueados || true)
midia=$(printf '%s\n' "$midia_lista" | grep -c . || true)
if [ "${midia:-0}" -gt 0 ]; then
  echo "[gate] FALHA: $midia arquivo(s) de midia no staging (midia fora do git)"
  printf '%s\n' "$midia_lista" | head -5
  falhas=1
fi

if [ "$falhas" -ne 0 ]; then
  if [ "${PNAAT_HOOK_BYPASS:-0}" = "1" ]; then
    # Escape consciente: o motivo tem de estar NA MENSAGEM do commit, nao so na variavel.
    MSG="${RAIZ}/.git/COMMIT_EDITMSG"
    if grep -qiE '^Bypass: *\S' "$MSG" 2>/dev/null; then
      echo "[gate] BLOQUEADO, mas PNAAT_HOOK_BYPASS=1 e trailer 'Bypass: <motivo>' presente -> passando." >&2
      exit 0
    fi
    echo "[gate] PNAAT_HOOK_BYPASS=1 exige o trailer 'Bypass: <motivo>' na mensagem do commit." >&2
    exit 1
  fi
  echo "[gate] COMMIT BLOQUEADO. Corrija os itens acima." >&2
  exit 1
fi
echo "[gate] ok"
exit 0
