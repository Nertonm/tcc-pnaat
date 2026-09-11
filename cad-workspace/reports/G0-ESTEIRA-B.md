# Coleta G0 física - Esteira B

Pacote `template-r01`, preparado para a coleta no workspace CAD. Estado do pacote: preenchível e verificado por teste negativo. Estado da evidência física: `BLOCKED`. Gates de coleta P0/M0/P1: `INCOMPLETE`. Decisão de arquitetura: `OPEN`.

Nenhum dado físico foi preenchido. O próximo artefato operacional é `data/g0/esteira-b-g0-template.yaml`, acompanhado do checklist de campo. Identificadores de formulário, nomes dos campos e versão de schema são metadados, não medições. `measured: false`, `reference_only: false` e `fabrication_allowed: false`. Um formulário vazio para coleta física não é um conjunto de medidas nem um envelope de referência.

O mock-up r03 foi informado no pedido como `PASS_REFERENCE_ONLY`; esse resultado não foi reexecutado nesta tarefa. Ele não representa dimensões da máquina real e não deve alimentar chassi, furos, datums, cargas ou calibração. Valores comerciais e o canário também não são medição física.

## Uso em campo

Preservar o template e criar uma revisão de coleta quando a visita ocorrer. O padrão local é `esteira-b-g0-r01.yaml`, desde que o caminho ainda não exista. Registrar data, responsável, sessão, máquina e catálogo de fotos/arquivos com SHA-256. Preencher cada registro com valor, unidade, instrumento, método, leituras brutas, repetições, incerteza, limitações e IDs de provenance. Dados desconhecidos permanecem `null` e `BLOCKED`; nunca converter ausência em zero.

`raw_readings` guarda uma cópia completa da estrutura de `value` por repetição, na unidade declarada. Vetores usam XYZ; limites são pares mínimo/máximo XYZ, um par por objeto. Identificar objetos, pontos e ordem das listas no método e nas fotos. Medidas dimensionais não devem ser escondidas em texto. Observações qualitativas usam `unit: not_applicable` e justificativa em `uncertainty.basis`. Uma ausência verificada pode ser descrita em texto; dimensões inexistentes continuam bloqueadas para o gate dependente, até revisão humana da aplicabilidade do schema. Não preencher dimensões fictícias para obter PASS.

`REFERENCE` identifica origem de referência neste schema de coleta; não é um novo estado de evidência do workspace policy. `MEASURED` exige leitura física rastreável; `DERIVED` exige equação e IDs de fontes diretamente `MEASURED`, válidas; `BLOCKED` preserva a lacuna. Um registro derivado usa `measured: false`; o indicador global `measured: true` declara a existência da coleta física de origem. `READY`, `INCOMPLETE`, `PASS`, `FAIL` pertencem ao eixo de gate; seleção de arquitetura pertence ao eixo de decisão.

## Dados necessários por etapa

Os documentos lidos não definem formalmente P0. Neste pacote, P0 é somente uma proposta de agrupamento da coleta inicial para revisão humana; não altera gates existentes nem concede liberação mecânica.

| Etapa | Evidência necessária para encaminhar a revisão |
|---|---|
| P0, agrupamento proposto | Identificação física e fabricante/modelo verificáveis, fotos/provenance, unidades de comprimento, XYZ/origem recuperáveis, dimensões do chassi, interfaces fixas, inventário de furos, correia e zonas móveis/proibidas, instrumentos e anomalias. |
| M0, candidato geométrico | P0 mais geometria das interfaces, materiais verificados e espessuras, acesso a fixadores, centros/diâmetros de furos, candidatos A/B/C, limites das zonas proibidas, envelopes das três câmeras, iluminação, cabos, trigger, encoder e retenção conceitual. Aprovação humana de datums, interfaces e caminho de carga continua necessária. |
| P1, avaliação posterior | Configuração de carga, massas/CG de dummy e hardware, velocidade real, partida/frenagem, tracking, vibração, temperatura, relação encoder/deslocamento e slip; depois critérios e ensaios de carga, rigidez, repetibilidade, retenção, folgas/tolerâncias, material/processo e revisão mecânica. |

