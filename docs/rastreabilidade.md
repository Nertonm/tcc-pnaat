# Rastreabilidade requisito -> prova

Gerado por `code-workspace/scripts/rastreabilidade.py`. Nao editar a mao.

| requisito | titulo | status | onde aparece |
|---|---|---|---|
| `ACC-01` | ACC-01: Rastreabilidade completa | sem prova | - |
| `ACC-02` | ACC-02: Estados honestos | sem prova | - |
| `ACC-03` | ACC-03: Prazo operacional | sem prova | - |
| `ACC-04` | ACC-04: Entrega de requisitos | sem prova | - |
| `ACC-05` | ACC-05: Demonstração defensável | sem prova | - |
| `ACT-01` | Dependências ACT-01..10, SAFE-01..03, DAT-06 e PoC 07. | sem prova | - |
| `ACT-02` | ACT-02: Estados de rejeição separados | sem prova | - |
| `ACT-03` | ACT-03: Correlação sem troca de item | sem prova | - |
| `ACT-04` | ACT-04: Timeout, retry e idempotência | sem prova | - |
| `ACT-05` | ACT-05: Estado operacional do atuador | sem prova | - |
| `ACT-06` | ACT-06: Parada manual auditável | sem prova | - |
| `ACT-07` | ACT-07: Evidência da atuação | sem prova | - |
| `ACT-08` | ACT-08: Não ejetar OK e não mascarar falha | sem prova | - |
| `ACT-09` | Dependências: DAT-05 e ACT-09. | sem prova | - |
| `ACT-10` | Verificação: payload enviado, resposta e recebimento. Dependências: RF-09, ACT-10. | sem prova | - |
| `DAT-01` | Dependências: HW-01, IF-01, DAT-01, RF-01.1 e RF-01.2. | citado | src-production/identidade.py, src-production/registro.py |
| `DAT-02` | Verificação: matriz de confusão e manifest de teste. Dependências: ML-01, ML-02, DAT-02. | sem prova | - |
| `DAT-03` | Dependências: RF-01, RF-01.1, RF-07, DAT-01 e DAT-03. | coberto | src-production/tests/test_registro.py |
| `DAT-04` | Verificação: query de auditoria. Dependências: DAT-04, STK-01. | sem prova | - |
| `DAT-05` | Dependências: DAT-05 e ACT-09. | sem prova | - |
| `DAT-06` | Dependências: RF-01.2, RF-02, RF-03, RF-04, RF-04.1 e DAT-06. | sem prova | - |
| `DAT-07` | Verificação: log de queda/reconexão e banco. Dependências: DAT-07, IF-04. | sem prova | - |
| `DAT-08` | DAT-08: Evidência recuperável | sem prova | - |
| `DOC-01` | Verificação: clone limpo e revisão documental. Dependências: DOC-01..07. | sem prova | - |
| `DOC-02` | DOC-02: Dependências declaradas | sem prova | - |
| `DOC-03` | DOC-03: Clone limpo | sem prova | - |
| `DOC-04` | Verificação: PDF gerado e log de envio. Dependências: RF-06, IF-06, DOC-04. | sem prova | - |
| `DOC-05` | Verificação: ficha de PoC e DECISIONS.md. Dependências: REL-01/02, DOC-05. | sem prova | - |
| `DOC-06` | DOC-06: Pitch rastreável | sem prova | - |
| `DOC-07` | Verificação: `git log` e diff. Dependências: DOC-07. | sem prova | - |
| `ENV-01` | ENV-01: Condições do ensaio | sem prova | - |
| `HW-01` | Dependências: HW-01, IF-01, DAT-01, RF-01.1 e RF-01.2. | sem prova | - |
| `HW-02` | Verificação: checklist/fotos/medição. Dependências: HW-02, SAFE-03. | sem prova | - |
| `HW-03` | Verificação: desenho, fotos e ensaio repetido. Dependências: HW-03, ML-03. | sem prova | - |
| `HW-04` | Dependências: RF-01, RF-01.2, HW-04, ML-01 e DAT-02. | sem prova | - |
| `HW-05` | HW-05: BOM e interfaces | sem prova | - |
| `HW-06` | HW-06: Segurança física e térmica | sem prova | - |
| `IF-01` | Dependências: HW-01, IF-01, DAT-01, RF-01.1 e RF-01.2. | sem prova | - |
| `IF-02` | Verificação: fixture de eventos fora de ordem. Dependências: DAT-03, IF-02. | sem prova | - |
| `IF-03` | Verificação: JSON Schema, fixtures e replay. Dependências: IF-03/04. | sem prova | - |
| `IF-04` | Verificação: banco temporário e consulta de leitura. Dependências: DAT-01/02, IF-04. | sem prova | - |
| `IF-05` | IF-05: SQLite para dashboard | sem prova | - |
| `IF-06` | Verificação: captura do dashboard e payload da notificação. Dependências: IF-06, OPS-03. | sem prova | - |
| `IF-07` | IF-07: Atuador para confirmação | sem prova | - |
| `ML-01` | Verificação: matriz de confusão e manifest de teste. Dependências: ML-01, ML-02, DAT-02. | sem prova | - |
| `ML-02` | Verificação: matriz de confusão e manifest de teste. Dependências: ML-01, ML-02, DAT-02. | sem prova | - |
| `ML-03` | Verificação: manifest, pesos e amostras. Dependências: ML-03/05. | sem prova | - |
| `ML-04` | Dependências: ML-04 e PERF-01. | sem prova | - |
| `ML-05` | Verificação: relatório de PoC. Dependências: ML-05, PERF-01. | sem prova | - |
| `ML-06` | Verificação: logs de treino e benchmark no Pi. Dependências: ML-06. | sem prova | - |
| `OPS-01` | OPS-01: Runbook de bancada | sem prova | - |
| `OPS-02` | OPS-02: Logs por fronteira | sem prova | - |
| `OPS-03` | Verificação: captura do dashboard e payload da notificação. Dependências: IF-06, OPS-03. | sem prova | - |
| `OPS-04` | Dependências: RF-08, RF-24, OPS-04 e REL-02. | sem prova | - |
| `PERF-01` | Verificação: relatório de PoC. Dependências: ML-05, PERF-01. | sem prova | - |
| `PERF-02` | Dependências: IF-02, PERF-02, RF-26, RF-27 e PoC 03. | sem prova | - |
| `QLT-02` | Verificação: matriz e manifest. Dependências: QLT-02, DAT-06. | sem prova | - |
| `REL-01` | Verificação: ficha de PoC e DECISIONS.md. Dependências: REL-01/02, DOC-05. | sem prova | - |
| `REL-02` | Verificação: log e consulta de heartbeat. Dependências: REL-02, IF-04. | sem prova | - |
| `RF-01` | | RF-01 | Capturar mais de uma vista do mesmo item após o evento de presença, com timestamp e identificador de | citado | src-production/captura.py, src-production/conformidade.py, code-workspace/src/pocs/poc01_trigger/README.md |
| `RF-01.1` | | RF-01.1 | Verificar confiabilidade do trigger de captura por sensor de presença, com timing determinístico d | coberto | src-production/tests/test_fonte_de_gatilho.py, src-production/tests/test_painel.py, src-production/tests/test_registro.py |
| `RF-01.2` | Dependências: HW-01, IF-01, DAT-01, RF-01.1 e RF-01.2. | coberto | src-production/tests/test_captura.py, src-production/tests/test_identidade.py |
| `RF-02` | | RF-02 | Classificar tampa ausente nas vistas disponíveis. | Núcleo | | citado | code-workspace/src/pocs/poc02_classificacao/README.md |
| `RF-03` | | RF-03 | Classificar tampa mal rosqueada usando a composição multi-view. | Núcleo | | citado | code-workspace/src/pocs/poc02_classificacao/README.md |
| `RF-04` | | RF-04 | Classificar deformidade do corpo nas vistas laterais e preservar a medida de referência. | Núcleo | | citado | code-workspace/src/pocs/poc03_deformidade/README.md |
| `RF-04.1` | RF-04.1: Realizar medição dimensional de apoio à classificação | sem prova | - |
| `RF-05` | | RF-05 | Combinar resultados das vistas e produzir classe, confiança e resultado do item. | Núcleo | | citado | code-workspace/src/pocs/poc04_fusao/README.md |
| `RF-05.1` | RF-05.1: Tratar evidência insuficiente sem aprovação silenciosa | sem prova | - |
| `RF-06` | | RF-06 | Registrar evento com identificador, timestamp, localização, defeito, evidência, confiança, vista e q | citado | src-production/identidade.py, code-workspace/src/pocs/poc05_registro/README.md |
| `RF-07` | | RF-07 | Correlacionar eventos de uma futura expansão multi-nó por identificador e origem. | Expansão | | sem prova | - |
| `RF-08` | | RF-08 | Emitir telemetria de saúde do nó: heartbeat, fila, latência e falha. | Núcleo | | citado | code-workspace/src/pocs/poc06_resiliencia/README.md |
| `RF-09` | | RF-09 | Apresentar dashboard com itens, defeitos, localização, recorrência e saúde do nó. | Núcleo | | citado | code-workspace/src/pocs/poc07_dashboard/README.md |
| `RF-10` | | RF-10 | Medir taxa de eventos da bancada sem controlar a velocidade da esteira. | Expansão | | sem prova | - |
| `RF-11` | | RF-11 | Identificar intervalos sem evento acima do limite definido e registrá-los para análise. | Expansão | | sem prova | - |
| `RF-12` | | RF-12 | Registrar correção do operador preservando decisão original, correção, responsável e horário. | Expa | sem prova | - |
| `RF-13` | | RF-13 | Avaliar detector opcional de anomalia desconhecida como camada adicional. | Expansão | | sem prova | - |
| `RF-14` | | RF-14 | Registrar encaminhamento de item para análise humana, sem comandar atuação física. | Expansão | | sem prova | - |
| `RF-15` | | RF-15 | Medir altura da tampa em milímetros quando a calibração estiver disponível. | Expansão | | sem prova | - |
| `RF-16` | | RF-16 | Manter golden samples com defeito conhecido, isolados das estatísticas operacionais. | Expansão | | sem prova | - |
| `RF-17` | | RF-17 | Gerar relatório de lote com indicadores, severidade, evidências e tendência. | Expansão | | sem prova | - |
| `RF-18` | | RF-18 | Calcular descritores geométricos por vista e score de anomalia sobre conjunto normal. | Expansão | | sem prova | - |
| `RF-19` | | RF-19 | Avaliar detecção autossupervisionada com imagens de itens normais e anomalias sintéticas. | Expansão | sem prova | - |
| `RF-20` | | RF-20 | Avaliar consistência entre vistas pelo score conjunto dos classificadores. | Expansão | | sem prova | - |
| `RF-21` | | RF-21 | Avaliar destilação de modelo para execução no hardware alvo. | Expansão | | sem prova | - |
| `RF-22` | | RF-22 | Comparar timestamp previsto e observado quando houver referência de deslocamento disponível. | Expan | sem prova | - |
| `RF-23` | | RF-23 | Avaliar expansão do dataset por supervisão fraca, documentando incerteza. | Expansão | | sem prova | - |
| `RF-24` | | RF-24 | Conduzir testes de resiliência com hipótese, métrica e impacto definidos antes do ensaio. | Núcleo | | citado | code-workspace/src/pocs/poc06_resiliencia/README.md |
| `RF-25` | | RF-25 | Manter histórico de decisões e mudanças do projeto. | Núcleo | | sem prova | - |
| `RF-26` | | RF-26 | Verificar continuidade de conexões críticas do rig. | Expansão | | sem prova | - |
| `RF-27` | | RF-27 | Planejar base rígida e pontos de fixação para captura. | Expansão | | sem prova | - |
| `RF-28` | | RF-28 | Planejar suportes e gabaritos para posicionamento e deformidades controladas. | Expansão | | sem prova | - |
| `RF-29` | | RF-29 | Aplicar design for testability: entradas controláveis e saídas observáveis. | Núcleo | | sem prova | - |
| `RF-30` | | RF-30 | Avaliar iluminação pulsada e difusa para reduzir saturação nas imagens. | Expansão | | sem prova | - |
| `RNF-01` | | RNF-01 | Latência de registro por item menor que 500 ms, sob condição declarada. | Núcleo | | sem prova | - |
| `RNF-02` | | RNF-02 | Acurácia com intervalo de confiança: tampa ausente 95% ou mais, tampa mal rosqueada 90% ou mais e d | citado | code-workspace/src/pocs/poc02_classificacao/README.md, code-workspace/src/pocs/poc02_classificacao/classificacao.py, code-workspace/src/pocs/poc03_deformidade/README.md |
| `RNF-03` | | RNF-03 | Falsos positivos até 2% para tampa ausente e 5% para as demais classes. | Núcleo | | citado | code-workspace/src/pocs/poc02_classificacao/README.md |
| `RNF-04` | | RNF-04 | Correlação multi-nó de 98% ou mais em ensaio de 50 itens. | Expansão | | sem prova | - |
| `RNF-04.1` | RNF-04.1: Limitar o erro da medição dimensional do corpo | sem prova | - |
| `RNF-05` | | RNF-05 | Integridade do registro de 99% ou mais em 30 minutos de estresse. | Núcleo | | citado | code-workspace/src/pocs/poc05_registro/README.md |
| `RNF-06` | | RNF-06 | Retransmissão de 100% dos eventos bufferizados após reconexão, sem duplicação. | Núcleo | | citado | code-workspace/src/pocs/poc05_registro/README.md |
| `RNF-07` | | RNF-07 | Detecção de nó indisponível abaixo de 10 segundos. | Núcleo | | citado | code-workspace/src/pocs/poc06_resiliencia/README.md |
| `RNF-08` | | RNF-08 | Resiliência a reconexão, debounce, sensor nulo e watchdog sem interrupção silenciosa. | Núcleo | | citado | code-workspace/src/pocs/poc01_trigger/README.md, code-workspace/src/pocs/poc06_resiliencia/README.md |
| `RNF-09` | | RNF-09 | Taxa de eventos da bancada registrada junto da qualidade da captura. | Expansão | | sem prova | - |
| `RNF-10` | | RNF-10 | Documentação reproduzível com README, decisões e proveniência de dataset. | Núcleo | | sem prova | - |
| `RNF-11` | | RNF-11 | Calibração pixel--milímetro documentada por posição fixa. | Expansão | | citado | code-workspace/src/pocs/poc03_deformidade/README.md |
| `RNF-12` | | RNF-12 | Qualidade do registro propagada aos consumidores do dashboard. | Núcleo | | citado | code-workspace/src/pocs/poc04_fusao/README.md, code-workspace/src/pocs/poc05_registro/README.md, code-workspace/src/pocs/poc07_dashboard/README.md |
| `RNF-13` | | RNF-13 | Caso exista encaminhamento físico futuro, confirmação correta de 99% e nenhum item normal encaminha | sem prova | - |
| `RNF-14` | | RNF-14 | Precisão dimensional da tampa dentro de 0,5 mm e nenhuma rejeição de golden sample normal. | Expans | citado | code-workspace/src/pocs/poc03_deformidade/README.md |
| `RNF-15` | | RNF-15 | Custo da camada de descritores abaixo de 10 ms por vista. | Expansão | | sem prova | - |
| `RNF-16` | | RNF-16 | Detector de anomalia treinado apenas com itens normais, com validação e latência compatíveis. | Exp | sem prova | - |
| `RNF-17` | | RNF-17 | Modelo aluno validado no hardware alvo com fallback documentado. | Expansão | | sem prova | - |
| `RNF-18` | | RNF-18 | Validação de timestamp com tolerância configurável, quando a referência estiver disponível. | Expan | sem prova | - |
| `RNF-19` | | RNF-19 | Cada teste de resiliência possui hipótese e métrica antes do experimento. | Núcleo | | citado | code-workspace/src/pocs/poc06_resiliencia/README.md |
| `RNF-20` | | RNF-20 | Estabilidade mecânica sem recalibração indevida após movimentação prevista. | Expansão | | sem prova | - |
| `RNF-21` | | RNF-21 | Iluminação difusa sem saturação que prejudique a extração de contornos. | Expansão | | sem prova | - |
| `SAFE-01` | Dependências ACT-01..10, SAFE-01..03, DAT-06 e PoC 07. | sem prova | - |
| `SAFE-02` | SAFE-02: Falha segura de sensor | sem prova | - |
| `SAFE-03` | Verificação: checklist/fotos/medição. Dependências: HW-02, SAFE-03. | sem prova | - |
| `STK-01` | Verificação: query de auditoria. Dependências: DAT-04, STK-01. | sem prova | - |

Total: 119 requisito(s) -- 20 citado, 3 coberto, 96 sem prova.

