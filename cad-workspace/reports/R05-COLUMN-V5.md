# R05 Column V5 — gates geométricos PASS

Documento FreeCAD real: **R05ColumnV5**, **59 objetos**, **49 peças físicas** (17 impressas e 32 envelopes de ferragens). Construção e auditoria por MCP qwen-mm-plugins-freecad, com Part/OCCT nativo. Nenhuma geometria da coluna v1/v3/v4 foi importada.

## Resultados

| Gate | Resultado | Evidência medida |
|---|---|---|
| 1. Interferência | PASS | 1176 pares, volume máximo 0.00000000 mm³; todos os 49 sólidos físicos válidos e conexos. |
| 2. Garrafa | PASS | H370/D120, Y[-60,60]; zero colisão. Menor distância: 101.01009 mm. |
| 3. C_TOP | PASS | Frente da lente no STEP oficial CM3 Wide em Z540, direção −Z. |
| 4. Encaixes + M4 | PASS | Cinco interfaces em Z140/235/330/425/520, vão axial 0 mm; ombro conectado de 12 mm, bolso de 12,2 mm, folga lateral 0,2 mm. M4 Ø4 em furos Ø4,4 e porcas modeladas. |
| 5. Canal FPC | PASS | Sonda sólida conexa 20×10 mm: zero volume ocupado em todas as 49 peças físicas. |
| 6. Grip trocável | PASS | Sleeve e adaptador com abertura passante 20×10 mm e quatro furos Ø4,4 no padrão 60×44 mm. |
| 7. K1C | PASS | Todas as peças cabem em 220×220×250 mm mediante orientação indicada abaixo. |

Tolerância de decisão para volume: 1e-5 mm³. Contato entre faces é permitido; nenhum par apresentou sobreposição volumétrica positiva. O gate 1 enumera peças impressas e envelopes de ferragens, inclusive case, grip e mounts derivados. Garrafa tem checagem separada. STEPs eletrônicos e painel de backlight são corpos de referência, excluídos da enumeração de peças fabricadas. O encaixe detalhado da eletrônica não foi certificado.

## Arquitetura e correções da v3

A case pipiece está **de pé**: X[-32,72;32,72], Y[-216,57;-183,43], Z[20;124,85] mm. O eixo longo original X foi transformado para +Z por rotação de −120° em torno de (1,1,1), seguida de translação. A transformação foi incorporada ao BRep depois dos cortes; por isso o Placement final do objeto é identidade. A case participa da haste entre sleeve inferior e collar superior, sem torre externa contornando-a.

- Grip light-clamp real abaixo de Z0; adaptador específico removível ligado à interface padrão da sleeve. O grip conserva a sede cilíndrica nominal 28,7 mm do original e usa parafuso transversal 1/4 de polegada. A borda específica da esteira continua agnóstica: o adaptador pode receber outro grip, e nenhuma esteira foi modelada.
- Sleeve em Z8–45 e collar superior em Z105–152. Aberturas FPC cortadas também nas extremidades da case real. Limpeza de malha preservou o volume de origem 55110,605427 mm³; após as aberturas, case = 54497,167834 mm³.
- Quatro módulos novos com passo 95 mm. Ombro superior unido por booleano ao corpo, bolso inferior, furos transversais M4, canal atravessando ombros. Não há os vãos de 42 mm da v3.
- A sleeve não invade o módulo 1. O ombro do módulo 4 entra no bolso da crossbar em Z520–532, sem overlap.
- Crossbar possui riser Z520–594 e braço Z580–594. A articulação C_TOP fica abaixo do braço, colocando a frente mecânica da lente Wide em Z540. O topo da estrutura em Z594 não é a altura óptica.
- C_LEFT/C_RIGHT estão nas orelhas integradas ao módulo 2, com pivôs X±55, Y−165, Z245. Os cradles pan M5/tilt M4 vêm do FCStd pi-camera-mounts. Backplates foram substituídos por peças com o padrão oficial CM3 Ø2,2 (X local 2/14,5; Y local 2/23 mm), após a aprovação geométrica do conjunto principal.
- Backlight de referência atrás da garrafa, em X140, corredor transversal Y[-80,80]; coluna centralizada em Y−200. Não houve validação óptica.

A sonda FPC sobe desde Z8 até Z596 em X[-10,10], Y[-205,-195]. No topo percorre Z582–592 até Y−19 e desce pela saída Y[-29,-19] até Z548, contornando o pivô M5. É uma sonda geométrica de passagem, não uma verificação de raio de dobra ou de comprimento do cabo.

## K1C por peça

