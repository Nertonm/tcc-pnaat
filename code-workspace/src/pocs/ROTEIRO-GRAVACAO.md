# Entrega 2 — roteiro de gravação das PoCs

Este documento transforma o enunciado da entrega em um plano executável e deixa explícito o que o
repositório **já prova**, o que ele apenas simula e o que ainda depende de bancada ou dados. Não se
deve apresentar teste unitário, tela estática ou saída inventada como se fossem a PoC física.

## 1. O que a entrega pede

Uma prova de conceito não é o produto final. Ela responde a uma pergunta técnica pequena:
"a tecnologia central escolhida consegue executar, na prática, o trecho mais arriscado da
solução?". No vídeo deve ser possível acompanhar, na mesma sequência:

1. **entrada:** item, imagem ou evento que inicia a execução;
2. **funcionamento:** processamento da tecnologia central, sem cortes que ocultem intervenção;
3. **resultado:** decisão e evidência produzidas;
4. **integração:** outro elemento da arquitetura funcionando junto;
5. **próxima etapa:** o que ainda não está integrado ou não foi validado.

Para buscar o nível avançado da rubrica, não basta mostrar código ou `pytest`: a entrada, a execução
e o resultado precisam aparecer de forma acompanhável, a tecnologia central deve operar com outro
elemento da arquitetura e a narração deve explicar a função de cada parte e a próxima integração.

## 2. Qual vídeo priorizar

**Prioridade: um vídeo da PoC Final usando `scripts/demo_poc.py`.** É o artefato mais próximo do
enunciado porque já organiza a execução em sete telas: gatilho, frames reais, pré-processamento,
modelo one-class, decisão, registro/dashboard e conclusão. Ele também gera imagens anotadas,
`resultados.json`, `registro.json` e `dashboard.html`.

Isso não significa que tudo esteja validado. O gatilho usado nesse demo é simulado; o registro é em
memória; a fusão recebe uma única vista; a geometria da tampa está "em validação"; e a classificação
depende de dataset e checkpoint externos ao Git. Essas limitações devem ser ditas no vídeo.

### Estado de cada PoC

| PoC | Dá para adiantar agora? | O que é demonstrável | Bloqueio para alegar validação completa |
|---|---|---|---|
| 01 — trigger | **Sim, em simulação** | debounce, rejeição de ruído, uma janela por passagem e três vistas solicitadas | vídeo físico exige ESP32, E18-D80NK e passagem real; o supervisor serial citado no README não está versionado |
| 02 — tampa | **Parcialmente** | política de decisão e avaliador de matriz/IC | faltam imagens rotuladas das classes, predições reais e limiares calibrados |
| 03 — deformidade | **Não como PoC visual** | conversão px→mm e tolerância em testes | faltam vistas laterais, referência dimensional e matriz de confusão |
| 04 — fusão | **Não entregar isoladamente** | votação, empate e encaminhamento humano | a implementação atual usa maioria global, mas o critério documentado exige preservar defeito por domínio |
| 05 — registro | **Parcialmente** | upsert idempotente e reconciliação durante uma execução | armazenamento é volátil e o evento ainda não possui contrato/evidência completos |
| 06 — resiliência | **Parcialmente** | retry de persistência | faltam watchdog, falha de câmera/sensor e medição de recuperação/perda |
| 07 — dashboard | **Só junto do demo final** | resumo, recorrência e HTML gerado pelo demo | não consulta uma base persistente nem liga evento à evidência completa |
| 08 — pré-processamento | **Sim, se OpenCV/NumPy/SciPy estiverem instalados** | geometria, CNR, foco, especular e ensaio de viés de elipse | rig atual não permite afirmar medida confiável da tampa nem calibração em mm |
| Final — integrada | **Sim, melhor candidata** | entrada→processamento→decisão→registro→dashboard | exige imagens externas; modelo completo exige checkpoint/anomalib; hardware continua simulado |

## 3. Preparação antes de gravar

Todos os comandos abaixo partem da raiz do repositório:

```bash
cd code-workspace
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e . pytest numpy scipy opencv-python
```

Para executar o modelo one-class, a máquina também precisa de uma versão compatível do `anomalib`
e do runtime indicado por ele. Não instalar ou treinar isso durante a gravação. Primeiro, confirmar:

```bash
export PNAAT_DATASETS=/caminho/absoluto/para/datasets/pnaat
test -n "$(find "$PNAAT_DATASETS/dataset/normal" -maxdepth 1 -name '*.jpg' -print -quit)"
test -f "$PNAAT_DATASETS/resultados/modelo_info.json"
PYTHONPATH=src .venv/bin/python -c 'import cv2, numpy, scipy; print("dependencias OK")'
.venv/bin/python -m pytest -q
```

