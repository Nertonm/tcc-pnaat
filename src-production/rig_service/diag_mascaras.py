#!/usr/bin/env python3
"""Mede a comparacao de silhuetas em todos os casos (sintetico + real) antes de fixar limiares."""
from pathlib import Path

import numpy as np
from PIL import Image

import visao
from autoteste import cena, cinza, L, A  # noqa: E402
from PIL import ImageDraw, ImageFilter  # noqa: E402


def clarear(im, fator):
    a = np.asarray(im).astype(np.float32) * fator
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def desfocar(im, raio):
    return im.filter(ImageFilter.GaussianBlur(raio))


def quadrao_gigante(im):
    d = ImageDraw.Draw(im)
    d.rectangle([80, 60, L - 80, A - 60], fill=(20, 20, 25))
    return im

lim = dict(visao.LIMIARES_PADRAO)
ROI_TUDO = (0.0, 0.0, 1.0, 1.0)
fundo = cinza(cena("fundo"))
ref = visao.medir(cinza(cena("boa")), fundo, lim, ROI_TUDO)
print("mascara da referencia sintetica: area=%d" % ref["mascara"].sum())

casos = [("boa (identica)", lambda: cinza(cena("boa"))),
         ("sem_tampa", lambda: cinza(cena("sem_tampa"))),
         ("torto", lambda: cinza(cena("torto"))),
         ("deformado", lambda: cinza(cena("deformado"))),
         ("exposicao +25%", lambda: cinza(clarear(cena("boa"), 1.25))),
         ("desfocado", lambda: cinza(desfocar(cena("boa"), 6))),
         ("cena trocada", lambda: cinza(quadrao_gigante(cena("fundo"))))]
print(f"\n{'caso':<18} {'ok':<6} {'iou':<8} {'queda_topo':<11} {'tilt_dif':<9} {'alt_razao':<10} {'dif_no_topo'}")
for nome, gerar in casos:
    m = visao.medir(gerar(), fundo, lim, ROI_TUDO)
    if not m.get("ok"):
        print(f"{nome:<18} recusa: {m.get('motivo')}")
        continue
    c = visao.comparar_mascaras(m["mascara"], ref["mascara"])
    print(f"{nome:<18} {'sim':<6} {c['iou']:<8} {c['queda_topo']:<11} {c['tilt_diferencial_graus']:<9} "
          f"{c['altura_razao']:<10} {c['frac_dif_no_topo']}")

print("\n== quadros REAIS do Pi ==")
DIR = Path("/tmp/reais")
def carregar(n):
    return np.asarray(Image.open(DIR / n).convert("RGB")).astype(np.int16)
f_user = carregar("fundo.jpg")
m_ref = visao.medir(carregar("referencia.jpg"), f_user, lim, ROI_TUDO)
m_ult = visao.medir(carregar("ultima.jpg"), f_user, lim, ROI_TUDO)
for nome, m in (("referencia", m_ref), ("ultima", m_ult)):
    print(f"  {nome}: ok={m.get('ok')} motivo={m.get('motivo')} "
          + (f"area={m['mascara'].sum()} altura_rel={m['altura_rel']}" if m.get("ok") else ""))
if m_ref.get("ok") and m_ult.get("ok"):
    print("  comparacao:", visao.comparar_mascaras(m_ult["mascara"], m_ref["mascara"]))
