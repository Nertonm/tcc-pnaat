# _experimentos/: saida de experimento, entrada rejeitada, controle

Saida que nao virou dado. Serve para lembrar o que ja foi tentado e por que nao entrou.

- saidas de modelo (ex.: PatchCore) que nao foram promovidas;
- entradas rejeitadas na validacao de par (bbox/mascara/isolamento);
- controles: perturbacao conhecida que **nao** e defeito real, usada para provar reacao do modelo
  (ver `TRABALHO/` para o gerador).
- `_EXPERIMENTO-ABSTENCAO`, `_EXPERIMENTO-DOMINIO-*`, `_COMPARACAO-EXTRATORES`: registros de
  decisao com numero medido.

Nao versionado. Se um experimento virar dado, ele e promovido para `nosso/` ou `anotacao/` com
movimentacao registrada em `REORGANIZACAO-<data>.csv`.
