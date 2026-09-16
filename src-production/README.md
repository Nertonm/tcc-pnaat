# src-production — o produto

Pacote `iamralp`. Esta arvore e o **entregavel**: codigo, testes, esquema do hub, firmware, o site
estatico e o pipeline de treino que produz o detector. `../code-workspace/` guarda as PoCs como
historico congelado (nada daqui importa de la; nada de la sobe para ca sem reescrita tipada) e
`revisar/` guarda a arvore de trabalho que originou esta — **nao e importada em runtime**.

## Modulos

| Arquivo | Responsabilidade |
|---|---|
| `dominio.py` | Dominios, vocabulario de classes por dominio (D-28), evidencia tipada e o contrato do evento |
| `decisao.py` | Decisao por vista (D-30): o classificador decide, a geometria e auxiliar, o fallback roteia e nunca aprova |
| `conformidade.py` | Regra por dominio (D-04/D-29): defeito em qualquer vista reprova, aprovacao exige o rig completo, discordancia preservada |
| `captura.py` | Monta as vistas do mesmo `item_id`; verificacao de posicionamento fail-closed (NCC + tolerancia em px) |
| `identidade.py` | Formato e geracao do `item_id` (`<lote>-<sequencia>`), com sequencia ancorada no banco |
| `registro.py` | Persistencia idempotente por `item_id`; recusa evidencia divergente |
| `painel.py` | As 14 consultas analiticas de `docs/dados-telemetria.md` secao 3, somente leitura |
| `orquestracao.py` | Pipeline unica (captura -> decisao -> conformidade -> registro) e entry point |
| `classificador.py` | Classificador da tampa (extrator congelado + linear) atras do protocolo da D-30; CORPO devolve `None` |
| `classificador_artefato.py` | Consumidor do artefato `.npz` medido (D-37) |
| `classificador_yolo.py` | Consumidor do PACOTE de detector (YOLO) na cadeia: contrato verificado, decisao sem silencio |
| `preparo_detector.py` | Pre-processamento do detector: recorte, rotacao e contrato — a MESMA funcao do treino |
| `pacote_detector.py` | Formato do pacote (peso + contrato + metadados + checksums), verificado dos dois lados |
| `fonte_gatilho.py` | Le o CSV de eventos de gatilho da bancada e persiste pela API do registro (RF-01.1) |
| `ingerir_serie.py` | Ingere uma serie de captura do rig como item do registro |
| `mapeamento_rig.py` | Mapa declarado camera -> vista (sem ele a ingestao para) |
| `apresentacao.py` | Relatorio HTML estatico a partir das consultas do painel (o elo 'apresenta') |
| `api.py` | API HTTP do hub; serve o site estatico na mesma origem |
| `esquema.sql` | Esquema do hub, com as invariantes no banco (o topo nunca decide; decidir exige dominio) |

## Frontend do site

O frontend estatico vive em `site/` e e servido pela API na mesma origem. O default de `api.py` aponta
para esse diretorio; use `--site` apenas para sobrescrever o caminho.

## A cadeia de treino, de ponta a ponta

```
anotacao humana (Label Studio)
  -> treino/exporta_anotacoes.py        CSV canonico + recibo de frescor
  -> treino/guarda_frescor.py           aborta se o LS avancou desde o export
  -> treino/monta_v1_detector.py        dataset: split POR ITEM, quase-duplicata (dHash), ROI
  -> treino/treina_v1.py                base limpa externa + ajuste fino no nosso dominio
  -> treino/avalia_por_dominio.py       mAP por dominio e classe
  -> treino/avalia_limiares.py          P/R/F1 por limiar
  -> treino/calibra_limiar_val.py       limiar por classe NA VALIDACAO -> contrato
  -> treino/kfold_por_item.py           metrica de aceitacao (listas disjuntas por item)
  -> treino/pacote_entrega.py           PACOTE: peso + contrato + metadados + checksums
  -> classificador_yolo.py              consome o pacote na cadeia (decide)
  -> orquestracao.py                    captura -> decisao -> conformidade -> registro
  -> painel.py / apresentacao.py / api.py   as consultas e a vitrine
```

