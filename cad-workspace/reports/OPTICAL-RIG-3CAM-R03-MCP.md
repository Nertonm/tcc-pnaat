# Optical rig R03 — pórtico aberto via MCP

Status: conceito geométrico editável; não liberado para fabricação.

Documento real: `OpticalRigR03OpenPortal`. Contagem confirmada por `get_objects`: **195 objetos**, incluindo origens automáticas, parâmetros, referências e TechDraw.

FCStd: `exports/concepts/optical-rig-r03/optical-rig-r03-open-portal.fcstd`.

## Reconstrução e comparação com R02

A rejeição do usuário foi arquitetural: a estação precisava funcionar como pórtico aberto, sem parede/placa no corredor óptico. O R03 foi criado do zero no FreeCAD real pelo MCP qwen-mm-plugins-freecad. Nenhum gerador CadQuery foi usado para o documento. R01/R02 não foram sobrescritos.

| Rejeição / requisito | Solução R03 |
|---|---|
| Parede no corredor | Dois postes de 30 × 30 mm em X=90, Y=±180; travessa em Z=460–490; base horizontal abaixo da correia |
| Câmeras pouco identificáveis | C_TOP/C_LEFT/C_RIGHT como App::Part, corpos verdes, lentes, eixos e cones amarelos transparentes; legendas na cena |
| Produto/corredor ilegível | Produto 80 × 80 × 240 em wireframe ciano, Z=0; envelope de transporte separado e oculto |
| Pi e cabos no corredor | Bandeja lateral na base e três rotas roxas independentes |
| Interface confundida com parede | DOCK laranja na borda negativa de Y; adapter, receiver, tongue, shoulder, came excêntrico, pivô M5 e alavanca separados |

O contrato local anterior mencionava base 600 × 520 e altura de poste 430 mm. Nesta reconstrução foram adotados 600 × 640 mm e topo de poste Z=460 mm para acomodar os envelopes e o suporte superior. São hipóteses construtivas, não medidas de esteira. A base ocupa Z=-60 a -42 mm; o plano de correia é apenas referência em Z=0.

## Parâmetros nativos

`Parameters` é Spreadsheet::Sheet com unidades e aliases. Produto, posições de câmeras, postes, base e abertura dos cones têm expressões nativas. Mounts, sensores, iluminação e rotas têm dimensões/posições editáveis, mas não todos dependem da planilha; mudanças dimensionais exigem nova revisão desses componentes.

| Alias | Valor |
|---|---|
| ProductX | 80.0 mm |
| ProductY | 80.0 mm |
| ProductZ | 240.0 mm |
| BeltZ | 0.0 mm |
| InspectionX | 0.0 mm |
| CenterY | 0.0 mm |
| TopZ | 420.0 mm |
| SideY | 230.0 mm |
| SideZ | 150.0 mm |
| PostY | 180.0 mm |
| PostX | 90.0 mm |
| PostTop | 460.0 mm |
| BaseX | 600.0 mm |
| BaseY | 640.0 mm |
| BaseT | 18.0 mm |
| PiX | 170.0 mm |
| PiY | 240.0 mm |
| TriggerX | -200 mm |
| RollerX | -270 mm |
| IllustrativeFOV | 55.0 deg |

+X transporte downstream; +Y transversal; +Z cima. Inspection plane X=0 e centerline Y=0. Origens de câmera representam o vértice óptico ilustrativo; corpos ficam atrás da lente.

## Verificação geométrica

Resultados calculados no FreeCAD via MCP, usando transformações globais e envelope de transporte X=[-300,300], Y=[-40,40], Z=[0,240]:

