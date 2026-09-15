#!/usr/bin/env python3
"""Auto-teste do site da garrafa com cenas sinteticas (sem camera).

Cria um fundo, uma garrafa BOA (referencia) e quatro itens: ok, sem tampa, tampa torta e corpo
deformado. Exige que a decisao acerte cada caso. Sai != 0 se qualquer caso divergir.
"""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import visao

L = 1296
A = 972


def _ruido(im: Image.Image, semente: int = 7) -> Image.Image:
    """Ruido de sensor sintetico: sem ele a cena fica lisa e o gate de nitidez reprova por foco."""
    rng = np.random.default_rng(semente)
    a = np.asarray(im).astype(np.float32) + rng.normal(0, 6.0, np.asarray(im).shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def cena(tipo: str) -> Image.Image:
    im = Image.new("RGB", (L, A), (128, 128, 128))
    d = ImageDraw.Draw(im)
    if tipo == "fundo":
        return _ruido(im)
    cx = L // 2
    corpo_l, corpo_a = 210, 470           # corpo da garrafa (largura x altura)
    y_base = 880
    y_topo_corpo = y_base - corpo_a
    ombro_a = 70                          # altura do ombro->gargalo
    gargalo_l = 70
    tampa_l, tampa_a = 96, 46

    d.rectangle([cx - corpo_l // 2, y_topo_corpo, cx + corpo_l // 2, y_base], fill=(45, 45, 50))
    if tipo == "deformado":
        # bojo lateral na parte media do corpo
        d.ellipse([cx + corpo_l // 2 - 30, y_topo_corpo + 200, cx + corpo_l // 2 + 70,
                   y_topo_corpo + 300], fill=(45, 45, 50))
    # ombro
    d.polygon([(cx - corpo_l // 2, y_topo_corpo), (cx + corpo_l // 2, y_topo_corpo),
               (cx + gargalo_l // 2, y_topo_corpo - ombro_a),
               (cx - gargalo_l // 2, y_topo_corpo - ombro_a)], fill=(45, 45, 50))
    y_gargalo_topo = y_topo_corpo - ombro_a
    if tipo != "sem_tampa":
        d.rectangle([cx - gargalo_l // 2, y_gargalo_topo - 30, cx + gargalo_l // 2, y_gargalo_topo],
                    fill=(45, 45, 50))
        if tipo == "torto":
            for i, dx in enumerate(range(0, 56, 11)):     # tampa deslocando lateralmente
                d.rectangle([cx - tampa_l // 2 + dx, y_gargalo_topo - 30 - tampa_a + i * 9,
                             cx + tampa_l // 2 + dx, y_gargalo_topo - 30 - tampa_a + (i + 1) * 9 - 1],
                            fill=(40, 40, 45))
        else:
            d.rectangle([cx - tampa_l // 2, y_gargalo_topo - 30 - tampa_a,
                         cx + tampa_l // 2, y_gargalo_topo - 30], fill=(40, 40, 45))
    return _ruido(im, semente=11 + len(tipo))


def cinza(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("RGB")).astype(np.int16)


def clarear(im, fator):
    a = np.asarray(im).astype(np.float32) * fator
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def desfocar(im, raio):
    return im.filter(ImageFilter.GaussianBlur(raio))


def quadrao_gigante(im):
    """Cena incompativel com o fundo (quadrado escuro cobrindo ~78% do quadro)."""
    d = ImageDraw.Draw(im)
    d.rectangle([80, 60, L - 80, A - 60], fill=(20, 20, 25))
    return im


def main() -> int:
    lim = dict(visao.LIMIARES_PADRAO)
    fundo = cinza(cena("fundo"))

    boa = visao.medir(cinza(cena("boa")), fundo, lim)
    print("REFERENCIA (garrafa boa):", {k: boa[k] for k in
          ("ok", "altura_rel", "largura_topo_rel", "tilt_tampa_graus", "nitidez", "frac_altura_quadro")})
    if not boa["ok"]:
        print("FALHA: referencia nao medida")
        return 1

    casos = [
        ("boa", "ok", "normal", lambda: cinza(cena("boa"))),
        ("sem_tampa", "defeito", "tampa_ausente", lambda: cinza(cena("sem_tampa"))),
        ("torto", "defeito", "tampa_mal_rosqueada", lambda: cinza(cena("torto"))),
        ("deformado", "defeito", "deformidade", lambda: cinza(cena("deformado"))),
        ("exposicao +25%", "ok", "normal", lambda: cinza(clarear(cena("boa"), 1.25))),
        ("desfocado", "inconclusivo", "inconclusivo", lambda: cinza(desfocar(cena("boa"), 6))),
        ("sem garrafa", "sem_garrafa", "sem_garrafa", lambda: cinza(cena("fundo"))),
        ("cena trocada", "cena_mudou", "cena_mudou", lambda: cinza(quadrao_gigante(cena("fundo")))),
    ]
    falhas = 0
    print(f"\n{'caso':<14} {'veredito esperado':<14} {'classe esperada':<20} {'obtido':<14} {'classe':<20} ok")
    for nome, ver_esp, cls_esp, gerar in casos:
        img_caso = gerar()
        med = visao.medir(img_caso, fundo, lim)
        res = visao.decidir(med, boa, lim, visao.metricas_frame(img_caso), boa["mascara"])
        ok = res["veredito"] == ver_esp and res["classe"] == cls_esp
        falhas += 0 if ok else 1
        print(f"{nome:<14} {ver_esp:<14} {cls_esp:<20} {res['veredito']:<14} {res['classe']:<20} "
              f"{'SIM' if ok else 'NAO'}  {res['motivos']}")

    print(f"\nRESULTADO: {len(casos)-falhas}/{len(casos)} casos conforme o esperado")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
