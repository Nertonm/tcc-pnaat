# PoC-Final: Conjectura integrada

| | |
|---|---|
| **Ideia isolada** | cada camada pode funcionar isolada e a cadeia inteira falhar quando roda junto |
| **Pergunta** | o conjunto observa, classifica, registra e apresenta o evento de forma rastreavel? |
| **Hipotese** | as camadas acopladas (captura, pre-processamento, decisao, fusao, registro e dashboard) sustentam um ensaio completo |
| **Metodo** | ensaiar a cadeia numa execucao unica, com o criterio de passagem definido por camada, e declarar o que nao entrou |
| **Criterio de passagem** | cada camada avaliada no mesmo ensaio, com o criterio declarado na PoC de origem |
| **Evidencia** | pacote do ensaio: captura, medidas, decisoes, registro, dashboard e log de falhas |
| **Limite atual** | a integracao atual faz upsert e resumo sobre eventos prontos; nao encadeia captura, pre-processamento, decisao nem fusao, e latencia, integridade e retransmissao nao sao medidas |
| **Dependencias** | PoC-01, PoC-04, PoC-05, PoC-07 e PoC-08; PoC-02, PoC-03 e PoC-06 ainda fora do ensaio |
| **Codigo** | `integrada.py`, `scripts/demo_poc.py` |
