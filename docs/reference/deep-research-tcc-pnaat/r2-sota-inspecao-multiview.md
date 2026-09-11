<!-- preserve: deep research TCC PNAAT -->
<!-- fonte: paste do assistente (fora do repo): paste_3_214812.txt -->
<!-- sha256_origem: 96dc3f32db8caa0bb60c088a1afca87cb9082e06e4a70ee661187d3faea5e344 -->
<!-- rodada: v2 — Estado da Arte (SOTA) multi-view + viabilidade em Raspberry Pi 5 -->

## PARTE A — Estado da Arte (SOTA) Aplicado ao Escopo

### A.1 Inspeção multi-view industrial: técnicas e viabilidade em Raspberry Pi 5

A literatura recente confirma late fusion (fusão de decisões pós-classificação, uma por vista) como técnica estabelecida e eficaz para inspeção multi-view industrial, incluindo um framework de detecção de defeitos que compara early e late fusion e reporta ganho de acurácia de ambos sobre a linha de base mono-view **[CONFIRMADO]**. Um estudo aplicado a inspeção prática de deterioração estrutural usando imagens multi-view confirma especificamente que a integração via late fusion (média de confiabilidade entre vistas, ou seleção do nível de maior risco entre vistas) é uma abordagem validada em cenário real de inspeção **[CONFIRMADO]**. Um survey de ensemble learning para fusão multi-câmera mostra que modelos de late fusion mantêm desempenho quase perfeito mesmo com frames ausentes de 1 a N-1 câmeras, o que é diretamente relevante para a resiliência exigida na Seção U4 — se uma câmera falhar, o sistema de votação por vista continua funcional em modo degradado **[CONFIRMADO]**. Um artigo mais recente propõe atenção ponderada entre vistas (VAAA) para inspeção multi-ângulo com número arbitrário de câmeras calibradas, mas isso exige calibração geométrica e uma rede de atenção treinada — nível de complexidade **acima** do necessário e do defensável para um TCC de 2 meses **[LIKELY over-engineering para este projeto]**.[1][2][3][4]

Detecção de anomalia few-shot e TinyML são linhas de pesquisa ativas para cenários com poucos dados rotulados, com métodos contrastivos e adaptação de domínio semi-supervisionada específicos para TinyML **[CONFIRMADO — existência da técnica]**. Isso é tecnicamente superior à classificação supervisionada simples nos casos onde o dataset é escasso, mas exige mais tempo de engenharia de modelo (perda contrastiva, arquitetura de anomaly detection) do que a classificação por votação já adotada no escopo — a recomendação é **citar essas técnicas na fundamentação teórica do TCC como trabalho relacionado/estado da arte**, mas não implementá-las no MVP, reservando-as como extensão pós-defesa justificada tecnicamente.[5][6]

**Conclusão SOTA para A.1:** a arquitetura de late fusion por votação já adotada no escopo é exatamente o que a literatura recomenda como abordagem madura e defensável para multi-view industrial sem reconstrução 3D, e está alinhada ao nível de maturidade esperado de um Pi 5 sem acelerador dedicado.[2][3][1]

### A.2 Datasets públicos de inspeção de garrafas — cobertura real das 3 classes

Localizou-se o "Water Bottle Defect-Level Detection Dataset" no Kaggle, com estrutura de anotação em formato YOLO (`data.yaml`) **[CONFIRMADO — existe e está estruturado para detecção]**. Contudo, a inspeção do conteúdo público disponível não confirma cobertura explícita das 3 classes do projeto (tampa ausente, tampa mal rosqueada, deformidade de corpo) — o nome sugere "níveis de defeito", que pode se referir a gravidade de enchimento/rótulo, não necessariamente às classes estruturais do projeto: **[SPECULATIVE — cobertura de classe não verificada em detalhe, validar manualmente antes de uso]**. Um dataset correlato de classificação de garrafa de água encontrado no Kaggle é voltado para nível de líquido (cheio/meio/derramando), não para defeitos estruturais de tampa/corpo **[CONFIRMADO — fora do escopo das 3 classes do projeto]**. Um dataset genérico de detecção de garrafas para segregação de resíduos também foi identificado, mas seu foco é presença/tipo de garrafa, não defeito estrutural **[CONFIRMADO — não cobre as classes-alvo]**.[7][8][9][10]

