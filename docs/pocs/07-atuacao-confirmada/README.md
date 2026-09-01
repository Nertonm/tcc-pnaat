# PoC 07: atuação confirmada

- Status: Pendente
- Pergunta binária: o defeito é separado e confirmado sem ejetar item OK?
- Hipótese: ordem, atuador e sensor de confirmação formam estados observáveis por item.
- Métrica: confirmações, falhas, retries, timeout e falsas ejeções.
- Go: confirmação ≥99% e zero falsa ejeção de golden OK.
- No-go: ordem apresentada como confirmação ou sensor ausente mascarado.
- Setup: atuador, sensor, golden samples, defeitos e parada manual.
- Evidência: eventos ACT, vídeo/sensor, logs e query.
- Dependências: RF-14, RNF-13/14, ACT-01..10, SAFE-01..03.
- Resultado: não executado.
