# R05 v3 — BLOCKED

Revalidação independente pelo MCP FreeCAD, no documento R05Refs. Entrada exclusiva de coluna: `exports/concepts/optical-rig-r05/optical-rig-r05-column-modules-v3.step`, SHA256 `8bbe3efa18f55fad7d70c533b3bbbe8728e58f23018dcea812911642cff35741`. Nenhum resultado geométrico da v1 foi reutilizado.

| Gate | Resultado | Evidência v3 |
|---|---|---|
| Interferência | FAIL | Plinth ↔ corpo módulo 1: 11.592 mm³. Ombro módulo 4 ↔ crossbar: 41.440 mm³. Demais pares sem interseção volumétrica acima de 1e-5 mm³. |
| Garrafa, subgate de interferência | PASS | Coluna integralmente em Y[-240,-160]; interseção zero com cilindro H370/D120, centrado X=Y=0 e base Z0. Distância mínima 100 mm. Corredor Y[-60,60] livre da coluna. |
| Altura | FAIL | Plataforma Z[423,433], topo Z433. Faltam 87–127 mm para Z520–560. Um módulo adicional com passo líquido de 100 mm daria Z533 à plataforma. Offset do ponto óptico da CM3 ainda precisa entrar na montagem final. |
| Encaixe + M4 | FAIL | Corpos Z[-38,62], [62,162], [162,262], [262,362], apenas justapostos. Ombros Z[104,120], [204,220], [304,320], [404,420]: vão axial de 42 mm em relação ao respectivo corpo. Corpo 4 ↔ barra: vão 43 mm; barra ↔ plataforma: 4 mm; ombro 4 ↔ plataforma: 3 mm. |
| Canal FPC | FAIL | Sonda central 20×10 mm em X[-10,10], Y[-205,-195] encontra seção totalmente bloqueada, 200 mm², em Z110/210/310/410 e Z425. Juntas dos corpos em Z62/162/262 estão localmente livres. |
| Grip trocável | FAIL | Interface correspondente de receptor/adaptador não demonstrada. LIGHTCLAMP do R05Refs está em Y[-25,0], distante pelo menos 135 mm em Y do plinth. Base do plinth em Z-5 apresenta seção fechada 120×80 sem abertura passante; cortes superiores Ø7,2 não comprovam intercâmbio do pé. |

Na v3 existem superfícies cilíndricas Ø4,4 nos corpos e ombros: folga nominal radial de 0,2 mm frente a Ø4. São arcos parciais/entalhes abertos; não demonstram um conjunto de fixação M4 montado. A folga macho/fêmea não foi aprovada, pois os ombros estão separados. Não se aplica à v3 a afirmação histórica de ausência de faces cilíndricas nos corpos.

A medição de 42 mm é o vão axial; a menor distância BRep corpo ↔ ombro respectivo é 42,107 mm. Os ombros intermediários ficam dentro da região vazia de outros corpos, sem interseção volumétrica, mas separados de material: ausência de colisão não estabelece encaixe.

A sonda FPC é diagnóstico de passagem central, não especificação aprovada de cabo/conector. Os volumes sobrepostos foram unidos antes de medir a ocupação, evitando contagem dupla em Z410. Nenhuma rota alternativa contínua foi demonstrada.

A correção lateral e o ganho de altura foram reconhecidos. Não foram importados Pi5/CM3 nem refinados backplates, case ou câmeras, conforme condição do gate. FOV, carga e safety não foram avaliados. Sem commit.

Evidências: [JSON completo](../exports/concepts/optical-rig-r05/validation-v3.json), [FreeCAD BLOCKED](../exports/concepts/optical-rig-r05/R05Refs-v3-BLOCKED.FCStd), [vista isométrica](../exports/concepts/optical-rig-r05/v3-gate-isometric.png), [frontal](../exports/concepts/optical-rig-r05/v3-gate-front.png), [superior](../exports/concepts/optical-rig-r05/v3-gate-top.png).

O documento R05Refs recebeu o grupo `V3_GATE_BLOCKED`, com sólidos originais v3, interseções em vermelho, garrafa de referência e planos Z520/Z560. Foi salvo no arquivo BLOCKED acima. Geometria/placement das referências existentes foram preservados; visibilidades temporariamente isoladas para as capturas e restauradas. Leitura MCP confirmou GateStatus e hash no grupo. Os artefatos antigos de v1 foram preservados como histórico.

Reprodução: executar `scripts/freecad_r05_v3_gate.py` via MCP execute_code em R05Refs sem o grupo de auditoria existente; o script impede duplicação. Operações nativas Part/OCCT, sem CadQuery.
