> **Estado: EXPANSÃO** — documento da fase F0 (escopo com atuação). O núcleo entregue é
> visibilidade/rastreabilidade. Conteúdo preservado por histórico.

# Requisitos funcionais detalhados

Fonte base: RF-01 a RF-30 em `../requisitos.md`; derivação alinhada às diretrizes da apostila.

## Convenção da ficha

Cada ficha informa ator, pré-condição, entrada, comportamento, saída, critério de reprovação, verificação e dependências.

## Captura, visão e decisão

### RF-01: Capturar as três vistas do item

- Ator: nó de visão.
- Pré-condição: item detectado no ponto de captura, câmeras disponíveis e trigger operacional.
- Entrada: evento válido de captura associado a um item.
- Comportamento: capturar uma imagem da vista superior e duas imagens das vistas laterais durante a janela de captura configurada.
- Saída: imagens das vistas `topo`, `lateral1` e `lateral2`, cada uma acompanhada de timestamp, identificação da câmera e estado de qualidade.
- Critério de reprovação: a ausência de uma câmera, falha de captura ou imagem inválida deve produzir registro parcial com a causa da falha, sem indicar captura completa.
- Verificação: executar capturas controladas, comparar a quantidade de imagens com os eventos de trigger e inspecionar os registros de disponibilidade e qualidade por vista.
- Dependências: HW-01, IF-01, DAT-01, RF-01.1 e RF-01.2.

### RF-01.1: Detectar a passagem do item e gerar o trigger físico

- Ator: ESP32 e nó de hardware.
- Pré-condição: E18-D80NK instalado no rig, interface elétrica verificada e parâmetros de detecção configurados.
- Entrada: sinal digital produzido pelo E18-D80NK durante a passagem do item.
- Comportamento: detectar a passagem do item por reflexão difusa, aplicar debounce no ESP32 e emitir um único evento de trigger com timestamp monotônico. O E18-D80NK deve ser tratado como componente candidato até a validação nas condições ópticas da bancada.
- Saída: evento de trigger com timestamp, estado do sensor e identificação da origem.
- Critério de reprovação: ocorrência de perda de detecção, disparo falso, eventos duplicados para um único item ou ausência de registro explícito quando o sinal for inválido.
- Verificação: executar ensaios com as garrafas previstas para a bancada, incluindo variações de transparência, conteúdo, posição e distância, registrando falsos positivos, falsos negativos, eventos duplicados e tempo de debounce.
- Dependências: HW-01, IF-01, RF-26, RF-27 e RF-28.

### RF-01.2: Associar as três vistas ao mesmo item

- Ator: nó de visão e hub.
- Pré-condição: trigger registrado, câmeras identificadas e política de janela temporal configurada.
- Entrada: evento de trigger e imagens produzidas pelas vistas `topo`, `lateral1` e `lateral2`.
- Comportamento: associar as imagens capturadas ao mesmo `item_id` quando seus timestamps estiverem dentro da janela temporal definida. O sistema deve preservar explicitamente vistas ausentes, atrasadas, duplicadas ou inválidas.
- Saída: conjunto de vistas associado ao `item_id`, com timestamps, disponibilidade, qualidade e estado da correlação.
- Critério de reprovação: imagens de itens diferentes não podem receber o mesmo `item_id`; uma vista ausente ou fora da janela não pode resultar em conjunto marcado como completo.
- Verificação: executar testes com imagens dentro e fora da janela, ausência de câmera, duplicação de imagem e eventos reordenados, verificando a associação e o estado produzido.
- Dependências: RF-01, RF-01.1, RF-07, DAT-01 e DAT-03.

### RF-02: Classificar tampa ausente

- Ator: classificador da vista topo. Pré-condição: imagem válida e modelo carregado.
- Entrada: imagem do topo.
- Comportamento: classificar presença/ausência segundo a taxonomia aprovada.
- Saída: classe, confiança, vista, timestamp e evidência.
- Critério de reprovação: conjunto separado com tampas presentes e ausentes deve produzir falso positivo/negativo mensurável.
- Verificação: matriz de confusão e manifest de teste. Dependências: ML-01, ML-02, DAT-02.

