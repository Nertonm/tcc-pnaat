<!-- preserve: deep research TCC PNAAT -->
<!-- fonte: paste do assistente (fora do repo): paste_8_000030.txt -->
<!-- sha256_origem: e38623b84d53c8280bcd33445c57fee1a23712cf6db9acacc2b8b26e32e7ebfa -->
<!-- rodada: v4 — reformulação / solução fora da caixa -->

## A Reformulação Central

A abordagem mais "fora da caixa" encontrada na pesquisa não é um modelo mais sofisticado — é uma **mudança de pergunta**. Em vez de "como treino um classificador para reconhecer defeitos que eu preciso fotografar", a pergunta se torna: **"como ensino o modelo a reconhecer o conceito de irregularidade sem nunca lhe mostrar um defeito real?"** Isso existe, tem nome, benchmark forte e resolve de forma elegante o maior gargalo prático do projeto (escassez de imagens reais de defeito).

## 1. CutPaste / Natural Synthetic Anomalies (NSA) — Autossupervisão que Inventa seus Próprios Defeitos

**O que é:** o método CutPaste, publicado pela equipe do Google Cloud AI na CVPR 2021, treina um detector de anomalia usando **apenas imagens de itens OK**. A ideia central é absurdamente simples: recorta-se um retalho retangular aleatório da própria imagem normal e cola-se de volta em outro lugar da mesma imagem, criando uma "anomalia sintética" artificial; a rede então aprende a distinguir a imagem original da imagem "remendada", e esse aprendizado — de reconhecer irregularidade local — generaliza para detectar defeitos reais nunca vistos no treino **[CONFIRMADO — paper original CVPR 2021, Google Research]**. O resultado reportado é 96,6% de AUC no MVTec AD usando apenas dados normais e essa augmentação sintética, superando o estado da arte da época em 3,1 pontos de AUC **[CONFIRMADO]**.[^1][^2][^3]

Uma evolução direta, **Natural Synthetic Anomalies (NSA)**, refina a técnica usando Poisson image editing para colar o retalho de forma "costurada" (sem bordas artificiais abruptas), tornando a anomalia sintética muito mais parecida com um defeito real de manufatura — o paper reporta AUROC de 97,2%, superando CutPaste em 2 pontos, e destaca explicitamente que o modelo treinado com essas anomalias sintéticas **generaliza bem para detectar tipos de defeito reais nunca vistos e desconhecidos a priori** **[CONFIRMADO — ECCV 2022]**. Um survey de 2024 sobre anomaly detection autossupervisionado confirma CutPaste e NSA como as duas referências centrais dessa linha de pesquisa, e cita variantes adicionais (SSAPS, cutout, cutmix) explorando a mesma ideia de "criar anomalia sintética por manipulação de patch" **[CONFIRMADO]**.[^4][^5][^6]

**Por que isso é a reformulação certa para o TCC:** o projeto já tem o problema mais frágil identificado nas rodadas anteriores — dataset de defeito escasso (fotos próprias de tampa + peças 3D impressas para deformidade). CutPaste elimina completamente a necessidade de fotografar defeitos reais para treinar a camada de anomalia: **qualquer foto de garrafa boa, mais um script de poucas linhas que recorta-e-cola um retalho aleatório, já gera dados de treino sintéticos "suficientemente bons"** segundo a evidência do paper original. Isso é conceitualmente diferente e mais barato do que gerar dados sintéticos fotorrealistas em Blender (avaliado e descartado como PARCIAL/INVIÁVEL na rodada anterior) — aqui a "síntese" é uma manipulação de pixel trivial sobre as próprias fotos reais já coletadas, não um pipeline de renderização 3D.

