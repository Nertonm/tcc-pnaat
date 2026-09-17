# Requisitos do nucleo

Esta é a versão canônica em Markdown do catálogo usado no PDF. Os requisitos são normativos: alguns já têm implementação de software em `src-production/`, enquanto hardware, integração externa e validação de desempenho continuam condicionados à evidência do setup declarado. `Núcleo` e `Expansão` classificam escopo, não substituem a verificação do código.

## Requisitos funcionais

| ID | Requisito | Escopo |
|---|---|---|
| RF-01 | Capturar mais de uma vista do mesmo item após o evento de presença, com timestamp e identificador de captura. | Núcleo |
| RF-01.1 | Verificar confiabilidade do trigger de captura por sensor de presença, com timing determinístico do microcontrolador. | Núcleo |
| RF-02 | Classificar tampa ausente nas vistas disponíveis. | Núcleo |
| RF-03 | Classificar tampa mal rosqueada usando a composição multi-view. | Núcleo |
| RF-04 | Classificar deformidade do corpo nas vistas laterais e preservar a medida de referência. | Núcleo |
| RF-05 | Combinar resultados das vistas e produzir classe, confiança e resultado do item. | Núcleo |
| RF-06 | Registrar evento com identificador, timestamp, localização, defeito, evidência, confiança, vista e qualidade. | Núcleo |
| RF-07 | Correlacionar eventos de uma futura expansão multi-nó por identificador e origem. | Expansão |
| RF-08 | Emitir telemetria de saúde do nó: heartbeat, fila, latência e falha. | Núcleo |
| RF-09 | Apresentar dashboard com itens, defeitos, localização, recorrência e saúde do nó. | Núcleo |
| RF-10 | Medir taxa de eventos da bancada sem controlar a velocidade da esteira. | Expansão |
| RF-11 | Identificar intervalos sem evento acima do limite definido e registrá-los para análise. | Expansão |
| RF-12 | Registrar correção do operador preservando decisão original, correção, responsável e horário. | Núcleo (implementado) |
| RF-13 | Avaliar detector opcional de anomalia desconhecida como camada adicional. | Parcial (camada isolada) |
| RF-14 | Registrar encaminhamento de item para análise humana; atuação física de separação fica na expansão (PoC-07). | Expansão |
| RF-15 | Medir altura da tampa em milímetros quando a calibração estiver disponível. | Expansão |
| RF-16 | Manter golden samples com defeito conhecido, isolados das estatísticas operacionais. | Expansão |
| RF-17 | Gerar relatório de lote com indicadores, severidade, evidências e tendência. | Expansão |
| RF-18 | Calcular descritores geométricos por vista e score de anomalia sobre conjunto normal. | Parcial (camada isolada) |
| RF-19 | Avaliar detecção autossupervisionada com imagens de itens normais e anomalias sintéticas. | Expansão |
| RF-20 | Avaliar consistência entre vistas pelo score conjunto dos classificadores. | Expansão |
| RF-21 | Avaliar destilação de modelo para execução no hardware alvo. | Expansão |
| RF-22 | Comparar timestamp previsto e observado quando houver referência de deslocamento disponível. | Expansão |
| RF-23 | Avaliar expansão do dataset por supervisão fraca, documentando incerteza. | Expansão |
| RF-24 | Conduzir testes de resiliência com hipótese, métrica e impacto definidos antes do ensaio. | Núcleo |
| RF-25 | Manter histórico de decisões e mudanças do projeto. | Núcleo |
| RF-26 | Verificar continuidade de conexões críticas do rig. | Expansão |
| RF-27 | Planejar base rígida e pontos de fixação para captura. | Expansão |
| RF-28 | Planejar suportes e gabaritos para posicionamento e deformidades controladas. | Expansão |
| RF-29 | Aplicar design for testability: entradas controláveis e saídas observáveis. | Núcleo |
| RF-30 | Avaliar iluminação pulsada e difusa para reduzir saturação nas imagens. | Expansão |

## Requisitos não funcionais

| ID | Qualidade ou restrição | Escopo |
|---|---|---|
| RNF-01 | Latência de registro por item menor que 500 ms, sob condição declarada. | Núcleo |
| RNF-02 | Acurácia com intervalo de confiança: tampa ausente 95% ou mais, tampa mal rosqueada 90% ou mais e deformidade 90% ou mais. | Núcleo |
| RNF-03 | Falsos positivos até 2% para tampa ausente e 5% para as demais classes. | Núcleo |
| RNF-04 | Correlação multi-nó de 98% ou mais em ensaio de 50 itens. | Expansão |
| RNF-05 | Integridade do registro de 99% ou mais em 30 minutos de estresse. | Núcleo |
| RNF-06 | Retransmissão de 100% dos eventos bufferizados após reconexão, sem duplicação. | Núcleo |
| RNF-07 | Detecção de nó indisponível abaixo de 10 segundos. | Núcleo |
| RNF-08 | Resiliência a reconexão, debounce, sensor nulo e watchdog sem interrupção silenciosa. | Núcleo |
| RNF-09 | Taxa de eventos da bancada registrada junto da qualidade da captura. | Expansão |
| RNF-10 | Documentação reproduzível com README, decisões e proveniência de dataset. | Núcleo |
| RNF-11 | Calibração pixel--milímetro documentada por posição fixa. | Expansão |
| RNF-12 | Qualidade do registro propagada aos consumidores do dashboard. | Núcleo |
| RNF-13 | Caso exista encaminhamento físico futuro, confirmação correta de 99% e nenhum item normal encaminhado. | Expansão |
| RNF-14 | Precisão dimensional da tampa dentro de 0,5 mm e nenhuma rejeição de golden sample normal. | Expansão |
| RNF-15 | Custo da camada de descritores abaixo de 10 ms por vista. | Expansão |
| RNF-16 | Detector de anomalia treinado apenas com itens normais, com validação e latência compatíveis. | Expansão |
| RNF-17 | Modelo aluno validado no hardware alvo com fallback documentado. | Expansão |
| RNF-18 | Validação de timestamp com tolerância configurável, quando a referência estiver disponível. | Expansão |
| RNF-19 | Cada teste de resiliência possui hipótese e métrica antes do experimento. | Núcleo |
| RNF-20 | Estabilidade mecânica sem recalibração indevida após movimentação prevista. | Expansão |
| RNF-21 | Iluminação difusa sem saturação que prejudique a extração de contornos. | Expansão |

A validação de cada requisito é definida pelas PoCs no PDF. 