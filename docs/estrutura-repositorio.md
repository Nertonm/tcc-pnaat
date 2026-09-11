# Estrutura e autoridade do repositorio

## Regra de autoridade

- `docs/` e a fonte normativa de requisitos, escopo, arquitetura, decisoes e PoCs.
- `latex-workspace/` e a fonte de publicacao do PDF. Divergencias com `docs/` devem ser resolvidas antes do PDF ser aceito.
- `cad-workspace/` e o namespace do pipeline mecanico: fontes CAD, canarios G0, scripts, design especifico e relatorios de referencia. Ele nao duplica a documentacao normativa.
- `evidencias/` versiona somente READMEs, templates, metadados e hashes. Fotos, videos, PDFs de instrumento, dumps e dados brutos ficam fora do Git por padrao.

## Estados

Metas nao sao resultados. Relatorios CAD devem preservar `reference_only`, `measured`, `fabrication_allowed`, `SPECULATIVE` e `BLOCKED` quando aplicavel. Um canario de schema nao valida geometria fisica nem autoriza fabricacao.

## Publicacao

Use staging por allowlist. Nao usar `git add -A` ou `git add .`. Antes de publicar, verificar links, IDs RF/RNF, manifest SHA-256, scan de sanitizacao, `git diff --check`, build LaTeX e validadores CAD disponiveis.

O clone CAD original e o archive de rollback ficam fora desta arvore publicada; este namespace contem somente a versao sanitizada candidata.
