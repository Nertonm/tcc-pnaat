# PoCs da Entrega 1

Cada PoC é uma proposta de validação. Ela deve produzir métrica, evidência, decisão e impacto de escopo antes que a capacidade seja tratada como validada.

| PoC | Ideia | Critério de passagem | Evidência esperada |
|---|---|---|---|
| PoC-01 | Captura multi-view | Mais de uma vista associada ao mesmo evento, sem duplicidade. | Imagens, timestamps e log. |
| PoC-02 | Classificação de tampa | Metas do RNF-02 para tampa ausente e mal rosqueada. | Matriz de confusão. |
| PoC-03 | Deformidade lateral | Meta de classificação e erro dimensional declarado. | Calibração e matriz. |
| PoC-04 | Fusão e identidade | Regra determinística preserva discordâncias e origem. | Fixture e log. |
| PoC-05 | Registro local | Evento contém origem, localização, classe, qualidade e evidência. | Consulta e reconciliação. |
| PoC-06 | Resiliência | Falha gera estado explícito e replay sem duplicação. | Falha injetada e log. |
| PoC-07 | Dashboard | Evento consultável por defeito, momento, esteira, nó e evidência. | Dashboard e notificação. |
| PoC-Final | Conjectura integrada | Captura, classificação, registro e visibilidade avaliados no mesmo ensaio. | Pacote de ensaio. |

Atuação física, ejeção, controle da esteira e MQTT/multi-nó não são critérios do núcleo da Entrega 1. Podem ser tratados como expansão após as PoCs de observação, identidade e registro.