Dimensões abaixo já orientadas nos eixos de impressão X×Y×Z. O teste é de envelope, sem brim, suportes ou fatiamento. Ferragens são envelopes de peças compradas; suas dimensões constam para completar a auditoria.

| Peça | Tipo | Envelope orientado (mm) | Eixos de montagem → impressão | Resultado |
|---|---|---|---|---|
| PIPIECE_CASE_VERTICAL | Impressa | 65.44 × 33.14 × 104.85 | X / Y / Z | PASS |
| LIGHTCLAMP_BODY | Impressa | 38.00 × 25.00 × 100.00 | X / Y / Z | PASS |
| LIGHTCLAMP_JAW | Impressa | 19.00 × 25.00 × 50.00 | X / Y / Z | PASS |
| GripCrossBolt_N12 | Ferragem | 6.99 × 35.00 × 6.98 | X / Y / Z | PASS |
| GripCrossNut_N12 | Ferragem | 8.00 × 3.00 × 8.00 | X / Y / Z | PASS |
| GripCrossBolt_12 | Ferragem | 6.99 × 35.00 × 6.98 | X / Y / Z | PASS |
| GripCrossNut_12 | Ferragem | 8.00 × 3.00 × 8.00 | X / Y / Z | PASS |
| BaseM4_N30_N222 | Ferragem | 6.99 × 6.99 × 24.00 | X / Y / Z | PASS |
| BaseNut_N30_N222 | Ferragem | 8.00 × 8.00 × 3.00 | X / Y / Z | PASS |
| BaseM4_N30_N178 | Ferragem | 6.99 × 6.99 × 24.00 | X / Y / Z | PASS |
| BaseNut_N30_N178 | Ferragem | 8.00 × 8.00 × 3.00 | X / Y / Z | PASS |
| BaseM4_30_N222 | Ferragem | 6.99 × 6.99 × 24.00 | X / Y / Z | PASS |
| BaseNut_30_N222 | Ferragem | 8.00 × 8.00 × 3.00 | X / Y / Z | PASS |
| BaseM4_30_N178 | Ferragem | 6.99 × 6.99 × 24.00 | X / Y / Z | PASS |
| BaseNut_30_N178 | Ferragem | 8.00 × 8.00 × 3.00 | X / Y / Z | PASS |
| GRIP_STANDARD_ADAPTER | Impressa | 76.00 × 60.00 × 20.00 | X / Y / Z | PASS |
| BASE_SLEEVE | Impressa | 76.00 × 60.00 × 37.00 | X / Y / Z | PASS |
| CASE_TOP_COLLAR | Impressa | 74.00 × 41.00 × 47.00 | X / Y / Z | PASS |
| MODULE_1 | Impressa | 40.00 × 32.00 × 107.00 | X / Y / Z | PASS |
| JointM4_0 | Ferragem | 52.00 × 6.99 × 6.98 | X / Y / Z | PASS |
| JointM4_0_NutEnvelope | Ferragem | 3.00 × 8.00 × 8.00 | X / Y / Z | PASS |
| MODULE_2 | Impressa | 176.00 × 32.00 × 114.00 | X / Y / Z | PASS |
| JointM4_1 | Ferragem | 52.00 × 6.99 × 6.98 | X / Y / Z | PASS |
| JointM4_1_NutEnvelope | Ferragem | 3.00 × 8.00 × 8.00 | X / Y / Z | PASS |
| MODULE_3 | Impressa | 40.00 × 32.00 × 107.00 | X / Y / Z | PASS |
| JointM4_2 | Ferragem | 52.00 × 6.99 × 6.98 | X / Y / Z | PASS |
| JointM4_2_NutEnvelope | Ferragem | 3.00 × 8.00 × 8.00 | X / Y / Z | PASS |
| MODULE_4 | Impressa | 40.00 × 32.00 × 107.00 | X / Y / Z | PASS |
| JointM4_3 | Ferragem | 52.00 × 6.99 × 6.98 | X / Y / Z | PASS |
| JointM4_3_NutEnvelope | Ferragem | 3.00 × 8.00 × 8.00 | X / Y / Z | PASS |
| CROSSBAR_C_TOP | Impressa | 40.00 × 74.00 × 236.00 | X / Z / Y | PASS |
| JointM4_4 | Ferragem | 52.00 × 6.99 × 6.98 | X / Y / Z | PASS |
| JointM4_4_NutEnvelope | Ferragem | 3.00 × 8.00 × 8.00 | X / Y / Z | PASS |
| Grip_QuarterInch_Screw | Ferragem | 52.00 × 10.95 × 11.00 | X / Y / Z | PASS |
| C_TOP_PAN_TILT_CRADLE | Impressa | 66.00 × 20.00 × 40.50 | X / Y / Z | PASS |
| C_TOP_CM3_BACKPLATE | Impressa | 57.60 × 32.00 × 15.00 | X / Y / Z | PASS |
| C_TOP_TILT_M4_L | Ferragem | 12.00 × 6.99 × 6.99 | X / Y / Z | PASS |
| C_TOP_TILT_M4_R | Ferragem | 12.00 × 6.99 × 6.99 | X / Y / Z | PASS |
| C_TOP_PAN_M5 | Ferragem | 8.50 × 8.50 × 26.00 | X / Y / Z | PASS |
| C_LEFT_PAN_TILT_CRADLE | Impressa | 66.00 × 40.50 × 20.00 | X / Y / Z | PASS |
| C_LEFT_CM3_BACKPLATE | Impressa | 57.60 × 15.00 × 32.00 | X / Y / Z | PASS |
| C_LEFT_TILT_M4_L | Ferragem | 12.00 × 6.99 × 6.99 | X / Y / Z | PASS |
| C_LEFT_TILT_M4_R | Ferragem | 12.00 × 6.99 × 6.99 | X / Y / Z | PASS |
| C_LEFT_PAN_M5 | Ferragem | 8.50 × 28.00 × 8.49 | X / Y / Z | PASS |
| C_RIGHT_PAN_TILT_CRADLE | Impressa | 66.00 × 40.50 × 20.00 | X / Y / Z | PASS |
| C_RIGHT_CM3_BACKPLATE | Impressa | 57.60 × 15.00 × 32.00 | X / Y / Z | PASS |
| C_RIGHT_TILT_M4_L | Ferragem | 12.00 × 6.99 × 6.99 | X / Y / Z | PASS |
| C_RIGHT_TILT_M4_R | Ferragem | 12.00 × 6.99 × 6.99 | X / Y / Z | PASS |
| C_RIGHT_PAN_M5 | Ferragem | 8.50 × 28.00 × 8.49 | X / Y / Z | PASS |

