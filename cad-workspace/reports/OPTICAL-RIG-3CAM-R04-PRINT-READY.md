# Optical rig 3CAM — R04 — peças para impressão

Documento mantido: **OpticalRigR03OpenPortal**, **1263 objetos**, incluindo ferramentas booleanas, origens, referências e **95 peças imprimíveis**.

Arquivo de trabalho atualizado no mesmo caminho R03: `exports/concepts/optical-rig-r03/optical-rig-r03-open-portal.fcstd`. Cópia R04: `exports/concepts/optical-rig-r04/optical-rig-r04-print-ready.fcstd`. Backup anterior à continuação: `exports/concepts/optical-rig-r04/r03-before-continuation.fcstd`.

A base 600 × 640 mm é montada com 16 placas de 150 × 160 × 18 mm. São peças PETG, sem MDF ou perfis. As emendas usam talas inferiores aparafusadas; os furos e parafusos localizam positivamente as placas. Cada poste tem três módulos, luvas e sapata; a travessa tem três segmentos, luvas e cantoneiras. As peças permanecem primitivas e operações booleanas nativas do FreeCAD, editáveis sem um módulo Python externo.

## Resultado real dos gates

| Check | Resultado |
|---|---|
| all_parts_fit_k1c | PASS |
| all_parts_valid_single_solids | PASS |
| exports_roundtrip | PASS |
| all_required_bindings | PASS |
| negative_test_detects_unlinked_position | PASS |
| parameter_response | PASS |
| document_recompute | PASS |
| r03_contract_preserved | PASS |
| corridor_clear | PASS |
| manufactured_parts_no_solid_overlap | PASS |
| adapter_assemblies_no_solid_overlap | PASS |
| same_receiver_pattern_ABC | PASS |
| cam_positive_geometric_retention | PASS |
| analytical_structural_sections_min_4mm | PASS |

Auditoria: 4597 propriedades de geometria/posição; 28 perturbações de parâmetros. O teste negativo remove e restaura `C_LEFT.Placement.Base.y` e exige detecção. Ver `validation.json`, `expression-bindings.json` e `scripts/validate_freecad_r04.py`.

Executar o teste dentro de `execute_code` do MCP: `exec(compile(open("/home/<usuario>/tcc-pnaat/github/cad-workspace/scripts/validate_freecad_r04.py").read(), "validate_freecad_r04.py", "exec"))`. O script restaura os parâmetros, exporta, relê STEP/STL, salva os resultados e lança AssertionError se algum gate falhar.

## Parâmetros e contrato óptico

`Parameters` contém `camera_spacing`, `working_distance`, `top_height`, `side_y`, `side_z`, `post_x`, `post_y`, produto, base, juntas, braços, dock e adaptadores. `side_y = camera_spacing/2`; `top_height = product_z + working_distance`. Os aliases antigos R03 encaminham aos novos. Os offsets locais, ferramentas e dimensões dos componentes preservados também têm expressões na planilha. Alterar um parâmetro pode exigir uma nova impressão; os slots oferecem ajuste adicional na bancada.

Contrato nominal preservado: C_TOP=(0,0,420), eixo −Z; C_LEFT=(0,−230,150), eixo +Y; C_RIGHT=(0,230,150), eixo −Y; produto 80 × 80 × 240 mm; FOV ilustrativo 55°. Produto, Pi, sensores e rotas de cabos permanecem fora da função estrutural do portal. As rotas de cabo são referências R03 preservadas, não chicotes físicos ou raios de curvatura validados.

## Receiver e adaptadores intercambiáveis

Um `receiver_common` fica na estrutura. Duas réguas de captura imprimidas separadamente fecham o canal sem exigir uma ponte de teto na impressão. A `tongue_common` tem ombro positivo e extensão externa; um came giratório bloqueia o ombro e usa pivô M5 cativo. Abrir o came requer giro de 180°. O padrão de quatro parafusos M5 da tongue é 32 × 32 mm (`dock_pitch`), comum aos três carriers.

