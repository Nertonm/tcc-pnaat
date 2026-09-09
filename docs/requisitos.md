# Requisitos e artefatos

Especificação de requisitos do projeto de inspeção multi-view e rastreabilidade. Os itens aqui descritos são metas de engenharia; nenhum deles representa resultado medido até ser verificado no setup declarado.

## 1. Requisitos funcionais

- RF-01: capturar uma imagem da vista superior e duas imagens das vistas laterais para cada item detectado.
- RF-01.1: detectar a passagem do item e gerar o trigger físico de captura por meio do sensor fotoelétrico E18-D80NK, operando por reflexão difusa e com debounce executado pelo ESP32. A confiabilidade da detecção nas condições ópticas da bancada deve ser verificada na PoC 03; caso o componente não atenda ao critério definido, deverá ser substituído por uma alternativa compatível.
- RF-01.2: associar as três imagens ao mesmo identificador de item dentro da janela temporal definida e validada na PoC 03.
- RF-02: classificar tampa ausente na vista de topo.
- RF-03: classificar tampa mal rosqueada na vista de topo.
- RF-04: classificar deformidades do corpo com base nas evidências obtidas pelas duas vistas laterais.
- RF-04.1: quando a medição dimensional for utilizada para apoiar a classificação, estimar a dimensão de referência nas condições de calibração definidas na PoC 02. a medição dimensional utilizada para avaliar deformidades do corpo deve apresentar erro relativo inferior a 5% da referência no setup calibrado da PoC 02.
- RF-05: combinar as decisões dos classificadores por domínio, considerando a vista superior para o domínio da tampa e as duas vistas laterais para o domínio do corpo. O sistema deve reprovar o item quando qualquer domínio detectar defeito e deve preservar no resultado a confiança, a disponibilidade das vistas e eventual discordância entre as vistas laterais.
- RF-05.1: quando pelo menos um domínio detectar defeito, o sistema deve reprovar o item independentemente do resultado do outro domínio. Quando nenhum defeito for detectado, mas a evidência necessária estiver ausente ou abaixo do critério mínimo de qualidade, o sistema deve produzir o estado inconclusivo e registrar a causa, sem aprovar silenciosamente o item.
- RF-06: registrar cada item no hub com identificador, timestamp, ponto, defeito, evidência, confiança, vista de origem e qualidade do registro.
- RF-07: correlacionar eventos multi-nó do mesmo item por identificador sequencial e relógio externo.
- RF-08: emitir telemetria de saúde dos nós, incluindo heartbeat, fila, latência e watchdog.
- RF-09: apresentar dashboard com itens, defeitos e status dos nós, com notificação de defeito crítico.
- RF-10: medir o deslocamento e estimar a velocidade e o throughput do rig por meio de um encoder incremental mecanicamente acoplado ao elemento móvel. O KY-040 será utilizado inicialmente como componente candidato, condicionado à validação de resolução, estabilidade da montagem, perda de pulsos e repetibilidade na PoC 03.
- RF-11: detectar micro-paradas acima do limite definido sem falso positivo.
- RF-12: registrar correção do operador preservando a decisão original e a corrigida, com responsável e horário.
- RF-13: detector opcional de anomalia desconhecida como camada adicional à votação.
- RF-14: separar o item defeituoso no fim do trilho para análise manual, com confirmação por sensor e evento de qualidade quando a confirmação falhar.
- RF-15: medir a altura da tampa em milímetros com backlight e decidir por limite dimensional, usando o classificador como segunda camada.
- RF-16: manter kit de golden samples com defeito conhecido para injeção sob demanda, isolado das estatísticas de produção.
- RF-17: gerar relatório de lote em PDF com indicadores, severidade, evidências e tendência, com envio por notificação.
- RF-18: calcular descritores geométricos por vista e score de anomalia calibrado sobre o conjunto normal.
- RF-19: treinar detector de anomalia autossupervisionado somente com imagens de itens normais, com anomalias sintéticas por recorte e colagem de patch, no formato original, sem autoencoder puro.
- RF-20: avaliar a consistência das evidências dentro de cada domínio, comparando as duas vistas laterais no domínio do corpo e verificando a disponibilidade e a confiança da vista superior no domínio da tampa, sem utilizar a consistência entre domínios para cancelar um defeito detectado.
- RF-21: destilar professor para aluno leve quantizado, treinando o professor apenas em GPU disponível e rodando o aluno no hardware alvo.
- RF-22: calcular o instante esperado de passagem do item com base na distância calibrada e na velocidade estimada pelo encoder, compará-lo ao timestamp observado e registrar alerta quando a divergência ultrapassar a tolerância configurada. A aplicação desse requisito dependerá da aprovação do mecanismo de medição na PoC 03.
- RF-23: expandir o dataset por supervisão fraca combinando regras de medição, descritores e score de anomalia, documentando a incerteza.
- RF-24: conduzir testes de resiliência como experimentos com hipótese falsável, métrica prévia e blast radius mínimo.
- RF-25: manter commits estruturados para histórico e linha do tempo de decisões.
- RF-26: fixar conexões críticas do rig em headers com teste de continuidade.
- RF-27: construir painel de base rígido com furos fixos para câmeras, trigger e encoder.
- RF-28: montar suportes parafusados, jig de posicionamento e réplicas parametrizadas de deformidade.
- RF-29: aplicar design for testability como princípio orientador da arquitetura.
- RF-30: acionar pulso estroboscópico de LEDs RGB sincronizado ao trigger, desligando logo após a janela de captura.

