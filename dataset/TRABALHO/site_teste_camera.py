#!/usr/bin/env python3
"""Site de teste ao vivo do candidato v7a (bancada).

O que faz: consome o MJPEG que o serviço de câmera do host já publica (não abre o device —
o serviço é dono do V4L2), roda o detector v7a em cada quadro, aplica a decisão operacional
(limiar POR CLASSE + regra do silêncio: nada passa -> REVISAR) e devolve um MJPEG anotado.

Contrato honesto: é bancada. Não há ROI do rig, o alvo é o que estiver na frente da câmera, e
o número aqui não é métrica de acurácia — é prova de encanamento e comportamento ao vivo.

Uso: uvicorn site_teste_camera:app --host 0.0.0.0 --port 8097
Env: FONTE (default http://127.0.0.1:8099/stream.mjpg), PESO, IMGSZ, CONF
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import threading
import time
from collections import Counter

import cv2
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from ultralytics import YOLO

FONTE = os.environ.get('FONTE', 'http://127.0.0.1:8099/stream.mjpg')
_G = Path(__file__).resolve().parents[2]
PESO = os.environ.get('PESO') or str(_G.parent.parent /
                                   'pnaat-modelos/ENTREGA/v7a-lateral/v7a-lateral.pt')
IMGSZ = int(os.environ.get('IMGSZ', '480'))
CONF = float(os.environ.get('CONF', '0.05'))
# limiares vêm do contrato (fonte única) — não manter tabela própria aqui
_CONTRATO = Path(__file__).resolve().parents[2] / 'dataset/TRABALHO/preprocessamento.json'


CLASSES_LIMIAR = ('normal', 'tampa_ausente', 'defeito_tampa', 'deformidade')


def _limiares_do_contrato(imgsz: int) -> dict:
    """Lê os limiares do contrato; recusa imgsz não calibrado (cai para 480, avisando)."""
    try:
        c = json.loads(_CONTRATO.read_text())
        bloco = c['limiares_por_imgsz']
        lim = bloco.get(str(imgsz)) or {}
        if not lim.get('calibrado', False):
            print(f'[contrato] imgsz {imgsz} NÃO calibrado; usando 480 (o calibrado)')
            lim = bloco.get('480') or {}
            if imgsz != 480:
                globals()['IMGSZ'] = 480
                _config['imgsz'] = 480
        # só as classes: `calibrado` é bool e bool é int em Python — não pode entrar
        return {k: float(lim[k]) for k in CLASSES_LIMIAR if isinstance(lim.get(k), (int, float))}
    except Exception as exc:  # noqa: BLE001
        print(f'[contrato] falha lendo limiares ({exc}); usando conservadores')
        return {'normal': 0.30, 'tampa_ausente': 0.15, 'defeito_tampa': 0.15}.copy()


LIMIARES = _limiares_do_contrato(IMGSZ)

app = FastAPI(title='Teste ao vivo — v7a-lateral')
_modelo: YOLO | None = None
_lock = threading.Lock()
_estado = {'frames': 0, 'decisoes': Counter(), 'ultima': None, 'lat_ms': [], 'inicio': time.time()}
_config = {'imgsz': IMGSZ, 'conf': CONF, 'fonte': FONTE}


def _m() -> YOLO:
    global _modelo
    if _modelo is None:
        _modelo = YOLO(PESO)
    return _modelo


PAGINA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Teste ao vivo — v7a-lateral</title>
<style>
 body{background:#141418;color:#e8e8ea;font:14px/1.5 system-ui,sans-serif;margin:0;padding:16px}
 h1{font-size:16px;margin:0 0 10px} .cx{max-width:960px}
 img{width:100%;border-radius:8px;background:#000}
 table{border-collapse:collapse;margin-top:10px} td,th{border:1px solid #333;padding:4px 8px;font-size:13px}
 .ok{color:#5adc8a}.rev{color:#f0be3c}.bad{color:#f05a5a}.dim{color:#9a9aa2}
 .linha{display:flex;gap:16px;align-items:baseline;margin-top:10px;flex-wrap:wrap}
 code{background:#22222a;padding:1px 5px;border-radius:4px}
</style></head><body><div class="cx">
<h1>Teste ao vivo — v7a-lateral <span class="dim">(bancada; não é promoção)</span></h1>
<img src="/stream" alt="câmera com detecção">
<div class="linha">
  <div>decisão agora: <b id="d">—</b></div>
  <div class="dim">limiares: normal 0,30 · tampa_ausente 0,15 · defeito_tampa 0,30</div>
</div>
<div class="linha dim">
  <div id="s">carregando…</div>
</div>
<table><tr><th>imgsz</th><th>conf</th></tr>
<tr><td><a href="/config?imgsz=416">416 (recomendado)</a> · <a href="/config?imgsz=480">480</a> · <a href="/config?imgsz=320">320</a></td>
<td><a href="/config?conf=0.05">0,05</a> · <a href="/config?conf=0.15">0,15</a></td></tr></table>
<p class="dim">Regra do silêncio: se nenhuma caixa passa o limiar da classe, a decisão é
<code>REVISAR</code> — silêncio nunca vira "normal". "Sem peça" é outro estado (vem do gatilho no rig).</p>
</div>
<script>
async function puxa(){
  try{ const r = await fetch('/estado'); const j = await r.json();
    const d = j.ultima_decisao || '—';
    const el = document.getElementById('d'); el.textContent = d;
    el.className = d==='normal' ? 'ok' : (d==='REVISAR' ? 'rev' : 'bad');
    const s = j.resumo;
    document.getElementById('s').textContent =
      `quadros ${s.frames} · fps ${s.fps} · latência mediana ${s.latencia_mediana_ms} ms · `+
      `REVISAR ${s.decisoes.REVISAR||0} · normal ${s.decisoes.normal||0} · tampa_ausente ${s.decisoes.tampa_ausente||0} · defeito_tampa ${s.decisoes.defeito_tampa||0}`;
  }catch(e){}
  setTimeout(puxa, 700);
}
puxa();
</script></body></html>"""


