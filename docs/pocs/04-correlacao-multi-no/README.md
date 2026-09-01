# PoC 04: correlação multi-nó

- Status: Pendente
- Pergunta binária: o hub associa corretamente 50 itens aos eventos dos nós?
- Hipótese: ID sequencial e RTC DS3231 mantêm a identidade entre visão e sensores.
- Métrica: percentual de associações corretas e timestamp divergente.
- Go: ≥98% de correlação; no-go: troca ou associação silenciosa.
- Setup: payload versionado, nós e sequência conhecida.
- Evidência: manifest de eventos, query e relatório.
- Dependências: RF-07/08, DAT-01/03/07, IF-03/04.
- Resultado: não executado.
