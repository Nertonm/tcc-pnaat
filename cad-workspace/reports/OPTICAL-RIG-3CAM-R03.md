# Optical portal R03: contrato e arquitetura

Status: CONCEPT_CONTRACT. R02 foi REJECTED como arquitetura mecânico-óptica por perder o corredor aberto, datums XYZ, entidades de câmera, FOV e caminho de carga.

## Sistema global

- +X: direção de transporte downstream.
- +Y: transversal à esteira.
- +Z: para cima.
- `belt_plane_z = 0`.
- `inspection_plane_x = 0`.
- `product_center_y = 0`.

Não usar U/V/W como eixos globais.

## Contrato óptico

Envelope assumido do produto: 80 x 80 x 240 mm. C_TOP fica acima, mirando -Z, para tampa. C_LEFT e C_RIGHT ficam em lados opostos, mirando +Y e -Y, respectivamente, para corpo. Cada câmera tem entidade, mount, eixo óptico e cone FOV separados. O FOV é ilustrativo e não substitui calibração de lente.

## Arquitetura mecânica

O módulo é um pórtico aberto em X, com base, dois postes laterais em Y e travessa superior. A garrafa permanece visível e atravessável no corredor óptico. A Pi 5 fica na base. As luzes ficam próximas a cada vista, fora do eixo do produto. O caminho de carga é explícito: câmera -> mount -> poste/travessa -> base -> receiver -> tongue -> adapter -> estrutura de bancada/esteira.

O dock comum é receiver + tongue + retenção positiva. O adapter específico não é confundido com a estrutura óptica. O protótipo atual usa envelopes genéricos para a esteira e não afirma compatibilidade dimensional.

## Sensores e cabos

E18 fica upstream; VL53L0X é diagnóstico; KY-040 fica no rolete upstream. CSI_TOP, CSI_LEFT e USB_RIGHT são rotas independentes, representadas como corredores abertos presos ao frame. A escolha de cabo/conversor continua separada do envelope mecânico.

## Arquivos

- Contrato: `data/concepts/optical-rig-r03-contract.json`
- Gerador: `cad/cadquery/concepts/optical-rig-r03/rig.py`
- Assembly aberto: `exports/concepts/optical-rig-r03/optical-rig-r03-open-portal.step`
- Componentes: `exports/concepts/optical-rig-r03/components.json`
- Cena leve de inspeção: abrir o STEP acima no FreeCAD.
- MCP de referência: `references/vendor/qwen-mm-plugins/`, commit `3927a9582b5a8a4edb533e3212997149ca73e68c`.

## Critérios para a próxima revisão

1. A cena deve manter corredor aberto e envelope do produto visível.
2. C_TOP/C_LEFT/C_RIGHT devem ser identificáveis.
3. Cada eixo óptico deve ser independente e não colinear por erro de representação.
4. O frame deve usar somente XYZ global.
5. Câmera, mount, estrutura, receiver e adapter devem aparecer como cadeia separada.
6. Nenhum sólido maciço deve ocupar o volume óptico sem função explícita.
7. Alterações de posição devem vir do contrato, não de edição manual no STEP.

## Limites

As dimensões são hipóteses para visualização. O R03 ainda não valida FOV, foco, iluminação real, rigidez, carga, vibração, cabo, sincronização, impressão ou encaixe nas esteiras. O MCP foi baixado como referência isolada; não está registrado no catálogo desta sessão.
