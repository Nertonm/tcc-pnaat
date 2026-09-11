# Operação, documentação, aceite e calendário

## Operação e manutenção

### OPS-01: Runbook de bancada

- Critério: operador consegue preparar, iniciar, parar e identificar uma demo sem conhecimento implícito do autor.
- Critério de reprovação: passo depende de caminho privado, comando ausente ou hardware não descrito. Evidência: execução por pessoa externa.

### OPS-02: Logs por fronteira

- Critério: logs separam captura, inferência, fusão, persistência, MQTT, sinalização e confirmação de leitura, com `item_id` e timestamps.
- Critério de reprovação: log agregado não permite localizar a falha. Evidência: amostra estruturada.

### OPS-03: Observabilidade do sistema

- Critério: dashboard/queries mostram item, defeito, fila, heartbeat, latência, qualidade e estado da sinalização.
- Critério de reprovação: campo existe no banco mas não chega ao consumidor. Evidência: query versus dashboard.

### OPS-04: Matriz de falhas

- Critério: câmera, rede, sensor, banco, sinalização e alimentação têm sintoma, resposta segura, recuperação e evidência definidos.
- Critério de reprovação: falha não classificada ou processo morto sem alerta. Evidência: matriz e ensaio.

### MAINT-01: Calibração repetível

- Critério: ajuste do grip, troca de câmera e recalibração preservam posição, fator pixel→mm e data.
- Critério de reprovação: alteração não deixa cópia anterior nem novo fator. Evidência: ficha antes/depois.

### MAINT-02: Histórico de decisão

- Critério: mudança de hardware, modelo, schema ou escopo entra em `DECISIONS.md` com motivo e evidência.
- Critério de reprovação: código/documento contradiz decisão sem registro. Evidência: `git log` e decisão.

## Documentação e reprodutibilidade

### DOC-01: README completo

- Critério: problema, arquitetura, setup, execução, teste, limites e estado atual estão descritos.
- Critério de reprovação: README chama documentação de implementação ou promete comando inexistente. Evidência: revisão contra árvore.

### DOC-02: Dependências declaradas

- Critério: runtime, testes, firmware e ferramentas têm manifestos versionáveis.
- Critério de reprovação: clone limpo depende de pacote instalado no host. Evidência: instalação em venv limpo.

### DOC-03: Clone limpo

- Critério: clone público/candidato executa o comando documentado sem arquivos ocultos do autor.
- Critério de reprovação: teste passa somente com caminho ou venv externo. Evidência: clone limpo.

### DOC-04: Esquemático do rig

- Critério: diagrama mostra alimentação, interfaces, trigger, iluminação estroboscópica com difusor, câmeras, encoder, sinalização ao operador, confirmação de leitura e fluxo MQTT.
- Critério de reprovação: diagrama omite componente necessário ao teste. Evidência: revisão cruzada com BOM.

### DOC-05: Registro de PoC

- Critério: cada PoC contém pergunta binária, setup, resultado, go/no-go, evidência e lição.
- Critério de reprovação: “funcionou” sem métrica ou hipótese. Evidência: ficha em `docs/pocs/`.

### DOC-06: Pitch rastreável

- Critério: pitch separa gancho/dor, solução, evidências e continuidade; cada número aponta para medição ou referência.
- Critério de reprovação: benchmark externo apresentado como medição do rig. Evidência: roteiro e fontes.

### DOC-07: Higiene da publicação

- Critério: GitHub não recebe credenciais, prompts internos, infraestrutura privada, dados brutos ou histórico CTGit não revisado.
- Critério de reprovação: scan de paths/histórico encontra material excluído. Evidência: manifest público e revisão.

## Aceite e calendário

### ACC-01: Rastreabilidade completa

- Critério: cada requisito aponta para fonte, teste, dependência e evidência.
- Critério de reprovação: requisito órfão ou aceito por inspeção visual. Evidência: matriz final.

### ACC-02: Estados honestos

- Critério: estados planejado, condicional, medido, bloqueado e ausente não são confundidos.
- Critério de reprovação: meta ou benchmark externo aparece como resultado. Evidência: revisão documental.

### ACC-03: Prazo operacional

- Critério: plano lógico S1–S8 fica separado dos marcos reais: 09/09 requisitos, 11/09 POC, 15/09 esboço, 18/09 vídeo/documentação.
- Critério de reprovação: documento apresenta oito semanas como prazo vigente sem ressalva. Evidência: calendário e plano reconciliados.

### ACC-04: Entrega de requisitos

- Critério: pacote contém dor, escopo, tipos de requisito, critérios de reprovação, dependências e rastreabilidade.
- Critério de reprovação: RF/RNF sem método de aceite ou extensão experimental no núcleo. Verificação: revisão do pacote de requisitos.

### ACC-05: Demonstração defensável

- Critério: toda afirmação da defesa tem medição própria ou é identificada como referência, meta ou roadmap.
- Critério de reprovação: número sem setup, n, ferramenta ou artefato. Evidência: roteiro auditado.
