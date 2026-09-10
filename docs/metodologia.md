# Metodologia

## Fonte pedagógica

Apostila do Trabalho de Conclusão da Capacitação, PNAAT 2026, FIT. O material estrutura o trabalho em quatro unidades e serve de referência de método, não de conteúdo técnico literal.

## As quatro unidades

### Unidade 1: Engenharia de requisitos e escopo

Parte-se de uma dor industrial real, levantam-se requisitos, delimita-se o escopo e definem-se critérios de sucesso testáveis. No projeto, isso resulta na inspeção de produção, nos requisitos numerados, nos indicadores e nos limites explícitos.

### Unidade 2: Prototipagem rápida e prova de conceito

A prova de conceito isola a variável crítica e permite falhar cedo. A ordem proposta é classificador de topo, deformidade lateral, sincronização física, correlação multi-nó, integração de dados, resiliência e atuação confirmada. Não se começa pela integração completa.

### Unidade 3: Estruturação do repositório e roteirização

README, reprodutibilidade em ambiente limpo, esquemático, documentação visual e pitch são parte do produto. O repositório preserva a evolução; a publicação segue as convenções de `CONTRIBUTING.md`.

### Unidade 4: Integração e defesa

Firmware, hardware e modelos precisam integrar-se com critérios de aceite, testes de resiliência e demonstração operacional. A defesa usa números medidos na bancada reduzida e identifica explicitamente o caminho de escalonamento.

## Cenários de origem

O programa oferece cenários industriais de referência. A direção preferida é o cenário de inspeção de produção, sujeito a confirmação: garrafas com tampa ausente, tampa mal rosqueada ou deformidade no corpo chegam ao fim do processo e causam paradas, retrabalho e perda de rastreabilidade.

## Direção do projeto (a confirmar)

A direção adotada é o cenário de inspeção de produção, sujeita a confirmação nas provas de conceito: garrafas com tampa ausente, tampa mal rosqueada ou deformidade no corpo chegam ao fim do processo e causam paradas, retrabalho e perda de rastreabilidade.

Camadas adicionais de anomalia, como detecção autossupervisionada, descritores geométricos e destilação professor-aluno, são condicionais: só entram no sistema se a prova de conceito atingir a métrica e o custo definidos.

## Critério transversal

Design for testability: testabilidade igual a controlabilidade mais observabilidade. Entradas controláveis (golden samples, trigger) e saídas observáveis (dashboard, heartbeat, timestamps, evidências e métricas) são pré-requisito de qualquer aceite.

## Referências

- Apostila TCC PNAAT 2026, FIT.
- Cenários TCC PNAAT 2026, FIT.
- Documentos de escopo e requisitos deste repositório.
