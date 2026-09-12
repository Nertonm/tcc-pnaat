#!/usr/bin/env python3
"""Sanitizador do repo do TCC (fluxo F4): detecta e remove o que nao pode ser publico.

    python3 scripts/sanitizar_repo.py            # --check (padrao): sai 1 se houver achado
    python3 scripts/sanitizar_repo.py --apply    # sanitiza docs/relatorios e limpa notebooks
    python3 scripts/sanitizar_repo.py --selftest # prova que os detectores detectam

Regras (documentadas em docs/SANITIZACAO.md):
  1. midia/binario versionado (foto, video, STL, STEP, ckpt...)
  2. segredo com valor (chave de API, token, chave privada) — heuristica de VALOR, nao de palavra
  3. infraestrutura: IP privado, hostname do homelab, caminho pessoal, usuario de SO
  4. notebook com saida embutida (imagem base64 / outputs preenchidos)
  5. arquivo grande rastreado
  6. camada de ferramenta: caminho de vault/mynotes, state.db, auth.json, /srv/hermes, CT2xx

Codigo (.py/.sh/Makefile) NAO e reescrito automaticamente: o script lista as linhas para correcao
com caminho default via ambiente (mudar string em codigo pode quebrar execucao silenciosamente).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXT_MIDIA = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".heic", ".gif", ".mp4", ".mov", ".avi",
             ".stl", ".step", ".stp", ".3mf", ".fcstd", ".obj", ".glb", ".ckpt", ".h5")
EXT_CODIGO = (".py", ".sh", ".mk", ".toml", ".cfg")
EXT_TEXTO = (".md", ".json", ".yaml", ".yml", ".txt", ".tex", ".csv")
# Varredura por exclusao: tudo que nao for binario/midia entra no scan de texto.
EXT_BINARIO = EXT_MIDIA + (".pyc", ".so", ".o", ".a", ".zip", ".gz", ".tar", ".pdf", ".whl",
                           ".pack", ".idx", ".ico", ".woff", ".woff2", ".ttf", ".mp3", ".wav")
# Excecao de midia versionada: TODAS as imagens dentro de dataset/ (captura propria do rig).
# Video, CAD e qualquer midia fora de dataset/ continuam sendo achado.
# A regra NAO mora mais aqui: politica unica em code-workspace/scripts/politica_midia.py,
# importada tambem por commit_gate.sh e doctor.py (antes as tres divergiam sobre dataset/).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from politica_midia import (  # noqa: E402
    LIMITE_GRANDE_BYTES,
    MIDIA_PERMITIDA,
    TETO_PERMITIDO_BYTES,
    motivo_achado,
)

# Heuristica de VALOR (evita falso positivo em palavras como "token" ou "api_key" em texto):
RE_SEGREDO = re.compile(
    r"(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{30,}|"
    r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.|"
    r"BEGIN [A-Z ]*PRIVATE KEY|"
    r"(?:api[_-]?key|secret|senha|password|passwd|token)\s*[:=]\s*[\"']?[A-Za-z0-9+/=._@-]{16,})",
    re.I,
)
RE_IP_PRIVADO = re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b")
RE_CAMINHO_PESSOAL = re.compile(r"(?<![\w./-])/home/(?!<)[a-z][a-z0-9_-]{2,}|[A-Z]:\\\\?Users\\\\?[A-Za-z0-9._-]+")
RE_HOST = re.compile(r"\b(?:gaspar|abacate|acerola|moranguinho)\b", re.I)
# Usuario de sistema em uso operacional (runuser -u X, find -user X, GF_USER=X).
# Nao casa nome proprio em prosa (ex.: identificacao do entregavel), nem contas genericas
# (root/usuario/user), nem `systemctl --user` (o `-user` precisa nao ser precedido de hifen).
RE_USUARIO_SO = re.compile(
    r"(?:runuser\s+-u\s+|-not\s+-user\s+|(?<![-\w])-user\s+|\bGF_USER=|\bTCC_USER=|--user=)"
    r"(?!(?:root|usuario|user|nobody|daemon|www-data)\b)([A-Za-z_][A-Za-z0-9_-]{2,})")
SUB_USUARIO = (r"(runuser\s+-u\s+|-not\s+-user\s+|\bGF_USER=|\bTCC_USER=)[A-Za-z_][A-Za-z0-9_-]{2,}", r"\1<usuario>")
RE_CAMADA_FERRAMENTA = re.compile(
    r"(?i)(?:mynotes|/vault/|state\.db|auth\.json|/srv/hermes|hermes-pure|hermes|\bCT2\d{2}\b)")
LIMITE_GRANDE = LIMITE_GRANDE_BYTES  # politica unica em politica_midia.py

# O proprio sanitizador contem os padroes como regex: nao se auto-flagra.
IGNORAR_ARQUIVOS = {"code-workspace/scripts/sanitizar_repo.py"}
# Arquivos de politica cujo conteudo o sanitizador NUNCA reescreve: substituir quebra a sintaxe
# ou apaga a propria regra (foi assim que `**/(fora do repo)` entrou no .gitignore).
IGNORAR_ESCRITA = {".gitignore", ".gitattributes", "docs/SANITIZACAO.md"}


def _git(cmd: str) -> str:
    r = subprocess.run(["git"] + cmd.split(), capture_output=True, text=True)
    return r.stdout


def _rastreados() -> list[str]:
    return [x for x in _git("ls-files").splitlines() if x]


def protegidos_por_receipt(raiz: Path = Path("."), arquivos: list[str] | None = None) -> set[str]:
    """Arquivos cujo receipt CONFERE (sha256 do conteudo == hash do sidecar): NAO sanear.

    Sem a conferencia, um .sha256 qualquer servia para 'lavar' o arquivo (achado descontado).
    """
    hashes: dict[str, str] = {}
    for rel in (arquivos if arquivos is not None else _rastreados()):
        if not rel.endswith(".sha256"):
            continue
        try:
            linhas = (raiz / rel).read_text(errors="replace").splitlines()
        except OSError:
            continue
        for linha in linhas:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split(None, 1)
            if len(partes) != 2 or len(partes[0]) != 64:
                continue
            caminho = partes[1].strip()
            if caminho.startswith("/"):
                continue  # caminho absoluto: nao mapeavel para o repo
            if not (raiz / caminho).is_file():
                caminho = str(Path(rel).parent / caminho)
            hashes[caminho] = partes[0]
    prot: set[str] = set()
    for caminho, h in hashes.items():
        p = raiz / caminho
        try:
            if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == h:
                prot.add(caminho)
        except OSError:
            continue
    return prot


def _conteudo_indexado(rel: str, p: Path) -> str | None:
    """Le o conteudo do INDICE (o que sera commitado); cai para a worktree se nao estiver no indice."""
    try:
        r = subprocess.run(["git", "show", ":%s" % rel], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout
    except Exception:
        pass
    try:
        return p.read_text(errors="replace")
    except OSError:
        return None


def detectar(caminhos: list[str], raiz: Path = Path(".")) -> dict[str, list[str]]:
    achados: dict[str, list[str]] = {"midia": [], "segredo": [], "infra": [], "notebook": [],
                                     "grande": [], "ferramenta": []}
    for rel in caminhos:
        if rel in IGNORAR_ARQUIVOS:
            continue
        p = raiz / rel
        if not p.is_file():
            continue
        baixo = rel.lower()
        if baixo.endswith(EXT_MIDIA):
            if not MIDIA_PERMITIDA.match(rel):
                achados["midia"].append(rel)
        try:
            tamanho = p.stat().st_size
        except OSError:
            tamanho = 0
        motivo = motivo_achado(rel, tamanho, midia=baixo.endswith(EXT_MIDIA))
        if motivo:
            if motivo.startswith("imagem de dataset") or "grande" in motivo:
                achados["grande"].append(f"{rel} ({tamanho // 1024} KB)")
            else:
                achados["midia"].append(rel)
        if baixo.endswith(".ipynb"):
            try:
                nb = json.loads(p.read_text(errors="replace"))
            except Exception:
                achados["notebook"].append(f"{rel} (ilegivel)")
                continue
            com_saida = 0
            for celula in nb.get("cells", []):
                for saida in celula.get("outputs", []) or []:
                    texto = json.dumps(saida)[:2000]
                    if "data:image" in texto or saida.get("data"):
                        com_saida += 1
            if com_saida:
                achados["notebook"].append(f"{rel} ({com_saida} saidas com dados)")
            texto = p.read_text(errors="replace")
            if RE_SEGREDO.search(texto):
                achados["segredo"].append(rel)
            if (RE_IP_PRIVADO.search(texto) or RE_CAMINHO_PESSOAL.search(texto)
                    or RE_HOST.search(texto) or RE_USUARIO_SO.search(texto)):
                achados["infra"].append(rel)
            if RE_CAMADA_FERRAMENTA.search(texto):
                achados["ferramenta"].append(rel)
            continue
        if baixo.endswith(EXT_BINARIO):
            continue
        texto = _conteudo_indexado(rel, p)
        if texto is None:
            continue
        if RE_SEGREDO.search(texto):
            achados["segredo"].append(rel)
        if (RE_IP_PRIVADO.search(texto) or RE_CAMINHO_PESSOAL.search(texto)
                or RE_HOST.search(texto) or RE_USUARIO_SO.search(texto)):
            achados["infra"].append(rel)
        if RE_CAMADA_FERRAMENTA.search(texto):
            achados["ferramenta"].append(rel)
    return achados


def aplicar(achados: dict[str, list[str]], raiz: Path = Path("."), arquivos: list[str] | None = None) -> int:
    """Sanitiza texto (docs/relatorios) e limpa notebooks. Codigo fica para correcao manual."""
    mudados = 0
    prot = protegidos_por_receipt(raiz, arquivos)
    for rel in achados.get("ferramenta", []):
        p = raiz / rel
        if rel in prot or rel in IGNORAR_ESCRITA or rel.lower().endswith(EXT_CODIGO) or not p.is_file():
            continue
        texto = p.read_text(errors="replace")
        novo = RE_CAMADA_FERRAMENTA.sub("(fora do repo)", texto)
        if novo != texto:
            p.write_text(novo)
            mudados += 1
    for rel in achados["infra"]:
        p = raiz / rel
        if rel in prot or rel in IGNORAR_ESCRITA or rel.lower().endswith(EXT_CODIGO) or not p.is_file():
            continue  # receipt, arquivo de politica ou codigo: reportado, nao reescrito
        texto = p.read_text(errors="replace")
        novo = RE_IP_PRIVADO.sub("(host interno)", texto)
        novo = RE_CAMINHO_PESSOAL.sub("/home/<usuario>", novo)
        novo = RE_HOST.sub("<host>", novo)
        novo = re.sub(*SUB_USUARIO, string=novo)
        if novo != texto:
            p.write_text(novo)
            mudados += 1
    for rel in achados["notebook"]:
        p = raiz / rel.split(" ")[0]
        if not p.is_file():
            continue
        nb = json.loads(p.read_text(errors="replace"))
        for celula in nb.get("cells", []):
            if celula.get("cell_type") == "code":
                celula["outputs"] = []
                celula["execution_count"] = None
        p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n")
        mudados += 1
    return mudados


def _selftest() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "doc.md").write_text("servidor 10.0.0.1 e /home/usuario/tcc-pnaat no gaspar\n")
        (raiz / "segredo.md").write_text('token = "sk-abcdefghijklmnopqrstuvwx1234"\n')
        (raiz / "foto.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (raiz / "nb.ipynb").write_text(json.dumps(
            {"cells": [{"cell_type": "code", "outputs": [{"data": {"image/png": "AAAA"}}]}]}))
        (raiz / "grande.txt").write_text("x" * (LIMITE_GRANDE + 10))
        achados = detectar(["doc.md", "segredo.md", "foto.png", "nb.ipynb", "grande.txt"], raiz)
        assert "doc.md" in achados["infra"], achados
        assert "segredo.md" in achados["segredo"], achados
        assert "foto.png" in achados["midia"], achados
        assert achados["notebook"], achados
        assert achados["grande"], achados
        # contraprova da excecao: imagem em dataset/ nao e achado; video em dataset/ e
        (raiz / "dataset").mkdir(exist_ok=True)
        (raiz / "dataset" / "frame_0000.jpg").write_bytes(b"\xff\xd8\xff")
        (raiz / "dataset" / "anotada.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (raiz / "dataset" / "clipe.mp4").write_bytes(b"\x00\x00\x00\x18ftyp")
        exc = detectar(["dataset/frame_0000.jpg", "dataset/anotada.png", "dataset/clipe.mp4"], raiz)
        assert "dataset/frame_0000.jpg" not in exc["midia"], "excecao de imagem do dataset nao aplicada"
        assert "dataset/anotada.png" not in exc["midia"], "imagem do dataset deveria ser permitida"
        assert "dataset/clipe.mp4" in exc["midia"], "video deveria continuar sendo achado"
        # contraprova da politica unica: imagem de dataset ACIMA do teto e achado; grande fora
        # de dataset tambem; imagem de dataset abaixo do teto nao e
        (raiz / "dataset" / "gigante.jpg").write_bytes(b"\xff\xd8\xff" + b"0" * (TETO_PERMITIDO_BYTES + 1))
        (raiz / "fora.jpg").write_bytes(b"\xff\xd8\xff")
        exc2 = detectar(["dataset/gigante.jpg", "fora.jpg"], raiz)
        assert any(x.startswith("dataset/gigante.jpg") for x in exc2["grande"]), \
            "imagem de dataset acima do teto deveria ser achado"
        assert "fora.jpg" in exc2["midia"], "imagem fora de dataset deveria continuar sendo achado"
        # contraprova: documento limpo nao gera achado
        (raiz / "limpo.md").write_text("caminho relativo e (host interno) apenas\n")
        assert not detectar(["limpo.md"], raiz)["infra"], "falso positivo em documento limpo"
        # receipt: arquivo com .sha256 sidecar nao pode ser saneado
        (raiz / "protegido.md").write_text("10.0.0.1\n")
        _dig = hashlib.sha256((raiz / "protegido.md").read_bytes()).hexdigest()
        (raiz / "protegido.md.sha256").write_text(f"{_dig}  protegido.md\n")
        (raiz / "falso.md").write_text("10.0.0.1\n")
        (raiz / "falso.md.sha256").write_text("0" * 64 + "  falso.md\n")
        achados_prot = detectar(["protegido.md", "doc.md"], raiz)
        fix = ["doc.md", "segredo.md", "protegido.md", "protegido.md.sha256"]
        assert protegidos_por_receipt(raiz, fix) == {"protegido.md"}, protegidos_por_receipt(raiz, fix)
        assert "falso.md" not in protegidos_por_receipt(
            raiz, ["falso.md", "falso.md.sha256"]), "receipt com hash falso nao pode proteger"
        aplicar(achados_prot, raiz, fix)
        assert "10.0.0.1" in (raiz / "protegido.md").read_text(), "sanitizou arquivo com receipt"

        # camada de ferramenta (vault/agente): detector proprio, com contraprova
        (raiz / "camada.md").write_text("nota em /vault/mynotes e state.db em /srv/hermes-pure\n")
        ach_camada = detectar(["camada.md", "limpo.md"], raiz)
        assert "camada.md" in ach_camada["ferramenta"], ach_camada
        assert "limpo.md" not in ach_camada["ferramenta"], "falso positivo de camada de ferramenta"
        aplicar(ach_camada, raiz, ["camada.md", "limpo.md"])
        assert "/vault/mynotes" not in (raiz / "camada.md").read_text(), "nao neutralizou a camada"
        assert "state.db" not in (raiz / "camada.md").read_text(), "nao neutralizou state.db"

        # apply limpa notebook e substitui infraestrutura em texto
        aplicar(achados, raiz, ["doc.md", "segredo.md", "foto.png", "nb.ipynb", "grande.txt"])
        assert "(host interno)" in (raiz / "doc.md").read_text()
        assert json.loads((raiz / "nb.ipynb").read_text())["cells"][0]["outputs"] == []

        # usuario de sistema em uso operacional: detecta e saneia
        (raiz / "ops.md").write_text("runuser -u fulano -- env FOO=1\nfind . -not -user fulano\n")
        ach_ops = detectar(["ops.md", "limpo.md"], raiz)
        assert "ops.md" in ach_ops["infra"], ach_ops
        aplicar(ach_ops, raiz, ["ops.md", "limpo.md"])
        txt_ops = (raiz / "ops.md").read_text()
        assert "fulano" not in txt_ops and "<usuario>" in txt_ops, txt_ops
        # contraprova: nome proprio em prosa (identificacao do entregavel) NAO e achado
        (raiz / "capa.md").write_text("Integrantes: Fulano de Tal e Beltrano Souza\n")
        assert not detectar(["capa.md"], raiz)["infra"], "falso positivo em nome proprio"
        # contraprova: conta generica e `systemctl --user` NAO sao vazamento
        (raiz / "ops2.md").write_text("find . -user root -print\nsystemctl --user status pnaat\n")
        assert not detectar(["ops2.md"], raiz)["infra"], "falso positivo em conta generica"

        # arquivo de politica (.gitignore) e reportado, nunca reescrito
        (raiz / ".gitignore").write_text("**/(fora do repo)\n10.0.0.1\n")
        ach_gi = detectar([".gitignore"], raiz)
        assert ".gitignore" in ach_gi["infra"], ach_gi
        aplicar(ach_gi, raiz, [".gitignore"])
        assert "10.0.0.1" in (raiz / ".gitignore").read_text(), "reescreveu arquivo de politica"
    print("selftest OK: detecta midia, segredo, infra, camada de ferramenta, saida de notebook e arquivo grande; apply funciona")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="sanitiza texto e notebooks")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--raiz", default=".")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()

    raiz = Path(args.raiz)
    if args.raiz == ".":
        topo = _git("rev-parse --show-toplevel").strip()
        if topo:
            raiz = Path(topo)
    import os as _os
    _os.chdir(raiz)
    caminhos = _rastreados()
    if not caminhos:
        print("ERRO: nenhum arquivo rastreado (esta fora de um repositorio git?).")
        print("A sanitizacao nao pode falhar aberta: exit 2.")
        return 2
    prot = protegidos_por_receipt(raiz)
    achados = detectar(caminhos, raiz)
    cobertos = sorted({rel for rel in (achados["infra"] + achados["segredo"]
                                       + achados["ferramenta"]) if rel in prot})
    if args.apply:
        n = aplicar(achados, raiz)
        print(f"apply: {n} arquivo(s) sanitizado(s)")
        achados = detectar(caminhos, raiz)

    # arquivo coberto por receipt esta fora do escopo de sanitizacao (o produtor regenera)
    total = sum(len(v) for v in achados.values())  # receipt tambem conta: achado nao se desconta
    for chave, rotulo in (("midia", "midia versionada"), ("segredo", "segredo com valor"),
                          ("infra", "infraestrutura (IP/host/caminho)"),
                          ("notebook", "notebook com saida"), ("grande", "arquivo grande"),
                          ("ferramenta", "camada de ferramenta (vault/agente)")):
        print(f"\n{chave} ({len(achados[chave])}) — {rotulo}:")
        for x in achados[chave][:15]:
            print("   -", x)
    if cobertos:
        print(f"\nreceipt ({len(cobertos)}) — NAO sanear: o hash cobre o arquivo, regenerar com o produtor:")
        for x in cobertos[:15]:
            print("   -", x)
    print(f"\nRESULTADO: {total} achado(s) | arquivos rastreados: {len(caminhos)}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
