#!/usr/bin/env python3
"""Auditoria repetivel de perdas de referencia/informacao do PNAAT (fluxo F5).

Roda no host do agente (onde vivem o banco de sessoes, os pastes de origem e o vault),
nao no host de build. Os caminhos vem dos argumentos ou do ambiente
(PNAAT_BANCO_SESSOES, PNAAT_PASTES_ORIGEM, PNAAT_VAULT): o repo nao guarda caminho de host.

    python3 scripts/auditar_referencias.py --repo <host>:$TCC_HOME/github
    python3 scripts/auditar_referencias.py --selftest

Checagens:
  P) pastes que mencionam PNAAT e nao sao citados por nenhum doc do repo
  S) URLs de repositorio citadas em sessoes de PNAAT que nao entram no registro de referencias
  V) notas PNAAT do vault que nao sao indexadas por nenhum doc do repo
  H) higiene: midia rastreada, arquivos root-owned na arvore, objetos .git sem escrita

Sai com codigo 1 quando encontra achado (gate do fluxo F5).
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

TERMOS_PNAAT = ("pnaat", "bottle", "garrafa", "envase")
RE_URL = re.compile(r"https?://[^\s\)\]\"'>,]+")
RE_SLUG = re.compile(r"(?:github|gitlab)\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", re.I)

# Slugs que aparecem no proprio texto das ferramentas de auditoria (auto-referencia), nao em trabalho real.
IGNORAR_SLUGS = {"fulano/nao-registrado", "usuario/repo"}


def _ssh(host: str, cmd: str, timeout: int = 60) -> str:
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
         "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8", host, cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout if r.returncode == 0 else ""


def _listar_repo(repo: str) -> tuple[list[str], str]:
    """Devolve (caminhos de docs, conteudo concatenado) do repo local ou via ssh."""
    if ":" in repo and not Path(repo).exists():
        host, caminho = repo.split(":", 1)
        docs = _ssh(host, f"find {caminho}/docs -name '*.md' -printf '%P\\n' | sort")
        cat = _ssh(host, f"cat {caminho}/docs/*.md {caminho}/docs/**/*.md 2>/dev/null")
        return [d for d in docs.splitlines() if d], cat
    base = Path(repo)
    arquivos = sorted(str(p.relative_to(base / "docs")) for p in (base / "docs").rglob("*.md"))
    cat = "\n".join(p.read_text(errors="replace") for p in (base / "docs").rglob("*.md"))
    return arquivos, cat


def checar_pastes(pastes: Path, docs_conteudo: str, limite: int = 10) -> list[str]:
    achados: list[str] = []
    if not pastes.is_dir():
        return [f"pastes ausente: {pastes}"]
    for p in sorted(pastes.glob("*.txt")):
        try:
            txt = p.read_text(errors="replace")[:4000].lower()
        except Exception:
            continue
        if not (("pnaat" in txt and ("garrafa" in txt or "envase" in txt))
                or ("tcc" in txt and "garrafa" in txt)):
            continue
        if p.name in docs_conteudo:
            continue
        achados.append(str(p.name))
    return achados[:limite]


def checar_sessoes(state_db: Path, docs_conteudo: str, limite: int = 12) -> list[str]:
    if not state_db.exists():
        return [f"banco de sessoes ausente: {state_db}"]
    con = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True)
    cur = con.cursor()
    faltando: set[str] = set()
    # Proximidade: a URL precisa estar a <=400 chars de um termo de garrafa/envase/PET na MESMA
    # mensagem. Sessoes mistas (PNAAT + outros projetos) citam dezenas de repos irrelevantes.
    consulta = (
        "select content from messages where lower(content) like '%pnaat%' and content like '%http%' "
        "and (lower(content) like '%garrafa%' or lower(content) like '%envase%' "
        "or lower(content) like '%bottle%')"
    )
    for (content,) in cur.execute(consulta):
        baixo = (content or "").lower()
        ancoras = [m.start() for t in ("garrafa", "envase", "bottle", "pet ") for m in re.finditer(re.escape(t), baixo)]
        for i in ancoras:
            janela = (content or "")[max(0, i - 400): i + 400]
            content = content  # noqa: PLW0127 - mantido por clareza
            for url in RE_URL.findall(janela):
                slug = RE_SLUG.search(url)
                if not slug:
                    continue
                alvo = slug.group(1)
                if alvo.lower() in IGNORAR_SLUGS:
                    continue
                if alvo.lower() in docs_conteudo.lower():
                    continue
                faltando.add(alvo)
    con.close()
    return sorted(faltando)[:limite]


def checar_vault(vault: Path, docs_conteudo: str, limite: int = 15) -> list[str]:
    if not vault.is_dir():
        return [f"vault ausente: {vault}"]
    faltando: list[str] = []
    for p in sorted(vault.rglob("*pnaat*.md")):
        if p.stem in docs_conteudo:
            continue
        faltando.append(p.stem)
    return faltando[:limite]


def checar_higiene(repo: str, limites: int = 5) -> list[str]:
    if ":" not in repo or Path(repo).exists():
        return []
    host, caminho = repo.split(":", 1)
    out = _ssh(host, (
        f"cd {caminho} && "
        f"echo MEDIA=$(git ls-files | grep -icE '\\.(jpg|jpeg|png|bmp|mp4|mov|stl|step|FCStd|3mf)$'); "
        f"echo ROOTOWNED=$(find . -path ./.git -prune -o -user root -print 2>/dev/null | wc -l); "
        f"echo GITOBJ=$(find .git/objects -not -user \"$(id -un)\" 2>/dev/null | wc -l)"
    ))
    achados = []
    for linha in out.splitlines():
        if "=" in linha:
            k, v = linha.split("=", 1)
            if v.strip().isdigit() and int(v) > 0:
                achados.append(f"{k}={v.strip()}")
    return achados[:limites]


def _selftest() -> int:
    """Prova que as checagens detectam achado (senao a auditoria e teatro)."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        void = base / "docs"; void.mkdir()
        (void / "index.md").write_text("# vazio\n")
        docs_conteudo = (void / "index.md").read_text()

        pastes = base / "pastes"; pastes.mkdir()
        (pastes / "paste_1_x.txt").write_text("projeto PNAAT garrafa pet" * 20)
        assert checar_pastes(pastes, docs_conteudo), "nao detectou paste nao citado"

        db = base / "sessoes.db"
        con = sqlite3.connect(db)
        con.execute("create table messages (content text)")
        con.execute("insert into messages values (?)",
                    ("pnaat garrafa ver https://github.com/Fixture/repo-de-teste",))
        con.commit(); con.close()
        assert "Fixture/repo-de-teste" in checar_sessoes(db, docs_conteudo), "nao detectou repo nao registrado"

        vault = base / "vault"; (vault / "10-Projects").mkdir(parents=True)
        (vault / "10-Projects" / "pnaat-nota-orfa.md").write_text("x")
        assert checar_vault(vault, docs_conteudo), "nao detectou nota orfa"

        # contraprova: quando o doc registra tudo, nao ha achado
        docs_conteudo2 = docs_conteudo + "paste_1_x.txt pnaat-nota-orfa Fixture/repo-de-teste"
        assert not checar_pastes(pastes, docs_conteudo2)
        assert not checar_sessoes(db, docs_conteudo2)
        assert not checar_vault(vault, docs_conteudo2)
    print("selftest OK: as checagens detectam achado sintetico e ficam limpas quando ha registro")
    return 0


