# Adaptação do yolo-edge-api para as PoCs de classificação e deformidade

Documento de trabalho, local (não entra no versionado). Orienta a reutilização do projeto
`yolo-edge-api` (Aula 6) nas PoCs do TCC: **PoC-02 (classificação de tampa)** e **PoC-03 (deformidade
lateral)**, usando os dados públicos que já estão no disco.

## 1. O que o yolo-edge-api é, e o que dele interessa

Verificado em `~/yolo-edge-api`:

| Peça | Arquivo | Serve para nós? |
|---|---|---|
| Treino | `train_epi.py` (Ultralytics; `epochs=100`, `imgsz=640`, `patience=20`, `device=0`; patch de `torch.load` com `weights_only=False`) | Sim, como molde |
| Gate | `scripts/validate_model.py` (bloqueia se mAP@0.5 < 0.60) | Só o **padrão** de bloquear; a métrica muda |
| CI/CD | `.github/workflows/edge-deploy.yml` (lint e testes, build ARM64, gate, deploy; Tailscale e segredos) | Só a estrutura de jobs |
| Serviço | `app/` (FastAPI), `client/`, `Dockerfile.*`, `docker-compose.yml` | Desnecessário nas duas PoCs |
| Dados e pesos | DVC: `dataset/exports/{epi-v1,epi-v1-dark}.dvc`, `models/{yolov8n.pt,yolo-epi.pt}.dvc` | Sim: mesmo problema já resolvido (RAW canônico e ponteiro no git) |
| Auditoria | `scripts/inspect_dataset.py` | Sim |

Não se transfere: o formato de apresentação da aula, hub/MQTT, deploy com Tailscale e a divisão do
dataset por imagem (padrão Roboflow, que vaza cena entre splits).

## 2. Dados disponíveis (o que temos, com números conferidos)

### 2.1 Cinco conjuntos públicos de tampa, já no disco

Em `~/tcc-pnaat/datasets/externos/` (2,3 GB, 5.174 imagens, formato YOLOv8 com caixas, licença
CC BY 4.0; contagens lidas dos rótulos e digest em `INDEX.md` e nos `*.proveniencia.json`; registro no
repositório em `docs/reference/datasets-externos-roboflow.md`):

| Conjunto | Imagens | Classes (instâncias) |
|---|---|---|
| `bottle_cap_sdp-3v0vj-qzaan` | 3.554 | `good_cap` 2020, `wet_cap` 394, `open_cap` 311, `damaged_cap` 309, `no_cap` 270, `misplaced_cap` 248 |
| `original-zotc7-1j0kr` | 685 | `defect` 360, `good` 138, `ring-missing` 111, `loos-cap` 77, `no-cap` 46 |
| `dataset-joren-newest-a4vuy` | 570 | `Good Cap` 218, `No Cap` 162, `Loose Cap` 124, `Broken Cap` 54, `Broken Ring` 48 |
| `bottle-defect-detection-c6ts8` | 262 | `label` 266, `not-crumbled` 203, `cap` 180, `no-cap` 146, `crumbled` 120 |
| `bottle-lte35-abhgw` | 103 | `Missing cap` 35, `Unclosed` 35, `Closed` 35 |

Também há `archive.zip` do conjunto *Water Bottle Defect-Level Detection* (Kaggle: `no_cap` 150 e
`loose_cap` 150) em `~/Downloads`, ainda não extraído, e um conjunto de vinho (Mendeley) que **não se
aplica** (garrafa opaca, visão de topo, sem tampa rosqueada).

### 2.2 Mapeamento para as nossas classes

| Classe pública | Conjuntos | Nossa classe |
|---|---|---|
| `no_cap`, `no-cap`, `No Cap`, `Missing cap` | sdp, zotc7, joren, defect-detection, lte35 | `tampa_ausente` |
| `misplaced_cap`, `Loose Cap`, `loos-cap`, `Unclosed` | sdp, joren, zotc7, lte35 | `tampa_mal_rosqueada` |
| `good_cap`, `Good Cap`, `Closed`, `cap`, `good` | sdp, joren, lte35, defect-detection, zotc7 | `normal` |
| `open_cap`, `wet_cap` | sdp | **revisar antes de mapear**: a semântica não está confirmada |
| `damaged_cap`, `Broken Cap`, `Broken Ring`, `ring-missing`, `crumbled` | vários | fora do escopo (observação) |
| `defect`, `label`, `not-crumbled` | zotc7, defect-detection | fora do escopo |

