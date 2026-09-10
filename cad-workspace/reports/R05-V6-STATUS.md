# R05 v6 — estado histórico (2 câmeras, Pi vertical)

> **Substituído para o escopo do TCC por R05 v7.** O requisito confirmado é
> três câmeras: `C_TOP` e `C_LEFT` Raspberry Pi CSI, além de `C_RIGHT`
> USB-C/UVC no lado oposto. Consultar `R05-V7-3CAM-NOMINAL.md` e o contrato
> `data/concepts/optical-rig-r05-contract.json`. Este arquivo preserva o
> registro da tentativa v6 de duas câmeras; não é a fonte de escopo atual.

Status: CONCEPT_REVISED / OPEN. Geometria estrutural construída no FreeCAD MCP; gates volumétricos finais pendentes (MCP travou em `common`).

## Escopo (confirmado pelo usuário)
- 2 CÂMERAS: C_TOP (tampa) + UMA C_SIDE (corpo). Nada de 2 laterais agora.
- Pi5 NA VERTICAL, ALTA na coluna (Z420-524) para alcançar C_TOP e C_SIDE com cabos curtos.
- Grip agnóstico (light-clamp ISC) + coluna modular impressa (Opção 1: macho/fêmea + M4 lateral).

## Estrutura vertical (contínua, todos os encaixes com overlap intencional)
grip(light-clamp Z-100..0) → adapter padrão → base sleeve(Z8-32) → mod1(Z20-127)→mod2(115-222)→mod3(210-317)→mod4(305-412) → case lower collar(400-445) → case top collar(505-552) → crossbar C_TOP(540-594)
+ C_SIDE + MOUNT_C_SIDE no mod2 (Z~146-158) apontando +Y ao corpo

## O que adicionei localmente (após Astra cortado por quota)
- MOUNT_C_SIDE (36x60x8 + braço 30x80x8) em mod2
- C_SIDE (25x24x12 placeholder CM3) no topo do braço, mirando a garrafa

## Gates verificado (bbox)
- Cadeia grip→adapter→sleeve→mods→collars→crossbar: todos os pares de junta têm bbox overlap (encaixe presente).
- Sem overlap espúrio com a garrafa/envelope.
- 44 objetos no FCStd `optical_rig_r05_column_v6.fcstd`.

## Pendências (sem mais quota Astra por ora)
- Interferência volumétrica REAL (Common/boolean) entre pares: MCP travou; usar leitura leve ou quando quota voltar.
- Encaixe macho/fêmea + M4 continuidade nas juntas (o Astra construiu JointM4_0..5 + nut envelopes).
- Canal FPC PROBE_20x10 presente; atravessar juntas a confirmar.
- Grip: melhorar fixação padrão 4-parafusos e alívio de torque (próximo foco).
- Refinamento: importar STEPs Pi5/CM3, backplates CM3 (Wide/Standard), janela óptica, cabos.

## Sobre "como as partes se juntam" (decisão)
Opção 1 acoplamento: ombro macho/fêmea + parafuso M4 LATERAL em cada junta. Alinhamento vem da geometria; o M4 só trava. Interface case-Pi vertical usa o mesmo padrão (boss M2.5 p/ placa + ombro p/ módulo). Grip trocável: adapter padrão 4 parafusos no pé.
