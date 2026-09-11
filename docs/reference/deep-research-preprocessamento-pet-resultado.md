# Ingest: Deep research — pipeline ótimo de aquisição/pré-processamento PET (resultado)

Fonte: relatório de deep research fornecido por Nerton (texto colado na sessão, 2026-09-10).
Status: **ingest de resultado de pesquisa** (não é fonte primária; claims abaixo classificados).

## Recomendação central do relatório

Pipeline **híbrido**: condicionamento óptico + processamento clássico (determinístico) **antes**
dos modelos de anomalia (PatchCore/PaDiM/EfficientAD). Rejeita DL puro para geometria.

Assimetria de iluminação proposta:
- **Câmera da tampa (alta-direita)**: **backlight difuso** (campo claro) → silhueta de alto
  contraste para geometria/dimensão da tampa.
- **Câmera do corpo (baixa-esquerda)**: **luz frontal com polarização cruzada** → revela
  birrefringência (deformidade/tensão) e elimina reflexo especular.
- Fundo: backlight é o próprio fundo da câmera 1; câmera 2 com fundo **absorvedor escuro**
  (<2% refletividade). Sem chroma-key; separação por **subtração de fundo absoluta** (absdiff).

Câmera/ótica: **mono** (evita CFA/demosaic e aliasing) e **global shutter** obrigatório
(rolling shutter → skew em esteira). Telecêntrica ideal mas cara → lente de baixa distorção
(<1%) + calibração por Charuco. Abertura f/8–f/11; exposição <1 ms com **LED estroboscópico**
sincronizado ao global shutter pelo GPIO. HDR por bracketing **descartado** na borda (>150 ms);
preferir filtro polarizador ou sensor com DCG.

Pré-processamento (ordem proposta): correção flat-field (LUT) → alinhamento por template
matching NCC em pirâmide (1/4–1/8) → recorte de ROI (terço superior = geometria; 2/3 inferiores =
modelo) → **Canny + ajuste de elipse por mínimos quadrados diretos (Halir)** para inclinação da
tampa → CLAHE/normalização nas ROIs → máscara de especular (limiar ~245) **passada ao modelo**
(em vez de inpainting) → inferência INT8 (PaDiM/EfficientAD) nas ROIs.

Fusão **em nível de decisão** (não de feature) por restrição de banda/memória; métricas de tampa
priorizadas na câmera alta-direita; anomalias de corpo por OR/max-pooling entre vistas.

Robustez: defeito sintético deve passar por **isolation gate** (desvio ~0 fora do bbox; o
relatório cita "R ≥ 15% da área"); FID não prova realismo. Pitfalls citados: deriva térmica
(recalibrar flat-field), gotículas de condensação (viram micro-lentes → FP; incluir no
randomization), vibração (strobe 0,5–0,8 ms), rebarbas de PET nas roscas (FP na elipse → RANSAC).

Orçamento estimado no Pi 5 (por item): DMA 1–2 ms, flat-field 1–2 ms, TM piramidal 3–5 ms,
ROI <1 ms, geometria ~4 ms, CLAHE ~4 ms, máscara ~1 ms, INT8 35–50 ms → **50–65 ms** (~10–15
garrafas/s). Métricas de qualidade: CNR ≥18 (alerta <12), Tenengrad (foco), cobertura especular ≤3%.

## Verificação dos claims (o que NÃO confiar direto)

- **ERRO físico (CONFIRMED)**: o trecho "approximate refractive indices of PET, PE, PP and PS
  bottles were 0.3363, 0.0757, 0.2062 and 0.1989" está incorreto — índice de refração de PET é
  ~1,57; esses valores não são índices. Não usar.
- **Citações não verificadas (UNVERIFIED)**: `nightjar.so/blog/...` é usado como fonte de duas
  afirmações diferentes atribuídas a "Edmund Optics"; `PMC12736620`,
  `assets-eu.researchsquare.com/files/rs-9814627/`, `mdpi.com/1424-8220/25/12/3721` (SACD),
  `arxiv.org/html/2404.08401v4` — precisam de DOI/trecho verificado antes de citar no TCC.
- **Números apresentados como CONFIRMED que são ESTIMATIVA**: 50–65 ms, 10–15 garrafas/s,
  ±0,2 mm, CNR ≥18, especular ≤3%, f/8–f/11, "R≥15%". São hipóteses de engenharia a **medir**
  no nosso rig, não resultados.
- **Escolha de projeto a revisar**: "métricas de tampa só na câmera alta-direita" contraria nossa
  fusão determinística (que usa as duas vistas e manda discordância para análise humana). Pode ser
  adotado como priorização, não como exclusão.
- **Dependência não resolvida**: cross-polarização corta ~50% da luz → conferir orçamento de luz.

## O que adotar no nosso plano (acionável)

1. Rig assimétrico: backlight difuso na câmera da tampa; polarização cruzada + fundo escuro na
   câmera do corpo. (Resolve a dúvida anterior: com backlight + elipse, 1 vista pode bastar para
   inclinação — validar linearidade na PoC-03.)
2. Backbone de pré-processamento implementável já: flat-field, TM piramidal, ROI, Canny+Halir
   (com RANSAC), CLAHE, máscara de especular passada ao modelo.
3. Instrumentar as métricas de qualidade (CNR, Tenengrad, cobertura especular) e correlacionar com
   o gate RNF-02.
4. Dataset: manter nosso **isolation gate** (já implementado em `validar_pares.py`); adicionar
   variante por heatmap (professor) depois; incluir gotículas/condensação no randomization.
5. Ordens de grandeza (50–65 ms) entram como **meta a medir**, não como fato.