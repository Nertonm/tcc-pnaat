# PoC-08: pré-processamento e geometria determinística (PET)

## Pergunta binária

Um pipeline determinístico (sem rede neural) consegue **localizar a tampa e medir sua geometria**
(silhueta/elipse) e **medir a qualidade da captura** o suficiente para alimentar o classificador e o
gate dimensional?

## Por que existe

É a camada 1 do stack híbrido: geometria antes do modelo. Ataca `tampa_ausente` e, principalmente,
`tampa_mal_rosqueada` (tilt/altura) sem depender de dados defeituosos, e produz métricas de qualidade
do pré-processamento (CNR, Tenengrad, cobertura especular) que condicionam o gate RNF-02.

## O que roda

`workspace/src/pocs/poc08_preproc/preproc.py`:

| Etapa | Função | Custo alvo |
|---|---|---|
| Correção de campo plano | `flat_field` (LUT) | ~1-2 ms |
| Alinhamento por template (NCC piramidal) | `align_by_template` | ~3-5 ms |
| Recorte de ROI | `crop_roi` | <1 ms |
| Realce/normalização | `clahe_normalize` | ~4 ms |
| Máscara de especular (passada ao modelo) | `specular_mask` / `specular_coverage` | ~1 ms |
| Geometria da tampa (Canny → elipse LS direta + RANSAC) | `cap_geometry`, `fit_ellipse_direct_ls`, `fit_ellipse_ransac` | ~4 ms |
| Métricas de qualidade | `cnr`, `tenengrad`, `specular_coverage` | ~1 ms |

## Critério de passagem

- `make test-vision` verde (16 testes: recuperação de elipse sintética com ruído, RANSAC com 30% de
  outliers, shift conhecido no template matching, flat-field uniformiza vinheta, métricas coerentes).
- Numa frame real: elipse encontrada (`ok=True`) e métricas dentro da faixa (CNR/especular documentados).
- Regressão: qualquer mudança de parâmetro deve invalidar `pipeline_version`.

## Estado

Implementado e testado (MVP). Falta integrar no fluxo do dataset (`rig-<id>.yaml` + `apply_pipeline`)
e calibrar mm (Charuco) para destravar RNF-14.