**Como implementar no contexto (concreto, poucos dias de esforço):**
1. Usar apenas as fotos de itens OK já capturadas nas 3 vistas (topo/lateral1/lateral2).
2. Escrever um script simples (recorte de patch retangular de tamanho e posição aleatória, com opção de rotação/jitter de cor, colado de volta em local aleatório da mesma imagem — a receita exata do CutPaste está documentada passo a passo no paper).[^1]
3. Treinar um classificador binário leve (rede pequena tipo MobileNetV2/EfficientNet-lite, já compatível com o hardware do projeto) para distinguir "imagem original" vs "imagem com CutPaste".
4. Na inferência, usar a saída dessa rede (ou o classificador one-class construído sobre suas representações, conforme o framework de 2 estágios do paper) como uma **4ª camada de anomalia genérica**, complementar ao classificador supervisionado de defeito específico já existente.[^3]

**Classificação: FACTÍVEL.** Esforço: baixo-médio (poucos dias para o script de augmentação + treino de uma rede pequena, que já é ordem de grandeza similar ao classificador principal já planejado). Risco técnico: baixo — é uma técnica publicada, com receita exata disponível, sem dependência de hardware novo ou modelo pesado de fundação.

**Impacto na nota: Alto.** Isso é qualitativamente diferente de "peguei um modelo pronto": é uma solução de pesquisa publicada (CVPR/ECCV) aplicada de forma inteligente ao gargalo real do projeto (escassez de dados de defeito) — a narrativa de pitch fica: **"o sistema aprende o conceito de anomalia sem nunca ter visto um defeito real, criando seus próprios exemplos de treino a partir de fotos de itens perfeitos."** Isso é literalmente o tipo de "solução inteligente e fora da caixa" que a apostila valoriza, e resolve — em vez de contornar — o problema de dataset identificado desde a primeira rodada de pesquisa.

## 2. Consistência Cross-View como Sinal de Anomalia (Sem Reconstrução 3D)

**O que é:** pesquisa recente propõe que, em sistemas multi-câmera, em vez de processar cada vista de forma independente (como o projeto faz hoje com late fusion por votação), pode-se explorar a **consistência geométrica entre vistas** como uma fonte adicional de sinal de anomalia — um trabalho de 2026 usa restrição epipolar (relação geométrica entre duas câmeras calibradas) para guiar a fusão de features entre vistas, sintetizando "amostras negativas" a partir de inconsistências entre o que uma vista prevê e o que a outra vista realmente mostra **[CONFIRMADO]**. Outro trabalho recente (AAAI 2025) propõe explicitamente um framework de anomaly detection multi-vista que modela a consistência intra-vista e a decomposição implícita entre vistas para melhorar a detecção **[CONFIRMADO]**.[^7][^8]

**Insight fora da caixa aplicável sem a complexidade geométrica plena:** o princípio central — "o que uma vista vê deve ser consistente com o que as outras vistas veem, e a *inconsistência* em si é um sinal de anomalia" — pode ser aplicado de forma muito mais simples do que a matriz fundamental epipolar completa (que exigiria calibração estéreo precisa entre as 3 câmeras, esforço de engenharia significativo e risco de instabilidade, incompatível com "sem reconstrução 3D densa"). Uma versão simplificada e barata: como o trigger físico (E18-D80NK/VL53L0X) já garante que as 3 vistas capturam o **mesmo item na mesma posição conhecida via guias mecânicas** (já parte da arquitetura decidida), o sistema pode aprender a distribuição conjunta esperada dos 3 anomaly-scores (um por vista, gerado pela camada CutPaste do item 1) para itens normais — e sinalizar como suspeito qualquer item cuja combinação de scores das 3 vistas seja estatisticamente incomum, mesmo que nenhuma vista individual cruze seu próprio threshold. Isso é, na prática, adicionar uma camada de decisão multivariada leve (ex. distância de Mahalanobis sobre o vetor de 3 scores) sobre um sinal que o sistema já produziria de qualquer forma.