O dataset esperado não vive neste repositório. `modelo_info.json` deve apontar para um checkpoint
que exista nessa mesma máquina. Se o checkpoint não estiver pronto, ainda é possível gravar as
métricas geométricas/de qualidade, mas o apresentador deve dizer "modelo indisponível"; não deve
chamar essa execução de classificação validada.

Limpe saídas antigas para não confundi-las com o ensaio filmado e gere o controle conhecido:

```bash
rm -rf demo/entrada demo/saida
mkdir -p demo/entrada demo/saida
PNAAT_DATASETS="$PNAAT_DATASETS" PYTHONPATH=src .venv/bin/python \
  scripts/gerar_perturbacao_controle.py \
  --origem "$PNAAT_DATASETS/dataset/normal/frame_0000.jpg" \
  --tipo oclusao --dest "$PNAAT_DATASETS/controle" --seed 7
```

A perturbação é um **controle**, não uma garrafa defeituosa real. Sua função é verificar se o modelo
reage a uma alteração conhecida sem falsificar evidência de defeito industrial.

## 4. Ensaio geral antes da gravação

Rode sem pressa e confirme código de saída zero:

```bash
PNAAT_DATASETS="$PNAAT_DATASETS" PYTHONPATH=src .venv/bin/python \
  scripts/demo_poc.py --frames 3 --pausa 0 --saida demo/saida
test -s demo/saida/resultados.json
test -s demo/saida/registro.json
test -s demo/saida/dashboard.html
```

Abra o dashboard localmente:

```bash
.venv/bin/python -m http.server 8000 --directory demo/saida
```

Visite `http://localhost:8000/dashboard.html`. Verifique antes de filmar se as miniaturas aparecem,
se há score quando o modelo está disponível e se o texto não promete mais do que os resultados.

## 5. Roteiro do vídeo principal (4–6 minutos)

Grave a tela em resolução legível, com terminal e navegador lado a lado. Evite cortes entre entrada,
execução e resultado. Use uma nova pasta para cada tomada aprovada.

### 0:00–0:30 — problema e hipótese

Dizer: "A solução observa embalagens na linha e procura tornar anomalias rastreáveis. Esta PoC não
é o produto pronto; ela testa se conseguimos receber uma passagem/imagens, extrair sinais de
qualidade e anomalia, decidir, registrar e apresentar o resultado em uma única execução."

Mostrar rapidamente uma imagem normal e a perturbação de controle. Identificá-las verbalmente.

### 0:30–1:10 — entrada e gatilho

Iniciar, sem pausar a captura:

```bash
rm -rf demo/tomada-01 demo/entrada
PNAAT_DATASETS="$PNAAT_DATASETS" PYTHONPATH=src .venv/bin/python \
  scripts/demo_poc.py --frames 3 --pausa 2 --saida demo/tomada-01
```

Apontar na saída: mudança livre→presente, debounce, identificador da janela e vistas solicitadas.
Dizer explicitamente: "nesta execução o sinal do sensor é simulado pela mesma máquina de estados;
o ensaio físico com ESP32 é uma integração seguinte".

### 1:10–2:40 — funcionamento central

Na listagem de frames, mostrar nome, hash e quantidade. Explicar:

- ROI superior para tampa e restante para corpo;
- Tenengrad como indicador de foco, cobertura especular e CNR como qualidade;
- contorno/elipse como geometria ainda em validação;
- modelo one-class treinado somente com normais e comparação do score bruto com o limiar;
- captura ruim gera `inconclusivo`, em vez de aprovação silenciosa.

Não dizer que o sistema reconhece tampa ausente/mal rosqueada se o ensaio não possui exemplos reais
dessas classes e uma matriz de confusão.

### 2:40–3:40 — resultado e integração

Mostrar cada decisão no terminal e os eventos `ev-...` gravados. Explicar que o segundo elemento da
arquitetura é o registro/dashboard. Ao final, manter o terminal visível com resumo e caminho das
saídas. Sem encerrar a gravação, iniciar o servidor em outro terminal:

```bash
.venv/bin/python -m http.server 8000 --directory demo/tomada-01
```

Abrir `http://localhost:8000/dashboard.html`, clicar/rolar e relacionar pelo nome um frame de entrada,
sua decisão, métricas, imagem anotada e mapa. Mostrar também `resultados.json` ou `registro.json` para
provar que o resultado não existe apenas na tela.

