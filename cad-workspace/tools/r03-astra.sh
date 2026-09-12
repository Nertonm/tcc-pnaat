#!/usr/bin/env bash
# r03-astra.sh -- roda o Codex Astra com o MCP FreeCAD no distrobox 'trabalho'.
# Uso:  r03-astra.sh <prompt_file>   |   r03-astra.sh --status
set -euo pipefail
GF_USER="${TCC_USER:-$USER}"
WS="${TCC_HOME:-$HOME/tcc-pnaat/github}/cad-workspace"
UVX=/home/${GF_USER}/.cache/qwen-mm-freecad-venv/bin/uvx
PORT=9875
FREE_PKG="qwen-mm-plugins[freecad] @ git+https://github.com/QwenLM/Qwen-MM-Plugins.git@qwen-mm-plugins-freecad-v1.1.0"

# Se roda como root, despacha para o nerton; se já nerton, segue direto.
if [ "$(id -un)" = "root" ]; then
  exec runuser -u "$GF_USER" -- bash "$0" "$@"
fi

case "${1:-}" in
  --status)
    echo "== RPC ==";     ss -ltn 2>/dev/null | grep -q ":$PORT " && echo "up 127.0.0.1:$PORT" || echo "DOWN"
    echo "== FreeCAD MCP =="; pgrep -af "freecad-1.1.1|FreeCAD" | grep -v grep | head -3 || echo "none"
    echo "== MCP config =="; grep -A1 'mcp_servers.qwen-mm-plugins-freecad' ~/.codex/config.toml | head -1
    echo "== uvx resolve =="; timeout 90 "$UVX" --from "$FREE_PKG" qwen-mm-plugins-freecad --help 2>&1 | sed -n '1p'
    exit 0
    ;;
esac

PROMPT="${1:?uso: r03-astra.sh <prompt_file>}"
[ -f "$WS/$PROMPT" ] || { echo "prompt nao existe: $PROMPT"; exit 2; }

# 1. Garante RPC usando o FreeCAD gerenciado pelo proprio MCP (AppImage 1.1.1).
if ! ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  echo "RPC down -> subindo FreeCAD via MCP (janela visivel)..."
  nohup env DISPLAY=:0 QT_QPA_PLATFORM=xcb QT_X11_NO_MITSHM=1 LIBGL_ALWAYS_SOFTWARE=1 \
    WAYLAND_DISPLAY= XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
    QWEN_MM_AUTOLAUNCH=1 FREECAD_RPC_PORT=$PORT \
    "$UVX" --from "$FREE_PKG" qwen-mm-plugins-freecad --launch-app --gui >/tmp/pnaat-freecad-mcp.log 2>&1 &
  echo "aguardando RPC..."
  for i in $(seq 1 90); do ss -ltn 2>/dev/null | grep -q ":$PORT " && break; sleep 2; done
  ss -ltn 2>/dev/null | grep -q ":$PORT " || { echo "RPC nao subiu; ver /tmp/pnaat-freecad-mcp.log"; exit 3; }
fi

# 2. Roda o Astra no distrobox com o MCP apontando para o RPC vivo.
echo "== rodando Astra com MCP FreeCAD =="
distrobox enter trabalho -- bash -lc "cd $WS && codex exec --approve-for-me --skip-git-repo-check - < $PROMPT"
echo "== done =="
