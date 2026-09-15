# Receita do pipeline de detecção + correções de 2026-09-15

Script da cadeia completa, correções aplicadas e como reproduzir. Os números medidos
estão em `docs/reference/resultados-deteccao-20260915.md`, com o estado de validade de
cada um declarado (dois números do dia foram invalidados e estão marcados lá).

## 1. Correções aplicadas hoje (todas em script versionado)

| defeito | onde | correção |
|---|---|---|
| k-fold usava a MESMA lista em treino e validação (treinava na validação) + arquivos de lista colidiam entre execuções | `kfold_por_item.py` | listas separadas por dobra, diretório único por execução (`mkdtemp`), asserção que aborta se houver imagem nos dois lados |
| pesos iniciais já tinham visto o teste (v1 viu 12 de 18 imagens; v0 tinha 25 imagens nossas) | `treina_v1.py` / filas | base passa a ser pré-treino **só externo** (lista com asserção de 0 imagens nossas); as métricas anteriores ficam marcadas como inválidas |
| imagens do projeto 19 (equipe) nunca entravam: o filtro de classe descartava `classe=deformidade` em silêncio | `monta_v1_detector.py` | classe aceita nas duas montagens; `--com-corpo` cria a 4ª classe `corpo_deformidade`; contagem de descartes por motivo no manifest |
| gate de presença de classe reprovava vistas com menos classes (topo tem 2) | `monta_v1_detector.py` | `--permitir-classe-ausente` rebaixa a gate a aviso, com registro |
| caminho de mídia do Label Studio (`/data/upload/N/…`) não resolvia | `monta_v1_detector.py` | `resolve()` acha o arquivo no volume (nome tem prefixo uuid); `/data/upload/` conta como domínio próprio |
| quase-duplicata cruzando splits (mesma garrafa em séries diferentes) | `monta_v1_detector.py` | agrupamento por hash perceptual (dHash) antes do split; o grupo inteiro vai para o mesmo destino |
| `treina_v1.py` exigia manifest do dataset derivado da `--tag` (quebrava k-fold com tag própria) | `treina_v1.py` | campo do manifest vira opcional |

## 2. A cadeia (ordem exata)

```bash
cd ~/tcc-pnaat/github
PY=./.venv/bin/python

# 0) rótulos: export canônico + trava de frescor (aborta se o Label Studio avançou)
$PY dataset/TRABALHO/exporta_anotacoes.py
$PY dataset/TRABALHO/guarda_frescor.py

# 1) dataset do nosso domínio (split por ITEM + quase-duplicata + ROI)
$PY dataset/TRABALHO/monta_v1_detector.py --vista lateral --roi --somente-dominio \
    --out <diretório de modelos>/<tag>-lateral-detector-roi/dataset
# variantes: --com-corpo (4ª classe), --permitir-classe-ausente (vistas com menos classes)

# 2) base limpa: pré-treino SÓ com dados externos (nunca usa imagem nossa)
$PY dataset/TRABALHO/treina_v1.py --vista lateral --tag ext --roi --epochs 60 --imgsz 480 \
    --data <yaml só-externo> --modelo yolov8n.pt --nome ext-pretreino

# 3) ajuste fino do domínio próprio, a partir da base limpa
$PY dataset/TRABALHO/treina_v1.py --vista lateral --tag <tag> --roi --epochs 150 --imgsz 480 \
    --data <yaml do dataset> --modelo <base limpa>/weights/best.pt --nome <nome>

# 4) avaliação: por domínio, por classe e por limiar (a métrica que a linha usa)
$PY dataset/TRABALHO/avalia_por_dominio.py --dataset <ds> --peso <w> --split test --imgsz 480 \
    --saida <out>/avaliacao-teste.json
$PY dataset/TRABALHO/avalia_limiares.py --dataset <ds> --peso <w> --split test \
    --confs 0.05,0.15,0.30 --imgsz 480 --saida <out>/limiares-teste.json

# 5) evidência visual para a entrega (mosaico + JSON por imagem + acurácia de decisão)
$PY dataset/TRABALHO/evidencia_candidato.py --peso <w> --dataset <ds> --split test \
    --confs 0.15,0.30 --saida <out>

# 6) medida principal: k-fold POR ITEM (teste próprio é pequeno demais sozinho)
$PY dataset/TRABALHO/kfold_por_item.py --dataset <ds> --k 5 --vista lateral --imgsz 480 \
    --epochs 150 --tag <tagk> --modelo <base limpa>
```

Filas que encadeiam tudo sem disputar GPU: `dataset/TRABALHO/filas/fila_limpa.sh`
(base limpa + 3 ajustes finos em paralelo + avaliações + k-fold) e
`dataset/TRABALHO/filas/fila_final.sh` (reconstrói com o rótulo mais novo e repete a cadeia).

## 3. Aumento de dados (offline, com proveniência)

`aumenta_offline.py`: 3× no split de **treino** apenas, dedup por sha256, cada cópia grava
origem + ops + seed no manifest. Ops: brilho ±20%, contraste ±15%, ruído gaussiano, motion
blur leve, re-encode JPEG 85–95, flip horizontal, rotação ±5°. Fora de propósito: hue forte
(cor da tampa é sinal de classe), shear/perspectiva/90° (câmera fixa), rotação grande.

## 4. Regras que não podem ser quebradas (aprendidas na marra)

1. Nada de métrica sem lista de treino e validação **separadas e verificadas**.
2. Nenhum peso que já viu o teste pode ser base de avaliação — base limpa ou nada.
3. Split por item **e** quase-duplicata: sha256 sozinho não protege.
4. Descarte de item no montador tem que ser **contado por motivo** — descarte silencioso já
   escondeu 16 imagens anotadas.
5. Limiar se escolhe em validação, nunca no teste.

## 5. Artefatos e hashes

```
docs/reference/resultados-deteccao-20260915.md   relatório do dia (números + validade)
dataset/TRABALHO/anotacoes-ls.csv                export canônico (recibo com fingerprint do LS)
<diretório de modelos>/<tag>/model-meta.json peso + sha256 + métricas + dataset + seed
```
