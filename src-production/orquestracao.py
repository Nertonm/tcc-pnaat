"""Pipeline unica: captura -> decisao por vista -> conformidade por dominio -> registro.

Uma direcao, um caminho. Nao existe segunda pipeline nem atalho de gravacao.

Travas que este modulo faz valer:
  - a decisao por vista passa pelo `Decisor` da D-30 (classificador decide, geometria auxiliar,
    fallback roteia e escala): **nao existe caminho que consulte o classificador por fora dele**;
  - a regiao de recorte (`roi`) e DECLARADA pelo rig: sem ela nao se decide nada, porque medir a
    area errada produz numero com cara de valido (fail-closed);
  - so vistas utilizaveis sao consultadas (alinhadas, dentro da janela, sem duplicata) e a vista de
    check nunca e consultada para classificar (D-23/D-30);
  - o classificador nao pode mentir sobre a origem; a validacao vive no `Decisor`;
  - vista declarada e sem medida continua declarada no evento: a ausencia e registrada, nao apagada;
  - a identidade do rig (equipamento, localizacao) e obrigatoria: evento sem origem nao e rastreavel.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from captura import ItemCapturado, VistaCapturada
from conformidade import (
    DOMINIOS_ESPERADOS,
    ConfiguracaoDoRig,
    ResultadoDaConformidade,
    avaliar_conformidade,
)
from decisao import ClassificadorDeVista, Decisor, MedidorGeometrico
from dominio import Classe, Dominio, Evento, Medida, Vista
from registro import ReferenciaDaEvidencia, Registro

#: regiao de recorte relativa (x1, y1, x2, y2) em fracao do quadro; declarada pelo rig
Roi = tuple[float, float, float, float]
DEFAULT_CONFIG = ConfiguracaoDoRig()
#: o check dimensional devolve (escalonou, motivo). Ele NAO devolve classe (D-23/D-30).
VerificadorDoCheck = Callable[[VistaCapturada], "tuple[bool, str | None]"]


class ErroDeOrquestracao(Exception):
    """A execucao nao pode continuar (origem incoerente, recorte nao declarado, identidade faltando)."""


@dataclass(frozen=True)
class IdentidadeDoRig:
    equipamento: str
    localizacao: str
    esteira: str | None = None

    def __post_init__(self) -> None:
        if not self.equipamento.strip() or not self.localizacao.strip():
            raise ErroDeOrquestracao(
                "evento sem equipamento ou localizacao nao e rastreavel"
            )


@dataclass(frozen=True)
class ResultadoDoEnsaio:
    item_id: str
    status: str
    gravacao: str
    conformidade: ResultadoDaConformidade
    medidas: tuple[Medida, ...]
    check_presente: bool = False

    @property
    def aprovado(self) -> bool:
        return self.status == "ok"


class SemModelo:
    """Classificador declaradamente ausente: devolve None para tudo, o que aciona o fallback da D-30.

    Serve para rodar a cadeia inteira sem modelo e obter `inconclusivo`; a resposta correta e
    fail-closed, no lugar de um numero inventado. Quando o classificador real entrar, ele substitui
    este objeto e nada mais muda na pipeline.
    """

    identificacao = "sem-modelo"

    def prever(self, recorte, dominio: Dominio, vista: Vista) -> Medida | None:
        return None


def recorte_da_vista(imagem, roi: Roi):
    """Le a imagem e recorta a regiao declarada; ROI invalida falha sem clamp."""
    import math

    import cv2

    try:
        if len(roi) != 4 or any(not math.isfinite(float(v)) for v in roi):
            raise ValueError
        x1_rel, y1_rel, x2_rel, y2_rel = (float(v) for v in roi)
    except (TypeError, ValueError):
        raise ErroDeOrquestracao(
            f"roi invalida (esperado x1,y1,x2,y2 finitos): {roi!r}"
        ) from None
    if not (0.0 <= x1_rel < x2_rel <= 1.0 and 0.0 <= y1_rel < y2_rel <= 1.0):
        raise ErroDeOrquestracao(f"roi fora de [0,1] ou degenerada: {roi!r}")

    quadro = cv2.imread(str(imagem))
    if quadro is None:
        raise ErroDeOrquestracao(f"imagem ilegivel: {imagem}")
    altura, largura = quadro.shape[:2]
    x1, y1, x2, y2 = (
        int(x1_rel * largura),
        int(y1_rel * altura),
        int(x2_rel * largura),
        int(y2_rel * altura),
    )
    recorte = quadro[y1:y2, x1:x2]
    if recorte.size == 0:
        raise ErroDeOrquestracao(f"recorte degenerado com roi={roi} em {imagem}")
    return recorte


def _classe_do_evento(conformidade: ResultadoDaConformidade) -> Classe:
    if conformidade.status == "ok":
        return Classe.NORMAL
    if conformidade.status == "inconclusivo":
        return Classe.INCONCLUSIVO
    for dominio in conformidade.por_dominio:
        if dominio.classe is not None:
            return dominio.classe
    return Classe.INCONCLUSIVO


def _referencias_das_vistas(item: ItemCapturado) -> tuple[ReferenciaDaEvidencia, ...]:
    """Hash de cada imagem capturada: sem ele a rastreabilidade para no evento, sem chegar a prova."""
    import hashlib

    return tuple(
        ReferenciaDaEvidencia(
            vista=v.vista,
            caminho=str(v.imagem),
            sha256=hashlib.sha256(v.imagem.read_bytes()).hexdigest(),
        )
        for v in item.vistas
    )


def executar(
    item: ItemCapturado,
    classificador: ClassificadorDeVista,
    registro: Registro,
    identidade: IdentidadeDoRig,
    roi: Roi | None = None,
    config: ConfiguracaoDoRig = DEFAULT_CONFIG,
    medidor: MedidorGeometrico | None = None,
    check: VerificadorDoCheck | None = None,
) -> ResultadoDoEnsaio:
    """Roda a cadeia uma vez para um item. Devolve o resultado e grava o evento."""
    if roi is None:
        raise ErroDeOrquestracao(
            "regiao de recorte (roi) nao declarada: sem ela a decisao mediria a area errada e o "
            "resultado teria cara de valido"
        )
    decisor = Decisor(classificador, medidor)

    medidas: list[Medida] = []
    for vistacap in item.vistas_utilizaveis:
        if vistacap.vista not in config.vistas_decisorias:
            continue  # o check nunca classifica (D-23/D-30)
        recorte = recorte_da_vista(vistacap.imagem, roi)
        # a geometria mede a VISTA: uma vez por vista, reaproveitada nos dois dominios
        medicoes = tuple(medidor.medir(recorte)) if medidor is not None else ()
        for dominio in DOMINIOS_ESPERADOS:
            decisao = decisor.decidir(recorte, dominio, vistacap.vista, medicoes)
            medidas.append(
                Medida(
                    vista=decisao.vista,
                    dominio=decisao.dominio,
                    classe=decisao.classe,
                    confianca=decisao.confianca,
                    evidencias=decisao.evidencias,
                )
            )

    vistacap_do_check = next(
        (v for v in item.vistas_utilizaveis if v.vista is config.vista_check), None
    )
    escalonado, motivo = (False, None)
    check_presente = False
    if check is not None and vistacap_do_check is not None:
        escalonado, motivo = check(vistacap_do_check)
        check_presente = True
    conformidade = avaliar_conformidade(
        medidas,
        config,
        check_escalonado=escalonado,
        check_motivo=motivo,
        check_presente=check_presente,
    )
    evento = Evento(
        item_id=item.item_id,
        capturado_em=item.trigger_em,
        equipamento=identidade.equipamento,
        localizacao=identidade.localizacao,
        esteira=identidade.esteira,
        vistas=tuple(v.vista for v in item.vistas),
        medidas=tuple(medidas),
        status=_classe_do_evento(conformidade),
    )
    gravacao = registro.registrar(
        evento,
        fora_da_janela=tuple(v.vista for v in item.fora_da_janela),
        duplicadas=tuple(v.vista for v in item.duplicadas),
        referencias=_referencias_das_vistas(item),
        motivos_conformidade=tuple(conformidade.motivos),
    )
    return ResultadoDoEnsaio(
        item_id=item.item_id,
        status=conformidade.status,
        gravacao=gravacao,
        conformidade=conformidade,
        medidas=tuple(medidas),
        check_presente=check_presente,
    )


def criar_classificador(
    artefato: str | Path | None = None,
    *,
    fonte: str | None = None,
    limiar: float | None = None,
    embutidor=None,
):
    """Classificador da cadeia: o artefato medido quando ele abre; `SemModelo` quando nao.

    Devolve `(classificador, motivo)`. O motivo descreve o que entrou; vintage/extrator/limiar/sha do
    artefato, ou a razao exata pela qual nao ha modelo. Sem isso a cadeia registra ausencia de modelo
    como se fosse normal, e ninguem sabe se rodou o artefato ou o nada.
    """
    from classificador import ErroDeClassificacao
    from classificador_artefato import (
        ARTEFATO_PADRAO,
        FONTE_PADRAO,
        ClassificadorDoArtefato,
    )

    if artefato is None:
        return (
            SemModelo(),
            f"sem modelo de visao pedido (nenhum artefato: {ARTEFATO_PADRAO})",
        )
    caminho = Path(artefato)
    try:
        classificador = ClassificadorDoArtefato.abrir(
            caminho,
            fonte=fonte or FONTE_PADRAO,
            limiar_de_confianca=limiar,
            embutidor=embutidor,
        )
    except ErroDeClassificacao as erro:
        return SemModelo(), f"artefato {caminho} nao abriu: {erro}"
    return classificador, classificador.procedencia.linha()


def main(argv: list[str] | None = None) -> int:
    """Entry point da cadeia (captura -> decisao -> conformidade -> registro).

    O classificador vem de `criar_classificador`: o artefato medido quando ele abre, `SemModelo`
    quando nao; e o motivo sempre impresso, para ausencia de modelo nao virar silencio."""
    import argparse
    from datetime import UTC, datetime

    from captura import FonteDeDiretorio

    ap = argparse.ArgumentParser(
        description="Ensaio da cadeia (captura -> decisao -> conformidade -> registro)"
    )
    ap.add_argument(
        "--captura", required=True, help="diretorio com <item_id>/<vista>.jpg"
    )
    ap.add_argument("--item", required=True)
    ap.add_argument(
        "--roi",
        required=True,
        nargs=4,
        type=float,
        metavar=("X1", "Y1", "X2", "Y2"),
        help="regiao de recorte em fracao do quadro (declarada pelo rig)",
    )
    ap.add_argument("--db", default="hub.db")
    ap.add_argument(
        "--modelo",
        default=None,
        help="artefato de inferencia (.npz + .json); padrao: dataset/modelo-inferencia.npz",
    )
    ap.add_argument(
        "--fonte",
        default=None,
        help="fonte das estatisticas de padronizacao do artefato (padrao: 'nosso')",
    )
    ap.add_argument(
        "--sem-modelo",
        action="store_true",
        help="forca `SemModelo` (sem visao): usado no ensaio de contrato",
    )
    ap.add_argument("--equipamento", default="rig-bancada")
    ap.add_argument("--localizacao", default="bancada-b")
    ap.add_argument(
        "--janela",
        type=float,
        default=None,
        help="janela temporal declarada do rig, em segundos (sem ela nada e utilizavel)",
    )
    a = ap.parse_args(argv)

    item = FonteDeDiretorio(a.captura, janela_s=a.janela).capturar(
        a.item, datetime.now(UTC)
    )
    registro = Registro.abrir(a.db)
    try:
        classificador, motivo_do_modelo = criar_classificador(
            None if a.sem_modelo else a.modelo, fonte=a.fonte
        )
        print(f"  modelo: {motivo_do_modelo}")
        resultado = executar(
            item,
            classificador,
            registro,
            IdentidadeDoRig(a.equipamento, a.localizacao),
            roi=tuple(a.roi),
        )
        print(f"item {resultado.item_id}: {resultado.status} ({resultado.gravacao})")
        print("  motivos:", ", ".join(resultado.conformidade.motivos) or "(nenhum)")
        print(f"  vistas capturadas: {[v.vista.value for v in item.vistas]}")
        print(
            f"  vistas utilizaveis: {[v.vista.value for v in item.vistas_utilizaveis] or '(nenhuma)'}"
        )
        print(f"  faltantes: {[v.value for v in item.faltantes] or '(nenhuma)'}")
        if item.fora_da_janela:
            print(
                f"  fora da janela: {[v.vista.value for v in item.fora_da_janela]} (janela={a.janela}s)"
            )
        print(
            f"  itens no registro: {registro.contar()} | aprovados: {1 if resultado.aprovado else 0}"
        )
    finally:
        registro.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