#

## 1.1 Requisitos condicionais e evolutivos

Os requisitos RF-13, RF-17, RF-18, RF-19, RF-21, RF-23 e RF-30 não integram o núcleo mínimo da demonstração. Sua implementação depende da aprovação das PoCs essenciais, da disponibilidade de tempo e de decisão registrada em `docs/DECISIONS.md`. A permanência dos IDs nesta seção preserva a rastreabilidade histórica e não representa compromisso de implementação na entrega atual.

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
- RNF-09: o mecanismo de medição de movimento deve apresentar resolução e repetibilidade suficientes para estimar a velocidade e o throughput do rig sem perda de pulsos que comprometa a correlação das três vistas. Os limiares quantitativos devem ser definidos antes da execução e registrados na PoC 03.
- RNF-10: documentação reproduzível, com README, esquemático, decisões e proveniência de dataset.
- RF-11: detectar uma microparada quando a ausência de deslocamento indicada pelo mecanismo de medição ultrapassar o limiar temporal configurado, registrando o início, a duração e o término do evento. O limiar e a taxa aceitável de falsos positivos devem ser definidos antes do ensaio no rig.
- RNF-12: qualidade do registro propagada aos consumidores.
- RNF-13: confirmação correta de pelo menos 99% das separações comandadas e nenhum item normal direcionado ao caminho de análise manual durante o ensaio da PoC 07.
- RNF-14: precisão dimensional da tampa dentro de 0,5 mm e nenhuma rejeição de golden sample normal.
- RNF-15: custo da camada de descritores abaixo de 10 ms por vista, com threshold calibrado e falha natural independente.
- RNF-16: detector de anomalia treinado apenas com itens normais, com alvo de área sob a curva na validação e latência compatível.
- RNF-17: aluno destilado validado no hardware alvo, com fallback documentado caso a latência estoure.
- RNF-18: validação física de timestamp com tolerância configurável.
- RNF-19: cada teste de resiliência com hipótese e métrica definidas antes do experimento.
- RNF-20: estabilidade mecânica sem recalibração após movimentação dentro do uso previsto.
- RNF-21: eliminar hotspots de saturação luminosa nas imagens capturadas, usando lente difusora acoplada aos LEDs, sem regiões estouradas que prejudiquem a extração de bordas e contornos.

As fichas detalhadas estão em `docs/requisitos/02-nao-funcionais.md`.

## 3. Arquitetura

O diagrama e a revisão dos componentes estão em `docs/arquitetura.md`. O desenho separa o caminho de inspeção, a telemetria paralela, a atuação com confirmação e os consumidores do hub. Ele representa o plano; captura simultânea, latência, correlação, atuação e fallback dependem de verificação no hardware.

## 4. Mapa de valor

| Funcionalidade | Dor que alivia | Benefício esperado |
|---|---|---|
| Inspeção multi-view | Garrafas defeituosas podem chegar ao fim do processo | Pode reduzir a passagem de itens defeituosos no cenário representado pela bancada |
| Rastreabilidade por item | Ausência de evidência individualizada sobre os itens | Fornece evidência por item que poderá apoiar investigações mais específicas |
| Telemetria e microparadas | Paradas podem não ser registradas de maneira estruturada | Permite estimar disponibilidade e desempenho no rig |
| Detecção de anomalia | Defeitos não previstos pelas classes podem passar despercebidos | Pode atuar como camada evolutiva de apoio, condicionada à validação |
| Separação com análise humana | Itens reprovados podem permanecer misturados aos aprovados | Mantém o item reprovado disponível para análise manual |

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
| S7 | PoC 5: integração, PoC 6: resiliência, PoC 7: separação confirmada, dashboard |
| S8 | Testes de estresse, ensaio da demonstração, README e pitch |

O calendário operacional define os marcos da apresentação: requisitos, apresentação da PoC, esboço de vídeo e documentação, e vídeo final com documentação.

## 7. Critérios de aceite da demonstração

- [ ] Dataset com proveniência documentada.
- [ ] PoC 1 e 2 com acurácia e intervalo de confiança reportados.
- [ ] PoC 3 com throughput real medido pelo encoder.
- [ ] PoC 4 com correlação no limite definido.
- [ ] PoC 5 sem perda de eventos sob carga.
- [ ] PoC 6 com cenários de falha recuperando sem interrupção.
- [ ] PoC 7 com separação confirmada e nenhum item normal direcionado ao caminho de análise manual.
- [ ] Golden samples rotulados e prontos para injeção sob demanda.
- [ ] Medida dimensional da tampa demonstrada, caso sua inclusão no núcleo seja aprovada por PoC e decisão registrada.
- [ ] Relatório de lote gerado e enviado, caso o requisito evolutivo correspondente seja aprovado para implementação.
- [ ] Camadas condicionais apenas se a PoC correspondente for aprovada.
- [ ] Schema populado com consultas analíticas demonstráveis.
- [ ] Dashboard e notificação funcionando com o mesmo identificador de item.
- [ ] Decisões datadas com justificativa.
- [ ] README reproduzível em ambiente limpo, com esquemático do rig.
- [ ] Pitch ensaiado com as quatro partes e números de evidência.

## 8. Registro de prova de conceito

O protocolo e o modelo de registro estão em `docs/pocs/README.md`. Cada PoC registra pergunta binária, hipótese, setup, métrica, go/no-go, evidência e decisão seguinte.
