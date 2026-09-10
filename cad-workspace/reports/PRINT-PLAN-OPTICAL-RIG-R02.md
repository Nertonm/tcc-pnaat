# Plano de primeiro protótipo: optical-rig-r02

Status: PROTOTYPE_CONCEPT. A R02 pode ser impressa como protótipo de montagem com as dimensões assumidas no JSON. Não é liberação industrial.

## Lote 1: imprimir primeiro

| Peça | Qtde | Material | Observação |
|---|---:|---|---|
| receiver | 1 | PETG | usar parafusos/porcas M5; não carregar só pelo plástico |
| tongue | 1 | PETG | interface removível |
| cam_lever | 1 | PETG | pivô e arruela metálicos |
| captive_screw_keeper | 1 | PETG | parafuso cativo M5 |
| jaw_left/jaw_right | 2 de cada | PETG | mordentes intercambiáveis |
| mount_C_TOP/LEFT/RIGHT | 1 de cada | PETG | câmera não deve tocar lente/FPC |
| support_camera_module_3_C_* | 1 de cada | PETG | suporte do envelope oficial |
| cable_guide_00..08 | 1 de cada | PETG | prender com parafuso/abraçadeira macia |
| pi5_concept_case | 1 | PETG | deixar ventilação e acesso aos conectores |
| trigger_mount | 1 | PETG | E18 a montante |
| diagnostic_mount | 1 | PETG | VL53L0X, diagnóstico |
| ky040_mount | 1 | PETG | junto ao rolete |

## Lote 2: adapters

Imprimir apenas um por vez para escolha de bancada: `adapter_plate_A`, `adapter_plate_B` ou `adapter_plate_C`. Os três têm furos circulares, não slots oblongos, porque o `slot2D` do CadQuery 2.8.0 produziu STL não estanque. O arquivo STEP/STL atual foi reconstruído e passou no `validate_mesh.py`.

`base_clamp_lower`, `base_clamp_upper`, `saddle_foot_-1`, `saddle_foot_1` e `bench_plate` são variantes de acoplamento e não precisam ser impressos no primeiro lote se a placa de bancada C for usada.

## Hardware mínimo

- parafusos M5, porcas e arruelas largas;
- parafuso M5 cativo e arruela de retenção;
- parafuso/pino de pivô metálico para a came;
- inserts metálicos apenas onde houver ciclos repetidos;
- fita macia ou abraçadeira de velcro para cabos;
- MDF ou perfil para base e colunas;
- três suportes de iluminação ajustáveis.

Não usar zip tie apertado sobre FPC. A fixação do cabo fica no frame, com folga de serviço até o conector.

## Sequência

1. Imprimir o lote 1.
2. Fixar receiver em uma placa plana de MDF.
3. Montar tongue no frame óptico e testar inserção/remoção.
4. Instalar cam lever, parafuso cativo e retenção metálica.
5. Montar C_TOP, C_LEFT e C_RIGHT nos braços.
6. Posicionar Pi 5 na base, com ventilação livre.
7. Fixar guias e passar três rotas de cabo sem tensionar conectores.
8. Instalar E18 a montante, VL53L0X como diagnóstico e KY-040 no rolete.
9. Passar manualmente um volume de produto de 80x80x240 mm.
10. Ajustar altura, espaçamento e ângulos pelo JSON; gerar nova pasta ao alterar parâmetros.

## Gate executado

`validate_optical_rig_r02.py`: PASS_ASSUMPTION_DRIVEN. Todos os 38 STL da R02 devem passar `validate_mesh.py`; os adapters A/B/C foram revalidados após reconstrução. `sha256sum -c reports/OPTICAL-RIG-3CAM-R02.sha256`: todos OK.

A primeira impressão deve ser tratada como prova de montagem e ajuste, não como validação de carga, FOV, sincronização, cabo real ou repetibilidade industrial.