Para deformidade de corpo, o dataset industrial mais relevante e amplamente citado na literatura de defeitos é o MVTec AD (disponibilizado também via espelho no Kaggle), que cobre uma ampla gama de categorias de objetos com anomalias superficiais/estruturais, mas **não é específico de garrafas/tampas** — serve como benchmark metodológico geral de anomaly detection industrial, não como fonte direta de imagens de garrafa **[CONFIRMADO — dataset real e reconhecido, mas de domínio genérico]**. O Defect Spectrum no Hugging Face é outro benchmark granular de defeitos industriais com anotação semântica rica, também de domínio genérico industrial, não específico de garrafas **[CONFIRMADO — existe, domínio genérico]**.[11][12]

**Veredito para A.2, atualizando a estratégia de dataset já definida na Seção 4.2 (não reaberta, apenas reforçada com evidência):** nenhum dataset público encontrado cobre de forma confirmada e específica as 3 classes exatas do projeto. Isso valida — com evidência de busca real, não apenas suposição — a decisão já tomada de fotografia própria para tampa (ausente/mal rosqueada) e peças impressas 3D para deformidade de corpo, usando os datasets públicos genéricos (MVTec AD, Water Bottle Defect-Level) apenas como **validação cruzada de metodologia de anotação e como dataset auxiliar de pré-treino/transfer learning**, nunca como fonte primária de imagens rotuladas para as classes do projeto.

### A.3 Benchmarks de modelos leves de visão na borda no Raspberry Pi 5

Um benchmark comparativo recente avalia YOLOv8 (Nano/Small/Medium), EfficientDet Lite e SSD MobileNet em Raspberry Pi 3/4/5, com e sem acelerador Coral TPU: SSD MobileNet V1 atinge a menor latência e consumo de energia, mas com a menor acurácia; YOLOv8 Medium atinge a maior acurácia ao custo computacional mais alto **[CONFIRMADO — paper com metodologia experimental explícita]**. Um estudo dedicado à quantização INT8 de YOLOv11n/YOLOv8n em Raspberry Pi 5 (8GB) com CPU em modo "performance" reporta ~13 FPS e latência média de 76,78 ms para o YOLOv11n quantizado, e ~7 FPS com 152,20 ms para o YOLOv11s — uma redução de ~46% de latência do nano frente ao small **[CONFIRMADO — números experimentais específicos, hardware idêntico ao do projeto]**. Uma análise de benchmarking prático (não peer-reviewed, mas com metodologia detalhada e reprodutível) reforça que 64-bit OS com kernel 6.6+, desabilitar swap, fixar o CPU governor em "performance" e usar quantização INT8 (ganho de ~3,2× de velocidade sobre FP32) são pré-requisitos práticos para inferência estável no Pi 5 **[LIKELY — fonte não acadêmica, mas tecnicamente consistente com os benchmarks acadêmicos citados]**.[13][14][15][16]

**Implicação direta para o projeto:** um classificador leve tipo YOLOv8n/YOLOv11n quantizado em INT8, ou um pipeline equivalente de Edge Impulse, é o patamar de modelo correto para os 3 classificadores por vista (topo, lateral 1, lateral 2) — rodando três instâncias sequenciais (não simultâneas, já que a decisão de vista é por captura discreta via trigger, não streaming contínuo) no Pi 5, a latência somada de ~3×77ms (~230ms) permanece dentro da meta de latência de decisão por item de <500ms definida no relatório anterior, com margem confortável.[16]

### A.4 Câmeras USB UVC baratas no varejo brasileiro e caminho físico das 3 câmeras

A pesquisa de mercado confirma webcams USB UVC de 5MP disponíveis no Mercado Livre em faixas de preço que vão de ~R$ 65 a ~R$ 280, dependendo de marca e recursos (autofoco, microfone embutido) **[CONFIRMADO — preços reais coletados]**: uma webcam de 5MP "para videoaula" custa R$ 64,99, uma webcam 5MP 1080p genérica está listada sem preço fixo claro mas na mesma faixa, e uma webcam de marca (Dahua) 5MP UVC custa R$ 280,27 — acima do teto do projeto. Um módulo de câmera USB industrial de 5MP/30FPS também foi localizado, sem preço explícito capturado, mas descrito com especificações compatíveis com uso em bancada fixa **[CONFIRMADO — existe no varejo]**. **Recomendação de compra:** a opção de ~R$ 65 identificada cabe com folga no orçamento de ≤R$250, deixando margem para uma eventual segunda unidade reserva ou acessório de montagem — evitar a opção de marca Dahua por exceder isoladamente quase o teto total do orçamento adicional.[17][18][19][20]

