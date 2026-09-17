# anotacao/: o julgamento humano, nao a imagem

Este diretorio guarda **anotacao**. A imagem de origem continua em `nosso/` ou `externo/`; o que se
preserva aqui e o que a equipe decidiu sobre ela.

- `ls/` export do Label Studio no schema canonico (`anotacoes-ls.csv`, 22 colunas;
  `anotacoes-por-imagem.csv`; `imagens/`; `MANIFEST.sha256`). Ver `ls/README.md`.
- `deteccao_tampa/` labels YOLO `nc=3` convertidos do export, para treino de detector.
- `revisao-auto/` rotulos **automaticos** (triagem), nunca confundir com anotacao humana.

Nao versionado, com excecao deste README. O ciclo completo (capturar -> importar -> anotar ->
exportar -> compor -> medir) esta em `../README.md`, secao "A pratica incremental".
