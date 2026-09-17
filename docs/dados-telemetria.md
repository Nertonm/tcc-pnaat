# Dados e telemetria: estado implementado

A fonte canônica do contrato de dados é `src-production/esquema.sql`, consumida por `registro.py`,
`painel.py`, `consultas_site.py` e `api.py`. Este documento explica o que já está implementado e
separa as interfaces que continuam fora do núcleo.

## 1. Persistência implementada

O SQLite do produto contém, entre outras, estas tabelas:

| Tabela | Papel no produto | Fonte |
|---|---|---|
| `lote` | agrupamento de itens | `esquema.sql` |
| `ponto_linha` | identificação do ponto de captura | `esquema.sql` |
| `taxonomia_defeito` | classe, descrição, severidade e vista | `esquema.sql` |
| `item` | identidade, lote, trigger, status por domínio e status final | `esquema.sql`, `registro.py` |
| `inspecao_vista` | vista, domínio, qualidade, classe, confiança, evidência e latência | `esquema.sql`, `registro.py` |
| `evento_gatilho` | evento recebido do sensor ou de fonte declarada | `esquema.sql`, `registro.py` |
| `evidencia` | caminho, SHA-256, vista e origem da prova | `esquema.sql`, `registro.py` |
| `heartbeat_no` | estado, fila e latência de nós observados | `esquema.sql`, `painel.py` |
| `correcao_operador` | decisão original, correção, operador e horário | `esquema.sql`, `registro.py` |
| `evento_rejeicao` | estados de ordem/confirmação quando houver produtor de atuação | `esquema.sql`; sem atuador no núcleo |
| `descritor_geometrico` | descritores e score de anomalia quando produzidos | `esquema.sql`; camada OOD isolada |

`Registro.registrar()` grava item, vistas e evidências em transação. O mesmo `item_id` com a mesma
prova é reenvio idempotente; evidência divergente é conflito. Falha na gravação faz rollback.
`correcao_operador` não substitui `status_final`: a consulta deriva a decisão efetiva sem apagar o
valor original.

## 2. Regras de estado

- `defeito` vence quando qualquer domínio detecta defeito.
- Sem evidência necessária, o estado é `inconclusivo`, não `ok`.
- `erro_processamento` é distinto de defeito físico.
- Qualidade da captura (`completo`, parcial, timestamp divergente e evidência insuficiente) não é
  confundida com a classe do item.
- Consultas de leitura abrem o banco em modo read-only; `/api/health` é a exceção, pois pode criar o
  schema de um banco novo.

## 3. Consultas e consumidores implementados

As agregações de `painel.py` alimentam `/api/qualidade`, `/api/resumo`, `/api/lotes`, `/api/gatilhos`
e o site. Estão implementadas taxas por lote, defeitos por severidade, tendência temporal, saúde,
latência, correções, inconclusivos, saturação, gatilhos e discordância lateral. O frontend também
faz polling periódico enquanto está visível.

A evidência é servida por `/api/evidencia` somente quando o caminho registrado resolve dentro da raiz
de evidências e o arquivo é uma imagem permitida. Arquivo ausente, tipo inválido ou escape da raiz
vira erro HTTP explícito.

## 4. Interfaces do sistema

| Interface | Estado |
|---|---|
| trigger físico -> ponte serial -> câmera | implementada em `main.c`, `transport_bin.py` e `esp32cam_site.py`; a ligação elétrica e a instalação física exigem bancada |
| CSV/HTTP -> `evento_gatilho` | implementada; persiste apenas o evento, não substitui captura |
| serviço de rig/ponte -> gateway API | implementada por `PNAAT_RIG`, `PNAAT_PONTE` e `/api/rig/*` |
| série materializada -> ingestão | implementada em `ingerir_serie.py`, com `manifest.json`, mapa e artefato legado |
| captura materializada -> pacote YOLO -> decisão | implementada em `orquestracao.py` e `classificador_yolo.py` |
| SQLite -> painel/site | implementada em `painel.py`, `consultas_site.py` e `api.py` |
| correção -> trilha de operador | implementada e append-only |
| SQLite -> MQTT | não implementada no núcleo |
| SQLite -> ntfy | não implementada no núcleo |
| atuador -> confirmação física | schema e consultas existem; produtor e ensaio físico não existem no núcleo |
| encoder -> velocidade/throughput | coluna existe; produtor e ensaio não existem no núcleo |

## 5. O que não deve ser confundido

O schema modela estados de MQTT, atuação, heartbeat e geometria para preservar o contrato de dados,
mas a existência da coluna não prova que haja produtor operacional. Do mesmo modo, uma leitura de
health ou heartbeat prova o estado registrado, não a cobertura de todos os nós físicos.

A camada OOD/one-class existe como avaliação isolada e tem testes próprios. Ela não está integrada à
decisão normal do item nem deve ser apresentada como detector de produção.

## 6. Verificação

```bash
make -C src-production verificar
make -C src-production lint
```

A suíte do produto cobre registro, rollback, idempotência, API, painel, site, contrato, pacote,
qualidade e regras de decisão. O firmware tem suíte própria. A validação de hardware, MQTT, ntfy,
atuador, encoder e retenção depende de seus produtores e ensaios específicos.
