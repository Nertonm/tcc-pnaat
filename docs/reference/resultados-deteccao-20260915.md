# Detecção de estado de tampa — resultados medidos (2026-09-15)

Relatório técnico do dia. Todo número vem de execução real e traz o **estado de validade**
declarado. O que ainda não rodou está marcado como **pendente** (não há estimativa
apresentada como medida).

## 0. Correção de integridade (auditoria de 2026-09-15)

Três defeitos foram encontrados depois das primeiras medições do dia. Dois invalidavam
número; o terceiro escondia dado de treino. Todos foram corrigidos, e as medições
afetadas estão marcadas como inválidas — não foram reaproveitadas.

1. **Validação cruzada inválida.** O script de k-fold usava o MESMO arquivo de lista em
   treino e validação, então treinava na validação; os arquivos de lista ainda colidiam
   entre execuções simultâneas. Correção: listas separadas, diretório único por execução e
   asserção que aborta se qualquer imagem aparecer nos dois lados. **Resultados descartados.**
2. **Contaminação dos pesos iniciais.** Os pesos usados como base do ajuste fino já tinham
   visto parte do teste: o `v1` viu **12 das 18 imagens** do teste atual e o `v0` inclui
   25 imagens `nosso`. Nenhum peso existente é limpo para esse teste. Correção: a base passa
   a ser um **pré-treino exclusivamente externo** (2.994 imagens, 0 do nosso domínio,
   verificado por asserção na lista). **As medições "0,969" e "0,797" ficam inválidas como
   estimativa de generalização.**
3. **Imagens dos colegas descartadas em silêncio.** As 16 imagens do projeto 19 (9 de
   deformidade de corpo, 7 de tampa mal rosqueada) nunca entraram em treino: o filtro de
   classe do montador usava a lista de 3 classes e descartava as linhas `classe=deformidade`
   sem aviso. Correção: a classe é aceita nas duas montagens. Efeito medido no ensaio:
   domínio próprio de **125 → 137 imagens**, anotações humanas de **168 → 180**, e a classe
   `corpo_deformidade` de 6 → ~15 instâncias de treino.

## 1. Corpus e origem do dado

```
Label Studio: 37.200 imagens em 12 projetos
  dataset/externo       22.268  (3 datasets Roboflow do workspace thiago-nerton-macedo-alves, CC BY 4.0)
  dataset/benchmark      6.612  (MVTec AD — teste fora de domínio, fora do treino por decisão registrada)
  dataset/derivado       4.559  (classificação por pasta)
  dataset/anotacao       3.145
  corpus capturas          301  (CSI topo · USB lateral · ESP-CAM lateral)
  dataset/nosso            124  (rig: frames + tampa: mal_rosqueada/ausente/deformidade)
  uploads da equipe         16  (projeto 19 — passaram a entrar em 2026-09-15, ver §0.3)
anotações humanas submetidas: 180+ (p3 · p11 · p13 · p14 · p19)
  rascunhos não submetidos não entram no export canônico
```

## 2. Protocolo (o que garante que o número vale)

1. **Split por ITEM**, não por imagem: frames vizinhos são a mesma garrafa.
2. **Quase-duplicata por hash perceptual (dHash)**: a mesma cena em séries diferentes cai no
   mesmo split. O sha256 (usado antes) só pega cópia exata — a revisão achou 3 grupos
   cruzando splits (2 de `tampa_ausente`, 1 de espcam) que o sha256 não via.
3. **Base limpa**: pré-treino só com dados externos; ajuste fino no nosso treino. Nenhuma
   imagem do nosso teste participa, direta ou indiretamente.
4. **ROI por câmera** derivada das caixas anotadas (cobertura 1,000): csi 0,573×0,512 ·
   usb 0,756×0,455 · espcam 0,834×1,000.
5. **Exclusão respeitada**: `excluir_do_treino`/`imagem_ruim` fora do treino.
6. **Trava de frescor**: o montador aborta se o Label Studio avançou desde o export
   canônico — foi ela que detectou os rótulos novos que a equipe submeteu durante o dia.
7. **Acordo entre anotadores**: 8 tarefas com 2+ anotações, 8 concordam (100%).
8. **k-fold por item** (5 dobras) como medida principal: o teste próprio é pequeno demais
   para sustentar conclusão sozinho.

## 3. Resultados

**Todos os números da tabela abaixo estão marcados quanto à validade.** Os válidos são os
que usam split por item + quase-duplicata + base limpa.

