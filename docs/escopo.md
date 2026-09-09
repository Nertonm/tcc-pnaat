# Escopo do projeto

## 1. Contexto e objetivo

O projeto endereça um cenário de inspeção de envase no qual garrafas podem chegar à etapa final com tampa ausente, tampa mal rosqueada ou deformidade no corpo. Essas ocorrências podem contribuir para retrabalho, separação de itens, investigação de lotes e perda de eficiência, mas seus impactos industriais não serão medidos nesta bancada.

A solução proposta utiliza inspeção multi-view, com uma vista superior e duas vistas laterais, sem reconstrução 3D densa, e rastreabilidade por item. O nó de visão realiza a captura e o processamento das evidências, enquanto o hub centraliza persistência, telemetria e consulta em topologia estrela. A decisão final é organizada nos domínios da tampa e do corpo e associada ao mesmo `item_id`.

O protótipo é uma bancada de teste em escala reduzida. A extrapolação industrial é apresentada como caminho de escalonamento, não como resultado demonstrado.

## 2. Posições de escopo

As posições abaixo distinguem decisões já adotadas, componentes candidatos e requisitos condicionais. Uma direção adotada orienta o desenvolvimento, mas não representa resultado validado. Questões dependentes de ensaio permanecem abertas até que a PoC correspondente produza evidência e decisão registrada em `docs/DECISIONS.md`.

1. **Bancada de teste** utilizar trilho deslizante artesanal com carrinho em velocidade controlada, documentado como bancada em escala reduzida. O E18-D80NK será ensaiado como sensor fotoelétrico de reflexão difusa candidato ao trigger. O KY-040 será ensaiado como mecanismo incremental candidato para medição de movimento. A adequação dos dois componentes, o acoplamento mecânico, a repetibilidade e os critérios de substituição serão avaliados na PoC 03. O uso do VL53L0X como validação ou fallback não integra o núcleo enquanto sua função não estiver definida em decisão específica.

2. **Dataset** utilizar fotografia própria para tampa ausente e tampa mal rosqueada e peças impressas em 3D com deformações controladas para o corpo. Datasets públicos podem apoiar a validação metodológica, mas não substituem a coleta representativa da bancada. Cada imagem deve preservar proveniência, classe, vista, setup e divisão entre treino, validação e teste.

3. **Câmeras** utilizar duas câmeras CSI e uma câmera USB UVC como direção de implementação, condicionada à validação de largura de banda, disponibilidade das três vistas, janela temporal e compatibilidade com o trigger na PoC 03. A captura deve preservar a identificação da câmera, o timestamp, a qualidade e a disponibilidade de cada vista. Iluminação pulsada e difusor permanecem alternativas condicionais, não premissas validadas.

4. **Fusão multi-view por domínios** utilizar um classificador por vista, com a vista superior decidindo isoladamente o domínio da tampa e as duas vistas laterais fornecendo evidências para o domínio do corpo. Não existe maioria global entre as três câmeras. Defeito detectado em qualquer domínio reprova o item, e um domínio não pode cancelar defeito detectado pelo outro. A regra definitiva para combinar as duas vistas laterais e tratar discordância permanece pendente das PoCs 01 e 02.

5. **Evidência insuficiente** quando nenhum defeito tiver sido detectado, mas uma evidência necessária estiver ausente, inválida ou abaixo dos critérios mínimos de qualidade ou confiança, o resultado deve permanecer `inconclusivo`. Vista ausente, baixa qualidade, baixa confiança ou discordância lateral não resolvida não podem ser convertidas em aprovação silenciosa.

6. **Nós da demonstração** utilizar sensores físicos, um nó de visão e um hub central em topologia estrela. O número definitivo de sensores e a distribuição dos serviços devem respeitar a arquitetura e os contratos de interface aprovados. Captura, classificação, persistência, telemetria e atuação devem permanecer observáveis de forma independente.

7. **Separação com análise humana** utilizar mecanismo no fim do trilho para direcionar o item reprovado ao caminho de análise manual, sem descarte automático. A decisão, a ordem de atuação, o movimento físico e a confirmação devem permanecer como estados distintos. A confirmação deve ser produzida por sensor independente e associada ao mesmo `item_id`. Tipo de atuador, modelo e interface do sensor, posicionamento, timeout e procedimento diante de falha serão validados na PoC 07.

