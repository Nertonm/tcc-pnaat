# PoC-04: Fusao e identidade

| | |
|---|---|
| **Ideia isolada** | uma fusao por maioria pode cancelar um defeito detectado em uma vista, apagando o achado mais importante do item |
| **Pergunta** | a fusao preserva o defeito quando as vistas discordam? |
| **Hipotese** | uma regra deterministica por dominio, que preserva discordancia e origem, mantem o defeito visivel mesmo quando as outras vistas discordam |
| **Metodo** | montar fixtures com vistas discordantes (uma reprova, outra aprova); verificar a decisao do item e o registro de origem e discordancia |
| **Criterio de passagem** | regra deterministica que reprova o item quando qualquer dominio reprova e registra origem por vista, sem maioria global |
| **Evidencia** | fixture de vistas discordantes + log com origem por vista |
| **Limite atual** | a implementacao atual usa maioria global entre vistas, o que contraria essa regra; no ensaio de demonstracao a fusao recebe uma unica vista |
| **Dependencias** | RF-05, RNF-12; D-04 (decisao por dominio), D-11 (camada secundaria nao cancela reprovacao) |
| **Codigo** | `fusion.py` |
