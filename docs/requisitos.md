# Requisitos e artefatos

Especificação de requisitos do projeto de inspeção multi-view e rastreabilidade. Os itens aqui descritos são metas de engenharia; nenhum deles representa resultado medido até ser verificado no setup declarado.

## 1. Requisitos funcionais

- RF-01: capturar as três vistas (topo e duas laterais) do mesmo item, sincronizadas por trigger físico.
- RF-01.1: garantir a confiabilidade do gatilho de captura via barreira por oclusão retrorrefletiva no E18-D80NK, com timing determinístico calculado pelo ESP32.
- RF-02: classificar tampa ausente na vista de topo.
- RF-03: classificar tampa mal rosqueada na vista de topo.
- RF-04: classificar deformidade de corpo nas vistas laterais, com erro dimensional abaixo de 5% da referência.
- RF-05: combinar os classificadores por votação e produzir o status final do item com código de severidade.
- RF-06: registrar cada item no hub com identificador, timestamp, ponto, defeito, evidência, confiança, vista de origem e qualidade do registro.
- RF-07: correlacionar eventos multi-nó do mesmo item por identificador sequencial e relógio externo.
- RF-08: emitir telemetria de saúde dos nós, incluindo heartbeat, fila, latência e watchdog.
- RF-09: apresentar dashboard com itens, defeitos e status dos nós, com notificação de defeito crítico.
- RF-10: medir throughput real do rig pelo encoder.
- RF-11: detectar micro-paradas acima do limite definido sem falso positivo.
- RF-12: registrar correção do operador preservando a decisão original e a corrigida, com responsável e horário.
- RF-13: detector opcional de anomalia desconhecida como camada adicional à votação.
- RF-14: separar o item defeituoso no fim do trilho para análise manual, com confirmação por sensor e evento de qualidade quando a confirmação falhar.
- RF-15: medir a altura da tampa em milímetros com backlight e decidir por limite dimensional, usando o classificador como segunda camada.
- RF-16: manter kit de golden samples com defeito conhecido para injeção sob demanda, isolado das estatísticas de produção.
- RF-17: gerar relatório de lote em PDF com indicadores, severidade, evidências e tendência, com envio por notificação.
- RF-18: calcular descritores geométricos por vista e score de anomalia calibrado sobre o conjunto normal.
- RF-19: treinar detector de anomalia autossupervisionado somente com imagens de itens normais, com anomalias sintéticas por recorte e colagem de patch, no formato original, sem autoencoder puro.
- RF-20: avaliar consistência entre vistas pelo score conjunto dos três classificadores.
- RF-21: destilar professor para aluno leve quantizado, treinando o professor apenas em GPU disponível e rodando o aluno no hardware alvo.
- RF-22: validar o timestamp esperado pela distância e velocidade do encoder e alertar quando o observado divergir.
- RF-23: expandir o dataset por supervisão fraca combinando regras de medição, descritores e score de anomalia, documentando a incerteza.
- RF-24: conduzir testes de resiliência como experimentos com hipótese falsável, métrica prévia e blast radius mínimo.
- RF-25: manter commits estruturados para histórico e linha do tempo de decisões.
- RF-26: fixar conexões críticas do rig em headers com teste de continuidade.
- RF-27: construir painel de base rígido com furos fixos para câmeras, trigger e encoder.
- RF-28: montar suportes parafusados, jig de posicionamento e réplicas parametrizadas de deformidade.
- RF-29: aplicar design for testability como princípio orientador da arquitetura.
- RF-30: acionar pulso estroboscópico de LEDs RGB sincronizado ao trigger, desligando logo após a janela de captura.

As fichas detalhadas de cada requisito estão em `docs/requisitos/01-funcionais.md`.

## 2. Requisitos não funcionais

- RNF-01: latência de decisão por item abaixo de 500 ms.
- RNF-02: acurácia com intervalo de confiança: tampa ausente 95% ou mais, mal rosqueada 90% ou mais, deformidade 90% ou mais.
- RNF-03: falsos positivos até 2% para tampa ausente e até 5% para as demais classes.
- RNF-04: correlação multi-nó de 98% ou mais em ensaio de 50 itens.
- RNF-05: integridade do registro de 99% ou mais em 30 minutos de estresse.
- RNF-06: retransmissão de 100% dos eventos bufferizados após reconexão, sem duplicação.
- RNF-07: detecção de nó offline abaixo de 10 segundos.
- RNF-08: resiliência a reconexão, debounce, sensor nulo e watchdog, sem interrupção silenciosa.
- RNF-09: throughput real medido no rig, mantendo a acurácia.
- RNF-10: documentação reproduzível, com README, esquemático, decisões e proveniência de dataset.
- RNF-11: calibração pixel em milímetro documentada por posição fixa.
- RNF-12: qualidade do registro propagada aos consumidores.
- RNF-13: confirmação de ejeção de 99% ou mais e nenhum item normal ejetado.
- RNF-14: precisão dimensional da tampa dentro de 0,5 mm e nenhuma rejeição de golden sample normal.
- RNF-15: custo da camada de descritores abaixo de 10 ms por vista, com threshold calibrado e falha natural independente.
- RNF-16: detector de anomalia treinado apenas com itens normais, com alvo de área sob a curva na validação e latência compatível.
- RNF-17: aluno destilado validado no hardware alvo, com fallback documentado caso a latência estoure.
- RNF-18: validação física de timestamp com tolerância configurável.
- RNF-19: cada teste de resiliência com hipótese e métrica definidas antes do experimento.
- RNF-20: estabilidade mecânica sem recalibração após movimentação dentro do uso previsto.

