# Requisitos detalhados

Esta árvore divide cada requisito por domínio e transforma o mapa em fichas executáveis. O arquivo legado `../requisitos.md` permanece como baseline RF/RNF; `../requisitos.md` permanece como mapa geral de aspectos.

## Ficha padrão

Cada ficha deve responder:

- ID e título.
- Tipo: funcional, qualidade, dado, interface, hardware, segurança, operação ou aceite.
- Ator e pré-condições.
- Entrada e comportamento esperado.
- Saída e estados de erro.
- Critério de reprovação.
- Evidência e dependências.

## Arquivos

- `01-funcionais.md`: RF-01 a RF-30, incluindo RF-01.1.
- `02-nao-funcionais.md`: RNF-01 a RNF-21.
- `03-dados-interfaces.md`: dados, contratos MQTT, interfaces e rastreabilidade.
- `04-atuacao-seguranca.md`: atuação, controlabilidade, observabilidade e segurança operacional.
- `05-hardware-ml.md`: rig, elétrica, iluminação, dataset e modelos.
- `06-operacao.md`: operação, manutenção, documentação e reprodutibilidade.

## Regra de status

Uma ficha descreve o que deve ser feito. O estado muda somente com artefato produzido no setup declarado. Um teste que não consegue executar por falta de hardware, dependência ou fonte fica bloqueado, não aprovado.

## Dependências de leitura

1. `../metodologia.md`
2. `01-funcionais.md` e `02-nao-funcionais.md`
3. `03-dados-interfaces.md` e `04-atuacao-seguranca.md`
4. `05-hardware-ml.md` e `06-operacao-documentacao.md`
5. `07-aceite-calendario.md`