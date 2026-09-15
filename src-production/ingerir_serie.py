"""Ingere um conjunto de captura do rig como item do registro (o elo que faltava).

Hoje a serie vive em disco (`series-3-cameras/<carimbo>/`) e o registro nunca a ve: nenhuma rota cria
item, o id nao tem gerador no caminho e o mapa camera->vista nao existe. Esta ferramenta fecha isso
usando a cadeia QUE JA EXISTE (`orquestracao.executar`), sem segundo caminho de decisao.

O que ela faz, em ordem:

  1. le o manifesto da serie e associa cada camera a uma vista (mapa DECLARADO da instalacao —
     `--mapa`, `--mapa-arquivo` ou `mapeamento-rig.json` ao lado do modulo; sem ele a ingestao PARA);
  2. copia as fotos para a RAIZ DE EVIDENCIA do hub e calcula o sha256 de cada uma — a evidencia passa
     a viajar com o registro (a serie do rig pode ser apagada sem perder a prova), e a rota de
     evidencia continua servindo so o que esta dentro da raiz;
  3. reserva o `item_id` na sequencia do lote DENTRO da transacao que grava o item;
  4. roda a cadeia (`executar`) com o classificador do artefato, declarando janela e alinhamento;
  5. vincula o evento de gatilho ao item, quando o id do evento for informado.

Fail-closed em tudo: serie sem vista, camera fora do mapa, janela nao declarada e alinhamento nao
verificado NAO viram item "ok" — a ausencia e declarada pelo proprio registro.

Uso:
  python3 ingerir_serie.py --serie <dir-da-serie> --lote L1 --db hub.db \
      --roi 0.0 0.0 1.0 1.0 --janela-ms 800 --alinhamento declarado \
      [--evidencias <dir>] [--mapa camera=vista,... | --mapa-arquivo <json>] [--gatilho-id N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import captura
from captura import Alinhamento, FonteDeDiretorio, ItemCapturado, VistaCapturada
from dominio import Vista
from identidade import SequenciaDeItens
from classificador_artefato import ARTEFATO_PADRAO
from orquestracao import IdentidadeDoRig, criar_classificador, executar
from registro import Registro

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from mapeamento_rig import (ErroDeMapeamento, faltantes, fotos_do_manifesto,  # noqa: E402
                            ler_mapa)


def _sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def _manifesto(serie: Path) -> dict:
    arquivo = serie / "manifest.json"
    if not arquivo.is_file():
        raise ErroDeMapeamento(
            f"serie sem manifest.json: {serie} — sem ele nao se sabe qual camera tirou qual foto "
            f"(e serie parcial precisa ser declarada como parcial, nao ignorada)")
    return json.loads(arquivo.read_text(encoding="utf-8"))


def _copia_para_evidencia(serie: Path, destino: Path, nome: str) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    alvo = destino / nome
    origem = serie / nome
    if not origem.is_file():
        raise ErroDeMapeamento(f"foto declarada no manifesto nao esta no disco: {origem}")
    shutil.copy2(origem, alvo)
    return alvo


def ingerir(serie: Path, *, lote: str, db: Path, roi: tuple[float, float, float, float],
            janela_ms: int | None, alinhamento_declarado: bool, evidencias: Path | None = None,
            mapa_texto: str | None = None, mapa=None, mapa_arquivo=None,
            artefato: str | None = None, equipamento: str = "rig-bancada",
            localizacao: str = "bancada-b", gatilho_id: int | None = None,
            capturado_em: datetime | None = None, classificador=None) -> dict:
    """Ingere a serie e devolve o que ficou no registro (nao o que se pretendia gravar)."""
    serie = Path(serie).resolve()
    mapa = ler_mapa(mapa_texto, arquivo=mapa_arquivo, mapa=mapa)
    manifesto = _manifesto(serie)
    fotos = fotos_do_manifesto(manifesto, mapa)
    sem_vista = faltantes(fotos)

    raiz_evidencias = Path(evidencias).resolve() if evidencias else Path(db).resolve().parent
    pasta_da_serie = raiz_evidencias / "series" / serie.name

    quando = capturado_em or datetime.now(UTC)
    vistas: list[VistaCapturada] = []
    provas: dict[str, dict] = {}
    for foto in fotos:
        alvo = _copia_para_evidencia(serie, pasta_da_serie, foto.arquivo)
        vistas.append(VistaCapturada(
            vista=foto.vista,
            imagem=alvo,
            capturado_em=quando,
            alinhamento=(Alinhamento.OK if alinhamento_declarado else Alinhamento.NAO_VERIFICADO),
            no_janela=(True if janela_ms else None),
            motivo_da_janela=("janela declarada na ingestao" if janela_ms
                              else "janela nao declarada: a serie nao sustenta associacao temporal"),
        ))
        provas[foto.camera] = {"vista": foto.vista.value, "caminho": str(alvo),
                               "sha256": _sha256(alvo), "bytes": alvo.stat().st_size}

    registro = Registro.abrir(db)
    try:
        if classificador is None:
            classificador, motivo_do_modelo = criar_classificador(artefato)
        else:
            # injetado (teste/canario): a cadeia e a mesma, so nao passa pelo artefato
            motivo_do_modelo = getattr(classificador, "identificacao", "classificador injetado")
        with SequenciaDeItens(registro._cx).reservar(lote) as item_id:
            item = ItemCapturado(item_id=item_id, trigger_em=quando, vistas=tuple(vistas))
            resultado = executar(item, classificador, registro,
                                 IdentidadeDoRig(equipamento, localizacao), roi=roi)
    finally:
        registro.fechar()

    if gatilho_id is not None:
        registro = Registro.abrir(db)
        try:
            registro.vincular_gatilho_a_item(gatilho_id, resultado.item_id)
        finally:
            registro.fechar()

    return {
        "serie": serie.name,
        "item_id": resultado.item_id,
        "status": str(getattr(resultado, "status", "")),
        "gravacao": str(getattr(resultado, "gravacao", "")),
        "motivos": list(getattr(resultado.conformidade, "motivos", ()) or ()) if hasattr(resultado, "conformidade") else [],
        "vistas": [v.vista.value for v in item.vistas],
        "vistas_utilizaveis": [v.vista.value for v in item.vistas_utilizaveis],
        "faltantes": list(sem_vista),
        "janela_ms": janela_ms,
        "alinhamento": "declarado" if alinhamento_declarado else "nao_verificado",
        "modelo": motivo_do_modelo,
        "evidencias": provas,
        "evidencias_raiz": str(raiz_evidencias),
        "gatilho_id": gatilho_id,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ingere uma serie do rig como item do registro")
    ap.add_argument("--serie", required=True, help="diretorio da serie (com manifest.json)")
    ap.add_argument("--lote", required=True, help="lote do item (ex.: L1)")
    ap.add_argument("--db", default="hub.db")
    ap.add_argument("--roi", required=True, nargs=4, type=float, metavar=("X1", "Y1", "X2", "Y2"))
    ap.add_argument("--janela-ms", type=int, default=None,
                    help="janela temporal declarada da passagem; sem ela a serie nao sustenta associacao")
    ap.add_argument("--alinhamento", choices=("declarado", "nao_verificado"), default="nao_verificado",
                    help="'declarado' so quando o rig verificou o alinhamento (o padrao e nao verificado)")
    ap.add_argument("--evidencias", default=None, help="raiz de evidencia (padrao: pasta do banco)")
    ap.add_argument("--mapa", default=None, help="camera=vista,camera=vista")
    ap.add_argument("--mapa-arquivo", default=None,
                    help="JSON camera->vista da instalacao (padrao: mapeamento-rig.json ao lado do modulo)")
    ap.add_argument("--modelo", default=None,
                    help="artefato de inferencia (.npz + .json); padrao: o artefato medido do repo")
    ap.add_argument("--equipamento", default="rig-bancada")
    ap.add_argument("--localizacao", default="bancada-b")
    ap.add_argument("--gatilho-id", type=int, default=None, help="id do evento de gatilho a vincular")
    a = ap.parse_args(argv)

    try:
        # sem --modelo, usa o artefato medido do repo quando ele existe (e declara o motivo quando nao):
        # ingerir sem decidir e util, mas nao pode ser o padrao silencioso
        artefato = a.modelo or (str(ARTEFATO_PADRAO) if ARTEFATO_PADRAO.is_file() else None)

        resultado = ingerir(Path(a.serie), lote=a.lote, db=Path(a.db), roi=tuple(a.roi),
                            janela_ms=a.janela_ms, alinhamento_declarado=(a.alinhamento == "declarado"),
                            evidencias=Path(a.evidencias) if a.evidencias else None,
                            mapa_texto=a.mapa, mapa_arquivo=a.mapa_arquivo, artefato=artefato,
                            equipamento=a.equipamento,
                            localizacao=a.localizacao, gatilho_id=a.gatilho_id)
    except ErroDeMapeamento as erro:
        print(f"serie recusada: {erro}", file=sys.stderr)
        return 2

    print(json.dumps(resultado, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
