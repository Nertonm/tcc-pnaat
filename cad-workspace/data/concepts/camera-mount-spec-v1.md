# SPEC: Mount da câmera CM3 Wide para trilho DIN TS35 (v1)

Status: **spec congelada antes da modelagem** (2026-09-10). Todos os números
abaixo foram EXTRAÍDOS de fonte primária (STEP oficial / medição das peças),
não estimados. Cada item traz a origem.

## Contexto
Peça que falta no rig R05. Recebe a Raspberry Pi Camera Module 3 Wide, inclina
o eixo óptico em 49° e se fixa ao trilho DIN TS35 que corre na vertical.
Todas as demais peças do rig já são prontas (case Pi5 DIN, angle adapter 90°,
bracket M6, trilho comercial).

## A. Interface 1: trilho DIN TS35 (IEC 60715)
| item | valor | origem |
|---|---|---|
| perfil do trilho | 35 mm largura × 7.5 mm profundidade | norma IEC 60715 |
| abertura das garras | 34 mm (closed_width) a 36 mm | `DIN Rail Bracket Redux` parâmetros do autor + medição do STL (garras em X: -27..-14 e +22..+28) |
| extensão ao longo do trilho | 18 mm (mín.); adotar 24–30 mm p/ estabilidade | bbox medido do Redux (Y=18) |
| altura do perfil do clip | 7.6 mm | bbox medido (Z=7.6) |
| mola | 1.6 mm de espessura, raio interno 0.4 mm | parâmetros do autor |
| folga de deslizamento | 0.2 mm | parâmetros do autor |
| trava anti-deriva | **parafuso M3** contra o trilho (a definir no desenho) | requisito do doc grip-extensivel (estabilizar pós-ajuste) |

**Decisão de design:** importar `din-clip-redux-*.3mf` como base (garante o
encaixe DIN medido) em vez de redesenhar o clip; elimina a maior fonte de erro.

## B. Interface 2: Camera Module 3 Wide (STEP oficial)
Sistema local do STEP (`Camera_module_3_wide_model_simple.stp`):
| item | valor | origem |
|---|---|---|
| PCB | 23.86 (X) × 25.00 (Y) mm | bbox + faces planas |
| plano da PCB | Z ≈ 0 (faces de área 2111 / 1757 mm²) | análise de faces |
| corpo total | 23.86 × 25.00 × 11.40 mm (Z −8.81..+2.60) | bbox |
| furos de montagem | **Ø2.2 mm**, eixo Z, em Z=−0.366 | 8 faces cilíndricas r=1.10 |
| posições dos furos | X ∈ {2.00, 14.50}; Y ∈ {1.30, 2.70, 22.30, 23.70} | idem |
| **caixa dos furos** | **12.50 (X) × 22.40 (Y) mm** (externos) | derivado |
| lente | aponta **−Z**, centro (X=14.40, Y=12.50), Ø externo ≈11 mm, corpo até Z=−8.81 | faces circulares r≈5.4 + bbox |
| conector FPC | borda **X 18.0–23.5**, Y≈12.5, **Z 0.8–2.6** | faces planas em Z>0 |
| folga obrigatória | região do conector LIVRE (nenhum material do mount) | requisito mecânico |

Atenção: o centro da lente (X=14.40) **não** coincide com o centro da PCB
(X=11.93); deslocado +2.5 mm em X.

## C. Óptica (da análise R05-CAMERA-DISTANCE-ANALYSIS)
| item | valor |
|---|---|
| inclinação do eixo óptico | 49° (elevação, pior caso 2L com CM3 Wide) |
| distância de trabalho | ~171 mm do eixo da garrafa |
| ajuste fino de ângulo | pivot com trava (do doc grip-extensivel) |
| cabo | FPC 200 mm Standard-Mini; saída sem dobra aguda |

## D. Fabricação
| item | valor |
|---|---|
| impressora | Creality K1C, envelope 220×220×250 mm |
| material | PETG |
| meta | peça única, sem suporte se possível |
| encaixe da câmera | retenção por ressaltos/pinos (evitar parafuso na PCB) + 1 M2 opcional |

## E. Gates de validação (determinísticos, antes de declarar pronto)
1. sólido único válido (`isValid()`, contagem de solids == 1)
2. bbox dentro de 220×220×250 mm
3. abertura das garras entre 34 e 36 mm (encaixa no TS35)
4. caixa dos pinos/ressaltos do berço == 12.50 × 22.40 mm (±0.2)
5. abertura da lente: Ø ≥ 11 mm, centrada em (14.40, 12.50) local
6. região do conector (X 18.0–23.5, Y≈12.5, Z 0.8–2.6) sem material
7. ângulo assinado do berço == 49° ± 0.5 (via normal transformada)
8. round-trip: export → reimport → mesmos invariantes

## F. Riscos identificados (com mitigação)
| risco | mitigação |
|---|---|
| folga do clip → jitter na vibração | trava M3 + altura reduzida do braço |
| cantilever da câmera no clip | clip estendido (24–30 mm ao longo do trilho) |
| conector FPC bloqueado | gate 6 obrigatório |
| lente deslocada (X=14.4 vs 12.0) | gate 5 usa o centro real da lente |

## G. Fora de escopo desta peça
- travessa/horizontal e sua corrida → angle adapter (pronta)
- fixação na esteira → bracket M6 (pronta)
- host da Pi → case Diyalec (pronta)