8. **Recursos complementares do núcleo** manter o kit de golden samples, a rastreabilidade por item, a persistência, a telemetria, o dashboard e a separação confirmada. A medição dimensional da tampa permanece condicionada à calibração e à validação do erro no setup. Marcação visual por LED ou bandeirola pode ser utilizada como sinalização, mas não substitui os estados registrados pelo sistema.

9. **Camada evolutiva de descritores** descritores geométricos por vista e score de anomalia podem ser avaliados como camada adicional, sem substituir os classificadores dos domínios da tampa e do corpo. Sua inclusão depende de ganho mensurável, taxa aceitável de falsos positivos e orçamento de latência definidos antes do ensaio.

10. **Detector evolutivo de anomalia** o treinamento autossupervisionado com imagens normais e transformações sintéticas versionadas permanece como evolução. Método, métrica, população de validação, alvo de desempenho e orçamento de latência devem ser definidos antes da PoC. O detector deve produzir score separado e não pode cancelar uma reprovação produzida pelo núcleo.

11. **Destilação professor-aluno** a produção de modelo aluno quantizado para o Raspberry Pi 5 permanece condicionada à validação prévia do modelo professor e do detector evolutivo. Latência, consumo de memória, perda aceitável de qualidade, runtime e fallback devem ser medidos no hardware-alvo antes da inclusão.

12. **Expansão do dataset** supervisão fraca e sinais produzidos pelo sistema podem apoiar uma expansão futura do dataset, desde que cada rótulo preserve origem, função de rotulagem, peso, incerteza, conflitos e política de revisão humana. Nenhum rótulo automático deve ser promovido a confirmado sem rastreabilidade.

13. **Relatório de lote** o relatório em PDF permanece como evolução condicionada à conclusão do núcleo e à disponibilidade de prazo. Caso implementado, deve apresentar identificação do lote, indicadores, severidade, evidências e qualidade dos dados sem preencher campos ausentes com valores inventados. O dashboard e os registros consultáveis constituem o fallback.

14. **Iluminação sincronizada** iluminação pulsada sincronizada ao trigger e o uso de difusor permanecem alternativas condicionadas à PoC 03. O circuito deve possuir limitação de corrente e interface de acionamento dimensionada. Intensidade, duração, canais, saturação, reflexos, uniformidade, consumo e temperatura devem ser avaliados no setup. A ativação simultânea dos canais RGB em potência máxima não deve ser presumida como iluminação branca adequada.

15. **Estabilidade mecânica e elétrica** utilizar painel rígido, suportes parafusados, gabarito de posicionamento, réplicas parametrizadas e conexões críticas fixadas de forma reproduzível. A estrutura deve preservar a geometria de captura dentro de uma tolerância definida antes do ensaio. Continuidade, polaridade, isolamento e estabilidade da calibração devem ser verificáveis.

16. **Rigor de processo** executar testes de resiliência como experimentos com hipótese, estado inicial, estímulo, impacto controlado, métrica e critério definidos antes da falha. Os resultados devem registrar recuperação, perdas, estados observados e decisão, inclusive quando a hipótese for rejeitada.

17. **Design for testability** aplicar controlabilidade e observabilidade de forma transversal em cada requisito, seguindo a sequência `fisica -> dados -> modelo -> teste -> documentacao`. Requisito sem entrada controlável, estado observável, falha explícita ou evidência reproduzível não pode ser considerado aceito.

18. **Separação entre núcleo e evolução** RF-13, RF-17, RF-18, RF-19, RF-21, RF-23 e RF-30 são requisitos condicionais. Eles não podem bloquear a validação do núcleo e somente entram na demonstração após aprovação da PoC aplicável, verificação do orçamento de desempenho e decisão registrada.

## 3. Indicadores e critérios de sucesso

Os valores abaixo são metas de engenharia. Nenhum deles representa resultado observado antes da execução do ensaio no setup documentado.