```json
{
  "FRAME_sweep_overlap_mm3": 0.0,
  "PI5_sweep_overlap_mm3": 0.0,
  "SENSORS_sweep_overlap_mm3": 0.0,
  "DOCK_sweep_overlap_mm3": 0.0,
  "cable_distance_to_sweep_mm": {
    "C_TOP_CABLE_ROUTE_TO_PI": 165.0,
    "C_LEFT_CABLE_ROUTE_TO_PI": 20.0,
    "C_RIGHT_CABLE_ROUTE_TO_PI": 220.0
  },
  "frame_axis_intersections": {
    "C_TOP": 0,
    "C_LEFT": 0,
    "C_RIGHT": 0
  },
  "camera_contract": {
    "C_TOP": {
      "position": [
        0.0,
        0.0,
        420.0
      ],
      "axis": [
        0.0,
        0.0,
        -1.0
      ]
    },
    "C_LEFT": {
      "position": [
        0.0,
        -230.0,
        150.0
      ],
      "axis": [
        0.0,
        1.0,
        0.0
      ]
    },
    "C_RIGHT": {
      "position": [
        0.0,
        230.0,
        150.0
      ],
      "axis": [
        0.0,
        -1.0,
        0.0
      ]
    }
  },
  "invalid_shapes": [],
  "document": "OpticalRigR03OpenPortal",
  "object_count": 195
}
```

Volume de interferência zero não exclui contato tangente, nem valida movimento, fixação ou montagem. Os testes de eixos cobrem FRAME, não uma calibração/oclusão integral de todos os raios do FOV. O came representa retenção positiva por bloqueio do ombro da tongue; curso de abertura, tolerâncias, folgas e ferragens permanecem conceituais. Cabos são centerlines, sem seção nem raio de curvatura validado.

## Evidência de vistas e inspeção negativa

- [Isométrica padrão](../exports/concepts/optical-rig-r03/isometric.png).
- [Frontal padrão FreeCAD, plano XZ](../exports/concepts/optical-rig-r03/front.png).
- [Frontal do pórtico, olhando ao longo de X, plano YZ](../exports/concepts/optical-rig-r03/front-inspection-x.png).
- [Superior](../exports/concepts/optical-rig-r03/top.png).
- [FRAME oculto, frontal do pórtico](../exports/concepts/optical-rig-r03/negative-frame-hidden.png).

A vista Right do FreeCAD corresponde à frontal mecânica do pórtico neste contrato. A inspeção negativa manteve produto, três câmeras, eixos e cones legíveis com FRAME oculto. FRAME foi restaurado antes do salvamento. Na isométrica padrão os postes sobrepõem parcialmente algumas legendas; a vista frontal do pórtico e a inspeção negativa separam a óptica claramente.

Página TechDraw `R03_Views` com template A4 e vistas nativas `FRONT_INSPECTION_X`, `TOP_Z`, `ISOMETRIC`. Não é prancha cotada de fabricação. Screenshots são a evidência visual principal.

## Readback MCP

`list_documents`, `get_objects`, `get_object(C_LEFT)` e `get_view(Isometric)` executados após salvar. `get_view(Right)` também executado com FRAME oculto. Retornos textuais preservados em [mcp-readback.json](../exports/concepts/optical-rig-r03/mcp-readback.json); geometria e árvore em [validation.json](../exports/concepts/optical-rig-r03/validation.json) e [object-tree.json](../exports/concepts/optical-rig-r03/object-tree.json).

A biblioteca opcional de peças retornou FileNotFoundError para parts_library; a conexão com o FreeCAD permaneceu operacional. Foram usadas create_document, create_object, execute_code, get_objects, get_object e get_view. Importação STEP realizada dentro do FreeCAD por execute_code, sem substituição das operações CAD por shell.

## Fontes e licença

- Geometria principal: primitivas nativas e envelopes simplificados criados nesta tarefa a partir do contrato do usuário e `data/concepts/optical-rig-r03-contract.json`.
- Câmera de referência: `references/vendor/raspberry-pi/camera-module-3/step/Camera_module_3_std_model_simple.stp`, importada via MCP/Part.read, preservada oculta em `Camera3_VENDOR_STEP_REFERENCE` (590 sólidos). Licença da câmera não estabelecida nesta sessão; não se atribui MIT automaticamente a esse arquivo.
- Pi 5: `references/vendor/raspberry-pi/pi5/step/rpi-5b_no_graphics.step`, importado via MCP/Import.insert durante o trabalho; sua extensa árvore de montagem foi removida do documento final. A Pi final é envelope simplificado identificado, com fonte original preservada no workspace.
- Licença da fonte Pi 5: MIT, Copyright (c) 2026 Raspberry Pi Ltd, texto completo em `references/vendor/raspberry-pi/pi5/step/LICENSE.txt`, incluindo ausência de garantia dimensional.