A/B/C são alternativas separadas para industrial, mini/acrílico e bancada. Não representam dimensões medidas dessas esteiras. `adapter_A/B/C_opening`, `grip_distance` e `slot_travel` comandam cada alternativa. Garras, porcas capturadas e pastilhas de contato são peças separadas. A posição de exibição dos adaptadores é uma vista de alternativas, não a montagem simultânea no receiver. Para montagem, alinhar o padrão do carrier ao padrão externo da tongue; apenas uma alternativa é instalada.

## Peças, orientação e K1C

Os STEP e STL de cada linha estão em `exports/concepts/optical-rig-r04/parts/<peça>.step` e `.stl`. Ambos já usam a orientação descrita e a origem na mesa. Os limites são medidos no BRep exportado e a leitura STEP/STL é verificada. Ferramentas booleanas, envelopes ópticos e hardware de referência não são peças de impressão.

Material sugerido para todas as peças: PETG. Parede nominal estrutural mínima: 4 mm; placas 18 mm, talas 8 mm, pisos do receiver 6 mm, réguas 4 mm. A checagem de parede usa dimensões analíticas e ligamentos locais, não uma análise integral de espessura mínima em todos os pontos. Não há validação de processo de impressão, resistência entre camadas ou compensação de retração.

| Peça | Dimensões orientadas (mm) | K1C | Orientação | Junta/fixadores |
|---|---:|---|---|---|
| base_joint_x_1_1 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_1_2 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_1_3 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_1_4 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_2_1 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_2_2 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_2_3 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_2_4 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_3_1 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_3_2 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_3_3 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_x_3_4 | 50 × 40 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_1_1 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_1_2 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_1_3 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_1_4 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_2_1 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_2_2 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_2_3 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_2_4 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_3_1 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_3_2 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_3_3 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| base_joint_y_3_4 | 40 × 50 × 8 | PASS | XY flat; +Z up | 4 M5x35 + washers + locking nuts; bolts locate both plates |
| post_left_seg_1 | 30 × 30 × 164.667 | PASS | post axis +Z; print upright, insert bores horizontal | Sleeve socket + M5 screw into blind M5 insert at each end |
| post_left_seg_3 | 30 × 30 × 164.667 | PASS | post axis +Z; print upright, insert bores horizontal | Sleeve socket + M5 screw into blind M5 insert at each end |
| post_left_joint_1 | 46.6 × 46.6 × 48 | PASS | socket axis +Z; open through bore | 2 M5x16 and 2 M5 inserts in adjacent segments; 24 mm engagement per segment |
| post_left_joint_2 | 46.6 × 46.6 × 48 | PASS | socket axis +Z; open through bore | 2 M5x16 and 2 M5 inserts in adjacent segments; 24 mm engagement per segment |
| post_left_foot | 90 × 90 × 32 | PASS | XY flat; +Z up | Socket + M5x16 into bottom insert; 4 M5 through slot/plate with backing washers |
| post_right_seg_1 | 30 × 30 × 164.667 | PASS | post axis +Z; print upright, insert bores horizontal | Sleeve socket + M5 screw into blind M5 insert at each end |
| post_right_seg_3 | 30 × 30 × 164.667 | PASS | post axis +Z; print upright, insert bores horizontal | Sleeve socket + M5 screw into blind M5 insert at each end |
| post_right_joint_1 | 46.6 × 46.6 × 48 | PASS | socket axis +Z; open through bore | 2 M5x16 and 2 M5 inserts in adjacent segments; 24 mm engagement per segment |
| post_right_joint_2 | 46.6 × 46.6 × 48 | PASS | socket axis +Z; open through bore | 2 M5x16 and 2 M5 inserts in adjacent segments; 24 mm engagement per segment |
| post_right_foot | 90 × 90 × 32 | PASS | XY flat; +Z up | Socket + M5x16 into bottom insert; 4 M5 through slot/plate with backing washers |
| crossbar_seg_1 | 30 × 130 × 30 | PASS | XY flat; +Z up | 2 M5 blind insert sockets; external sleeves lock adjacent modules |
| crossbar_seg_3 | 30 × 130 × 30 | PASS | XY flat; +Z up | 2 M5 blind insert sockets; external sleeves lock adjacent modules |
| crossbar_joint_1 | 46.6 × 46.6 × 48 | PASS | rotate +90 deg about X; open sleeve axis vertical | 2 M5x16 + 2 M5 inserts in crossbar ends |
| crossbar_joint_2 | 46.6 × 46.6 × 48 | PASS | rotate +90 deg about X; open sleeve axis vertical | 2 M5x16 + 2 M5 inserts in crossbar ends |
| crossbar_left_corner | 60 × 60 × 8 | PASS | rotate +90 deg about Y; 60x60 face on bed | 2 M5x16 into post and crossbar blind inserts; two-sided bearing at corner |
| crossbar_right_corner | 60 × 60 × 8 | PASS | rotate +90 deg about Y; 60x60 face on bed | 2 M5x16 into post and crossbar blind inserts; two-sided bearing at corner |
| camera_mount_left | 125 × 24 × 16 | PASS | XY flat; +Z up | Two 18 mm M5 slots; swivel/translation before tightening; camera requires separate M2 mounting plate |
| camera_mount_right | 125 × 24 × 16 | PASS | XY flat; +Z up | Two 18 mm M5 slots; swivel/translation before tightening; camera requires separate M2 mounting plate |
| camera_mount_top | 125 × 30 × 14 | PASS | XY flat; +Z up | Two 18 mm M5 slots; swivel/translation before tightening; camera requires separate M2 mounting plate |
| receiver_common | 140 × 82 × 22 | PASS | XY flat; +Z up | 4 M5 through mounting/lip bolts; 1 captive M5 cam pivot; capture lips trap tongue vertically |
| receiver_capture_lip_1 | 140 × 18 × 4 | PASS | XY flat; +Z up | 2 shared M5 through receiver and base; 4 mm retaining overhang |
| receiver_capture_lip_2 | 140 × 18 × 4 | PASS | XY flat; +Z up | 2 shared M5 through receiver and base; 4 mm retaining overhang |
| tongue_common | 190 × 52 × 27 | PASS | XY flat; +Z up | 4 M5 on common 32x32 pattern to any A/B/C adapter; 10 mm end shoulder blocked by cam |
| adapter_A_carrier | 180 × 150 × 10 | PASS | XY flat; +Z up | Same 32x32 M5 tongue pattern; slotted jaw reach controlled by grip_distance and slot_travel |
| adapter_B_carrier | 180 × 150 × 10 | PASS | XY flat; +Z up | Same 32x32 M5 tongue pattern; slotted jaw reach controlled by grip_distance and slot_travel |
| adapter_C_carrier | 180 × 150 × 10 | PASS | XY flat; +Z up | Same 32x32 M5 tongue pattern; slotted jaw reach controlled by grip_distance and slot_travel |
| post_left_seg_2 | 30 × 30 × 164.667 | PASS | post axis +Z; print upright, insert bores horizontal | Sleeve socket + M5 screw into blind M5 insert at each end |
| post_right_seg_2 | 30 × 30 × 164.667 | PASS | post axis +Z; print upright, insert bores horizontal | Sleeve socket + M5 screw into blind M5 insert at each end |
| cam_positive_lock | 50 × 42 × 8 | PASS | XY flat; +Z up | Positive rotary dog blocks shoulder; 180 degree opening; captive M5 pivot with washer, locknut and E-clip |
| Pi5TrayOutsideSweep_printed | 110 × 85 × 5 | PASS | XY flat; +Z up | 2 M5 through holes; separate printed support, retain R03 sensor position |
| E18_SeparateTriggerArm_printed | 24 × 125 × 12 | PASS | XY flat; +Z up | 2 M5 through holes; separate printed support, retain R03 sensor position |
| E18_TriggerArmPost_printed | 20 × 20 × 83 | PASS | XY flat; +Z up | 2 M5 through holes; separate printed support, retain R03 sensor position |
| VL53_DiagnosticArm_printed | 15 × 85 × 8 | PASS | XY flat; +Z up | 2 M5 through holes; separate printed support, retain R03 sensor position |
| VL53_DiagnosticPost_printed | 15 × 15 × 128 | PASS | XY flat; +Z up | 2 M5 through holes; separate printed support, retain R03 sensor position |
| base_plate_1_1 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_1_2 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_1_3 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_1_4 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_2_1 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_2_2 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_2_3 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_2_4 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_3_1 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_3_2 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_3_3 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_3_4 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_4_1 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_4_2 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_4_3 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| base_plate_4_4 | 150 × 160 × 18 | PASS | XY flat; +Z up | 4-hole M5 bolted spline at each internal edge; dedicated installation bores |
| camera_tie_left | 30 × 46.7 × 16 | PASS | XY flat; +Z up | Longitudinal M5 slot for transverse reach |
| camera_tie_right | 30 × 46.7 × 16 | PASS | XY flat; +Z up | Longitudinal M5 slot for transverse reach |
| E18_TriggerArmPost_base_flange | 50 × 50 × 8 | PASS | XY flat; +Z up | M5 center through bolt to post; two M5 flange screws to base |
| VL53_DiagnosticPost_base_flange | 50 × 50 × 8 | PASS | XY flat; +Z up | M5 center through bolt to post; two M5 flange screws to base |
| adapter_A_jaw_1 | 50 × 24 × 63 | PASS | XY flat; +Z up | Two M5 foot bolts; M5 clamp screw with captive nut and separate swivel pad |
| adapter_A_jaw_1_pad | 24 × 24 × 8 | PASS | XY flat; +Z up | M5 screw and washer into a replaceable contact pad; pad shown in exploded position |
| adapter_A_jaw_2 | 50 × 24 × 63 | PASS | XY flat; +Z up | Two M5 foot bolts; M5 clamp screw with captive nut and separate swivel pad |
| adapter_A_jaw_2_pad | 24 × 24 × 8 | PASS | XY flat; +Z up | M5 screw and washer into a replaceable contact pad; pad shown in exploded position |
| adapter_B_jaw_1 | 50 × 24 × 63 | PASS | XY flat; +Z up | Two M5 foot bolts; M5 clamp screw with captive nut and separate swivel pad |
| adapter_B_jaw_1_pad | 24 × 24 × 8 | PASS | XY flat; +Z up | M5 screw and washer into a replaceable contact pad; pad shown in exploded position |
| adapter_B_jaw_2 | 50 × 24 × 63 | PASS | XY flat; +Z up | Two M5 foot bolts; M5 clamp screw with captive nut and separate swivel pad |
| adapter_B_jaw_2_pad | 24 × 24 × 8 | PASS | XY flat; +Z up | M5 screw and washer into a replaceable contact pad; pad shown in exploded position |
| adapter_C_jaw_1 | 50 × 24 × 63 | PASS | XY flat; +Z up | Two M5 foot bolts; M5 clamp screw with captive nut and separate swivel pad |
| adapter_C_jaw_1_pad | 24 × 24 × 8 | PASS | XY flat; +Z up | M5 screw and washer into a replaceable contact pad; pad shown in exploded position |
| adapter_C_jaw_2 | 50 × 24 × 63 | PASS | XY flat; +Z up | Two M5 foot bolts; M5 clamp screw with captive nut and separate swivel pad |
| adapter_C_jaw_2_pad | 24 × 24 × 8 | PASS | XY flat; +Z up | M5 screw and washer into a replaceable contact pad; pad shown in exploded position |
| crossbar_seg_2 | 30 × 130 × 30 | PASS | XY flat; +Z up | 2 M5 blind insert sockets; external sleeves lock adjacent modules |
| camera_post_collar_left | 62.6 × 62.6 × 24 | PASS | XY flat; +Z up | M5x25 lateral insert screw to post + M5x25 vertical insert screw through tie slot; 16 mm sleeve wall |
| camera_post_collar_right | 62.6 × 62.6 × 24 | PASS | XY flat; +Z up | M5x25 lateral insert screw to post + M5x25 vertical insert screw through tie slot; 16 mm sleeve wall |
| pi_tray_spacer_1 | 16 × 16 × 5 | PASS | XY flat; +Z up | M5 through tray, 5 mm annular spacer and base; 5.2 mm radial wall |
| pi_tray_spacer_2 | 16 × 16 × 5 | PASS | XY flat; +Z up | M5 through tray, 5 mm annular spacer and base; 5.2 mm radial wall |

