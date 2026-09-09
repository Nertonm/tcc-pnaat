# Requisitos não funcionais detalhados

Base: RNF-01 a RNF-21 em `../requisitos.md`. Os valores apresentados neste documento são metas de engenharia, e não resultados observados. Um requisito somente pode ser considerado validado quando o método, a amostra, o setup, as versões envolvidas e a evidência reproduzível estiverem registrados.

## Desempenho e qualidade de decisão

### RNF-01: Manter a latência de decisão por item abaixo de 500 ms

- Mede: tempo entre o recebimento do trigger válido e a persistência da decisão final do item, incluindo captura, pré-processamento, inferências, combinação por domínios e registro.
- Meta: latência inferior a 500 ms no percentil definido para o ensaio, no setup e sob a carga documentados.
- Método: registrar timestamps monotônicos no início e no fim de cada etapa e calcular média, mediana, percentis e valor máximo da distribuição.
- Aceite: o percentil adotado deve permanecer abaixo de 500 ms, com tamanho da amostra, carga, hardware, versões dos modelos e condições térmicas registrados antes da interpretação do resultado.
- Critério de reprovação: medição de apenas uma vista, exclusão não declarada de etapas, uso exclusivo da média ou ausência da distribuição de latência não atende ao requisito.
- Verificação: log por `item_id`, script versionado de agregação e relatório da distribuição observada.
- Dependências: PERF-01, RF-01, RF-05 e RF-06.

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

### RNF-04: Manter correlação multi-nó de pelo menos 98%

- Mede: proporção de itens cujos eventos de visão, sensores e atuação foram associados corretamente ao mesmo `item_id` em ensaio de 50 itens.
- Meta: pelo menos 98% dos itens corretamente correlacionados e nenhuma associação cruzada entre itens distintos.
- Método: utilizar sequência conhecida de itens e eventos com IDs e timestamps controlados, incluindo atraso, reordenação, duplicação e ausência de eventos.
- Aceite: atingir a meta de correlação sem atribuir ao mesmo `item_id` evidências pertencentes a itens diferentes; eventos ausentes ou fora da janela devem permanecer explicitamente incompletos.
- Critério de reprovação: qualquer associação cruzada, normalização silenciosa de evento ausente ou registro parcial apresentado como completo reprova o ensaio.
- Verificação: dataset versionado de eventos, fixture de reordenação e consultas que comparem associação esperada e observada.
- Dependências: RF-01.2, RF-07 e DAT-03.

### RNF-04.1: Limitar o erro da medição dimensional do corpo

- Mede: erro relativo entre a dimensão estimada nas vistas laterais e a dimensão da referência física.
- Meta: erro relativo inferior a 5% no setup calibrado da PoC 02.
- Método capturar referências ou réplicas com dimensões conhecidas, aplicar a calibração pixel para milímetro e comparar os valores estimados e de referência.
- Aceite: cada resultado deve preservar medida, unidade, vista de origem, versão da calibração, referência utilizada e erro relativo calculado.
- Critério de reprovação: medição sem calibração válida, unidade, referência, vista de origem ou com erro igual ou superior ao limite não pode ser apresentada como evidência dimensional válida.
- Verificação: relatório de calibração, imagens utilizadas, dimensões de referência e cálculo reproduzível do erro.
- Dependências: RF-04.1, RNF-11, HW-04 e PoC 02.

### RNF-05: Manter integridade de pelo menos 99% durante o estresse

- Mede: proporção de eventos que percorrem geração, transmissão, persistência e consulta preservando os campos obrigatórios do contrato de dados.
- Meta: pelo menos 99% de integridade em ensaio contínuo de 30 minutos.
- Método: comparar eventos gerados, recebidos, persistidos e consultados por identificador estável, verificando presença e consistência dos campos obrigatórios.
- Aceite: atingir a meta com perdas, duplicações, registros parciais e inconsistências classificadas separadamente.
- Critério de reprovação: verificar apenas o conteúdo final do banco, ignorar registros parciais ou contabilizar evento duplicado como evento íntegro não comprova o requisito.
- Verificação: contadores por etapa, logs, contrato de dados e consultas de consistência.
- Dependências: REL-01, IF-04, DAT-01, DAT-06 e RF-06.

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

### RNF-08: Tratar falhas sem interrupção silenciosa

