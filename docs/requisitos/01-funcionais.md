# Requisitos funcionais detalhados

Fonte base: RF-01 a RF-29 em `../requisitos.md`; derivação alinhada às diretrizes da apostila. 

## Convenção da ficha

Cada ficha informa ator, pré-condição, entrada, comportamento, saída, critério de reprovação, verificação e dependências.

## Captura, visão e decisão

### RF-01: Capturar três vistas sincronizadas

- Ator: nó de visão. Pré-condição: item no ponto de captura e trigger operacional.
- Entrada: evento do E18-D80NK ou VL53L0X.
- Comportamento: capturar topo, lateral1 e lateral2 do mesmo item dentro da janela definida.
- Saída: três imagens identificadas pelo mesmo `item_id` e timestamps.
- Critério de reprovação: deslocar uma câmera ou remover uma vista deve gerar registro parcial, não sucesso completo.
- Verificação: três imagens, log do trigger e teste de correlação. Dependências: HW-01, IF-01, DAT-01.

### RF-01.1: Garantir confiabilidade do trigger E18-D80NK via barreira por oclusão retrorrefletiva e ESP32

- Ator: ESP32 / nó de hardware. Pré-condição: E18-D80NK instalado no rig com inclinação de 10°–15°, fita retrorrefletiva 3M no anteparo oposto e esteira em operação.
- Entrada: interrupção gerada pela oclusão/refração do feixe infravermelho no sensor E18-D80NK e pulsos do encoder KY-040.
- Comportamento:detectar a passagem de qualquer garrafa (transparente, opaca ou com líquido) pela interrupção do retorno da fita retrorrefletiva; aplicar debounce de 30–50 ms; calcular a velocidade real da esteira a partir do encoder e determinar a janela de chegada (`tempo_chegada = distância / velocidade`); disparar o trigger/timestamp para o Raspberry Pi 5 e acionar a iluminação estroboscópica no instante calculado; correlacionar eventos do VL53L0X (validação/fallback) com os do E18-D80NK para evitar duplicidade de evento.
- Saída: timestamp determinístico, estimativa de velocidade, sinal de trigger para o Raspberry Pi 5 e pulso de iluminação estroboscópica.
- Critério de reprovação: falsos disparos ou perda de detecção em garrafas transparentes/com líquido, ou falha de correlação entre E18 e VL53L0X gerando duplicidade de evento.
- Verificação: ensaio comparativo em garrafas vazias, cheias e transparentes; medição do tempo de debounce no ESP32.
- Dependências: HW-01, HW-04, IF-01, RF-26..28.

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

### RF-04: Classificar deformidade de corpo

- Ator: classificadores laterais. Pré-condição: calibração pixel→mm e iluminação definida.
- Entrada: imagens lateral1/lateral2.
- Comportamento: classificar deformidade e calcular erro dimensional quando aplicável.
- Saída: classe, medida, erro e vista de origem.
- Critério de reprovação: peça 3D com deformação conhecida deve exceder ou atender o limite de erro de forma mensurável.
- Verificação: relatório de calibração e matriz de deformidade. Dependências: HW-04, ML-01.

### RF-05: Fazer late fusion por votação

- Ator: agregador de visão. Pré-condição: resultados identificados por item e vista.
- Entrada: resultados dos três classificadores.
- Comportamento: aplicar regra de votação/união lógica e conservar discordâncias.
- Saída: status final, defeito, severidade e confiança agregada.
- Critério de reprovação: resultados discordantes devem produzir a regra definida, sem escolher silenciosamente uma vista.
- Verificação: fixture com combinações de resultados. Dependências: RF-01..04, DAT-06.

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

- Ator: avaliador/operador. Pré-condição: hub com dados.
- Entrada: itens, defeitos, nós e eventos de qualidade.
- Comportamento: mostrar estado vivo e notificar defeito crítico via ntfy.
- Saída: dashboard e mensagem com item/severidade.
- Critério de reprovação: evento crítico que não chega a uma das superfícies é falha de integração.
- Verificação: captura do dashboard e payload da notificação. Dependências: IF-06, OPS-03.

### RF-10: Medir throughput real

