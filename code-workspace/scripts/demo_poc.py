#!/usr/bin/env python3
"""DEMO da PoC (demonstracao): pipeline de inspeção ponta a ponta em imagens REAIS.

Sequência acompanhável (exigência da demonstração): entrada -> funcionamento -> resultado,
usando DOIS elementos da arquitetura (gatilho de presença + registro/dashboard).

    cd code-workspace
    PYTHONPATH=src <TCC_HOME>/github/.venv/bin/python scripts/demo_poc.py --frames 3 --pausa 1.0

Saídas em demo/saida/: imagens anotadas, mapas de anomalia, dashboard.html, registro.json.

HONESTIDADE DO ESCOPO (declarado no próprio demo):
  * métricas de qualidade e modelo one-class: medidos aqui, com números reais;
  * geometria da tampa: o contorno é detectado, mas a MEDIÇÃO ainda não é confiável nas
    imagens atuais (rig v0, sem backlight) -> aparece como "em validação", nunca como medida;
  * defeito real: não existe no dataset ainda; a perturbação de CONTROLE serve para provar
    que o modelo reage a uma anomalia conhecida (ground truth registrado).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from pocs.events import DefectClass, Dominio, ObservationEvent, ViewResult
from pocs.poc01_trigger.presence import PresenceTrigger, present_from_sensor
from pocs.poc04_fusao import ConfiguracaoFusao, fundir
from pocs.poc05_registro import LocalRegistry
from pocs.poc07_dashboard import recorrencia, summarize
from pocs.poc08_preproc import preproc

# Configuracao DECLARADA do rig na bancada desta demonstracao (D-04/D-23).
# Uma unica vista de corpo e sem check dimensional: a fusao NAO pode ser cobrada por uma
# segunda vista que nao existe -- mas o item tambem nao pode ser aprovado com dominio nao medido.
CONFIG_FUSAO_DEMO = ConfiguracaoFusao(
    rig_id="bancada-1-vista",
    vistas_decisoria_por_dominio=1,
    checagem_obrigatoria=False,
    dominios_medidos=(Dominio.CORPO,),
)

TCC_HOME = Path(os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat")))
BASE_DATASETS = Path(os.environ.get("PNAAT_DATASETS", str(TCC_HOME / "datasets" / "pnaat")))
ROI_TAMPA = 0.35           # fracao superior usada para o dominio da tampa
ESPECULAR_MAX = 0.03       # acima disso a captura e parcial (gate de qualidade)
TENENGRAD_MIN = 20.0       # abaixo disso a captura esta sem foco util


def _confianca_por_margem(score: float | None, limiar: float | None, suspeita: bool) -> float:
    """Confianca declarada = distancia relativa do score ao limiar derivado (0..1).

    Nao e probabilidade: e a margem medida em relacao ao proprio limiar. Sem modelo/limiar, a
    confianca fica 0.0 -- nao se inventa confianca para evidencia que nao existe.
    """
    if score is None or not limiar:
        return 0.0
    margem = (score - limiar) / limiar if suspeita else (limiar - score) / limiar
    return round(min(1.0, max(0.0, margem)), 4)


def medida_do_corpo(r: dict, limiar: float | None) -> ViewResult:
    """Traduz a decisao do detector (dominio do corpo) em UMA medida do PoC-04.

    Regra de honestidade (D-11/D-04): a suspeita do detector de anomalia NAO vira classe de
    defeito -- vira escalonamento para analise humana. Captura degradada tambem nao aprova.
    """
    decisao = r["decisao"]
    score = r["corpo"]["score"]
    if decisao == "suspeita_anomalia":
        return ViewResult("lateral1", Dominio.CORPO, DefectClass.INCONCLUSIVO,
                          _confianca_por_margem(score, limiar, True),
                          escalona=True, motivo="suspeita_de_anomalia")
    if decisao == "normal":
        return ViewResult("lateral1", Dominio.CORPO, DefectClass.NORMAL,
                          _confianca_por_margem(score, limiar, False))
    return ViewResult("lateral1", Dominio.CORPO, DefectClass.INCONCLUSIVO, 0.0,
                      escalona=True, motivo="captura_ou_modelo_indisponivel")


def titulo(n: int, total: int, texto: str) -> None:
    print(f"\n{'=' * 72}\n[{n}/{total}] {texto}\n{'=' * 72}")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def carregar_modelo(pasta_imgs: Path) -> tuple[dict, str]:
    """Carrega o checkpoint one-class e devolve {nome_arquivo: {score, mapa}} + status."""
    info_path = BASE_DATASETS / "resultados" / "modelo_info.json"
    if not info_path.exists():
        return {}, f"modelo_info.json ausente ({info_path}): rode treinar_dataset.py"
    info = json.loads(info_path.read_text())
    ckpt = info.get("checkpoint")
    if not ckpt or not Path(ckpt).exists():
        return {}, "checkpoint ausente: rode treinar_dataset.py"
    try:
        from anomalib.engine import Engine
        from anomalib.models import Padim, Patchcore

        modelo_cls = {"patchcore": Patchcore, "padim": Padim}[info.get("modelo", "patchcore")]
        eng = Engine(accelerator="auto", devices=1, enable_progress_bar=False,
                     default_root_dir=str(BASE_DATASETS / "resultados"))
        preds = eng.predict(model=modelo_cls(), data_path=str(pasta_imgs), ckpt_path=ckpt)
        saida: dict[str, dict] = {}
        # anomalib 2.x devolve LOTES (ImageBatch): image_path/pred_score/anomaly_map sao listas/tensores
        # com dimensao de batch -> parear por indice dentro de cada lote.
        for lote in preds:
            caminhos = list(getattr(lote, "image_path", []) or [])
            scores = getattr(lote, "pred_score", None)
            mapas = getattr(lote, "anomaly_map", None)
            for i, caminho in enumerate(caminhos):
                nome = Path(str(caminho)).name
                mapa = None
                if mapas is not None:
                    try:
                        mapa = np.asarray(mapas)[i].squeeze()
                    except Exception:
                        mapa = None
                # SINAL UTILIZADO: maximo do anomaly_map CRU. O pred_score do anomalib 2.6.1
                # satura (0 ou 1) por normalizacao com os limites do conjunto -> nao compara itens.
                bruto = float(np.asarray(mapa).max()) if mapa is not None else None
                try:
                    normalizado = float(np.asarray(scores).ravel()[i])
                except Exception:
                    normalizado = None
                saida[nome] = {"score": bruto, "score_normalizado": normalizado, "mapa": mapa}
        return saida, (f"modelo={info.get('modelo')} sinal=max(anomaly_map) "
                       f"limiar_bruto={info.get('limiar_bruto')}")
    except Exception as e:  # nunca derruba o demo por causa do modelo
        return {}, f"falha ao carregar/predizer: {str(e)[:160]}"


def analisar(frame: Path, saida_dir: Path, scores: dict, limiar: float | None) -> dict:
    """Roda o pipeline num item e devolve o resultado + evidencia."""
    img = cv2.imread(str(frame))
    h, w = img.shape[:2]
    tampa = img[0: int(h * ROI_TAMPA), :]
    corpo = img[int(h * ROI_TAMPA):, :]

    geom = preproc.cap_geometry(preproc.to_gray(tampa))
    ten = preproc.tenengrad(img)
    esp = preproc.specular_coverage(img)
    cnr_tb = preproc.cnr(tampa, corpo)

    score = scores.get(frame.name, {}).get("score")
    mapa = scores.get(frame.name, {}).get("mapa")

    # domínio do corpo: modelo one-class (limiar derivado das próprias normais, 3 sigma)
    if score is None or limiar is None:
        corpo_classe, corpo_nota = "inconclusivo", "modelo indisponível"
    elif score > limiar:
        corpo_classe, corpo_nota = "suspeita_anomalia", f"score {score:.4f} > limiar {limiar:.4f}"
    else:
        corpo_classe, corpo_nota = "normal", f"score {score:.4f} <= limiar {limiar:.4f}"

    # gate de qualidade: captura ruim nunca vira aprovação silenciosa (regra D-04)
    qualidade = "ok"
    if esp > ESPECULAR_MAX or ten < TENENGRAD_MIN:
        qualidade = "parcial"
        corpo_classe, corpo_nota = "inconclusivo", f"captura {qualidade}: {corpo_nota}"

    # anotação visual
    vis = img.copy()
    cv2.rectangle(vis, (0, 0), (w - 1, int(h * ROI_TAMPA)), (60, 200, 60), 1)
    cv2.putText(vis, f"ROI tampa ({int(ROI_TAMPA*100)}% topo)", (6, 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 200, 60), 1, cv2.LINE_AA)
    cv2.putText(vis, f"corpo: {corpo_classe}", (6, int(h * ROI_TAMPA) + 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 200, 60), 1, cv2.LINE_AA)
    if score is not None:
        cv2.putText(vis, f"score={score:.4f} limiar={limiar:.4f}", (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 200, 60), 1, cv2.LINE_AA)
    if geom.get("ok"):
        cv2.ellipse(vis, (int(geom["cx"]), int(geom["cy"])),
                    (int(geom["semi_maior"]), int(geom["semi_menor"])),
                    geom["tilt_graus"], 0, 360, (0, 165, 255), 1)
        cv2.putText(vis, "contorno detectado (medicao em validacao)", (6, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 165, 255), 1, cv2.LINE_AA)
    cv2.imwrite(str(saida_dir / f"{frame.stem}_anotado.png"), vis)

    if mapa is not None:
        m = mapa.astype(np.float32)
        m = (m - m.min()) / (np.ptp(m) + 1e-9)
        calor = cv2.applyColorMap((m * 255).astype(np.uint8), cv2.COLORMAP_JET)
        calor = cv2.resize(calor, (w, h))
        sobreposto = cv2.addWeighted(img, 0.55, calor, 0.45, 0)
        cv2.imwrite(str(saida_dir / f"{frame.stem}_mapa.png"), sobreposto)

    return {
        "frame": frame.name, "sha256": sha256(frame),
        "tampa": {"contorno_detectado": bool(geom.get("ok")),
                  "inliers": geom.get("inliers"), "pontos": geom.get("pontos"),
                  "medicao": "em validacao (rig v0 sem backlight)"},
        "qualidade": {"tenengrad": round(ten, 1), "especular_pct": round(esp * 100, 3),
                      "cnr_tampa_corpo": round(cnr_tb, 3), "estado": qualidade},
        "corpo": {"classe": corpo_classe, "nota": corpo_nota, "score": score,
                   "score_normalizado": scores.get(frame.name, {}).get("score_normalizado")},
        "decisao": corpo_classe,
    }


def escrever_dashboard(saida_dir: Path, resumo: dict, linhas: list[dict]) -> None:
    corpo_html = []
    for r in linhas:
        stem = Path(r["frame"]).stem
        score = "" if r["corpo"]["score"] is None else f"{r['corpo']['score']:.4f}"
        mapa_html = ""
        if (saida_dir / f"{stem}_mapa.png").exists():
            mapa_html = f'<img src="{stem}_mapa.png" width="190">'
        corpo_html.append(
            f"<tr><td>{r['frame']}</td><td>{r['decisao']}</td><td>{score}</td>"
            f"<td>{r['qualidade']['tenengrad']}</td><td>{r['qualidade']['especular_pct']}%</td>"
            f"<td>{r['qualidade']['cnr_tampa_corpo']}</td>"
            f'<td><img src="{stem}_anotado.png" width="190"></td><td>{mapa_html}</td></tr>'
        )
    html = f"""<!doctype html><html lang="pt-br"><meta charset="utf-8">