### 3:40–4:30 — conclusão honesta e próxima etapa

Dizer: "Esta execução prova o encadeamento e a geração de evidência por item. Ela ainda não prova as
metas de acurácia industrial." Listar, nessa ordem:

1. ensaiar classes defeituosas rotuladas para produzir matriz de confusão e IC;
2. trocar o gatilho simulado pela passagem no ESP32/E18-D80NK;
3. usar rig com iluminação adequada e calibrar pixel→milímetro;
4. corrigir a fusão para decisão por domínio e persistir eventos/evidências;
5. executar a cadeia no Raspberry Pi 5 e medir latência/resiliência.

## 6. Vídeo curto que pode ser adiantado sem dataset nem hardware

A PoC-01 simulada é útil como vídeo complementar e ensaio de narração, mas deve carregar "SIMULAÇÃO"
no título. Ela mostra entradas normais e ruidosas e o resultado observável:

```bash
cd code-workspace
mkdir -p ../evidencias/medicoes/poc01
PYTHONPATH=src python3 scripts/simular_trigger.py --caso todos \
  --json ../evidencias/medicoes/poc01/trigger-simulado.json
```

Gravar: (1) a sequência de níveis `1/0`; (2) pulso isolado rejeitado; (3) passagem limpa abrindo uma
janela; (4) duas passagens abrindo duas janelas; (5) JSON final. Explicar que `LOW` significa objeto
presente, cinco leituras estáveis fazem o debounce e uma presença contínua não pode reabrir janelas.
Esse vídeo adianta a lógica e o formato da evidência, mas não substitui a filmagem do sensor físico.

## 7. Checklist da tomada válida

- [ ] título/descrição dizem se é simulação, bancada ou integração;
- [ ] entrada aparece antes da execução;
- [ ] tecnologia central e métricas são narradas enquanto rodam;
- [ ] resultado é ligado ao mesmo item por nome/ID/hash;
- [ ] registro/dashboard aparecem na mesma sequência;
- [ ] não há alegação de acurácia sem matriz, tamanho amostral e intervalo de confiança;
- [ ] limitações e próxima integração são faladas;
- [ ] terminal termina sem traceback e artefatos têm conteúdo;
- [ ] vídeo é enviado como **não listado**, e o link é testado em janela anônima;
- [ ] comando, commit, data, ambiente e hashes do ensaio são guardados junto das evidências.

## 8. Critério de decisão para esta entrega

- **Entregar como principal:** PoC Final, somente após o ensaio geral funcionar com imagens e gerar
  dashboard/JSON. Se houver checkpoint válido, mostrar scores; sem ele, reduzir a alegação ao
  pipeline geométrico/de qualidade e à integração.
- **Entregar como complementar:** PoC-01 simulada agora; substituir ou complementar pelo ensaio
  físico assim que sensor e ESP32 estiverem disponíveis.
- **Não gravar como validação ainda:** PoCs 02, 03 e 04. Elas têm código, mas os dados/calibração ou a
  regra de fusão não atendem ao próprio critério declarado.
- **Não separar em vídeos por enquanto:** PoCs 05, 06, 07 e 08; usá-las como partes do vídeo final ou
  como evidência técnica auxiliar, deixando claros os limites descritos na tabela.

## 9. Modelo mental do sistema inteiro

O sistema é uma cadeia. Um arquivo isolado não é “a inteligência” completa:

```text
E18/níveis simulados
  → PresenceTrigger abre uma janela e atribui w-N
  → imagens da tampa/corpo entram no pré-processamento
  → métricas de captura + geometria + score do modelo
  → política transforma medidas em decisão por vista/domínio
  → fusão deveria produzir a decisão única do item
  → ObservationEvent empacota ID, origem, horário, vistas, decisão e qualidade
  → LocalRegistry evita duplicação na execução
  → dashboard resume e apresenta os eventos
```

No estado atual, `demo_poc.py` não percorre literalmente todas essas setas: simula o trigger, executa
o pré-processamento e o detector one-class, cria uma única `ViewResult` do corpo, passa essa vista
pela fusão, grava em memória e exporta um HTML. A política de tampa de `politica_tampa.py` não está
conectada ao demo. Essa diferença entre **arquitetura desejada** e **demo atual** é a principal coisa
que a equipe precisa entender para não narrar uma capacidade inexistente.

### Vocabulário usado na gravação

