"""Rastreabilidade requisito -> prova. Le os IDs de docs/requisitos*.md e procura a citacao
nos testes e no codigo; escreve docs/rastreabilidade.md.

Status por requisito, sem nota de credito:
  coberto     -- o ID aparece em algum arquivo de teste (prova executavel)
  citado      -- o ID aparece so em documentacao/codigo, nunca em teste
  sem prova   -- o ID nao aparece em lugar nenhum alem do proprio documento de requisito

Uso: python3 code-workspace/scripts/rastreabilidade.py [--conferir]
     --conferir: nao escreve; sai != 0 se algum ID nao tiver linha no documento gerado.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DOCS_REQ = [RAIZ / "docs/requisitos.md", *sorted((RAIZ / "docs/requisitos").glob("*.md"))]
SAIDA = RAIZ / "docs/rastreabilidade.md"
ID = re.compile(r"\b([A-Z]{2,4}-\d{2}(?:\.\d+)?)\b")
FONTES = [RAIZ / "src-production/tests", RAIZ / "code-workspace/tests",
          RAIZ / "src-production/firmware/esp32cam-test/tests"]
CODIGO = [RAIZ / "src-production", RAIZ / "code-workspace/src"]


def ids_declarados() -> dict[str, str]:
    """ID -> titulo (primeira linha util seguinte na origem)."""
    declarados: dict[str, str] = {}
    for doc in DOCS_REQ:
        if not doc.is_file():
            continue
        linhas = doc.read_text(encoding="utf-8").splitlines()
        for i, linha in enumerate(linhas):
            for achado in ID.findall(linha):
                titulo = linha.strip().lstrip("#-* ").strip()
                if not titulo or titulo == achado:
                    titulo = next((l.strip().lstrip("#-* ") for l in linhas[i + 1:i + 3]
                                   if l.strip()), "")
                declarados.setdefault(achado, titulo[:110])
    return declarados


def ocorrencias(pastas: list[Path]) -> dict[str, list[str]]:
    achados: dict[str, list[str]] = {}
    for pasta in pastas:
        if not pasta.is_dir():
            continue
        for caminho in sorted(pasta.rglob("*")):
            if not caminho.is_file() or caminho.suffix not in {".py", ".sh", ".js", ".md", ".c"}:
                continue
            try:
                texto = caminho.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for achado in set(ID.findall(texto)):
                achados.setdefault(achado, []).append(
                    caminho.relative_to(RAIZ).as_posix())
    return achados


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conferir", action="store_true",
                    help="nao escreve: falha se algum ID declarado nao tiver linha no documento")
    a = ap.parse_args(argv)
    declarados = ids_declarados()
    em_teste = ocorrencias(FONTES)
    em_codigo = ocorrencias(CODIGO)
    status_por_id: dict[str, str] = {}
    linhas = ["# Rastreabilidade requisito -> prova", "",
              "Gerado por `code-workspace/scripts/rastreabilidade.py`. Nao editar a mao.", "",
              "| requisito | titulo | status | onde aparece |", "|---|---|---|---|"]
    for rid in sorted(declarados, key=lambda x: (x.split("-")[0], x)):
        testes, codigo = em_teste.get(rid, []), em_codigo.get(rid, [])
        if testes:
            status, onde = "coberto", ", ".join(testes[:3])
        elif codigo:
            status, onde = "citado", ", ".join(codigo[:3])
        else:
            status, onde = "sem prova", "-"
        status_por_id[rid] = status
        linhas.append(f"| `{rid}` | {declarados[rid]} | {status} | {onde} |")
    contagem: dict[str, int] = {}
    for status in status_por_id.values():
        contagem[status] = contagem.get(status, 0) + 1
    linhas += ["", f"Total: {len(declarados)} requisito(s) -- " +
               ", ".join(f"{v} {k}" for k, v in sorted(contagem.items())) + ".", ""]
    conteudo = "\n".join(linhas) + "\n"

    if a.conferir:
        if not SAIDA.is_file():
            print("documento de rastreabilidade ausente: rode sem --conferir", file=sys.stderr)
            return 1
        atual = SAIDA.read_text(encoding="utf-8")
        faltando = [rid for rid in declarados if f"`{rid}`" not in atual]
        if faltando:
            print(f"requisito(s) sem linha: {', '.join(faltando)}", file=sys.stderr)
            return 1
        print(f"rastreabilidade ok: {len(declarados)} requisito(s)")
        return 0

    SAIDA.write_text(conteudo, encoding="utf-8")
    for linha in linhas:
        if linha.startswith("Total:"):
            print(linha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
