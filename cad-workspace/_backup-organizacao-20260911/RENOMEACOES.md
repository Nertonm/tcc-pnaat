# Renomeacoes e movimentos de 2026-09-11

Script: `cad_org_phase2_organizar.py` (executado como nerton). Nenhum `git add/commit/push/merge/revert/reset`, nenhum `git clean`, nenhuma remocao de arquivo.

## Diretorios renomeados (`mv`, nao `git mv`)

| nome antigo | nome novo |
|---|---|
| `candidate-audit-20260911T052357Z` | `auditoria-r07-20260911T052357Z` |
| `structural-candidate-20260911T053435Z` | `base-estrutura-20260911T053435Z` |
| `stage0-reference-review-20260911T032253Z` | `stage0-referencias-20260911T032253Z` |
| `stage1-references-20260911` | `stage1-referencias-20260911` |

Motivo do carimbo: os diretorios nao sao rastreados pelo git (`git ls-files cad-workspace/<dir>` = 0 arquivos em todos os quatro), entao a operacao correta e `mv`, nao `git mv`. O sufixo de tempo foi mantido porque carrega a ordem de geracao entre estagios do mesmo dia e torna a operacao reversivel.

## Movidos (nao apagados)

- `exports/concepts/optical-rig-r05/camera-mount-din-v1-interferencia.step`
  -> `exports/concepts/optical-rig-r05/_diagnostico/camera-mount-din-v1-interferencia.step`

## Copiados (originais intactos)

- `reports/R05-CAMERA-MOUNT-DIN.md` -> `exports/concepts/optical-rig-r05/LAUDO-camera-mount-din-v6.md`
  (sha256 do original: `495bfb5e4f314a634a8ff0d6758e47b6118a712872b68c64950bf8acac3bc4bb`)

## Adicionados

- `INDICE.md` (raiz do workspace)
- `exports/concepts/optical-rig-r06-estrutura/REPROVADO.md`
- `exports/concepts/optical-rig-r07-estrutura/REPROVADO.md`
- `exports/concepts/optical-rig-r05/_diagnostico/LEIA-ME.md`
- `_backup-organizacao-20260911/*` (manifesto, baseline, tar.gz)