- Ator: encoder/hub. Pré-condição: distância/contagem calibradas.
- Entrada: pulsos e timestamps do KY-040.
- Comportamento: calcular peças/min sustentado, sem usar FPS nominal.
- Saída: série de throughput com setup e duração.
- Critério de reprovação: variar velocidade deve alterar a métrica medida; contador desconectado deve gerar erro.
- Verificação: log do encoder e cálculo reproduzível. Dependências: IF-02, PERF-02.

### RF-11: Detectar micro-paradas

- Ator: hub. Pré-condição: stream de eventos e limiar configurado.
- Entrada: ausência de eventos por mais de 5 s.
- Comportamento: distinguir parada real de atraso de comunicação ou sensor.
- Saída: evento de micro-parada com causa/qualidade.
- Critério de reprovação: interromper somente a rede não pode ser contado como parada física sem evidência.
- Verificação: ensaio combinado encoder/heartbeat. Dependências: RF-08, RF-10.

### RF-12: Registrar correção do operador

- Ator: operador. Pré-condição: item com decisão original.
- Entrada: decisão corrigida, operador, horário e motivo.
- Comportamento: manter original e correção como eventos imutáveis relacionados.
- Saída: auditoria consultável.
- Critério de reprovação: editar a correção não pode apagar a decisão original.
- Verificação: query de auditoria. Dependências: DAT-04, STK-01.

## Atuação, dados e extensão

### RF-13: Detectar anomalia desconhecida

- Ator: camada one-class. Pré-condição: PoC aprovada e latência dentro do orçamento.
- Entrada: representações/imagens de itens.
- Comportamento: sinalizar anomalia fora da votação sem substituir o núcleo.
- Saída: score e estado separado.
- Critério de reprovação: PoC não atingir critério ou estourar latência gera no-go e fallback.
- Verificação: relatório de PoC. Dependências: ML-05, PERF-01.

### RF-14: Informar defeito ao operador

- Ator: serviço de notificação. Pré-condição: decisão defeito persistida e canal configurado.
- Entrada: `item_id`, defeito, severidade, confiança e evidência.
- Comportamento: publicar o alerta no dashboard e no canal de notificação configurado, sem acionar remoção física da garrafa.
- Saída: `pendente`, `entregue`, `lida` ou `falha`; nunca “entregue” só porque a decisão foi criada.
- Critério de reprovação: falha de envio ou alerta sem vínculo ao item ser apresentado como entregue.
- Verificação: eventos SIG, captura do dashboard/notificação e consulta. Dependências: SIG-01..06, IF-06.

### RF-15: Medir altura da tampa

- Ator: módulo dimensional. Pré-condição: backlight e pixel→mm calibrados.
- Entrada: imagem e referência dimensional.
- Comportamento: decidir por threshold dimensional e usar ML como segunda camada.
- Saída: medida em mm, threshold aplicado e decisão.
- Critério de reprovação: deslocar a tampa por valor conhecido deve alterar a medida dentro da tolerância.
- Verificação: calibração, imagens e cálculo. Dependências: HW-04, DAT-02.

### RF-16: Manter golden samples

- Ator: operador/demo. Pré-condição: kit rotulado.
- Entrada: peça OK e quatro defeitos conhecidos.
- Comportamento: permitir injeção sob demanda e marcar `is_golden`.
- Saída: resultado de teste excluído do FPY de produção.
- Critério de reprovação: golden sample aparecer em KPI produtivo é falha de isolamento.
- Verificação: inventário e consulta filtrada. Dependências: DAT-05, SIG-05.

### RF-17: Gerar relatório de lote

- Ator: hub. Pré-condição: lote com dados completos.
- Entrada: KPIs, severidade, evidências e lotes anteriores.
- Comportamento: gerar PDF e enviar notificação sem afirmar dados ausentes.
- Saída: relatório identificável pelo lote e status de envio.
- Critério de reprovação: lote parcial deve exibir qualidade e não preencher gráfico com valores inventados.
- Verificação: PDF gerado e log de envio. Dependências: RF-06, IF-06, DOC-04.

### RF-18: Calcular descritores geométricos universais

- Ator: camada geométrica. Pré-condição: contorno e distribuição normal calibrada.
- Entrada: imagem por vista.
- Comportamento: calcular Hu, compacidade, simetria, proporção e Mahalanobis.
- Saída: descritores e score com versão da calibração.
- Critério de reprovação: 2-3 objetos novos devem ser avaliados somente nessa camada.
- Verificação: benchmark e manifest. Dependências: ML-04, PERF-01.

