# MAPA: PoCs dos docs × PoCs entregues (sem renomear nada)

Os diretórios originais ficam como estão (histórico preservado). Este mapa só traduz.

| Docs (original) | Entregue (Entrega 1 / código) | Observação |
|---|---|---|
| `01-classificador-topo` | **PoC-01: captura multi-view** | o docs focava topo; o entregue cobre abertura de janela por evento com mais de uma vista |
| `02-deformidade-lateral` | **PoC-03: deformidade lateral** | muda o número (02→03) |
| `03-sincronizacao-fisica` | **Expansão: calibração trigger → captura** (`code-workspace/src/pocs/expansao_sincronizacao/`, `code-workspace/scripts/calibrar_delay_trigger.py`) | sincronização física com a esteira saiu do núcleo; o código da expansão é `expansao_sincronizacao/`, sem número, para não colidir com a numeração entregue |
| `04-correlacao-multi-no` | **PoC-04: identidade e fusão** | multi-nó virou expansão; o núcleo funde vistas do mesmo item |
| `05-integracao-dados` | **PoC-05: registro local** | mesmo tema, nome diferente |
| `06-resiliencia` | **PoC-06: resiliência** | alinhado |
| `07-atuacao-confirmada` | **PoC-07: dashboard e visibilidade** | mudança de tese (atuação → observabilidade) |
| — | **PoC-02: classificação de tampa** | não existia no docs |
| — | **PoC-Final: conjectura integrada** | não existia no docs |

Código correspondente: `workspace/src/pocs/pocNN_*/` (01..08) + `pocfinal/`.


---

> **Armadilha de numeracao (verificada em 2026-09-11).** `docs/pocs/01-classificador-topo/README.md`
> descreve tampa ausente + mal rosqueada com matriz de confusao: isso e, no conteudo, a **PoC-02**
> entregue, nao a PoC-01. Citar a pasta pelo numero entrega a spec errada. Mesmo padrao:
> `02-deformidade-lateral/` e hoje a PoC-03 e `07-atuacao-confirmada/` nao e o dashboard.
> D-06, D-01, D-03, D-15, D-18, D-20 e D-21 ainda apontam para a numeracao antiga.

Regra: ao citar o PDF (números entregues), usar a coluna da direita; para arqueologia/análise,
usar a coluna da esquerda.