- Abrangência: perda e reconexão MQTT, evento duplicado, sinal instável sujeito a debounce, sensor inválido, câmera ou nó ausente e acionamento do watchdog.
- Método: executar cenários de falha controlados, cada um com hipótese, estado inicial, estímulo, impacto máximo permitido e métrica definidos antes da execução.
- Aceite: o sistema deve recuperar a operação ou assumir estado degradado ou offline de forma explícita, preservando a causa e os eventos afetados.
- Critério de reprovação: processo encerrado silenciosamente, registro parcial apresentado como completo, falha convertida em estado normal ou ensaio sem hipótese e métrica não atende ao requisito.
- Verificação: protocolo de resiliência, logs, heartbeats, estados observados e evidências da recuperação.
- Dependências: RF-08, RF-24, OPS-04 e REL-02.

### RNF-09: Garantir qualidade suficiente da medição de movimento

- Mede: resolução, repetibilidade, pulsos falsos, perda de pulsos e estabilidade do mecanismo utilizado para estimar deslocamento, velocidade e throughput.
- Meta: os limiares quantitativos devem ser definidos antes da PoC 03, considerando as velocidades e os deslocamentos previstos para o rig.
- Método: executar deslocamentos conhecidos e repetidos, nas velocidades previstas, comparando contagem de pulsos, distância estimada, variação entre repetições, escorregamento e resposta à desconexão.
- Aceite: o mecanismo deve demonstrar resolução e repetibilidade suficientes para não comprometer a associação das três vistas nem a estimativa do throughput. O KY-040 permanece como componente candidato até essa validação.
- Critério de reprovação: perda de pulsos, pulsos falsos, escorregamento, instabilidade mecânica, ausência de repetibilidade ou desconexão não detectada impedem que a medição seja tratada como válida.
- Verificação: log do encoder, referência física de deslocamento, relatório da PoC 03 e cálculo reproduzível.
- Dependências: RF-10, RF-22, PERF-02 e PoC 03.

## Documentação e reprodutibilidade

### RNF-10: Documentação como produto

- Abrangência: README, esquemático, DECISIONS.md e proveniência do dataset.
- Aceite: pessoa externa identifica setup, comando, resultado e limites.
- Critério de reprovação: instrução depende de caminho do autor ou arquivo não versionado.
- Verificação: clone limpo e revisão documental. Dependências: DOC-01..07.

### RNF-11: Documentar e versionar a calibração pixel para milímetro

- Mede: fator de conversão e erro da calibração para cada câmera, posição e plano de medição aplicável.
- Método: utilizar referência dimensional conhecida posicionada no plano do item, registrando câmera, distância, orientação, resolução, foco, iluminação e data da calibração.
- Aceite: a calibração deve possuir versão, validade, referência física, procedimento, imagens e erro observado recuperáveis.
- Critério de reprovação: apresentar medida em pixels como milímetros, reutilizar calibração após alteração da geometria sem verificar sua validade ou omitir a vista e a versão reprova o requisito.
- Verificação: ficha de calibração, imagens, dimensões da referência e cálculo reproduzível.
- Dependências: RF-04.1, RF-15, RF-27, RF-28 e HW-01/04.

### RNF-12: Propagar a qualidade e a completude do registro

- Estados mínimos: completo, parcial, inconclusivo e inválido, acompanhados da causa aplicável, como vista ausente, imagem inválida, baixa qualidade, baixa confiança, divergência temporal ou discordância lateral.
- Método: injetar cada condição e consultar o registro do item, as decisões por domínio, o dashboard e os demais consumidores habilitados.
- Aceite: nenhum consumidor pode remover, normalizar ou converter silenciosamente um estado parcial, inconclusivo ou inválido em registro completo ou decisão aprovada.
- Critério de reprovação: o estado existir apenas no schema, desaparecer em algum consumidor ou não afetar a decisão quando aplicável reprova o requisito.
- Verificação: fixtures end-to-end para cada condição e comparação dos estados em persistência, dashboard e saída da decisão.
- Dependências: RF-05.1, DAT-02, DAT-03, DAT-06 e OPS-03.

## Atuação e estabilidade física

### RNF-13: Confirmar a separação sem direcionar item normal