Sobre compatibilidade: a documentação oficial do Raspberry Pi confirma que câmeras CSI são detectadas e controladas via `libcamera`, com o parâmetro `camera_auto_detect` no `config.txt` controlando a detecção automática — não há menção a limite de banda que impeça uma câmera USB UVC adicional operando em paralelo via v4l2, já que USB e CSI são barramentos independentes **[CONFIRMADO — fonte oficial, ainda que não trate do caso combinado explicitamente]**. Um tópico do fórum oficial Raspberry Pi sobre "USB bandwidth" no Pi 5 recomenda usar `lsusb -t` para confirmar a topologia de conexão e distribuir câmeras entre portas USB 2.0 e USB 3.0 quando há múltiplas câmeras USB — não é o caso aqui (apenas 1 USB + 2 CSI), mas confirma que o Pi 5 tem headroom de banda USB suficiente para uma única câmera UVC adicional sem risco de gargalo **[CONFIRMADO — fonte oficial do fórum, cenário testado é mais exigente que o do projeto]**. **Veredito: a arquitetura 2×CSI + 1×USB definida na Seção 4.3 é tecnicamente viável sem gargalo de banda relevante**, desde que a captura seja por trigger discreto (não streaming de vídeo contínuo em 3 canais simultâneos), o que já é o modelo de operação adotado pelo projeto.[21][22]

### A.5 Alternativas inteligentes de baixo custo para estabilizar a inspeção

Nenhuma busca adicional específica sobre iluminação controlada/marcadores foi necessária além do raciocínio de engenharia já estabelecido na literatura de visão industrial consultada — mas vale registrar como recomendação técnica derivada do conjunto de fontes revisadas: os LEDs RGB do inventário podem ser usados como iluminação de referência fixa e padronizada no ponto de captura (reduzindo variância de exposição entre capturas, um fator crítico de estabilidade citado implicitamente em todo o benchmarking de modelos leves revisado, já que variação de iluminação é uma das causas mais comuns de queda de acurácia em classificadores leves quantizados) **[LIKELY — inferência de engenharia bem fundamentada, não citação direta de paper]**.

## PARTE B — Relatório de Escopo e Critérios de Pontuação

### B.1 Escopo Mapeado (MVP 2 meses)

| Semana | Entrega incremental | Ancoragem SOTA/técnica |
|---|---|---|
| 1-2 | Requisitos formalizados (U1): KPIs testáveis, diagrama de arquitetura, delimitação de escopo por escrito, mapeamento de datasets públicos avaliados e descartados (com justificativa, citando A.2) | Documentar por que MVTec AD/Water Bottle Defect Dataset foram avaliados e não adotados como fonte primária[11][7] |
| 2-3 | Construção do rig de trilho deslizante com encoder KY-040; captura inicial de dataset próprio (topo) | — |
| 3-4 | PoC 1: classificador de topo (tampa) quantizado INT8, item parado | Modelo classe YOLOv8n/YOLOv11n quantizado, latência esperada ~77ms por inferência[16] |
| 4-5 | Construção física das 2 câmeras laterais (1 CSI adicional se orçamento permitir + 1 USB UVC ~R$65)[20]; PoC 2: classificador de deformidade, item parado | Validar captura simultânea 2×CSI+1×USB via trigger discreto[21][22] |
| 5-6 | PoC 3: sincronização no trilho com medição de throughput real via encoder; late fusion por votação entre as 3 vistas | Late fusion por votação/maior risco entre vistas, técnica validada na literatura[3][2] |
| 6-7 | Nós distribuídos (Heltec + BitDogLab) publicando via MQTT; hub com SQLite; PoC 4 (correlação multi-nó) | — |
| 7-8 | Testes de resiliência (reconexão, debounce, watchdog, buffer local, fallback LoRa); dashboard mínimo; polimento de documentação e pitch | — |

