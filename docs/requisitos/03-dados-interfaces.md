# Dados, interfaces e rastreabilidade

Estas fichas definem e detalham os contratos DAT-01..08 e IF-01..07, referenciados pelos RF/RNF de `../requisitos.md`. Parte dos contratos já está implementada no produto em `src-production/`; a ficha continua normativa e não substitui a prova do código. O estado implementado e as fronteiras externas estão resumidos em `../dados-telemetria.md`.

## Dados

### DAT-01: Identidade e registro do item

- Entrada: lote, data, sequência, trigger e ponto.
- Contrato: `item_id` estável no formato definido, timestamp com fuso, lote e status final.
- Critério de reprovação: registro sem ID, lote ou timestamp deve ser rejeitado ou marcado parcial.
- Verificação: schema, fixture inválido e consulta de leitura. Dependências: RF-06/07.

### DAT-02: Registro por vista

- Entrada: resultado de topo/lateral, confiança, evidência e latência.
- Contrato: cada vista mantém origem e vínculo ao item.
- Critério de reprovação: serializar e desserializar não pode perder vista, score ou evidência.
- Verificação: round-trip e query. Dependências: RF-01..04.

### DAT-03: Qualidade do registro

- Entrada: vista faltante, timestamp divergente ou evento completo.
- Contrato: `completo`, `parcial_1_vista_faltante` e `timestamp_divergente` são estados distintos.
- Critério de reprovação: dado degradado apresentado como normal.
- Verificação: três fixtures e propagação até dashboard/relatório. Dependências: RF-07/22.

### DAT-04: Genealogia de decisão

- Entrada: item, decisão original, correção, operador e horário.
- Contrato: correção adiciona evento e não sobrescreve o original.
- Critério de reprovação: update destrutivo apaga decisão original.
- Verificação: consulta de auditoria. Dependências: RF-12, STK-01.

### DAT-05: Isolamento de golden samples

- Entrada: amostra marcada `is_golden`.
- Contrato: amostra participa da demo e é excluída de FPY/KPIs produtivos.
- Critério de reprovação: golden aparece em taxa de defeito do lote.
- Verificação: query produtiva e query de demo. Dependências: RF-16, ACT-09.

### DAT-06: Taxonomia de defeitos

- Entrada: classificação e severidade.
- Contrato: defeito físico e `ERRO_PROCESSAMENTO` não são a mesma categoria.
- Critério de reprovação: falha de câmera contabilizada como defeito da garrafa.
- Verificação: taxonomia versionada e agregação por severidade. Dependências: RF-05.

### DAT-07: Payload MQTT

- Entrada: evento de visão, sensor, heartbeat ou atuação.
- Contrato mínimo: versão, `event_id`, `item_id` quando aplicável, nó, timestamp, tipo, payload e qualidade.
- Critério de reprovação: payload sem versão ou ID não pode ser deduplicado/diagnosticado.
- Verificação: JSON Schema, fixtures e replay. Dependências: IF-03/04.

### DAT-08: Evidência recuperável

- Entrada: imagem, vídeo, sensor ou log.
- Contrato: caminho/identificador, hash quando aplicável, item, vista e data.
- Critério de reprovação: registro aponta para caminho privado inexistente ou arquivo mutável sem hash.
- Verificação: manifest e leitura do artefato. Dependências: DOC-04, RF-06.

## Interfaces

### IF-01: Trigger para captura

- Entrada:  sinal do E18-D80NK (sensor IR difuso, active-low), com VL53L0X como validação/fallback correlacionado.
- Contrato: uma borda do trigger inicia a janela das três vistas.
- Critério de reprovação: uma câmera fora da janela deve ser identificada como faltante.
- Verificação: osciloscópio/log e três timestamps. Dependências:  RF-01, RF-01.1, HW-01.

### IF-02: Encoder para contagem

- Entrada: pulsos KY-040.
- Contrato: velocidade/contagem associadas ao item e ao trigger.
- Critério de reprovação: contagem desconectada não pode produzir throughput válido.
- Verificação: pulsos conhecidos versus cálculo. Dependências: RF-10.

### IF-03: Visão para MQTT

- Entrada: resultado por vista e decisão final.
- Contrato: payload versionado, com status e qualidade.
- Critério de reprovação: consumidor antigo deve rejeitar ou diagnosticar versão incompatível.
- Verificação: fixture de produtor e consumidor. Dependências: DAT-07.

### IF-04: MQTT para SQLite

- Entrada: mensagens novas, duplicadas, atrasadas e replay.
- Contrato: persistência transacional e upsert idempotente.
- Critério de reprovação: reconexão duplica evento ou perde evento confirmado.
- Verificação: ensaio de queda/replay. Dependências: RNF-05/06.

### IF-05: SQLite para dashboard

- Entrada: queries do estado atual.
- Contrato: dashboard lê o schema canônico, sem banco paralelo.
- Critério de reprovação: dashboard mostra estado diferente da query direta.
- Verificação: snapshot de query e tela com mesmo `item_id`. Dependências: RF-09.

### IF-06: Hub para ntfy

- Entrada: defeito crítico e falha crítica de atuação.
- Contrato: notificação contém item, severidade, estado e horário.
- Critério de reprovação: evento crítico persistido sem notificação ou com mensagem sem vínculo.
- Verificação: payload enviado, resposta e recebimento. Dependências: RF-09, ACT-10.

### IF-07: Atuador para confirmação

- Entrada: ordem e sensor E18-D80NK/VL53L0X.
- Contrato: ordem, movimento e confirmação são estados distintos.
- Critério de reprovação: remover sensor deve produzir `falha`, nunca `confirmada`.
- Verificação: evento_rejeicao e ensaio físico. Dependências: ACT-01..10.