- Mede: proporção das separações comandadas que foram fisicamente confirmadas e quantidade de itens normais direcionados ao caminho de análise manual.
- Meta: confirmar corretamente pelo menos 99% das separações comandadas e não direcionar nenhum item classificado como normal ao caminho de análise manual durante a PoC 07.
- Método executar itens normais e reprovados em sequência conhecida, comparando decisão final, ordem de atuação, movimento observado e transição do sensor de confirmação.
- Aceite: decisão, ordem, atuação física e confirmação devem permanecer como estados distintos e rastreáveis pelo mesmo `item_id`.
- Critério de reprovação: comando sem confirmação apresentado como sucesso, item normal separado, confirmação associada ao item errado ou timeout não registrado reprova o requisito.
- Verificação: eventos de atuação, transições do sensor, vídeo e contagem reproduzível da PoC 07.
- Dependências RF-14, ACT-01..10, SAFE-01..03 e PoC 07.

### RNF-14: Medida dimensional e golden samples

- Mede: precisão da tampa de ±0,5 mm e zero falsa rejeição de golden OK.
- Método: referência física, calibração e repetição.
- Aceite: erro absoluto por amostra e filtro `is_golden` reportados.
- Critério de reprovação: média sem distribuição ou golden misturado no FPY falha.
- Verificação: relatório de calibração e consultas. Dependências: RF-15/16, DAT-05.

## Metas condicionais e evolutivas

Os RNF-15, RNF-16 e RNF-17 somente se aplicam quando os requisitos funcionais correspondentes forem aprovados para implementação. Seus valores são metas preliminares e devem ser confirmados ou revisados antes dos ensaios por meio de decisão registrada em `docs/DECISIONS.md`.

### RNF-15: Limitar o custo da camada evolutiva de descritores

- Aplicabilidade: somente quando o RF-18 for aprovado por PoC e decisão registrada.
- Mede: latência acrescentada por vista e taxa de falsos positivos da camada de descritores no hardware-alvo.
- Meta preliminar: acrescentar menos de 10 ms por vista; o limiar de falsos positivos deve ser definido antes do ensaio.
- Método: executar benchmark no Raspberry Pi 5 com dataset fixado, aquecimento declarado, número de repetições definido e medição monotônica isolada da camada.
- Aceite: registrar descritores habilitados, score, limiar, distribuição de latência, taxa de falsos positivos e comportamento de fallback.
- Critério de reprovação: benchmark executado apenas em outro hardware, limiar não calibrado, dataset não versionado ou ausência de ganho mensurável para o sistema deve produzir decisão de no-go ou adaptação.
- Verificação: benchmark versionado, manifest do dataset e decisão da PoC.
- Dependências: RF-18, ML-04 e PERF-01.

### RNF-16: Validar o detector evolutivo de anomalia

- Aplicabilidade: somente quando o RF-19 for aprovado por PoC e decisão registrada.
- Mede: desempenho do detector em conjunto de validação separado e latência acrescentada à decisão por item.
- Meta: o alvo de desempenho, a métrica, o orçamento de latência e a população de teste devem ser definidos antes do ensaio.
- Método: verificar a proveniência do dataset de treino composto somente por itens normais e avaliar o modelo em conjunto separado, contendo itens normais e anômalos, sem vazamento entre as divisões.
- Aceite: origem de cada amostra, divisão dos dados, transformações sintéticas, sementes, configuração, versão do modelo e métricas devem ser auditáveis.
- Critério de reprovação: defeito real no conjunto de treino normal, vazamento entre treino e validação, alvo definido depois do resultado ou latência incompatível com o RNF-01 deve produzir no-go ou adaptação.
- Verificação: manifest, logs de treinamento, configuração versionada, relatório de desempenho e benchmark no hardware-alvo.
- Dependências: RF-19, RF-20, ML-02, ML-03 e PERF-01.

### RNF-17: Validar o modelo aluno quantizado no Raspberry Pi 5

- Aplicabilidade: somente quando o RF-21 for aprovado e houver modelo professor validado.
- Mede: latência, consumo de memória e perda de qualidade do modelo aluno quantizado em relação à referência definida.
- Meta: o limite de perda de qualidade, o orçamento de latência, o runtime e o comportamento de fallback devem ser definidos antes do ensaio.
- Método: executar o modelo professor somente no ambiente de treino e realizar o benchmark do modelo aluno no Raspberry Pi 5, usando dataset, runtime, número de repetições e condições térmicas documentados.
- Aceite: publicar versões dos modelos, parâmetros de quantização, runtime, distribuição de latência, consumo de memória, diferença de qualidade e fallback.
- Critério de reprovação: extrapolar resultados de outro hardware, executar o modelo professor como solução operacional no Raspberry Pi 5 ou definir limites após observar os resultados reprova a validação.
- Verificação: logs de treinamento, manifest dos modelos e benchmark reproduzível no Raspberry Pi 5.
- Dependências RF-21, ML-06 e PERF-01.

