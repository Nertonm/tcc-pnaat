"""Pipeline unica: captura -> decisao por vista -> conformidade por dominio -> registro.

Uma direcao, um caminho. Nao existe segunda pipeline, nem caminho alternativo de gravacao.

Travas que este modulo faz valer:
  - o decisor so e consultado para vista que passou no alinhamento (`vistas_utilizaveis`): evidencia
    descartada nao vira medicao;
  - o decisor nao pode mentir sobre a origem: se devolver uma `Medida` de outra vista ou dominio, a
    execucao para (`ErroDeOrquestracao`);
  - vista declarada e sem medida continua declarada no evento — a ausencia e registrada, nao apagada;
  - a identidade do rig (equipamento, localizacao) e obrigatoria: evento sem origem nao e rastreavel.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from captura import ItemCapturado, VistaCapturada
from dominio import Classe, Dominio, Evento, Medida
from conformidade import DOMINIOS_ESPERADOS, ConfiguracaoDoRig, ResultadoDaConformidade, avaliar_conformidade
from registro import Registro

Decisor = Callable[[VistaCapturada, Dominio], Medida | None]
#: o check dimensional devolve (escalonou, motivo). Ele NAO devolve classe (D-23/D-30).
VerificadorDoCheck = Callable[[VistaCapturada], "tuple[bool, str | None]"]


class ErroDeOrquestracao(Exception):
    """A execucao nao pode continuar (origem incoerente ou identidade faltando)."""


@dataclass(frozen=True)
class IdentidadeDoRig:
    equipamento: str
    localizacao: str
    esteira: str | None = None

    def __post_init__(self) -> None:
        if not self.equipamento.strip() or not self.localizacao.strip():
            raise ErroDeOrquestracao("evento sem equipamento ou localizacao nao e rastreavel")


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


def _classe_do_evento(conformidade: ResultadoDaConformidade) -> Classe:
    if conformidade.status == "ok":
        return Classe.NORMAL
    if conformidade.status == "inconclusivo":
        return Classe.INCONCLUSIVO
    for dominio in conformidade.por_dominio:
        if dominio.classe is not None:
            return dominio.classe
    return Classe.INCONCLUSIVO


def executar(item: ItemCapturado, decidir: Decisor, registro: Registro,
             identidade: IdentidadeDoRig,
             config: ConfiguracaoDoRig = ConfiguracaoDoRig(),
             check: VerificadorDoCheck | None = None) -> ResultadoDoEnsaio:
    """Roda a cadeia uma vez para um item. Devolve o resultado e grava o evento.

    So as vistas DECISORIAS sao consultadas para classificar (D-23/D-30): o topo nunca emite classe.
    O check dimensional entra por `check`, e a ausencia dele e declarada, nao presumida."""
    medidas: list[Medida] = []
    for vistacap in item.vistas_utilizaveis:
        if vistacap.vista not in config.vistas_decisorias:
            continue
        for dominio in DOMINIOS_ESPERADOS:
            medida = decidir(vistacap, dominio)
            if medida is None:
                continue
            if medida.vista is not vistacap.vista or medida.dominio is not dominio:
                raise ErroDeOrquestracao(
                    f"decisor devolveu medida de {medida.vista.value}/{medida.dominio.value} "
                    f"quando foi consultado para {vistacap.vista.value}/{dominio.value}")

            medidas.append(medida)

    vistacap_do_check = next((v for v in item.vistas_utilizaveis if v.vista is config.vista_check), None)
    escalonado, motivo = (False, None)
    check_presente = False
    if check is not None and vistacap_do_check is not None:
        escalonado, motivo = check(vistacap_do_check)
        check_presente = True
    conformidade = avaliar_conformidade(medidas, config, check_escalonado=escalonado, check_motivo=motivo,
                   check_presente=check_presente)
    evento = Evento(item_id=item.item_id, capturado_em=item.trigger_em,
                    equipamento=identidade.equipamento, localizacao=identidade.localizacao,
                    esteira=identidade.esteira,
                    vistas=tuple(v.vista for v in item.vistas),
                    medidas=tuple(medidas), status=_classe_do_evento(conformidade))
    gravacao = registro.registrar(evento)
    return ResultadoDoEnsaio(item_id=item.item_id, status=conformidade.status, gravacao=gravacao,
                             conformidade=conformidade, medidas=tuple(medidas),
                             check_presente=check_presente)


def main(argv: list[str] | None = None) -> int:
    """Entry point da cadeia. Sem modelo de visao ainda: o decisor de bancada devolve `None` para
    tudo, e o ensaio termina `inconclusivo` — que e a resposta correta e fail-closed, nao um numero
    inventado. Quando o classificador entrar, ele substitui o `decidir` e nada mais muda."""
    import argparse

    ap = argparse.ArgumentParser(description="Ensaio da cadeia (captura -> decisao -> conformidade -> registro)")
    ap.add_argument("--captura", required=True, help="diretorio com <item_id>/<vista>.jpg")
    ap.add_argument("--item", required=True)
    ap.add_argument("--db", default="hub.db")
    ap.add_argument("--equipamento", default="rig-bancada")
    ap.add_argument("--localizacao", default="bancada-b")
    a = ap.parse_args(argv)

    from datetime import datetime, timezone

    from captura import FonteDeDiretorio

    fonte = FonteDeDiretorio(a.captura)
    item = fonte.capturar(a.item, datetime.now(timezone.utc))
    registro = Registro.abrir(a.db)
    try:
        resultado = executar(item, decidir=lambda vista, dominio: None, registro=registro,
                             identidade=IdentidadeDoRig(a.equipamento, a.localizacao))
        print(f"item {resultado.item_id}: {resultado.status} ({resultado.gravacao})")
        print("  motivos:", ", ".join(resultado.conformidade.motivos) or "(nenhum)")
        print(f"  vistas capturadas: {[v.vista.value for v in item.vistas]}")
        print(f"  vistas utilizaveis: {[v.vista.value for v in item.vistas_utilizaveis] or '(nenhuma)'}")
        print(f"  faltantes: {[v.value for v in item.faltantes] or '(nenhuma)'}")
        print(f"  itens no registro: {registro.contar()} | aprovados: "
              f"{registro.contar() if resultado.aprovado else 0}")
    finally:
        registro.fechar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
