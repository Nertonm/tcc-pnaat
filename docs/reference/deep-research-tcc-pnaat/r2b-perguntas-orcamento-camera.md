<!-- preserve: deep research TCC PNAAT -->
<!-- fonte: paste do assistente (fora do repo): paste_2_213452.txt -->
<!-- sha256_origem: 0b505b1449fd4b1a1b62853b5114b4e3cb5422ed5492ea43100835fa77ca1cb2 -->
<!-- rodada: v2 — respostas pontuais (abordagem de pesquisa, orçamento de câmera) -->

## Respostas às Perguntas Pontuais

Confirmando as recomendações propostas, com ajuste no ponto 4 (orçamento de câmera):

1. **Pesquisa web com fontes verificáveis** — confirmado como abordagem correta; este addendum já aplica isso (datasets, hardware, custo real no BR).
2. **Esteira** — maquete/trilho deslizante com item em posição fixa ou baixíssima velocidade é a escolha tecnicamente correta para 2 meses; abaixo detalha-se o rig recomendado a partir do inventário disponível.
3. **Dataset** — proposta abaixo com prós/contras e fontes reais localizadas.
4. **Compra de câmeras** — 2× Pi Camera Module 3 padrão custam ~R$ 1.168 a R$ 1.298 cada no varejo brasileiro pesquisado, ou seja, ~R$ 2.300-2.600 para o par — muito acima do teto de ~R$ 400 sugerido. Isso muda a recomendação: ver alternativa de menor custo abaixo.[1]
5. **Nós na demo** — 2 sensores + 1 visão + hub é confirmado como suficiente e alinhado ao prazo.

## 1. Rig de Teste (Esteira) — Lacuna Crítica Resolvida

O inventário não contém motor, correia ou chassi de esteira. Para 2 meses, a solução tecnicamente defensável e documentável é um **trilho deslizante artesanal (maquete)**, não uma esteira industrial real:

- **Estrutura:** trilho de madeira/perfil de alumínio (ou impressão 3D) com um carrinho/deslizador que transporta o item de teste (garrafa/frasco de amostra) em velocidade controlada manualmente ou por um motor DC de baixo custo com controle PWM simples.
- **Encoder KY-040** (já no inventário) acoplado ao eixo de tração para medir velocidade real de deslocamento — permite calcular o throughput real (peças/min) a partir da velocidade do trilho e do espaçamento entre itens, dando ao KPI de throughput uma métrica física verificável, não estimada.
- **Trigger de posição:** o sensor E18-D80NK ou VL53L0X (ambos no inventário) fixado no ponto de captura, disparando quando o item cruza a posição — isso substitui a "esteira industrial" por um rig reproduzível e citável no relatório como "bancada de teste em escala reduzida", uma prática padrão em TCCs de automação com kit limitado.
- **Justificativa de escopo (U1):** documentar explicitamente que o rig é uma bancada de validação, não a esteira real da fábrica, e que a extrapolação para produção industrial é um item do roadmap pós-defesa — isso é honestidade de escopo, que a apostila recompensa mais que uma simulação inflada.
- **PoC 3 (sincronização com movimento)** deve ser reformulada com esse rig: medir a velocidade real via encoder, definir a janela de captura permitida antes que motion blur degrade a classificação, e reportar o throughput máximo que o rig sustenta com acurácia mantida — este é o número real a ser citado na demo, não os 60 peças/min do exemplo da apostila.

## 2. Dataset — Lacuna Mais Perigosa, Estratégia Proposta

Localizaram-se datasets públicos relevantes de inspeção de garrafas, incluindo um dataset de defeitos por nível de gravidade em garrafas de água no Kaggle e um dataset de detecção de garrafas voltado a visão computacional. Nenhum dos dois foi verificado em profundidade quanto a cobrir exatamente as 3 classes do projeto (tampa ausente, tampa mal rosqueada, deformidade de corpo) com anotação adequada — isso precisa ser validado manualmente antes de assumir uso direto.[2][3]

Estratégia recomendada, combinando as três abordagens por classe de defeito:

| Classe de defeito | Estratégia recomendada | Justificativa |
|---|---|---|
| Tampa ausente | Fotografia própria de peças reais (garrafas do dia a dia, com e sem tampa) + augmentação (rotação, brilho, escala) | Fácil de produzir em quantidade suficiente (50-100 imagens/classe) sem necessidade de dataset externo; alta fidelidade à câmera real do projeto |
| Tampa mal rosqueada | Fotografia própria, simulando rosqueamento parcial manualmente em amostras reais | Defeito difícil de encontrar em dataset público; produção manual controlada garante variação suficiente de ângulo de desalinhamento |
| Deformidade de corpo | Combinação de peças impressas em 3D com deformação proposital (mais realista, mas mais lento) + dataset público de defeitos de garrafa como complemento/validação cruzada[3] | Deformidades físicas reais (amassados) são difíceis de gerar por manipulação simples; impressão 3D permite variar o grau de deformidade de forma controlada e repetível para o teste de erro dimensional |