### Fora do MVP (justificado por U1, reforçado por SOTA)

- **Early fusion / concatenação de features multi-view com rede de atenção (ex. VAAA):** tecnicamente superior em papers recentes, mas exige calibração geométrica entre câmeras e treinamento de rede de atenção — esforço incompatível com 2 meses e com o hardware sem acelerador dedicado.[4]
- **Anomaly detection few-shot/contrastivo:** linha de pesquisa relevante e citável na fundamentação teórica, mas implementá-la troca classificação supervisionada simples e defensável por uma técnica de maior risco de execução sem dataset amplo — reservado como extensão pós-defesa.[6][5]
- **Aceleradores dedicados (Coral TPU, Hat de IA):** benchmarks mostram ganho de eficiência para SSD/EfficientDet mas não estão no inventário nem no orçamento — usar apenas quantização INT8 em CPU, que já atinge latência compatível com a meta do projeto.[14][13][16]

### B.2 Critérios de Pontuação Derivados

| Dimensão | Peso implícito | Como a pesquisa SOTA reforça o critério |
|---|---|---|
| KPI testável (U1) | Alto | Throughput real medido via encoder no rig (não estimado) é evidência de rigor experimental equivalente ao padrão de benchmarking encontrado nos papers revisados[16][13] |
| Resiliência (U4) | Alto | Late fusion por votação tolera falha de 1 câmera sem colapso total — propriedade documentada na literatura de ensemble multi-câmera[2], deve ser testada e demonstrada explicitamente na banca |
| PoC isolando maior risco (U2) | Médio-alto | Sequência de PoCs alinhada ao princípio de isolar a variável de maior incerteza técnica antes de integrar |
| Documentação (U3) | Médio-alto | Proveniência de dataset e justificativa de descarte de datasets públicos avaliados é evidência de rigor de pesquisa, citável com URLs reais |
| Pitch/valor (U3) | Médio | Conectar "rastreabilidade por item" a recall direcionado e defesa contra devolução continua sendo o gancho de valor de negócio |
| Escolha de modelo leve fundamentada (Edge AI real) | Médio-alto | Citar benchmark real de latência/acurácia do modelo escolhido (não "modelo pronto" genérico) demonstra decisão técnica informada, não commodity |

### B.3 KPIs por Classe de Defeito e por Rastreabilidade

| Classe/Capacidade | Métrica | Meta MVP | Fonte de calibração |
|---|---|---|---|
| Tampa ausente | Acurácia de classificação binária | ≥ 95% | Dataset próprio, validado contra literatura de late fusion[1] |
| Tampa mal rosqueada | Acurácia (3 classes) | ≥ 90% | Idem |
| Deformidade de corpo | Acurácia binária + erro dimensional | ≥ 90% classificação; erro < 5% | Peças 3D com deformação controlada; validação cruzada com MVTec AD como benchmark metodológico[11] |
| Latência de decisão por item | Tempo trigger → 3 inferências → registro | < 500ms | Latência medida de modelo quantizado ~77ms/inferência × 3 vistas sequenciais + overhead de I/O[16] |
| Throughput real do rig | Peças/min sustentado com acurácia mantida | Medido via encoder KY-040, não estimado | — |
| Correlação por item (multi-nó) | % de itens com registro consistente entre nós | ≥ 98% | — |
| Integridade do registro | % de eventos sem perda sob teste de estresse de 30 min | ≥ 99% | — |
| Retransmissão/resiliência de rede | % de eventos bufferizados entregues após reconexão | 100% | Propriedade de tolerância a falha de fusão multi-view reforça robustez geral do sistema[2] |
| Tempo de detecção de nó offline (watchdog) | Latência de sinalização | < 10s | — |

### B.4 Arquitetura Recomendada

Fluxo de dados: sensor de passagem (E18-D80NK/VL53L0X) dispara captura simultânea nas 3 câmeras (2 CSI + 1 USB UVC) → cada vista alimenta seu classificador leve quantizado (INT8, arquitetura classe YOLOv8n/YOLOv11n ou pipeline Edge Impulse equivalente) → late fusion por votação decide o resultado final por item → publicação via MQTT ao hub → persistência em SQLite (schema: item_id, timestamp, ponto_linha, tipo_defeito, vista_origem, confianca, caminho_evidencia, status_transmissao) → dashboard mínimo local. Nós distribuídos (Heltec ESP32-S3 + 2× BitDogLab) operam em estrela, publicando telemetria complementar (contagem, RTC, ambiente) com fallback LoRa SX1262 para o Heltec.[3][2][16]