| Capacidade | Métrica | Meta |
|---|---|---|
| Tampa ausente | Acurácia binária com intervalo de confiança | Pelo menos 95% na população de teste documentada |
| Tampa mal rosqueada | Acurácia por classe com intervalo de confiança | Pelo menos 90% na população de teste documentada |
| Deformidade do corpo | Acurácia por classe com intervalo de confiança | Pelo menos 90% na população de teste documentada |
| Medição dimensional do corpo | Erro relativo no setup calibrado | Inferior a 5% da referência |
| Latência da decisão | Trigger válido até persistência da decisão final | Inferior a 500 ms no percentil definido antes do ensaio |
| Medição de movimento | Resolução, repetibilidade, pulsos falsos e perda de pulsos | Limiares definidos antes da PoC 03 |
| Throughput do rig | Peças por minuto calculadas a partir da medição física aprovada | Reportado somente após aprovação do mecanismo de medição |
| Correlação multi-nó | Itens corretamente associados | Pelo menos 98% em 50 itens e nenhuma associação cruzada |
| Integridade do registro | Eventos íntegros durante estresse | Pelo menos 99% em 30 minutos |
| Retransmissão após reconexão | Eventos aceitos no buffer e entregues sem duplicação lógica | 100% |
| Detecção de nó offline | Tempo entre último heartbeat e sinalização | Inferior a 10 segundos |
| Separação confirmada | Separações comandadas e fisicamente confirmadas | Pelo menos 99% e nenhum item normal separado na PoC 07 |

## 4. Arquitetura

A arquitetura de referência está em `docs/arquitetura.md`. O fluxo deve representar separadamente:

- item e sensor de presença candidato;
- debounce e geração do trigger pelo ESP32;
- mecanismo de medição de movimento candidato;
- captura das vistas `topo`, `lateral1` e `lateral2`;
- associação das imagens ao mesmo `item_id`;
- decisão do domínio da tampa;
- decisão do domínio do corpo;
- combinação final sem maioria global entre as três câmeras;
- estados `aprovado`, `reprovado` e `inconclusivo`;
- persistência e telemetria por MQTT;
- hub com SQLite e dashboard;
- ordem de separação;
- confirmação física por sensor independente;
- encaminhamento do item reprovado para análise manual.

O E18-D80NK e o KY-040 devem aparecer como componentes candidatos da PoC 03. O modelo e o posicionamento do sensor de confirmação permanecem abertos até a PoC 07.

O desenho representa uma especificação arquitetural. Captura, sincronização, latência, correlação, atuação, componentes candidatos e comportamentos de fallback dependem de verificação no hardware.

## 5. Plano de provas de conceito

| # | PoC | Pergunta binária | Critério de aprovação |
|---|---|---|---|
| 01 | Classificação da vista superior | O classificador preliminar de tampa alcança o limite definido no protocolo? | Pelo menos 90%, com amostra, divisão dos dados e matriz de confusão registradas |
| 02 | Deformidade multi-view | As vistas laterais alcançam o limite preliminar e permitem avaliar a regra do domínio do corpo? | Pelo menos 85%, com resultados por vista, discordância e erro dimensional documentados |
| 03 | Sincronização física | O trigger, as câmeras e o mecanismo de medição permitem associar as três vistas ao mesmo item dentro da janela definida? | Limiares definidos antes do ensaio, sem associação cruzada e com decisão registrada para E18-D80NK, KY-040 e iluminação |
| 04 | Correlação multi-nó | Os eventos de 50 itens são associados corretamente? | Pelo menos 98% e nenhuma associação cruzada |
| 05 | Integração em estrela | Os eventos preservam identidade e campos obrigatórios sob a carga definida? | Meta de integridade atingida, com perdas, duplicações e registros parciais classificados |
| 06 | Resiliência | As falhas controladas resultam em recuperação ou degradação explícita? | Nenhuma interrupção silenciosa e causa da falha preservada |
| 07 | Separação confirmada | O item reprovado é direcionado e confirmado no caminho de análise manual sem separar itens normais? | Pelo menos 99% das separações confirmadas e nenhum item normal separado |

Os protocolos completos estão em `docs/pocs/`.

## 6. Riscos principais

1. **Sincronização das câmeras** as três imagens podem ficar fora da janela temporal ou ser associadas ao item incorreto. Mitigação: trigger identificado, timestamps por vista, registro de disponibilidade e testes de ausência, atraso, duplicação e reordenação na PoC 03.

2. **Desfoque, rolling shutter e exposição** movimento e iluminação podem degradar as evidências visuais. Mitigação: comparar velocidades, exposições e geometrias de iluminação, preservando as configurações e os resultados observados.

3. **Correlação entre nós** atraso, duplicação ou reordenação de eventos pode causar associação cruzada. Mitigação: `item_id` estável, timestamps, política de janela temporal e fixtures controladas na PoC 04.

4. **Falha do hub ou da comunicação** perda de MQTT ou indisponibilidade do hub pode interromper persistência e observação. Mitigação: buffer local, retransmissão idempotente, heartbeat e estados `degradado` e `offline`, validados nas PoCs 05 e 06.