### RF-03: Classificar tampa mal rosqueada

- Ator: classificador da vista topo. Pré-condição: definição visual e, se adotada, referência dimensional.
- Entrada: imagem do topo e medida dimensional quando disponível.
- Comportamento: distinguir correta, ausente e mal rosqueada sem esconder casos ambíguos.
- Saída: classe, confiança e motivo/evidência.
- Critério de reprovação: amostras de rosca parcial/alinhamento limítrofe devem revelar confusão na matriz.
- Verificação: matriz por classe e exemplos limítrofes. Dependências: RF-15, ML-01.

### RF-04: Classificar deformidades do corpo

- Ator: classificadores das vistas laterais.
- Pré-condição: imagens laterais disponíveis, iluminação configurada e modelos carregados.
- Entrada: imagens das vistas `lateral1` e `lateral2`, acompanhadas de seus estados de qualidade.
- Comportamento: classificar separadamente as evidências de deformidade do corpo em cada vista lateral, preservando classe, confiança, qualidade da imagem, disponibilidade e vista de origem.
- Saída: resultado de classificação por vista lateral, com classe, confiança, qualidade e evidência associada.
- Critério de reprovação: uma vista ausente, inválida ou abaixo do critério mínimo de qualidade não pode ser tratada como evidência de normalidade; os resultados das duas laterais não podem ser combinados sem preservar sua origem.
- Verificação: executar o conjunto de teste documentado para cada vista, gerar matriz de confusão por classe e inspecionar casos de vista ausente, imagem inválida e discordância lateral.
- Dependências: RF-01, RF-01.2, HW-04, ML-01 e DAT-02.

### RF-04.1: Realizar medição dimensional de apoio à classificação

- Ator: módulo dimensional das vistas laterais.
- Pré-condição: geometria de captura fixa, referência dimensional disponível e calibração pixel para milímetro válida.
- Entrada: imagem lateral, referência dimensional e versão da calibração.
- Comportamento: quando a medição dimensional for adotada, estimar a dimensão de interesse e calcular o erro relativo em relação à referência, sem substituir silenciosamente a classificação visual.
- Saída: medida, unidade, erro relativo, vista de origem, versão da calibração e estado de validade da medição.
- Critério de reprovação: medição produzida sem calibração válida, sem unidade, sem vista de origem ou com erro acima do limite aplicável deve ser marcada como inválida e não pode sustentar aprovação do item.
- Verificação: comparar as medidas estimadas com réplicas ou referências de dimensões conhecidas no setup calibrado da PoC 02.
- Dependências RF-04, RF-27, RF-28, HW-04 e DAT-02.

### RF-05: Combinar as decisões por domínio

- Ator: agregador de visão.
- Pré-condição: resultados associados ao mesmo `item_id`, identificados por vista e acompanhados dos estados de qualidade e disponibilidade.
- Entrada: decisão da vista superior para o domínio da tampa e decisões das duas vistas laterais para o domínio do corpo.
- Comportamento: produzir separadamente a decisão do domínio da tampa e a decisão do domínio do corpo. A vista superior deve decidir o domínio da tampa, enquanto as duas vistas laterais devem fornecer as evidências do domínio do corpo. O sistema deve reprovar o item quando qualquer domínio detectar defeito, sem aplicar maioria global entre as três câmeras e sem permitir que um domínio cancele defeito detectado pelo outro.
- Saída: decisões por domínio, status final do item, defeitos detectados, severidade, confiança, disponibilidade das vistas e indicador de discordância lateral.
- Critério de reprovação: qualquer combinação que aprove o item apesar de um domínio ter detectado defeito deve reprovar o requisito; também deve ser considerada falha a perda da origem por vista ou a aplicação de maioria global entre as três câmeras.
- Verificação: executar fixtures com combinações de aprovação, reprovação, ausência de vista, baixa confiança e discordância entre as laterais, verificando as decisões por domínio e o status final.
- Dependências: RF-01.2, RF-02, RF-03, RF-04, RF-04.1 e DAT-06.

### RF-05.1: Tratar evidência insuficiente sem aprovação silenciosa

