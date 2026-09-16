# R05: Composição com modelos reais (progresso)

Status: REAL_MODELS_COMPOSED. Arquitetura Pi=haste, coluna modular, usando modelos existentes (não caixas).

## Modelos reais usados (todos em references/vendor/)
| Elemento | Modelo | Licença | Pode usar como base? |
|---|---|---|---|
| Case Pi5 | pipiece/case.stl (104.8×65.4×33.1) | ISC | SIM (base da coluna) |
| Housing câmera | pipiece/cam top/bottom | ISC | SIM (referência de housing) |
| Grip/Clamp | light-clamp/body.stl + clamp.stl (38×25×100; 19×25×50) | ISC | SIM (ancora na esteira) |
| Mount câmera | pi-camera-mounts (STL + FCStd parametr.) | GPL-2.0 | SIM (cinemática pan M5/tilt M4/backplate M2.5; trocar backplate p/ CM3) |

## Assembly resultante
- exports/concepts/optical-rig-r05/r05-full-real-assembly.stl (1.9MB): case + grip + 3 mounts posicionados.
- exports/concepts/optical-rig-r05/r05-full-real-assembly.png: render isométrico.
- Documento FreeCAD R05Refs: PIPIECE_CASE, PIPIECE_CAM_TOP/BOT, LIGHTCLAMP_BODY/CLAMP, PICAMMOUNT_BOTTOM, MOUNT_C_TOP/LEFT/RIGHT.

## Posições (contrato)
- C_TOP: mount no topo (Z~430) mirando -Z.
- C_LEFT/C_RIGHT: mounts laterais (Z~150) mirando ±Y.
- Case na base; grip por baixo na esteira.

## Pendências
1. Backplate CM3 em cada mount: substituir backplate GS/HQ do pi-camera-mounts pelo STEP oficial do CM3.
2. Janela óptica por variante (Wide p/ C_TOP, Standard p/ laterais).
3. Módulos superior da coluna com encaixe macho/fêmea + M4 + canal FPC.
4. Spreadsheet Params; gates de corredor/encaixe.