Somando o que mapeia direto: **`tampa_ausente` 659**, **`tampa_mal_rosqueada` 484** e **`normal` 2.591**
instâncias (derivado das contagens acima). É volume suficiente para comparar método, e nada disso
responde ao requisito do projeto.

### 2.3 Como transformar em dado das PoCs

Os conjuntos públicos estão em **caixas** (detecção). As duas PoCs querem **classificação de recorte**.
Receita:

1. Ler os rótulos do formato Ultralytics (`classe cx cy w h`, normalizado) de
   `externos/<conjunto>/{train,valid,test}/labels/*.txt`.
2. Recortar cada caixa com uma margem (8% do lado é um ponto de partida) e redimensionar para o lado de
   entrada do classificador (224 px serve).
3. Salvar em árvore de classificação: `dataset/classify_externo/<nossa_classe>/<conjunto>__<imagem>__<i>.png`,
   aplicando o mapeamento da tabela 2.2 e **descartando** as classes fora do escopo.
4. Gravar um manifesto por recorte: `arquivo`, `conjunto`, `classe_publica`, `nossa_classe`, `bbox`,
   `item_id` (não existe no dado público: usar `<conjunto>__<imagem>` como identidade de item), `sha256`.
5. Dividir por **imagem de origem**, não por recorte: dois recortes da mesma foto não podem cair em
   splits diferentes.

Esboço do utilitário (a escrever em `code-workspace/scripts/`, depois de decidir com você):

```
python3 scripts/boxes_para_crops.py \
  --origem  ~/tcc-pnaat/datasets/externos \
  --destino ~/tcc-pnaat/datasets/classify_externo \
  --margem 0.08 --lado 224
```

### 2.4 O que esses dados provam, e o que não provam

Provam: que existe sinal separável nas três classes com um classificador leve (comparação de método), a
convenção de rótulo de terceiros, e um banco de pré-treino. Não provam: nada do requisito do projeto.
Outra bancada, outra ótica, outro fundo, outra iluminação, outro formato de tampa, e sem calibração
pixel a milímetro. Regra: métrica pública é sempre por conjunto de origem, nunca agregada entre
conjuntos, e nunca apresentada como acurácia do nosso sistema.

Para a PoC-03 (deformidade) os conjuntos públicos **não ajudam**: não há rótulo de deformidade de corpo
com referência dimensional. A PoC-03 depende de captura própria nas duas vistas e de calibração.

### 2.5 Duas armadilhas de dado no disco (verificadas)

1. **`~/tcc-pnaat/datasets/nossas/bad/` não é "bad".** Os 81 arquivos são cópia byte a byte das nossas
   frames normais (`sha256` idêntico a `datasets/pnaat/origem/`), e `nossas/good/` tem 3 PNGs de 900x900
   sem procedência registrada. Não usar essa pasta como conjunto rotulado; se for para usar, reconstruir
   o rótulo.
2. **Nome de pasta não é rótulo.** Regra prática antes de qualquer treino: contar arquivos por classe,
   conferir `sha256` das amostras e comparar com a procedência registrada. Foi assim que a pasta acima
   apareceu.

## 3. Ambiente

O venv do projeto (`~/tcc-pnaat/github/.venv`) **não tem `ultralytics`** (tem torch CPU, onnx, openvino,
anomalib). Instalar lá quebra o ambiente do anomalib. Usar venv separado (`~/.venvs/yolo`) com
`ultralytics` e o torch da variante certa. Venv de um host não executa dentro do distrobox, e venv
montado por SSHFS não executa (o symlink do interpretador não resolve).

## 4. Adaptação para a PoC-02 (classificação de tampa)

**Problema de forma:** a decisão é o estado da tampa por item, com medida geométrica e critério por
classe (ausente >= 95% e mal rosqueada >= 90% com intervalo de confiança; falso positivo <= 2% e <= 5%).

