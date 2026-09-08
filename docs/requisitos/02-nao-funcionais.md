# Requisitos não funcionais detalhados

Base: RNF-01 a RNF-20 em `../requisitos.md`. Nenhum item representa resultado medido até ser verificado no setup declarado.

## Desempenho e qualidade de decisão

### RNF-01: Latência por item abaixo de 500 ms

- Mede: trigger até registro após três inferências e fusão.
- Método: relógio monotônico em cada etapa, incluindo persistência.
- Aceite: percentil e média declarados; não usar apenas benchmark de uma vista.
- Critério de reprovação: qualquer execução acima do orçamento sem classificação de carga é não aceite.
- Verificação: log por item e script de agregação. Dependências: PERF-01, RF-01/RF-06.

### RNF-02: Acurácia com intervalo de confiança

- Mede: tampa ausente ≥95%, mal rosqueada ≥90%, deformidade ≥90%.
- Método: conjuntos separados, n declarado e Wilson ou Clopper-Pearson.
- Aceite: resultado por classe com IC e matriz de confusão.
- Critério de reprovação: acurácia sem n, split ou IC não atende.
- Verificação: relatório e manifest do teste. Dependências: ML-01/02/03.

### RNF-03: Limite de falsos positivos

- Mede: ≤2% para tampa ausente e ≤5% nas demais classes.
- Método: classe negativa conhecida, sem contar erro de processamento como negativo.
- Aceite: FP separado de FN e erro técnico.
- Critério de reprovação: remover imagens inválidas ou golden samples sem declarar invalida o ensaio.
- Verificação: matriz e manifest. Dependências: QLT-02, DAT-06.

### RNF-04: Correlação multi-nó ≥98%

- Mede: itens corretamente associados em ensaio de 50 itens.
- Método: IDs e timestamps conhecidos, incluindo eventos atrasados.
- Aceite: pelo menos 98% sem associação cruzada.
- Critério de reprovação: dois itens consecutivos trocados ou sem vínculo são falhas.
- Verificação: dataset de eventos e query. Dependências: RF-07, DAT-03.

### RNF-05: Integridade ≥99% em estresse

- Mede: eventos sem perda em 30 minutos contínuos.
- Método: contar eventos gerados, recebidos, persistidos e consultados.
- Aceite: diferença dentro do limite com falhas classificadas.
- Critério de reprovação: olhar somente o banco final não prova ausência de perda.
- Verificação: contadores e logs. Dependências: REL-01, IF-04.

### RNF-06: Retransmissão idempotente

- Mede: 100% dos eventos bufferizados recuperados após reconexão, sem duplicação.
- Método: queda controlada, replay e comparação por ID de evento.
- Aceite: todos recuperados uma vez, ou falha explícita por evento.
- Critério de reprovação: replay duplicado ou sem ID estável falha.
- Verificação: log de queda/reconexão e banco. Dependências: DAT-07, IF-04.

### RNF-07: Detecção de nó offline abaixo de 10 s

- Mede: tempo entre último heartbeat e sinalização.
- Método: relógio sincronizado e atraso conhecido.
- Aceite: tempo medido por nó, não valor configurado.
- Critério de reprovação: dashboard apenas consultado manualmente não atende.
- Verificação: heartbeat e alerta. Dependências: RF-08, OPS-03.

### RNF-08: Resiliência sem crash

- Abrangência: MQTT, debounce, sensor nulo, câmera/ nó ausente e watchdog.
- Método: quatro cenários de falha com hipótese e blast radius mínimo.
- Aceite: recuperação ou degradação explícita, sem processo silenciosamente morto.
- Critério de reprovação: teste sem hipótese, métrica ou observação do processo não fecha.
- Verificação: protocolo chaos e logs. Dependências: RF-24, OPS-04.

### RNF-09: Throughput real mantendo acurácia

- Mede: peças/min sustentado via encoder, junto da qualidade de decisão.
- Método: mesma configuração, duração, temperatura e carga declaradas.
- Aceite: número medido, nunca FPS nominal ou estimativa.
- Critério de reprovação: throughput sem contagem física ou sem acurácia pareada falha.
- Verificação: log encoder e relatório. Dependências: RF-10, PERF-02.

## Documentação e reprodutibilidade

### RNF-10: Documentação como produto

- Abrangência: README, esquemático, DECISIONS.md e proveniência do dataset.
- Aceite: pessoa externa identifica setup, comando, resultado e limites.
- Critério de reprovação: instrução depende de caminho do autor ou arquivo não versionado.
- Verificação: clone limpo e revisão documental. Dependências: DOC-01..07.

### RNF-11: Calibração pixel→mm documentada

- Mede: fator de conversão por câmera/posição fixa.
- Método: régua ou paquímetro no plano do item, antes do dataset.
- Aceite: erro da referência reportado e artefato recuperável.
- Critério de reprovação: medida em pixels apresentada como milímetros falha.
- Verificação: ficha de calibração e imagem. Dependências: RF-15, HW-01/04.

### RNF-12: Qualidade do registro propagada