def _resolver(valor, var: str, flag: str, descricao: str) -> Path:
    """Caminho de dado do agente: vem do argumento ou do ambiente (nunca do repo)."""
    if valor is not None:
        return Path(valor)
    env = os.environ.get(var)
    if not env:
        raise SystemExit(f"informe {flag} ou defina {var} ({descricao})")
    return Path(env)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state-db", type=Path, default=None,
                    help="banco de sessoes do agente (ou env PNAAT_BANCO_SESSOES)")
    ap.add_argument("--pastes", type=Path, default=None,
                    help="pastes de origem (ou env PNAAT_PASTES_ORIGEM)")
    ap.add_argument("--vault", type=Path, default=None,
                    help="vault do projeto (ou env PNAAT_VAULT)")
    ap.add_argument("--repo", default=os.environ.get("PNAAT_REPO", ""),
                    help="host:/caminho do repo (ou env PNAAT_REPO); vazio desliga as checagens de repo")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    args.state_db = _resolver(args.state_db, "PNAAT_BANCO_SESSOES", "--state-db", "banco de sessoes")
    args.pastes = _resolver(args.pastes, "PNAAT_PASTES_ORIGEM", "--pastes", "pastes de origem")
    args.vault = _resolver(args.vault, "PNAAT_VAULT", "--vault", "vault do projeto")

    if not args.repo:
        print("--repo/PNAAT_REPO vazio: checagens que dependem do repo (P, V, H) serao puladas.")
        s = checar_sessoes(args.state_db, "")
        print(f"\nS) repositorios citados em sessoes sem entrada no registro ({len(s)}):")
        for x in s:
            print("   -", x)
        return 1 if s else 0

    caminhos, docs_conteudo = _listar_repo(args.repo)
    print(f"repo: {args.repo} | docs indexados: {len(caminhos)}")

    p = checar_pastes(args.pastes, docs_conteudo)
    s = checar_sessoes(args.state_db, docs_conteudo)
    v = checar_vault(args.vault, docs_conteudo)
    h = checar_higiene(args.repo)

    print(f"\nP) pastes PNAAT sem citacao em docs ({len(p)}):")
    for x in p:
        print("   -", x)
    print(f"\nS) repositorios citados em sessoes sem entrada no registro ({len(s)}):")
    for x in s:
        print("   -", x)
    print(f"\nV) notas PNAAT do vault nao indexadas ({len(v)}):")
    for x in v:
        print("   -", x)
    print(f"\nH) higiene ({len(h)}):")
    for x in h:
        print("   -", x)

    total = len(p) + len(s) + len(v) + len(h)
    print(f"\nRESULTADO: {total} achado(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