- **PoC:** experimento pequeno para reduzir um risco técnico; não é produto acabado.
- **item:** uma garrafa/unidade física; várias imagens podem pertencer ao mesmo item.
- **vista:** posição da câmera (`topo`, `lateral1`, `lateral2` ou, no demo, `corpo`).
- **janela de captura:** intervalo aberto por uma passagem confirmada no sensor.
- **ROI:** recorte da imagem no qual uma medida é calculada.
- **gate de qualidade:** impede que captura ruim seja aprovada silenciosamente.
- **ground truth/verdade:** rótulo conhecido antes de olhar a predição.
- **controle:** alteração conhecida para observar reação; não equivale a defeito industrial real.
- **inconclusivo/análise humana:** saída válida para evidência insuficiente; não é “normal”.
- **fusão:** combinação dos resultados das vistas/domínios em uma decisão por item.
- **idempotência:** reenviar o mesmo `event_id` não cria uma segunda ocorrência.
- **IC95:** faixa de incerteza da taxa medida; poucos acertos em poucas imagens não bastam.

## 10. Mapa de arquivos: para que serve cada um

### Raiz de `code-workspace`

| Arquivo | Função | Alterar para a gravação? |
|---|---|---|
| `README.md` | índice rápido das PoCs e comandos gerais | não; apenas consulte |
| `pyproject.toml` | pacote Python, versão mínima e descoberta de `src/pocs` | não para trocar caminhos/limiares; dependências de visão ainda são instaladas à parte |
| `Makefile` | atalhos `test`, `test-vision`, `demo`, `controle`, `treino` | preferir comandos explícitos deste guia; os defaults do Makefile são específicos do ambiente original |
| `src/pocs/ROTEIRO-GRAVACAO.md` | este manual operacional | sim: preencher caminhos/comandos na sua cópia de trabalho somente se forem defaults reutilizáveis |

### Contrato e módulos Python em `src/pocs`

| Arquivo | Entrada → saída | O que realmente faz |
|---|---|---|
| `events.py` | campos Python → `ViewResult`/`ObservationEvent` | define classes canônicas, confiança entre 0 e 1 e evento com pelo menos uma vista; ainda não contém versão do contrato nem referência de imagem |
| `poc01_trigger/presence.py` | nível digital → `CaptureRun` | converte `LOW` em presença, conta leituras estáveis, abre `w-1`, `w-2` etc. uma vez e rearma depois de ausências estáveis |
| `poc01_trigger/esp/main.py` | GPIO real → log/CSV no ESP32 | firmware MicroPython da bancada; é o arquivo enviado à placa como `main.py` |
| `poc02_classificacao/politica_tampa.py` | geometria/qualidade → classe, motivos e escalonamento | aplica gate de qualidade, ausência por altura, tilt e fallback auxiliar; os limiares default são provisórios |
| `poc02_classificacao/classificacao.py` | listas de previsto/verdade → acurácia/matriz simples | harness antigo e básico; para relatório da entrega, usar `scripts/avaliar_poc02.py` |
| `poc03_deformidade/medicao.py` | pixels + referência → mm/tolerância | só contém a matemática de escala; não detecta o contorno da garrafa nem calibra a câmera sozinho |
| `poc04_fusao/fusion.py` | várias `ViewResult` → classe/confiança | usa maioria estrita e empate→humano; não implementa ainda a fusão por domínio decidida em D-04/D-23 |
| `poc05_registro/registry.py` | `ObservationEvent` → armazenamento/consulta | dicionário em RAM indexado por `event_id`; `upsert` devolve `stored` ou `exists`; tudo some ao encerrar o processo |
| `poc06_resiliencia/resilience.py` | função de persistência → resultado de retries | captura exceção, tenta novamente e gera alerta ao esgotar; não monitora câmera, GPIO ou heartbeat |
| `poc07_dashboard/dashboard.py` | registro em RAM → resumo/recorrência | agrega total, esteira, defeito e falha; não é servidor web e não lê um banco persistente |
| `poc08_preproc/preproc.py` | arrays NumPy → imagem/medidas | flat-field, alinhamento, ROI, CLAHE, especular, foco, CNR e elipse; o demo usa apenas parte dessas funções |
| `pocfinal/integrada.py` | lista de eventos já prontos → resumo | integra apenas registro e consulta; o executável visual da entrega é `scripts/demo_poc.py` |

Arquivos `__init__.py` tornam as pastas importáveis e reexportam símbolos. Normalmente não são
editados para gravar. Os `README.md` dentro de cada `pocNN_*` são fichas da conjectura: ideia,
pergunta, hipótese, método, critério, evidência, limite e dependências. Eles dizem **o que seria
necessário para aprovar a PoC**, não garantem que o código já tenha produzido essa evidência.

