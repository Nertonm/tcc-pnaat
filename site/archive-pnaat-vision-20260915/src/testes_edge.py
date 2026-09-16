#!/usr/bin/env python3
"""Testes de borda e de caminho de erro do site da garrafa (nao dependem de camera).

Roda com asserts simples (o Pi nao tem pytest):
    python3 testes_edge.py      ->  saida 0 = tudo passou; != 0 = falhas listadas
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

import visao

FALHAS: list[str] = []
OK = 0


def chk(nome: str, cond: bool, detalhe: str = ""):
    global OK
    if cond:
        OK += 1
    else:
        FALHAS.append(f"{nome} {detalhe}")


def cena_simples(h=120, w=160, com_objeto=True, valor=128):
    a = np.full((h, w, 3), valor, np.uint8)
    if com_objeto:
        a[h // 6: int(h * 0.9), w // 3: w // 3 + 18] = 40
    return a


lim = dict(visao.LIMIARES_PADRAO)

# ---------------------------------------------------------------- utilidades numericas

chk("_otsu em imagem constante nao explode",
    isinstance(visao._otsu(np.full((20, 20), 7, np.uint8)), float))
t_const = visao._otsu(np.full((20, 20), 7, np.uint8))
chk("_otsu constante devolve limiar valido (0..255)", 0 <= t_const <= 255, f"t={t_const}")

bi = np.zeros((10, 10), np.uint8)
bi[:5] = 10
bi[5:] = 200
t_bi = visao._otsu(bi)
chk("_otsu devolve limiar entre as populacoes", 10 <= t_bi < 200, f"t={t_bi}")
escuro = bi <= t_bi
chk("_otsu: lado escuro e o menor (senao a mascara sai vazia)",
    bool(escuro.any()) and bool((~escuro).any()), f"escuro={escuro.mean():.2f}")

chk("_box_blur em 1x1", visao._box_blur(np.ones((1, 1), np.float32)).shape == (1, 1))
chk("_box_blur preserva media (borda refletida)",
    abs(float(visao._box_blur(np.full((30, 30), 5.0, np.float32)).mean()) - 5.0) < 1e-6)
chk("_box_blur k par nao quebra", visao._box_blur(np.ones((12, 12), np.float32), 4).shape == (12, 12))

m_vazia = np.zeros((50, 50), bool)
chk("_maior_componente com mascara vazia devolve vazio", visao._maior_componente(m_vazia).sum() == 0)
m2 = np.zeros((200, 200), bool)
m2[10:60, 10:40] = True      # componente pequena
m2[100:190, 80:120] = True   # componente grande
sel = visao._maior_componente(m2)
chk("_maior_componente mantem a MAIOR", sel[100:190, 80:120].all() and not sel[10:60, 10:40].any())

chk("nitidez em imagem lisa e ~0", visao.nitidez(cena_simples(com_objeto=False)) < 1.0)
chk("nitidez sobe com borda", visao.nitidez(cena_simples()) > visao.nitidez(cena_simples(com_objeto=False)))

chk("_anel tem borda e nao o centro",
    bool(visao._anel((100, 100))[0, 0]) and not bool(visao._anel((100, 100))[50, 50]))

# ---------------------------------------------------------------- ROI

saved = (visao.DADOS / "roi.json")
pre = saved.read_text() if saved.exists() else None
try:
    r = visao.salvar_roi(0.9, 0.9, 0.1, 0.1)          # invertido de proposito
    chk("salvar_roi ordena e limita", r == (0.1, 0.1, 0.9, 0.9), str(r))
    erro = False
    try:
        visao.salvar_roi(0.2, 0.2, 0.22, 0.22)        # pequena demais
    except ValueError:
        erro = True
    chk("salvar_roi recusa ROI pequena", erro)
    chk("roi_px devolve caixa dentro do quadro",
        visao.roi_px((100, 200, 3), (0.0, 0.0, 1.0, 1.0)) == (0, 0, 200, 100))
    chk("roi_px com roi invertida nao estoura",
        isinstance(visao.roi_px((100, 100, 3), (0.8, 0.8, 0.2, 0.2)), tuple))
finally:
    if pre is None:
        saved.unlink(missing_ok=True)
    else:
        saved.write_text(pre)

# ---------------------------------------------------------------- mascara / medir

fundo = cena_simples(com_objeto=False)
item = cena_simples(com_objeto=True)
chk("formato diferente -> motivo explicito",
    visao.mascara_garrafa(item, fundo[:50], lim)[1] == "tamanho_diferente_do_fundo")
chk("imagem minuscula -> motivo explicito",
    visao.mascara_garrafa(np.zeros((10, 10, 3), np.uint8),
                          np.zeros((10, 10, 3), np.uint8), lim)[1] == "roi_pequena_demais")
m, motivo = visao.mascara_garrafa(item, fundo, lim)
chk("silhueta detectada no caso simples", m is not None and m.sum() > 50, f"motivo={motivo}")
chk("ROI estreita demais para medir -> motivo explicito",
    visao.mascara_garrafa(item, fundo, lim, (0.75, 0.75, 1.0, 1.0))[1] == "roi_pequena_demais")
_m_roi, _ = visao.mascara_garrafa(item, fundo, lim, (0.30, 0.0, 0.80, 1.0))
chk("mascara respeita a ROI (nada fora dela)",
    _m_roi is None or not _m_roi[: int(120 * 0.0), :].any())

chk("medir sem fundo cai no Otsu e nao explode", isinstance(visao.medir(item, None, lim), dict))
med = visao.medir(item, fundo, lim)
chk("medir devolve mascara e bbox", med.get("ok") and "mascara" in med and len(med["bbox"]) == 4)
chk("medir marca motivo quando nao ok",
    visao.medir(fundo, fundo, lim).get("ok") is False)

# ---------------------------------------------------------------- comparacao de mascaras

c = visao.comparar_mascaras(med["mascara"], med["mascara"])
chk("mascara identica -> IoU 1.0", c["iou"] == 1.0 and c["tilt_diferencial_graus"] == 0.0, str(c))
c2 = visao.comparar_mascaras(np.zeros((10, 10), bool), np.zeros((10, 10), bool))
chk("mascara vazia -> recusa", c2.get("ok") is False and c2.get("motivo") == "mascara_vazia")
c3 = visao.comparar_mascaras(np.zeros((10, 10), bool), med["mascara"][:10, :10])
chk("tamanhos diferentes nao explodem", c3.get("ok") is False)

# ---------------------------------------------------------------- qualidade / decidir

ref = dict(med)
frame = visao.metricas_frame(item)
chk("metricas_frame devolve as 3 chaves", set(frame) == {"nitidez", "brilho", "saturado"})
chk("qualidade: foco ruim acusa",
    visao.qualidade({"nitidez": 0.0, "brilho": 100.0, "saturado": 0.0}, ref, lim, apenas_foco=True) != [])
chk("qualidade: captura igual nao acusa",
    visao.qualidade(frame, ref, lim) == [], str(visao.qualidade(frame, ref, lim)))

d = visao.decidir(med, None, lim, frame)
chk("sem referencia -> sem_referencia", d["veredito"] == "sem_referencia", str(d))
d = visao.decidir(med, ref, lim, frame, med["mascara"])
chk("mesma silhueta -> ok", d["veredito"] == "ok", str(d))
d = visao.decidir({"ok": False, "motivo": "cena_diferente_do_fundo"}, ref, lim, frame, med["mascara"])
chk("cena trocada -> cena_mudou", d["veredito"] == "cena_mudou")
d = visao.decidir({"ok": False, "motivo": "motivo_novo_desconhecido"}, ref, lim, frame, med["mascara"])
chk("motivo desconhecido -> inconclusivo (nao explode)", d["veredito"] == "inconclusivo")
d = visao.decidir({"ok": False, "motivo": "sem_silhueta"}, ref, lim,
                  {"nitidez": 0.0, "brilho": 100.0, "saturado": 0.0}, med["mascara"])
chk("foco ruim domina o motivo de recusa", d["veredito"] == "inconclusivo" and "foco" in d["motivos"][0])
d = visao.decidir(med, ref, lim, frame, None)
chk("referencia sem mascara cai no fallback de perfil", d["veredito"] in ("ok", "defeito", "inconclusivo"), str(d))

# ---------------------------------------------------------------- persistencia

mask_arq = visao.DADOS / "referencia_mascara.png"
pre_m = mask_arq.read_bytes() if mask_arq.exists() else None
try:
    visao.salvar_mascara(med["mascara"])
    carregada = visao.carregar_mascara()
    chk("mascara salva e recarregada igual", carregada is not None and np.array_equal(carregada, med["mascara"]))
    mask_arq.write_bytes(b"lixo")                       # arquivo corrompido
    chk("mascara corrompida -> None (nao explode)", visao.carregar_mascara() is None)
finally:
    if pre_m is None:
        mask_arq.unlink(missing_ok=True)
    else:
        mask_arq.write_bytes(pre_m)

lim_arq = visao.DADOS / "limiares.json"
pre_l = lim_arq.read_text() if lim_arq.exists() else None
try:
    lim_arq.write_text("{isso nao e json")
    chk("limiares.json corrompido -> volta ao padrao",
        visao.limiares()["diff_fundo"] == visao.LIMIARES_PADRAO["diff_fundo"])
    lim_arq.write_text(json.dumps({"diff_fundo": 44, "chave_inventada": 9}))
    l2 = visao.limiares()
    chk("limiar valido do arquivo e aplicado", l2["diff_fundo"] == 44)
    chk("chave desconhecida do arquivo nao entra", "chave_inventada" not in l2, str(sorted(l2)))
    novo = visao.salvar_limiares({"diff_fundo": "33", "nao_existe": "1"})
    chk("salvar_limiares converte string", novo["diff_fundo"] == 33.0)
    chk("salvar_limiares ignora chave desconhecida", "nao_existe" not in novo)
    chk("salvar_limiares ignora valor invalido",
        isinstance(visao.salvar_limiares({"diff_fundo": "abc"})["diff_fundo"], float))
finally:
    if pre_l is None:
        lim_arq.unlink(missing_ok=True)
    else:
        lim_arq.write_text(pre_l)

# ---------------------------------------------------------------- camera (sem abrir a camera)

cam = visao.Camera()
chk("Camera.ultimo sem iniciar devolve (None, 0)", cam.ultimo() == (None, 0.0))
cam.parar()
cam.parar()
chk("Camera.parar e idempotente", cam.parar() is None)
chk("esperar_frame sem camera respeita o timeout",
    cam.esperar_frame(timeout=0.3) is None)

# ---------------------------------------------------------------- leitura de JPEG real

with tempfile.TemporaryDirectory() as td:
    jpg = Path(td) / "a.jpg"
    Image.fromarray(cena_simples(com_objeto=True)).save(jpg)
    arr = visao.imagem(jpg.read_bytes())
    chk("imagem() le JPEG e devolve int16 RGB", arr.dtype == np.int16 and arr.ndim == 3 and arr.shape[2] == 3)
    try:
        visao.imagem(b"isto nao e jpeg")
        chk("imagem() com bytes invalidos levanta erro", False, "nao levantou")
    except Exception:
        chk("imagem() com bytes invalidos levanta erro tratavel", True)

print(f"testes de borda: {OK} ok, {len(FALHAS)} falha(s)")
for f in FALHAS:
    print("  FALHA:", f)
sys.exit(1 if FALHAS else 0)