- Estados: completo, parcial por vista ausente ou timestamp divergente.
- Método: injetar cada condição e consultar item/dashboard/relatório.
- Aceite: nenhum consumidor perde ou normaliza o estado.
- Critério de reprovação: campo existir somente no schema e não afetar consumidores falha.
- Verificação: fixture end-to-end. Dependências: DAT-03, OPS-03.

## Atuação e estabilidade física

### RNF-13: Ejeção confirmada e sem falsa ejeção

- Mede: ≥99% de confirmações dos itens ordenados e zero item OK ejetado.
- Método: golden samples, defeitos conhecidos e sensor de confirmação real.
- Aceite: ordem, movimento e confirmação são estados separados.
- Critério de reprovação: comando sem confirmação apresentado como sucesso falha.
- Verificação: eventos ACT, vídeo/sensor e contagem. Dependências: ACT-01..10, SAFE-01..03.

### RNF-14: Medida dimensional e golden samples

- Mede: precisão da tampa de ±0,5 mm e zero falsa rejeição de golden OK.
- Método: referência física, calibração e repetição.
- Aceite: erro absoluto por amostra e filtro `is_golden` reportados.
- Critério de reprovação: média sem distribuição ou golden misturado no FPY falha.
- Verificação: relatório de calibração e consultas. Dependências: RF-15/16, DAT-05.

### RNF-15: Descritores geométricos abaixo de 10 ms/vista

- Mede: custo OpenCV e falso positivo de calibração ≤2%.
- Método: benchmark no Pi 5 com dataset OK fixado.
- Aceite: score, threshold, latência e fallback documentados.
- Critério de reprovação: benchmark em outra máquina ou sem threshold calibrado falha.
- Verificação: benchmark e manifest. Dependências: RF-18, ML-06.

### RNF-16: CutPaste/NSA somente com OK

- Mede: AUROC alvo ≥95% e latência compatível com 500 ms.
- Método: verificar manifest de treino e validação sem defeitos reais.
- Aceite: origem de cada amostra e configuração do treino auditáveis.
- Critério de reprovação: vazamento de defeito real ou autoencoder puro invalida a camada.
- Verificação: manifest, logs e relatório. Dependências: RF-19/20, ML-02/03.

### RNF-17: Aluno teacher-student leve no Pi 5

- Mede: latência real do aluno INT8 no Pi 5.
- Método: teacher somente em GPU de treino; benchmark do aluno no alvo.
- Aceite: latência, modelo, runtime e fallback publicados.
- Critério de reprovação: extrapolar benchmark de Jetson ou rodar teacher no Pi falha.
- Verificação: logs de treino e benchmark. Dependências: RF-21, ML-06.

### RNF-18: Timestamp físico com tolerância configurável

- Mede: desvio entre timestamp observado e esperado por distância/velocidade.
- Método: atraso conhecido e variância do rig documentada.
- Aceite: desvio acima da tolerância gera alerta de qualidade sem apagar o original.
- Critério de reprovação: tolerância fixa sem calibração ou timestamp corrigido silenciosamente falha.
- Verificação: ensaio e registro DAT-03. Dependências: RF-22, RF-10.

### RNF-19: Testes de resiliência com hipótese prévia

- Mede: cada experimento possui hipótese, métrica, blast radius e resultado.
- Método: registrar protocolo antes da falha e resultado depois.
- Aceite: falha de hipótese é preservada como achado.
- Critério de reprovação: checklist “não caiu” sem métrica não atende.
- Verificação: fichas de PoC e DECISIONS.md. Dependências: RF-24, DOC-05.

### RNF-20: Estabilidade mecânica e elétrica

- Abrangência: mounts parafusados, painel rígido, continuidade, ventilação e calibração.
- Método: mover o conjunto, medir drift e testar continuidade antes da integração.
- Aceite: tolerância definida antes do teste e nenhum jumper crítico solto.
- Critério de reprovação: recalibração necessária após movimentação dentro do uso previsto ou circuito aberto falha.
- Verificação: desenho, fotos, multímetro e calibração antes/depois. Dependências: RF-26..28, HW-01..06.

### RNF-21: Lente difusora óptica para mitigação de hotspots na captura

- Mede: eliminação de pontos rígidos de saturação luminosa (*hotspots*) causados por LEDs de 5 mm na superfície curva de garrafas PET e vidro.
- Método: instalação de lente difusora em PLA branco translúcido impresso em 3D, acrílico ou papel vegetal acoplada à frente dos 2 LEDs RGB de 5 mm; análise do histograma da imagem capturada.
- Aceite: ausência de regiões estouradas (valor de brilho máximo 255 constante) no corpo e na tampa que impeçam a extração de bordas e contornos pelos classificadores.
- Critério de reprovação: imagens com reflexos especulares rígidos gerando falsos positivos de deformidade ou falha de rosqueamento.
- Verificação: análise de histograma em conjunto de imagens de teste com e sem difusor.
- Dependências: RF-30, HW-04, RNF-11.

## Promoção de estado

Um RNF só pode ser considerado medido quando o método, amostra, hardware, versão do software e artefato estiverem registrados. Referência externa não substitui medição própria.
