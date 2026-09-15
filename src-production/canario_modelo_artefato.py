"""Canario do artefato: recomputa os numeros que o json DECLARA, com o conjunto do produtor.

Nao e teste unitario — e canario de bancada, e existe por um motivo especifico: o classificador
desta cadeia (`classificador_artefato.py`) e um PORT da receita medida. Port que divergiu da receita
ainda "funciona" (devolve classe e confianca) e mesmo assim mente. Este canario fecha isso: ele usa
o mesmo `carrega()` do produtor (`dataset/TRABALHO/compara_extratores.py`) para montar exatamente o
conjunto declarado — dominio `nosso`, split val+test — e recomputa, com o classificador da cadeia, as
mesmas metricas do json:

    recall por classe (argmax, sem abstencao)   +   taxa de inconclusivo no limiar declarado

Se o port divergiu, os numeros nao batem e o canario sai != 0. Sem isso, "portei a receita" e so
afirmacao.

Uso (na bancada, com o venv do repo):
    .venv/bin/python src-production/canario_modelo_artefato.py [--json /tmp/canario.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src-production"))
#: reuso deliberado do produtor: o conjunto do canario tem de ser o MESMO que o json declara. Se
#: cada lado montasse a sua lista, a comparacao nao provaria nada sobre o port.
sys.path.insert(0, str(RAIZ / "dataset" / "TRABALHO"))

from classificador_artefato import ARTEFATO_PADRAO, ClassificadorDoArtefato  # noqa: E402
from dominio import Dominio, Vista  # noqa: E402

FONTE = "nosso"
VISTA = Vista.LATERAL1
DOMINIO = Dominio.TAMPA


def conjunto_declarado() -> list[dict]:
    """Itens do dominio `nosso` em val+test, pela mesma funcao do produtor do artefato."""
    from compara_extratores import carrega

    return [item for item in carrega()
            if item["dominio"] == FONTE and item["split"] in {"val", "test"}]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Canario: o port reproduz os numeros declarados?")
    ap.add_argument("--artefato", default=str(ARTEFATO_PADRAO))
    ap.add_argument("--json", default="/tmp/canario-artefato.json", help="onde gravar o recibo")
    ap.add_argument("--cadeia", action="store_true",
                    help="roda tambem o item pela cadeia (executar) e le o rastro de volta do registro")
    a = ap.parse_args(argv)

    cls = ClassificadorDoArtefato.abrir(a.artefato, fonte=FONTE)
    itens = conjunto_declarado()
    declarado = cls.procedencia.avaliacao
    print("procedencia:", cls.procedencia.linha(), flush=True)
    print(f"conjunto: dominio={FONTE} split=val+test n={len(itens)} "
          f"(declarado no json: n={declarado.get('n')})", flush=True)

    verdadeiros, argmax, medidas = [], [], []
    for i, item in enumerate(itens, 1):
        recorte = cv2.imread(item["crop"], cv2.IMREAD_COLOR)
        if recorte is None:
            raise SystemExit(f"crop ilegivel: {item['crop']}")
        probabilidades, medida = cls.avaliar(recorte, DOMINIO, VISTA)
        verdadeiros.append(item["classe"])
        medidas.append(medida)
        argmax.append(cls.procedencia.classes[int(np.argmax(probabilidades))])
        if i % 10 == 0:
            print(f"  {i}/{len(itens)}", flush=True)

    verdadeiros = np.array(verdadeiros)
    argmax = np.array(argmax)
    inconclusivos = np.array([m.classe.value == "inconclusivo" for m in medidas])

    medido: dict[str, object] = {"n": len(itens)}
    divergencias: list[str] = []
    for classe, esperado in (declarado.get("por_classe") or {}).items():
        mascara = verdadeiros == classe
        recall = float((argmax[mascara] == classe).mean()) if mascara.sum() else None
        fn = int((argmax[mascara] != classe).sum())
        fp = int(((argmax == classe) & ~mascara).sum())
        medido[classe] = {"n": int(mascara.sum()), "recall": recall, "fn": fn, "fp": fp}
        if esperado.get("n") != int(mascara.sum()):
            divergencias.append(f"{classe}: n medido {int(mascara.sum())} != declarado {esperado.get('n')}")
        if esperado.get("recall") is not None and recall is not None and abs(recall - esperado["recall"]) > 1e-9:
            divergencias.append(f"{classe}: recall medido {recall:.6f} != declarado {esperado['recall']:.6f}")
        for chave, valor in (("fn", fn), ("fp", fp)):
            if esperado.get(chave) is not None and valor != esperado[chave]:
                divergencias.append(f"{classe}: {chave} medido {valor} != declarado {esperado[chave]}")

    taxa_inconclusivo = float(inconclusivos.mean())
    medido["inconclusivo"] = taxa_inconclusivo
    if declarado.get("inconclusivo") is not None and abs(taxa_inconclusivo - declarado["inconclusivo"]) > 1e-6:
        divergencias.append(f"inconclusivo medido {taxa_inconclusivo:.6f} != declarado "
                            f"{declarado['inconclusivo']:.6f}")
    recalls = [medido[c]["recall"] for c in (declarado.get("por_classe") or {}) if medido[c]["recall"] is not None]
    recall_macro = float(np.mean(recalls)) if recalls else None
    acuracia_por_item = float((argmax == verdadeiros).mean())
    medido["recall_macro"] = recall_macro
    medido["acuracia_por_item"] = acuracia_por_item
    if declarado.get("recall_medio") is not None and recall_macro is not None \
            and abs(recall_macro - declarado["recall_medio"]) > 1e-9:
        divergencias.append(f"recall_macro medido {recall_macro:.6f} != declarado "
                            f"{declarado['recall_medio']:.6f}")

    recibo = {
        "artefato": Path(a.artefato).name,
        "sha256": cls.procedencia.sha256,
        "vintage": cls.procedencia.vintage,
        "extrator": cls.procedencia.extrator,
        "limiar": cls.limiar_de_confianca,
        "fonte": FONTE,
        "aviso_do_artefato": cls.procedencia.aviso,
        "medido": medido,
        "declarado": {"n": declarado.get("n"), "por_classe": declarado.get("por_classe"),
                      "inconclusivo": declarado.get("inconclusivo"),
                      "recall_macro": declarado.get("recall_medio")},
        "divergencias": divergencias,
    }
    Path(a.json).write_text(json.dumps(recibo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"recall_macro (media das classes, como o produtor mede) medido={recall_macro:.4f} "
          f"declarado={declarado.get('recall_medio')}")
    print(f"acuracia_por_item medido={acuracia_por_item:.4f} (metrica diferente: nao e a declarada)")
    print(f"inconclusivo medido={taxa_inconclusivo:.4f} declarado={declarado.get('inconclusivo')}")
    if a.cadeia:
        codigo_da_cadeia = _pela_cadeia(cls)
        if codigo_da_cadeia != 0:
            divergencias.append("a cadeia nao registrou o rastro do modelo")

    if divergencias:
        print("DIVERGENCIA entre o port e o artefato:")
        for d in divergencias:
            print("  -", d)
        print(f"recibo: {a.json}")
        return 1
    print(f"OK: o port reproduz o artefato. recibo: {a.json}")
    return 0



def _pela_cadeia(cls) -> int:
    """Roda UM item pela cadeia com o artefato e le o rastro de volta do banco.

    O item e sintetico (um recorte do conjunto copiado para as tres vistas) e o alinhamento e
    DECLARADO OK: sem isso a vista nao entra como evidencia (fail-closed de `captura.utilizavel`) e o
    ensaio nao exercita o caminho do modelo. O que este trecho prova e o que interessa: a medida do
    artefato chega ao `Decisor`, e o registro guarda a evidencia com a procedencia do artefato.
    """
    import sqlite3
    import tempfile
    from datetime import UTC, datetime

    from captura import Alinhamento, ItemCapturado, VistaCapturada
    from orquestracao import IdentidadeDoRig, executar
    from registro import Registro

    with tempfile.TemporaryDirectory() as pasta:
        origem = Path(conjunto_declarado()[0]["crop"])
        imagem = cv2.imread(str(origem), cv2.IMREAD_COLOR)
        copia = Path(pasta) / "lateral1.jpg"
        cv2.imwrite(str(copia), imagem)
        item = ItemCapturado(
            item_id="CANARIO-1", trigger_em=datetime.now(UTC),
            vistas=(VistaCapturada(vista=Vista.LATERAL1, imagem=copia, capturado_em=datetime.now(UTC),
                                   alinhamento=Alinhamento.OK, no_janela=True,
                                   motivo_da_janela="janela declarada pelo canario"),))
        banco = Path(pasta) / "canario.db"
        registro = Registro.abrir(str(banco))
        try:
            resultado = executar(item, cls, registro, IdentidadeDoRig("bancada", "canario"),
                                 roi=(0.0, 0.0, 1.0, 1.0))
            print(f"cadeia: item {resultado.item_id} -> {resultado.status} "
                  f"({resultado.gravacao}); motivos={list(resultado.conformidade.motivos)}")
            linhas = list(sqlite3.connect(str(banco)).execute(
                "select grandeza, round(valor,4), origem, papel, metodo from evidencia"))
        finally:
            registro.fechar()

    print(f"cadeia: {len(linhas)} evidencia(s) no registro")
    for linha in linhas:
        print("  ", linha)
    do_modelo = [l for l in linhas if l[2] == "classificador"]
    if not do_modelo:
        print("cadeia: nenhuma evidencia de origem 'classificador' no registro")
        return 1
    if cls.procedencia.vintage.split(" ")[0] not in str(do_modelo[0][4]):
        print(f"cadeia: evidencia sem o vintage do artefato: {do_modelo[0][4]!r}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
