# Documentação do projeto

## Documento de referência

A fonte de verdade do documento é `latex-workspace/`, que gera o PDF de Levantamento de Requisitos.

O recorte atual é: Cenário 1, Inspeção de envase. O núcleo propõe observação multi-view, classificação, registro rastreável e dashboard usando um nó de observação. O documento não assume controle da velocidade da esteira, atuação física, ejeção, hub central, MQTT ou múltiplos nós como capacidades do núcleo.

## Leitura por objetivo

| Necessidade | Documento |
|---|---|
| Escopo e limites do projeto | `escopo.md` |
| Arquitetura proposta | `arquitetura.md` |
| Catálogo RF/RNF | `requisitos.md` |
| PoCs e conjectura integrada | `pocs/README.md` |
| Decisões anteriores e alternativas | `DECISIONS.md` |

## Referências
- `reference/ref-pysource-bottle-defect-inspection.md`: inspeção de defeito de garrafa em esteira (Pysource): ID único + banco + dashboard por lote. Referência, não decisão de stack.
- `reference/ref-eca-efficientdet-packaging-bottle-defects.md`: detecção de defeito de tampa/rótulo com ECA-EfficientDet (mAP 99,16%). Referência, não decisão de stack.
- `design/preprocessamento-ideal-pet.md`: spec consolidada de aquisicao/pre-processamento PET (iluminacao assimetrica, flat-field, Halir+RANSAC, metricas CNR/Tenengrad).
- `reference/ref-jarvis-bits-bottle-defect-detection.md`: referencia recuperada (Mask-RCNN + CNN, 87,7%/72%).
