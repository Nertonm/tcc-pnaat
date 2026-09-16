"""Compara o runtime publicado com o deste clone (read-only).

O servico em producao roda copia propria do api.py. Este script:
  1. pega o sha256 local de src-production/api.py;
  2. consulta <URL>/api/health e le a versao declarada;
  3. escreve um recibo com os dois, para o hash do deployado deixar de ser BLOCKED.

Uso: python3 code-workspace/scripts/verifica_deploy.py --url http://<host>:<porta>
     --recibo <arquivo.json>   (default: fora do repositorio)
Sai != 0 quando nao consegue falar com o servico (o host pode estar fora).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
API = RAIZ / "src-production/api.py"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True, help="origem do servico, sem barra final")
    ap.add_argument("--recibo", default=None, help="onde gravar o recibo JSON")
    a = ap.parse_args(argv)
    local = hashlib.sha256(API.read_bytes()).hexdigest()
    recibo = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "url": a.url, "api_local_sha256": local, "api_publicada": None, "erro": None}
    try:
        with urllib.request.urlopen(a.url.rstrip("/") + "/api/health", timeout=10) as resp:
            recibo["api_publicada"] = json.loads(resp.read().decode()).get("api")
            recibo["http"] = resp.status
    except (urllib.error.URLError, OSError, ValueError) as erro:
        recibo["erro"] = f"{type(erro).__name__}: {erro}"
    destino = Path(a.recibo) if a.recibo else Path.home() / "tcc-pnaat" / "_fora-do-repo" \
        / "recibo-deploy.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(recibo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(recibo, ensure_ascii=False))
    if recibo["erro"]:
        print("servico inalcancavel: hash publicado continua desconhecido", file=sys.stderr)
        return 2
    print(f"api local {local[:12]} | api publicada {recibo['api_publicada']}")
    return 0 if recibo["api_publicada"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
