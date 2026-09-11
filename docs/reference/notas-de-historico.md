# Notas de histórico (sem reescrita)

Histórico preservado por decisão de projeto: **não reescrevemos commits nem apagamos artefatos**.
Quando algo ficou inconsistente, registramos aqui em vez de reescrever o passado.

## Correções de rótulo de commit

| Commit | Rótulo declarado | Conteúdo real | Correção |
|---|---|---|---|
| `80df6e9` | `fix(guards): doctor, testes do gate, ...` | untrack de `cad-workspace/exports/.../camera-mount-din-v6.step` (128.749 linhas removidas) | rótulo incorreto; o conteúdo é `chore(repo): untrack export .step`. Este commit **não** contém os guards — eles estão em `cd54d98`. |

Convenção a partir de agora: um commit = uma intenção; mensagem descreve o conteúdo real.

## Camadas históricas do projeto (ver auditoria e análise cronológica)

- **F0 (até 08-31):** escopo com atuação — preservado como expansão e rotulado em `docs/backlog/README.md`.
- **F1 (09-08/09):** Entrega 1 (visibilidade) — documento entregue em `latex-workspace/`.
- **F2 (09-10):** rig/CAD + higiene; D-22 declarada.
- **F3 (09-10/11):** ferramentas, preproc, dataset, guardas.

Documentos relacionados: `docs/reference/auditoria-projeto-2026-09-11.md`,
`docs/reference/analise-cronologica-2026-09-11.md`, `docs/reference/runbook-erros-e-guardas.md`.