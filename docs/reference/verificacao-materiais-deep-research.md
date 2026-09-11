# Verificação dos materiais citados pelo deep research (PET / pré-processamento)

Data: 2026-09-11. Método: browser real + busca + páginas primárias (não aceitei o texto do
relatório como prova). Fonte auditada: `paste_1_003308.txt` (relatório completo, 45 KB) e o
ingest `docs/reference/deep-research-preprocessamento-pet-resultado.md`.

Regra: claim só entra em decisão com status **CONFIRMADO** e trecho verificado.

## Tabela de verificação

| # | Material citado | Claim que o relatório extrai | Status | Evidência |
|---|---|---|---|---|
| 1 | `nightjar.so/blog/how-to-photograph-transparent-products-glass-bottles-liquids` | "a clear bottle is both subject and lens"; "light the edges and the scene seen through the product" | **CONFIRMADO (verbatim)** | blog real ("How to Photograph Transparent Products", pub. 07/04/2026), 18.038 chars, trecho presente. **É blog de fotografia de produto, não fonte de metrologia.** |
| 2 | (mesmo blog, 2ª citação) | "Edmund Optics' backlighting guide notes that backlight is useful for seeing liquid levels and label placement in transparent vials…" | **CONFIRMADO no blog, cadeia secundária** | o trecho existe no blog, que **cita** um guia da Edmund Optics. O guia primário não é acessível por nós (Cloudflare) → **UNVERIFIED na origem** |
| 3 | `edmundoptics.com/.../successful-light-polarization-techniques` | "Linear polarization… reduces the intensity theoretically by 50%… almost total elimination of hot spots and glare" | **CONFIRMADO (verbatim) + correção** | página oficial (e cópia Unice). Texto completo: "…theoretically by 50%, **and in practice closer to 60-65%**". O relatório truncou → **a perda real é 60–65%**, não ~50% |
| 4 | `cognex.com/en/.../machine-vision-lighting` | "In-line illumination enables brightfield illumination… Moritex telecentric and bi-telecentric lenses provide unparalleled measurement accuracy" | **parcial: página existe, citação NÃO verbatim** | a página (Moritex Lights) fala de back/bar/brick/coaxial/ring lights e de lentes **MML telecêntricas** com luz coaxial; "In-line illumination" **não aparece**. Citação foi montada |
| 5 | `pmc.ncbi.nlm.nih.gov/articles/PMC12736620/` | fotoelasticidade: "The photoelastic method is a non-contact optical technique for stress analysis, based on the birefringence…" | **CONFIRMADO (verbatim)** | paper real: *A Multi-Parameter Inspection Platform for Transparent (ampoules)* — estresse fotoelástico (**±3 nm**), medição dimensional com **telecêntrica + subpixel** (**±0,2 mm**) e **YOLOv8** (mAP@0.5 **90,3%**) |
| 6 | `assets-eu.researchsquare.com/files/rs-9814627/` | FID não prova realismo; "Synthetic-to-real defect-detection validation…" | **NÃO VERIFICÁVEL** | URL é **diretório sem arquivo/versão** → página vazia; a frase não foi encontrada em busca. **Não citar** |
| 7 | `arxiv.org/html/2404.08401v4` | "Mínimos Quadrados Diretos (Halir)" | **MISATRIBUÍDA** | o paper é **PnLCalib — Sports Field Registration** (campo de futebol). A frase citada **existe**, mas trata de **linhas do campo/court** ("conics on the field"); **"Halir" não aparece** no paper |
| 8 | `mdpi.com/1424-8220/25/12/3721` | SACD | **CONFIRMADO** | Li J., Li M., Huang S., Wang G., Zhao X. *Sensors* **2025**, 25(12):3721, DOI 10.3390/s25123721. Reverse distillation teacher–student com **pseudo-anomalias** (Gaussian/Simplex) |
| 9 | "Tan et al." (sem link nem ano) | índices de refração "PET 0,3363 / PE 0,0757 / PP 0,2062 / PS 0,1989" | **ERRO FÍSICO + fonte não identificada** | PET tem **n ≈ 1,57–1,64** (refractiveindex.info n=1,57; KLA 1,6357 @632,8 nm; lista Wikipedia 1,5750; guia bioplástico 1,57). `n < 1` é impossível em sólido. **Não usar** |

## O que a verificação muda no plano

**Sobrevive (pode entrar em decisão):** assimetria óptica (backlight para geometria da tampa;
polarização cruzada para o corpo), flat-field com dark frame, template matching NCC em pirâmide,
recorte de ROI (topo = geometria, 2/3 = modelo), Canny + ajuste de elipse com RANSAC, CLAHE nas
ROIs, máscara de especular (~245) **delegada ao modelo** em vez de inpainting, fusão em nível de
decisão, e a lógica de gotículas/vibração/deriva térmica como pitfalls a instrumentar.

**Muda:**
1. **Orçamento de luz**: polarização cruzada custa **60–65%** da luz (não 50%) → revisar o
   orçamento de iluminação e a exposição antes de prometer <1 ms.
2. **±0,2 mm é resultado do paper das ampolas** (PMC12736620), não do nosso rig. Não repetir como
   se fosse nosso número; é a meta a bater.
3. **Citação do ajuste de elipse**: trocar arXiv/PnLCalib por **Halir & Flusser (1998),
   "Numerically Stable Direct Least Squares Fitting of Ellipses"** (verificado).
4. **Ressalva do próprio Halir (nova, material)**: o método usa distância *algébrica* → **viés
   sistemático que encolhe a elipse**; o paper diz explicitamente que "cannot be used directly in
   applications where excellent accuracy of the fitting is required" e recomenda usá-lo como
   estimador inicial seguido de refino com distância *geométrica*. Como o RF-15/RNF-14 mira
   **0,5 mm**, precisamos medir esse viés no nosso `fit_ellipse_direct_ls` — e, se ele aparecer
   na ordem da tolerância, adicionar refino geométrico/subpixel antes de qualquer claim dimensional.
5. **SACD não é protocolo de validação** de defeito sintético: é um **framework de detecção**
   treinado com pseudo-anomalias. O *isolation gate* é **nosso** (R1 não o fornece) — mantê-lo como
   critério nosso, sem atribuição externa.
6. **Não citar** o preprint da researchsquare (não verificável) nem os números de "Tan et al.".

**Continua UNVERIFIED** (não bloqueia, mas não pode ser citado como fato): o guia primário da
Edmund Optics sobre backlighting (acessível apenas via blog) e o preprint rs-9814627.

## Consequência prática imediata

Frente de maior ROI que sai desta verificação: **quantificar o viés do ajuste direto de elipse**
nas nossas condições (teste sintético com ruído conhecido, medindo erro de semi-eixo e de ângulo
contra ground truth). Se o viés ficar abaixo de ~0,05 mm na escala do nosso pixel, o pipeline
geométrico está apto; se não, entra refino subpixel/geométrico antes de medir em mm.
