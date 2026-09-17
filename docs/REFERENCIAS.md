# Referências

Referências usadas nas decisões do projeto. Cada linha diz **o que a referência estabelece**, o grau de
verificação e onde ela é usada. Número de terceiro não vira resultado nosso.

Grau de verificação: **P** texto conferido na fonte · **S** secundária (abstract, snippet ou índice) ·
**B** prática de mercado (blog, guia; sem valor de norma) · **N** produção nossa.

## Normas e prática industrial (tampa e envase)

| Referência | O que estabelece | Gr. | Usada em |
|---|---|---|---|
| ISBT, *Plastic Bottle Closure Qualification Test Manual* (PTC-00019, abr/2023); *Plastic Closure Ovality Guideline* (PTC-00022, nov/2024); *Capping and Inspection Equipment* (PTC-00012, mai/2014) | os ensaios avaliam o sistema de embalagem completo e a especificação é acordada entre fornecedor e engarrafador; não há tolerância angular universal publicada | P (ementa) | D-24 (por que a calibração é empírica) |
| Manual de defeitos de fechamento (Delta El Nile) | catálogo de falhas de capping: tampa inclinada após assentada, ângulo de aproximação do mandril acima de 2°, torque de aplicação insuficiente, anel de lacre rompido | P | D-23, D-24 |
| Bandas de referência PCO 1881 / bebida carbonatada | torque de aplicação 13-19 in·lbs, ângulo de aplicação 760°-800°, abertura 5-14 in·lbs, strip > 25 in·lbs, selo ≥ 100 psi | P | referência de processo (não é o nosso limiar) |
| Bevcap / PMMI-OMAC (ângulo de aplicação, §5.2/§3.4, via manual acima) | 2° de desvio do vertical no contato mandril-gargalo | S | D-24 (grandeza diferente do tilt da tampa) |

## Óptica e aquisição em material transparente

| Referência | O que estabelece | Gr. | Usada em |
|---|---|---|---|
| *Multi-Parameter Inspection Platform for Transparent Containers* (PMC12736620) | fotoelasticidade (±3 nm), telecêntrica com subpixel (±0,2 mm) e YOLOv8 (mAP@0.5 90,3%) em ampolas | P | teto de metrologia e de detecção (números deles) |
| Halir & Flusser (1998), *Numerically Stable Direct Least Squares Fitting of Ellipses* | ajuste de elipse estável, com viés algébrico que encolhe a cota | P | geometria da tampa (PoC-02/PoC-08) |
| Edmund Optics: técnicas de polarização | polarização cruzada: ~50% teórico e 60-65% na prática | P | escolha de iluminação |
| Fotografia de produto transparente (nightjar, abr/2026) | o frasco é simultaneamente objeto e lente; fundo e luz definem o contorno | B | prática de captura |
| Cognex: iluminação em visão industrial | geometria de luz por tipo de defeito | B | prática de captura |
| Nosso ensaio de viés de elipse | viés de 0,023 mm (σ=1 px); arco ocluído degrada o ângulo (1,3° → 4,1° a 270°); escala 0,611 mm/px | N | critério de arco visível |

## Detecção e classificação

| Referência | O que estabelece | Gr. | Usada em |
|---|---|---|---|
| Sheng & Wang, *Fast Method of Detecting Packaging Bottle Defects Based on ECA-EfficientDet* (J. Sensors 2022, 9518910) | detecção supervisionada de tampa/rótulo, mAP 99,16% com 1.200 amostras | P | teto de acurácia supervisionada |
| *Machine-Vision-Based Plastic Bottle Inspection* (Eng. Proc. 2022, 20(1):9) | tampa assentada por Harris + linha entre cantos extremos + limiar derivado de referência; 95% no conjunto; tampa sem falso positivo | S | método geométrico com limiar calibrado |
| Xie et al. (2017): PET, distância entre anel de apoio e tampa | 99% para tampa solta em PET | S | precedente de medição por distância |
| Kumchoo & Chiracharit (2018): vidro, tampa solta e anel | 87% | S | piso de desempenho em vidro |
| Jarvis-BITS/bottle-defect-detection | Mask-RCNN + CNN: 87,7% (normal/defeituoso) e 72% (material), 740 imagens | P (clone) | referência do que não atende |
| PatchCore (2106.08265) · FastFlow (2111.07677) · CutPaste (2104.04015) · anomalia no Pi (2409.15980) | detecção sem supervisão com conjuntos normais | S | escolha de detector (Expansão) |
| Li J. et al., *Industrial Image Anomaly Detection via SACD* (Sensors 25(12):3721, 2025) | teacher-student com pseudo-anomalias | P | alternativa de detector |
| Pysource: defeito em esteira em tempo real | padrão prático: detecção + rastreio + identificador + banco + dashboard | B | arquitetura de referência |
| anomalib 2.6.1 | API de detecção sem supervisão (verificada por execução; não há CutPaste) | N | ferramenta |
| Nosso piloto MVTec (bottle) | PatchCore image_AUROC 1,0 e PaDiM 0,999 no proxy; ≈1,0 também nas nossas 81 frames: mede o *domain gap* | N | por que validação é na bancada |

## Datasets públicos usados como apoio

| Referência | O que estabelece | Gr. | Usada em |
|---|---|---|---|
| Roboflow: `bottle_cap_sdp`, `dataset-joren-newest`, `original-zotc7`, `bottle-defect-detection`, `bottle-lte35` (licença CC BY 4.0) | classes de tampa com contagens reais: `no_cap`, `misplaced_cap`, `Loose Cap`, `Missing cap`, `ring-missing`, `Unclosed` | P (baixado e contado) | banco de comparação de método e de convenção de rótulo |
| Kaggle: *Water Bottle Defect-Level Detection* | `no_cap` 150 e `loose_cap` 150 em garrafa de água | S | banco de comparação |
| Mendeley: defeitos de embalagem em vinho | tampa ausente em garrafa opaca, visão de topo | S | não se aplica (domínio distinto) |