Duas rotas, nesta ordem:

1. **Recorte fixo e classificação**: a região vem do pré-processamento determinístico (o PoC-08 já
   localiza a tampa por contorno e elipse). Treina-se `yolov8n-cls` sobre os recortes das vistas
   laterais. Menos dependência de anotação com caixa, e é a rota que usa o dado da seção 2.
2. **Detector e decisão geométrica**: `yolov8n` de detecção com as classes da tampa; a caixa localiza, e
   a medida continua decidindo, como manda a política atual. A vista de topo não decide: verifica
   dimensão. A decisão roda nas duas laterais e a fusão preserva discordância.

Pipeline de dado próprio: 20 a 50 itens por classe produzidos à mão (tampa removida; rosqueada parcial
em três severidades), rótulo registrado antes de ver a saída do pipeline, divisão por item,
`inconclusivo` como estado de decisão (não classe de treino).

**Pré-processamento:** divergência deliberada em relação ao `yolo-edge-api`, que assou a preparação na
exportação do Roboflow (auto-orient, resize 640x480 stretch, equalização adaptativa, flip, rotação
15 graus, cisalhamento 10 graus, saturação e brilho 25%, blur, ruído). Aqui nada é assado: o pipeline do
PoC-08 roda igual no treino e na inferência, pela mesma função, com a versão registrada no manifesto.

**Gate:** copiar o padrão do `validate_model.py` (bloquear abaixo do alvo) e trocar a métrica por
`scripts/avaliar_poc02.py` (recall por classe com limite inferior do intervalo e teto de falso positivo).
O relatório sai com a imagem anotada de cada item, com a medida que discriminou.

**Edge:** exportar para OpenVINO INT8 (o `openvino` já está no venv) e manter o ponteiro do peso no DVC.

## 5. Adaptação para a PoC-03 (deformidade lateral)

Deformidade é medida, não só classe:

1. **Silhueta**: `yolov8n-seg` nas vistas laterais para o contorno do corpo.
2. **Comparação com a referência**: desvio do contorno contra a peça normal, com calibração pixel a
   milímetro por posição fixa (sem ela não há erro dimensional a declarar).
3. **Severidade** (normal, leve, severa) como camada complementar; a decisão vem da medida dentro da
   tolerância.

Dados: duas vistas laterais do mesmo item (depende da captura da PoC-01), peças com deformidade
induzida por gabarito, casos de fronteira registrados, calibração tipo Charuco documentada. Métrica:
acurácia por classe (>= 90%) **e** erro dimensional; o gate checa as duas, e sem calibração válida ele
falha por pré-condição, não por desempenho.

## 6. CI/CD: o que reaproveitar e o que cortar

Reaproveitar: formato do workflow (lint e testes, gate, publicação do artefato); DVC para dados e pesos,
com `dvc status -c` conferido antes de qualquer job que faça `dvc pull`; `inspect_dataset.py` para
auditoria.
Cortar: deploy para Raspberry e ingresso em Tailscale; segredos do repositório da aula; o fallback para
COCO128 no gate e qualquer default genérico de modelo (o caminho do peso vai explícito); Dockerfiles e
`docker-compose` (só se a entrega pedir API, o que hoje não pede).

## 7. Armadilhas herdadas do projeto da aula

1. `dvc pull` sem alvo falha o job inteiro quando existe `.dvc` sem push prévio: rodar `dvc status -c`
   por arquivo antes.
2. Gate com `--model` omitido valida o modelo errado e bloqueia para sempre: caminho explícito.
3. `ruff check` local com o comando exato do CI (ordem de imports reprova mesmo com teste verde).
4. Testes que carregam modelo precisam do caminho de pesos: passar `MODELS_DIR` no ambiente de teste.
5. Depois de operação git como root num checkout do usuário, `chown -R` no repositório.
6. `.dvc/config.local` não é portável (aponta para a chave do host de origem): reescrever a chave e testar
   com `ssh -i <chave> -o IdentitiesOnly=yes -o BatchMode=yes <remote> 'hostname'`.
7. `torch.load` com `weights_only` bloqueado no torch 2.6 ou superior: o patch (`weights_only=False`) é
   aceitável para artefato próprio, com o motivo documentado no script.

