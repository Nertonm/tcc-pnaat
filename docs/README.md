# Documentação do projeto

## Autoridade da Entrega 1

A fonte de verdade da entrega atual é `latex-workspace/`, que gera o PDF de Levantamento de Requisitos.

O recorte atual é: Cenário 1, Inspeção de envase. O núcleo propõe observação multi-view, classificação, registro rastreável e dashboard usando um nó de observação. O documento não assume controle da velocidade da esteira, atuação física, ejeção, hub central, MQTT ou múltiplos nós como capacidades do núcleo.

## Leitura por objetivo

| Necessidade | Documento |
|---|---|
| Escopo e limites da Entrega 1 | `escopo.md` |
| Arquitetura proposta | `arquitetura.md` |
| Catálogo RF/RNF | `requisitos.md` |
| PoCs e conjectura integrada | `pocs/README.md` |
| Decisões anteriores e alternativas | `DECISIONS.md` |
| Backlog técnico detalhado | `requisitos/` |

## Regra para o backlog detalhado

Os arquivos em `requisitos/` preservam hipóteses e alternativas de engenharia acumuladas antes do recorte atual. Eles não são autoridade para o PDF da Entrega 1 quando contradisserem `escopo.md`, `arquitetura.md` ou `requisitos.md`.

O estado de qualquer capacidade é proposta até a PoC correspondente produzir evidência identificável.

## Referências
- `reference/ref-pysource-bottle-defect-inspection.md` — inspeção de defeito de garrafa em esteira (Pysource): ID único + banco + dashboard por lote. Referência, não decisão de stack.
- `reference/ref-eca-efficientdet-packaging-bottle-defects.md` — detecção de defeito de tampa/rótulo com ECA-EfficientDet (mAP 99,16%). Referência, não decisão de stack.