Não há alegação de validação física, calibração FOV, foco, cobertura integral do produto, carga, resistência, segurança, dissipação, sincronização, compatibilidade elétrica ou encaixe em esteira real. FOV 55° é hipótese ilustrativa. Sem commit/push.

## Árvore completa de objetos

Lista incluindo objetos automáticos do FreeCAD; Group explicita as relações de agrupamento.

| Nome | Tipo | Filhos Group |
|---|---|---|
| Parameters | Spreadsheet::Sheet |  |
| DATUMS | App::Part | AXIS_X_DOWNSTREAM, AXIS_Y_TRANSVERSE, AXIS_Z_UP, INSPECTION_PLANE_X0, BELT_PLANE_Z0 |
| Origin | App::Origin |  |
| X_Axis | App::Line |  |
| Y_Axis | App::Line |  |
| Z_Axis | App::Line |  |
| XY_Plane | App::Plane |  |
| XZ_Plane | App::Plane |  |
| YZ_Plane | App::Plane |  |
| Origin001 | App::Point |  |
| PRODUCT_ENVELOPE | App::Part | Product_80x80x240_OPEN |
| Origin002 | App::Origin |  |
| X_Axis001 | App::Line |  |
| Y_Axis001 | App::Line |  |
| Z_Axis001 | App::Line |  |
| XY_Plane001 | App::Plane |  |
| XZ_Plane001 | App::Plane |  |
| YZ_Plane001 | App::Plane |  |
| Origin003 | App::Point |  |
| FRAME | App::Part | BaseBelowBelt, Post_Left, Foot_Left, CameraArm_Left, ArmTie_Left, Post_Right, Foot_Right, CameraArm_Right, ArmTie_Right, CrossbarAboveProduct, TopCameraCantilever |
| Origin004 | App::Origin |  |
| X_Axis002 | App::Line |  |
| Y_Axis002 | App::Line |  |
| Z_Axis002 | App::Line |  |
| XY_Plane002 | App::Plane |  |
| XZ_Plane002 | App::Plane |  |
| YZ_Plane002 | App::Plane |  |
| Origin005 | App::Point |  |
| OPTICS | App::Part | C_TOP, C_LEFT, C_RIGHT, Text, Text001, Text002 |
| Origin006 | App::Origin |  |
| X_Axis003 | App::Line |  |
| Y_Axis003 | App::Line |  |
| Z_Axis003 | App::Line |  |
| XY_Plane003 | App::Plane |  |
| XZ_Plane003 | App::Plane |  |
| YZ_Plane003 | App::Plane |  |
| Origin007 | App::Point |  |
| LIGHTING | App::Part | C_TOP_LightOuter, C_TOP_LightOpening, C_TOP_LIGHTING_ENVELOPE, C_LEFT_LightOuter, C_LEFT_LightOpening, C_LEFT_LIGHTING_ENVELOPE, C_RIGHT_LightOuter, C_RIGHT_LightOpening, C_RIGHT_LIGHTING_ENVELOPE |
| Origin008 | App::Origin |  |
| X_Axis004 | App::Line |  |
| Y_Axis004 | App::Line |  |
| Z_Axis004 | App::Line |  |
| XY_Plane004 | App::Plane |  |
| XZ_Plane004 | App::Plane |  |
| YZ_Plane004 | App::Plane |  |
| Origin009 | App::Point |  |
| SENSORS | App::Part | E18_SeparateTriggerArm, E18_TriggerArmPost, E18_UPSTREAM_TRIGGER, VL53L0X_DIAGNOSTIC, VL53_DiagnosticArm, VL53_DiagnosticPost, UPSTREAM_ROLLER_REFERENCE, KY040_UPSTREAM_ROLLER, KY040_RollerCoupling |
| Origin010 | App::Origin |  |
| X_Axis005 | App::Line |  |
| Y_Axis005 | App::Line |  |
| Z_Axis005 | App::Line |  |
| XY_Plane005 | App::Plane |  |
| XZ_Plane005 | App::Plane |  |
| YZ_Plane005 | App::Plane |  |
| Origin011 | App::Point |  |
| CABLES | App::Part | C_TOP_CABLE_ROUTE_TO_PI, C_LEFT_CABLE_ROUTE_TO_PI, C_RIGHT_CABLE_ROUTE_TO_PI |
| Origin012 | App::Origin |  |
| X_Axis006 | App::Line |  |
| Y_Axis006 | App::Line |  |
| Z_Axis006 | App::Line |  |
| XY_Plane006 | App::Plane |  |
| XZ_Plane006 | App::Plane |  |
| YZ_Plane006 | App::Plane |  |
| Origin013 | App::Point |  |
| PI5 | App::Part | Pi5TrayOutsideSweep, Pi5_SIMPLIFIED_REFERENCE, Pi5PortsEnvelope, PiStandoff_165_238, PiStandoff_165_282, PiStandoff_235_238, PiStandoff_235_282 |
| Origin014 | App::Origin |  |
| X_Axis007 | App::Line |  |
| Y_Axis007 | App::Line |  |
| Z_Axis007 | App::Line |  |
| XY_Plane007 | App::Plane |  |
| XZ_Plane007 | App::Plane |  |
| YZ_Plane007 | App::Plane |  |
| Origin015 | App::Point |  |
| DOCK | App::Part | AdapterSeparateBaseInterface, ReceiverFloor, ReceiverRailLeft, ReceiverRailRight, TongueSlidingInsert, TonguePositiveShoulder, ReceiverHardStop, CaptiveM5CamPivot, EccentricCamPositiveRetention, CamLever |
| Origin016 | App::Origin |  |
| X_Axis008 | App::Line |  |
| Y_Axis008 | App::Line |  |
| Z_Axis008 | App::Line |  |
| XY_Plane008 | App::Plane |  |
| XZ_Plane008 | App::Plane |  |
| YZ_Plane008 | App::Plane |  |
| Origin017 | App::Point |  |
| EXCLUSIONS | App::Part | ProductSweep_EXCLUSION, Camera3_VENDOR_STEP_REFERENCE |
| Origin018 | App::Origin |  |
| X_Axis009 | App::Line |  |
| Y_Axis009 | App::Line |  |
| Z_Axis009 | App::Line |  |
| XY_Plane009 | App::Plane |  |
| XZ_Plane009 | App::Plane |  |
| YZ_Plane009 | App::Plane |  |
| Origin019 | App::Point |  |
| BaseBelowBelt | Part::Box |  |
| Post_Left | Part::Box |  |
| Foot_Left | Part::Box |  |
| CameraArm_Left | Part::Box |  |
| ArmTie_Left | Part::Box |  |
| Post_Right | Part::Box |  |
| Foot_Right | Part::Box |  |
| CameraArm_Right | Part::Box |  |
| ArmTie_Right | Part::Box |  |
| CrossbarAboveProduct | Part::Box |  |
| TopCameraCantilever | Part::Box |  |
| Product_80x80x240_OPEN | Part::Box |  |
| AXIS_X_DOWNSTREAM | Part::Feature |  |
| AXIS_Y_TRANSVERSE | Part::Feature |  |
| AXIS_Z_UP | Part::Feature |  |
| INSPECTION_PLANE_X0 | Part::Feature |  |
| BELT_PLANE_Z0 | Part::Feature |  |
| C_TOP | App::Part | C_TOP_BODY, C_TOP_LENS, C_TOP_FOV_ILLUSTRATIVE, C_TOP_OPTICAL_AXIS |
| Origin020 | App::Origin |  |
| X_Axis010 | App::Line |  |
| Y_Axis010 | App::Line |  |
| Z_Axis010 | App::Line |  |
| XY_Plane010 | App::Plane |  |
| XZ_Plane010 | App::Plane |  |
| YZ_Plane010 | App::Plane |  |
| Origin021 | App::Point |  |
| C_TOP_BODY | Part::Box |  |
| C_TOP_LENS | Part::Cylinder |  |
| C_TOP_FOV_ILLUSTRATIVE | Part::Cone |  |
| C_TOP_OPTICAL_AXIS | Part::Line |  |
| C_TOP_LightOuter | Part::Cylinder |  |
| C_TOP_LightOpening | Part::Cylinder |  |
| C_TOP_LIGHTING_ENVELOPE | Part::Cut |  |
| C_LEFT | App::Part | C_LEFT_BODY, C_LEFT_LENS, C_LEFT_FOV_ILLUSTRATIVE, C_LEFT_OPTICAL_AXIS |
| Origin022 | App::Origin |  |
| X_Axis011 | App::Line |  |
| Y_Axis011 | App::Line |  |
| Z_Axis011 | App::Line |  |
| XY_Plane011 | App::Plane |  |
| XZ_Plane011 | App::Plane |  |
| YZ_Plane011 | App::Plane |  |
| Origin023 | App::Point |  |
| C_LEFT_BODY | Part::Box |  |
| C_LEFT_LENS | Part::Cylinder |  |
| C_LEFT_FOV_ILLUSTRATIVE | Part::Cone |  |
| C_LEFT_OPTICAL_AXIS | Part::Line |  |
| C_LEFT_LightOuter | Part::Cylinder |  |
| C_LEFT_LightOpening | Part::Cylinder |  |
| C_LEFT_LIGHTING_ENVELOPE | Part::Cut |  |
| C_RIGHT | App::Part | C_RIGHT_BODY, C_RIGHT_LENS, C_RIGHT_FOV_ILLUSTRATIVE, C_RIGHT_OPTICAL_AXIS |
| Origin024 | App::Origin |  |
| X_Axis012 | App::Line |  |
| Y_Axis012 | App::Line |  |
| Z_Axis012 | App::Line |  |
| XY_Plane012 | App::Plane |  |
| XZ_Plane012 | App::Plane |  |
| YZ_Plane012 | App::Plane |  |
| Origin025 | App::Point |  |
| C_RIGHT_BODY | Part::Box |  |
| C_RIGHT_LENS | Part::Cylinder |  |
| C_RIGHT_FOV_ILLUSTRATIVE | Part::Cone |  |
| C_RIGHT_OPTICAL_AXIS | Part::Line |  |
| C_RIGHT_LightOuter | Part::Cylinder |  |
| C_RIGHT_LightOpening | Part::Cylinder |  |
| C_RIGHT_LIGHTING_ENVELOPE | Part::Cut |  |
| Pi5TrayOutsideSweep | Part::Box |  |
| Pi5_SIMPLIFIED_REFERENCE | Part::Box |  |
| Pi5PortsEnvelope | Part::Box |  |
| PiStandoff_165_238 | Part::Cylinder |  |
| PiStandoff_165_282 | Part::Cylinder |  |
| PiStandoff_235_238 | Part::Cylinder |  |
| PiStandoff_235_282 | Part::Cylinder |  |
| E18_SeparateTriggerArm | Part::Box |  |
| E18_TriggerArmPost | Part::Box |  |
| E18_UPSTREAM_TRIGGER | Part::Cylinder |  |
| VL53L0X_DIAGNOSTIC | Part::Box |  |
| VL53_DiagnosticArm | Part::Box |  |
| VL53_DiagnosticPost | Part::Box |  |
| UPSTREAM_ROLLER_REFERENCE | Part::Cylinder |  |
| KY040_UPSTREAM_ROLLER | Part::Box |  |
| KY040_RollerCoupling | Part::Cylinder |  |
| C_TOP_CABLE_ROUTE_TO_PI | Part::Feature |  |
| C_LEFT_CABLE_ROUTE_TO_PI | Part::Feature |  |
| C_RIGHT_CABLE_ROUTE_TO_PI | Part::Feature |  |
| AdapterSeparateBaseInterface | Part::Box |  |
| ReceiverFloor | Part::Box |  |
| ReceiverRailLeft | Part::Box |  |
| ReceiverRailRight | Part::Box |  |
| TongueSlidingInsert | Part::Box |  |
| TonguePositiveShoulder | Part::Box |  |
| ReceiverHardStop | Part::Box |  |
| CaptiveM5CamPivot | Part::Cylinder |  |
| EccentricCamPositiveRetention | Part::Cylinder |  |
| CamLever | Part::Box |  |
| ProductSweep_EXCLUSION | Part::Box |  |
| Camera3_VENDOR_STEP_REFERENCE | Part::Feature |  |
| Text | App::FeaturePython |  |
| Text001 | App::FeaturePython |  |
| Text002 | App::FeaturePython |  |
| R03_Views | TechDraw::DrawPage |  |
| FRONT_INSPECTION_X | TechDraw::DrawViewPart |  |
| R03_Template | TechDraw::DrawSVGTemplate |  |
| TOP_Z | TechDraw::DrawViewPart |  |
| ISOMETRIC | TechDraw::DrawViewPart |  |
