"""Write the R04 report from measured MCP validation; this does not create/read CAD."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'exports/concepts/optical-rig-r04'
v=json.loads((out/'validation.json').read_text())
lines=[
'# Optical rig 3CAM — R04 — peças para impressão',
'',
f"Documento mantido: **{v['document']}**, **{v['object_count']} objetos**, incluindo ferramentas booleanas, origens, referências e **{v['print_part_count']} peças imprimíveis**.",
'',
'Arquivo de trabalho atualizado no mesmo caminho R03: `exports/concepts/optical-rig-r03/optical-rig-r03-open-portal.fcstd`. Cópia R04: `exports/concepts/optical-rig-r04/optical-rig-r04-print-ready.fcstd`. Backup anterior à continuação: `exports/concepts/optical-rig-r04/r03-before-continuation.fcstd`.',
'',
'A base 600 × 640 mm é montada com 16 placas de 150 × 160 × 18 mm. São peças PETG, sem MDF ou perfis. As emendas usam talas inferiores aparafusadas; os furos e parafusos localizam positivamente as placas. Cada poste tem três módulos, luvas e sapata; a travessa tem três segmentos, luvas e cantoneiras. As peças permanecem primitivas e operações booleanas nativas do FreeCAD, editáveis sem um módulo Python externo.',
'',
'## Resultado real dos gates',
'',
'| Check | Resultado |',
'|---|---|']
for name,passed in v['gates'].items():lines.append(f"| {name} | {'PASS' if passed else 'FAIL'} |")
lines += ['',f"Auditoria: {v['expression_audit']['checked_property_count']} propriedades de geometria/posição; {len(v['parameter_probes'])} perturbações de parâmetros. O teste negativo remove e restaura `C_LEFT.Placement.Base.y` e exige detecção. Ver `validation.json`, `expression-bindings.json` e `scripts/validate_freecad_r04.py`.",
'',
'Executar o teste dentro de `execute_code` do MCP: `exec(compile(open("<CAD_WORKSPACE>/scripts/validate_freecad_r04.py").read(), "validate_freecad_r04.py", "exec"))`. O script restaura os parâmetros, exporta, relê STEP/STL, salva os resultados e lança AssertionError se algum gate falhar.',
'',
'## Parâmetros e contrato óptico',
'',
'`Parameters` contém `camera_spacing`, `working_distance`, `top_height`, `side_y`, `side_z`, `post_x`, `post_y`, produto, base, juntas, braços, dock e adaptadores. `side_y = camera_spacing/2`; `top_height = product_z + working_distance`. Os aliases antigos R03 encaminham aos novos. Os offsets locais, ferramentas e dimensões dos componentes preservados também têm expressões na planilha. Alterar um parâmetro pode exigir uma nova impressão; os slots oferecem ajuste adicional na bancada.',
'',
'Contrato nominal preservado: C_TOP=(0,0,420), eixo −Z; C_LEFT=(0,−230,150), eixo +Y; C_RIGHT=(0,230,150), eixo −Y; produto 80 × 80 × 240 mm; FOV ilustrativo 55°. Produto, Pi, sensores e rotas de cabos permanecem fora da função estrutural do portal. As rotas de cabo são referências R03 preservadas, não chicotes físicos ou raios de curvatura validados.',
'',
'## Receiver e adaptadores intercambiáveis',
'',
'Um `receiver_common` fica na estrutura. Duas réguas de captura imprimidas separadamente fecham o canal sem exigir uma ponte de teto na impressão. A `tongue_common` tem ombro positivo e extensão externa; um came giratório bloqueia o ombro e usa pivô M5 cativo. Abrir o came requer giro de 180°. O padrão de quatro parafusos M5 da tongue é 32 × 32 mm (`dock_pitch`), comum aos três carriers.',
'',
'A/B/C são alternativas separadas para industrial, mini/acrílico e bancada. Não representam dimensões medidas dessas esteiras. `adapter_A/B/C_opening`, `grip_distance` e `slot_travel` comandam cada alternativa. Garras, porcas capturadas e pastilhas de contato são peças separadas. A posição de exibição dos adaptadores é uma vista de alternativas, não a montagem simultânea no receiver. Para montagem, alinhar o padrão do carrier ao padrão externo da tongue; apenas uma alternativa é instalada.',
'',
'## Peças, orientação e K1C',
'',
'Os STEP e STL de cada linha estão em `exports/concepts/optical-rig-r04/parts/<peça>.step` e `.stl`. Ambos já usam a orientação descrita e a origem na mesa. Os limites são medidos no BRep exportado e a leitura STEP/STL é verificada. Ferramentas booleanas, envelopes ópticos e hardware de referência não são peças de impressão.',
'',
'Material sugerido para todas as peças: PETG. Parede nominal estrutural mínima: 4 mm; placas 18 mm, talas 8 mm, pisos do receiver 6 mm, réguas 4 mm. A checagem de parede usa dimensões analíticas e ligamentos locais, não uma análise integral de espessura mínima em todos os pontos. Não há validação de processo de impressão, resistência entre camadas ou compensação de retração.',
'',
'| Peça | Dimensões orientadas (mm) | K1C | Orientação | Junta/fixadores |',
'|---|---:|---|---|---|']
for p in v['parts']:
    size=' × '.join(f'{x:.3f}'.rstrip('0').rstrip('.') for x in p['oriented_mm'])
    lines.append(f"| {p['id']} | {size} | {'PASS' if p['k1c_pass'] else 'FAIL'} | {p['orientation']} | {p['joint']} |")
lines += ['',
'Imprimir placas e talas deitadas; postes em pé; luvas com eixo da abertura vertical; cantoneiras sobre a face larga. As garras em L têm apoio plano e parede vertical. Furos horizontais pequenos e bolsões de porca exigem revisão no slicer; não foi simulado suporte. Usar o volume K1C informado pelo usuário: 220 × 220 × 250 mm. Não presumir que uma edição posterior continuará cabendo: repetir o gate.',
'',
'## BOM de hardware e peças de reposição',
'',
'| Hardware | Quantidade / aplicação |',
'|---|---|',
'| M5 × 35, porca autotravante e arruelas | 96 conjuntos nas 24 talas da base; 8 nas duas sapatas; 4 nas flanges dos sensores |',
'| M5 × 16 + inserto M5 | 8 nas luvas dos postes; 2 nas sapatas; 4 nas luvas da travessa; 4 nas cantoneiras |',
'| M5 × 25 dos suportes | 2 nos colares/postes; 2 nos tirantes/colares; 1 no braço superior/travessa |',
'| M5 × 45 + porcas e arruelas | 2 ligações dos braços laterais aos tirantes |',
'| Insertos M5 — 23 unidades | Diâmetro nominal de alojamento 6,4 mm, profundidade 8 mm; selecionar inserto compatível e testar cupom antes de inserir |',
'| M5 × 55 do receiver | 4 conjuntos passantes nas réguas/receiver/base, com arruelas e porcas |',
'| Pivô M5 × 65 cativo do came | 1 parafuso com sistema de retenção cativa, arruelas, porca autotravante e anel/arruela de retenção compatível |',
'| M5 × 30 de interface tongue/carrier | 4 por alternativa instalada, padrão 32 × 32 mm |',
'| M5 × 30 de pés das garras | 4 por alternativa; 12 para fabricar os três kits |',
'| M5 de aperto das garras + porca capturada + pastilha | 2 por alternativa; 6 para os três kits |',
'| Hastes roscadas M5 e porcas para sensores | 2: comprimentos de referência 140 e 180 mm, conferir a pilha de arruelas e acessórios; não constituem postes estruturais |',
'| M5 × 40 da bandeja da Pi | 2 com arruelas e porcas, através dos espaçadores impressos de 5 mm |',
'| Fixação da Pi e câmeras | Parafusos/arruelas/espaçadores compatíveis com o hardware realmente escolhido; envelopes não certificam furação de placa comercial |',
'',
'Os parafusos, porcas, insertos, arruelas, componentes de retenção cativa, Pi 5, três câmeras/lentes, iluminação, E18, VL53L0X, KY-040, rolete, cabos e conectores são hardware de reposição e não são impressos. O came e suas garras/pastilhas são impressos. Nenhum STEP vendor é exportado como peça de produção.',
'',
'## Evidência e limites',
'',
'Readback final MCP: `mcp-readback.json`. Vistas: `isometric.png`, `front-inspection-x.png`, `top.png`, `dock.png` e `adapters.png`. Resultados completos: `validation.json`. A contagem inclui o histórico nativo e não equivale à quantidade de peças físicas.',
'',
'As quantidades acima correspondem ao conjunto nominal. A seleção final de parafusos cativos, insertos e fixação das placas eletrônicas depende das ferragens adquiridas; dimensões de envelope não certificam a interface de uma câmera comercial.',
'',
'Esta revisão verifica geometria CAD e limites de impressão. Não valida FOV, calibração, foco, cobertura real, carga, segurança, dissipação, montagem em uma esteira específica ou encaixe em hardware comprado. Os nomes “print-ready” identificam o entregável solicitado e não uma liberação física de fabricação. Sem commit/push.',
'']
if not v['all_gates_pass']:
    lines.insert(2,'**GATES COM FALHA — não considerar a revisão concluída. Consulte validation.json.**')
(root/'reports/OPTICAL-RIG-3CAM-R04-PRINT-READY.md').write_text('\n'.join(lines))
print(root/'reports/OPTICAL-RIG-3CAM-R04-PRINT-READY.md')