### RNF-18: Validar fisicamente o timestamp com tolerância configurável

- Mede: diferença entre o timestamp observado e o instante esperado, calculado a partir da distância calibrada e da velocidade estimada.
- Pré-condição: mecanismo de medição aprovado na PoC 03, distância calibrada e tolerância definida antes do ensaio.
- Método: introduzir atrasos conhecidos abaixo e acima da tolerância e registrar a variabilidade natural do rig.
- Aceite: diferença acima da tolerância deve gerar alerta de qualidade sem alterar o timestamp original; entrada inválida deve produzir estado inconclusivo.
- Critério de reprovação: utilizar mecanismo de medição não aprovado, tolerância sem calibração, omitir a diferença calculada ou corrigir silenciosamente o timestamp reprova o requisito.
- Verificação: ensaio com atraso controlado, logs e registros DAT-03.
- Dependências RF-10, RF-22, DAT-03 e PoC 03.

### RNF-19: Testes de resiliência com hipótese prévia

- Mede: cada experimento possui hipótese, métrica, blast radius e resultado.
- Método: registrar protocolo antes da falha e resultado depois.
- Aceite: falha de hipótese é preservada como achado.
- Critério de reprovação: checklist “não caiu” sem métrica não atende.
- Verificação: fichas de PoC e DECISIONS.md. Dependências: RF-24, DOC-05.

### RNF-20: Manter estabilidade mecânica e elétrica do rig

- Abrangência: suportes parafusados, painel rígido, gabaritos, conexões críticas, continuidade elétrica, ventilação e geometria de calibração.
- Meta: após movimentação compatível com o uso previsto, a variação da geometria e da calibração deve permanecer dentro da tolerância definida antes do ensaio.
- Método: registrar a condição inicial, movimentar e reposicionar o conjunto conforme o procedimento previsto, medir o desvio geométrico, repetir a calibração de verificação e testar continuidade, polaridade e isolamento.
- Aceite: nenhuma conexão crítica pode permanecer solta ou aberta, e o desvio observado deve permanecer dentro da tolerância previamente definida.
- Critério de reprovação: necessidade de recalibração completa após movimentação prevista, componente sem fixação repetível, circuito aberto, polaridade incorreta ou alteração acima da tolerância reprova o requisito.
- Verificação: desenho com cotas, fotos, medições antes e depois, multímetro e relatório de estabilidade.
- Dependências: RF-26, RF-27, RF-28 e HW-01..06.

### RNF-21: Controlar a qualidade óptica e térmica da iluminação

- Aplicabilidade: quando o RF-30 for aprovado como requisito evolutivo.
- Mede: saturação, uniformidade, reflexos, estabilidade da exposição, corrente, duração do pulso e temperatura do arranjo de iluminação.
- Método: capturar imagens representativas do corpo e da tampa com configurações controladas de canais, intensidade e duração; analisar histograma, regiões saturadas, uniformidade e reflexos; medir corrente, tensão e temperatura durante acionamentos repetidos.
- Aceite: a configuração não pode produzir regiões saturadas ou reflexos que impeçam a extração das evidências necessárias, nem exceder os limites elétricos e térmicos definidos para os LEDs, o driver e a alimentação.
- Critério de reprovação: saturação persistente, reflexos que provoquem erro de classificação, iluminação insuficiente ou não uniforme, corrente acima do limite, aquecimento excessivo ou consumo incompatível com a alimentação reprova a configuração.
- Verificação: imagens e histogramas, medições elétricas e térmicas, timestamps dos pulsos e comparação entre configurações.
- Dependências: RF-30, HW-04, SAFE-01..03 e RNF-11.

## Promoção de estado

Um RNF somente pode ser considerado medido quando estiverem registrados:

- requisito e versão aplicável;
- meta e critério definidos antes do ensaio;
- método e procedimento executado;
- setup físico e condições de operação;
- hardware, software, modelos e calibrações utilizados;
- população, amostra ou duração do teste;
- resultado observado e unidade;
- artefatos de evidência;
- decisão resultante.

Os estados permitidos são `aberto`, `proposto`, `em teste`, `validado`, `rejeitado` e `bloqueado`. Uma meta numérica não representa estado nem resultado observado.

Referências externas podem justificar uma escolha ou um limite inicial, mas não substituem a medição no setup do projeto. Resultado ausente, inválido ou inconclusivo não pode ser promovido a validado.
