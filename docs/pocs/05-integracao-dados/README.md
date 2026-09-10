# PoC 05: integração de dados

- Status: Proposto
- Pergunta binária: eventos chegam ao SQLite sem perda ou duplicação sob carga?
- Hipótese: payload com event_id, fila e upsert idempotente preserva os eventos.
- Métrica: gerados, recebidos, persistidos, consultados e duplicados.
- Go: integridade ≥99% no ensaio definido; no-go: perda sem estado explícito.
- Setup: MQTT, hub, SQLite, carga controlada e queda de conexão.
- Evidência: logs estruturados, banco temporário e queries.
- Dependências: DAT-07, IF-04, RNF-05/06.
- Resultado esperado: registrar a métrica, a decisão e a evidência desta PoC.
