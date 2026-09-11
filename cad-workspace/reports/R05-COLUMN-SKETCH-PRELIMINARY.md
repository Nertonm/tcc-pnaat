# R05 — Esboço da coluna modular "Pi=Haste" (draft local CadQuery)

Status: DRAFT_LOCAL (gerado por (fora do repo) via CadQuery 2.8, sem depender do Astra/quota).
Fonte primária do design: `reports/R05-COLUNA-MODULAR-DESIGN.md` + `data/concepts/optical-rig-r05-contract.json`.
Não é peça final: é esboço conceitual parametrizável. Não valida FOV/carga/safety.

## Arquivo
`exports/concepts/optical-rig-r05/optical-rig-r05-column-draft.step` (278 KB, sha256 777e181...)

## O que o esboço contém (17 primitivos)
| Grupo | Peças | Nota |
|---|---|---|
| Produto | PRODUCT_ENVELOPE (H370/D120) | garrafa no corredor, X=0 |
| Clamp | CLAMP_TOP, CLAMP_JAW_L/R | C-clamp M6/M8 (primitivo) |
| Base | COLUMN_BASE (4-bolt) | recebe módulo 1 |
| Pi | PI5_BASE_MODULE + PI5_BOARD_REF | Pi na base (CG baixo) |
| Coluna | COLUMN_MODULE_2, _3, COLUMN_TOP | módulos empilháveis, canal FPC |
| Câmeras | C_TOP_WIDE + mount no topo; C_LEFT/C_RIGHT_STANDARD + mounts na coluna | Wide topo, Standard laterais |
| Backlight | BACKLIGHT_RESERVED (painel fino atrás) | espaço reservado, Y>0 |

## Coordenadas (contrato)
+X transporte, +Y transversal, +Z cima. Coluna fica em X≈60 / Y≈-120 (LATERAL, não oclui backlight Y>0).
Garrafa H370/D120 em X≈0. C_TOP no topo ~Z430. Laterais na coluna ~Z150 (altura do corpo).

## Como ele relaciona os modelos (composição)
- Pi5 e CM3: referência dimensional (esboço usa primitivos; STEPs oficiais prontos para import no próximo passo).
- pi-camera-mounts (FCStd, GPL): a cinemática base/swivel/tilt será trazida no refinamento.
- pcb-enclosure-generator: lógica de encaixe modular (não copiada aqui, só primitivo).
- pipiece: inspiração de topologia (SEM licença, não copiar).

## Próximos passos (quando quota Astra voltar / ou via MCP FreeCAD)
1. Importar STEPs oficiais Pi5 + CM3 como reference bodies.
2. Transformar primitivos em peças com: ombro de encaixe macho/fêmea + pinos + M4, canal FPC contínuo.
3. Backplates CM3 a partir do STEP oficial (Wide vs Standard), janela por variante.
4. Encaixar cinemática do pi-camera-mounts nos mounts.
5. Spreadsheet Parameters com aliases; gates de corredor/encaixe.
