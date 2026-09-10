# FreeCAD: práticas e projetos de referência para o TCC

Status: REFERENCE_INGEST. Esta nota é base de engenharia, não especificação final.

## Fontes primárias

- FreeCAD oficial: https://github.com/FreeCAD/FreeCAD
- Assembly Workbench: https://wiki.freecad.org/Assembly_Workbench
- PartDesign: https://wiki.freecad.org/PartDesign_Workbench
- Spreadsheet: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Spreadsheet_Workbench.md
- Expressions: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Expressions.md
- TechDraw: https://wiki.freecad.org/TechDraw_Workbench
- Fasteners: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Fasteners_Workbench.md

## Padrões assimilados

1. Assembly separado da definição de cada peça. Usar um documento de conjunto com componentes importados, placements e joints; não transformar um STEP monolítico em fonte paramétrica.
2. Cada peça carregada deve ter um sólido contínuo quando a intenção for imprimir. Validar `isValid`, número de sólidos, watertight, volume e bounds antes de exportar.
3. Parâmetros devem existir em um único lugar, com unidades e aliases. O Spreadsheet/Expressions é a prática FreeCAD para propagar dimensões e evitar números duplicados.
4. Usar PartDesign/Body para peças que precisam de histórico editável e Part/CSG para envelopes e geometrias auxiliares. Bodies não devem esconder múltiplos sólidos acidentais.
5. Juntas devem eliminar graus de liberdade uma vez. Fixar a base, usar rigid groups para conjuntos rígidos e revolute/slider somente onde o movimento é real. Evitar sobreconstrained assembly.
6. Separar referência, mockup e peça fabricável. Modelos oficiais de placa/câmera entram como reference bodies; não reexportar nem misturar com peças autorais.
7. Fasteners e BOM devem representar hardware real quando a união depende de parafuso, porca, arruela ou inserto. A rosca visual completa é desnecessária para o primeiro protótipo.
8. TechDraw só depois da geometria estabilizar. Gerar vistas, seções e cotas diretamente do modelo, nunca dimensionar a partir da imagem raster.
9. Cada componente deve ter nome estável, função, material, orientação de impressão, fixadores e fonte. A árvore deve comunicar a montagem.

## Projetos semelhantes

### felipe-m/freecad_filter_stage
https://github.com/felipe-m/freecad_filter_stage

Projeto OSH com estágio óptico parametrizado. Padrões úteis: scripts FreeCAD/CadQuery separados, peças imprimíveis separadas de perfis, motores, correia e guias não imprimíveis, parâmetros documentados, imagens de montagem, BOM de ferragens e orientação de impressão sem suporte. Licenças declaradas: hardware CERN-OHL-1.2, software LGPL-3.0, documentação CC BY 4.0.

Aplicação: manter base/pórtico/MDF e perfis como componentes de cena, separar mounts/dock/cable guides como peças imprimíveis e documentar ferragens fora do STL.

### openUC2/UC2-GIT
https://github.com/openUC2/UC2-GIT/tree/master/CAD

Sistema modular de óptica com blocos, placas, módulos de câmera e configurações completas. Padrões úteis: interface repetível, módulos intercambiáveis, setups compostos, tutoriais por módulo, BOM separado e histórico de versões. O projeto combina peças impressas, ferragens e componentes comerciais.

Aplicação: tratar receiver/tongue como interface comum e adapters A/B/C como módulos específicos. A posição das câmeras deve ser recalável sem alterar o dock.

### FreeCAD Fasteners Workbench
https://github.com/shaise/FreeCAD_FastenersWB

Workbench externo para adicionar e anexar ferragens a furos circulares. Padrão útil: o furo circular é a interface de referência mais simples; o fastener pode ser ligado à geometria e gerar BOM.

Aplicação: a R02 usa furos circulares nos adapters. Isso foi deliberado depois de `slot2D` gerar STL não estanque no CadQuery 2.8.0.

### FreeCAD camera-mount
https://github.com/lud77/camera-mount

Exemplo de suporte de câmera com estrutura ajustável e projeto FreeCAD; o próprio README registra a limitação de depender da desmontagem de uma câmera específica. Padrão útil: não chamar um mount de universal quando o envelope e a carcaça não foram confirmados.

Aplicação: nossos mounts usam o envelope oficial Camera Module 3 e deixam C_RIGHT substituível por câmera USB de envelope equivalente, sem inventar modelo do conversor.

## Decisão para o TCC

A base adequada não é um único arquivo FreeCAD rígido. É:

```text
parameters.json
  ↓
parametric source (CadQuery/FreeCAD)
  ↓
per-part STEP/STL
  ↓
assembly scene STEP
  ↓
TechDraw/overview/BOM
```

O R02 deve evoluir para um FCStd editável com Spreadsheet de parâmetros, App::Part por subsistema e uma Assembly contendo: `Frame`, `OpticalDock`, `Camera_TOP`, `Camera_LEFT`, `Camera_RIGHT`, `Lighting`, `Trigger`, `Encoder`, `Pi5` e `ProductEnvelope`.

O frame principal pode continuar MDF/perfil. O FreeCAD deve modelar o envelope e as interfaces; não é necessário imprimir o pórtico inteiro.

## Regra de impressão

Imprimir primeiro somente as interfaces e suportes: receiver, tongue, came, mordentes, mounts das três câmeras, guias de cabo, bandeja Pi e suportes de sensores. Usar metal nos caminhos de carga. Orientação, walls, infill e tolerância permanecem parâmetros do processo, não garantias do material.

## Limites

As fontes externas orientam processo e arquitetura. Não comprovam encaixe na nossa esteira, resistência, FOV, cabo, sincronização ou desempenho. Os repositórios semelhantes não foram incorporados ao código do TCC; os links acima são a proveniência para consulta.
