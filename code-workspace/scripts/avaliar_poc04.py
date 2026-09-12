#!/usr/bin/env python3
"""PoC-04: harness determinista da fusao por dominio (D-04, emenda D-23).

Pergunta do protocolo: a fusao PRESERVA o defeito quando as vistas discordam, sem maioria global,
sem aprovacao por evidencia insuficiente e com origem registrada por vista?

Metodo: casos declarados com ground truth conhecido (a decisao esperada e escrita ANTES de rodar),
executados por `fundir()`. O harness FALHA (exit != 0) quando qualquer caso divergir do esperado.

  python3 scripts/avaliar_poc04.py                 # tabela + log json em resultados_poc04/
  python3 scripts/avaliar_poc04.py --saida DIR      # escolhe o diretorio do log
  python3 scripts/avaliar_poc04.py --selftest       # prova que o harness DETECTA uma divergencia

Saida: tabela no terminal + `resultados_poc04/fusao.json` e `fusao.txt`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]          # raiz de trabalho do projeto
sys.path.insert(0, str(RAIZ / "github" / "code-workspace" / "src"))

from pocs.events import DefectClass, Dominio, Qualidade, ViewResult  # noqa: E402
from pocs.poc04_fusao import ConfiguracaoFusao, fundir  # noqa: E402

N, T, M, D, I = (DefectClass.NORMAL, DefectClass.TAMPA_AUSENTE, DefectClass.TAMPA_MAL_ROSQUEADA,
                 DefectClass.DEFORMIDADE, DefectClass.INCONCLUSIVO)

RIG_2L_TOPO = ConfiguracaoFusao(rig_id="rig-2laterais-topo")
RIG_1L = ConfiguracaoFusao(rig_id="bancada-1-vista", vistas_decisoria_por_dominio=1,
                           checagem_obrigatoria=False, dominios_medidos=(Dominio.CORPO,))


def normal_colchete():
    return [
        ViewResult("lateral1", Dominio.TAMPA, N, 0.90),
        ViewResult("lateral2", Dominio.TAMPA, N, 0.90),
        ViewResult("lateral1", Dominio.CORPO, N, 0.90),
        ViewResult("lateral2", Dominio.CORPO, N, 0.90),
        ViewResult("topo", Dominio.DIMENSAO, N, 0.95),
    ]


CASOS: list[dict] = [
    dict(nome="normal completo", cfg=RIG_2L_TOPO, views=normal_colchete(),
         esperado=dict(classe="normal", status_tampa="ok", status_corpo="ok",
                       discordancia=0, escalonado=False, qualidade="completo"),
         pergunta="item com as duas laterais e o check ok aprova?"),
    dict(nome="defeito de tampa nao cancelado", cfg=RIG_2L_TOPO,
         views=[ViewResult("lateral1", Dominio.TAMPA, M, 0.80), *normal_colchete()[1:]],
         esperado=dict(classe="tampa_mal_rosqueada", status_tampa="defeito", status_corpo="ok",
                       discordancia=1, escalonado=False, qualidade="completo"),
         pergunta="1 vista reprova e 2 'aprovam': o defeito sobrevive a discordancia?"),
    dict(nome="defeito de corpo com tampa ok", cfg=RIG_2L_TOPO,
         views=[*normal_colchete()[:2], ViewResult("lateral1", Dominio.CORPO, D, 0.85),
                *normal_colchete()[3:]],
         esperado=dict(classe="deformidade", status_tampa="ok", status_corpo="defeito",
                       discordancia=1, escalonado=False, qualidade="completo"),
         pergunta="defeito de corpo reprova, contamina a tampa e registra a discordancia?"),
    dict(nome="tampa ausente vence mal rosqueada", cfg=RIG_2L_TOPO,
         views=[ViewResult("lateral1", Dominio.TAMPA, M, 0.95),
                ViewResult("lateral2", Dominio.TAMPA, T, 0.60), *normal_colchete()[2:]],
         esperado=dict(classe="tampa_ausente", status_tampa="defeito", status_corpo="ok",
                       discordancia=1, escalonado=False, qualidade="completo"),
         pergunta="a precedencia declarada dentro do dominio e estavel?"),
    dict(nome="check dimensional violado", cfg=RIG_2L_TOPO,
         views=[*normal_colchete()[:4],
                ViewResult("topo", Dominio.DIMENSAO, N, 0.90, escalona=True, motivo="dimensao_violada")],
         esperado=dict(classe="inconclusivo", status_tampa="ok", status_corpo="ok",
                       discordancia=0, escalonado=True, qualidade="completo"),
         pergunta="o check do topo escala o item sem virar classe de defeito?"),
    dict(nome="check dimensional ausente", cfg=RIG_2L_TOPO, views=normal_colchete()[:4],
         esperado=dict(classe="inconclusivo", status_tampa="ok", status_corpo="ok",
                       discordancia=0, escalonado=True, qualidade="parcial_1_vista_faltante"),
         pergunta="sem check nao existe aprovacao?"),
    dict(nome="uma lateral so", cfg=RIG_2L_TOPO,
         views=[ViewResult("lateral1", Dominio.TAMPA, N, 0.90),
                ViewResult("lateral1", Dominio.CORPO, N, 0.90)],
         esperado=dict(classe="inconclusivo", status_tampa="inconclusivo", status_corpo="inconclusivo",
                       discordancia=0, escalonado=True, qualidade="parcial_1_vista_faltante"),
         pergunta="uma vista so aprova o dominio quando o rig exige duas?"),
    dict(nome="evidencia insuficiente", cfg=RIG_2L_TOPO,
         views=[normal_colchete()[0],
                ViewResult("lateral2", Dominio.TAMPA, N, 0.90, qualidade=Qualidade.INSUFICIENTE),
                *normal_colchete()[2:]],
         esperado=dict(classe="inconclusivo", status_tampa="inconclusivo", status_corpo="ok",
                       discordancia=0, escalonado=False, qualidade="evidencia_insuficiente"),
         pergunta="medida de qualidade ruim vira aprovacao silenciosa?"),
    dict(nome="rig de 1 vista declarado", cfg=RIG_1L,
         views=[ViewResult("lateral1", Dominio.CORPO, N, 0.90)],
         esperado=dict(classe="inconclusivo", status_tampa="inconclusivo", status_corpo="ok",
                       discordancia=0, escalonado=False, qualidade="parcial_1_vista_faltante"),
         pergunta="dominio declarado como nao medido bloqueia a aprovacao do item?"),
    dict(nome="rig de 1 vista com suspeita", cfg=RIG_1L,
         views=[ViewResult("lateral1", Dominio.CORPO, I, 0.80, motivo="suspeita_de_anomalia")],
         esperado=dict(classe="inconclusivo", status_tampa="inconclusivo", status_corpo="inconclusivo",
                       discordancia=0, escalonado=False, qualidade="evidencia_insuficiente"),
         pergunta="suspeita do detector de anomalia vira classe de defeito?"),
]


def executar(casos=None):
    casos = CASOS if casos is None else casos
    linhas = []
    for caso in casos:
        f = fundir(caso["views"], caso["cfg"])
        obtido = dict(classe=f.classe.value, status_tampa=f.status_tampa, status_corpo=f.status_corpo,
                      discordancia=int(f.discordancia_lateral), escalonado=f.escalonado,
                      qualidade=f.qualidade_registro)
        esperado = caso["esperado"]
        divergencias = [k for k, v in esperado.items() if obtido[k] != v]
        linhas.append(dict(
            nome=caso["nome"], pergunta=caso["pergunta"], rig_id=caso["cfg"].rig_id,
            esperado=esperado, obtido=obtido, ok=not divergencias, divergencias=divergencias,
            motivos=list(f.motivos), origens=[list(o) for o in f.origens],
            confidence=f.confidence, n_vistas=len(caso["views"]),
        ))
    return linhas


def main() -> int:
    ap = argparse.ArgumentParser(description="Harness determinista do PoC-04 (fusao por dominio).")
    ap.add_argument("--saida", type=Path, default=RAIZ / "resultados_poc04")
    ap.add_argument("--selftest", action="store_true",
                    help="injeta um caso com esperado ERRADO e exige que o harness detecte")
    args = ap.parse_args()

    casos = list(CASOS)
    if args.selftest:
        errado = dict(casos[0])
        errado["nome"] = "SELFTEST (esperado propositalmente errado)"
        errado["esperado"] = dict(casos[0]["esperado"], classe="tampa_ausente")
        casos = [errado]

    linhas = executar(casos)

    print(f"PoC-04 - fusao por dominio | casos: {len(linhas)} | "
          f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"{'caso':<34} {'esperado':<52} {'obtido':<52} ok")
    for l in linhas:
        exp = f"{l['esperado']['classe']}/{l['esperado']['status_tampa']}/{l['esperado']['status_corpo']}"
        obt = f"{l['obtido']['classe']}/{l['obtido']['status_tampa']}/{l['obtido']['status_corpo']}"
        print(f"{l['nome']:<34} {exp:<52} {obt:<52} {'SIM' if l['ok'] else 'NAO ' + ','.join(l['divergencias'])}")

    falhas = [l for l in linhas if not l["ok"]]
    if not args.selftest:
        classes = {l["esperado"]["classe"] for l in linhas}
        if not ({"normal"} <= classes and classes & {"tampa_ausente", "tampa_mal_rosqueada",
                                                     "deformidade", "inconclusivo"}):
            print("META-CHECK FALHOU: suite sem caso de aprovacao e de nao-aprovacao - nao prova nada")
            return 2

    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "fusao.json").write_text(json.dumps(linhas, indent=1, ensure_ascii=False))
    (args.saida / "fusao.txt").write_text("\n".join(
        f"{l['nome']}: {'ok' if l['ok'] else 'FALHA ' + ','.join(l['divergencias'])} "
        f"classe={l['obtido']['classe']} tampa={l['obtido']['status_tampa']} "
        f"corpo={l['obtido']['status_corpo']} motivos={','.join(l['motivos'])}"
        for l in linhas) + "\n")
    print(f"\nlog: {args.saida / 'fusao.json'}")
    if falhas:
        print(f"RESULTADO: {len(falhas)}/{len(linhas)} caso(s) divergente(s) do esperado")
        return 1
    print(f"RESULTADO: {len(linhas)}/{len(linhas)} casos conforme o esperado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