As fichas detalhadas estão em `docs/requisitos/02-nao-funcionais.md`.

## 3. Arquitetura

O diagrama e a revisão dos componentes estão em `docs/arquitetura.md`. O desenho separa o caminho de inspeção, a telemetria paralela, a atuação com confirmação e os consumidores do hub. Ele representa o plano; captura simultânea, latência, correlação, atuação e fallback dependem de verificação no hardware.

## 4. Mapa de valor

| Funcionalidade | Dor que alivia | Benefício |
|---|---|---|
| Inspeção multi-view | Garrafas defeituosas chegam ao fim do processo | Reduz envio de itens defeituosos e devolução de lote |
| Rastreabilidade por item | Causa raiz desconhecida e recall de lote inteiro | Recall cirúrgico com evidência fotográfica |
| Telemetria e micro-paradas | Paradas invisíveis mascaram a eficiência | Dado real de disponibilidade e desempenho |
| Detecção de anomalia | Defeitos novos passam despercebidos | Camada extra de segurança |
| Separação com análise humana | Defeituosos misturados ao lote bom | Loop de qualidade fechado |

## 5. Esqueleto do pitch

1. Dor: garrafas com tampa ausente ou corpo deformado chegam ao fim do processo; cada parada custa eficiência e cada lote rejeitado custa retrabalho.
2. Solução: inspeção multi-view com um classificador por vista e rastreabilidade por item em topologia estrela.
3. Evidências: acurácia por classe com intervalo de confiança, latência por item, correlação multi-nó e throughput medido na bancada reduzida.
4. Continuidade: escalonamento para o throughput da linha, atuação com análise humana e evolução para indicadores de fábrica.

Toda alegação numérica vem de medição no rig ou é identificada como meta.

## 6. Cronograma

O plano lógico de desenvolvimento em semanas:

| Semana | Entrega |
|---|---|
| S1 | Requisitos, indicadores, diagrama e início do rig |
| S2 | Rig completo e captura do dataset de topo |
| S3 | PoC 1: classificador de topo |
| S4 | Câmeras laterais e PoC 2: deformidade multi-view |
| S5 | PoC 3: sincronização no trilho; revisão do escopo |
| S6 | PoC 4: correlação multi-nó e hub SQLite |
| S7 | PoC 5: integração, PoC 6: resiliência, PoC 7: ejeção, dashboard |
| S8 | Testes de estresse, ensaio da demonstração, README e pitch |

O calendário operacional define os marcos da apresentação: requisitos, apresentação da PoC, esboço de vídeo e documentação, e vídeo final com documentação.

## 7. Critérios de aceite da demonstração

- [ ] Dataset com proveniência documentada.
- [ ] PoC 1 e 2 com acurácia e intervalo de confiança reportados.
- [ ] PoC 3 com throughput real medido pelo encoder.
- [ ] PoC 4 com correlação no limite definido.
- [ ] PoC 5 sem perda de eventos sob carga.
- [ ] PoC 6 com cenários de falha recuperando sem interrupção.
- [ ] PoC 7 com ejeção confirmada e nenhum item normal ejetado.
- [ ] Golden samples rotulados e prontos para injeção sob demanda.
- [ ] Medida dimensional da tampa demonstrada.
- [ ] Relatório de lote gerado e enviado.
- [ ] Camadas condicionais apenas se a PoC correspondente for aprovada.
- [ ] Schema populado com consultas analíticas demonstráveis.
- [ ] Dashboard e notificação funcionando com o mesmo identificador de item.
- [ ] Decisões datadas com justificativa.
- [ ] README reproduzível em ambiente limpo, com esquemático do rig.
- [ ] Pitch ensaiado com as quatro partes e números de evidência.

## 8. Registro de prova de conceito

O protocolo e o modelo de registro estão em `docs/pocs/README.md`. Cada PoC registra pergunta binária, hipótese, setup, métrica, go/no-go, evidência e decisão seguinte.