| configuração | teste | mAP50 | mAP50-95 | validade |
|---|---|---|---|---|
| só-domínio, 320px | 23 imgs (split antigo) | 0,837 | 0,395 | parcial (split com quase-duplicata) |
| só-domínio, 640px | 23 imgs (split antigo) | 0,921 | 0,444 | parcial (split com quase-duplicata) |
| misto (externo + 5× domínio) | 23 imgs (split antigo) | 0,946 | 0,498 | parcial (split com quase-duplicata) |
| misto + ajuste fino | 23 imgs (split antigo) | 0,969 | 0,542 | **INVÁLIDA** (base viu 12/18 do teste) |
| misto + ajuste fino | 18 imgs (split corrigido) | 0,797 | 0,412 | **INVÁLIDA** (base contaminada) |
| **base limpa + ajuste fino, 3 classes (v5)** | 18 imgs | **0,695 / 0,995 / 0,636** (normal/ausente/defeito) | 0,254 / 0,474 / 0,267 | **VÁLIDA** |
| base limpa + ajuste fino, 4 classes (v4) | 18 imgs | 0,500 / 0,600 / 0,727 / 1,000 (deformidade) | — | válida (com 1 instância de deformidade no teste) |

**Topo — modelo treinado só com KMITL (2 classes), medido nas nossas 40 capturas:**

| entrada | acurácia | normal | tampa_ausente |
|---|---|---|---|
| frame inteiro | 0,725 | 26/26 | 3/14 |
| com ROI | 0,675 | 24/26 | 3/14 |

Recall de `tampa_ausente` = 21%: o mAP50 0,995 declarado no KMITL não transfere. Mesma
receita indicada (KMITL → ajuste fino nas nossas capturas).

**Tabela de limiar por classe (modelo v3, inválido para generalização mas válido para
mostrar o trade-off do limiar baixo):**

| limiar | classe | P | R | F1 |
|---|---|---|---|---|
| 0,05 | normal / tampa_ausente / defeito_tampa | 0,24 / 0,29 / 0,28 | 0,80 / **1,00** / **1,00** | 0,36 / 0,45 / 0,44 |
| 0,15 | normal / tampa_ausente / defeito_tampa | 0,75 / 0,60 / 0,36 | 0,60 / **1,00** / **1,00** | 0,67 / 0,75 / 0,53 |
| 0,30 | normal / tampa_ausente / defeito_tampa | 1,00 / 1,00 / 0,50 | 0,40 / 0,56 / **1,00** | 0,57 / 0,71 / 0,67 |

Leitura: em 0,15 as duas classes de defeito ficam com recall 100%; em 0,30 a precisão vai a
1,00 e o recall de `tampa_ausente` cai para 0,56. Para linha de produção (perder defeito
custa mais que alarme falso), o ponto útil é 0,15.

**Estresse fora de domínio (MVTec, detector v0):** FPR em imagens boas — bottle 100%,
pill 100%, metal_nut 86%, hazelnut 73%; AUROC ≈ 0,48. Uso correto: gate de promoção
(FPR não pode subir), não métrica de acuidade.


## 3b. Métrica de DECISÃO (a que a linha de produção usa)

Além do mAP de caixa, mede-se a decisão por imagem (caixa de maior confiança). No teste do
candidato v3 (base ainda contaminada — número a reconfirmar no candidato limpo):

| limiar | acurácia da decisão | observação |
|---|---|---|
| 0,15 | **17/18 = 0,944** | único erro: um `normal` dito `defeito_tampa` |
| 0,30 | 12/18 = 0,667 | as 5 falhas são silêncio (sem caixa acima do limiar), não erro de classe |

Leitura: a precisão de caixa baixa vem de caixas duplicadas/extras na mesma peça, não de
decisão errada. Para a linha, o limiar escolhe entre cobertura (0,15) e silêncio (0,30) —
não entre acerto e erro. Artefatos: mosaico com caixas e rótulos por imagem
(`evidencia-*.png`) e JSON por imagem (`evidencia-*.json`), gerados por
`dataset/TRABALHO/evidencia_candidato.py`.


## 3c. Candidato de base limpa — medido (2026-09-15, tarde)

Protocolo válido: split por item + quase-duplicata, base = pré-treino só externo, ajuste
fino no nosso treino (96 imagens / 52 itens), 480 px.

**3 classes (v5) — teste próprio, 18 imagens:**

| classe | mAP50 | mAP50-95 |
|---|---|---|
| normal | 0,695 | 0,254 |
| tampa_ausente | **0,995** | 0,474 |
| defeito_tampa | 0,636 | 0,267 |

**Tabela de limiar do candidato limpo (a decisão prática):**