- Ator: agregador de visão.
- Pré-condição: política mínima de disponibilidade, qualidade e confiança configurada para cada domínio.
- Entrada: resultados por vista, indicadores de disponibilidade, qualidade da imagem, confiança e discordância lateral.
- Comportamento: quando nenhum defeito tiver sido detectado, mas a evidência necessária para avaliar um domínio estiver ausente, inválida ou abaixo dos critérios mínimos, produzir o estado `inconclusivo` e registrar a causa. Até a validação da regra definitiva para discordância entre as laterais, uma discordância não resolvida deve permanecer explícita e não pode resultar em aprovação silenciosa.
- Saída: estado `aprovado`, `reprovado` ou `inconclusivo`, acompanhado da decisão por domínio e da causa aplicável.
- Critério de reprovação: vista ausente, imagem inválida, baixa qualidade, baixa confiança ou discordância não resolvida não podem ser convertidas automaticamente em aprovação.
- Verificação: executar fixtures para `missing_view`, `invalid_image`, `low_quality`, `low_confidence` e `lateral_disagreement`, verificando estado, domínio afetado e causa registrada.
- Dependências: RF-05, RF-20, DAT-02, DAT-06 e decisões registradas em `docs/DECISIONS.md`.

### RF-06: Registrar item no hub

- Ator: serviço de visão/hub. Pré-condição: `item_id` e lote válidos.
- Entrada: resultado final, vistas, evidência e qualidade.
- Comportamento: persistir uma linha de item e seus registros de vista sem perder campos.
- Saída: registro consultável e status de transmissão.
- Critério de reprovação: omitir campo obrigatório deve rejeitar ou marcar parcial, nunca criar registro aparentemente completo.
- Verificação: banco temporário e consulta de leitura. Dependências: DAT-01/02, IF-04.

### RF-07: Correlacionar eventos multi-nó

- Ator: hub. Pré-condição: ID sequencial e RTC configurados.
- Entrada: eventos de visão, sensores e timestamps.
- Comportamento: associar somente eventos do mesmo item e sinalizar divergência temporal.
- Saída: item correlacionado ou qualidade divergente.
- Critério de reprovação: atrasar/reordenar dois itens deve impedir associação cruzada.
- Verificação: fixture de eventos fora de ordem. Dependências: DAT-03, IF-02.

### RF-08: Emitir telemetria de saúde

- Ator: cada nó. Pré-condição: comunicação disponível ou fila local.
- Entrada: heartbeat, fila pendente, latência e estado.
- Comportamento: publicar estado online/degradado/offline conforme política.
- Saída: registro `heartbeat_no` e alerta quando offline.
- Critério de reprovação: interromper heartbeat deve gerar offline dentro do RNF-07.
- Verificação: log e consulta de heartbeat. Dependências: REL-02, IF-04.

### RF-09: Expor dashboard e notificação

- Ator: operador. Pré-condição: hub com dados.
- Entrada: itens, defeitos, nós e eventos de qualidade.
- Comportamento: mostrar estado vivo e notificar defeito crítico via ntfy.
- Saída: dashboard e mensagem com item/severidade.
- Critério de reprovação: evento crítico que não chega a uma das superfícies é falha de integração.
- Verificação: captura do dashboard e payload da notificação. Dependências: IF-06, OPS-03.

### RF-10: Medir o movimento e estimar o throughput do rig

- Ator: mecanismo de medição de movimento e hub.
- Pré-condição: mecanismo mecanicamente acoplado, parâmetros de conversão configurados e interface de leitura operacional.
- Entrada: pulsos, direção quando disponível e timestamps produzidos pelo encoder incremental.
- Comportamento: medir o deslocamento e estimar a velocidade e o throughput real do rig a partir dos pulsos observados, sem utilizar FPS nominal como substituto da medição física. O KY-040 deve ser tratado como componente candidato até a validação na PoC 03.
- Saída deslocamento, velocidade estimada, throughput, timestamps, estado do mecanismo de medição e identificação do setup.
- Critério de reprovação: perda de pulsos, pulsos falsos, escorregamento, instabilidade da montagem, ausência de repetibilidade ou desconexão não detectada devem impedir que a medição seja apresentada como válida.
- Verificação: executar deslocamentos conhecidos e repetições nas velocidades previstas, comparando contagens, distância estimada, perda de pulsos, repetibilidade e resposta à desconexão.
- Dependências: IF-02, PERF-02, RF-26, RF-27 e PoC 03.