As dependências de dados estão fixadas no validador: P0 afeta P0/M0/P1; M0 afeta M0/P1; P1 afeta somente P1. Um teste confirma que a ausência isolada de temperatura conserva P0/M0 como `READY` no schema. Massa/CG não libera estrutura por estar preenchida, e a falta desses dados não impede documentar um envelope geométrico sem carga. Campos de identificação, integridade e provenance comuns são pré-requisitos globais.

`PASS_G0_COLLECTION_SCHEMA` significa apenas completude formal do pacote. O validador não aprova fabricação, não mede arquivos/fotos, não verifica a equação numericamente, não garante resistência, veracidade das leituras ou suficiência das incertezas. Os hashes das evidências são verificados quanto a formato e IDs; a comparação com os bytes originais deve ocorrer de modo independente na revisão de campo. P1 não fica liberado mecanicamente por `READY` no schema.

Correia não é interface estrutural. Encoder é independente do datum óptico; atuador tem estrutura própria. Não há autorização de datum crítico, trava ou retenção plástica. A proposta antiga de grip ajustável nos documentos históricos não substitui as restrições atuais do workspace policy.

## Execução e validação

| Comando/verificação | Exit code | Resultado |
|---|---:|---|
| `PYTHONPYCACHEPREFIX=ambiente temporario/g0-collection-pycache python3 -m py_compile scripts/validate_g0_real.py` | 0 | Sintaxe válida; cache fora do workspace. |
| `python3 scripts/validate_g0_real.py data/g0/esteira-b-g0-template.yaml` com Python do sistema | 1 | Falha de ambiente: `ModuleNotFoundError: yaml`. Não é sucesso do teste negativo. |
| `PATH="$PWD/.venv/bin:$PATH" python3 scripts/validate_g0_real.py data/g0/esteira-b-g0-template.yaml` | 1 | `BLOCKED_G0_INCOMPLETE`: teste negativo esperado. |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python ambiente temporario/g0-collection-checks.py` | 0 | 31 testes por subprocessos; validação independente do preenchimento e da preservação do YAML. |
| `.venv/bin/python scripts/validate_g0_real.py data/g0/esteira-b-g0-template.yaml` | 1 | Releitura para este relatório; bloqueio esperado confirmado. |

Usar o Python do venv, que possui PyYAML 6.0.3. Nenhuma dependência foi instalada. Controles sintéticos de teste existiram apenas em memória/arquivos temporários em `ambiente temporario`; não foram usados como G0 nem como dimensões CAD.

### Bloqueadores do template vazio

O relatório JSON do validador identifica 228 bloqueadores, cada um com campo, motivo e gates afetados. Não houve erro de parser nessa execução. Eles incluem:

- Declaração de coleta e estado global ainda não medidos.
- Unidades globais, provenance de sessão e catálogo de fotos/SHA-256 ausentes.
- Todos os 51 registros de coleta com estado `BLOCKED`, valor/unidade nulos e conflito ainda não verificado.
- Metadados de instrumento, método, repetição e incerteza permanecem nulos; passar a `MEASURED` exige preenchê-los e anexar provenance.

### Resultados independentes

| Caso | Exit code esperado e observado | Resultado |
|---|---:|---|
| empty physical template | 1 | BLOCKED_G0_INCOMPLETE |
| synthetic complete schema control | 0 | PASS_G0_COLLECTION_SCHEMA |
| missing global units | 1 | BLOCKED_G0_INCOMPLETE |
| dimension without unit | 1 | BLOCKED_G0_INCOMPLETE |
| null essential | 1 | BLOCKED_G0_INCOMPLETE |
| measured missing instrument | 1 | BLOCKED_G0_INCOMPLETE |
| measured missing method | 1 | BLOCKED_G0_INCOMPLETE |
| measured missing provenance_ids | 1 | BLOCKED_G0_INCOMPLETE |
| measured missing repetitions | 1 | BLOCKED_G0_INCOMPLETE |
| measured missing raw_readings | 1 | BLOCKED_G0_INCOMPLETE |
| measured missing uncertainty | 1 | BLOCKED_G0_INCOMPLETE |
| measured missing limitations | 1 | BLOCKED_G0_INCOMPLETE |
| fabrication forbidden | 1 | BLOCKED_G0_INCOMPLETE |
| top reference | 1 | BLOCKED_G0_INCOMPLETE |
| malformed state | 1 | BLOCKED_G0_INCOMPLETE |
| nonfinite number | 1 | BLOCKED_G0_INCOMPLETE |
| boolean quantity | 1 | BLOCKED_G0_INCOMPLETE |
| dimension encoded as text | 1 | BLOCKED_G0_INCOMPLETE |
| hash missing | 1 | BLOCKED_G0_INCOMPLETE |
| missing provenance collector | 1 | BLOCKED_G0_INCOMPLETE |
| unresolved conflict | 1 | BLOCKED_G0_INCOMPLETE |
| state REFERENCE | 1 | BLOCKED_G0_INCOMPLETE |
| state BLOCKED | 1 | BLOCKED_G0_INCOMPLETE |
| traceable derived control | 0 | PASS_G0_COLLECTION_SCHEMA |
| derived invalid source propagation | 1 | BLOCKED_G0_INCOMPLETE |
| derived missing equation and sources | 1 | BLOCKED_G0_INCOMPLETE |
| P1-only missing record | 1 | BLOCKED_G0_INCOMPLETE |
| invalid syntax | 1 | BLOCKED_G0_INCOMPLETE |
| duplicate keys | 1 | BLOCKED_G0_INCOMPLETE |
| root list | 1 | BLOCKED_G0_INCOMPLETE |
| unsafe tag | 1 | BLOCKED_G0_INCOMPLETE |

## Escopo e auditoria

Foram preparados somente os artefatos de coleta e validacao incluidos neste pacote. A revisao compara os arquivos publicados e seus hashes; insumos e resultados temporarios nao fazem parte da publicacao.

A evidencia fisica permanece BLOCKED. Nenhum dado sintetico ou envelope de referencia autoriza dimensionamento, fabricacao ou conclusao sobre a maquina real.

## Manifest e provenance do pacote

Autor: equipe do projeto; data de preparação: 2026-09-08; revisão: template-r01. Este manifest é de preparação de formulário, separado da proveniência física ainda nula.

| Artefato | SHA-256 dos bytes |
|---|---|
| `data/g0/esteira-b-g0-template.yaml` | `a99d36d5c77f7b7191edfa34ea6494e315e954ab22defd9317e5d6eb31acd92e` |
| `data/g0/esteira-b-g0-checklist.md` | `2b832b3d95fc77b26315cb636827518b33b4b29fdc668c764487f8349ba833fa` |
| `scripts/validate_g0_real.py` | `10a9f7e0dac82796eb561d0b0ecfdc644740f864b185d3c93b66477121e6673e` |
| `reports/G0-ESTEIRA-B.md` | Ver digest canônico abaixo; hash integral registrado na auditoria final da execução. |

Evidências temporárias da verificação nesta sessão:

| Arquivo | SHA-256 |
|---|---|
| `ambiente temporario/g0-collection-baseline.json` | `fdc5497f8a31b05476de437751a7f8ef504b0503392a46113d37a3d19ad75a2a` |
| `ambiente temporario/g0-collection-checks.py` | `1c42fb156db54b0903c619f0f0f7be85ddb38cf7c166e8ab89569275cc54138e` |
| `ambiente temporario/g0-collection-checks.json` | `f3ebe40c1d6309a655498a6b47991b7df15127eb3287e473e35e00c7f377b617` |

Para evitar hash circular e um quinto arquivo, este relatório registra SHA-256 canônico: substituir somente os 64 caracteres na linha `REPORT_CANONICAL_SHA256` por 64 zeros, mantendo todos os demais bytes UTF-8, e calcular SHA-256. O hash integral dos quatro arquivos será registrado na saída da auditoria final; não confundir o digest canônico com hash integral.

REPORT_CANONICAL_SHA256: a156a032cc52f9de3c4ed1d09a46a8fe0a387e5b4f76f3b8f5f5d1030a192b42

Próxima medição: identificar o exemplar físico da Esteira B, registrar fotos gerais e etiquetas, definir XYZ/origem recuperável e medir chassi/interfaces fixas com instrumento e incerteza documentados. Nenhum CAD real foi gerado.
