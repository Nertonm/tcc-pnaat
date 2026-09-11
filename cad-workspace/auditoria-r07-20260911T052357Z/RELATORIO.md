# Revisão independente — composição DIN PNAAT

**Resultado: composição R07 REPROVADA; refinamento limitado de topologia PASS. Não fabricar.**

## Autoridade e preservação
<host>, workspace `/home/<usuario>/tcc-pnaat/github/cad-workspace`, repositório pai `github`, HEAD registrado em baseline.json. Escritas apenas neste NOVO diretório; fontes originais e exports R07 copiados em inputs antes da execução. Nenhum commit, index, serviço, GUI ou documento alheio alterado. Scripts locais de transporte em /root não são fontes canônicas.
A solicitação atual autoriza revisão/refinamento estrutural e supera o bloqueio etapa0 do BRIEFING antigo. O documento docs/design/grip-extensivel.md ainda descreve T-slot/USB: conflito documental, não autorização para retornar a esse conceito.

## Arquitetura
O pórtico aprovado continua sendo dois montantes DIN em grips de aperto nas laterais FIXAS da esteira, sem furar, travessa DIN apoiada nos dois montantes, com ajuste de altura e largura e sobras externas. Este conceito é uma arquitetura candidata coerente, mas NÃO está materializado/validado pelo módulo R07. Rigidez de trilho DIN usado como estrutura, torque no grip, retenção após ajustes e contato com máquina permanecem abertos.

| Interface | Evidência | Estado / ação necessária |
|---|---|---|
| Esteira fixa → clamp | Não existe seção medida da máquina nesta entrega | BLOCKED: medir espessura, geometria, acesso ao parafuso/sapata e envelope móvel; não adotar vão10mm como capacidade |
| Clamp → adaptador | STL original tem 2 componentes e isSolid=false | Referência; não usar common/Volume para certificar contato. Dois sentidos de acoplagem NÃO obrigam uso simultâneo dos dois furos |
| Adaptador → Redux | Furos de R07 alinhados em X, mas datum do clip incompatível com o rail | FAIL: reconciliar plano de montagem antes de desenhar outra peça; não resolver por busca cega de translations |
| Redux → montante | normal clip paralela ao comprimento do trilho em R07 | FAIL: 182mm³ não prova mola nem encaixe. Deflexão só com trajetória/retorno/retention e ensaio |
| Montantes → travessa | STEP angle adapter é segmento DIN impresso sobre outro DIN, não união completa entre dois trilhos metálicos contínuos | REFERENCE: falta caminho de suporte/guia/trava independente para largura e altura, nos dois lados |

Não selecionar silenciosamente M6 bracket ou cantoneira dupla. O M6 é uma alternativa ainda aberta: PDF diz inserção de 5,5mm NAS EXTREMIDADES e suportes embutidos removíveis. Sua malha tem 5 componentes; scans anteriores sobre suportes e orientação não demonstram incompatibilidade. Não foi reprojetado nem certificado aqui. Adaptador com uma tomada + apoio antirotação é alternativa ADAPT a discutir, não mudança implementada.

## Medições reais
FreeCAD headless 1.1.1. `checks-build.json`, `checks-verify.json`, logs e scripts reproduzíveis acompanham esta revisão.

