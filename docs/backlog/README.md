# Backlog / expansão (fora do núcleo entregue)

Este diretório **não substitui** os artefatos originais: ele os **indexa e rotula**, preservando
histórico. Nada aqui foi movido ou apagado — os arquivos continuam nos caminhos originais.

Critério (decisão **D-22** — separação núcleo × evolutivo): o núcleo entregue na Entrega 1 é
**visibilidade e rastreabilidade** (sem atuação física, sem controle de velocidade da esteira,
sem encoder, multi-view sem cardinalidade fixa). Tudo que trata de **atuar, medir velocidade,
sincronizar fisicamente ou estroboscopia** é **expansão** — vale como análise e caminho futuro,
não como requisito do núcleo.

## Artefatos de expansão (mantidos nos locais originais)

| Artefato | Fase | Por que é expansão | Estado |
|---|---|---|---|
| `docs/requisitos/04-atuacao-seguranca.md` | F0 (08-31) | atuação/ejeção e segurança de atuador | expansão |
| `docs/requisitos/01-funcionais.md` (trechos de encoder KY-040, estroboscópica, retrorrefletiva, 3 câmeras) | F0→F2 | pressupõe controle de esteira e óptica de 3 câmeras | expansão (parcial) |
| `docs/pocs/03-sincronizacao-fisica/` | F0 | sincronização física com a esteira | expansão |
| `docs/pocs/07-atuacao-confirmada/` | F0 | atuação confirmada (o núcleo usa `07` = dashboard) | expansão |
| `docs/pocs/01-classificador-topo/`, `04-correlacao-multi-no/` | F0 | recorte de PoC diferente do entregue | ver `docs/pocs/MAPA.md` |
| `cad-produto/reports/OPTICAL-RIG-3CAM-*`, `R05-V7-3CAM-NOMINAL.md` | F0/F2 | preveem **3 câmeras**; a decisão vigente é 2 câmeras em ângulo obtuso | histórico + revisar decisão |
| D-11 / D-12 (detector evolutivo de anomalia) | F0 | escritos antes da evidência de *domain gap* (MVTec ≠ rig) | revisar |
| `docs/design/grip-extensivel.md` | F2 | extensão mecânica de bancada | expansão |

## O que o núcleo mantém

`docs/requisitos.md`, `docs/requisitos/02-nao-funcionais.md`, `docs/escopo.md`, `docs/arquitetura.md`,
`docs/dados-telemetria.md`, `docs/metodologia.md`, `latex-workspace/` (Entrega 1), `code-workspace/`.

## Regra de uso

- Citar um item de expansão no documento entregue **só** como "fora do escopo / evolução".
- Ao retomar expansão, rebaixar/migrar com o rótulo de estado, nunca apagando o original.
