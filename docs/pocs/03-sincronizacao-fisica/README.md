# PoC 03: sincronização física

- Status: Proposto
- Pergunta binária: as três imagens pertencem ao mesmo item na janela definida?
- Hipótese: trigger único, encoder e posição fixa evitam troca de item.
- Métrica: correlação por item, janela temporal e perda de vista.
- Go: três vistas associadas sem queda acima do limite definido.
- No-go: troca, vista atrasada ou timestamp sem diagnóstico.
- Setup: trilho, trigger, encoder, três câmeras e dois itens próximos.
- Evidência: eventos, imagens e timestamps.
- Dependências: RF-01, RF-10, RNF-04, HW-01.
- Resultado esperado: registrar a métrica, a decisão e a evidência desta PoC.