**Classificação: FACTÍVEL como refinamento leve da votação já decidida — não como reconstrução geométrica epipolar completa.** A versão epipolar rigorosa dos papers seria PARCIAL/INVIÁVEL em 2 meses (exige calibração estéreo e é essencialmente uma forma disfarçada de reconstrução 3D leve, o que o escopo já decidiu evitar); a versão simplificada de "consistência estatística entre scores de anomalia das 3 vistas" é um upgrade de baixo custo sobre a arquitetura de votação já existente. **Impacto na nota: Médio-alto** — é uma forma elegante de extrair mais sinal da arquitetura multi-view já decidida (justamente o diferencial já central do projeto) sem violar a restrição de não fazer reconstrução 3D, e conecta-se diretamente ao argumento de "multi-view entrega o mesmo valor com 1/10 da complexidade" já validado em rodadas anteriores.[^8][^7]

## Recomendação de Composição

A combinação mais forte e genuinamente inovadora para o pitch: **camada CutPaste/NSA (item 1) treinada com fotos de item OK já coletadas + votação já existente + camada de consistência estatística entre os 3 scores de anomalia (item 2, versão simplificada)**. Isso reformula o problema de "classificar 3 tipos de defeito conhecidos" para "detectar irregularidade de forma autossupervisionada, com 3 vistas que se verificam mutuamente" — uma moldura conceitual mais sofisticada, cientificamente fundamentada em publicações de peso (CVPR, ECCV, AAAI), e que não exige nenhum dado adicional de defeito real além do que já foi coletado como item OK, sem tocar no núcleo já congelado do classificador supervisionado.

**Risco a monitorar:** um trabalho recente demonstra que autoencoders/redes de reconstrução podem "aprender demais" e reconstruir anomalias perfeitamente, tornando-as invisíveis ao detector — uma falha teórica documentada da abordagem baseada em erro de reconstrução **[CONFIRMADO — risco genuíno, não hipotético]**. Isso reforça a recomendação de usar CutPaste no formato original (classificação binária real/sintético + one-class classifier sobre a representação aprendida, não um autoencoder puro de reconstrução), que é a variante validada nos papers com melhor resultado e sem essa vulnerabilidade específica.[^9]

---

## References

1. [[PDF] Self-Supervised Learning for Anomaly Detection and Localization](https://openaccess.thecvf.com/content/CVPR2021/papers/Li_CutPaste_Self-Supervised_Learning_for_Anomaly_Detection_and_Localization_CVPR_2021_paper.pdf)

2. [[PDF] CutPaste: Self-Supervised Learning for Anomaly Detection and Localization | Semantic Scholar](https://www.semanticscholar.org/paper/CutPaste:-Self-Supervised-Learning-for-Anomaly-and-Li-Sohn/78d80c343d36baaf89f18e12d325cf6309fb6c8f) - This work proposes a two-stage framework for building anomaly detectors using normal training data o...

3. [Discovering Anomalous Data with Self-Supervised Learning](https://research.google/blog/discovering-anomalous-data-with-self-supervised-learning/) - We then follow up on this in “CutPaste: Self-Supervised Learning for Anomaly Detection and Localizat...

4. [Self-Supervised Anomaly Detection: A Survey and Outlook](https://arxiv.org/html/2205.05173v5)

5. [Natural Synthetic Anomalies for Self-Supervised](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136910459.pdf)

6. [Self-Supervised Augmented Patches Segmentation for Anomaly Detection](https://openaccess.thecvf.com/content/ACCV2022/papers/Long_Self-Supervised_Augmented_Patches_Segmentation_for_Anomaly_Detection_ACCV_2022_paper.pdf)

7. [Multi-View Industrial Anomaly Detection with Epipolar Constrained Cross-View Fusion](https://ar5iv.labs.arxiv.org/html/2503.11088) - Multi-camera systems provide richer contextual information for industrial anomaly detection. However...

8. [Unveiling Multi-View Anomaly Detection: Intra- ...](https://ojs.aaai.org/index.php/AAAI/article/view/33349/35504) - de K Mao · 2025 · Citado por 6 — We propose a multi-view anomaly detection framework. IDIF, which le...

9. [Autoencoders for Anomaly Detection are Unreliable - arXiv](https://arxiv.org/html/2501.13864v1)