### Scripts executáveis

| Script | Quando usar | Entrada principal | Saída/efeito |
|---|---|---|---|
| `demo_poc.py` | vídeo integrado | normais em `dataset/normal`, controles e opcionalmente checkpoint | terminal em 7 etapas, anotados/mapas, dois JSON e HTML |
| `simular_trigger.py` | vídeo complementar sem placa | casos internos ou `--niveis` | eventos no terminal e JSON opcional |
| `poc01_teste.py` | ensaio físico do trigger | `~/poc01/stream.log` alimentado pelo supervisor externo | PASS/FAIL por passagem e `~/poc01/evidencia-poc01.json` |
| `poc01_escopo.py` | ajustar/visualizar sensor físico | mesmo stream serial intermediado | gráfico textual do nível e taxa de bordas; não abre a serial diretamente |
| `esp_tool.py` | administrar ESP32 | `/dev/ttyUSB0`, `pyserial` | upload/pull/run/reset via raw REPL; cria sentinela `~/poc01/PAUSA` |
| `gerar_perturbacao_controle.py` | produzir controle reproduzível | uma foto normal, tipo e seed | JPG alterado, máscara e JSON de proveniência |
| `treinar_dataset.py` | gerar checkpoint one-class | `dataset/normal` e opcional `defective` | checkpoint e `resultados/modelo_info.json` |
| `calibrar_limiar_modelo.py` | depois do treino | checkpoint + normais | acrescenta distribuição e `limiar_bruto` a `modelo_info.json` |
| `calibrar_limiares_tampa.py` | calibrar tilt/altura com dados | CSV rotulado, coluna, classes e `n-min` | JSON de limiar com hash, método e estatísticas |
| `avaliar_poc02.py` | medir PoC-02 real | manifest CSV + predições JSON | matriz por fonte, recall/IC/FP, vereditos e anotados opcionais |
| `medir_vies_elipse.py` | evidência matemática da PoC-08 | cenários sintéticos internos | tabela ou JSON do viés por ruído/arco |
| `validar_pares.py` | auditar defeitos sintéticos | pasta de pares e originais | PASS/FAIL de schema, bbox, máscara, isolamento e duplicatas |
| `montar_dataset.py` | promover somente pares aprovados | gerados + originais | cópia para `dataset/defective` e relatório de revisão |

### Testes

Cada `tests/test_<tema>.py` protege o módulo/script de mesmo tema. Teste verde significa que a regra
programada se comporta nos casos artificiais; não significa que câmera, sensor ou acurácia foram
validados. `test_preproc.py`, `test_validar_pares.py` e `test_vies_elipse.py` precisam do stack de
visão. Os demais permitem verificar a lógica sem hardware.

## 11. Documentos: ordem de leitura e autoridade

| Documento | Responde a quê? | Quando alterar |
|---|---|---|
| `docs/escopo.md` | o que pertence ao núcleo e o que é expansão? | só se a banca/equipe aprovar mudança de escopo |
| `docs/arquitetura.md` | quais blocos existem e como os dados fluem? | ao integrar/remover um componente de verdade |
| `docs/requisitos.md` | qual RF/RNF e qual meta precisam ser verificadas? | ao aprovar nova versão dos requisitos, nunca para “fazer o teste passar” |
| `docs/DECISIONS.md` | por que uma escolha foi feita, alternativas e pendências? | adicionar nova decisão/emenda quando evidência mudar a direção técnica |
| `docs/pocs/README.md` | matriz canônica de PoCs e estado adversarial do demo | atualizar depois de um ensaio, citando sua evidência |
| `docs/pocs/02-classificacao-tampa/README.md` | protocolo rigoroso e dados exigidos para PoC-02 | atualizar protocolo/pendências, não números medidos |
| `docs/pocs/08-preprocessamento-geometria/README.md` | pergunta, etapas e critério da PoC-08 | atualizar quando pipeline/versão/critério mudar |
| `src/pocs/*/README.md` | ficha executável próxima do código | atualizar junto com comportamento, limite ou comando do respectivo módulo |
| `docs/reference/*` | fonte externa, cálculo ou justificativa de calibração | incluir fonte e data; não tratar referência como medição própria |
| `evidencias/*` | índice/metadados dos artefatos obtidos | a cada tomada/medição realmente realizada |
| `latex-workspace/*` | fonte do PDF acadêmico | sincronizar quando o conteúdo validado precisar entrar no documento formal |