O elo treino→inferencia e o **pacote**, verificado dos dois lados:

```text
<pacote>/<peso>.pt             peso torch do detector (nunca desserializado fora do predict)
<pacote>/preprocessamento.json contrato de pre-processamento (ROI/rotacao/imgsz/classes/limiares)
<pacote>/metadados-treino.json model-meta.json do run que produziu o peso
<pacote>/modelo.json           manifesto do pacote (hashes declarados, limitacoes)
<pacote>/SHA256SUMS            inventario fechado
```

## O que faz treino e inferencia serem a MESMA coisa

`preparo_detector.py` e a unica definicao de recorte, rotacao e leitura de contrato; o montador de
dataset e o consumidor da cadeia usam **a mesma funcao**. Antes eram duas regras (PIL no treino,
outra formula na inferencia): medido em 2026-09-15, 1 px de deslocamento e 0,17 de F1 macro.

Campos que o contrato precisa declarar, e por que cada um e guarda:

| Campo | Por que existe |
|---|---|
| `roi_por_camera` | recorte declarado por camera; sem ele o modelo ve outra imagem |
| `rotacao_graus` + `orientacao_entrada` | `quadro_ja_orientado` (a fonte entrega como no treino) ou `rotacionar_no_consumo`. **Ambiguidade e erro**: adivinhar troca 90 por 0 em silencio |
| `vista_por_camera` | qual camera produz qual vista; vista repetida em duas cameras e erro |
| `imgsz_treino` | a resolucao do treino; limiar calibrado em outro tamanho nao vale |
| `limiares_por_imgsz[c].calibrado` + `fonte` | limiar sem fonte e provisorio (D-24) e nao decide sem pedido explicito |
| `classes` | por NOME; a ordem do indice no `.pt` e a identidade da classe |
| `modelo.sha256` | contrato de um peso nao vale para outro |
| `fingerprint` | hash canonico dos campos que mudam a predicao; arquivo editado a mao nao abre |

## Regras de decisao que a cadeia faz valer

- **silencio nunca vira `normal`**: sem caixa acima do limiar da classe, o resultado e `inconclusivo`;
- **defeito nao e suprimido por `normal` mais confiante**: caixa de defeito acima do limiar dela
  decide, mesmo perdendo na confianca;
- `topo` nunca decide (D-23/D-30) e CORPO nao tem modelo neste pacote: devolvem `None` e o `Decisor`
  roteia para fallback;
- aprovacao exige o rig completo (D-04/D-29): sem medida de CORPO o item fica `inconclusivo`, nunca
  `ok`;
- a decisao passa pela **unica** pipeline (`orquestracao.executar`) e chega ao registro com o
  `sha256` do peso e o fingerprint do contrato no campo `metodo`.

## Firmware

`firmware/esp32cam-test/` traz o firmware proprio (fonte, manifest do IDF, parser de transporte e seu
teste). Os vendorizados (`components/esp32-camera/`, `managed_components/`) **nao** sao copiados: o
gerenciador de componentes do ESP-IDF os restaura a partir de `idf_component.yml` +
`dependencies.lock`. Build (`build/`), `sdkconfig` gerado e backups ad-hoc ficam fora.

## Como rodar

