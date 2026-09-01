# Escopo do projeto

## 1. Contexto e objetivo

O projeto endereça o cenário de inspeção de envase: garrafas chegam à etapa final com tampa ausente, tampa mal rosqueada ou deformidade no corpo, causando paradas não programadas, desperdício de lote e queda de eficiência.

A solução proposta é inspeção multi-view (topo e duas laterais, sem reconstrução 3D densa) com rastreabilidade completa por item: saber quais itens passaram, com qual defeito e em qual ponto. A decisão é local por nó; a coleta é central em topologia estrela.

O protótipo é uma bancada de teste em escala reduzida. A extrapolação industrial é apresentada como caminho de escalonamento, não como resultado demonstrado.

## 2. Posições de escopo (a confirmar)

As posições abaixo orientam o desenvolvimento, mas permanecem abertas até a validação nas PoCs correspondentes. O registro completo de cada decisão, com opções e critérios de confirmação, está em `docs/DECISIONS.md`.

1. **Bancada de teste:** trilho deslizante artesanal com carrinho em velocidade controlada, encoder KY-040 para medição física de velocidade e trigger E18-D80NK ou VL53L0X no ponto de captura. A estabilidade e a repetibilidade são validadas na PoC 3.
2. **Dataset:** fotografia própria para tampa ausente e mal rosqueada, peças 3D com deformação controlada para deformidade de corpo, e datasets públicos genéricos apenas como validação metodológica. A proveniência é documentada por imagem. O dataset próprio é a direção forte.
3. **Câmeras:** duas CSI nativas (uma no topo) e uma USB UVC, dentro de orçamento indicativo. Captura por trigger discreto, não por streaming contínuo. Largura de banda e captura simultânea são validadas na PoC 3.
4. **Fusão multi-view:** um classificador por vista e votação para a decisão final. Não concatenar imagens como canais.
5. **Nós da demonstração:** dois sensores, um nó de visão e um hub, extensível.
6. **Separação com análise humana:** atuador no fim do trilho ejeta o item defeituoso para análise manual, não para descarte automático. A confirmação da ejeção é feita por sensor; falha de confirmação gera evento de qualidade registrado. O ciclo é detectar, separar, analisar, corrigir e registrar. Mecanismo, timeout e parada manual são validados na PoC 7.
7. **Diferenciais propostos:**
   - medida dimensional da tampa (pixel em milímetro com backlight), com limite dimensional e modelo como segunda camada, para decisão explicável;
   - kit de golden samples com defeitos conhecidos para injeção sob demanda na demonstração;
   - relatório de lote em PDF com indicadores, distribuição por severidade, evidências e tendência;
   - marcação de baixo risco na saída (LED por severidade e bandeirola), sem caneta física.
   Inspeção multimodal visão e som fica fora do escopo.
8. **Camada de generalização:** descritores geométricos clássicos por vista (momentos de Hu, compacidade, simetria, proporções) com score de anomalia calibrado sobre o conjunto de itens normais. A generalização é demonstrada somente nessa camada, com dois ou três objetos de teste, nunca no classificador específico. Backbones pesados de visão para detecção zero-shot ficam fora do escopo por inviabilidade na borda.
9. **Anomalia autossupervisionada:** treinar o detector apenas com imagens de itens normais, criando anomalias sintéticas por recorte e colagem de patch, no formato original de classificação binária real/sintético, sem autoencoder puro. A consistência entre vistas usa o score conjunto dos três classificadores.
10. **Destilação professor-aluno:** o modelo professor pesado roda somente no treino, em GPUs disponíveis; o modelo aluno leve e quantizado roda no Raspberry Pi 5. A latência do aluno no hardware alvo precisa ser medida antes de aceitar a camada; existe fallback documentado.
11. **Auto-supervisão a partir da estrutura física e estatística:** usar o sinal que o sistema já produz (defeito sintético, discrepância professor-aluno, regras de supervisão fraca, física do rig) para reduzir dependência de anotação manual. A validação física de timestamp (esperado pela distância e velocidade do encoder) entra no núcleo; o clustering de drift de captura fica condicionado a uma camada de anomalia estável.
12. **Rigor de processo:** testes de resiliência como experimentos com hipótese falsável e métrica definida antes da falha; revisão dos logs para cobrir combinações não exercitadas; commits estruturados desde o início.
13. **Estabilidade mecânica:** soldar conexões críticas em headers fixos com teste de continuidade; painel de base rígido com furos fixos para câmeras, trigger e encoder; suportes parafusados, jig de posicionamento e réplicas parametrizadas de deformidade; gabinetes por último.
14. **Design for testability como princípio orientador:** testabilidade igual a controlabilidade mais observabilidade. Ordem de execução consolidada: solda, painel, suportes, golden samples, schema e heartbeat, medida dimensional, anomalia autossupervisionada, destilação, dashboard, resiliência, relatório e commits estruturados.

## 3. Indicadores e critérios de sucesso

| Capacidade | Métrica | Meta |
|---|---|---|
| Tampa ausente | Acurácia binária | 95% ou mais, com amostra definida |
| Tampa mal rosqueada | Acurácia de três classes | 90% ou mais |
| Deformidade de corpo | Acurácia binária e erro dimensional | 90% ou mais; erro abaixo de 5% da referência |
| Latência de decisão por item | Trigger até registro | Abaixo de 500 ms |
| Throughput real do rig | Peças por minuto sustentado via encoder | Medido, não estimado |
| Correlação multi-nó | Itens com registro consistente | 98% ou mais |
| Integridade do registro | Eventos sem perda em estresse | 99% ou mais |
| Retransmissão pós-queda | Eventos bufferizados entregues | 100% |
| Detecção de nó offline | Tempo de sinalização | Abaixo de 10 s |