### RF-11: Detectar microparadas do rig

- Ator: hub.
- Pré-condição: mecanismo de medição operacional, heartbeat disponível e limiar temporal configurado.
- Entrada: ausência de deslocamento indicada pelo mecanismo de medição, eventos de heartbeat e estado da comunicação.
- Comportamento: detectar uma microparada quando a ausência de deslocamento ultrapassar o limiar temporal configurado, registrando início, duração, término, causa e qualidade da evidência. O sistema deve distinguir parada física de falha do sensor ou interrupção de comunicação.
- Saída: evento de microparada ou evento de falha de observação, com timestamps, duração, causa e qualidade.
- Critério de reprovação: a interrupção exclusiva da rede ou a falha do encoder não pode ser registrada automaticamente como parada física sem evidência correspondente; eventos abaixo do limiar também não podem ser classificados como microparada.
- Verificação: executar ensaios separados de parada física, interrupção da rede, desconexão do mecanismo de medição e ausência abaixo do limiar, comparando os estados produzidos.
- Dependências: RF-08, RF-10, IF-02 e REL-02.

### RF-12: Registrar correção do operador

- Ator: operador. Pré-condição: item com decisão original.
- Entrada: decisão corrigida, operador, horário e motivo.
- Comportamento: manter original e correção como eventos imutáveis relacionados.
- Saída: auditoria consultável.
- Critério de reprovação: editar a correção não pode apagar a decisão original.
- Verificação: query de auditoria. Dependências: DAT-04, STK-01.

## Atuação, dados e extensão

Os requisitos desta subseção não integram automaticamente o núcleo mínimo da demonstração. Sua implementação depende da aprovação da PoC aplicável, do orçamento de desempenho, da disponibilidade de prazo e de decisão registrada em `docs/DECISIONS.md`. A preservação dos IDs mantém a rastreabilidade e não representa validação ou compromisso de implementação.

### RF-13: Detectar anomalia desconhecida como camada condicional

- Ator: camada de detecção de anomalia.
- Pré-condição: PoC aprovada, orçamento de latência definido e decisão de inclusão registrada.
- Entrada: representações/imagens de itens.
- Comportamento: sinalizar anomalia em estado separado, sem substituir os classificadores do núcleo, sem participar de maioria global e sem alterar silenciosamente as decisões dos domínios de tampa e corpo.
- Saída: score e estado separado.
- Critério de reprovação: PoC não atingir critério ou estourar latência gera no-go e fallback.
- Verificação: relatório de PoC. Dependências: ML-05, PERF-01.

### RF-14: Separar item reprovado para análise manual

- Ator: controlador do mecanismo de separação.
- Pré-condição: decisão final de reprovação associada ao `item_id`, mecanismo disponível e condições de segurança atendidas.
- Entrada: ordem de separação com `item_id`, timestamp, defeito e severidade.
- Comportamento: acionar o mecanismo de separação e aguardar a confirmação de passagem por sensor independente instalado no caminho de análise manual. A emissão da ordem de atuação não deve ser interpretada como separação concluída.
- Saída: estado `pendente`, `confirmada` ou `falha`, acompanhado dos eventos de comando, confirmação ou timeout.
- Critério de reprovação: ausência de confirmação dentro do timeout deve produzir estado de falha; item normal direcionado ao caminho de análise manual ou separação registrada como concluída somente pela emissão da ordem também reprovam o requisito.
- Verificação: comparar ordens de atuação, transições do sensor de confirmação e evidência física em vídeo durante a PoC 07.
- Dependências ACT-01..10, SAFE-01..03, DAT-06 e PoC 07.

### RF-15: Medir altura da tampa

