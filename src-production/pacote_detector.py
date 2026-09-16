"""Contrato do PACOTE do detector: uma definicao, dois lados (produtor e consumidor).

O pacote e o unico elo entre treinar e inferir. Ele existe porque o peso sozinho nao diz o que o
modelo espera: classes tem ordem, ROI e rotacao mudam o pixel, e limiar calibrado num `imgsz` nao vale
noutro. Sem este contrato, treino e inferencia divergem em silencio (medido: 0,17 de F1 macro).

Estrutura obrigatoria do diretorio do pacote:

    <peso>.pt                 peso torch do detector (nunca desserializado aqui)
    preprocessamento.json     contrato de pre-processamento usado no treino (bytes exatos)
    metadados-treino.json     model-meta.json do run que produziu o peso (bytes exatos)
    modelo.json               manifesto do pacote (hashes declarados, classes, limitacoes)
    SHA256SUMS                inventario fechado `sha256  nome`

Regras que este modulo faz valer (fail-closed):

  * o inventario do diretorio e EXATAMENTE o dos checksums: arquivo extra ou faltando e erro;
  * nenhum nome fora do diretorio, nenhum symlink, nenhum duplicado;
  * todo hash declarado em `modelo.json` e conferido contra os bytes reais;
  * `modelo.json` sem campo obrigatorio e erro, nunca default silencioso.

Conferir checksum prova integridade dos bytes que estao ali, NAO autenticidade nem qualidade do
detector. Quem consome continua obrigado a validar os campos semanticos do contrato de
pre-processamento (isso e `preparo_detector.py`).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

NOME_DO_MANIFESTO = "modelo.json"
NOME_DOS_CHECKSUMS = "SHA256SUMS"
NOME_DO_CONTRATO = "preprocessamento.json"
NOME_DOS_METADADOS = "metadados-treino.json"

#: campos de `modelo.json` sem os quais o pacote nao e identificavel
CAMPOS_DO_MANIFESTO = (
    "versao", "estado", "arquivo", "sha256", "classes", "imgsz_treino",
    "imgsz_calibrados", "manifests", "preprocessamento_sha256", "metadados_treino_sha256",
    "limitacoes_declaradas",
)

#: estado do pacote: exportar nao promove. Promover e ato humano, fora daqui.
ESTADO_DE_CANDIDATO = "candidato_nao_promovido"

_RE_SHA256 = re.compile(r"[0-9a-f]{64}")
_RE_PESO = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.pt")


class ErroDePacote(ValueError):
    """O pacote nao e um pacote valido: formato, inventario ou hash declarado inconsistente."""


def sha256_do_arquivo(caminho: Path) -> str:
    with Path(caminho).open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def _sha256_declarado(valor, campo: str) -> str:
    if not isinstance(valor, str) or not _RE_SHA256.fullmatch(valor):
        raise ErroDePacote(f"{campo}: sha256 ausente ou invalido: {valor!r}")
    return valor


def _json(caminho: Path) -> dict:
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except OSError as erro:
        raise ErroDePacote(f"{caminho}: ilegivel: {erro}") from erro
    except json.JSONDecodeError as erro:
        raise ErroDePacote(f"{caminho}: JSON invalido: {erro}") from erro
    if not isinstance(dados, dict):
        raise ErroDePacote(f"{caminho}: o conteudo tem de ser um objeto JSON")
    return dados


def verificar_bundle(diretorio: str | Path) -> dict:
    """Valida o pacote inteiro e devolve o manifesto; qualquer divergencia e erro.

    Espelhado no produtor (`treino/pacote_entrega.py`) porque o consumidor precisa da MESMA
    verificacao: se ela vive so no produtor, o runtime aceita pacote corrompido.
    """
    diretorio = Path(diretorio)
    if not diretorio.is_dir():
        raise ErroDePacote(f"diretorio do pacote nao existe: {diretorio}")
    arquivo_dos_checksums = diretorio / NOME_DOS_CHECKSUMS
    if not arquivo_dos_checksums.is_file():
        raise ErroDePacote(f"pacote sem {NOME_DOS_CHECKSUMS}: integridade nao verificavel")

    entradas: dict[str, str] = {}
    for linha in arquivo_dos_checksums.read_text(encoding="utf-8").splitlines():
        partes = linha.split("  ", 1)
        if len(partes) != 2:
            raise ErroDePacote(f"linha de checksum malformada: {linha!r}")
        valor, nome = partes
        _sha256_declarado(valor, f"checksum de {nome!r}")
        nome_limpo = Path(nome).name
        if nome != nome_limpo or nome in ("", ".", "..", NOME_DOS_CHECKSUMS):
            raise ErroDePacote(f"nome inseguro no checksum: {nome!r}")
        if nome in entradas:
            raise ErroDePacote(f"nome duplicado no checksum: {nome!r}")
        caminho = diretorio / nome
        if caminho.is_symlink() or not caminho.is_file():
            raise ErroDePacote(f"arquivo invalido no pacote: {nome!r}")
        if sha256_do_arquivo(caminho) != valor:
            raise ErroDePacote(f"checksum divergente: {nome!r}")
        entradas[nome] = valor

    inventario = {p.name for p in diretorio.iterdir()}
    if inventario != set(entradas) | {NOME_DOS_CHECKSUMS}:
        extra = sorted(inventario - set(entradas) - {NOME_DOS_CHECKSUMS})
        faltando = sorted(set(entradas) - inventario)
        raise ErroDePacote(f"inventario divergente; extra={extra} faltando={faltando}")

    modelo = _json(diretorio / NOME_DO_MANIFESTO)
    faltando_campos = [c for c in CAMPOS_DO_MANIFESTO if c not in modelo]
    if faltando_campos:
        raise ErroDePacote(f"{NOME_DO_MANIFESTO} sem os campos {faltando_campos}")
    peso = modelo["arquivo"]
    if not isinstance(peso, str) or not _RE_PESO.fullmatch(peso):
        raise ErroDePacote(f"nome do peso invalido no manifesto: {peso!r}")
    esperado = {peso, NOME_DO_MANIFESTO, NOME_DO_CONTRATO, NOME_DOS_METADADOS}
    if set(entradas) != esperado:
        raise ErroDePacote(
            f"pacote incompleto: tem {sorted(entradas)}, esperado {sorted(esperado)}")
    for nome, campo in ((peso, "sha256"),
                        (NOME_DO_CONTRATO, "preprocessamento_sha256"),
                        (NOME_DOS_METADADOS, "metadados_treino_sha256")):
        declarado = _sha256_declarado(modelo[campo], campo)
        if entradas[nome] != declarado:
            raise ErroDePacote(f"{campo} nao casa com o checksum de {nome!r}")
    classes = modelo["classes"]
    if (not isinstance(classes, list) or not classes
            or not all(isinstance(c, str) and c.strip() for c in classes)
            or len(set(classes)) != len(classes)):
        raise ErroDePacote(f"classes invalidas no manifesto: {classes!r}")
    if not isinstance(modelo["limitacoes_declaradas"], list) or not all(
            isinstance(x, str) and x.strip() for x in modelo["limitacoes_declaradas"]):
        raise ErroDePacote("limitacoes_declaradas tem de ser lista de textos nao vazios")
    return modelo


def abrir_pacote(diretorio: str | Path) -> tuple[Path, Path, Path, dict]:
    """Verifica o pacote e devolve `(peso, contrato, metadados, manifesto)`."""
    diretorio = Path(diretorio)
    modelo = verificar_bundle(diretorio)
    return (diretorio / modelo["arquivo"], diretorio / NOME_DO_CONTRATO,
            diretorio / NOME_DOS_METADADOS, modelo)
