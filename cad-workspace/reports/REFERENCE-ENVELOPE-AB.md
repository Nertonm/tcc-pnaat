# Envelope comparativo A/B - referência visual

reference_only=true; measured=false; fabrication_allowed=false. Evidência: SPECULATIVE. Gate digital: PASS. Decisão: OPEN.

O envelope permite manter a Arq.1 como opção tecnicamente plausível **somente nos dois cenários nominais de referência**, pois a disposição óptica comum permanece idêntica e afastada da correia nas duas cenas. Nenhum resultado prova compatibilidade com as máquinas reais ou libera fabricação. Não demonstra superioridade, menor custo, rigidez, repetibilidade ou fabricabilidade.

A: nominal 1500 × 190 mm; B: nominal 450 × 200 mm. A Large (1470 × 300 mm) e os extremos intervalares de B não foram validados. As posições ópticas de B foram transferidas como hipótese para A. Não foram modelados adaptadores, furos, datums, clamps nem caminhos de carga. A interface comum é apenas uma região abstrata acima das câmeras.

As dimensões ausentes de A continuam BLOCKED. Laterais e roletes de A são símbolos volumétricos derivados de side_clearance e motor_keepout; a espessura de exibição da correia reutiliza cable_bundle.height. Não representam espessuras, diâmetros ou superfícies reais. Em B, roletes são caixas de exclusão com o diâmetro nominal como extensão. Cada fórmula e fonte consta em components.json. A origem é sintética; o deslocamento entre cenas serve apenas à apresentação.

Há três câmeras, trigger, três regiões de iluminação, três ocupações locais de cabos, garrafa, laterais e exclusões em cada cena. Cabos não representam rotas verificadas. Garrafa toca nominalmente a correia como produto transportado. A região proibida da correia coincide intencionalmente com seu envelope. Nenhum elemento óptico toca a correia; isso não verifica um suporte, pois suporte estrutural não foi modelado. Não houve avaliação de campo de visão, foco, oclusão, curso do produto ou colisões de rotas completas.

Validação em processo separado: readback STEP e STL por componente, correspondência por bounds/volume com consumo de multiplicidade para correia/proibição coincidentes, sólidos válidos, valores finitos, malhas fechadas com volume positivo e orientação consistente, nomes das cenas, cobertura de todos os componentes e afastamento óptico da correia. Apenas união de vértices coincidentes no STL; sem reparo. Serialização: STEP 1e-5 mm e 1e-5 mm³; STL 0,1 mm e tesselação angular 0,1 rad. Esses valores não são precisão mecânica.

Bloqueios físicos: identificar A e B, medir interfaces de chassi, laterais, roletes/motor e regiões proibidas, levantar envelope e massa/CG do módulo, óptica e cabos reais; G0/M0/P1 e revisão humana seguem necessários. Próxima medição: caracterizar primeiro B, largura/comprimento efetivos, espessuras laterais, posição/extensão de motor/roletes e interfaces estruturais independentes da correia, com instrumento, método e repetição; depois A.

STEP: external archive only; the generated export is not part of this publication. STL separados destinam-se exclusivamente à inspeção digital. Manifest, readback, auditoria e SHA256SUMS acompanham a revisão. Hashes formam grafo sem ciclo: manifest referencia payloads; auditoria referencia manifest; SHA256SUMS cobre ambos e não inclui a si mesmo.

A tentativa inicial em ab-r01 falhou na serialização de booleano NumPy no JSON; seus arquivos foram preservados. Esta review02 corrige a serialização e contabiliza os volumes coincidentes da correia/proibição por multiplicidade.

## Bounds globais por componente (mm)

