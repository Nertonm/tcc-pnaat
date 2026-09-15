#!/usr/bin/env python3
"""Teste de bancada: inferência ao vivo na câmera do host, com a decisão operacional.

O que é e o que NÃO é:
  - É teste de ENCANAMENTO: câmera -> modelo v7a -> limiar por classe -> decisão -> evidência.
  - NÃO é medida de acurácia: a webcam do host não tem garrafa, não tem a ROI do rig e tem
    outra lente/luz. O número que sai daqui vale para provar que a cadeia roda ao vivo.

Regras aplicadas (as mesmas da entrega):
  - conf baixa (0.05) para ver tudo que o modelo oferece
  - decisão pelo limiar DA CLASSE; se nada passa -> REVISAR (silêncio nunca vira "normal")
  - sem ROI: o rig aplica ROI por câmera, aqui não existe — declarado na saída

Uso: python inferencia_camera_teste.py --camera 1 --segundos 20 --peso <v7a/best.pt> [--salvar N]
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
from ultralytics import YOLO

VERDE, VERMELHO, AMBAR, BRANCO = (90, 220, 120), (240, 90, 90), (240, 190, 60), (235, 235, 235)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--camera', type=int, default=0)
    ap.add_argument('--url', default=None,
                    help='fonte HTTP (ex.: http://127.0.0.1:8099/stream.mjpg); se dada, ignora --camera')
    ap.add_argument('--segundos', type=float, default=20.0)
    ap.add_argument('--peso', required=True)
    ap.add_argument('--imgsz', type=int, default=480)
    ap.add_argument('--conf', type=float, default=0.05)
    ap.add_argument('--limiares', default='normal=0.30,tampa_ausente=0.15,defeito_tampa=0.30,deformidade=0.60')
    ap.add_argument('--salvar', type=int, default=5, help='salva 1 a cada N frames')
    ap.add_argument('--saida', default='/var/tmp/teste-camera')
    a = ap.parse_args()

    limiares = {}
    for parte in a.limiares.split(','):
        k, _, v = parte.partition('=')
        limiares[k.strip()] = float(v)

    destino = Path(a.saida)
    destino.mkdir(parents=True, exist_ok=True)
    modelo = YOLO(a.peso)

    fonte = a.url if a.url else a.camera
    cap = cv2.VideoCapture(fonte)
    if not cap.isOpened():
        print(f'FALHA: fonte {fonte} nao abriu')
        return 2
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f'fonte {fonte}: {largura}x{altura} | modelo {a.peso}')

    decisões: list[str] = []
    latencias: list[float] = []
    por_frame = []
    t0 = time.time()
    n = 0
    while time.time() - t0 < a.segundos:
        ok, frame = cap.read()
        if not ok:
            print('FALHA: frame nao lido'); break
        n += 1
        t = time.time()
        r = modelo.predict(frame, imgsz=a.imgsz, conf=a.conf, verbose=False)[0]
        latencias.append((time.time() - t) * 1000)
        nomes = r.names or {}
        cand = []
        if r.boxes is not None and len(r.boxes):
            for b, c, k in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy(),
                               r.boxes.cls.cpu().numpy().astype(int)):
                cand.append((float(c), nomes.get(int(k), str(k)), b))
        cand.sort(key=lambda x: -x[0])
        escolhida = next(((cl, b) for c, cl, b in cand if c >= limiares.get(cl, 1.0)), None)
        decisao = escolhida[0] if escolhida else 'REVISAR'
        decisões.append(decisao)

        if n % a.salvar == 0:
            # salva COM ou SEM detecção: sem isso não há evidência visual do que a câmera viu
            cor = VERDE if decisao == 'normal' else (AMBAR if decisao == 'REVISAR' else VERMELHO)
            if escolhida is not None:
                x1, y1, x2, y2 = [int(v) for v in escolhida[1]]
                cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2)
                cv2.putText(frame, decisao, (x1, max(20, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
            else:
                cv2.putText(frame, 'sem deteccao (REVISAR)', (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
            cv2.imwrite(str(destino / f'frame-{n:04d}-{decisao}.jpg'), frame)
        por_frame.append({'frame': n, 'decisao': decisao,
                          'candidatas': [{'classe': cl, 'conf': round(c, 3)} for c, cl, _ in cand[:3]]})
    cap.release()

    resumo = {
        'quando': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'fonte': str(fonte), 'resolucao': [largura, altura], 'peso': a.peso,
        'imgsz': a.imgsz, 'conf': a.conf, 'limiares': limiares,
        'roi': None, 'frames': n, 'segundos': round(time.time() - t0, 1),
        'decisoes': {d: decisões.count(d) for d in sorted(set(decisões))},
        'latencia_ms': {'min': round(min(latencias), 1), 'mediana': round(statistics.median(latencias), 1),
                        'max': round(max(latencias), 1)} if latencias else {},
        'por_frame': por_frame,
    }
    (destino / 'resumo-teste-camera.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=1))

    print(f"\nframes: {n} em {resumo['segundos']}s | latencia mediana {resumo['latencia_ms'].get('mediana')} ms")
    print('decisões:', resumo['decisoes'])
    print('quadros salvos:', len(list(destino.glob('frame-*.jpg'))))
    print('resumo:', destino / 'resumo-teste-camera.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
