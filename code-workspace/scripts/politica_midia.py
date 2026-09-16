"""Politica unica de midia do repositorio: fonte da verdade das guardas.

Antes deste modulo, `commit_gate.sh`, `sanitizar_repo.py` e `doctor.py` tinham regras
proprias e divergentes sobre `dataset/**` e sobre o limite de 300 KB: o sanitizador
reprovava qualquer arquivo rastreado acima do limite (incluindo as imagens de `dataset/`
que o proprio gate permite versionar), o que tornava o gate intransponivel e empurrava
todo commit para o bypass declarado.

Agora a regra mora so aqui. `sanitizar_repo.py` importa `motivo_achado` e as constantes;
`commit_gate.sh` chama este modulo com `--bloqueados` em vez de repetir regex.

Excecoes declaradas (detalhadas na doc de sanitizacao do projeto):

- imagem em `dataset/**` e evidencia de metodo: PERMITIDA, abaixo do teto por arquivo,
  com `dataset/MANIFEST.sha256` presente;
- CAD do entregavel em `cad-produto/**`: PERMITIDO, abaixo do teto por arquivo, com
  `cad-produto/MANIFEST.json` e `cad-produto/SHA256SUMS` presentes. O CAD de terceiro
  continua fora do repositorio;
- qualquer outra midia (video, CAD fora de `cad-produto/`, foto fora de `dataset/`)
  continua PROIBIDA;
- arquivo rastreado grande fora das excecoes continua sendo achado.
"""
from __future__ import annotations

import os
import re
import sys

#: Extensoes de midia reconhecidas. Canonica: os outros guardas importam daqui.
EXT_MIDIA = (
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".heic", ".gif",
    ".mp4", ".mov", ".avi", ".mkv",
    ".stl", ".step", ".stp", ".3mf", ".brep", ".fcstd", ".obj", ".glb",
    ".ckpt", ".h5",
)

#: Imagem permitida (excecao declarada de `dataset/**`).
MIDIA_PERMITIDA = re.compile(r"^dataset/.*\.(jpg|jpeg|png|bmp|webp|heic|gif)$", re.I)
#: CAD do entregavel permitido (excecao declarada de `cad-produto/**`).
CAD_PERMITIDO = re.compile(r"^cad-produto/.*\.(stl|step|stp|3mf|png|pdf|svg)$", re.I)
#: Teto por arquivo da excecao de dataset (bytes).
TETO_PERMITIDO_BYTES = 2 * 1024 * 1024
#: Teto por arquivo da excecao de cad-produto (bytes). Maior peca hoje: 3,82 MB.
TETO_CAD_BYTES = 8 * 1024 * 1024
#: Teto para arquivo rastreado fora das excecoes (bytes).
LIMITE_GRANDE_BYTES = 300 * 1024
#: Manifest exigido quando existe imagem versionada em `dataset/**`.
MANIFEST_DATASET = "dataset/MANIFEST.sha256"
#: Manifest exigido pela excecao de `cad-produto/**`.
MANIFEST_CAD = "cad-produto/SHA256SUMS"


def eh_imagem_permitida(rel: str) -> bool:
    """True quando o caminho e uma imagem da excecao declarada de `dataset/**`."""
    return bool(MIDIA_PERMITIDA.match(rel))


def eh_cad_permitido(rel: str) -> bool:
    """True quando o caminho e CAD do entregavel, dentro de `cad-produto/**`."""
    return bool(CAD_PERMITIDO.match(rel))


def eh_excecao(rel: str) -> bool:
    """True quando o caminho esta em alguma excecao declarada de midia."""
    return eh_imagem_permitida(rel) or eh_cad_permitido(rel)


def midia_bloqueada(rel: str) -> bool:
    """True quando o caminho tem extensao de midia e nao esta em nenhuma excecao.

    Usado pelo gate para decidir o que pode entrar no staging. Nao olha tamanho:
    o teto por arquivo e responsabilidade de `motivo_achado`, que o sanitizador roda.
    """
    if os.path.splitext(rel)[1].lower() not in EXT_MIDIA:
        return False
    return not eh_excecao(rel)


def motivo_achado(rel: str, tamanho: int, *, midia: bool = False) -> str | None:
    """Motivo pelo qual o arquivo entra nas categorias `midia`/`grande`, ou None se conforme.

    `midia=True` indica que a extensao e de midia (o chamador classifica pelo nome).
    """
    if eh_cad_permitido(rel):
        if tamanho > TETO_CAD_BYTES:
            # a palavra "grande" e o que roteia o achado para o balde de tamanho
            # em sanitizar_repo.detectar; sem ela o achado cai como midia
            return (f"arquivo grande: CAD de cad-produto acima do teto de "
                    f"{TETO_CAD_BYTES // (1024 * 1024)} MiB")
        return None
    if midia and not eh_imagem_permitida(rel):
        return "midia fora de dataset/ e de cad-produto/"
    if tamanho > TETO_PERMITIDO_BYTES and eh_imagem_permitida(rel):
        return f"imagem de dataset acima do teto de {TETO_PERMITIDO_BYTES // (1024 * 1024)} MiB"
    if tamanho > LIMITE_GRANDE_BYTES and not eh_imagem_permitida(rel):
        return f"arquivo grande ({tamanho // 1024} KB)"
    return None


def main(argv: list[str] | None = None) -> int:
    """CLI minima para o gate usar a regra unica sem duplicar regex.

    `--bloqueados` le caminhos do stdin, um por linha, e imprime os bloqueados.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--bloqueados" in argv:
        for linha in sys.stdin:
            rel = linha.strip()
            if rel and midia_bloqueada(rel):
                print(rel)
        return 0
    if "--selftest" in argv:
        # contraprovas da regra unica: permitido nao acusa, proibido acusa
        assert not midia_bloqueada("dataset/frame_0000.jpg")
        assert not midia_bloqueada("cad-produto/00-produto/conjunto-portico.stl")
        assert not midia_bloqueada("cad-produto/02-impressao/base-trilho/base-somente.step")
        assert midia_bloqueada("outra-pasta/peca.stl"), "CAD fora de cad-produto deve bloquear"
        assert midia_bloqueada("cad-workspace/references/vendor/x.stl"), "vendor deve bloquear"
        assert midia_bloqueada("dataset/clipe.mp4"), "video deve bloquear"
        assert midia_bloqueada("foto.png"), "imagem fora de dataset deve bloquear"
        assert not midia_bloqueada("cad-produto/README.md"), "texto nao e midia"
        assert motivo_achado("cad-produto/a.stl", 1000, midia=True) is None
        assert motivo_achado("cad-produto/a.stl", TETO_CAD_BYTES + 1, midia=True)
        assert motivo_achado("fora/peca.stl", 1000, midia=True)
        # o teto de 8 MiB vale para as pecas de CAD; texto grande dentro de
        # cad-produto continua caindo na regra geral de 300 KB
        assert motivo_achado("cad-produto/nota.md", LIMITE_GRANDE_BYTES + 1), \
            "texto grande em cad-produto deve continuar sendo achado"
        assert motivo_achado("cad-produto/nota.md", 1000) is None
        print("politica_midia --selftest OK")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
