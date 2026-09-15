"""Mapa camera -> vista do rig, DECLARADO (nao inferido).

O rig do PNAAT grava uma foto por CAMERA (os papeis sao `csi`, `usb` e `espcam`; o nome real de cada
camera e dado da instalacao e fica no `mapeamento-rig.json`), e o registro do hub
fala por VISTA (`topo`, `lateral1`, `lateral2`). Nada nos dois lados liga os dois nomes: o `roi.json`
lista cameras, o `dominio.py` lista vistas, e nenhum arquivo diz qual camera e qual vista. Sem esta
declaracao, qualquer associacao serie->item e adivinhacao de quem le — e como o topo NUNCA decide
(D-23/D-30), trocar a ordem muda a decisao do item.

Regras que este modulo faz valer:

  * o mapa e DECLARADO na instalacao (nao deduzido do nome do arquivo nem da ordem da captura);
  * cada vista do rig aparece UMA vez: vista repetida e erro, nao "a primeira vale";
  * camera desconhecida no manifesto e ERRO declarado, nunca ignorada em silencio;
  * serie incompleta e declarada como incompleta (a vista que falta e nomeada).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dominio import Vista

#: nome do arquivo de mapa da INSTALACAO (fica fora do controle de versao: os nomes das cameras sao
#: dado do rig, e o repositorio nao carrega nome de host). Criar ao lado deste modulo com
#: {"<camera-no-manifesto>": "<vista>", ...}
ARQUIVO_DO_MAPA = Path(__file__).resolve().parent / "mapeamento-rig.json"


class ErroDeMapeamento(Exception):
    """O manifesto nao casa com o mapa declarado: sem isso nao ha associacao honesta."""


@dataclass(frozen=True)
class FotoDaSerie:
    """Uma foto do conjunto, ja associada a uma vista."""

    camera: str
    vista: Vista
    arquivo: str
    bytes: int | None = None


def validar_mapa(mapa: Mapping[str, Vista]) -> dict[str, Vista]:
    """Confere o mapa: vista conhecida, sem repeticao, sem camera vazia."""
    limpo: dict[str, Vista] = {}
    for camera, vista in mapa.items():
        nome = str(camera).strip()
        if not nome:
            raise ErroDeMapeamento("camera vazia no mapa")
        if not isinstance(vista, Vista):
            try:
                vista = Vista(str(vista))
            except ValueError as exc:
                raise ErroDeMapeamento(
                    f"vista desconhecida para a camera {nome!r}: {vista!r} "
                    f"(validas: {[v.value for v in Vista]})") from exc
        limpo[nome] = vista

    vistas = list(limpo.values())
    if len(set(vistas)) != len(vistas):
        repetidas = sorted({v.value for v in vistas if vistas.count(v) > 1})
        raise ErroDeMapeamento(f"vista repetida no mapa ({repetidas}): cada vista tem UMA camera")
    if not limpo:
        raise ErroDeMapeamento("mapa vazio: sem ele nao ha associacao honesta entre camera e vista")
    return limpo


def ler_mapa(texto: str | None, *, arquivo: str | Path | None = None,
             mapa: Mapping[str, Vista] | None = None) -> dict[str, Vista]:
    """Resolve o mapa na ordem: dict > texto `camera=vista,...` > arquivo da instalacao > ERRO.

    O repositorio NAO tem mapa default de proposito: os nomes das cameras sao dado do rig (e o repo
    nao carrega nome de host). Sem declaracao, a ingestao PARA — em vez de adivinhar qual foto e a
    lateral.
    """
    if mapa is not None:
        return validar_mapa(dict(mapa))

    if texto:
        resolvido: dict[str, Vista] = {}
        for par in texto.split(","):
            par = par.strip()
            if not par:
                continue
            if "=" not in par:
                raise ErroDeMapeamento(f"par sem '=' no mapa: {par!r} (use camera=vista)")
            camera, _, nome_da_vista = par.partition("=")
            try:
                resolvido[camera.strip()] = Vista(nome_da_vista.strip())
            except ValueError as exc:
                raise ErroDeMapeamento(
                    f"vista desconhecida no mapa: {nome_da_vista.strip()!r} "
                    f"(validas: {[v.value for v in Vista]})") from exc
        return validar_mapa(resolvido)

    caminho = Path(arquivo) if arquivo else ARQUIVO_DO_MAPA
    if caminho.is_file():
        try:
            declarado = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ErroDeMapeamento(f"mapa ilegivel em {caminho}: {exc}") from exc
        if not isinstance(declarado, dict):
            raise ErroDeMapeamento(f"mapa de {caminho} tem de ser objeto camera->vista")
        return validar_mapa({str(c): Vista(str(v)) for c, v in declarado.items()})

    raise ErroDeMapeamento(
        f"mapa camera->vista nao declarado: informe --mapa camera=vista,... ou crie {caminho} "
        "(o repositorio nao carrega os nomes das cameras da instalacao)")


def fotos_do_manifesto(manifesto: Mapping[str, object],
                       mapa: Mapping[str, Vista]) -> tuple[FotoDaSerie, ...]:
    """Associa as fotos do manifesto a vistas, na ordem das vistas do rig.

    Erros declarados (nunca silencio): camera fora do mapa, foto repetida para a mesma vista,
    manifesto sem a lista de fontes.
    """
    fontes = manifesto.get("fontes")
    if not isinstance(fontes, list) or not fontes:
        raise ErroDeMapeamento("manifesto sem 'fontes': nao ha foto para associar")

    fotos: list[FotoDaSerie] = []
    vistas_vistas: set[Vista] = set()
    for fonte in fontes:
        if not isinstance(fonte, dict):
            raise ErroDeMapeamento(f"fonte do manifesto nao e objeto: {fonte!r}")
        camera = str(fonte.get("camera") or "").strip()
        arquivo = str(fonte.get("nome") or "").strip()
        if not camera or not arquivo:
            raise ErroDeMapeamento(f"fonte sem camera/nome: {fonte!r}")
        if camera not in mapa:
            raise ErroDeMapeamento(
                f"camera {camera!r} nao esta no mapa declarado "
                f"({sorted(mapa)}): declarar o mapa antes de ingerir")
        vista = mapa[camera]
        if vista in vistas_vistas:
            raise ErroDeMapeamento(
                f"duas cameras mapeadas para a vista {vista.value!r}: a vista decide uma vez")
        vistas_vistas.add(vista)
        tamanho = fonte.get("bytes")
        fotos.append(FotoDaSerie(camera=camera, vista=vista, arquivo=arquivo,
                                 bytes=int(tamanho) if isinstance(tamanho, int) else None))

    # ordem canonica das vistas (topo primeiro, como o rig captura) — a associacao e a mesma
    ordem = {vista: indice for indice, vista in enumerate((Vista.TOPO, Vista.LATERAL1, Vista.LATERAL2))}
    return tuple(sorted(fotos, key=lambda f: ordem.get(f.vista, 99)))


def faltantes(fotos: tuple[FotoDaSerie, ...]) -> tuple[str, ...]:
    """Vistas do rig que a serie nao trouxe (declaradas, para o item nao virar 'completo')."""
    presentes = {f.vista for f in fotos}
    return tuple(v.value for v in (Vista.TOPO, Vista.LATERAL1, Vista.LATERAL2) if v not in presentes)