- Ator: módulo dimensional. Pré-condição: backlight e pixel→mm calibrados.
- Entrada: imagem e referência dimensional.
- Comportamento: decidir por threshold dimensional e usar ML como segunda camada.
- Saída: medida em mm, threshold aplicado e decisão.
- Critério de reprovação: deslocar a tampa por valor conhecido deve alterar a medida dentro da tolerância.
- Verificação: calibração, imagens e cálculo. Dependências: HW-04, DAT-02.

### RF-16: Manter golden samples

- Ator: operador ou responsável pela demonstração.
- Pré-condição: kit rotulado, classes aprovadas e identificação individual das amostras.
- Entrada: amostras de referência normais e defeituosas representativas das classes disponíveis.
- Comportamento: permitir a injeção controlada das amostras de referência, identificando cada evento com `is_golden` e preservando a classe esperada.
- Saída: resultado de teste associado à amostra, à classe esperada e ao setup, isolado dos indicadores produtivos.
- Critério de reprovação: golden sample sem identificação, sem classe esperada ou incluído nos indicadores produtivos representa falha de rastreabilidade ou isolamento.
- Verificação: conferir o inventário do kit, executar cada amostra e consultar os registros com e sem o filtro `is_golden`.
- Dependências: DAT-05 e ACT-09.

### RF-17: Gerar relatório de lote como evolução

- Ator: hub.
- Pré-condição: requisito aprovado como evolução, lote identificável e qualidade dos dados conhecida.
- Entrada: KPIs, severidade, evidências e lotes anteriores.
- Comportamento: gerar relatório em PDF com indicadores, severidade, evidências, qualidade dos dados e identificação do lote, registrando campos ausentes sem inventar valores, e emitir a notificação configurada.
- Saída: relatório identificável pelo lote e status de envio.
- Critério de reprovação: lote parcial deve exibir qualidade e não preencher gráfico com valores inventados.
- Verificação: PDF gerado e log de envio. Dependências: RF-06, IF-06, DOC-04.

### RF-18: Calcular descritores geométricos como camada evolutiva

- Ator: camada geométrica.
- Pré-condição: estratégia aprovada por PoC, segmentação ou contorno disponível e distribuição de referência calibrada.
- Entrada: imagem válida identificada por vista.
- Comportamento: calcular os descritores geométricos aprovados, como momentos de Hu, compacidade, simetria e proporção, e produzir score de anomalia calibrado sem substituir a decisão principal.
- Saída: descritores, score, vista de origem, versão do algoritmo e versão da calibração.
- Critério de reprovação: descritor sem vista de origem, calibração ou versão não pode ser usado como evidência válida; ausência de ganho mensurável ou estouro do orçamento de latência deve produzir decisão de no-go.
- Verificação: executar benchmark documentado com conjunto separado, medir desempenho e latência e registrar a decisão da PoC.
- Dependências: ML-04 e PERF-01.

### RF-19: Treinar detector de anomalia autossupervisionado como evolução

- Ator: pipeline de treino.
- Pré-condição: estratégia aprovada, dataset de treino composto somente por itens normais e proveniência verificada.
- Entrada: imagens normais e patches sintéticos.
- Comportamento: treinar o detector no formato de imagem definido, utilizando transformações sintéticas versionadas e preservando configuração, sementes e proveniência dos dados.
- Saída: modelo, configuração e métrica.
- Critério de reprovação: qualquer defeito real no treino invalida a proveniência.
- Verificação: manifest de treino e relatório. Dependências: ML-02/03/05.

### RF-20: Verificar a consistência das evidências por domínio

- Ator: agregador de visão.
- Pré-condição: resultados associados ao mesmo `item_id`, com vista, domínio, disponibilidade, qualidade e confiança preservados.
- Entrada: evidências da vista superior no domínio da tampa e evidências das duas vistas laterais no domínio do corpo.
- Comportamento: comparar as duas vistas laterais dentro do domínio do corpo e verificar a disponibilidade, a qualidade e a confiança da vista superior no domínio da tampa. A consistência entre domínios não pode cancelar defeito detectado.
- Saída: indicador de consistência por domínio, discordância lateral, disponibilidade das evidências e motivo de sinalização.
- Critério de reprovação: evidência incompleta não pode ser tratada como normal; resultados de tampa e corpo não podem ser combinados como se avaliassem o mesmo fenômeno; um score global não pode cancelar uma reprovação existente.
- Verificação: executar fixtures com laterais concordantes, laterais discordantes, vista ausente, baixa qualidade e defeitos isolados em cada domínio.
- Dependências: RF-01.2, RF-05, RF-05.1 e DAT-06.