### RF-19: Treinar CutPaste/NSA com itens OK

- Ator: pipeline de treino. Pré-condição: dataset somente OK.
- Entrada: imagens normais e patches sintéticos.
- Comportamento: treinar no formato definido, sem autoencoder puro.
- Saída: modelo, configuração e métrica.
- Critério de reprovação: qualquer defeito real no treino invalida a proveniência.
- Verificação: manifest de treino e relatório. Dependências: ML-02/03/05.

### RF-20: Verificar consistência cross-view

- Ator: agregador de anomalia. Pré-condição: três scores do mesmo item.
- Entrada: vetor de scores por vista.
- Comportamento: calcular score multivariado e manter ausência de vista explícita.
- Saída: score e motivo de sinalização.
- Critério de reprovação: vetor incompleto não pode ser tratado como normal.
- Verificação: fixtures completos/incompletos. Dependências: RF-01, RF-19.

### RF-21: Destilar teacher para aluno INT8

- Ator: pipeline de treino/deploy. Pré-condição: GPU disponível para treino e Pi 5 para validação.
- Entrada: itens OK e teacher pesado.
- Comportamento: teacher roda somente no treino; aluno quantizado roda no Pi.
- Saída: aluno, latência real e fallback documentado.
- Critério de reprovação: execução do teacher no Pi ou latência fora do orçamento gera no-go.
- Verificação: logs de treino e benchmark no Pi. Dependências: ML-06.

### RF-22: Validar timestamp pela física do rig

- Ator: hub. Pré-condição: distância conhecida e velocidade do encoder.
- Entrada: trigger, velocidade e timestamp observado.
- Comportamento: calcular timestamp esperado e sinalizar desvio.
- Saída: score/flag de qualidade, sem reescrever o timestamp original.
- Critério de reprovação: introduzir atraso conhecido deve produzir alerta.
- Verificação: ensaio com atraso injetado. Dependências: RF-10, DAT-03.

### RF-23: Aplicar weak supervision no dataset

- Ator: pipeline de dados. Pré-condição: labeling functions versionadas.
- Entrada: medida dimensional, Hu/compacidade e score de anomalia.
- Comportamento: agregar rótulos ponderados e preservar incerteza.
- Saída: dataset semi-rotulado e relatório de conflito.
- Critério de reprovação: regra discordante não pode virar rótulo confirmado sem rastreio.
- Verificação: manifest, pesos e amostras. Dependências: ML-03/05.

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
- Entrada: cada subsistema e teste.
- Comportamento: demonstrar controlabilidade e observabilidade na ordem física → dados → modelo → teste → documentação.
- Saída: matriz DFT ligada aos requisitos e evidências.
- Critério de reprovação: requisito sem entrada controlável ou saída observável fica sem aceite.
- Verificação: matriz e revisão da arquitetura. Dependências: todas as categorias.

### RF-30: Acionar iluminação estroboscópica RGB sincronizada ao trigger

- Ator: ESP32 / controlador de iluminação. Pré-condição: LEDs RGB alimentados e sinal de trigger válido.
- Entrada: pulso de confirmação de presença do frasco no ponto de captura emitido pelo ESP32.
- Comportamento: acionar simultaneamente 2 LEDs RGB de alto brilho (5 mm) configurados em potência máxima nos canais Vermelho, Verde e Azul (R, G, B via GPIO/PWM) para gerar luz branca brilhante de iluminação direta no exato instante da captura das câmeras.
- Saída: pulso de iluminação síncrono (estroboscópio) que retorna ao estado desligado/repouso imediatamente após a janela de captura.
- Critério de reprovação: manter a iluminação acesa continuamente, provocando superaquecimento dos LEDs, reflexos persistentes ou consumo excessivo do pacote de baterias 18650.
- Verificação: log monotônico do tempo de pulso do PWM, monitoramento de temperatura dos LEDs e nível de carga da bateria 18650.
- Dependências: RF-01, RF-01.1, HW-04.

## Fechamento

Nenhum RF é considerado implementado por existir documentação. O estado muda somente com evidência reproduzível e rastreável ao setup.