def _anota(frame, caixas, decisao):
    cores = {'normal': (120, 220, 140), 'tampa_ausente': (240, 190, 60), 'defeito_tampa': (90, 90, 240)}
    cor = cores.get(decisao, (200, 200, 200))
    for cl, cf, b in caixas[:4]:
        x1, y1, x2, y2 = [int(v) for v in b]
        c = cores.get(cl, (200, 200, 200))
        cv2.rectangle(frame, (x1, y1), (x2, y2), c, 2)
        cv2.putText(frame, f'{cl} {cf:.2f}', (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, c, 2)
    txt = decisao if decisao != 'REVISAR' else 'REVISAR (nada passou o limiar)'
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 30), (20, 20, 24), -1)
    cv2.putText(frame, f'decisao: {txt}', (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
    return frame


def _gerador():
    modelo = _m()
    cap = cv2.VideoCapture(_config['fonte'])
    if not cap.isOpened():
        return
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.1)
            cap.release()
            cap = cv2.VideoCapture(_config['fonte'])
            continue
        t = time.time()
        r = modelo.predict(frame, imgsz=_config['imgsz'], conf=_config['conf'], verbose=False)[0]
        nomes = r.names or {}
        cand = []
        if r.boxes is not None and len(r.boxes):
            for b, c, k in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy(),
                               r.boxes.cls.cpu().numpy().astype(int)):
                cand.append((nomes.get(int(k), str(k)), float(c), b))
        cand.sort(key=lambda x: -x[1])
        escolhida = next((x for x in cand if x[1] >= LIMIARES.get(x[0], 1.0)), None)
        decisao = escolhida[0] if escolhida else 'REVISAR'
        lat = (time.time() - t) * 1000
        with _lock:
            _estado['frames'] += 1
            _estado['decisoes'][decisao] += 1
            _estado['ultima'] = (decisao, cand[:3])
            _estado['lat_ms'].append(lat)
            _estado['lat_ms'] = _estado['lat_ms'][-120:]
        frame = _anota(frame, cand, decisao)
        ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            continue
        yield (b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' +
               str(len(buf)).encode() + b'\r\n\r\n' + buf.tobytes() + b'\r\n')


@app.get('/', response_class=HTMLResponse)
def raiz():
    return PAGINA


@app.get('/stream')
def stream():
    return StreamingResponse(_gerador(), media_type='multipart/x-mixed-replace; boundary=frame')


@app.get('/estado')
def estado():
    with _lock:
        lat = sorted(_estado['lat_ms'])
        resumo = {
            'frames': _estado['frames'],
            'fps': round(_estado['frames'] / max(1e-6, time.time() - _estado['inicio']), 1),
            'latencia_mediana_ms': round(lat[len(lat) // 2], 1) if lat else None,
            'decisoes': dict(_estado['decisoes']),
        }
        ultima, cands = _estado['ultima'] or (None, [])
    return JSONResponse({'ultima_decisao': ultima,
                         'candidatas': [{'classe': c, 'conf': round(f, 3)} for c, f, _ in cands],
                         'limiares': LIMIARES, 'config': _config, 'peso': PESO, 'resumo': resumo})


@app.get('/config')
def config(imgsz: int | None = None, conf: float | None = None):
    if imgsz:
        _config['imgsz'] = imgsz
        global LIMIARES
        LIMIARES = _limiares_do_contrato(imgsz)
    if conf is not None:
        _config['conf'] = conf
    return JSONResponse(_config)