- Cantoneira R07 reconstruída da fonte: **2 sólidos**, apesar de `isValid=true`; STL salvo R07 também tem **2 componentes**, `isSolid=false`. Portanto validade BRep sozinha mascarava falha de peça única.
- Correção exclusivamente topológica: aba H de 66×5×20 iniciada em X=-66 passa a 71×5×20 iniciada em X=-71. Aba V e todos os cortes existentes mantidos. Junção por face **100mm²** em vez de contato sem área. Não certifica resistência nem mantém uma arquitetura escolhida; é cupom de diagnóstico.
- Candidato: **1 sólido válido**, volume **10192,515797875318mm³**, envelope **71×40×20mm**. Acréscimo material 500mm³ sem mudar envelope externo. STEP e FCStd relidos em processo separado: diferença de volume e bbox **zero**. STL fechado, 1 componente; erro relativo volume 6,3066e-6.
- Quatro superfícies cilíndricas preservadas: raios1,7 e3,175mm. Probes axiais de raio0,5mm atravessam 5mm sem material. Isto comprova passagens abertas, NÃO diâmetro de parafuso escolhido, folga de impressão, rosca ou montagem.
- 3MF Redux lido com ElementTree: unidade millimeter, um objeto id1, um item build id1 sem transform, sem componentes. Nenhum flatten por regex. 9524 facetas, malha fechada, 1 componente.
- Seções Redux Z=0,5/2/4mm mostram loops de furo centrados em X=-22,5/+28,5, Y=0, extensão X2,8mm. Translation R07 X=-33,5 leva a X=-56/-5, igual à cantoneira. **Alinhamento dos furos NÃO salva o plano de engate.**
- STEP Winford original: X comprimento75, Y profundidade7,5, Z largura35; 1 sólido válido. Rotação R07 leva comprimento a +Y e normal a +Z. Rotação Redux X=-90 leva normal local+Z a +Y: dot(normais)≈0; dot(normal_clip,comprimento_rail)=1. Orientação incompatível no datum, não apenas problema de render.
- G-clamp vendor e export R07: 3218 facetas, 2 componentes, isSolid=false. Valores Volume de shell no JSON são diagnósticos de kernel, NÃO volume físico nem prova de aptidão para boolean. Não inferir rosca ausente pela facetação, nem1/4-20 de diâmetro.
- Angle adapter100mm: 7 sólidos válidos. Seis corpos pequenos têm espessuraY0,6mm; consistente com PDF que explica suportes removíveis separados. Não unir tudo nem considerar automaticamente peças soltas defeituosas. Main body não foi ensaiado com trilho.

### Correção do próprio medidor
`checks-build.json` contém common entre sólidos adjacentes com area=0 inclusive no candidato: essa operação descarta contato de dimensão inferior. **Não usar esses campos para medir área da junção.** O verificador independente intersecta FACES em Y67 e mede100mm²; a fusão final de um sólido também passa. O teste negativo usa construção antiga e falha no critério de sólido único.

## Fontes lidas e limites
README workspace, BRIEFING e source-excerpts etapa0, RELATORIO R07, /tmp/r07b.py, provenance G-clamp, inventários DIN e documento grip-extensivel. PDFs dos autores extraídos em stage1/evidence: M6 descreve suportes/inserção; angle adapter descreve segmento impresso90°, suportes0,6mm e CC BY-NC-SA4.0. Licença G-clamp é declaração secundária de API no PROVENANCE; Redux tem declaração local não confirmada em primária nesta revisão. Nenhuma publicação autorizada.

## Entregáveis e reprodução
- `contract.json`: invariantes e escopo congelados antes de gerar CAD.
- `inputs/`, `baseline.json`: cópias e SHA das entradas originais.
- `build.py`: gera diagnóstico e cupom; `verify.py`: relê artefatos em processo separado.
- `section-summary.py`: resume componentes das seções, com junção de endpoints arredondados a0,0001mm; não é medição de tolerância física.
- `cantoneira-topology-only.FCStd`, `.step`, `.stl`: **cupom topológico, não composição aprovada**.
- `checks-build.json`, `checks-verify.json`, `redux-sections.json`, `redux-section-components.json`, logs.
- `SHA256SUMS.json`, `closeout.json`: integridade e preservação.

Executar no <host> com o freecadcmd existente e ambiente descrito em `run.sh`. Não instalar nada. Reexecução deve ocorrer em outra cópia candidata para evitar sobrescrever esta evidência.

## Bloqueios / barreira humana
Não apresentar R08 montada nem abrir uma composição falsa na GUI: gate global falhou. O FCStd do cupom pode ser aberto como diagnóstico, mas a GUI atual não foi tocada.
Antes de seguir, decidir interface clamp→rail por DATUMS e disponibilidade de fixadores reais; comprovar assento/antirotação e trajetória de engate; medir lateral fixa da máquina; estabelecer união metálica da travessa com ajustes independentes. Não avançar câmeras/Pi/cabos. Nenhuma carga, FPC200mm, FOV, retenção, impressão ou ajuste físico validado.