### RF-21: Destilar teacher para aluno INT8 como evolução

- Ator: pipeline de treino e implantação.
- Pré-condição: requisito aprovado, modelo professor validado, ambiente de treino disponível e Raspberry Pi 5 preparado para benchmark.
- Entrada: itens OK e teacher pesado.
- Comportamento: executar o modelo professor somente durante o treinamento e produzir um modelo aluno quantizado para execução no Raspberry Pi 5, preservando as versões dos modelos e os parâmetros de quantização.
- Saída: aluno, latência real e fallback documentado.
- Critério de reprovação: execução do teacher no Pi ou latência fora do orçamento gera no-go.
- Verificação: logs de treino e benchmark no Pi. Dependências: ML-06.

### RF-22: Validar o timestamp pela física do rig

- Ator: hub.
- Pré-condição: distância calibrada, mecanismo de medição aprovado na PoC 03 e tolerância temporal configurada.
- Entrada: evento de trigger, velocidade estimada, distância calibrada e timestamp observado.
- Comportamento: calcular o instante esperado de passagem, comparar o valor esperado ao timestamp observado e sinalizar desvio quando a diferença ultrapassar a tolerância configurada, sem reescrever o timestamp original.
- Saída: timestamp esperado, timestamp observado, diferença calculada, tolerância aplicada e estado de qualidade.
- Critério de reprovação: atraso conhecido acima da tolerância deve produzir alerta; mecanismo de medição não aprovado ou entrada inválida deve produzir estado inconclusivo, e não validação positiva.
- Verificação: executar ensaios com atrasos controlados abaixo e acima da tolerância e repetir o teste após desconexão ou invalidação do mecanismo de medição.
- Dependências: RF-01.1, RF-10, DAT-03 e PoC 03.

### RF-23: Aplicar supervisão fraca ao dataset como evolução

- Ator: pipeline de dados.
- Pré-condição: requisito aprovado, funções de rotulagem versionadas e fontes de evidência disponíveis.
- Entrada: medida dimensional, Hu/compacidade e score de anomalia.
- Comportamento: agregar rótulos ponderados e preservar incerteza.
- Saída: dataset semi-rotulado e relatório de conflito.
- Critério de reprovação: regra discordante não pode virar rótulo confirmado sem rastreio.
- Verificação: manifest, pesos e amostras. Dependências: ML-03/05.

## Requisitos de processo, montagem e testabilidade

Os requisitos RF-24 a RF-29 são preservados como requisitos rastreáveis do projeto, mas descrevem práticas de engenharia, montagem, documentação e testabilidade, e não exclusivamente comportamentos funcionais do software de inspeção.

### RF-24: Conduzir resiliência como experimento

- Ator: equipe de teste. Pré-condição: estado estável e métrica definida.
- Entrada: falha controlada de nó, rede, sensor ou banco.
- Comportamento: executar blast radius mínimo e registrar hipótese antes.
- Saída: resultado, recuperação, perdas e decisão.
- Critério de reprovação: teste sem hipótese ou métrica não é evidência de resiliência.
- Verificação: ficha de PoC e DECISIONS.md. Dependências: REL-01/02, DOC-05.

### RF-25: Adotar commits convencionais

- Ator: equipe.
- Entrada: alteração revisada.
- Comportamento: usar `feat:`, `fix:`, `decision:` ou `test:` e gerar linha do tempo quando houver ferramenta.
- Saída: histórico legível.
- Critério de reprovação: commit que declara implementação inexistente falha na revisão do diff.
- Verificação: `git log` e diff. Dependências: DOC-07.

### RF-26: Fixar conexões críticas

