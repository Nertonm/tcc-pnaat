# Documentação do projeto

Índice da documentação. Cada linha diz o que o documento responde e onde ele está.

## Documento de referência

A fonte de verdade do documento formal é `latex-workspace/`: `main.tex` gera o PDF de Levantamento de Requisitos e `Roteiro.tex` gera o roteiro do vídeo pitch.

O recorte atual é: Cenário 1, inspeção de envase. O núcleo propõe observação multi-view, classificação por domínio, registro rastreável e dashboard usando um nó de observação. O documento não assume controle da velocidade da esteira, atuação física, ejeção, hub central, MQTT ou múltiplos nós como capacidades do núcleo.

## Leitura por objetivo

| Necessidade | Documento |
|---|---|
| Escopo, núcleo e limites do projeto | `escopo.md` |
| Arquitetura proposta e componentes implementados | `arquitetura.md` |
| Catálogo RF-01 a RF-30 e RNF-01 a RNF-21 | `requisitos.md` |
| Fichas detalhadas por domínio | `requisitos/README.md` |
| Dados, schema do registro, taxonomia e consultas | `dados-telemetria.md` |
| Estado do dashboard e das rotas de escrita | `docs/dashboard-site.md` |
| Decisões técnicas, alternativas e critério de fechamento | `DECISIONS.md` |
| Histórico e protocolo das provas de conceito | `pocs/README.md` (fontes de código removidas deste checkout) |
| Correspondência da numeração de PoCs anterior | `pocs/MAPA.md` (histórico) |
| Referências com grau de verificação | `REFERENCIAS.md` |
| Hardware: BOM, pinagem, montagem e limites medidos | `hardware.md` |
| Diagrama de interligação elétrica do núcleo implementado | `diagramas/` |
| Como o dataset foi anotado, com o Label Studio (e o que é dado de instalação) | `reference/uso-do-label-studio.md` |
| Rotulagem assistida por modelo generativo: só criação de dataset, não é runtime | `reference/classificar-gemini.md` |
| Esquemático do trigger (Wokwi ESP32-S3 + sensor) | `reference/esquematico-trigger.md`; zip na raiz `ESP32S3-Trigger.zip` |
| Guia das rotas de trigger, captura, inferência e registro | `operacao-pipeline.md` |
| Replicação do zero, de ponta a ponta (firmware, serviços, ciclo) | `replicacao-ponta-a-ponta.md` |
| Manual de replicação (instalação, execução, verificação) | `../README.md` |

## Fichas de requisitos

| Arquivo | Cobertura |
|---|---|
| `requisitos/01-funcionais.md` | RF-01 a RF-30, incluindo sub-IDs (RF-01.1/1.2, RF-04.1, RF-05.1) |
| `requisitos/02-nao-funcionais.md` | RNF-01 a RNF-21, incluindo RNF-04.1 |
| `requisitos/03-dados-interfaces.md` | DAT-01 a DAT-08 e IF-01 a IF-07 |
| `requisitos/04-atuacao-seguranca.md` | Atuação, controlabilidade, observabilidade e segurança (expansão) |
| `requisitos/05-hardware-ml.md` | Rig, elétrica, iluminação, dataset e modelos |
| `requisitos/06-operacao.md` | Operação, manutenção, documentação e reprodutibilidade |

## Provas de conceito

| Caminho | Conteúdo |
|---|---|
| `pocs/README.md` | Matriz canônica das PoCs e estado verificado da execução de referência |
| `pocs/MAPA.md` | De-para entre os diretórios da geração anterior e as PoCs entregues |
| `pocs/poc02_classificacao/` | Protocolo da PoC-02 (classificação de tampa) |
| `pocs/poc08_preproc/` | Protocolo da PoC-08 (pré-processamento e geometria) |
| `pocs/03-sincronizacao-fisica/CALIBRACAO-DELAY.md` | Calibração do atraso trigger → captura e do casamento da velocidade da esteira (expansão; protocolo, fontes removidas deste checkout) |
| `pocs/01-classificador-topo/`, `pocs/02-deformidade-lateral/`, `pocs/03-sincronizacao-fisica/`, `pocs/04-correlacao-multi-no/`, `pocs/05-integracao-dados/`, `pocs/06-resiliencia/`, `pocs/07-atuacao-confirmada/` | Fichas da geração anterior, preservadas como histórico e expansão |

## Referência e design

| Caminho | Conteúdo |
|---|---|
| `reference/` | Notas de referência, medições próprias e caracterização de componentes |

## Referências externas verificadas

- `reference/ref-pysource-bottle-defect-inspection.md`: inspeção de defeito de garrafa em esteira (Pysource): ID único, banco e dashboard por lote. Referência, não decisão de stack.
- `reference/ref-eca-efficientdet-packaging-bottle-defects.md`: detecção de defeito de tampa e rótulo com ECA-EfficientDet (mAP 99,16%).
- `reference/ref-jarvis-bits-bottle-defect-detection.md`: Mask-RCNN com CNN (87,7% e 72%), recuperada como piso de comparação.
- `reference/ref-e18-d80nk-sensor.md`: caracterização do sensor candidato de presença.
- `reference/limiares-tampa-fonte-e-calibracao.md`: por que os limiares da tampa exigem calibração empírica (D-24).
- `reference/medicao-vies-elipse-geometria.md`: medição própria do viés do ajuste de elipse.
