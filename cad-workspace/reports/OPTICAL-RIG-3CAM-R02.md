# PNAAT optical rig R02: protótipo agnóstico

Status: ASSUMPTION_DRIVEN. Classe: PROTOTYPE_CONCEPT. `prototype_print_allowed=true`; `production_release=false`; `measured=false`.

## Objetivo

Esboço imprimível de uma estação óptica com três vistas: C_TOP para tampa, C_LEFT e C_RIGHT para corpo e deformidade. A Raspberry Pi 5 fica na base. O frame óptico usa estrutura MDF/perfil e ferragens; FDM fica restrito a mounts, guias, bandeja, dock e protetores.

## Interface comum

O conjunto usa receiver + tongue, dois datums, batente anti-rotação, furos oblongos e trava por came com parafuso cativo M5. A retenção não depende apenas de atrito. Adapters A, B e C representam clamp lateral, saddle/base e placa de bancada; os três compartilham o receiver. As cotas dos adapters são hipóteses, não encaixe confirmado em esteira real.

## Disposição

- C_TOP: Camera Module 3 standard, vista superior.
- C_LEFT: Camera Module 3 wide, vista lateral esquerda.
- C_RIGHT: envelope Camera Module 3 standard substituível por módulo USB/UVC de volume equivalente.
- Dois canais CSI são conceituais para C_TOP/C_LEFT; a terceira rota é USB/UVC conceitual. Conversor não selecionado.
- E18 a montante no trigger_mount.
- VL53L0X em diagnostic_mount, como diagnóstico/PoC.
- KY-040 em ky040_mount junto ao rolete, fora do pórtico óptico.
- Três envelopes de iluminação acompanham as vistas.
- Guias de cabo e standoffs percorrem o frame; FPC não é preso pelo conector.

## Parâmetros assumidos

`camera_spacing=400 mm`, `working_distance=180 mm`, `product_envelope=80x80x240 mm`, `top_height=420 mm`, `dock_width=140 mm`, `cable_length=2200 mm`, `bend_radius=25 mm`, base `450x680x18 mm`, ferragens M5, PETG, quatro paredes, 30-50% infill nos mounts. O modelo é parametrizado em `data/concepts/optical-rig-r02.json`.

## Arquivos

- Gerador: `cad/cadquery/concepts/optical-rig-r02/rig.py`
- Cena: `cad/cadquery/concepts/optical-rig-r02/view_scene.py`
- Configuração: `data/concepts/optical-rig-r02.json`
- Exportações: `exports/concepts/optical-rig-r02/`
- Validator: `scripts/validate_optical_rig_r02.py`
- Prancha: `exports/concepts/optical-rig-r02/overview.pdf` e `.png`

## Montagem inicial

Imprimir primeiro receiver, tongue, cam_lever, jaw_left/right, um mount de cada vista, três cable guides, pi5_concept_case, trigger_mount, diagnostic_mount e ky040_mount. Usar porcas/parafusos/inserts metálicos nas interfaces carregadas. Montar sobre placa plana assumida, posicionar envelopes oficiais e passar um gabarito de produto. Ajustar somente parâmetros do JSON e gerar uma nova pasta de saída; não sobrescrever R01/R02.

## Nota de exportação dos adapters

Os adapters A/B/C foram reconstruídos como placas com furos circulares. O `slot2D` do CadQuery 2.8.0 produziu STL não estanque neste caso; por isso os oblongos foram removidos da R02. Os três STEP/STL atuais passaram o `validate_mesh.py`.

## Limites

Este R02 não valida resistência, foco, FOV, sincronização CSI/USB, raio admissível do cabo real, aquecimento da Pi, vibração, segurança, carga, furos ou encaixe nas duas esteiras. Os modelos oficiais são referências preservadas em `references/vendor/raspberry-pi`; não foram reexportados. O R02 deixa de usar o G0 físico como requisito de geração, mas não converte hipótese em medição.
