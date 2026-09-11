# Sinalização de defeito e segurança operacional

Esta seção substitui a atuação física por sinalização rastreável ao operador.
O escopo não inclui atuador, servo, solenoide, ejeção, separação ou descarte de
garrafas. Uma futura remoção física exige decisão, análise de segurança e
validação próprias.

### SIG-01: Ordem de sinalização observável

- Entrada: `item_id`, status de defeito e severidade.
- Contrato: registrar origem, timestamp, `notification_id`, canal e tentativa.
- Critério de reprovação: notificação apenas em log textual ou sem item vinculado.
- Verificação: tabela/evento consultável. Dependências: RF-14, DAT-07.

### SIG-02: Estados de entrega separados

- Entrada: decisão, canal e relógio.
- Contrato: `pendente`, `enviada`, `entregue`, `lida` e `falha`; `lida` é opcional quando o canal não oferece confirmação.
- Critério de reprovação: tentativa de envio produzir `entregue`.
- Verificação: fixture de cada transição. Dependências: IF-07.

### SIG-03: Correlação sem troca de item

- Entrada: eventos de dois itens consecutivos.
- Contrato: cada alerta referencia o `item_id` e a decisão correspondente.
- Critério de reprovação: alerta do item A ser associado ao item B.
- Verificação: ensaio com eventos próximos e consulta. Dependências: DAT-01/03.

### SIG-04: Timeout, retry e idempotência

- Entrada: envio sem entrega.
- Contrato: timeout configurável, retry contado e nenhuma notificação duplicada por replay.
- Critério de reprovação: repetir a mesma mensagem gera alertas independentes sem vínculo.
- Verificação: log de tentativas e consulta. Dependências: DAT-07, IF-04.

### SIG-05: Teste controlado separado

- Entrada: golden sample ou modo simulado.
- Contrato: testar a sinalização sem contaminar estatísticas nem confundir produção.
- Critério de reprovação: evento de teste contado como lote produtivo.
- Verificação: flag de modo e consulta filtrada. Dependências: DAT-05.

### SIG-06: Propagação de falha

- Entrada: falha de sinalização crítica.
- Contrato: a mesma falha chega ao banco, dashboard, relatório e ntfy quando aplicável.
- Critério de reprovação: uma superfície diz entregue e outra diz falha/ausência.
- Verificação: `item_id` e `notification_id` nas superfícies. Dependências: IF-05/06.

### SAFE-01: Sem remoção física no escopo

- Contrato: o sistema somente informa a decisão; a garrafa segue na esteira e a análise/ação é humana.
- Critério de reprovação: qualquer comando de remoção, ejeção ou descarte ser tratado como capacidade implementada.
- Verificação: revisão de hardware, fluxo de dados e demonstração.

### SAFE-02: Falha segura de sinalização

- Contrato: falha de rede, canal indisponível ou payload ambíguo registra `falha`; nunca afirma entrega.
- Critério de reprovação: forçar erro de envio e observar estado de sucesso.
- Verificação: fixture/simulação e evento de qualidade.

## Lacuna de schema

O schema deve registrar um `evento_sinalizacao` com decisão, tentativa, estado,
canal, timeout, retry e evidência. A alteração do schema é uma decisão
separada antes da implementação.