## 8. Referências que sustentam estas escolhas

Grau: **P** texto conferido na fonte; **S** secundária (abstract ou índice); **B** prática de mercado.
Lista completa e verificada em `docs/REFERENCIAS.md`.

| Decisão | Referência | O que ela estabelece | Gr. |
|---|---|---|---|
| Medir antes de classificar (geometria da tampa) | Halir & Flusser (1998), ajuste de elipse por mínimos quadrados | ajuste estável, com viés algébrico que encolhe a cota | P |
| Idem, limite prático | Nosso ensaio de viés de elipse (`docs/reference/medicao-vies-elipse-geometria.md`) | viés 0,023 mm (sigma 1 px); arco ocluído degrada o ângulo (1,3 grau para 4,1 grau a 270 graus); escala 0,611 mm/px | N |
| Limiar a partir de referência da peça boa | *Machine-Vision-Based Plastic Bottle Inspection* (Eng. Proc. 2023) | tampa assentada por Harris mais linha entre cantos extremos, com limiar derivado da tampa de referência; 95% no conjunto | S |
| Tampa solta por medição de distância | Xie et al. (2017) | 99% para tampa solta em PET, por distância entre anel de apoio e tampa | S |
| Piso de desempenho (vidro) | Kumchoo & Chiracharit (2018) | 87% para tampa solta e anel | S |
| Teto supervisionado | Sheng & Wang, ECA-EfficientDet (J. Sensors 2022) | detecção de tampa e rótulo, mAP 99,16% com 1.200 amostras | P |
| Teto de metrologia e detecção em transparente | PMC12736620 (ampolas) | fotoelasticidade, telecêntrica com subpixel (0,2 mm) e YOLOv8 (mAP@0.5 90,3%) | P |
| Alternativa sem rótulo de defeito | PatchCore, FastFlow, CutPaste, anomalia no Pi | detecção sem supervisão com conjunto normal | S |
| Alternativa com pseudo-anomalias | SACD (Sensors 25(12):3721, 2025) | professor-aluno com pseudo-anomalias | P |
| Comparação com trabalho de terceiros | Jarvis-BITS/bottle-defect-detection | Mask-RCNN mais CNN: 87,7% (normal e defeituoso) e 72% (material) | P |
| Limiar de aceitação e processo | ISBT PTC-00019/2023, PTC-00022/2024, PTC-00012/2014 | os ensaios avaliam o sistema de embalagem e a especificação é acordada entre fornecedor e engarrafador; não há tolerância angular universal | P (ementa) |
| Falhas de fechamento e bandas de processo | Manual de defeitos de fechamento; bandas PCO 1881 | tampa inclinada, ângulo de aproximação acima de 2 graus, torque insuficiente; torque de aplicação 13-19 in.lbs, abertura 5-14 in.lbs | P |
| Dados públicos usados | Conjuntos Roboflow (CC BY 4.0) e Kaggle | classes e contagens reais, registradas com digest | P (baixado) |

Atribuições que **não** se usam: `arXiv:2404.08401` (é registro de campo esportivo, não a fonte do ajuste
de elipse), "Tan et al." com índice de refração 0,3363 (erro físico: PET fica em cerca de 1,57 a 1,64) e
`researchsquare rs-9814627` (URL sem conteúdo).

## 9. Ordem de execução sugerida

1. Converter os conjuntos públicos em recortes com manifesto (seção 2.3) e rodar o classificador leve
   neles: isso responde se a separação das três classes existe com dado abundante, e com que arquitetura.
2. Coletar e rotular os itens da PoC-02 (20 a 50 por classe) com divisão por item.
3. Rodar a avaliação **geométrica** atual nesse conjunto, sem modelo, e medir a matriz por classe. Se a
   geometria atender ao critério, o modelo passa a reforço e não a decisão.
4. Só então treinar o classificador próprio e comparar com o passo 3, reportando as duas contas
   separadas (dado público e dado nosso).
5. Para a PoC-03: capturar as duas vistas, calibrar pixel a milímetro e repetir a lógica de medir antes
   de modelar.
6. Exportar para OpenVINO INT8 o que for para o Pi 5, com o ponteiro no DVC.
