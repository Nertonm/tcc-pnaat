#!/usr/bin/env bash
# backup-pnaat.sh (v2) — monta o pacote NO host de treino; o transporte é feito por quem chama (pull).
#
# Correções sobre a v1: (a) profundidade do find cobria só parte dos caminhos; (b) a
# precedência de -name/-o/-exec pegava só o último padrão; (c) o host de treino não alcança o nó do
# homelab na porta 22 — então o script NÃO envia, só empacota.
set -euo pipefail

RAIZ=$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)
# a pasta de modelos e IRMA de tcc-pnaat/: deriva da localizacao do repo, nunca de $HOME
# (rodando como root, a home resolvida era a do root e o pacote saia vazio)
M="${PNAAT_MODELOS:-$(dirname "$(dirname "$RAIZ")")/pnaat-modelos}"
CARIMBO=$(date +%Y%m%dT%H%M%S)
STAGE=$(mktemp -d /var/tmp/backup-pnaat-XXXXXX)
PACOTE=/var/tmp/backup-pnaat-$CARIMBO.tar.gz

mkdir -p "$STAGE/pesos" "$STAGE/evidencias" "$STAGE/manifests"

# 1) pesos (candidatos e bases; ignora os runs de k-fold, que são descartáveis)
n=0
while IFS= read -r w; do
  nome=$(echo "$w" | sed "s#$M/##; s#/runs/#__#; s#/weights/best.pt##")
  cp -f "$w" "$STAGE/pesos/${nome}__best.pt"; n=$((n+1))
done < <(find "$M" -mindepth 4 -maxdepth 6 -path "*/weights/best.pt" 2>/dev/null \
         | grep -vE "kfold|kfcand|kfv7|kflimpo|kfl4|kft4" | sort | head -25)
echo "pesos copiados: $n"

# 2) evidências (JSONs) e manifests dos datasets
find "$M" -mindepth 2 -maxdepth 3 -type f -name "*.json" 2>/dev/null \
  \( -name "avaliacao-*" -o -name "limiares-*" -o -name "evidencia-*" -o -name "decisao-*" \
     -o -name "kfold-*" -o -name "model-meta.json" -o -name "ood-*" \) \
  -exec cp -f {} "$STAGE/evidencias/" \; 2>/dev/null || true
find "$M" -mindepth 3 -maxdepth 4 -type f -name manifest.json 2>/dev/null \
  -exec sh -c 'cp -f "$1" "$2/$(echo "$1" | sed "s#/home/[^/]*/pnaat-modelos/##; s#/dataset/manifest.json##")__manifest.json"' _ {} "$STAGE/manifests" \; 2>/dev/null || true
echo "evidências: $(ls "$STAGE/evidencias" | wc -l) | manifests: $(ls "$STAGE/manifests" | wc -l)"

# 3) bundle dos commits que ainda não existem no remote
git -C "$RAIZ" bundle create "$STAGE/commits-so-locais.bundle" "origin/main..HEAD" >/dev/null 2>&1 \
  && echo "bundle: ok ($(stat -c%s "$STAGE/commits-so-locais.bundle") bytes)" \
  || echo "bundle: não criado (verificar range)"

# 4) índice com sha256 de cada arquivo
( cd "$STAGE" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
tar -czf "$PACOTE" -C "$STAGE" .
rm -rf "$STAGE"

echo "pacote: $PACOTE ($(du -h "$PACOTE" | cut -f1))"
echo "sha256: $(sha256sum "$PACOTE" | cut -d' ' -f1)"
echo "puxe com: scp -J <host-do-salto> -i <chave> -P <porta> <usuario>@<host-do-tailnet>:$PACOTE <destino>/"
