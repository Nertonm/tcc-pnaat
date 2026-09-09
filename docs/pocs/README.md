# Protocolo de provas de conceito

## Objetivo

Uma PoC responde uma pergunta de viabilidade antes da integração. Ela não é uma versão incompleta do produto e não recebe o rótulo “funciona” por uma execução feliz.

## Ciclo obrigatório

1. Definir uma pergunta binária e o risco que ela reduz.
2. Registrar hipótese, setup, entradas, métrica, limiar e condição de parada antes do teste.
3. Isolar uma variável crítica; não integrar componentes não necessários.
4. Executar casos positivos, negativos e de fronteira.
5. Registrar resultado observado, falhas, ambiente e artefatos.
6. Decidir entre aprovada, não aprovada ou aprovada com condição.
7. Propagar a decisão para requisitos, escopo e próximo experimento.

## Registro mínimo

```markdown
# PoC NN: nome

- Status: Pendente | Em execução | Aprovada | Não aprovada | Aprovada com condição | Bloqueada
- Data:
- Responsável:
- Pergunta binária:
- Hipótese:
- Risco coberto:
- Setup: hardware, software, versão, iluminação e dataset
- Entrada e amostra:
- Métrica e limiar:
- Casos positivos:
- Casos negativos:
- Casos de fronteira:
- Resultado observado:
- Go/no-go:
- Evidência:
- Requisitos afetados:
- Decisão seguinte:
```

## Regras de validade

- Meta não é medição.
- Benchmark externo não é resultado do Pi 5.
- Um log sem amostra, versão e setup não fecha a PoC.
- Falha de hipótese é resultado válido e deve ser preservada.
- PoC de componente não prova integração ponta a ponta.
- Modo de teste e golden samples devem ser separados das estatísticas produtivas.
- Alterar hardware, modelo, dataset ou limiar invalida a comparação anterior.
- A inclusão de um componente no setup não representa sua aprovação; componentes candidatos devem possuir critério de validação, alternativa e decisão go/no-go registradas.
- Evidência insuficiente, vista ausente ou resultado inconclusivo não pode ser convertido em aprovação por ausência de defeito detectado.

## Ordem por risco

| ID | PoC | Pergunta | Dependência de saída |
|---|---|---|---|
| 01 | Classificador de topo | Tampa ausente/mal rosqueada atinge o limiar preliminar? | dataset e iluminação |
| 02 | Deformidade lateral | As laterais identificam deformidade com erro aceitável? | calibração e PoC 01 |
| 03 | Sincronização física | O trigger e o mecanismo de medição permitem associar as três vistas ao mesmo item dentro da janela definida? | rig, E18-D80NK candidato, encoder candidato e critérios de substituição |
| 04 | Correlação multi-nó | O hub associa eventos de 50 itens sem troca? | payload e relógios |
| 05 | Integração de dados | Eventos chegam ao SQLite sem perda/duplicação? | MQTT e schema |
| 06 | Resiliência | Falhas definidas recuperam sem crash e com estado observável? | PoC 05 |
| 07 | Separação confirmada | O item reprovado é direcionado e confirmado no caminho de análise manual sem separar itens normais? | atuador, sensor independente, posicionamento, timeout e segurança |

## Evidência por PoC

Guardar somente artefatos diretamente ligados ao ensaio: manifest de entrada, configuração, logs estruturados, imagens ou vídeo, relatório e decisão. Binários grandes, dados brutos e arquivos privados ficam fora do Git, com caminho e hash no manifest.

## Critério de liberação

Uma PoC aprovada libera somente a próxima dependência declarada. Ela não transforma o sistema inteiro em implementado. A integração final exige novo ensaio com o conjunto completo.