| limiar | F1 macro | normal P/R | tampa_ausente P/R | defeito_tampa P/R |
|---|---|---|---|---|
| 0,05 | 0,525 | 0,43 / 0,60 | 0,32 / **1,00** | 0,42 / **1,00** |
| 0,15 | 0,692 | 0,60 / 0,60 | 0,47 / **1,00** | 0,71 / **1,00** |
| **0,30** | **0,806** | 0,75 / 0,60 | 0,60 / **1,00** | **1,00 / 1,00** |

Leitura: no candidato limpo o ponto útil é **0,30** (não 0,15 como no modelo contaminado):
as duas classes de defeito ficam com recall 1,00 e `defeito_tampa` chega a precisão 1,00.

**4 classes (v4), com `corpo_deformidade` como 4ª classe:**

| limiar | F1 macro | deformidade (tp/fp/fn) | custo observado |
|---|---|---|---|
| 0,15 | 0,733 | 1 / 0 / 0 | — |
| 0,30 | 0,794 | 1 / 0 / 0 | `defeito_tampa` cai de 1,00 para 0,727 de F1 |

A 4ª classe **funciona como sinal** (a única instância do teste foi detectada sem falso
positivo nos dois limiares), mas custa ~0,27 de F1 em `defeito_tampa` no limiar 0,30.
Com 1 instância no teste isso é indício, não garantia: a decisão de manter `deformidade`
no escopo precisa de mais anotação de corpo (o piso é ~20 por split).

**Impacto medido da contaminação:** o modelo com base contaminada dava 0,797 de mAP50 médio
no mesmo teste; o candidato limpo tem média por classe ≈0,775. A inflação existia, mas era
pequena (~0,02). O número realmente inflado foi o do split antigo (0,969), que além da base
contaminada também tinha quase-duplicata cruzando treino e teste.

**Topo (t5, ajuste fino a partir do KMITL):** não transfere. No teste de 2 imagens o modelo
emitiu ~35 caixas por imagem (F1 macro 0,018). O topo **não está validado** — o caminho é
captura e anotação de topo próprias antes de qualquer uso; o número de 0,675/0,725 medido
antes (KMITL puro) já indicava isso.


## 3d. Camada de decisão operacional (medida no candidato)

O detector não decide sozinho: ele emite caixas. A decisão é uma política, e ela foi medida
(`dataset/TRABALHO/decisao_operacional.py`) com **limiar por classe** e **regra do silêncio**
(nada passa acima do limiar → REVISAR, nunca "normal").

Limiares em uso: `normal` 0,30 · `tampa_ausente` 0,15 · `defeito_tampa` 0,30 · `deformidade` 0,60.

| resultado | valor |
|---|---|
| imagens | 18 |
| acerto automático | 10 (0.556) |
| encaminhadas para REVISAR | 6 |
| acurácia **sem contar as de revisão** | 0.833 |

Confusão (verdade → decisão):

```
  tampa_ausente    -> {'tampa_ausente': 5, 'REVISAR': 4}
  normal           -> {'normal': 2, 'defeito_tampa': 2, 'REVISAR': 1}
  defeito_tampa    -> {'defeito_tampa': 3, 'REVISAR': 1}
```

**O ponto que importa:** nenhuma peça com defeito foi decidida como "normal". Os quatro casos
de `tampa_ausente` em que o modelo ficava **calado** (sem caixa acima do limiar) passam a
REVISAR; o único par de erros restante são dois alarmes falsos em peças normais (0,878 e 0,662
de confiança). Em linha de inspeção isso é o trade-off certo: silêncio deixa de ser aprovação.

| limiar | F1 macro |
|---|---|
| 0,05 | 0.524 |
| 0,15 | 0.711 |
| 0,30 | 0.605 |

Origem: `decisao-operacional.json` sha256 `259afa47490d3263` ·
`limiares-teste.json` sha256 `d999a1e0cf319abf`.


## 3e. Números finais do dia (candidato v6a/v7a)

**Métrica de aceitação — k-fold por item, 5 dobras, mesmo protocolo de entrega:**

| métrica | média ± desvio | faixa |
|---|---|---|
| mAP50 | **0.6708 ± 0.1487** | 0.5123–0.9187 |
| mAP50-95 | 0.2743 ± 0.1018 | 0.1718–0.4414 |
| precision | 0.7205 ± 0.1667 | — |
| recall | 0.6621 ± 0.1228 | — |

O mesmo protocolo, executado duas vezes, devolveu **o mesmo valor** (seed fixa, determinístico):
o pipeline é reprodutível e o número não é sorte de rodada. As listas de cada dobra ficam em
`<dataset>/kfold-listas/kfv7/` e a checagem de disjunção passou (interseção 0).

