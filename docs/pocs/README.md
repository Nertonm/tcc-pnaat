## PoCs

Cada PoC é uma proposta de validação. Ela deve produzir métrica, evidência, decisão e impacto de escopo antes que a capacidade seja tratada como validada.

| PoC | Ideia | Critério de aprovação | Evidência esperada |
|---|---|---|---|
| PoC-01 | Captura multi-view (gatilho de presença) | Mais de uma vista associada ao mesmo evento, com identidade e timestamp, sem duplicidade nem janela espúria. Sensor é componente candidato (D-20). | Log de eventos por item (timestamp), veredito PASS/FAIL e JSON de evidência (`poc01_teste.py`). Captura das três vistas ainda não integrada ao gatilho real. |
| PoC-02 | Classificação de tampa | Metas do RNF-02 para tampa ausente e mal rosqueada. | Matriz de confusão. |
| PoC-03 | Deformidade lateral | Meta de classificação e erro dimensional declarado. | Calibração e matriz. |
| PoC-04 | Fusão e identidade | Regra determinística preserva discordâncias e origem por vista, sem maioria global (D-04). | Registro de eventos. |
| PoC-05 | Registro local | Evento contém origem, localização, classe, qualidade e evidência. | Consulta e reconciliação. |
| PoC-06 | Resiliência | Falha gera estado explícito e replay sem duplicação. | Falha injetada e log. |
| PoC-07 | Painel | Evento consultável por defeito, momento, esteira, nó e evidência. | Painel e notificação. |
| PoC-Final | Conjectura integrada | Captura, classificação, registro e visibilidade avaliados no mesmo ensaio. | Pacote completo do ensaio. |

Atuação física, ejeção, controle da esteira e MQTT/multi-nó não são critérios do núcleo do projeto. Podem ser tratados como expansão após as PoCs de observação, identidade e registro.

- `08-preprocessamento-geometria/`: PoC-08: pre-processamento deterministico (flat-field, alinhamento, ROI, elipse Canny+LS+RANSAC) e metricas de qualidade (CNR/Tenengrad/especular).

## Execucao de referencia: o que o ensaio mostra hoje

O ensaio de referencia precisa mostrar
**entrada**, **funcionamento** e **resultado**, em **sequencia unica e acompanhavel**, com a tecnologia
central **acompanhada de outro elemento** da arquitetura, a **funcao de cada elemento** explicada e a
**proxima etapa / o que ainda nao esta integrado** declarada.

**Estado verificado em 2026-09-11 (registro adversarial, com evidencia em `demo_poc.py`):**
o take atual executa gatilho real (E18-D80NK + ESP32) sem captura de vistas associada, pre-processamento parcial, um modelo one-class sobre o ROI do
**corpo** (que e Expansao, RF-19/RNF-16) e a fusao de **uma unica vista**, mais o registro e o dashboard.
**A classificacao de tampa (PoC-02) nao e executada por nenhum script** e, sem itens defeituosos no
dataset (`defective` = 0), **nao existe matriz de confusao**. Portanto:

| Papel no take | Situacao real |
|---|---|
| PoC-01 (gatilho) | Real: E18-D80NK + ESP32 detectando passagem física, com debounce e log de eventos. E18 permanece candidato (D-20). Captura das três vistas (topo, lateral1, lateral2) ainda não integrada ao gatilho — nenhuma câmera está associada ao evento de trigger no ensaio atual. |
| PoC-08 pre-processamento | parcial: ROI + geometria + metricas; flat-field/alinhamento nao usados |
| **PoC-02 tecnologia central** | **NAO INTEGRADA**: nenhum script executa a politica; sem dado de defeito |
| PoC-03 deformidade | nao integrada (sem vistas laterais, sem calibracao) |
| PoC-04 fusao | parcial e com defeito conhecido: uma vista e maioria global (contradiz D-04) |
| PoC-05 registro | parcial: dict em memoria, sem campo de evidencia |
| PoC-06 resiliencia | nao integrada (so retry de persistencia) |
| PoC-07 dashboard | parcial: le `resultados.json`, nao o registro; sem notificacao |
| PoC-Final | nao executada como ensaio unico |

Enquanto a classificacao de tampa nao estiver integrada e sem dados de defeito, a demonstracao cobre
apenas parte do fluxo. O video deve **dizer isso em voz alta**: declarar o que nao esta integrado e
qual e o proximo passo tecnico.

Cada README de pacote (`code-workspace/src/pocs/pocNN_*/README.md`) declara a ideia isolada,
a hipotese, o metodo, o criterio de passagem, a evidencia e o limite atual daquela camada.
