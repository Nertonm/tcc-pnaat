# nosso/: a evidencia do projeto (versionado)

E o unico bloco de imagem que entra no git, por decisao do grupo: e o dado que o projeto produziu,
e sem ele a conclusao nao e auditavel.

- `rig/` 81 frames 640x480 da bancada, garrafas **normais** (o rotulo foi corrigido de `defective`
  para `normal`; a versao antiga esta em `_copias/rig-rotulado-bad-81/`).
- `tampa/` 43: 9 `deformidade_frame_*` (normais na tampa, decisao D-28), 14 `tampa_ausente_frame*`,
  20 `tampa_mal_rosqueada_frame_*`.
- campanhas do rig entram como `nosso/<campanha>/`, so as que viraram evidencia anotada.

Regras: nome = `classe_frameNNNN.jpg`, minisculas, snake_case, sem acento. Teto de 2 MiB por arquivo
(politica de midia). Todo arquivo aqui tem sha256 em `../MANIFEST.sha256`, e o manifesto e conferido
no gate (`sha256sum -c`).
