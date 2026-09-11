# PoC-05: Registro local

| | |
|---|---|
| **Ideia isolada** | evento sem contrato completo e sem idempotencia nao permite reconstruir o que aconteceu, e a rastreabilidade se perde |
| **Pergunta** | o evento chega ao registro com origem, localizacao e qualidade? |
| **Hipotese** | registro local com contrato versionado e gravacao idempotente preserva o evento sem perda nem duplicacao |
| **Metodo** | gerar eventos e reenviar o mesmo identificador; reconciliar gerados, gravados e consultados |
| **Criterio de passagem** | evento completo (identificador, timestamp, local, classe, confianca, vista, qualidade e referencia da evidencia) sem perda nem duplicacao |
| **Evidencia** | consulta ao registro + reconciliacao entre gerados, gravados e consultados |
| **Limite atual** | o registro atual e em memoria, nao persiste entre execucoes e o evento ainda nao carrega referencia de evidencia nem versao de contrato |
| **Dependencias** | RF-06, RNF-05, RNF-12; RNF-06 e expansao (retransmissao) |
| **Codigo** | `registry.py`, `events.py` |
