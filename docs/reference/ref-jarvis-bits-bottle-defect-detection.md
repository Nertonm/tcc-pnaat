# Ingest: repositório Jarvis-BITS/bottle-defect-detection (referência recuperada)

Status: **referência pública analisada** (não é fonte primária de método; os números são
auto-relatados pelos autores). Analisada em 2026-09-11.

## Proveniência

| Campo | Valor |
|---|---|
| URL | https://github.com/Jarvis-BITS/bottle-defect-detection |
| Commit clonado | `80c68a944abe094f4c02203b5787e2433497bef2` |
| Data do commit | 2022-05-26 |
| Tamanho do clone | 124 MB |
| Licença | presente no repo (`LICENSE`) |
| Origem declarada | projeto PS-1 (BITS Pilani) para a Plastic Water Labs Pvt. Ltd.; equipe Ishaan, Jishnu, Javin, Shivank |

## O que o repositório contém (verificado por inspeção do clone)

- `main.py` (Flask web app), `server_model.py` (segmentação sem web-app), `templates/index.html`
- `Defect Detection.ipynb`, `Model Prediction.ipynb`
- Modelos: `model_tacc8275_val8493.h5` (~85% no nome), `2nd_defect_detect.model` (~94% segundo o README),
  `64x3-CNN_material.model` (TensorFlow SavedModel), mask/segmentation (pixellib)
- Dados versionados: `Data/Proper` **375** imagens e `Data/Defective` **365** imagens (740 no repo;
  o README fala de 1000 imagens criadas com Kaggle + augmentation)
- `colors.csv` (classificação de cor), `Sample-pictures/` (GIF + 4 PNGs)

## Números auto-relatados (README, não reproduzidos por nós)

| Componente | Métrica declarada |
|---|---|
| CNN normal vs defeituoso (scratch/dent) | **87,7%** de acurácia |
| CNN de material (plástico vs vidro) | **72%** de acurácia |
| Segundo modelo de defeito | ~**94%** |
| Detecção/segmentação | Mask R-CNN fine-tuned (transfer learning) + pixellib |
| Dataset | 1000 imagens de garrafas normais/defeituosas (Kaggle + augmentation) |

## Relevância para o PNAAT (o que aproveitar e o que não)

**Aproveitar como referência:**
1. **Taxonomia de defeito por classe de aparência** (arranhão/dent): comparável à nossa
   `deformidade do corpo`; útil para nomear subclasses se a granularidade crescer.
2. **Precedente de pipeline em camadas**: detectar → segmentar → classificar. Espelha nossa
   camada 1 (geometria/localização) + camada 2 (classificador leve de aparência).
3. **Precedente de dataset aumentado** (Kaggle + augmentation) para compensar ausência de defeito
   real de linha: mesmo problema que enfrentamos; o repo confirma que é prática aceita.
4. **Números de referência baixos** (87,7% e 72%): calibram expectativa e reforçam que nosso
   RNF-02 (≥95%) não é trivial de atingir com abordagem puramente supervisionada.

**Não aproveitar / não repetir:**
1. **Não serve para métrica**: acurácia agregada sem matriz de confusão por classe e sem split
   declarado (risco de vazamento com augmentation antes do split).
2. **Não é solução de borda**: Mask R-CNN + Flask em nuvem/laptop: inviável no Pi 5 em tempo real.
3. **Sem metrologia**: nada de calibração px→mm, sem medição dimensional, sem fotoelasticidade -
   não cobre nosso RF-15/RNF-14.
4. **Sem isolamento de defeito sintético**: usa augmentation, não composição isolada com gate;
   nossa verificação exige o gate (mede o pixel fora do bbox).

## Consequência para o nosso plano

- Mantém o desenho híbrido (geometria determinística + classificador leve) e **não** justifica
  migrar para detector pesado.
- Reforça que a camada supervisionada precisa de **matriz de confusão por classe** e de split por
  sessão para valer como evidência (nosso RNF-03/RNF-15).
- Serve como referencia de comparacao de desempenho.
