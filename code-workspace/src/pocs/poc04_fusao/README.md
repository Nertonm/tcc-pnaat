# PoC-04: Fusao e identidade

| | |
|---|---|
| **Ideia isolada** | uma fusao por maioria pode cancelar um defeito detectado em uma vista, apagando o achado mais importante do item |
| **Pergunta** | a fusao preserva o defeito quando as vistas discordam? |
| **Hipotese** | uma regra deterministica POR DOMINIO, que preserva discordancia e origem, mantem o defeito visivel mesmo quando as outras vistas discordam |
| **Metodo** | decidir por dominio (tampa e corpo) com as vistas decisorias; tratar a vista de topo como check dimensional (so veta/escala); exigir evidencia completa para aprovar; registrar origem por vista. Fixtures com vistas discordantes + harness de casos declarados com ground truth |
| **Criterio de passagem** | nenhum caso do harness diverge do esperado: defeito nao e cancelado por discordancia, topo nao aprova, dominio nao medido e evidencia insuficiente nao viram aprovacao, origem e discordancia ficam registradas |
| **Evidencia** | `scripts/avaliar_poc04.py` (tabela + `resultados_poc04/fusao.json`) + `tests/test_fusion.py` (protocolo em 20 testes) + teste de mutacao do harness |
| **Limite atual** | a demonstracao roda com a configuracao DECLARADA do rig v0 (1 vista de corpo, sem check dimensional); com ela, item normal fica `inconclusivo` porque o dominio da tampa nao e medido. A fusao com o rig completo (2 laterais + topo) e coberta pelo harness, nao pela bancada |
| **Dependencias** | RF-05, RNF-12; D-04 (decisao por dominio), emenda D-23 (topo nao decide tampa), D-11 (camada secundaria nao cancela reprovacao), D-28 (vocabulario) |
| **Codigo** | `fusion.py`, `scripts/avaliar_poc04.py`, `tests/test_fusion.py` |