5. **Dataset não representativo** quantidade, variedade, iluminação ou separação inadequada entre treino e teste podem produzir métricas otimistas. Mitigação: proveniência por imagem, divisão versionada, classes controladas e registro do setup.

6. **Confiabilidade do E18-D80NK** transparência, conteúdo, posição, distância e fundo podem afetar a detecção por reflexão difusa. Mitigação: tratar o sensor como candidato, ensaiar as variações previstas na PoC 03 e manter alternativa de substituição. Anteparo ou fita refletiva podem ser testados apenas como arranjo experimental.

7. **Adequação do KY-040** resolução, contato mecânico, escorregamento, pulsos falsos ou perda de pulsos podem comprometer a medição contínua. Mitigação: deslocamentos conhecidos, repetições, ensaio nas velocidades previstas e alternativa por encoder mais adequado.

8. **Evidência insuficiente** vista ausente, imagem inválida, baixa qualidade, baixa confiança ou discordância lateral podem resultar em aprovação indevida. Mitigação: estado `inconclusivo`, causa explícita e proibição de aprovação silenciosa.

9. **Confirmação incorreta da separação** ordem de atuação pode ser confundida com movimento concluído ou associada ao item errado. Mitigação: estados independentes, sensor de confirmação, timeout, associação por `item_id` e validação na PoC 07.

10. **Iluminação inadequada** saturação, reflexos, baixa uniformidade, aquecimento ou consumo excessivo podem prejudicar as imagens e o hardware. Mitigação: comparar configurações, medir corrente e temperatura e tratar o difusor como alternativa candidata.

## 7. Metodologia

### Iluminação

Luz, câmera, superfície do item e geometria de captura devem ser avaliadas como um único sistema. No topo, devem ser comparadas configurações de backlight e campo claro difuso. Nas laterais, devem ser comparadas geometrias capazes de preservar contorno e evidências de deformidade.

A iluminação pulsada sincronizada ao trigger integra o RF-30 e permanece condicionada à PoC 03. Duração, intensidade e canais devem ser configuráveis. O circuito deve possuir limitação de corrente e interface de acionamento compatível com a carga.

O difusor integra as alternativas da configuração óptica, mas não deve ser tratado como solução obrigatória ou garantia de eliminação de hotspots. Cada configuração deve ser avaliada por imagens, histograma, regiões saturadas, uniformidade, reflexos, corrente, tensão, duração do pulso e temperatura.

Devem ser comparadas pelo menos duas geometrias por vista antes da fixação da configuração. A decisão deve registrar setup, parâmetros, imagens, medições e impacto na extração das evidências necessárias.

### Validação estatística

Acurácia reportada com intervalo de confiança (Wilson ou Clopper-Pearson), tamanho da amostra e setup. Calibração pixel em milímetro com artefato de referência no plano do item, por posição fixa de câmera.

### Rastreabilidade

Identificador de item no formato lote, data e sequência, inspirado no padrão GS1. Evento rastreável mínimo com timestamp, identificador do item, local ou etapa e responsável. Leitura de DataMatrix ou RFID fica fora do núcleo.

### Indicadores no pitch

Apresentar acurácia por classe com intervalo de confiança, falsos positivos e falsos negativos separados, latência da decisão, cobertura da rastreabilidade, correlação entre nós e microparadas observadas no rig.

O throughput somente deve ser apresentado como medido quando o mecanismo de medição tiver sido aprovado na PoC 03. Resultados da bancada não devem ser convertidos diretamente em PPM, OEE ou impacto industrial sem população, período e condições representativas.

Toda afirmação deve distinguir meta, resultado observado na bancada e hipótese de escalonamento.

### Documentação e processo

Decisões datadas com justificativa e evidência em `docs/DECISIONS.md`. Análise de modos de falha leve por PoC. Congelamento de escopo após a PoC 3 com checklist de aceite.

### Fora do escopo

Permanecem fora do núcleo:

- leitura operacional de DataMatrix ou RFID;
- integração completa com MES ou ISA-95;
- cartas de controle SPC;
- FMEA formal extenso;
- descarte automático sem análise humana;
- DMAIC completo;
- inspeção multimodal por visão e som;
- pipeline contínuo de retreinamento;
- validação em linha industrial real;
- declaração de impacto industrial baseada apenas nos resultados da bancada.

A separação física confirmada para análise manual permanece dentro do escopo. Os requisitos RF-13, RF-17, RF-18, RF-19, RF-21, RF-23 e RF-30 são extensões condicionais, conforme `docs/DECISIONS.md`.

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
