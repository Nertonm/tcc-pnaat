# PoC-08: Pre-processamento e geometria deterministica (PET)

| | |
|---|---|
| **Ideia isolada** | sem pre-processamento deterministico e sem qualidade de captura declarada, a medida da tampa nao e interpretavel |
| **Pergunta** | um pipeline deterministico localiza a tampa, mede sua geometria e mede a qualidade da captura o suficiente para alimentar a decisao? |
| **Hipotese** | contorno por Canny com ajuste de elipse e metricas de qualidade (CNR, Tenengrad, cobertura especular) bastam para alimentar a decisao e condicionar o gate |
| **Metodo** | extrair contorno e ajustar elipse por minimos quadrados e RANSAC; medir o vies do ajuste com arco completo e ocluido; medir as metricas de qualidade por imagem |
| **Criterio de passagem** | geometria extraida com erro conhecido e metricas de qualidade declaradas, com o limite de arco visivel documentado |
| **Evidencia** | medida por imagem (arco, tilt, CNR, especular) + ensaio de vies do ajuste de elipse + testes do modulo |
| **Limite atual** | no ensaio atual o pipeline usa apenas ROI, geometria e metricas; etapas como flat-field, alinhamento e mascara especular existem mas nao estao na cadeia |
| **Dependencias** | serve a PoC-02 e a PoC-03; RNF-02 via qualidade; descritores e calibracao em mm sao expansao |
| **Codigo** | `preproc.py`, `scripts/medir_vies_elipse.py` |