Regra prática: **requisito é meta; README de PoC é protocolo; código é mecanismo; evidência é o que
aconteceu; decisão interpreta a evidência**. Não copie um valor do requisito para um relatório como
se fosse valor medido.

## 12. Estrutura de dados externa esperada

O Git não contém o dataset. Antes do vídeo, organize o diretório apontado por `PNAAT_DATASETS`:

```text
$PNAAT_DATASETS/
├── origem/                 # fotos originais imutáveis
├── gerados/                # pares sintéticos aguardando validação
├── controle/               # controles do vídeo; fora das métricas de defeito real
├── dataset/
│   ├── normal/             # JPG/PNG normais usados no treino/demo
│   └── defective/          # defeitos validados, nunca controles improvisados
├── resultados/
│   ├── modelo_info.json    # modelo, caminho do checkpoint e limiar bruto
│   └── ...checkpoint...
└── revisao/                # relatórios de validação/montagem do dataset
```

O mínimo do demo são imagens `.jpg` em `dataset/normal`. O detector exige também
`resultados/modelo_info.json` e o checkpoint referenciado nele. Os controles são acrescentados ao
demo automaticamente quando o nome termina em `_controle_*.jpg`.

Exemplo mínimo conceitual de `modelo_info.json` (não copiar números; são produzidos pelo treino):

```json
{
  "modelo": "patchcore",
  "checkpoint": "/caminho/real/model.ckpt",
  "limiar_bruto": 0.123
}
```

Se mover o dataset de computador, o caminho absoluto do checkpoint pode ficar inválido. Corrija o
campo `checkpoint` para o arquivo real ou execute novamente o treino. Não altere `limiar_bruto` à
mão: rode `calibrar_limiar_modelo.py`.

## 13. O que você deve alterar antes dos vídeos

### Alterações operacionais obrigatórias (fora do código)

1. Defina `PNAAT_DATASETS` no terminal da máquina de gravação.
2. Coloque e revise as imagens normais em `dataset/normal`.
3. Gere os controles com seed fixa; não edite a imagem manualmente sem proveniência.
4. Treine/calibre e confira o caminho do checkpoint, se for mostrar o modelo.
5. Escolha uma pasta nova, como `demo/tomada-2026-09-11-01`, para cada tomada.
6. Preencha um manifest em `evidencias/manifests/` depois da tomada aprovada.
7. Coloque no repositório apenas metadados permitidos; o vídeo pode permanecer externo/não listado.

### Pontos de configuração no código — só alterar com justificativa

| Necessidade | Local correto | Observação |
|---|---|---|
| pasta de dados | variável `PNAAT_DATASETS` | preferível a editar Python/Makefile |
| quantidade de normais no vídeo | `demo_poc.py --frames N` | não muda treino, apenas quantas normais entram no take |
| ritmo visual | `demo_poc.py --pausa SEGUNDOS` | use 2 no vídeo e 0 no ensaio |
| pasta de artefatos | `demo_poc.py --saida DIR` | sempre use pasta vazia/nova |
| ROI da tampa | `ROI_TAMPA` em `demo_poc.py` | mudança algorítmica: justificar, testar e versionar |
| gate de especular/foco | `ESPECULAR_MAX`/`TENENGRAD_MIN` em `demo_poc.py` | são limiares; não ajustar olhando o resultado desejado |
| tilt, altura, CNR da tampa | `Limiares` em `politica_tampa.py` | substituir defaults somente por calibração versionada |
| leituras do trigger desktop | construtor `PresenceTrigger` | manter coerente com firmware e registrar frequência de amostragem |
| porta serial | `PORTA` em `esp_tool.py` | hoje fixa em `/dev/ttyUSB0`; confirme com `python -m serial.tools.list_ports` |
| pino/tempo no ESP32 | constantes de `poc01_trigger/esp/main.py` | alterar antes do upload e registrar versão/hash do firmware |
| classes e contrato | `events.py` | alteração de arquitetura; exige testes e migração dos consumidores |
| regra de fusão | `poc04_fusao/fusion.py` | pendência real; implementar por domínio antes de alegar PoC-04 aprovada |

**Não altere um limiar durante a gravação para transformar uma saída em “acerto”.** Interrompa,
registre a falha, calibre com conjunto separado, faça commit e execute uma nova tomada.

## 14. Procedimento do zero, sem pular etapas

### A. Antes do dia de gravar

