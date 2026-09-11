#!/usr/bin/env bash
# Move arquivos de SRC para DEST com verificacao de hash antes de remover a origem.
# Guarda contra o incidente de perda silenciosa (cp falhou e rm apagou).
# Uso: mover_verificado.sh SRC DEST
set -euo pipefail
src="${1:?uso: mover_verificado.sh SRC DEST}"
dst="${2:?uso: mover_verificado.sh SRC DEST}"
mkdir -p "$dst"
shopt -s nullglob
n=0
for f in "$src"/*; do
  [ -f "$f" ] || continue
  b="$(basename "$f")"
  cp -f "$f" "$dst/$b"
  if [ "$(sha256sum <"$f" | awk '{print $1}')" != "$(sha256sum <"$dst/$b" | awk '{print $1}')" ]; then
    echo "FALHA: hash divergente em $b — origem preservada, nada removido" >&2
    exit 1
  fi
  rm -f "$f"
  n=$((n+1))
done
echo "movidos com verificacao: $n (de $src para $dst)"