**A/B do aumento offline (3× no treino) — NÃO ajudou:**

| modelo | F1 macro @0,05 | @0,15 | @0,30 |
|---|---|---|---|
| candidato (sem aumento) | 0.524 | **0.711** | 0.605 |
| com aumento 3× | 0.496 | 0.550 | 0.686 |

Veredito: **manter sem aumento**. No ponto de operação (0,15) o braço aumentado perde ~0,16 de
F1; a hipótese de que mais cópias ajudariam não se confirmou neste conjunto. Resultado negativo
registrado — vale tanto quanto um positivo, porque evita trabalho futuro repetido.

**Gate fora de domínio (MVTec, 83 imagens de `bottle`):** AUROC de imagem =
**0.500** (20 boas, 63 com defeito). Em nível de acaso:
fora do nosso domínio o modelo não separa nada. Uso correto = **gate de promoção** (não pode
subir), nunca métrica de acuidade nem uso em objeto de fora.

**Topo:** val mAP50 = 0,035 — declarado **fora de escopo** até haver captura e anotação de topo
próprias.

Origem: `kfold-*.json` sha `f3593c2a3c1f0486` ·
`v7aug/limiares-teste.json` sha `f0fdccc827828447` ·
`ood-mvtec.json` sha `5fc3a93f09f8531d`


## 3f. Teste ao vivo na câmera do host (bancada, 2026-09-15T17:00:24+00:00)

Executado **sem tocar** no serviço que detém o V4L2: a leitura veio do MJPEG que ele já publica
(o próprio serviço declara, no cabeçalho, ser o leitor único do device — então ler o stream é o
uso previsto, não uma segunda abertura do device).

| item | valor |
|---|---|
| fonte | stream local (1280×720) |
| quadros processados | 250 (25 s) + 101 (10 s, com quadros salvos) |
| latência por quadro | mediana **5.9 ms** (min 5.2 / max 1858.2 no primeiro) |
| decisões | {'REVISAR': 101} — nada passou do limiar |
| candidatas no nível cru (conf 0,05) | 30 de 101 quadros; confiança máxima **0,109** |

Leitura honesta:

1. **O encanamento roda ao vivo** — câmera → modelo → limiar por classe → decisão → evidência,
   a 5.9 ms por quadro. Ordem de grandeza suficiente para a linha.
2. **Sem alucinação em cena desconhecida** — a maior confiança em 101 quadros foi 0,109, ou seja
   piso de ruído: zero alarme falso fora do domínio, no mundo real (o MVTec dava AUROC 0,5 nesse
   tipo de pergunta; aqui a resposta é "não inventa").
3. **Não é medida de acurácia** — não havia peça em vista e não existe a ROI por câmera do rig
   neste contexto. O que este teste valida é runtime e comportamento na ausência de alvo.
4. **Achado que só aparece rodando:** cena VAZIA caiu em REVISAR. Presença de peça é informação do
   gatilho/item no rig; no pipeline final, "sem peça" precisa ser estado próprio, distinto de
   "peça presente e incerta". A regra do silêncio vale para o segundo caso, não para o primeiro.

Artefatos: `dataset/TRABALHO/inferencia_camera_teste.py` (teste de bancada, com `--url` ou
`--camera`) · quadros anotados e resumo em `/var/tmp/teste-camera/` no host de treino (uma cópia
do quadro e do resumo foi puxada para uma maquina separada).


## 3g. Otimização para a borda — medida, não presumida

Três caminhos testados no candidato, todos no MESMO teste de 18 imagens. A latência da borda é
medida em **CPU** (é o que a linha tem); a do host, na GPU, aparece só como referência.

| formato | tamanho | mAP50 | latência CPU (mediana) | paridade de caixas (IoU≥0,5) |
|---|---|---|---|---|
| torch (fp32) | 6.23 MB | 0.6261 | 37.1 ms | referência |
| ONNX fp32 | 12.19 MB | 0.4713 | 46.1 ms | 16/18 = 0.889 |
| ONNX INT8 | 3.32 MB | 0.4897 | 72.4 ms | 15/18 = 0.833 |
| torch na GPU (referência) | 6.23 MB | — | 7,6 ms | — |

**O export não compensou.** Na CPU as duas variantes ONNX ficaram mais lentas que o torch e cerca
de 0,14 de mAP50 abaixo, com paridade de caixas de 83–89% (ou seja: o export muda a predição, não
só o formato). O único ganho é tamanho de arquivo (INT8 = metade), que não é restrição neste
problema. **Decisão medida: manter torch** — exportar aqui seria complexidade que perde.

**O ganho real está na resolução de entrada** (torch, CPU, mesmas 18 imagens):