1. Leia `docs/escopo.md`, `docs/arquitetura.md`, `docs/requisitos.md` e `docs/pocs/README.md`.
2. Escolha a alegação: integração do fluxo, e não acurácia industrial.
3. Crie o ambiente e execute todos os testes possíveis.
4. Confirme dataset, modelo e pelo menos três imagens normais legíveis.
5. Gere um controle, inspecione imagem, máscara e JSON.
6. Rode o demo com `--pausa 0` em pasta vazia.
7. Abra o HTML e compare cada linha com `resultados.json`.
8. Ensaie a fala cronometrada e anote limitações em papel/tela.

### B. Imediatamente antes da tomada

```bash
cd /caminho/para/tcc-pnaat/code-workspace
export PNAAT_DATASETS=/caminho/absoluto/para/datasets/pnaat
export PYTHONPATH=src
TAKE="demo/tomada-$(date -u +%Y%m%dT%H%M%SZ)"
test -d "$PNAAT_DATASETS/dataset/normal" || exit 1
test -f "$PNAAT_DATASETS/resultados/modelo_info.json" || exit 1
.venv/bin/python -c 'import cv2, numpy; print("ambiente OK")' || exit 1
printf 'saida=%s\n' "$TAKE"
```

Feche notificações, aumente a fonte do terminal, esconda dados pessoais/tokens e capture terminal e
navegador. Não grave instalação, treino demorado ou tentativa e erro.

### C. Durante a tomada

```bash
.venv/bin/python scripts/demo_poc.py --frames 3 --pausa 2 --saida "$TAKE"
```

Não interrompa o processo. Leia as sete etapas, explique entrada/processamento/resultado e só afirme
o que aparece. Depois sirva exatamente `$TAKE`, não uma pasta antiga:

```bash
.venv/bin/python -m http.server 8000 --directory "$TAKE"
```

### D. Depois da tomada

```bash
test -s "$TAKE/resultados.json"
test -s "$TAKE/registro.json"
test -s "$TAKE/dashboard.html"
find "$TAKE" -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum > "$TAKE/SHA256SUMS"
```

Anote commit (`git rev-parse HEAD`), ambiente (`python --version`), horário UTC, operador, setup,
comando e hashes. Envie o vídeo como não listado e teste o link deslogado.

## 15. Como gravar cada PoC isolada quando os insumos existirem

### PoC-01 física

Mostre a montagem, fio/pino, nível livre, passagem e log. Rode `poc01_teste.py`, faça exatamente o
número solicitado de passagens e mostre `VEREDITO`. Antes disso é necessário ter um processo externo
alimentando `~/poc01/stream.log`; o `poc01_supervisor.py` descrito no README não está neste Git. Sem
esse stream, `poc01_teste.py` e `poc01_escopo.py` não recebem eventos. Evidência: vídeo da passagem,
JSON do harness, log e imagens/timestamps associados à janela.

### PoC-02 classificação de tampa

Colete verdade antes da predição, com duas laterais e topo por `item_id`. Calibre em conjunto separado,
gere `predicoes.json`, rode `avaliar_poc02.py` e filme imagem de entrada → medidas/decisão → matriz,
IC, FP e anotação. Nunca misture fontes no mesmo resultado. Sem amostras defeituosas reais/validadas,
grave apenas “pipeline em construção”, não “classificador aprovado”.

### PoC-03 deformidade

Filme referência dimensional no mesmo plano, aquisição lateral, pixels medidos, fator mm/px, resultado
e comparação com instrumento. Várias repetições e matriz são necessárias. `medicao.py` sozinho não
produz a segmentação nem captura.

### PoC-04 fusão

Prepare o mesmo item em vistas discordantes, mostre resultados por vista e saída final com origem.
Não grave como aprovada enquanto `fusion.py` estiver em maioria global. A correção deve modelar domínio
de tampa/corpo e preservar reprovação/discordância conforme D-04/D-23.

### PoC-05 registro

Mostre evento completo, primeiro `upsert=stored`, reenvio do mesmo ID=`exists`, consulta e reconciliação.
Para atender completamente, implemente persistência e campos `evidence_ref`/versão do contrato antes
do ensaio; o dicionário atual demonstra apenas o princípio em uma execução.

### PoC-06 resiliência

Defina antes a falha, duração, resultado esperado e métricas. Injete uma falha por vez; mostre retries,
alerta, recuperação, perda e duplicação. O módulo atual permite demonstrar somente falha de persistência.

### PoC-07 dashboard

Mostre filtro e navegação desde o evento até a evidência. O HTML do demo é adequado como integração
visual, mas não prova consulta de registro persistente, filtro completo, saúde ou notificação.

