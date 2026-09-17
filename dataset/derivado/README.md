# derivado/: saida reproduzivel, nao entrada

Nada aqui e fonte. Tudo aqui e **reconstruivel** a partir de `nosso/` e `externo/` por um script
nomeado em `TRABALHO/`. Se um dia nao der para reconstruir, o problema e o script, nao o dado.

| caminho | o que e | como refazer |
|---|---|---|
| `classify224/` | recortes 224x224 na nossa taxonomia | `TRABALHO/` (preprocessamento + recorte) |

Nao versionado de proposito (`.gitignore`): e grande, e nao e nosso nem cru. O que se versiona e o
script e a contagem, nunca o recorte.