A crossbar usa X/Z/Y: seu comprimento de 236 mm fica no eixo vertical de impressão, dentro de 250 mm.

## Parâmetros e referências

Spreadsheet **Parameters** com aliases: `module_h=95`, `wall=4`, `ch=20`, `col_y=-200`, `top_z=540`, `jaw_opening=28.7`. Os aliases registram o snapshot validado; `Pitch` dos módulos lê `module_h`. Os sólidos são BReps nativos, e a montagem não possui propagação paramétrica completa: alterar células exige regenerar a geometria e repetir os gates.

Referências oficiais importadas somente após as checagens do conjunto principal: Pi5, CM3 Wide superior e duas CM3 Standard laterais. Pi5 fica oculto por padrão como referência. A altura usa a frente mecânica da lente, sem inferir pupila de entrada.

Licenças/fontes: pipiece e light-clamp ISC; cinemática derivada de pi-camera-mounts GPL-2.0, com arquivo LICENSE preservado em references/vendor. Hashes das fontes e do FCStd estão no JSON.

## Arquivos

- [FCStd](../exports/concepts/optical-rig-r05/optical-rig-r05-column-v5.fcstd)
- [validation.json](../exports/concepts/optical-rig-r05/validation.json)
- [Isométrica](../exports/concepts/optical-rig-r05/v5-isometric.png)
- [Frontal](../exports/concepts/optical-rig-r05/v5-front.png)
- [Direita](../exports/concepts/optical-rig-r05/v5-right.png)
- [Superior](../exports/concepts/optical-rig-r05/v5-top.png)
- [Canal FPC transparente](../exports/concepts/optical-rig-r05/v5-fpc-continuous.png)
- [Construção reproduzível via MCP](../scripts/freecad_r05_v5.py), [auditoria](../scripts/freecad_r05_v5_validate.py)

## Erros MCP recuperados

- Biblioteca opcional: `Failed to get parts list: <Fault 1: "<class 'FileNotFoundError'>:Not found: /home/nerton/.local/share/FreeCAD/v1-1/Mod/parts_library">`. Foram usadas as referências locais solicitadas.
- Primeira conversão: `OCCError: Removing splitter failed`. Recuperado após limpeza das facetas degeneradas e costura com tolerância menor; sólido final válido.
- Cor da sonda: `TypeError: Type in tuple must be consistent (integer)`. Corrigido usando componentes float.

FOV, carga e safety não foram avaliados. Sem commit/push.
