# Análise cronológica do projeto PNAAT (2026-09-11)

Reconstrução por evidência (git log com datas, mtimes de artefatos, D-01..D-22).
Objetivo: explicar por que existem incongruências e o que fazer com cada resíduo.

## Linha do tempo

| Fase | Datas | Evidência | Decisão central | Resíduo que ficou |
|---|---|---|---|---|
| **F0 — Escopo "rico"** | até **08-31** | `docs/requisitos/04-atuacao-seguranca.md` (mt 08-31 22:28) | atuação física, encoder KY-040, iluminação estroboscópica, barreira retrorrefletiva, **3 câmeras** | todo o `docs/requisitos/*` antigo + `docs/pocs/03-sincronizacao-fisica`, `07-atuacao-confirmada`, `04-correlacao-multi-no` |
| **F1 — Entrega 1 (pivô p/ visibilidade)** | **09-08 → 09-09** | `latex-workspace/main.tex` (09-09 22:21), `docs/requisitos.md` (09-09 20:39), `docs/pocs/*` (09-09 18:14) | sem atuação, sem encoder, foco em visibilidade/rastreabilidade; multi-view **sem fixar cardinalidade**; 30 RF / 21 RNF | PDF entregue enxuto × docs antigos intactos |
| **F2 — Rig/CAD + higiene** | **09-10** | commits CAD `9111dc6`→`ea9175f`, `c60a126` (revert), `5509065` (untrack mídia), `docs/DECISIONS.md` (09-10 21:12) | D-22 "separação núcleo × evolutivo"; rig R05 evolui (mount, DIN, **3CAM** nos reports) | mídia voltou ao git; `R05-V7-3CAM-NOMINAL.md` contradiz a decisão de **2 câmeras**; D-22 declarada mas **não executada** |
| **F3 — Ferramentas, modelo, dataset** | **09-10 → 09-11** | `a97c9bd` (classificador), `6dec91d` (validador), `ee19cb2` (preproc), `f849531` (auditoria) | pilotos one-class (PatchCore/PaDiM), preproc MVP, gate de isolamento, guardas | modelo ainda sem decisão formal; `defective=0`; venv duplo; notebooks não versionados |

## Pontos de virada (o que mudou e por quê)

1. **08-31 → 09-09: corte de escopo.** A "dor" passou de *atuar na esteira* para *dar visibilidade*.
   Tudo que era atuação/velocidade/estroboscopia virou **expansão** — mas os arquivos de F0 continuaram
   no lugar sem rótulo. É a origem da incongruência P1.1.
2. **09-09: sanitização do PDF.** O documento entregue foi limpo (sem encoder/atuação), enquanto
   `docs/` manteve a versão rica → **duas verdades** sobre o mesmo projeto.
3. **09-10: D-22 reconhece o problema** ("separação entre núcleo e requisitos evolutivos"), mas só
   declara; a execução (mover/rotular) ficou pendente.
4. **09-10: rig mudou de 3 → 2 câmeras** (proposta das duas em ângulo obtuso), o que **contradiz os
   reports CAD** (`OPTICAL-RIG-3CAM-*`, `R05-V7-3CAM-NOMINAL.md`) — incongruência viva, não só histórica.
5. **09-11: evidência de domínio.** O piloto one-class deu AUROC 1.0 no MVTec (top-down) e **todas as
   nossas frames ≈1.0** → provou *domain gap*. A decisão de modelo (D-11/D-12 "detector evolutivo")
   precisa ser reescrita com essa evidência; hoje o que temos é recomendação, não decisão.
6. **Padrão recorrente de mídia no git:** `5509065` (09-10) removeu mídia; em **09-11** um `.step`
   voltou ao git (pego pelo `doctor`). Conclusão: **disciplina manual não segura** — precisa de hook/CI.

## O que isso implica (ação por resíduo)

| Resíduo | Fase | Ação |
|---|---|---|
| `docs/requisitos/04-atuacao-seguranca.md`, trechos de encoder/estroboscopia/3 câmeras | F0 | mover para `docs/backlog/` com header "fora do escopo entregue" |
| `docs/pocs/{01-classificador-topo,03-sincronizacao-fisica,04-correlacao-multi-no,07-atuacao-confirmada}` | F0 | renomear/mapa de-para para os PoCs entregues |
| Reports CAD `*3CAM*` | F0/F2 | marcar como históricos e registrar a decisão vigente (2 câmeras obtusas) no `DECISIONS` |
| D-11/D-12 (detector evolutivo) | F0 | reescrever com a evidência do domain gap e o stack híbrido |
| Mídia entrando no git | F2→agora | hook `pre-commit` rodando `doctor` (mídia, root-owned, `.git` gravável) |
| Venv duplo (3.14/3.11) | F3 | unificar no 3.11 |
| Notebooks fora do git | F3 | scripts testados são canônicos; notebooks como conveniência (ou versioná-los) |
| `defective=0` / sem calibração mm | F3 | gerar patches → compor → gate → treinar; Charuco p/ RNF-14 |

## Leitura de conjunto

O projeto não está incoerente por descuido: ele **mudou de tese no meio do caminho** (de atuação para
observabilidade) e o repositório guarda as duas camadas. A correção certa não é apagar a camada antiga
(ela é evidência de análise e base de expansão), e sim **rotular a fronteira** núcleo × expansão,
**executar a D-22** e **automatizar a higiene** — porque o padrão de resíduo se repetiu em todas as fases.