### PoC-08 pré-processamento

Mostre imagem real, ROI/contorno anotado e números de CNR, Tenengrad e especular; depois o ensaio de
viés. Diga quais etapas estão realmente chamadas. Para alegar medição dimensional, inclua calibração
e incerteza — elipse detectada não equivale automaticamente a milímetros corretos.

## 16. Diagnóstico de erros comuns

| Sintoma | Causa provável | Como resolver sem improvisar |
|---|---|---|
| `ModuleNotFoundError: pocs` | `PYTHONPATH` ausente ou pacote não instalado | execute da pasta `code-workspace` com `PYTHONPATH=src` ou `pip install -e .` |
| `No module named cv2/numpy/scipy` | ambiente errado/incompleto | ative `.venv`, instale dependências e repita o pré-voo |
| `sem frames normais` | `PNAAT_DATASETS` errado ou pasta vazia | confira `echo`, `find` e extensões `.jpg`; não mude código |
| `modelo_info.json ausente` | treino ainda não executado ou base errada | treine ou assuma explicitamente demo sem modelo |
| `checkpoint ausente` | caminho absoluto antigo | localize o `.ckpt`, corrija referência ou retreine |
| demo sem score | anomalib/checkpoint falhou | leia o aviso completo antes de gravar; não chame de inferência válida |
| dashboard sem imagens | servidor apontando para pasta errada | use `--directory "$TAKE"` e abra a URL correta |
| arquivos de tomada anterior | `demo/entrada` acumula cópias | remova `demo/entrada` antes de cada ensaio e use `$TAKE` novo |
| porta serial ocupada | dois leitores em `/dev/ttyUSB0` | restaure o supervisor único/sentinela; não abra dois monitores |
| nenhum evento físico | stream externo ausente, fio/pino/polaridade ou distância | valide primeiro nível livre/presente com escopo; E18 é active-low |
| tudo vira `inconclusivo` | gate de qualidade ou modelo ausente | mostre métricas, corrija iluminação/foco; não afrouxe limiar ao vivo |
| controle chamado de defeito | erro conceitual | refaça narração e metadados: controle só prova reação conhecida |
| teste verde mas vídeo fraco | teste não mostra operação acompanhável | filme entrada, execução, resultado e integração na mesma sequência |

## 17. Pacote mínimo de evidência

Para cada tomada aprovada, preserve externamente:

```text
EVID-AAAA-MM-DD-pocfinal/
├── video.mp4 ou URL-nao-listada.txt
├── comando.txt
├── ambiente.txt
├── manifest.yaml
├── SHA256SUMS
├── resultados.json
├── registro.json
├── dashboard.html
├── *_anotado.png
└── *_mapa.png                 # quando modelo disponível
```

Use `evidencias/manifests/manifest.template.yaml` como base. `state=MEASURED` significa que o ensaio
foi executado e medido; `VALIDATED` só deve ser usado quando o critério de passagem foi atendido e
revisado. `DERIVED` é cálculo sobre uma medição; `SPECULATIVE` é hipótese; `BLOCKED` registra por que
o ensaio não ocorreu. `source_file` pode apontar para armazenamento externo, acompanhado de SHA-256.

## 18. Antes de pedir ajuda: bloco de diagnóstico

Copie e execute este bloco e envie a saída completa junto da dúvida; ele evita várias rodadas de
perguntas sobre pasta, Python e dados:

```bash
cd /caminho/para/tcc-pnaat/code-workspace
printf '%s\n' '=== git ==='
git status --short && git rev-parse --short HEAD
printf '%s\n' '=== python ==='
command -v python3 && python3 --version
printf '%s\n' '=== variaveis ==='
printf 'PNAAT_DATASETS=%s\n' "${PNAAT_DATASETS:-NAO_DEFINIDO}"
printf '%s\n' '=== dependencias ==='
PYTHONPATH=src python3 -c 'import pocs; print("pocs OK")'
python3 -c 'import cv2,numpy,scipy; print("visao OK")'
printf '%s\n' '=== dados ==='
find "${PNAAT_DATASETS:-/caminho-inexistente}" -maxdepth 3 -type f 2>&1 | sed -n '1,80p'
printf '%s\n' '=== modelo ==='
test -f "${PNAAT_DATASETS}/resultados/modelo_info.json" && \
  cat "${PNAAT_DATASETS}/resultados/modelo_info.json" || echo 'modelo_info AUSENTE'
```

Remova tokens, nomes pessoais e caminhos sensíveis antes de compartilhar a saída.
