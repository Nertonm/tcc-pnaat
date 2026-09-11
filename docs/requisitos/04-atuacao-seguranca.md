> **Estado: EXPANSÃO** — documento da fase F0 (escopo com atuação). O núcleo entregue é
> visibilidade/rastreabilidade. Conteúdo preservado por histórico.

# Atuação, controlabilidade e segurança operacional

Estas fichas detalham os requisitos de atuação e segurança operacional. Atuação confirmada significa movimento físico observado e confirmação recebida; comando emitido sozinho não é sucesso.

### ACT-01: Ordem de atuação observável

- Entrada: `item_id`, status defeito e severidade.
- Contrato: registrar atuador, origem, timestamp, `attempt_id` e tentativa.
- Critério de reprovação: ordem existente apenas em log textual ou sem item vinculado.
- Verificação: tabela/evento consultável. Dependências: RF-14, DAT-07.

### ACT-02: Estados de rejeição separados

- Entrada: ordem, sensor e relógio.
- Contrato: `pendente`, `confirmada` e `falha`, com timestamps ordenado/confirmado.
- Critério de reprovação: ordem sem sensor produzir `confirmada`.
- Verificação: fixture de cada transição. Dependências: IF-07.

### ACT-03: Correlação sem troca de item

- Entrada: eventos de dois itens consecutivos.
- Contrato: confirmação só fecha a ordem correspondente por ID/janela física.
- Critério de reprovação: atraso do sensor do item A atribuído ao item B.
- Verificação: ensaio com espaçamento mínimo. Dependências: DAT-01/03.

### ACT-04: Timeout, retry e idempotência

- Entrada: ordem sem confirmação.
- Contrato: timeout configurável, retry contado e nenhuma ejeção duplicada por replay.
- Critério de reprovação: repetir a mesma mensagem gera duas ordens físicas.
- Verificação: log de tentativas e contador físico. Dependências: DAT-07, IF-04.

### ACT-05: Estado operacional do atuador

- Entrada: ciclo do atuador.
- Contrato: `pronto`, `acionado`, `confirmado`, `falha`, `bloqueado`, `parada_manual`.
- Critério de reprovação: dashboard mostra pronto enquanto o atuador está bloqueado/falhando.
- Verificação: transição temporal e query. Dependências: OPS-03.

### ACT-06: Parada manual auditável

- Entrada: ação do operador.
- Contrato: interromper novas ordens e registrar operador, motivo e horário.
- Critério de reprovação: parada não impede novo acionamento ou não deixa trilha.
- Verificação: ensaio e evento de auditoria. Dependências: SAFE-03.

### ACT-07: Evidência da atuação

- Entrada: sensor, imagem/vídeo e evento.
- Contrato: evidência ligada ao item, vista, sensor e hash/caminho.
- Critério de reprovação: evento confirmado sem artefato recuperável quando o método exige imagem.
- Verificação: leitura do arquivo e evento. Dependências: DAT-08.

### ACT-08: Não ejetar OK e não mascarar falha

- Entrada: golden OK, defeito e sensor ausente.
- Contrato: OK segue; defeito sem confirmação vira falha de qualidade.
- Critério de reprovação: golden ejetado ou falha apresentada como confirmada.
- Verificação: ensaio negativo com contagem. Dependências: SAFE-01/02, RNF-13.

### ACT-09: Teste controlado separado

- Entrada: golden sample ou modo simulado.
- Contrato: testar o atuador sem contaminar estatísticas nem confundir produção.
- Critério de reprovação: evento de teste contado como lote produtivo.
- Verificação: flag de modo e consulta filtrada. Dependências: DAT-05.

### ACT-10: Propagação de falha

- Entrada: falha de atuação crítica.
- Contrato: mesma falha chega ao banco, dashboard, relatório e ntfy quando aplicável.
- Critério de reprovação: uma superfície diz falha e outra diz sucesso/ausência.
- Verificação: `item_id` nas quatro superfícies. Dependências: IF-05/06.

### SAFE-01: Quarentena e análise humana

- Contrato: atuador separa para análise manual; não descarta automaticamente.
- Critério de reprovação: sistema elimina item sem decisão humana.
- Verificação: fluxo físico e procedimento.

### SAFE-02: Falha segura de sensor

- Contrato: sensor nulo, desconectado ou ambíguo não confirma ejeção.
- Critério de reprovação: forçar leitura inválida e observar estado final.
- Verificação: fixture/simulação e evento de qualidade.

### SAFE-03: Parada e intertravamento

- Contrato: não acionar sem item/condição válida; existir parada manual e condição de recuperação.
- Critério de reprovação: ordem sem item ou durante parada aciona o mecanismo.
- Verificação: teste de bancada e checklist.

## Lacuna de schema

A tabela `evento_rejeicao` cobre ordem, confirmação, estado e sensor, mas a composição de atuação exige ainda tentativa, timeout, retry, estado operacional, motivo de parada, operador, evento de comando e evidência. A alteração do schema deve ser uma decisão separada antes do código.