Imprimir placas e talas deitadas; postes em pé; luvas com eixo da abertura vertical; cantoneiras sobre a face larga. As garras em L têm apoio plano e parede vertical. Furos horizontais pequenos e bolsões de porca exigem revisão no slicer; não foi simulado suporte. Usar o volume K1C informado pelo usuário: 220 × 220 × 250 mm. Não presumir que uma edição posterior continuará cabendo: repetir o gate.

## BOM de hardware e peças de reposição

| Hardware | Quantidade / aplicação |
|---|---|
| M5 × 35, porca autotravante e arruelas | 96 conjuntos nas 24 talas da base; 8 nas duas sapatas; 4 nas flanges dos sensores |
| M5 × 16 + inserto M5 | 8 nas luvas dos postes; 2 nas sapatas; 4 nas luvas da travessa; 4 nas cantoneiras |
| M5 × 25 dos suportes | 2 nos colares/postes; 2 nos tirantes/colares; 1 no braço superior/travessa |
| M5 × 45 + porcas e arruelas | 2 ligações dos braços laterais aos tirantes |
| Insertos M5 — 23 unidades | Diâmetro nominal de alojamento 6,4 mm, profundidade 8 mm; selecionar inserto compatível e testar cupom antes de inserir |
| M5 × 55 do receiver | 4 conjuntos passantes nas réguas/receiver/base, com arruelas e porcas |
| Pivô M5 × 65 cativo do came | 1 parafuso com sistema de retenção cativa, arruelas, porca autotravante e anel/arruela de retenção compatível |
| M5 × 30 de interface tongue/carrier | 4 por alternativa instalada, padrão 32 × 32 mm |
| M5 × 30 de pés das garras | 4 por alternativa; 12 para fabricar os três kits |
| M5 de aperto das garras + porca capturada + pastilha | 2 por alternativa; 6 para os três kits |
| Hastes roscadas M5 e porcas para sensores | 2: comprimentos de referência 140 e 180 mm, conferir a pilha de arruelas e acessórios; não constituem postes estruturais |
| M5 × 40 da bandeja da Pi | 2 com arruelas e porcas, através dos espaçadores impressos de 5 mm |
| Fixação da Pi e câmeras | Parafusos/arruelas/espaçadores compatíveis com o hardware realmente escolhido; envelopes não certificam furação de placa comercial |

Os parafusos, porcas, insertos, arruelas, componentes de retenção cativa, Pi 5, três câmeras/lentes, iluminação, E18, VL53L0X, KY-040, rolete, cabos e conectores são hardware de reposição e não são impressos. O came e suas garras/pastilhas são impressos. Nenhum STEP vendor é exportado como peça de produção.

## Evidência e limites

Readback final MCP: `mcp-readback.json`. Vistas: `isometric.png`, `front-inspection-x.png`, `top.png`, `dock.png` e `adapters.png`. Resultados completos: `validation.json`. A contagem inclui o histórico nativo e não equivale à quantidade de peças físicas.

As quantidades acima correspondem ao conjunto nominal. A seleção final de parafusos cativos, insertos e fixação das placas eletrônicas depende das ferragens adquiridas; dimensões de envelope não certificam a interface de uma câmera comercial.

Esta revisão verifica geometria CAD e limites de impressão. Não valida FOV, calibração, foco, cobertura real, carga, segurança, dissipação, montagem em uma esteira específica ou encaixe em hardware comprado. Os nomes “print-ready” identificam o entregável solicitado e não uma liberação física de fabricação. Sem commit/push.