A decisão de não fazer reconstrução 3D densa é agora tecnicamente reforçada pela literatura: mesmo papers de ponta em fusão multi-view industrial usam late fusion sobre classificadores 2D independentes, não reconstrução geométrica 3D, para o problema de detecção de defeito — a reconstrução 3D é empregada em domínios distintos (ex. medição dimensional de precisão milimétrica), não em classificação de presença/ausência de defeito estrutural visível.[1][3]

### B.5 Plano de PoCs Fatiado

| Ordem | PoC | Pergunta binária | Go/no-go | Duração |
|---|---|---|---|---|
| 1 | Classificador de topo, item parado | Acurácia preliminar ≥ 90%? | Go se ≥90%; senão revisar dataset | 3-5 dias |
| 2 | Classificador de deformidade multi-view, item parado | Acurácia preliminar ≥ 85%? | Go se ≥85% | 4-6 dias |
| 3 | Sincronização no trilho com encoder | Captura das 3 vistas dentro de janela <100ms, throughput real medido sem queda de acurácia >5pp? | Go se estável | 4-6 dias |
| 4 | Correlação multi-nó | ≥98% de correlação correta em teste de 50 itens? | Go se ≥98% | 3-5 dias |
| 5 | Integração estrela completa | Hub persiste todos eventos sob carga do throughput-alvo, sem perda em 10 min? | Go se sem perda | 4-6 dias |
| 6 | Resiliência (falha de câmera, reconexão, debounce, watchdog) | Sistema se recupera de queda de 1 câmera/nó sem crash, mantendo decisão via late fusion degradada?[2] | Go se recupera em todos os cenários | 5-7 dias |

### B.6 Riscos de Escopo (Top 5)

| Risco | Mitigação |
|---|---|
| Sincronização multi-câmera | Trigger físico único disparando as 3 capturas; validado no PoC 3 com o rig de trilho e encoder |
| Rolling shutter/motion blur no trilho | Captura com item momentaneamente parado ou velocidade controlada validada empiricamente no PoC 3 |
| Correlação de item entre nós | RTC dedicado (DS3231) + ID sequencial gerado no trigger, testado isoladamente no PoC 4 |
| SPOF do hub central | Buffer local (microSD) por nó + watchdog no hub, testado no PoC 6 |
| Dataset insuficiente/não representativo | Estratégia mista já validada contra ausência de dataset público específico às 3 classes[7][11] — fotografia própria + peças 3D + augmentação secundária, com proveniência documentada |

### B.7 Racional de Pontuação

A adoção de late fusion por votação em vez de reconstrução 3D ou early fusion complexa é simultaneamente a decisão de menor risco de execução em 2 meses e a decisão mais alinhada à literatura revisada sobre inspeção multi-view industrial, o que fortalece diretamente a nota de "relevância Edge AI" dentro dos 60% práticos, pois demonstra que a arquitetura foi escolhida com base em estado da arte real, não em suposição. A escolha de modelo leve quantizado com latência documentada por benchmark específico no mesmo hardware do projeto (Pi 5, INT8, ~77ms) substitui a alegação genérica "modelo roda rápido na borda" por um número rastreável a uma fonte, exatamente o padrão de rigor que U1 exige e pune sua ausência.[2][3][16][1]

A tolerância a falha de câmera inerente ao late fusion — resultado documentado na literatura de ensemble multi-câmera — torna o teste de resiliência do PoC 6 uma demonstração natural da arquitetura, não um patch adicional; isso maximiza os 30% de acompanhamento porque a evolução semana a semana no repositório mostra decisões de arquitetura sendo tomadas com base em evidência de pesquisa (datasets avaliados e descartados com justificativa, benchmarks citados, técnicas mais avançadas mencionadas mas conscientemente postergadas), sinal direto de proatividade técnica madura e não apenas execução mecânica de tarefas.[2]