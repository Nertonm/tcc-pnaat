"""Politica unica de midia do repositorio: fonte da verdade das tres guardas.

Antes deste modulo, `commit_gate.sh`, `sanitizar_repo.py` e `doctor.py` tinham regras
proprias e divergentes sobre `dataset/**` e sobre o limite de 300 KB: o sanitizador
reprovava qualquer arquivo rastreado acima do limite (incluindo as imagens de `dataset/`
que o proprio gate permite versionar), o que tornava o gate intransponivel e empurrava
todo commit para `PNAAT_HOOK_BYPASS`.

Regra vigente (declarada em docs/SANITIZACAO.md, secao "Excecao declarada"):
- imagem em `dataset/**` e evidencia de metodo: PERMITIDA, com `dataset/MANIFEST.sha256`
  e abaixo do teto por arquivo;
- qualquer outra midia (video, CAD, foto fora de `dataset/`) continua PROIBIDA;
- arquivo rastreado grande fora da excecao continua sendo achado.
"""
from __future__ import annotations

import re

#: Imagem permitida (excecao declarada de `dataset/**`).
MIDIA_PERMITIDA = re.compile(r"^dataset/.*\.(jpg|jpeg|png|bmp|webp|heic|gif)$", re.I)
#: Teto por arquivo da excecao (bytes): acima disso a imagem deixa de ser evidencia leve.
TETO_PERMITIDO_BYTES = 2 * 1024 * 1024
#: Teto para arquivo rastreado fora da excecao (bytes).
LIMITE_GRANDE_BYTES = 300 * 1024
#: Manifest exigido quando existe imagem versionada em `dataset/**`.
MANIFEST_DATASET = "dataset/MANIFEST.sha256"
#: Extensoes de midia que nunca entram (independente de tamanho).
EXT_MIDIA_PROIBIDA = (
    ".mp4", ".mov", ".avi", ".mkv", ".stl", ".step", ".stp", ".3mf", ".brep", ".fcstd",
)


def eh_imagem_permitida(rel: str) -> bool:
    """True quando o caminho e uma imagem da excecao declarada de `dataset/**`."""
    return bool(MIDIA_PERMITIDA.match(rel))


def motivo_achado(rel: str, tamanho: int, *, midia: bool = False) -> str | None:
    """Motivo pelo qual o arquivo entra nas categorias `midia`/`grande`, ou None se conforme.

    `midia=True` indica que a extensao e de imagem (o chamador classifica pelo nome).
    """
    if midia and not eh_imagem_permitida(rel):
        return "midia fora de dataset/"
    if tamanho > TETO_PERMITIDO_BYTES and eh_imagem_permitida(rel):
        return f"imagem de dataset acima do teto de {TETO_PERMITIDO_BYTES // (1024 * 1024)} MiB"
    if tamanho > LIMITE_GRANDE_BYTES and not eh_imagem_permitida(rel):
        return f"arquivo grande ({tamanho // 1024} KB)"
    return None