```sh
make test                                     # suite completa da arvore
make treino-dataset TAG=v10                   # monta o dataset (split por item + ROI)
make treino-run     TAG=v10 EPOCHS=150         # treina a partir do dataset
make treino-avalia  TAG=v10                    # mAP por dominio + tabela de limiar
make treino-kfold   TAG=v10 K=5                # metrica de aceitacao (k-fold por item)
make pacote PESO=... TAG=v10                   # empacota o candidato (dry-run; --apply grava)
make smoke-detector PACOTE=... CAPTURA=... ITEM=... DB=... JANELA=... ALINHAMENTO=... \
  EQUIPAMENTO=... LOCALIZACAO=...                  # execucao da cadeia com o pacote
make auditar-dataset DATASET=... KFOLD=...     # auditoria adversarial do dataset montado
make treino-run-seguro TAG=v10                 # treino pela porta de recursos (guardiao)
make treino-corpo-dataset && make treino-corpo-run    # frente CORPO (modelo separado)
make auditar-dataset DATASET=... KFOLD=...     # auditoria adversarial do dataset montado
make treino-run-seguro TAG=v10                 # treino pela porta de recursos (guardiao)
make treino-corpo-dataset && make treino-corpo-run    # frente CORPO (modelo separado)
```

Os alvos de treino param com mensagem explicita se `PNAAT_MODELOS` nao existir. Caminhos vem do
ambiente (`PNAAT_MODELOS`, `PNAAT_DADOS`) com default derivado da raiz do clone, sem nome de usuario.

Consumo programatico do pacote:

```sh
../.venv/bin/python orquestracao.py --captura <dir> --item <id> --db hub.db \
    --pacote-modelo /caminho/do/pacote --janela 3600 --alinhamento declarado
```

`--alinhamento declarado` e a atestacao de que o item esta na posicao de captura (bancada ou serie ja
gravada). Sem ela o alinhamento fica `nao_verificado` e **vista nao verificada nao e utilizavel**: o
item sai `inconclusivo` e nada e decidido (fail-closed). Com ela, o registro diz que o alinhamento foi
declarado, nunca que foi medido.

Sem `--pacote-modelo`, a rota legada (`--roi`, artefato `.npz`) continua disponivel; as duas nao se
misturam (`--pacote-modelo` com `--roi` e erro: a ROI da cadeia e a do contrato do pacote).

### Um contrato so: calibrado (nao existe modo provisorio)

O pacote exige limiar **calibrado no `imgsz` de treino**, com a fonte declarada. Nao ha flag que
contorne: o parametro de contrato nao calibrado foi removido do produto inteiro (preparo, classificador,
entry point e gerador), e nao existe alvo de execucao provisoria no Makefile. Contrato sem calibracao
simplesmente nao abre -- e essa e a unica forma de a decisao nunca sair com limiar inventado.

Fechar um pacote, em quatro passos, sem GPU:

```sh
# 1. limiar por classe NA VALIDACAO (protocolo correto; o teste so reporta)
../.venv/bin/python treino/calibra_limiar_val.py --peso PESO.pt \
    --dataset "$PNAAT_MODELOS/<tag>-lateral-detector-roi/dataset" --imgsz 480 \
    --saida "$PNAAT_MODELOS/calibracao-<tag>-val.json"

# 2. contrato: ROI derivada, rotacao e camera->vista declaradas, limiares da calibracao
../.venv/bin/python treino/gera_contrato_preproc.py --peso PESO.pt \
    --metadados "$PNAAT_MODELOS/<tag>-lateral-detector-roi/model-meta.json" \
    --roi treino/contrato/roi-por-camera.json --calibracao "$PNAAT_MODELOS/calibracao-<tag>-val.json" \
    --vistas csi=lateral1,usb=lateral2,espcam=topo --rotacao csi=0,usb=90,espcam=180 \
    --saida treino/contrato/preprocessamento.json --forcar

# 3. pacote (dry-run por padrao; --apply grava)
../.venv/bin/python treino/pacote_entrega.py --peso PESO.pt \
    --contrato treino/contrato/preprocessamento.json \
    --metadados "$PNAAT_MODELOS/<tag>-lateral-detector-roi/model-meta.json" \
    --saida "$PNAAT_MODELOS/ENTREGA/<tag>-lateral" --apply

# 4. execucao da cadeia com o pacote real: TUDO declarado, nada pre-programado
make smoke-detector PACOTE=<dir> CAPTURA=<dir> ITEM=<id> DB=<arquivo> \
    JANELA=<segundos> ALINHAMENTO=<declarado|nao_verificado> EQUIPAMENTO=<nome> LOCALIZACAO=<nome>
```

