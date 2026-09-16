#!/usr/bin/env python3
"""Gera o CONTRATO DE PRE-PROCESSAMENTO que treino e inferencia consomem.

Por que existe: a ROI vivia numa copia manual em cada lado e divergiu (medido: 0,17 de F1 macro entre
treinar com recorte e servir o quadro inteiro). O contrato resolve a classe do problema; este gerador
resolve o contrato -- e ele agora CONFERE o proprio resultado com o consumidor antes de gravar, porque
antes ele emitia um arquivo que o `preparo_detector` recusava (sem `orientacao_entrada`, sem
`vista_por_camera` e com fingerprint de outra lista de campos).

Nada aqui e inventado: classes e `imgsz` vem dos metadados do run, o sha do peso vem do peso, os
limiares vem da calibracao feita NA VALIDACAO, a rotacao e a associacao camera->vista sao DECLARADAS.

Uso:
  gera_contrato_preproc.py --peso PESO.pt --metadados model-meta.json \\
      --roi roi-por-camera.json --calibracao calibracao-limiar.json \\
      --vistas csi=lateral1,usb=lateral2 --rotacao csi=0,usb=90 \\
      [--orientacao quadro_ja_orientado|rotacionar_no_consumo] [--imgsz 480] \\
      [--saida treino/contrato/preprocessamento.json] [--forcar]

Falha (rc=2) quando falta declaracao, quando a calibracao e de outro peso/imgsz, ou quando o contrato
gerado nao passa na validacao do consumidor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE.parent))          # modulos da arvore (preparo_detector/dominio)

from dominio import Vista                                    # noqa: E402
from preparo_detector import (CAMPOS_DO_FINGERPRINT, ContratoDePreprocessamento,  # noqa: E402
                              ErroDePreparo, ORIENTACOES)


def sha256(p: Path) -> str:
    with p.open('rb') as arquivo:
        return hashlib.file_digest(arquivo, 'sha256').hexdigest()


def pares(texto: str, *, nome: str) -> dict[str, str]:
    saida: dict[str, str] = {}
    for parte in texto.split(','):
        parte = parte.strip()
        if not parte:
            continue
        if '=' not in parte:
            raise ValueError(f'{nome}: par sem "=" em {parte!r} (use camera=valor)')
        chave, _, valor = parte.partition('=')
        saida[chave.strip()] = valor.strip()
    if not saida:
        raise ValueError(f'{nome}: declaracao vazia')
    return saida


def limiares_da_calibracao(calibracao: Path, classes: list[str], imgsz: int,
                           peso_sha: str) -> dict:
    """Entrada de `limiares_por_imgsz` para o imgsz do treino, com a fonte declarada."""
    dado = json.loads(calibracao.read_text(encoding='utf-8'))
    escolhidos = dado.get('limiares_escolhidos_na_val') or {}
    if int(dado.get('imgsz', -1)) != imgsz:
        raise ValueError(f'calibracao foi feita em imgsz {dado.get("imgsz")!r}, contrato pede {imgsz}')
    declarado = dado.get('peso')
    if not declarado:
        raise ValueError('calibracao sem o peso de origem: nao ha como saber para qual modelo o limiar vale')
    caminho_do_peso = Path(str(declarado))
    if not caminho_do_peso.is_file():
        raise ValueError(f'peso da calibracao nao existe: {caminho_do_peso}')
    if sha256(caminho_do_peso) != peso_sha:
        raise ValueError('calibracao foi feita para OUTRO peso: limiar nao vale para este')
    faltando = [c for c in classes if c not in escolhidos]
    if faltando:
        raise ValueError(f'calibracao sem limiar para {faltando}')
    entrada = {classe: float(escolhidos[classe]['conf']) for classe in classes}
    entrada['calibrado'] = True
    entrada['fonte'] = f'{calibracao.name}#limiares_escolhidos_na_val'
    entrada['f1_val_por_classe'] = {classe: escolhidos[classe].get('f1_val') for classe in classes}
    return entrada


def montar(*, peso: Path, metadados: Path, roi_json: Path, calibracao: Path | None,
           vistas_texto: str, rotacao_texto: str, orientacao: str, imgsz: int | None) -> dict:
    meta = json.loads(metadados.read_text(encoding='utf-8'))
    classes = list(meta.get('classes') or [])
    if not classes:
        raise ValueError('metadados do run sem classes')
    imgsz = int(imgsz or (meta.get('args') or {}).get('imgsz') or 0)
    if imgsz <= 0:
        raise ValueError('imgsz ausente nos metadados e nao informado')
    roi_dado = json.loads(roi_json.read_text(encoding='utf-8'))
    rois = {cam: v['roi_normalizada'] for cam, v in (roi_dado.get('cameras') or {}).items()
            if v.get('roi_normalizada')}
    if not rois:
        raise ValueError(f'{roi_json.name} sem roi_normalizada por camera')
    rotacoes = {c: int(v) for c, v in pares(rotacao_texto, nome='--rotacao').items()}
    vistas = {c: Vista(v) for c, v in pares(vistas_texto, nome='--vistas').items()}
    if not vistas:
        raise ValueError('--vistas vazio: o contrato precisa das cameras em operacao')
    # o contrato declara as cameras DECLARADAS em --vistas (o runtime tem menos cameras que a tabela)
    sem_roi = sorted(set(vistas) - set(rois))
    if sem_roi:
        raise ValueError(f'camera sem ROI derivada em {roi_json.name}: {sem_roi} '
                         f'(tabela tem {sorted(rois)})')
    rois = {c: rois[c] for c in vistas}
    # declaracao incompleta e erro: a cadeia decide as DUAS laterais; contrato que declara so uma
    # deixaria a outra vista sem recorte e o item cairia em inconclusivo sem ninguem entender por que
    faltando_vistas = sorted(v.value for v in (Vista.LATERAL1, Vista.LATERAL2)
                             if v not in set(vistas.values()))
    if faltando_vistas:
        raise ValueError(f'declaracao incompleta: falta {faltando_vistas} em --vistas '
                         f'(a cadeia decide as duas laterais)')
    sem_rotacao = sorted(set(vistas) - set(rotacoes))
    if sem_rotacao:
        raise ValueError(f'camera sem rotacao declarada em --rotacao: {sem_rotacao}; '
                         f'rotacao NAO se adivinha')
    rotacoes = {c: rotacoes[c] for c in vistas}
    peso_sha = sha256(peso)
    if calibracao is not None:
        limiares = {str(imgsz): limiares_da_calibracao(calibracao, classes, imgsz, peso_sha)}
    else:
        limiares = {str(imgsz): {**{c: None for c in classes}, 'calibrado': False,
                                 'aviso': 'sem calibracao na validacao: o consumidor exige pedido '
                                          'explicito para decidir com limiar provisorio'}}
    contrato = {
        'nome': 'pnaat-preprocessamento',
        'versao': 1,
        'gerado_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'roi_por_camera': rois,
        'rotacao_graus': rotacoes,
        'orientacao_entrada': orientacao,
        'imgsz_treino': imgsz,
        'letterbox': True,
        'classes': classes,
        'limiares_por_imgsz': limiares,
        'modelo': {'arquivo': peso.name, 'sha256': peso_sha, 'tamanho_bytes': peso.stat().st_size},
        'vista_por_camera': {cam: vista.value for cam, vista in vistas.items()},
        'regra_decisao': ('limiar por classe; sem caixa acima do limiar -> REVISAR; '
                          '"sem peca" e estado separado'),
        'observacao': ('gerado por treino/gera_contrato_preproc.py; o fingerprint cobre os campos que '
                       'mudam a predicao e e conferido pelo consumidor antes de decidir'),
    }
    canonico = {campo: contrato[campo] for campo in CAMPOS_DO_FINGERPRINT}
    canonico['modelo_sha256'] = contrato['modelo']['sha256']
    contrato['fingerprint'] = hashlib.sha256(
        json.dumps(canonico, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return contrato


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--peso', required=True, type=Path)
    ap.add_argument('--metadados', required=True, type=Path, help='model-meta.json do run')
    ap.add_argument('--roi', required=True, type=Path, help='roi-por-camera.json')
    ap.add_argument('--calibracao', type=Path, default=None,
                    help='saida do calibra_limiar_val.py (limiar por classe NA VALIDACAO)')
    ap.add_argument('--vistas', required=True, help='camera=vista,camera=vista (ex.: csi=lateral1,usb=lateral2)')
    ap.add_argument('--rotacao', required=True, help='camera=graus,camera=graus (ex.: csi=0,usb=90)')
    ap.add_argument('--orientacao', choices=ORIENTACOES, default='quadro_ja_orientado',
                    help='se a fonte entrega o quadro ja orientado como no treino, ou cru')
    ap.add_argument('--imgsz', type=int, default=None, help='sobrepoe o imgsz dos metadados')
    ap.add_argument('--saida', type=Path, default=PIPELINE / 'contrato' / 'preprocessamento.json')
    ap.add_argument('--forcar', action='store_true', help='sobrescreve contrato existente')
    a = ap.parse_args(argv)

    try:
        contrato = montar(peso=a.peso, metadados=a.metadados, roi_json=a.roi,
                          calibracao=a.calibracao, vistas_texto=a.vistas,
                          rotacao_texto=a.rotacao, orientacao=a.orientacao, imgsz=a.imgsz)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        print(f'BLOQUEADO: {erro}', file=sys.stderr)
        return 2
    if a.saida.exists() and not a.forcar:
        print(f'BLOQUEADO: {a.saida} ja existe; use --forcar para sobrescrever', file=sys.stderr)
        return 2
    # auto-conferencia: quem gera tambem valida, com o MESMO validador do consumidor
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(json.dumps(contrato, ensure_ascii=False, indent=1))
    try:
        aberto = ContratoDePreprocessamento.abrir(
            a.saida)
    except ErroDePreparo as erro:
        a.saida.unlink()
        print(f'BLOQUEADO: contrato gerado nao passa no consumidor: {erro}', file=sys.stderr)
        return 2
    print('contrato:', a.saida)
    print('fingerprint:', contrato['fingerprint'][:32], '…')
    print('modelo sha256:', contrato['modelo']['sha256'][:32], '…')
    print('imgsz:', aberto.imgsz_treino, '| calibrado: sim')
    print('cameras:', ', '.join(f'{c}->{v}' for c, v in contrato['vista_por_camera'].items()))


if __name__ == '__main__':
    sys.exit(main())
