#!/usr/bin/env python3
"""Gera o CONTRATO DE PRÉ-PROCESSAMENTO — a fonte única que capture, treino e deploy consomem.

Por que existe (achado de 2026-09-15): a ROI vivia numa cópia manual em cada lado e divergiu —
treino recortava 0,573×0,512, deploy usava quadro inteiro. Custo medido: 0,17 de F1 macro.
Consertar a cópia resolve hoje; o contrato resolve a classe do problema.

O que o contrato carrega (o que TREINO e INFERÊNCIA têm de fazer igual, senão o número mente):
  - rotação por câmera            (hoje hardcoded nos dois lados: usb 90, espcam 180)
  - ROI normalizada por câmera    (hoje copiada à mão)
  - imgsz de treino               (mudar invalida os limiares — medido)
  - ordem e nomes das classes     (a ordem É a identidade do índice no .pt)
  - limiares por classe, POR imgsz (um limiar calibrado a 480 não vale a 416)
  - sha256 do modelo

E um `fingerprint`: hash canônico dos campos que afetam a predição. Quem consome compara o
fingerprint ANTES de rodar; divergência = falha alta, não degradação silenciosa.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

G = Path(__file__).resolve().parents[2]
M = G.parent.parent / 'pnaat-modelos'

roi_src = json.loads((G / 'dataset/TRABALHO/roi-por-camera.json').read_text())
pkg = M / 'ENTREGA/v7a-lateral'

# rotações: hoje hardcoded em /opt/pnaat-vision/app.py e no bridge do ESP. Aqui viram contrato.
ROTACAO = {'csi': 0, 'usb': 90, 'espcam': 180, 'rig': 0, 'desconhecida': 0}

# limiares POR imgsz: 480 é o calibrado; 416 NÃO está calibrado (medido: o mesmo limiar rende
# 0,590 em vez de 0,711). Marcar como não calibrado é o honesto — o consumidor decide falhar.
LIMIARES = {
    '480': {'normal': 0.30, 'tampa_ausente': 0.15, 'defeito_tampa': 0.30, 'calibrado': True},
    '416': {'normal': None, 'tampa_ausente': None, 'defeito_tampa': None, 'calibrado': False,
            'aviso': 'não calibrado neste imgsz; recalibrar na val (idealmente no k-fold) antes de usar'},
}

contrato = {
    'nome': 'pnaat-preprocessamento',
    'versao': 1,
    'gerado_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'roi_por_camera': {c: v['roi_normalizada'] for c, v in roi_src['cameras'].items()
                       if v.get('roi_normalizada')},
    'rotacao_graus': ROTACAO,
    'imgsz_treino': 480,
    'letterbox': True,
    'classes': ['normal', 'tampa_ausente', 'defeito_tampa'],
    'limiares_por_imgsz': LIMIARES,
    'modelo': {
        'arquivo': 'v7a-lateral.pt',
        'sha256': None,
        'tamanho_bytes': None,
    },
    'regra_decisao': 'limiar por classe; sem caixa acima do limiar -> REVISAR; "sem peça" é estado separado',
    'observacao': ('consome este arquivo em vez de manter cópia local; '
                   'compare o campo fingerprint antes de rodar'),
}
if (pkg / 'v7a-lateral.pt').is_file():
    h = hashlib.sha256((pkg / 'v7a-lateral.pt').read_bytes()).hexdigest()
    contrato['modelo']['sha256'] = h
    contrato['modelo']['tamanho_bytes'] = (pkg / 'v7a-lateral.pt').stat().st_size

# fingerprint: só o que muda a predição (não a data, não o nome do arquivo)
canonico = {k: contrato[k] for k in ('roi_por_camera', 'rotacao_graus', 'imgsz_treino',
                                     'letterbox', 'classes', 'regra_decisao')}
canonico['modelo_sha256'] = contrato['modelo']['sha256']
contrato['fingerprint'] = hashlib.sha256(
    json.dumps(canonico, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

destino = G / 'dataset/TRABALHO/preprocessamento.json'
destino.write_text(json.dumps(contrato, ensure_ascii=False, indent=1))
print('contrato:', destino)
print('fingerprint:', contrato['fingerprint'][:32], '…')
print('modelo sha256:', (contrato['modelo']['sha256'] or 'ausente')[:32], '…')