| imgsz | mAP50 | latência CPU | ganho de latência | perda de mAP50 |
|---|---|---|---|---|
| 320 | 0.5761 | ~20 ms | +58% | -0,0500 |
| **416** | **0.6047** | ~30 ms | **+39%** | **-0,0214** |
| 480 (atual) | 0.6261 | 48,7 ms | — | — |

**Recomendação para a borda: `imgsz=416`** — corta ~39% do tempo por quadro pagando 0,021 de mAP50
(~3% do valor), dentro da tolerância declarada de 0,03. Se a linha exigir mais folga, 320 dobra a
economia a um custo já visível (0,05).

Scripts: `dataset/TRABALHO/otimiza_modelo.py` (export + paridade + latência),
`dataset/TRABALHO/benchmark_justo.py` (CPU x CPU, com paridade de caixas),
`dataset/TRABALHO/otimiza_imgsz.py` (acurácia x latência por resolução).

## 4. Aumento de dados e preprocessing

- **Offline** (`aumenta_offline.py`, equivale ao "dataset version" do Roboflow): 3× no split
  de **treino**, dedup por sha256, proveniência por cópia (origem, ops, seed). Ops: brilho
  ±20%, contraste ±15%, ruído, motion blur leve, JPEG 85–95, flip, rotação ±5°.
  Fora de propósito: hue forte (cor da tampa é sinal), shear/perspectiva/90° (câmera fixa).
- **On-the-fly** (Ultralytics, mantido): mosaic 1,0 · close_mosaic 10 · mixup 0,03 ·
  copy_paste 0,3 · erasing 0,4 · scale 0,4 · fliplr 0,5 · flipud 0.
- **Box-level sem premium**: recorte da caixa da tampa colado em fundo do próprio rig.
- **Preprocessing**: captura com exposição/ganho/WB travados, luz difusa sem cintilação,
  exposição curta; depois derotação → ROI → letterbox preservando proporção, o mesmo
  pipeline em treino e inferência, com as constantes amarradas ao modelo.

**Pendências declaradas:** k-fold de 5 dobras por item (em execução na hora de fechar
este texto) para o candidato v5; FPR fora de domínio (MVTec) do candidato limpo; evidência
visual (mosaico + JSON por imagem) do candidato limpo; reconstrução v6 com as imagens do
projeto 19 (equipe) já incluídas, que é o dado mais novo do dia.

## 5. Limitações (declarar, não esconder)

1. Teste próprio pequeno (13–18 itens) → ±10 pontos; por isso o k-fold por item é a medida
   principal. Números por classe com 1–5 instâncias não sustentam conclusão.
2. mAP50-95 ≈ 0,41–0,54: a caixa está frouxa (tampa pequena). A decisão de classe é melhor
   que a localização.
3. O detector lateral treina classes de tampa; `corpo_deformidade` entra como 4ª classe
   **experimental**, com ~15 instâncias — a medir com limiar baixo e métrica declarada.
4. Heterogeneidade de câmera: ESP-CAM (640×480 JPEG) e USB (720×1280) são domínios distintos.
5. Dado próprio é o gargalo; o piso documentado é 20–50 por classe **por split**.
6. FPR OOD do modelo de hoje não foi medido: o gate MVTec precisa rodar de novo no candidato.

## 6. Reprodutibilidade

```
dataset/TRABALHO/monta_v1_detector.py      split por item + quase-duplicata + ROI + trava de frescor
dataset/TRABALHO/exporta_anotacoes.py      export canônico + recibo com fingerprint do Label Studio
dataset/TRABALHO/treina_v1.py              treino com args versionados (tag por experimento)
dataset/TRABALHO/avalia_por_dominio.py     avaliação separada por domínio
dataset/TRABALHO/avalia_limiares.py        precisão/recall/F1 por classe em vários limiares
dataset/TRABALHO/kfold_por_item.py         validação cruzada por item (listas separadas, disjunção verificada)
dataset/TRABALHO/aumenta_offline.py        aumento offline com proveniência
dataset/TRABALHO/avaliacao_ood.py          estresse fora de domínio (MVTec, em src-production/)
saídas: <diretório de modelos>/<tag>-<vista>-detector-roi/{dataset,runs,model-meta.json,avaliacao-*.json,limiares-*.json}
```

## 7. Próximo passo com gatilho

```
+ rótulo próprio        -> re-export -> montador (trava de frescor) -> ajuste fino -> k-fold
+ captura no rig        -> mesma cadeia (único item que muda o dado estruturalmente)
promoção                -> só com: k-fold por classe, FPR OOD medido, canário no rig, teste próprio
```
