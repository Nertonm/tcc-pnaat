# Escopo da Entrega 1

## Cenário e problema

Tema selecionado: Cenário 1, Inspeção de envase.

O Cenário 1 descreve gargalos na esteira principal quando recipientes com tampa ausente, tampa mal rosqueada ou deformidade no corpo chegam à etapa final da linha. Esta entrega trata a falta de visibilidade organizada sobre essas ocorrências: qual defeito ocorreu, quando, em qual esteira, em qual localização, com qual evidência e com que recorrência.

## Núcleo da proposta

- Captura multi-view de mais de uma vista por evento de presença.
- Classificação de tampa ausente, tampa mal rosqueada e deformidade do corpo.
- Fusão dos resultados das vistas, preservando discordâncias.
- Registro do evento com identificador, timestamp, localização, esteira, nó, confiança, qualidade e evidência.
- Dashboard e alertas para operação, manutenção e qualidade.
- Um nó de observação e registro local como configuração inicial.

## Fora do escopo desta entrega

- Controle da velocidade ou da lógica da esteira industrial.
- Ejeção, atuador, confirmação mecânica ou descarte automático.
- MQTT, hub central e múltiplos nós como exigência do núcleo.
- Detecção de anomalia desconhecida, descritores geométricos, destilação e supervisão fraca como capacidade inicial.
- Alegações de frequência real, impacto financeiro ou desempenho industrial sem coleta própria.

## Restrições

- A quantidade e a posição das vistas serão decididas nas PoCs de captura e classificação.
- A latência deve ser medida no ambiente declarado antes de restringir a composição multi-view.
- A proposta usa dados e imagens com proveniência registrada; não assume dataset industrial já disponível.
- Expansão multi-nó e MQTT dependem de PoCs de identidade, registro e resiliência.

## Critério de coerência

Uma alteração de escopo só entra no núcleo após registrar: necessidade atendida, requisito afetado, PoC, métrica, critério e evidência esperada.
