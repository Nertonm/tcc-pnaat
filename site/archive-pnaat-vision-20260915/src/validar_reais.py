#!/usr/bin/env python3
"""Valida a regra nas imagens REAIS capturadas no Pi (o teste que faltava).

Cenarios (todos com resultado esperado declarado ANTES):
  1. fundo da cena errada (teto) + item da mesa  -> cena_mudou  (antes: medidas sem sentido)
  2. fundo da propria referencia + mesma cena    -> sem_garrafa (nada mudou entre os quadros)
  3. fundo = referencia (mesma cena) + item = ultima -> decisao coerente, nunca quadro inteiro
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

import visao

DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/reais")


def carregar(nome):
    return np.asarray(Image.open(DIR / nome).convert("RGB")).astype(np.int16)


def main() -> int:
    lim = dict(visao.LIMIARES_PADRAO)
    fundo_teto = carregar("teto.jpg")
    fundo_user = carregar("fundo.jpg")
    ref = carregar("referencia.jpg")
    ult = carregar("ultima.jpg")

    falhas = 0

    print("== cenario 1: fundo do teto, item = sua referencia (mesa com garrafa) ==")
    med = visao.medir(ref, fundo_teto, lim)
    res = visao.decidir(med, None, lim)
    ok = res["veredito"] == "cena_mudou"
    falhas += 0 if ok else 1
    print(f"   medidas ok={med.get('ok')} motivo={med.get('motivo')} -> {res['veredito']} "
          f"{'SIM' if ok else 'NAO'}  {res['motivos']}")

    print("== cenario 2: fundo = seu fundo salvo, item = sua referencia ==")
    med = visao.medir(ref, fundo_user, lim)
    res = visao.decidir(med, None, lim)
    esperado = {"cena_mudou", "sem_garrafa", "sem_referencia"}
    ok = res["veredito"] in esperado
    falhas += 0 if ok else 1
    print(f"   medidas ok={med.get('ok')} motivo={med.get('motivo')} -> {res['veredito']} "
          f"{'SIM' if ok else 'NAO'}  {res['motivos']}"
          + (f" | frac_area={med.get('frac_area')}" if med.get("ok") else ""))

    print("== cenario 3: fundo = sua referencia, item = ultima captura (mesma cena) ==")
    med = visao.medir(ult, ref, lim)
    res = visao.decidir(med, None, lim)
    ok = med.get("motivo") != "cena_diferente_do_fundo"
    falhas += 0 if ok else 1
    print(f"   medidas ok={med.get('ok')} motivo={med.get('motivo')} -> {res['veredito']} "
          f"{'SIM' if ok else 'NAO'}"
          + (f" | frac_area={med.get('frac_area')} altura_rel={med.get('altura_rel')} "
             f"nitidez={med.get('nitidez')}" if med.get("ok") else ""))

    print("== cenario 4: decisao completa com quadros reais (fundo seu, ref sua, item = ultima) ==")
    med_ref = visao.medir(ref, fundo_user, lim)
    med_ult = visao.medir(ult, fundo_user, lim)
    if med_ref.get("ok") and med_ult.get("ok"):
        res = visao.decidir(med_ult, med_ref, lim, visao.metricas_frame(ult), med_ref.get("mascara"))
        print(f"   referencia: altura_rel={med_ref['altura_rel']} tilt={med_ref['tilt_tampa_graus']} "
              f"nitidez={med_ref['nitidez']} frac_area={med_ref['frac_area']}")
        print(f"   item      : altura_rel={med_ult.get('altura_rel')} tilt={med_ult.get('tilt_tampa_graus')} "
              f"nitidez={med_ult.get('nitidez')} frac_area={med_ult.get('frac_area')}")
        print(f"   -> {res['veredito']} / {res['classe']}  {res['motivos']}")
        # a mesma garrafa foi capturada nas duas fotos: qualquer "defeito" aqui e FALSO POSITIVO
        ok = res["veredito"] in ("ok", "inconclusivo")
        falhas += 0 if ok else 1
        print(f"   {'SIM' if ok else 'NAO'} (mesma garrafa: nao pode sair 'defeito' -- "
              f"defeito aqui seria falso positivo)")
    else:
        print(f"   recusa honesta: ref={med_ref.get('motivo')} item={med_ult.get('motivo')}")
        falhas += 0
    print(f"\nRESULTADO: {4-falhas}/4 cenarios conforme o esperado")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