- Ator: montador.
- Entrada: trigger, encoder e sensores móveis.
- Comportamento: soldar em header/breakout e testar continuidade.
- Saída: conexões identificadas e resultado do multímetro.
- Critério de reprovação: circuito aberto ou jumper solto bloqueia integração.
- Verificação: checklist/fotos/medição. Dependências: HW-02, SAFE-03.

### RF-27: Construir painel de base rígido

- Ator: montador.
- Entrada: posições definidas para câmeras, trigger e encoder.
- Comportamento: manter geometria repetível para calibração.
- Saída: painel e desenho com cotas.
- Critério de reprovação: reposicionar componente altera calibração além da tolerância.
- Verificação: desenho, fotos e recalibração. Dependências: HW-01/04.

### RF-28: Montar suportes e jig

- Ator: montador.
- Entrada: mounts, jig e réplicas parametrizadas.
- Comportamento: fixar por parafuso e posicionar item repetidamente.
- Saída: setup reproduzível e peças rotuladas.
- Critério de reprovação: reposicionamento manual muda a medida ou o enquadramento fora da tolerância.
- Verificação: desenho, fotos e ensaio repetido. Dependências: HW-03, ML-03.

### RF-29: Aplicar DFT como princípio transversal

- Ator: equipe.
- Pré-condição: requisito ou subsistema identificado e critério de verificação definido.
- Entrada: requisitos, interfaces, estados, falhas previstas e procedimentos de teste de cada subsistema.
- Comportamento: garantir controlabilidade das entradas e condições de teste e observabilidade das saídas, estados e falhas, seguindo a ordem física, dados, modelo, teste e documentação.
- Saída: matriz DFT relacionando requisito, estímulo controlável, saída observável, evidência, teste e decisão.
- Critério de reprovação: requisito sem entrada controlável, saída observável, estado de falha explícito ou evidência reproduzível não pode ser considerado aceito.
- Verificação: revisar a matriz DFT, executar o teste relacionado e conferir a rastreabilidade entre requisito, estímulo, observação, evidência e documentação.
- Dependências: todas as categorias de requisitos, interfaces e PoCs.

## Requisito evolutivo de iluminação

### RF-30: Acionar iluminação estroboscópica sincronizada ao trigger

- Ator: ESP32 e controlador de iluminação.
- Pré-condição: requisito aprovado como evolução, circuito de acionamento montado, limitação de corrente dimensionada, alimentação disponível e sinal de trigger válido.
- Entrada: evento de trigger associado ao `item_id` e parâmetros configurados de duração, intensidade e canais de iluminação.
- Comportamento: acionar um pulso de iluminação sincronizado à janela de captura e retornar ao estado desligado ao término do pulso. O acionamento dos LEDs deve utilizar interface elétrica compatível com a corrente exigida, sem alimentar cargas acima da capacidade diretamente pelos GPIOs. A combinação dos canais RGB deve ser calibrada pelas imagens e não presumida como iluminação branca adequada apenas pela ativação simultânea em potência máxima.
- Saída: evento de iluminação com instante de início, duração configurada, canais acionados, intensidade aplicada e estado do controlador.
- Critério de reprovação: pulso fora da janela de captura, acionamento contínuo não previsto, corrente acima do limite, aquecimento excessivo, consumo incompatível com a alimentação, imagem saturada, reflexos persistentes ou iluminação sem uniformidade suficiente devem reprovar a configuração.
- Verificação: comparar timestamps do trigger, do pulso e da captura; inspecionar histograma e regiões saturadas das imagens; medir corrente, tensão, duração do pulso e temperatura durante ensaio repetido.
- Dependências: RF-01, RF-01.1, HW-04, SAFE-01..03 e RNF-21.

## Fechamento

Nenhum requisito é considerado implementado ou validado apenas por existir na documentação. O estado deve mudar somente quando houver evidência reproduzível, vinculada ao requisito, ao setup, à versão do software ou hardware e ao procedimento de verificação.

Componentes candidatos, requisitos evolutivos e regras ainda pendentes devem permanecer explicitamente identificados até que uma PoC produza decisão `go`, `no-go`, `adaptar` ou `repetir`. Evidência ausente, inválida ou inconclusiva não pode ser convertida em aprovação.