<title>PNAAT PoC - dashboard</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;background:#0f1115;color:#e6e6e6}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #333;padding:6px;font-size:13px}}
th{{background:#1b1f27}}h1{{font-size:20px}}code{{background:#1b1f27;padding:2px 4px}}</style>
<h1>PNAAT - PoC: itens processados</h1>
<p>resumo: <code>{json.dumps(resumo, ensure_ascii=False)}</code></p>
<table><tr><th>frame</th><th>decisao</th><th>score</th><th>tenengrad</th><th>especular</th>
<th>CNR</th><th>anotado</th><th>mapa</th></tr>
{''.join(corpo_html)}</table>
<p style="opacity:.7">Geometria da tampa: em validacao. Modelo: one-class treinado so com normais.</p>
</html>"""
    (saida_dir / "dashboard.html").write_text(html)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", type=int, default=3, help="quantas normais usar")
    ap.add_argument("--pausa", type=float, default=1.0, help="segundos entre etapas (video)")
    ap.add_argument("--saida", type=Path, default=Path("demo/saida"))
    args = ap.parse_args()

    entrada_dir = Path("demo/entrada")
    entrada_dir.mkdir(parents=True, exist_ok=True)
    args.saida.mkdir(parents=True, exist_ok=True)

    normais = sorted((BASE_DATASETS / "dataset" / "normal").glob("*.jpg"))[: args.frames]
    controle = sorted((BASE_DATASETS / "controle").glob("*_controle_*.jpg")) if (
        BASE_DATASETS / "controle").exists() else []
    if not normais:
        print("ERRO: sem frames normais em", BASE_DATASETS / "dataset" / "normal")
        return 2

    itens = list(normais) + list(controle)
    for f in itens:  # copia para uma pasta de entrada unica (o preditor le uma pasta)
        shutil.copy(f, entrada_dir / f.name)

    print("PNAAT - Prova de Conceito: inspecao multi-view com rastreabilidade")
    print(f"data: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"normais: {len(normais)}  controles: {len(controle)}  saida: {args.saida}")
    time.sleep(args.pausa)

    # ---- 1) ENTRADA: gatilho (ESP32/E18-D80NK)
    titulo(1, 7, "ENTRADA 1/2 - gatilho de presenca (E18-D80NK + ESP32)")
    niveis = [1, 1, 0, 0, 0, 0, 0, 1, 1]
    trigger = PresenceTrigger(views=("topo", "lateral1", "lateral2"), stable_reads=5)
    janela = None
    for n in niveis:
        presente = present_from_sensor(n)
        run = trigger.update(presente)
        print(f"  leitura nivel={n} -> {'PRESENTE' if presente else 'livre'}"
              f"{'   << janela aberta' if run else ''}")
        if run:
            janela = run
        time.sleep(args.pausa / 3)
    if janela is None:
        print("  ERRO: gatilho nao abriu janela")
        return 3
    print(f"  janela={janela.item_window_id} vistas={janela.views} (gatilho estavel, sem duplicidade)")
    time.sleep(args.pausa)

    # ---- 2) ENTRADA: item fisico
    titulo(2, 7, "ENTRADA 2/2 - item real (frames do ensaio)")
    for f in itens:
        print(f"  {f.name}  sha256={sha256(f)}  ({f.stat().st_size // 1024} KB)")
    time.sleep(args.pausa)

    # ---- 3) PRE-PROCESSAMENTO
    titulo(3, 7, "FUNCIONAMENTO 1/3 - pre-processamento deterministico")
    print(f"  ROI tampa = {int(ROI_TAMPA*100)}% superior | ROI corpo = restante")
    print("  etapas disponiveis: flat-field, alinhamento NCC piramidal, ROI, CLAHE, "
          "mascara de especular, geometria (Canny+elipse RANSAC), metricas de qualidade")

    # ---- 4) MODELO
    titulo(4, 7, "FUNCIONAMENTO 2/3 - modelo one-class (treinado SO com normais)")
    scores, status_modelo = carregar_modelo(entrada_dir)
    print("  ", status_modelo)
    if not scores:
        print("   AVISO: sem scores - o demo segue com geometria/metricas e diz isso em voz alta")
    limiar = None
    info_path = BASE_DATASETS / "resultados" / "modelo_info.json"
    if info_path.exists():
        _info = json.loads(info_path.read_text())
        limiar = _info.get("limiar_bruto") or _info.get("limiar_3sigma")
    time.sleep(args.pausa)

    # ---- 5) ANALISE + DECISAO
    titulo(5, 7, "FUNCIONAMENTO 3/3 - analise por dominio + decisao deterministica")
    resultados = [analisar(f, args.saida, scores, limiar) for f in itens]
    for r in resultados:
        s = "n/d" if r["corpo"]["score"] is None else f"{r['corpo']['score']:.4f}"
        norm = r["corpo"].get("score_normalizado")
        norm_txt = "" if norm is None else f" (normalizado {norm:.2f})"
        print(f"  {r['frame']:<30} max(mapa)={s}{norm_txt:<18} tenengrad={r['qualidade']['tenengrad']:<7} "
              f"-> {r['decisao']}")
        print(f"      tampa: contorno={r['tampa']['contorno_detectado']} "
              f"inliers={r['tampa']['inliers']} | medicao: {r['tampa']['medicao']}")
    time.sleep(args.pausa)

    # ---- 6) REGISTRO + DASHBOARD
    titulo(6, 7, "RESULTADO 1/2 - fusao por dominio + registro local + dashboard")
    print(f"  config de fusao DECLARADA: rig_id={CONFIG_FUSAO_DEMO.rig_id} | "
          f"vistas decisorias por dominio={CONFIG_FUSAO_DEMO.vistas_decisoria_por_dominio} | "
          f"check dimensional obrigatorio={CONFIG_FUSAO_DEMO.checagem_obrigatoria} | "
          f"dominios medidos={[d.value for d in CONFIG_FUSAO_DEMO.dominios_medidos]}")
    reg = LocalRegistry()
    for i, r in enumerate(resultados, 1):
        views = (medida_do_corpo(r, limiar),)
        fusao = fundir(views, CONFIG_FUSAO_DEMO)
        ev = ObservationEvent(
            event_id=f"ev-{i:03d}", item_id=f"i-{i:03d}", esteira_id="est-b", node_id="n01",
            location="bancada-tcc", recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            views=views, fused=fusao.classe, confidence=fusao.confidence,
            quality=r["qualidade"]["estado"], fusao=fusao.como_dict(),
        )
        estado = reg.upsert(ev)
        print(f"  {ev.event_id} gravado ({estado}) classe={fusao.classe.value} "
              f"tampa={fusao.status_tampa} corpo={fusao.status_corpo} "
              f"qualidade={fusao.qualidade_registro} escalonado={fusao.escalonado}")
        print(f"      motivos: {', '.join(fusao.motivos) or '(nenhum)'}")

    resumo = summarize(reg)
    print(f"\n  resumo: {json.dumps(resumo, ensure_ascii=False)}")
    print("\n  ultimos itens:")
    for linha in recorrencia(reg, limite=10):
        print(f"    {linha['event_id']} {linha['item_id']} {linha['defeito']:<12} {linha['quality']}")

    (args.saida / "registro.json").write_text(json.dumps([l for l in recorrencia(reg, limite=50)],
                                                         indent=1, ensure_ascii=False))
    (args.saida / "resultados.json").write_text(json.dumps(resultados, indent=1, ensure_ascii=False))
    escrever_dashboard(args.saida, resumo, resultados)
    print(f"\n  dashboard.html e imagens em: {args.saida}")
    time.sleep(args.pausa)

    # ---- 7) RESULTADO + PROXIMO PASSO
    titulo(7, 7, "RESULTADO 2/2 - o que provou e o que falta")
    # Contagem pelo resultado do ITEM (fusao por dominio), nao pela decisao crua do detector:
    # rotulo que conta outra coisa que nao a decisao registrada e rotulo que mente.
    classes_item = [ev.fused.value for ev in reg.all()]
    com_defeito = sum(1 for c in classes_item if c not in ("normal", "inconclusivo"))
    inconclusivos = sum(1 for c in classes_item if c == "inconclusivo")
    print(f"  itens processados: {len(classes_item)} | itens com defeito: {com_defeito} | "
          f"inconclusivos: {inconclusivos}")
    print("  PROVADO: entrada (gatilho+imagem) -> pipeline (preproc+modelo+decisao) -> resultado "
          "(registro+dashboard), com metrica e evidencia por item.")
    print("  PROXIMO PASSO (nao integrado): (1) pares de defeito reais/sinteticos para medir "
          "acerto; (2) rig v1 com backlight para tornar a MEDICAO da tampa confiavel; "
          "(3) calibracao px->mm; (4) execucao no Raspberry Pi 5 com o firmware ESP32.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