Geração sintética por deformação de imagem (warping 2D) é desencorajada como fonte primária porque não reproduz sombra/geometria real sob a iluminação da bancada — deve ser usada apenas como augmentação secundária sobre imagens reais já capturadas, nunca como substituto integral do dataset real. O agente/aluno deve documentar no repositório a proveniência de cada imagem (própria vs. pública vs. augmentada), o que reforça diretamente o critério de "repositório como produto" (U3).

## 3. Caminho Físico das 3 Câmeras no Pi 5 — Resolvido

O Raspberry Pi 5 possui dois conectores CSI de 22 pinos (CAM0 e CAM1), suportando nativamente 2 câmeras MIPI simultâneas sem hardware adicional. Para a 3ª câmera, existem três caminhos, com trade-offs claros:[4][5][6]

| Opção | Como funciona | Trade-off |
|---|---|---|
| **Adaptador multi-câmera (Arducam V2.2)** | Multiplexa até 4 câmeras MIPI em uma única porta CSI via GPIO | Câmeras operam sequencialmente, não simultaneamente[7][8] — inviável para captura sincronizada das 3 vistas no mesmo instante, que é requisito central do projeto |
| **Câmera USB UVC na 3ª posição (recomendado)** | 2 câmeras CSI oficiais (topo + 1 lateral) nos conectores CAM0/CAM1 nativos, + 1 câmera USB barata (UVC, ex. câmera USB 5MP disponível no varejo BR por ~R$ 90)[9] na 2ª lateral | Captura verdadeiramente simultânea (USB é canal independente de CSI); menor custo; pequena perda de qualidade/controle de exposição na câmera USB, irrelevante para classificação binária de deformidade |
| **Nó de visão separado por câmera** | Cada câmera em um Raspberry Pi/SBC próprio, publicando ao hub via MQTT | Resolve simultaneidade, mas exige hardware adicional (SBC extra) fora do inventário e adiciona complexidade de sincronismo de rede entre nós de visão — desnecessário dado que a opção USB resolve o mesmo problema com custo quase zero |

**Recomendação final:** 2 câmeras CSI nativas (a V1.3 5MP existente no topo + 1 câmera adicional nas laterais) e 1 câmera USB UVC de baixo custo (~R$ 90) na segunda posição lateral. Isso substitui a recomendação anterior de comprar 2× Pi Camera Module 3 (~R$ 2.300-2.600, incompatível com o teto de R$ 400), reduzindo o custo total de hardware adicional para uma única compra de ~R$ 90-150 (câmera USB) e opcionalmente 1× Pi Camera V2/similar de menor custo para a 2ª posição CSI se disponível mais barata que o Module 3.

## 4. Estratégia de Fusão Multi-View — Especificada

Para o nível de exigência de um TCC de 2 meses, a estratégia correta é **fusão por votação de decisões (late fusion) com classificadores independentes por vista**, não concatenação de imagens como canais:

- Cada vista (topo, lateral 1, lateral 2) alimenta seu próprio classificador leve, treinado apenas para as classes que essa vista consegue discriminar (topo: tampa ausente/mal rosqueada; laterais: deformidade de corpo).
- A decisão final do item é a união lógica das saídas: **item é marcado com defeito se qualquer uma das vistas aciona sua respectiva classe de defeito**, com o tipo de defeito registrado sendo justamente a saída da vista que disparou.
- Isso evita o erro de tratar 3 imagens desalinhadas espacialmente como "canais" de uma única entrada (que exigiria correspondência geométrica pixel-a-pixel entre vistas, inexistente aqui) e é tecnicamente equivalente a um ensemble de classificadores especializados por vista — abordagem padrão e defensável para bancas técnicas.
- Cada classificador de vista pode ser a mesma arquitetura leve (ex. pipeline compatível com Edge Impulse ou modelo quantizado classe MobileNet) treinado com dataset próprio por vista, o que também simplifica a Seção 2 do PoC (validar cada vista isoladamente antes de integrar a votação).

## 5. Fontes das Citações da Seção de Hardware do Relatório Anterior — Verificação

As referências de FOV/sensor citadas no relatório original correspondem a: especificação oficial do sensor IMX708 usado no Camera Module 3, página de produto oficial Raspberry Pi do Camera Module 3, comparativo técnico de modelos de câmera Raspberry Pi (rolling vs. global shutter), e página de produto da Pi Camera V1.3 original. Todas são fontes verificáveis e devem ser citadas dessa forma explícita no repositório do projeto, não apenas mencionadas genericamente.[10][11][12][13][14]