| Cena / componente | Mínimo [x,y,z] | Máximo [x,y,z] |
|---|---|---|
| CONVEYOR_A_REFERENCE__belt_nominal | [-750.0000001, -95.00000010000001, -20.000000100000005] | [750.0000001, 95.00000010000001, 1.0000000397205465e-07] |
| CONVEYOR_A_REFERENCE__forbidden_belt_support | [-750.0000001, -95.00000010000001, -20.000000100000005] | [750.0000001, 95.00000010000001, 1.0000000397205465e-07] |
| CONVEYOR_A_REFERENCE__generic_side_left | [-750.0000001000001, -175.00000010000002, -200.00000010000002] | [750.0000001000001, -94.99999989999998, 1.0000002842170943e-07] |
| CONVEYOR_A_REFERENCE__generic_side_right | [-750.0000001000001, 94.99999989999998, -200.00000010000002] | [750.0000001000001, 175.00000010000002, 1.0000002842170943e-07] |
| CONVEYOR_A_REFERENCE__roller_keepout_start | [-850.0000001000001, -95.00000010000002, -200.00000010000002] | [-649.9999998999999, 95.00000010000002, 1.0000002864289338e-07] |
| CONVEYOR_A_REFERENCE__roller_keepout_end | [649.9999998999999, -95.00000010000002, -200.00000010000002] | [850.0000001000001, 95.00000010000002, 1.0000002864289338e-07] |
| CONVEYOR_A_REFERENCE__motor_keepout | [-850.0000001000001, 174.99999989999995, -200.00000010000005] | [-649.9999998999999, 375.0000001000001, 1.0000005859285502e-07] |
| CONVEYOR_A_REFERENCE__bottle | [-30.0000001, -30.0000001, -1e-07] | [30.0000001, 30.0000001, 220.0000001] |
| CONVEYOR_A_REFERENCE__camera_top | [-30.0000001, -30.0000001, 279.9999999] | [30.0000001, 30.0000001, 320.0000001] |
| CONVEYOR_A_REFERENCE__cable_top | [-10.000000100000001, -10.000000100000001, 329.9999999] | [10.000000100000001, 10.000000100000001, 350.0000001] |
| CONVEYOR_A_REFERENCE__camera_left | [-30.0000001, -180.0000001, 99.9999999] | [30.0000001, -119.9999999, 140.0000001] |
| CONVEYOR_A_REFERENCE__cable_left | [-10.000000100000001, -160.0000001, 149.9999999] | [10.000000100000001, -139.9999999, 170.0000001] |
| CONVEYOR_A_REFERENCE__camera_right | [-30.0000001, 119.9999999, 99.9999999] | [30.0000001, 180.0000001, 140.0000001] |
| CONVEYOR_A_REFERENCE__cable_right | [-10.000000100000001, 139.9999999, 149.9999999] | [10.000000100000001, 160.0000001, 170.0000001] |
| CONVEYOR_A_REFERENCE__trigger | [-115.0000001, -15.0000001, 104.9999999] | [-84.9999999, 15.0000001, 135.0000001] |
| CONVEYOR_A_REFERENCE__lighting_top | [-150.0000001, 39.9999999, 294.9999999] | [150.0000001, 60.0000001, 305.0000001] |
| CONVEYOR_A_REFERENCE__lighting_left | [-10.000000100000001, -320.0000001, 114.9999999] | [10.000000100000001, -199.9999999, 125.0000001] |
| CONVEYOR_A_REFERENCE__lighting_right | [-10.000000100000001, 199.9999999, 114.9999999] | [10.000000100000001, 320.0000001, 125.0000001] |
| CONVEYOR_A_REFERENCE__common_optical_interface_ABSTRACT | [-150.0000001, -180.0000001, 369.9999999] | [150.0000001, 180.0000001, 390.0000001] |
| CONVEYOR_B_REFERENCE__belt_nominal | [-225.0000001, 1079.9999999, -4.0000001] | [225.0000001, 1280.0000001, 1.000000004440892e-07] |
| CONVEYOR_B_REFERENCE__forbidden_belt_support | [-225.0000001, 1079.9999999, -4.0000001] | [225.0000001, 1280.0000001, 1.000000004440892e-07] |
| CONVEYOR_B_REFERENCE__generic_side_left | [-225.0000001, 1075.9999999, -28.000000100000005] | [225.0000001, 1080.0000001, 1.0000000355271367e-07] |
| CONVEYOR_B_REFERENCE__generic_side_right | [-225.0000001, 1279.9999999, -28.000000100000005] | [225.0000001, 1284.0000001, 1.0000000355271367e-07] |
| CONVEYOR_B_REFERENCE__roller_keepout_start | [-239.0000001, 1079.9999999, -28.000000100000005] | [-210.9999999, 1280.0000001, 1.0000000355271367e-07] |
| CONVEYOR_B_REFERENCE__roller_keepout_end | [210.9999999, 1079.9999999, -28.000000100000005] | [239.0000001, 1280.0000001, 1.0000000355271367e-07] |
| CONVEYOR_B_REFERENCE__motor_keepout | [-275.0000001, 1283.9999999, -100.00000010000004] | [-174.99999989999998, 1384.0000001, 1.0000003177643716e-07] |
| CONVEYOR_B_REFERENCE__bottle | [-30.0000001, 1149.9999999, -1e-07] | [30.0000001, 1210.0000001, 220.0000001] |
| CONVEYOR_B_REFERENCE__camera_top | [-30.0000001, 1149.9999999, 279.9999999] | [30.0000001, 1210.0000001, 320.0000001] |
| CONVEYOR_B_REFERENCE__cable_top | [-10.000000100000001, 1169.9999999, 329.9999999] | [10.000000100000001, 1190.0000001, 350.0000001] |
| CONVEYOR_B_REFERENCE__camera_left | [-30.0000001, 999.9999999, 99.9999999] | [30.0000001, 1060.0000001, 140.0000001] |
| CONVEYOR_B_REFERENCE__cable_left | [-10.000000100000001, 1019.9999999, 149.9999999] | [10.000000100000001, 1040.0000001, 170.0000001] |
| CONVEYOR_B_REFERENCE__camera_right | [-30.0000001, 1299.9999999, 99.9999999] | [30.0000001, 1360.0000001, 140.0000001] |
| CONVEYOR_B_REFERENCE__cable_right | [-10.000000100000001, 1319.9999999, 149.9999999] | [10.000000100000001, 1340.0000001, 170.0000001] |
| CONVEYOR_B_REFERENCE__trigger | [-115.0000001, 1164.9999999, 104.9999999] | [-84.9999999, 1195.0000001, 135.0000001] |
| CONVEYOR_B_REFERENCE__lighting_top | [-150.0000001, 1219.9999999, 294.9999999] | [150.0000001, 1240.0000001, 305.0000001] |
| CONVEYOR_B_REFERENCE__lighting_left | [-10.000000100000001, 859.9999999, 114.9999999] | [10.000000100000001, 980.0000001, 125.0000001] |
| CONVEYOR_B_REFERENCE__lighting_right | [-10.000000100000001, 1379.9999999, 114.9999999] | [10.000000100000001, 1500.0000001, 125.0000001] |
| CONVEYOR_B_REFERENCE__common_optical_interface_ABSTRACT | [-150.0000001, 999.9999999, 369.9999999] | [150.0000001, 1360.0000001, 390.0000001] |
