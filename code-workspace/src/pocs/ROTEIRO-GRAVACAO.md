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
| 01 — trigger | **Sim, em simulação** | debounce, rejeição de ruído, uma janela por passagem e três vistas solicitadas | vídeo físico exige ESP32, E18-D80NK e passagem real; scripts de supervisor/teste citados no README não estão versionados |
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