## 4. Arquitetura

A arquitetura de referência está em `docs/arquitetura.md`. O fluxo separa item, encoder e trigger; três câmeras e classificadores; fusão; ordem e confirmação de atuação; nós de telemetria; MQTT; hub com SQLite; dashboard, relatório e notificação.

O desenho é uma especificação. Composição física, payload MQTT, captura simultânea, gateway de fallback e estados do atuador ainda precisam de verificação.

## 5. Plano de provas de conceito

| # | PoC | Pergunta binária | Critério de aprovação |
|---|---|---|---|
| 1 | Classificador de topo | Acurácia preliminar atinge o limite? | 90% ou mais |
| 2 | Deformidade multi-view | Acurácia preliminar atinge o limite? | 85% ou mais |
| 3 | Sincronização no trilho | Três vistas na janela definida, sem queda de qualidade? | Estável |
| 4 | Correlação multi-nó | Associação correta em 50 itens? | 98% ou mais |
| 5 | Integração em estrela | Sem perda em carga controlada? | Sem perda |
| 6 | Resiliência | Falhas recuperam sem interrupção e com degradação explícita? | Recupera |
| 7 | Ejeção com confirmação | Defeito separado com confirmação e sem falsa ejeção? | 99% e zero |

Os protocolos completos estão em `docs/pocs/`.

## 6. Riscos principais

1. Sincronização multi-câmera: mitigada por trigger físico único, validada na PoC 3.
2. Rolling shutter e desfoque de movimento: validados com item parado ou baixa velocidade.
3. Correlação de item entre nós: relógio externo e identificador sequencial no trigger, validados na PoC 4.
4. Ponto único de falha do hub: buffer local e monitoramento, validados na PoC 6.
5. Dataset não representativo: estratégia mista com proveniência documentada.

## 7. Metodologia

### Iluminação

Luz e câmera formam um sistema conjunto. No topo, silhueta por backlight quando a geometria permitir, senão campo claro difuso. Nas laterais, campo escuro com LEDs em ângulo raso para realçar a deformidade. Luz pulsada sincronizada ao trigger para reduzir desfoque. Testar ao menos duas geometrias por vista e registrar o comparativo antes de fixar a configuração.

### Validação estatística

Acurácia reportada com intervalo de confiança (Wilson ou Clopper-Pearson), tamanho da amostra e setup. Calibração pixel em milímetro com artefato de referência no plano do item, por posição fixa de câmera.

### Rastreabilidade

Identificador de item no formato lote, data e sequência, inspirado no padrão GS1. Evento rastreável mínimo com timestamp, identificador do item, local ou etapa e responsável. Leitura de DataMatrix ou RFID fica fora do núcleo.

### Indicadores de fábrica no pitch

Acurácia como componente de qualidade, throughput via encoder como desempenho, falsos negativos como proxy de PPM, cobertura de rastreamento e micro-paradas como disponibilidade. Toda afirmação é qualificada como medida na bancada reduzida.

### Documentação e processo

Decisões datadas com justificativa e evidência em `docs/DECISIONS.md`. Análise de modos de falha leve por PoC. Congelamento de escopo após a PoC 3 com checklist de aceite.

### Fora do escopo

DataMatrix real, MES ou ISA-95 completo, cartas de controle SPC, FMEA formal extenso, automação de rejeição autônoma, DMAIC completo e pipeline de re-treinamento contínuo. Esses temas são citados como conceito ou extensão.

## 8. Referências

### Detecção e fusão multi-view

- Multi-View Camera System for Variant-Aware Autonomous Vehicle Inspection and Defect Detection, arXiv 2509.26454.
- Ensemble Learning for Fusion of Multiview Vision with Occlusion and Missing Information, arXiv 2301.12592.
- Multi-View Industrial Anomaly Detection with Epipolar Constrained Cross-View Fusion, arXiv 2503.11088.

### Anomalia e autossupervisão

- CutPaste: Self-Supervised Learning for Anomaly Detection and Localization, CVPR 2021.
- Natural Synthetic Anomalies (NSA), ECCV 2022.
- Self-Supervised Anomaly Detection: A Survey and Outlook, arXiv 2205.05173.
- Autoencoders for Anomaly Detection are Unreliable, arXiv 2501.13864.

### Modelos e edge

- A Comprehensive Evaluation of Deep Learning Object Detection Models on Heterogeneous Edge Devices, arXiv 2409.16808.
- A Case Study in Deploying Weak Supervision at Industrial Scale, SIGMOD 2019.
- Documentação oficial do Raspberry Pi, seção de software de câmera.

### Datasets

- MVTec AD, benchmark de detecção de anomalia industrial.
- Water Bottle Defect-Level Detection Dataset, Kaggle.

### Visão industrial e iluminação

- A Practical Guide to Machine Vision Lighting, NI/Emerson.
- Illumination Geometries and Techniques, Opto Engineering.
- Bright Field vs Dark Field, Advanced Illumination.
- Machine Vision Lighting Guide, Roboflow.

### Padrões e indicadores

- GS1 Global Traceability Standard.
- How to Calculate OEE, Scrap Rate, FPY, sharpenmfg.
- ISO 2859-1, referência conceitual para a taxonomia de defeitos.
