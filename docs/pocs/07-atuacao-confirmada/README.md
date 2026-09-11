# PoC 07: sinalização de defeito

- Status: Proposto
- Pergunta binária: uma decisão de defeito chega ao dashboard/notificação com o `item_id`, severidade e evidência corretos?
- Hipótese: decisão, persistência e notificação formam estados observáveis por item sem exigir remoção física da garrafa.
- Métrica: notificações entregues, falhas de entrega, retries, timeout e notificações indevidas para golden OK.
- Go: entrega rastreável da notificação e zero alerta de defeito para golden OK no cenário declarado.
- No-go: decisão apresentada como entrega, notificação sem vínculo ao item ou falha de envio mascarada.
- Setup: dashboard/ntfy, golden samples, defeitos conhecidos e logs.
- Evidência: eventos de sinalização, captura do dashboard/notificação, logs e query.
- Dependências: RF-09, RF-14, RNF-13/14, IF-06 e SIG-01..06.
- Resultado esperado: registrar a métrica, a decisão e a evidência desta PoC.
