# externo/: dado de terceiro, com credito

Politica do projeto: **credito e obrigatorio; licenca nao e gate**. Dado publico entra e e creditado
(nome do dataset, origem, URL, versao, licenca, contagens, digest) no `.proveniencia.json` de cada
fonte e listado aqui.

Fontes (5 exports Roboflow da mesma conta, versao raw, sem preprocess/augment):

| fonte | imagens |
|---|---|
| `bottle_cap_sdp-3v0vj-qzaan` | 3.554 |
| `original-zotc7-1j0kr` | 685 |
| `dataset-joren-newest-a4vuy` | 570 |
| `bottle-defect-detection-c6ts8` | 262 |
| `bottle-lte35-abhgw` | 103 |
| `ron88-defect-level` (Ron 88 Defect-Level) | 1.500 |

Nao versionado (`.gitignore`): e grande e nao e nosso. O que se versiona e este INDEX e o
`MAPA-CLASSES.md`, porque sao eles que provam a proveniencia.

Esperado de cada fonte: `data.yaml` proprio, `nc`, nomes de classe e split declarado. Fonte sem
proveniencia nao entra.