### ROI por camera: derivada por vista, com gate de saturacao

`treino/roi_por_camera.py` deriva a ROI das caixas anotadas **da vista pedida** (`--vista lateral`, o
padrao). Ate 2026-09-16 ele misturava caixas de `topo` e `lateral` no mesmo envelope: com caixa de topo
(que atravessa o quadro) a ROI derivada virava o quadro inteiro e o script ainda imprimia
`cobertura=1.000 OK`. Agora envelope >= 0,98 nos dois eixos e **SATURACAO**: reprova (rc=3) e so passa
com `--permitir-saturacao`, que existe para o caso legitimo (topo, por construcao).

### Frente CORPO: experimental, com o numero medido

O dataset de corpo e o treino estao na arvore, mas **o modelo nao serve**: medido em 2026-09-15, o
detector de corpo fez `recall = 0,0` nos 8 defeitos do teste (tp=0, fn=8) em todos os limiares, e a
avaliacao de 4 classes saiu vazia (`dominios: {}`). O `model-meta.json` do corpo ainda declara as
classes da TAMPA -- incongruencia que o exportador do pacote ja recusa. Tratar como frente de
experimento, nunca como modelo de decisao, ate haver captura propria de deformidade e nova medicao.

### Runtime do rig: fora do repositorio, de proposito

O runtime do rig (12 arquivos + `SHA256SUMS`, incluindo `roi.json`) nao entra no repositorio: ele
carrega caminho pessoal, host e tabela de ROI da instalacao, e o gate de higiene da propria arvore
bloqueia versionar isso. O arquivo de 2026-09-16 vive FORA do repositorio, no diretorio irmao do clone:
`_fora-do-repo/runtime-rig-20260916/` (com `RECIBO.txt` e `SHA256SUMS`). E
historico: nao e servido, nao e implantado e nao e autoridade para promocao -- o runtime ativo exige o
proprio canario e rollback.

## O que NAO esta verificado

- **Desempenho do detector**: nenhum numero aqui foi medido nesta arvore. O smoke de CPU exercita
  caminho real (peso carrega, classes casam, decide), nao qualidade. Numeros de deteccao saem do
  k-fold do pipeline de treino, em dado real.
- **Peso em uso no rig**: o contrato do pacote precisa ser gerado para o peso medido
  (`treino/calibra_limiar_val.py` + metadados do run). O contrato historico de `v9a` **nao** vale
  para `v9b` — o carregador recusa (sha divergente), de proposito.
- **ROI/rotacao medidos da instalacao atual**: a ROI por camera vem de `treino/roi_por_camera.py`
  (derivada das caixas anotadas) e a rotacao e declarada, nao inferida.

## Fora desta arvore (e por que)

Os nomes abaixo **nao existem nesta arvore** (vivem em `revisar/`, dado de instalacao ou fora do
repositorio) e aparecem aqui so para dizer onde foram parar. Excluidos: os candidatos v0 e
os experimentos pontuais (`monta_v0_*`, `treina_v0_*`, `experimento_*`, `revisao*_drift`, `t3b_split`,
`benchmark_justo`, `otimiza_*`), as filas antigas (`treino/filas/*.sh`, com caminhos da arvore
antiga), o servico de borda (`treino/servico_inferencia3.py`, `site_teste_camera.py`,
`inferencia_camera_teste.py`), o snapshot do rig (`pnaat-vision/`) e os dados de instalacao
(`mapeamento-rig.json`, que e dado do rig, nao do repositorio).
