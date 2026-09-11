# PoC-06: Resiliencia observavel

| | |
|---|---|
| **Ideia isolada** | falha silenciosa de sensor, camera ou armazenamento invalida o ensaio sem que ninguem perceba |
| **Pergunta** | o no mantem estado explicito apos falha de comunicacao local ou de captura? |
| **Hipotese** | watchdog, estado explicito de qualidade e reenvio idempotente tornam a falha observavel e recuperavel |
| **Metodo** | injetar uma falha por vez, com hipotese e metrica definidas antes do teste; medir deteccao, recuperacao, perda e duplicacao |
| **Criterio de passagem** | cada hipotese de falha tem resultado medido (detectado, recuperado, sem perda e sem duplicacao) e estado final registrado |
| **Evidencia** | protocolo da falha + log do ensaio + estado final |
| **Limite atual** | o codigo atual cobre apenas reenvio de persistencia; nao ha watchdog nem deteccao de no indisponivel |
| **Dependencias** | RF-08, RF-24, RNF-07, RNF-08, RNF-19 |
| **Codigo** | `resilience.py` |
