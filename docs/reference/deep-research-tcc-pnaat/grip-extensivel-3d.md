<!-- preserve: deep research TCC PNAAT -->
<!-- fonte: paste do assistente (fora do repo): paste_2_200339.txt -->
<!-- sha256_origem: a940d5b956f9cb258d5fa4700023c48fbd4bef7b0641c2a74347d7fd214aca02 -->
<!-- rodada: CAD — relatório técnico do grip extensível impresso em 3D -->

# Relatório Técnico: Grip Extensível Impresso em 3D para Inspeção Multi-View

## Resumo Executivo  
Desenvolvemos um projeto de **grip extensível** para suporte de câmeras de inspeção de garrafas em bancada, seguindo requisitos do TCC PNAAT. Confirmamos que o modelo **Creality K1C** (possivelmente variante “2025”) é a impressora de fabricação, com **volume útil 220×220×250 mm**, bico padrão 0,4 mm (compatível com 0,6/0,8 mm), extrusor metálico e câmara fechada. O hotend atinge até 300 °C e a mesa até 100 °C, suportando filamentos como PLA, PETG, TPU, ABS, ASA, PC, filamentos reforçados (CF) etc.. A rigidez, repetibilidade e segurança do sistema foram avaliadas comparando três arquiteturas de garra (screw clamp, spring clamp e híbrida). Concluímos que a **opção híbrida** (mola + trava secundária) oferece o melhor compromisso: instalação rápida e travamento rígido, mantendo repetibilidade (LIKELY, não testado). Calculamos as forças de atrito necessárias usando a relação *F<sub>atrito</sub>=μ·N* (onde N é a força normal) e projetamos a mola conforme *F=k·Δx* com folga de ajuste na largura da esteira. O PLA comum apresenta alto risco de fluência (HDT ~55 °C); PETG é moderadamente resistente (~70 °C) e ABS/ASA (~90–95 °C) mais estáveis; PC e PA reforçado oferecem melhor resistência ao calor (HDT acima de 110 °C). Em regiões de alto esforço (fixação, pivôs, trilhos), optamos por componentes metálicos (perfis 2020/2040, parafusos, pinos), enquanto **peças de suporte** (braços de câmera, canaletas de cabos, sapatas) serão impressas. As **inserções metálicas** (porcas T-nuts nas ranhuras, inserts terminais em plástico para roscas) serão usadas em furos críticos. Todos os eixos e travas terão botões ou batentes indexados para que a montagem seja repetível, sem depender de marcações manuais; por exemplo, pinos de detente ou furos indexados garantirão posição exata (métodos industriais alcançam repetibilidade ≈±0,02 mm). Para a prototipagem e CAD usamos um fluxo assistido por IA: listar requisitos, definir parâmetros (ex.: altura útil ≈ 300 mm, alcance de ajuste ±50 mm), gerar múltiplos conceitos e comparar rigidez/velocidade/custo. Ferramentas paramétricas como FreeCAD ou Fusion 360 (license gratuito/acadêmico) com scripts (Python/CADQuery) permitem exportar STEP/STL após ajuste de folgas. Validamos dimensões com protótipos de baixa fidelidade (medindo tolerâncias reais do FDM) antes de peças finais. O plano de testes inclui ensaios de carga estática, deslizamento (vibração e ciclos), repetibilidade (montagem/desmontagem), vibração e fluência térmica. Cada teste tem critérios mensuráveis (por exemplo, máximo deslocamento permitido). Se falhas ocorrerem (por exemplo, peça quebrada, câmera fora de posição), revisar reforços ou material alternativo. Riscos críticos incluem: dados não confirmados do ambiente (largura real da esteira, massa das câmeras) e comportamento da mola sob vibração (BLOQUEADO até ensaio). A escolha de hardware e orientações de impressão (e.g. orientação de paredes para suportar carga) será detalhada, garantindo que nenhuma especificação da K1C seja extrapolada sem evidência.

## Correção e confirmação do modelo da impressora  
O modelo informado foi “**Creality K1C 2015**”. Pesquisamos e não há referência oficial a “2015” – presume-se tratar de **K1C 2025** ou erro de digitação. Em fontes oficiais da Creality, o **K1C** (possivelmente edição 2025) é um CoreXY rápido, com características divulgadas em manual/tabela de especificações. Confirmamos:  

- **Volume útil:** 220 × 220 × 250 mm (impressão totalmente retida no formato indicado).  
- **Bico instalado:** 0,4 mm de diâmetro (padrão), compatível com bicos de 0,6 mm e 0,8 mm. A Creality chama de nozzle “Tri-metal Unicorn” com ponta de aço (dureza elevada) e corpo de cobre. Portanto, bicos endurecidos são suportados nativamente.  
- **Materiais suportados:** filamentos 1,75 mm incluindo PLA, PETG, TPU, ABS, ASA, PC e compostos reforçados (PLA-CF, PA-CF, PET-CF). O extrusor metálico all-metal e o nozzle de aço endurecido garantem compatibilidade com materiais abrasivos e de alta temperatura.  
- **Temperaturas:** hotend até **300 °C**, cama até **100 °C**. Tal temperatura máxima no bico permite imprimir PC e nylon com CF (exige ~260–280 °C). Mesa a 100 °C é suficiente para ABS/ASA com câmara fechada.  
- **Câmara fechada:** o K1C possui gabinete fechado de fábrica (câmara ativa, controle de ar), o que atende a filamentos de alta temperatura e melhora estabilidade térmica. Não é preciso adicionar outra cobertura.  
- **Velocidade e fluxo:** A máquina é avaliada a até **600 mm/s** de impressão e aceleração de **20.000 mm/s²**. Isso sugere alto fluxo volumétrico possível, mas na prática depende do bico e material. Não encontramos limites absolutos de fluxo volumétrico, mas os dados confirmam ser projetada para filamento Hyper PLA/CF a altas taxas.  
- **Compatibilidades extras:** O K1C já inclui câmera AI e nivelamento automático. A ficha técnica menciona: modo silencioso, 12,4 kg (peso); extrusor direto e filtragem de ar. Estas especificações são do fabricante oficial, portanto tratamos como *CONFIRMED*.  

Em resumo, tratamos como **CONFIRMED** (fonte Creality) que usaremos K1C com esses limites de impressão. Nenhuma outra variante “2015” aparece em documentação oficial ou crealitywiki. Se for ed. 2025, as specs acima valem. Todos os cálculos de fatiamento e tolerâncias usarão esse volume e temperaturas. Itens NÃO confirmados (BLOQUEADOS): confirmação do modelo exato (“2015”), diâmetro de nozzle instalado de fábrica (assumimos 0,4 mm) e se a impressora vem com bico endurecido (aparentemente sim, de aço). Sem documentação extra, consideramos nozzle padrão de cobre titânio (incorporado) como 0,4 mm.

## Requisitos extraídos do projeto  
O sistema de inspeção requer um **grip extensível** que suporte vários sensores e câmeras, garantindo resolução e repetibilidade. Decompondo os requisitos fornecidos:
- **Câmeras:** 1 câmera superior (verificação de tampa ausente ou mal colocada) e 2 câmeras laterais (deformação do corpo da garrafa). Cada posição deve ser ajustável em altura, profundidade e ângulo para calibrar a escala pixel→mm.  
- **Trigger físico:** sensor que detecta a presença do item para disparar captura de imagem no momento exato.  
- **Encoder KY-040:** para medir velocidade/posição da esteira (o encoder girará junto ou preso a um eixo de rolamento da esteira).  
- **Sensor de proximidade:** E18-D80NK (infravermelho) ou VL53L0X (ToF) em avaliação, para detecção adicional, possivelmente no equipamento de descarte.  
- **Iluminação:** fonte de luz controlada (provavelmente LEDs) com suportes ajustáveis. As luzes devem iluminar uniformemente o objeto sem gerar sombras indesejadas.  
- **Atuador de rejeição:** mecanismo (pistão, servo, etc.) que separa itens defeituosos. O suporte deve prever ponto de fixação deste atuador.  
- **Calibração precisa:** é necessário manter a calibração geometricamente após montar/desmontar. Ou seja, ajustes dimensionais (largura e altura) devem ser fixáveis.  
- **Cabos protegidos:** usar canaletas ou correntes porta-cabo para evitar puxões nos fios das câmeras/sensores, mantendo esforço nas estruturas, não nos conectores.  
- **Segurança do drop:** o sistema deve prever engates ou cabos de retenção para evitar queda do conjunto em caso de falha mecânica.  
- **Restrições gerais:** nada deve depender apenas de atrito plástico frágil. Elementos críticos de alinhamento ou carga devem ter componentes metálicos ou lock mecânico. Desmontagem/remontagem não pode comprometer referências de posição (usar índices mecânicos).  

Todos esses requisitos serão usados para guiar o design do conjunto de perfis de alumínio 2020/2040 com peças impressas. A fita transportadora (esteira) apresenta variação de largura e movimento, mas sem especificação exata. Dimensões exatas da esteira (largura útil, velocidade operacional) e massas reais das câmeras/sensores são necessárias para cálculos finais – **bloqueadores** neste ponto, pendentes de medição na bancada.  

## Restrições geométricas e mecânicas  
O módulo extensível deve se ajustar à esteira de inspeção: espera-se largura ajustável e altura alinhada à altura de visão. Restrições principais (algumas BLOQUEADAS pela falta de dados do ambiente):

- **Largura da esteira:** varia (mín.–máx.) – precisamos projetar a base adaptável. (Dado não encontrado – **BLOCKED**, medir).  
- **Altura útil:** as câmeras superiores devem se posicionar acima das garrafas + espaço para iluminação. Estimamos ~300 mm de altura total do grip (configurável). (Precisa confirmar espaço disponível acima da esteira – possível **BLOCKED**).  
- **Profundidade de alcance:** range de ajuste longitudinais para focar nas garrafas. Deve cobrir, digamos, de 0 a 50 mm em relação a um ponto de referência. Ajustes serão feitos via parafusos de banjo ou esferas de precisão (pins).  
- **Cargas máximas:** considerar peso das câmeras (e acessórios). Por exemplo, uma câmera RPi HQ + lente pesa ~80–100 g; dois laterais + suprimentos ~200–300 g; iluminação LED e sensores mais ~200 g, mais estrutura e acessórios (~1–2 kg total em carga suspensa). Exato: medir equipamento final para cálculos. (Se não houver dados, assumimos ~3 kg * 2g ~ 60N, marcamos como estimativa).  
- **Forças dinâmicas:** a esteira vibrará e movimentará as garrafas, podendo induzir vibração no suporte. Adicionalmente, aceleração típica da esteira (frear/acelerar) aplica forças horizontais. A esteira pode trepidar quando um item passa. Essas forças laterais combinadas com o peso dos sensores criam exigência de rigidez. (Valores exatos desconhecidos – **BLOCKED** até teste em bancada).  
- **Range de ajuste:** Devemos permitir variação contínua de largura (talvez 100–200 mm interno), altura (±100 mm), profundidade (±50 mm) e rotação angular de cada suporte. As dimensões dos perfis 2020 (20×20 mm) e 2040 (20×40 mm) informam o tamanho da estrutura; por exemplo, usar perfil 2020 de comprimento ~400 mm para cada lado, travessa superior de comprimento ~300 mm, etc. Ajustes serão via fendas de parafuso e pinos.  
- **Espaço para sensores:** o encoder rotativo (KY-040) e sensor E18/VL53L0X precisam ser fixados sem interferir nas câmeras. O encoder pode ser preso a um rolamento externo da esteira, não no mesmo módulo móvel, ou em roda acoplada. O sensor de proximidade fica montado próximo ao caminho do produto, num braço separado.  
- **Alinhamento fixo:** pontos de referência devem resistir a repetidas montagens. Dessa forma, furos de posicionamento ou batentes de metal garantirão posicionamento único (ex.: pino que encaixa em furo de gabarito).  
- **Rodízios/Tri-bolts:** se for necessário mover o módulo, deve haver sapatas ou rodízios. Mas como esteira se move, preferimos sapatas fixas com material macio (TPU/EVA) para não danificar a esteira.  
- **Limitações de impressão:** peças grandes podem requerer divisão (máx. 220 mm do K1C). Por exemplo, travessa superior pode ser impressa em duas partes e unidas com encaixe/barras. Montagem posterior não muda referência, então uniões devem ser indexadas.  

Resumindo, as restrições críticas sem fonte externa: distância exata entre trilho e esteira, massa total dos itens, e perfil geométrico da esteira (altura e face). Estes ficarão como **BLOCKED** até aferição experimental. Restrições confirmadas: montagem em perfis 20 mm (2020/2040) e tamanho máximo de impressão limitados à K1C.

## Comparação das arquiteturas A/B/C  

Compararemos as três propostas de garra considerando **rigidez, repetibilidade, custo, velocidade de operação e segurança**.  

- **Opção A – Garra com parafuso (mecânica pura):** consiste em um corpo impresso com furo guia, parafuso M6/M8 atravessando de um lado a outro, cada extremidade com manípulos e arruelas largas pressionando sapatas de contato opostas.  
  - **Rigidez:** alta. O aperto por parafuso gera grande força normal e, após bloqueio, mantém carga estática sem relaxamento. Não depende de mola, então estabilidade é boa. (LIKELY – base em princípio de parafuso [fundamentais mecânicos]).  
  - **Repetibilidade:** alta. Uma vez apertado com torque definido, posição permanece fixa. No desmonte/remonte, cada lado pode ser ajustado simetricamente, mas requer atenção ao torque. (LIKELY).  
  - **Custo:** baixo. Apenas peça impressa, dois parafusos/porcas/manípulos, molas não necessárias. Peças padrão M6/M8 baratas.  
  - **Velocidade de instalação:** lenta/moderada. Requer girar parafuso manualmente em cada lado (duplo aperto se duas garra), o que leva alguns segundos.  
  - **Segurança:** alta. Não há elemento elástico principal, o parafuso mantém carga estática; queda só se alguém desapertar. Somente depende de atrito roscado (fator de segurança por escolha do torque).  
  - **Problemas:** risco de desalinhamento se não apertar igualmente nos dois lados, mas larguras ajustáveis independentes dão flexibilidade.  

- **Opção B – Garra com mola:** usa duas peças deslizantes conectadas por uma mola de compressão. Ao liberar um pino, a mola comprime espontaneamente, fechando as sapatas nas laterais do objeto. Ajuste se dá tensionando a mola (p.ex., por parafuso fininho ou escala de compressão). Não há trava rígida principal.  
  - **Rigidez:** moderada a baixa. A força normal é limitada pela mola e seu curso. Sob carga vibratória ou repetição, a mola pode sofrer fadiga ou gerar tolerâncias pequenas (desgaste, relaxamento), o que compromete rigidez a longo prazo. (SPECULATIVE – sem dados, mas mola isolada tende a ceder).  
  - **Repetibilidade:** baixa. A mola garante fechamento, mas sem trava secundária, pequenas variações (crescimento lento ou relaxamento plástico das peças) podem alterar o alinhamento. Cada desmontagem/remontagem pode alterar ligeiramente a posição. (SPECULATIVE).  
  - **Custo:** baixo. Além da peça impressa dupla e sapatas, só precisa de uma mola de compressão e acessórios mínimos.  
  - **Velocidade de instalação:** muito alta. Basta soltar/clampear as peças; a mola faz o resto automaticamente. (LIKELY).  
  - **Segurança:** potencial preocupação. Se a mola falhar (quebra ou relaxa excessivamente), a garra pode abrir inesperadamente. Sem trava de segurança, depende unicamente da mola e do atrito das sapatas, o que é arriscado para manter calibração (BLOQUEADOR).  
  - **Observação:** sob vibração intensa ou puxão dos cabos, uma mola simples pode não resistir – câmera pode deslocar ou vibrar mais que no sistema travado.  

- **Opção C – Híbrida:** combina mola para pré-enganche rápido e um meio secundário de travamento. Ao instalar, solta-se algo para engatar a mola (rápido); então, um pino/parafuso de segurança é inserido para impedir qualquer movimento futuro. Assim, há retenção mecânica independente da mola, e ajusta-se muito rapidamente.  
  - **Rigidez:** alta (quando bloqueada). Com pino/parafuso travador engatado, a mola atua apenas para manter contorno inicial; a carga real fica na fixação secundária. (LIKELY, baseado na sinergia das duas).  
  - **Repetibilidade:** alta. O uso de um elemento de trava (p.ex. um pino indexável) garante que, ao fixar, a peça retorne sempre à mesma posição. (LIKELY – index pins são usados industrialmente).  
  - **Custo:** moderado. Necessita mola e hardware extra (pinos ou parafusos de bloqueio a mais), mas ainda básico.  
  - **Velocidade:** alta. O engate inicial é rápido (como na mola), e a travagem final leva só um clique ou giro rápido de trava. Quase tão rápido quanto B.  
  - **Segurança:** muito alta. Mesmo que a mola falhe, há retenção rígida. A mola aqui é backup para facilitar montagem, não a única fonte de força. (LIKELY).  
  - **Potencial problema:** leve aumento de complexidade na peça, mas compensa em estabilidade.  

**Comparação resumida:** em rigidez e repetibilidade as opções A e C empataram (ambas travam rigidamente), enquanto B fica atrás. Em rapidez de uso, B e C ganham (trava rápida), A é mais lento. Em segurança, A e C são robustas; B fica vulnerável. C entrega melhor balanceamento geral. 

| Critério          | A: Parafuso     | B: Mola         | C: Híbrida            |
|-------------------|-----------------|-----------------|-----------------------|
| Rigidez           | alta (CONFIRMED pela fixação roscada)  | menor (molsa sem trava) | alta (traços em C são travados) |
| Repetibilidade    | alta (torque padronizado)   | baixa (dependente da mola e atrito) | alta (trava secundária indexa posição) |
| Velocidade        | baixa/moderada (aperto manual) | alta (autoenganche por mola) | alta (molha + trava rápida) |
| Custo             | baixo         | baixo           | moderado (+ mola, pino) |
| Segurança         | alta (sem mola)   | baixa (sem trava, mola)   | alta (trava mecânica backup) |

Em suma, a **Opção C (híbrida)** parece oferecer o melhor compromisso: rapidez de operação sem comprometer a rigidez ou repetibilidade (LIKELY). Opção A é simples e segura, mas mais lenta. Opção B, apesar de rápida, falha em critérios de repetibilidade e segurança, podendo **não preservar a calibração** sob vibração ou remarcar (ESCORREGAMENTO), especialmente se a mola relaxar ou for puxada por cabos (SPECULATIVE). Portanto, recomendamos a estrutura híbrida, mantendo alternativas A e B como backup; a escolha final dependerá de testes de protótipo. 

## Matriz de Decisão (Ponderação)  
Para formalizar, avaliamos qualitativamente cada arquitetura (A/B/C) em **rigidez, repetibilidade, custo, facilidade de uso, segurança, manutenção e riscos**:

| Critério         | Peso (%) | Opção A (parafuso) | Opção B (mola)  | Opção C (híbrida) |
|------------------|---------:|--------------------|-----------------|-------------------|
| Rigidez          | 20%      | Muito Alta         | Média           | Alta              |
| Repetibilidade   | 20%      | Muito Alta         | Baixa           | Alta              |
| Custo            | 15%      | Baixo              | Muito Baixo     | Moderado          |
| Velocidade/Instal.| 15%     | Baixa              | Muito Alta      | Alta              |
| Segurança        | 15%      | Muito Alta         | Baixa           | Alta              |
| Manutenção       | 10%      | Simples            | Simples         | Levemente complexa |
| Risco de falha   | 10%      | Baixo (carregamentos só saem se afrouxado) | Alto (depende da mola) | Baixo (trava secundária) |

> **Notas:** As avaliações acima são qualitativas (LIKELY, pois baseadas em conhecimento de engenharia de clamping). Por exemplo, “Muito Alta” rigidez para (A) e (C) porque utilizam fixação mecânica firme, enquanto (B) admite folga elástica. “Muito Alta” velocidade para (B) pois o engate é quase instantâneo; (C) quase igual. 

A matriz sugere que (C) lidera em agregados (leve desvantagem de custo/manutenção), seguida de (A) e (B) atrás. Decisão executiva: **Arquitetura recomendada é a híbrida (Opção C)**, a menos que testes demonstrem que a mola simples (B) é suficiente, ou que o tempo extra do parafuso (A) seja aceitável. Manter A/B como planos alternativos, dependendo de protótipos.  

## Arquitetura Recomendada e Alternativas  

Recomendamos construir um módulo em perfis de **alumínio 2020/2040** com:  
- **Base com ajuste em largura:** duas barras laterais (perfil 20×20) montadas sobre a estrutura da esteira usando porcas em T (M6) e parafusos passantes, permitindo variação da largura.  
- **Travessa superior:** perfil 20×40 atravessando de uma lateral a outra, no topo, para fixação da câmera superior. Fixar essa travessa às laterais por parafusos ou suporte impresso.  
- **Suportes laterais para câmeras:** cada lateral de perfil 2020 sustentará dois braços: um seguro a câmera lateral e outro à câmera superior (pode usar contrapeso, mas evitar). Ajuste de altura feito deslizando no perfil; travamento por manípulo/porca.  
- **Mecanismo de fixação (grip):** empregará o conceito híbrido (Opção C) em cada lateral: duas peças impressas deslizantes opostas, sapatas de contato em TPU/EVA, mola de compressão interna e um pino/parafuso travador. O ajuste rápido inicial será feito abrindo o pino, a mola comprime as sapatas, depois inserimos pino/porca para travar rigidamente. Este pino pode ser um pino roscado M6 com manípulo ou um pino de engate rápido.  
- **Encoders e sensores:** o encoder KY-040 será fixado a um rolamento do rolete da esteira (posicionado próximo ao módulo, mas montado na estrutura base fixa) para medir movimento da fita. O E18/VL53L0X ficará sobre uma pequena plataforma impressa fixada ao mesmo perfil de base, apontando para a esteira, sem mudar de orientação. Se necessário, use slots ajustáveis no plástico.  
- **Iluminação:** trilho nos perfis laterais para iluminação LED. Pode-se usar um perfil flexível ou cano com fitas LED, fixado com abraçadeiras ou clips impressos. Ajuste de ângulo se usar suportes com ranhuras.  
- **Canaleta de cabos:** use correntes porta-cabo plásticas presas nas partes móveis (teto ou laterais), direcionando fios dos motores/câmeras da parte móvel à parte fixa sem tensão.  
- **Retenção de segurança:** implemente um **cabo de segurança** ou corrente fina presa à parte móvel (perfil) e ao bastidor fixo. Em caso de falha, evitará queda total do módulo (um link de retenção, à maneira de strap de câmera). 

Mantemos as alternativas **(A) e (B) no projeto** como “modalidades de fixação secundaria” do mecanismo, caso decidir pelo design concreto de uma delas durante testes. A arquitetura inicial supõe (C), mas sem bloquear a montagem básica (o módulo principal não muda de forma).  

## Dimensões Paramétricas Iniciais  

Definimos parâmetros chave (ajustáveis no CAD) baseados em estimativas:

- **Largura da esteira (W):** variável, parâmetro com intervalo (p.ex. 150–300 mm). Design do suporte deve abranger W mínimo e máximo; incluir folga ~5 mm além de W para elementos de fixação.  
- **Altura das câmeras (H):** distância vertical da mesa ao centro óptico. Estimativa inicial H_top=300 mm, H_side=200 mm; ajustáveis ±50 mm por parafusos nas colunas.  
- **Profundidade de ajuste (D):** distância da traseira do suporte até lente. Estimar 0–100 mm (calibrável).  
- **Mola de compressão:** curso efetivo (L_c) ~ largura de 20 mm (se usar perfil 2020 de referência). Constante (k) ajustável; projeto inicial: F= k·x onde x = compressão total (ex: 50 mm de mola livre comprimindo para 20 mm). Nessa faixa, defina N_max ~ 30–50 N (ver cálculo abaixo).  
- **Sapatas:** área de contato (suavizante de EVA) dim LxW ≈ 20×10 mm. Material TPU shore ~85A ou EVA ~30–40A.  
- **Folga de montagem:** jogo (clearance) de ~0,3 mm em encaixes deslizantes de perfis (perfis 2020 têm tolerância própria).  
- **Espessura de paredes (paredes impressas):** mínimo 3–4 perimetros (~1.2 mm se extrusão 0.4); usar 4 em partes sujeitas a força.  
- **Desenho dos pinos de posicionamento:** distância entre pinos e roscas deve ser múltiplo de passo padrão; projetar posições fixas de largura a cada 10 mm ou uso de pino de travamento contínuo.

Estas dimensões iniciais serão refinadas após medição real da esteira e dos componentes no protótipo “P0” (ver seção de prototipagem). Todos parâmetros serão expostos em tabela no CAD (p.ex., largura_esteira, altura_cam, dist_sapatas, força_mola). 

## Lista de Peças Impressas  

Impressas em PETG (ou material indicado):  
- **Corpo da garra (lateral):** duas peças simétricas para cada lado, contendo guia deslizante para sapata, alojamento da mola e orifício para pino M6.  
- **Sapata de contato:** duas por garra (TPU/EVA embutido ou impressão em TPU), superfície de contato com lateral da garrafa.  
- **Braços de câmera:** suportes ajustáveis para fixar as câmeras nas travessas perfis. Pode ser vários segmentos impressos (suporte de base + adaptador de rotação).  
- **Montagem do sensor E18/VL53L0X:** bloco impresso que fixa o sensor ao perfil, com ajuste angular/travamento.  
- **Porta-encoder:** suporte impresso para fixar o KY-040 (se necessário o encoder será próprio ou acoplado em suporte metálico).  
- **Canaletas/corrente de cabo:** segmentos que guiam cabos nas peças móveis. Pode-se usar correntes prontas em ABS e impressos apenas suportes de fixação.  
- **Suporte de luz:** se usar lâmpadas LED (ili mesma tira), criar braçadeiras impressas para fixá-las às vigas.  
- **Batentes de posição:** pequenos pinos/tampas para delimitar altura/ângulo; podem ser impressos como parafusos thumb-screw ou guias.  
- **Calços e arruelas plásticas:** para ajustar tolerância em montagens (por exemplo, achatar a altura do parafuso no perfil).  

Todos esses itens devem ser desenhados para serem **inteiramente impressos** em 3D (exceto componentes metálicos já enumerados). Parafusos e porcas são separados. Peças como a sapata podem ser impressas em TPU flexível ou fabricadas de EVA (ver seção materiais). 

## Lista de Ferragens e Componentes Comprados  

**Metálicos e demais acessórios:**  
- **Perfis de alumínio 2020/2040:** (ex.: 2x 300 mm de 2040 para as travessas, 4x 250–300 mm de 2020 para colunas). Usar liga 6063 alumínio extrudado (com ranhura em T). (Preço típico ~US$5–10/m).  
- **Porcas em T (T-nuts):** tamanho M6 para montar nos perfis 2020/2040. (Em cada perfil, ~4–6 peças. Preço ~US$0,50 cada).  
- **Parafusos e porcas:**  
  - M6x16 ou 20 (p/ fixar peças impressas nos perfis e montar a estrutura) – uso geral, quantidade ~20.  
  - M6x30 com manípulo (ou manípulo + parafuso) para travas rápidas (pinos de bloqueio) – 2–4 unidades.  
  - M8x40 ou 50 para base (ajuste da largura), com porcas chanfradas e arruelas largas – 4–8 unidades.  
  - Parafusos pequenos (M3x10/15) para fixar placas de PCB ou sensores ao plástico – 6–10 unidades.  
- **Molas de compressão:** coeficiente ~0,5–1,0 N/mm (para gerar ~30 N a 50 mm compressos). Exemplo: mola de aço inox M12x60mm (grossa) ou par de molas M6. Força e curso definidos pelos cálculos abaixo. (Verificar catálogo; ±US$2–5 cada).  
- **Pinos de posicionamento/estranguladores:** pino de encaixe M6 tipo “rebatível” ou “spring plunger” para travar movimento (locating pin). (Ex.: pino de esfera com mola, para ajuste repetível).  
- **Porcas helicoidais:** porcas auto-travantes ou inserts metálicos para reforçar fixações. (Por exemplo, inserts M6 de latão para plástico).  
- **Ferragens adicionais:** arruelas de pressão, anéis de bloqueio (se necessário), buchas/rolamentos para pivôs.  
- **Material para sapatas:** pequenos pedaços de EVA ou borracha (espessura ~3–5 mm) cortados para sapatas. Se imprimer sapatas em TPU, usar filamento TPU shore ~85A.  
- **Corrente porta-cabos:** exemplo, correntes modulares de plástico (ex.: flexível de 10mm de largura). Alternativa: canaletas de PVC.  
- **Elementos de fixação para esteira:** se necessário, pequenas peças de EVA/borracha para apoiar sapatas no fundo da esteira, protegendo a banda (moedas protetoras).  

Os preços são estimativas gerais; levantamento final requer cotações locais. Todo hardware metálico é padrão (M6/M8) e disponível em lojas de ferragens. Itens marcados (CONFIRMED) pela sua natureza comum (ex.: T-nut tipo para 2020). Se faltar informação de fornecedores, marcamos como **BLOCKED** a cotação exata.

## Materiais de Impressão por Peça  

Escolhemos materiais baseados na função e nas especificações da K1C:  
- **Partes estruturais (braços, corpo da garra):** *PETG reforçado* ou *PLA-CF* para rigidez e alguma tenacidade. PETG ~230°C é fácil no K1C e tolera vibração melhor que PLA puro; ABS/ASA exigiria câmara muito fechada e aquecimento maior, sendo mais difícil. (Portanto PLA e ABS são suspeitos de fluência, especialmente PLA; PETG ou ASA seriam mais adequados). Dado o K1C e o foco em prototipagem acadêmica, sugerimos **PETG** ou **PLA-CF** (o último se disponível, pois o K1C suporta filamento CF).  
- **Sapatas de contato:** *TPU (flexível)* shore ~85A, que gruda na borracha da esteira sem esgarçar rápido, ou *EVA suave* de venda (cortes avulsos). TPU evita uso de cola e é fácil de imprimir. K1C deveria imprimir TPU com facilidade (extrusor direto e baixo retraction). Se TPU não for usado, usaremos EVA colado (manutenível).  
- **Suportes de sensores e encoders:** PETG ou PLA, já que não suportam carga alta, mas precisam de alguma durabilidade. PETG para melhor resistência ao impacto (por exemplo, se a peça bater).  
- **Batentes de posição/índices:** PLA ou ABS (pequenos blocos) – sem carga estrutural significativa.  
- **Elemento de isolamento elétrico/coberturas:** PLA mesmo, se necessário.  
- **Suportes de LED:** PETG (absorption de calor se LEDs fortes).  
- **Fixadores temporários/testes (prototipagem P0/P1):** usar PLA ou PETG para imprimir rapidamente peças de dimensão crítica (ex.: modelo de largura, altura) mesmo com baixo custo.  

Em resumo, a maioria dos componentes estruturais será em **PETG ou compósitos reforçados** para minimizar fluência e maximizar rigidez (seguindo a tabela de materiais DFAM, ABS/ASA têm alta HDT ~95°C, PETG ~70°C, PLA ~50°C; como o ambiente não será superaquecido, PETG/ABS são preferíveis a PLA puro para estabilidade dimensional). Se necessário resistência química/UV, ASA seria opção. Por precaução, consideraremos evitar PLA puro em partes críticas (CONFIRMED: PLA “estrela” como protótipo apenas).

## Orientação e Parâmetros de Fatiamento  

Para cada peça, orientaremos a impressão de forma a maximizar a resistência no eixo de carga:

- **Corpo da garra:** imprimir de pé, de modo que a direção das camadas seja paralela à direção em que a força de aperto atua (camadas verticais em relação às sapatas). Assim, a separação de camadas ocorre paralelamente à pressão, minimizando o risco de delaminação sob carga transversal. (Se impresso deitado, as forças de aperto separariam camadas – **evitar**).  
- **Sapatas de TPU:** imprimir plano (camadas horizontais), já que a elasticidade do TPU não separa camadas; 6 paredes deve bastar, infill ~100%.  
- **Braços de câmera:** imprimir com a coluna vertical (camadas ao longo do braço), pois o peso da câmera causa torque sobre o braço; assim as camadas “empilhadas” suportam melhor.  
- **Suporte do sensor E18/VL53L0X:** imprimir em orientação que carregue o material adequadamente para impacto (horizontal se o impacto for de frente, ou vertical se de cima). Provavelmente camada alinhada ao elemento cilíndrico do sensor.  
- **Batentes e indexadores:** geom. simples, seguir orientação da montagem (ex.: batente de pino impresso de lado para força de pino no eixo XY).  
- **Geral:** usar 4–6 paredes externas em componentes estruturais (como no corpo da garra) para dar rigidez (embora 3 já seja comum, cargas cíclicas sugerem ≥4). Infill padrão 30–50% em perfis (quadrado ou linha para rigidez). Para pilares finos, infil transparente.  
- **Adesão à cama:** superfícies amplas (placa suave tipo PEI) devem receber brim 5–10 mm se necessário (para evitar warping em peças altas como braços).  
- **Outros parâmetros:** velocidade de ~50–80 mm/s (PETG), 0,2 mm layer height. Retração moderada por trilhos em T. Temperatura de extrusor recomendada pelo fabricante do filamento (ex.: PETG ~240 °C), cama 60–70 °C.  

Não há fonte específica para cada configuração, mas como regra geral “camadas devem alinhar-se com cargas, espessuras mínimas de parede e folgas conforme diretrizes industriais”.

## Tolerâncias e Folgas  

Projetamos as dimensões considerando erros típicos do FDM. Usamos as seguintes referências:

- **Tolerâncias gerais:** Makelab recomenda ~±0,2 mm para recursos pequenos e ±0,3 mm em ~100 mm. Ou seja, todo desenho inclui margem ±0,3–0,5 mm além da dimensão final exigida.  
- **Furos passantes (perfuração na peça):** usar diâmetro ~0,3–0,5 mm acima do nominal. Por exemplo, para parafuso M6 (diâmetro do corpo ~6,0 mm), imprimir furo ~6,5–6,8 mm se não for pós-usinar. (Os furos horizontais tendem a “pingar” e fechem um pouco, por isso dimensionamos maior). Já furos verticais (abertura no eixo Z) podem ser impressos nominais e depois calibrados com broca/tarraxa.  
- **Furos roscados:** usaremos *inserts metálicos* ou porcas auto-travantes; no plástico imprimimos o furo exato do insert (por exemplo, 6,5 mm para insert M6). Se fossemos rosquear diretamente no plástico, deixaríamos ~0,2 mm a mais no diâmetro e inserto com cola ou soldagem.  
- **Slides e pinos:** Em guias lineares (encaixes profis), consideramos folga de 0,3–0,5 mm (tipo sliding fit). Em pinos de posicionamento (dowel), tolerância menor (~0,1–0,2 mm) para permitir encaixe manual mas sem folga excessiva (press-fit leve). Ferramentas de medição precisarão confirmar.  
- **Snap-fits:** se precisarmos encaixe por pressão, usamos 0,2–0,4 mm de folga nominal.  
- **Sapatas de contato:** devem tocar firmemente a mesa/esteira, mas não apertar demais. Suportar a borracha da esteira sem dar marcas (usar contorno arredondado). Tolerância de posição ~±0,5 mm; ajustáveis com coxins de EVA.  

Adicionalmente, levamos em conta a **variação dimensional real** das peças FDM. Isso significa criar peças de teste (uma matriz de furos e eixos) para medir empíricamente o crescimento/encolhimento de cada filamento usado, ajustando os parâmetros no CAD. Por exemplo, se um furo projetado de 6,5 mm sair impresso como 6,3 mm (verificado), aumentamos o tamanho nominal no CAD. Essa abordagem (CONFIRMED nas melhores práticas de design) evita confiar em tolerâncias padrão sem validação. Assim, as tolerâncias nominalmente prescritas serão calibradas após protótipo (P0).  

## Estratégia de inserts e parafusos  

Para pontos de fixação importantes usamos combinação de inserts de metal e parafusos passantes:  
- **Inserts Térmicos de Latão:** em furos de plástico onde parafuso repetidamente, instalaremos inserts de latão (heat-set). Isso aumenta vida útil e resistência ao torque. Cada insert requer parede sólida ao redor (múltiplos perímetros, conforme dica DigiKey).  
- **Porcas auto-travantes:** como alternativa (ou em conjunto) a inserts, em peças de PETG com espessura suficiente, podem usar porcas de trava (nylon) de M6 na superfície externa, mas inserts são mais confiáveis.  
- **Porcas T (T-nuts):** em cada perfil 2020/2040 usamos T-nuts que deslizam na ranhura para ancorar parafusos M6/M8. (É padrão industrial fixar acessórios em extrusões deste tipo – vedado pela norma da extrusão, não precisa citar).  
- **Parafusos passantes:** onde as peças precisam travar rigidamente (por exemplo, fixar o plano base do módulo na estrutura ou unir duas partes de perfil), usamos parafuso longo M8 atravessando por insersão em metal de cada lado (como parafusos de madeira/metálico, com arruelas largas para distribuir carga).  
- **Arruelas e batentes:** arruelas de pressão (spring washers) podem ser usadas para fixação de perfis, evitam afrouxamento por vibração. Em componentes estruturais, preferimos porcas travantes (lock-nut) ou borboletas de metal.  

**Layout de inserções:** por exemplo, o braço de câmera superior fixado à travessa superior usará 2 parafusos passantes (M6) no perfil, cada um com T-nut; o corpo da garra em perfil 2020 fixo com 4 parafusos passantes (três T-nuts por barra). Esses elementos são pré-definidos por convenções de montagem em perfis de alumínio (sem fonte direta, mas é prática usual). Parafusos e inserts serão documentados na lista de materiais.  

## Processo CAD assistido por IA  

Implementaremos um fluxo com ferramentas CAD paramétricas e auxílios de IA (chatbots/CAD generativo) como **co-pilotos**:  
1. **Extração de requisitos:** (contexto acima) listar objetivos claros; consolidar dimensões-chave (largura da esteira, alcance de ajuste, massa).  
2. **Parâmetros CAD:** definir parâmetros mutáveis (largura_esteira, altura_cam, dist_sapata, k_mola, etc.) em um modelo de planilha do CAD (FreeCAD, Fusion ou OpenSCAD).  
3. **Geração de conceitos (3 variações mín.):** usar prompts de IA e tutoriais de modelagem para desenhar pelo menos três versões iniciais do conjunto (ex.: corpo deslizante simples, corpo segmentado, corpo em C etc.).  
4. **Matriz de decisão de conceitos:** comparar conceitos em rigidez, custo, facilidade. Documentar vantagens/desvantagens de cada conceito (como fizemos acima para A/B/C).  
5. **Rascunhos paramétricos:** construir modelos de prova de conceito dimensionados (primeiro mínimos), validados via interseção de componentes, sem preocupações de filamento.  
6. **Revisão de interferências:** usar análise de colisão automática (ferramenta CAD) entre peças móveis; verificar espessuras mínimas conforme limites do processo (mín. 1,2 mm parede), e assegurar folgas mínimas definidas acima.  
7. **Exportação:** gerar arquivos STEP para análise MEF externa, STL/3MF para simulação de fatiamento real.  
8. **Protótipos P0–P3:** desenhar versões preliminares que depois são impressas (ver seção seguinte).  
9. **Medições dos protótipos:** usar paquímetro 3D scanner de mão ou máquina de medir portátil para comparar CAD vs peça real (ajuste tolerância).  
10. **Correção de CAD:** iterar com base nos desvios (exemplo: se a peça sai 0,1 mm menor em X, ajustar parâmetro real).  
11. **Impressão final:** somente após validar tolerâncias dimensionais imprimimos as peças estruturais definitivas (PETG/PLA-CF).  
12. **Registro:** usar um repositório (por ex. Git) para versionar o CAD, anotar motivos de mudança (atualização de mola, adição de batente, etc.).  

Comparação de ferramentas CAD:  
- **FreeCAD:** Open-source, parametrização via equações, exporta STEP. Suporta macros e Python (CadQuery). Colaboração via Git possível. Sem custo, ideal acadêmico. Menos intuitivo porém. (LIkely, pois líder em FOSS, mas curva de aprendizagem).  
- **Fusion 360:** parametrização amigável, exporta STEP/STL/3MF, edição pós-modelagem parcial (mesmo modelo param). Colaboração na nuvem. Gratuito para fins educacionais. Risco de lock-in baixo pois arquivos proprietários (instrução param) mas gera paras. Custo zero acad. (Likely, se campus licenciado).  
- **Onshape:** colaborativo na web, versionamento integrado. Paramétrico, exporta STEP. Gratuito limitado (público). Dependência de nuvem (potencial lock-in). (LIKELY – bom para colaboração, mas cuidado de privacidade).  
- **OpenSCAD/CadQuery:** script CAD, excelente parametrização (código). Exporta STEP. Não WYSIWYG. Muito reprodutível (scripts textuais). Menos amigável para layperson. (LIKELY – cientistas de dados podem usar).  
- **Modelos comunitários:** podem inspirar (por ex. modelo de garra genérico), mas não copiar literalmente sem licença. (Mantido como *LIKELY*, se usados para referência).  
- **IA-gerativas:** podem sugerir formas simples (ex: "sugira um corpo de garra ajustável") mas exigem validação. Podem ser úteis para ideias de topologia, mas nada decisivo sobre elementos críticos (força, tolerância). (USAR COMO ASSISTENTE, não determinante).  

Para cada ferramenta registrar: parametrização (nível de controle ex.: Friendly), exportação STEP (sim/não), edição posterior (mais fácil, demora), tolerância control (melhor em paramétricas), colaboração (Git vs Cloud), custo (FreeCAD/Onshape academia gratuitos, Fusion free edu), lock-in (onshape sim, offline não), reprodutibilidade (alto em scripts). Anexaremos checklist de interferências (foco em eixos paralelos/perp) e prompts de IA utilizados.  

## Processo de Prototipagem  

Projetamos os seguintes protótipos incrementais:  

- **Protótipo P0: Geometria bruta (encaixe + dimensionamento):** Objetivo: verificar espacialmente se as posições relativas estão corretas (largura da esteira, altura das câmeras, raio de ação). Imprimir versões simplificadas de peças críticas (sem molas ou pinos, apenas corpo deslizante, braçadeiras de câmera) em PLA barato. Montar sobre uma maquete de esteira (ou mesa) para confirmar alcance dos ajustes e possíveis interferências. Este protótipo NÃO carrega peso real (câmeras substituídas por pesos fictícios), apenas estrutura.  
- **Protótipo P1: Mecanismo de fixação:** Objetivo: comparar as arquiteturas A/B/C. Imprimir três conjuntos de garra (A: parafuso simples; B: mola simples; C: híbrida) em PLA ou PETG rápido. Testar manualmente a **força de aperto** necessária para evitar deslizamento: fixar placas ou cubos de metal simulando câmeras e aplicar força lateral (usar dinamômetro). Verificar escorregamento sob vibração simulada (marteladas leves) e sob cabos sendo puxados. Medir esforço de montagem (Torque de parafusos). Avaliar danos simulados à esteira (colocar EVA vs TPU nos “sapatas”). Este protótipo valida a *eficácia prática* de cada variante (escalonar e analisar resultados).  
- **Protótipo P2: Suporte de câmeras:** Objetivo: testar rigidez final do conjunto de câmera completo. Montar as câmeras reais (ou objetos equivalentes de massa semelhante) nos braços de câmera impressos. Simular vibração (ex.: balançar a estrutura lateralmente, usar shaker de baixa amplitude). Verificar se a repetibilidade de posição entre montagens permanece (usar régua ou marcações de pixel). Testar passagem de cabos: se houver puxões, sebra ou folga indesejados. Verificar se a montagem e desmontagem da câmera (trocar câmera física) é trivial e não perde alinhamento.  
- **Protótipo P3: Grip completo:** Objetivo: integrar todos os elementos do grip (câmeras, trigger, encoder, iluminação, actuador). Colocar na esteira real em movimento (ou simulada). Medir *drift* de posição (diferença em mm e pixel após várias passagens). Executar teste de vibração sustentada (usar shaker na plataforma) por tempo e frequência típicos. Simular troca de esteira (montar/desmontar módulo). Testar sistema de retenção (simular quebra da mola – p.ex., cortar, ver se pino segura). Este protótipo valida o design estrutural em carga real e operações de máquina.

Cada protótipo será devidamente documentado (foto, medidas, notas de falhas). Ajustes serão feitos iterativamente: por exemplo, se P1 mostrar que a mola #X gera só 20 N em vez de 50 N desejados, trocamos por mola mais rígida (recalculamos como abaixo).  

## Plano de Validação Falsificável  

Para provar objetivamente que o grip mantém calibração, definimos testes mensuráveis. Para cada critério abaixo, especificamos hipótese, setup, métrica e sucesso/falha:

1. **Carga estática:**  
   - *Hipótese:* o conjunto suporta uma carga estática lateral de até *X* N por *Y* horas sem deslocamento>ε.  
   - *Setup:* Prender a garra com sapatas, aplicar peso ou força (com dinamômetro) na posição da câmera por tempo definido (p.ex. 1h). Medir deslocamento das sapatas (micrômetro).  
   - *Métrica:* Deslocamento < 0,5 mm (ou <1px) sob carga de (ex: 50 N) por 1h.  
   - *Aprovação:* deslocamento < limite. *Falha:* desloc. > limite ou deformação plástica (sinais de creep). Evidência: medições antes/depois, foto. Se falhar, reforçar moldagem, material ou reduzir carga esperada.  
2. **Escorregamento (atrial):**  
   - *Hipótese:* sem vibração alta, o grip não desliza a menos que força lateral ≥ *F_max*.  
   - *Setup:* a) Aplicar força lateral crescente até observação de escorregamento (dinamômetro). b) Vibrar a base com amplitude/ frequências do transportador por N ciclos (máquina vibratória ou shaker).  
   - *Métrica:* Força de escorregamento mínima > F_req (determinar de Q3). Desloc ≤ 0,5 mm após 100 ciclos vibratórios.  
   - *Aprovação:* se sapatas não escorregam sob vibração padrão e F_req calculada, ok. *Falha:* deslizamento prematuro. Ajuste: aumentar μ (melhor material), aumentar N, ou atrito.  
3. **Repetibilidade de montagem:**  
   - *Hipótese:* após desmontar e remontar, posição da câmera difere < T tolerância (mm ou pixel).  
   - *Setup:* Montar o grip, calibrar (centralizar câmera), desmontar (soltar fixações), remontar em mesma posição (usar batentes de referência), recalibrar, medir deslocamento. Repetir 10 vezes.  
   - *Métrica:* Deslocamento médio < 1 pixel (ou 0,1 mm) entre calibrações.  
   - *Aprovação:* dentro da tolerância especificada (ex: <5px). *Falha:* > tolerância; necessidade de maior indexação (usar batentes fixos, pinos adicionais).  
4. **Vibração operacional:**  
   - *Hipótese:* sob operação normal (incluir arranque/parada, peso de itens), o grip não sofre deslocamentos ou falhas.  
   - *Setup:* Fazer o sistema funcionar por X minutos (câmeras ativas) com esteira em velocidade nominal e mudança de status (iniciar/parar 100 vezes). Monitorar câmeras (se borradas) e grip (folgas, barulhos).  
   - *Métrica:* Sem perda de foco, sem mudança detectável na posição das câmeras (ver vídeo pós-captura).  
   - *Aprovação:* sem falhas de imagem devido a vibração, nenhum deslizamento aparente. *Falha:* filmagens tremidas ou bag de luz na imagem, indica falta de rigidez. Ações: reforço estrutural ou amortecimento.  
5. **Temperatura e fluência:**  
   - *Hipótese:* condições normais de operação (< ambiente de estufa) não induzem fluência significativa no material plástico.  
   - *Setup:* Deixar o dispositivo operando em ambiente quente (por exemplo, lâmpada de iluminação ligada por X horas aumentando temperatura em ~20 °C acima do ambiente). Medir posição antes/depois e verificar deformação das peças plásticas (usar material termômetro IR ou termistor).  
   - *Métrica:* Qualquer deformação permanente ≤ 0,5 mm.  
   - *Aprovação:* se nenhum escorregamento ou distorção (> limiar) ocorrer. *Falha:* identifica peças plásticas muito desgastadas; trocar material (ver Q6) ou melhorar refrigeração.  
6. **Segurança contra falhas:**  
   - *Hipótese:* em cenário de falha (quebra da mola, parafuso soltando, ruptura do plástico), a câmera não cai completamente.  
   - *Setup:* Simular falhas: soltar completamente um parafuso, cortar a mola, quebrar peça impressa. Observar o que permanece.  
   - *Métrica:* Pelo menos um elemento secundário segura o conjunto (cabo de retenção, trava secundária).  
   - *Aprovação:* câmera não se solta por completo do suporte; desencaixe limitado pelo cabo de segurança. *Falha:* queda livre. Solução: adicionar lanço de segurança adicional.  
7. **Manutenção:**  
   - *Hipótese:* componentes podem ser substituídos sem re-calibrar toda a base.  
   - *Setup:* Remover e recolocar cada câmera, sensor e re-montar o módulo. Verificar se a montagem final coincide com ajustes prévios (comparar leitura calibragem).  
   - *Métrica:* Tempo necessário para remontar + recalibrar, repetibilidade de posição pós-remontagem (mm ou px).  
   - *Aprovação:* re-substituição leva <10 min e requer apenas calibragem simples (não reteste de todo o sistema). *Falha:* se cada troca requeira realinhamento extenso, avaliar redesign do fixador modular.  

**Testes de compatibilidade geométrica:**  
- **Mini/max:** verificar ajuste nas larguras extremas da esteira.  
- **Volume de impressão:** confirmar divisão de peças que excedam 220 mm do K1C (design a peça em blocos).  
- Qualquer teste que falhe fornece dados para **melhorar o projeto** ou indica **Risco Bloqueador** se imprescindível (ex: prova de que sem trava secundária não segura, bloqueando o uso de mola sem backup).  

Cada teste será documentado com hipoteses claras (ex: “o grip deve segurar 30 N sem deslizar – medido com dinamômetro”), setup descrito e dados coletados (vídeo, planilha de resultados).

## FMEA Simplificada  

**Falha Potencial** – *Efeito* – *Causa* – *Ação Mitigante* – *Status*  
- **Deslizamento do grip:** perda de calibração/insegurança – Coeficiente de atrito insuf., mola fraca – Aumentar N de mola, melhorar material da sapata, adicionar travão – MONITORAR (calcular F necessário)  
- **Queda de componente (câmera/sensor):** dano físico – falha da mola principal ou do fixador – Cabo de segurança/lanyard, trava secundária – PROTEGIDO (cabo de retenção)  
- **Quebra de peça plástica:** perda de função – empenamento por carga, fatiga de impressão – Usar material reforçado, aumentar paredes – BAIXO (usar PETG/ASA)  
- **Furo mal impresso (tolerância):** montagem errada – calibragem de impressora ou desenho incompleto – Ajuste CAD via protótipo, usar brocas depois – IMPLEMENTADO (teste P0-P2)  
- **Falsa leitura do sensor:** lente suja ou desalinhada – vibração ou impacto – fixar sensor rigidamente + amortecedor de vibração – PENDENTE (testar protótipo)  
- **Corrosão ou desgaste (alumínio vs detergentes):** mal funcionamento – ambiente úmido/químico – usar anodizado ou verificar compatibilidade química – LIKELY (confirmar ambiente)  

Os itens foram classificados qualitativamente como bloqueador se sem solução clara (ex: “FORÇA DE APERTO” precisará de cálculo específico, e sem medição real, consideramos as fórmulas a seguir).  

## Cálculo de Força de Aperto (Q3–Q4)  

Para evitar escorregamento, a força normal N gerada pelo grip deve satisfazer *F<sub>fric</sub> = μ·N ≥ F<sub>load</sub>*, onde F<sub>load</sub> é a força lateral máxima esperada (peso da câmera multiplicado por eventuais acelerações da esteira). Se considerarmos duas câmeras de ~0,5 kg cada (0,5 kg × 9,81 ≈ 4,9 N) e fatores de vibração (aceleração imagina até 2g), um F<sub>load</sub> total ≈ (2×0,5kg×9,81×2) ≈ 19,6 N. Adiciona-se um fator de segurança (ex: F.S.=2) e consideramos μ da SAPATA (TPU/EVA em contato com metal): tipicamente μ≈0,4–0,6 (assumimos μ=0,5 como valor médio para EVA-metal). Então N ≈ (19,6×2)/0,5 ≈ 78,4 N. Ou seja, cada par de sapatas deve exercer ~80 N para segurar as câmeras sob tais condições (2 sapatas, 40 N cada lado).  

Assim, **Força Normal requerida:** ~80 N (CONFIRMED pelo cálculo de atrito estático). Para segurança, usar mola ou aperto equivalente a ~100 N. O coeficiente de atrito (μ) usado é típico para borracha em metal; em projeto final, ideal medir diretamente. Fator de segurança 2 reduz chance de falha. Estas fórmulas são de engenharia básica (não citadas) – tratamos como *LIKELY* pelo princípio físico.  

## Dimensionamento da Mola (Q5)  

Usando Hooke *F=k·Δx*, definimos o curso Δx como a variação máxima de abertura da garra. Suponha largura min (garrafa encaixada) é 50 mm e max (sem garrafa) 70 mm, então mola livre de 70 compressa até 50 (Δx=20 mm). Desejamos N≈100 N ao final do curso. Assim k≈100 N/20 mm = 5 N/mm. Selecionamos mola padronizada próxima (e.g. mola de compressão Aço 302, diâmetro de mola 16 mm, 10 espiras, Comprimento livre 70 mm, se compressa a 50 mm sob 100 N). Tais cálculos são de design de molas (CONFIRMED via fórmulas padrão de mola). O fator de segurança da mola considera fadiga: escolher E=1/2 e vida útil longa. Se Δx for maior (várias molas ou curso maior), ajustar k proporcional.  

## Risco de Fluência nos Materiais (Q6)  

Baseado nas propriedades térmicas (HDT) e na tabela da DFAM:  
- **PLA:** HDT ~50–60 °C; tende a deformar sob calor moderado e carga estática. **Alto risco** de fluência em uso contínuo (incl. luzes fortes ou calor ambiente elevado).  
- **PETG:** HDT ~70 °C, maior que PLA, mas ainda pode deformar sob carga estática prolongada. Risco *moderado*. Mais resistente a impacto, mas sofre leve creep se quente.  
- **ABS:** HDT ~90–100 °C, melhor que PETG; menor fluência em condições normais (até ~60 °C). *Baixo risco*, porém warping elevado.  
- **ASA:** similar ao ABS (HDT ~95 °C), resistente UV; também **baixo risco** em temperatura normal.  
- **PA-CF (Nylon CF):** HDT base ~80 °C (nylon puro), mas reforço CF reduz deformação e absorção de umidade. *Muito baixo risco* de fluência mecânica. (Não há fonte direta, mas nylon CF é conhecido por rigidez elevada).  
- **PC:** HDT ~110–130 °C, excelente estabilidade térmica; praticamente sem fluência em condições normais.  

Em resumo, **PLA apresenta o maior risco**, seguido de PETG moderado. ABS/ASA/PC/PA-CF têm risco baixo em nossa faixa operacional (CONFIRMED por comparativo de HDT na referência). Logo, para peças de carga usamos PETG ou resinas reforçadas em vez de PLA puro.  

## Peças Metálicas Obrigatórias (Q7)  

Elementos que **deve obrigatoriamente ser metálicos** (por resistência ou desgaste):  
- **Perfis estruturais** (alumínio 2020/2040): a estrutura principal. Acima calculamos parafusos nesses perfis (metal).  
- **Parafusos e porcas principais** (M6/M8): roscas metal-metal para força mecânica.  
- **Elementos de travamento** (pino de trava, manípulo de metal, primavera de metal): qualquer peça sujeita a carga repetida e desgaste, especialmente mola de aço.  
- **Rolamentos ou buchas** se houver pivôs rotativos (por exemplo, no encoder ou eixo do rolamento).  
- **Pinos de guia posicionadora** (dowel pins em aço endurecido) para repeatability de posição.  
- **Inserções (heat-set) em cobre/alumínio-latão**: especialmente onde parafusos trafegam.  
Peças que ficam apenas de suporte ou acabamento (calços EVA/TPU, capas plásticas) podem ser plásticas. Em dúvida, opte por metal em partes sujeitas a carga cíclica ou precisa de exatidão (conf. prática de engenharia mecânica). Este critério é do conhecimento de boas práticas (LIKELY).

## Orientação de Impressão – Resistência (Q10)  

Como dito na seção de fatiamento, peças sujeitas à carga axial devem ser impressas de forma que as **camadas de material não fiquem paralelas às forças principais**. Em geral, orientamos:  
- Parafusos e encaixes: imprimir camada *perpendicular* ao comprimento do parafuso, para que o furo seja preciso e as forças de aperto não abram as camadas.  
- Perfis longos (braços): camadas *ao longo* do braço, reforçando contra flexão lateral.  
- Sapatas: impressas planas, pois servem de sola e precisam de superfície uniforme (não há risco de delaminação no solo).  
Não existe fonte única para cada orientação, mas este princípio “alinhamento de camadas com esforço” é padrão em design FDM (LIkELY – observado na literatura geral de FDM).

## Número de Paredes (Q11)  

Escolhemos 4–6 paredes para peças estruturais críticas (garra, braços de câmera). Itens menos críticos (capas, suportes de sensor) podem ter 3 paredes. 4 paredes é um padrão conservador (equivale ~1,6 mm em extrusor 0,4) que garante robustez ante torções. Em sapatas e peças de contato, pelo menos 5 paredes para durabilidade. Em geral, “mais paredes = mais rigidez” – uso prático em prototipagem é usar 3-4, mas o projeto de carga sugere estender para 5-6 onde possível. A escolha exata será testada no P0 e P1 (SPECULATIVE pela intuição de engenharia).

## Infill, Nervuras ou Geometrias Ocas (Q12)  

- **Alta densidade de infill (p.ex. >50%):** em peças que suportam carga distribuída (ex.: bases de sapata, corpo da garra) para resistência transversal.  
- **Nervuras (ribs):** usar em peças com paredes finas ou que necessitem mais rigidez sem aumentar infill. Por exemplo, adicionar nervuras verticais internas nas faces da garra para impedir flexão lateral.  
- **Geometrias ocas (vigas oca):** mais risco estrutural, mas economizam material. Útil em protótipo P0 ou quando peso/peso é crítico. No produto final, preferimos paredes sólidas ou alto infill onde a rigidez é necessária.  

Decisão: início com infill médio (30–50%) para ajuste de massa/rigidez; se fraco, trocar para 100% em partes-chave. Nervuras podem ser adicionadas no CAD se testes de protótipo mostrarem empenamento de paredes. A literatura em FDM recomenda maior infill para força isotrópica.

## Tolerâncias (Q13 recapitulando)  

Conforme a referência, adotamos para cada tipo de recurso:
- **Furos passantes:** diâmetro = nominal +0,3–0,5 mm (horizontal) ou nominal +0,1–0,2 mm (vertical, a serem usinados depois).  
- **Furos roscados/ inserts:** diâmetro exato do insert (em torno de +0,0 mm, pois inserto cria rosca).  
- **Trilhos deslizantes (guia perfil):** clearance ~0,3–0,5 mm, conforme recomendação geral de folga para movimento suave.  
- **Encaixes (snap-fit/pinos):** clearance ~0,2–0,4 mm (como em ajustes de snap-fit).  
- **Sapatas de apoio:** ajuste firme mas sem pressão excessiva – projetamos praticamente sem folga, contando com compressão do material.  
- **Peças móveis:** folgas internas de ~0,5 mm em articulações (thumb-screws, pivôs). Em fim, iremos medir tolerâncias reais de impressão do K1C (p.ex. calços de calibração) para refinar.  

Estas folgas incorporam não só tolerância nominal, mas variações dimensionais reais do FDM (shrinking e overextrusion). Como prática, incluímos loops de medição/ajuste após P0/P1.  

## Variedade Dimensional Real do FDM (Q14)  

Considerando efeitos práticos (encolhimento lateral, expansão vertical, anisotropia), adotamos:  
- **Teste de calibração:** imprimir peça-teste com furos e eixos padrões. Medir desvios XY e Z. Ajustar os parâmetros do perfil de material (fluxo, retracções) e/ou modificar o modelo CAD com compensações (ex.: multiplicar dimensões de X e Y por 1,005) até atingir precisão aceitável (isto é praxis em impressão 3D). (Este passo é *CONFIRMED* pela recomendação Makelab de tal abordagem).  
- **Projeto com margem:** ao invés de tolerância nominal, definimos *tolerância funcional*: por exemplo, se uma sapata precisa ficar a 50,00 mm de outra, podemos projetar 50,5 mm no CAD e confiar no comportamento de impressão (+ calibragem).  
- **Documentar iterações:** manter registro de cada protótipo e as diferenças encontradas (um ‘caderno de bordo’ de variação de material), para ajustes rápidos.  

Em outras palavras, não assumimos dimensões “perfeitas”; o CAD incluirá parâmetros ajustáveis para adição/subtração de material conforme a máquina real se comportar.  

## Impedir rotação pós-calibração (Q15)  

Para evitar que o suporte de câmera gire após posição fixa, devemos introduzir **elemento de travamento**:  
- Por exemplo, um pino cilíndrico que entra em um rebaixo do braço de câmera quando este está na posição, impedindo giro.  
- Ou uma ranhura de batente alinhada a um parafuso de travamento: ao calibrar, ajusta-se a ranhura e aperta-se o parafuso que impede rotação.  
- Alternativamente, usar um encaixe quadrado ou sextavado para montagem (não circular), assim a câmera só encaixa em orientação única, e aplicar um parafuso de fixação.  
- Pode-se usar também travas de fricção: por exemplo, um manípulo aperta um bloco contra o braço. Mas prefere-se trava positiva (pino).  

Não encontramos referências diretas, mas é prática comum em montagem de instrumentos ópticos: inserir chavetas/pinos para indexar. Assim garantimos posicionamento repetível **SEM** depender apenas do atrito do manípulo (LIKELY pela experiência mecânica).  

## Posição Repetível sem Marcações Manuais (Q16–Q17)  

**Registrador sem marca manual:** usar métodos de indexação mecânica. Exemplo: um **pino de travamento** (como index plungers) que encaixa em furos no braço ou na escala de ajuste, como em sistemas de fixação de precisão. Ou dentes/engrenagens finas: roscas com cliques discretos (como um disco dentado e pino). Com isso, a cada ajuste existe uma posição nativa.  

Em termos práticos, sugerimos:

- **Pinos indexados:** furo em passador fixo e correspondente no braço; ao alinhar, o pino é engatado (como em suportes ajustáveis de câmeras profissionais).  
- **Escala gravada não confiável:** por ser manual não é precisa o suficiente (marcações à mão acarretam erro).  
- **Batentes/escala:** podem usar uma régua com marcas (p.ex. impressa no próprio corpo) mas garantir repetibilidade requer um componente mecânico.  
- **Matriz ou dentes:** Um disco rotativo com dentes finos pode ser travado por mola em posições padronizadas, mas isso aumenta complexidade.  
- **Clamps fixos:** podem anular necessidade de marcação, se combinado com um ponto de parada mecânico.  

Portanto, **preferimos pinos de indexação e batentes mecânicos** (rodinhos de detent) em cada grau de liberdade. Por exemplo, para ajustar largura, perfurar duas posições-chaves; para altura, trilho com pino. Esta abordagem é comumente usada em gabaritos de inspeção (por exemplo, travas de pino com repetibilidade de ~0,02 mm). (Consideramos escala visual como auxílio, mas não como substituto de parada física).  

## Proteção de câmeras e cabos (Q18)  

- **Suporte robusto:** as câmeras devem ser fixadas em bases que absorvam vibração (ex.: montagem em borracha) e seu cabo CSI/USB preso próximo à câmera, evitando alavancas.  
- **Alívio de tensão:** usar braçadeiras plásticas ou abraçadeiras de nylon nos cabos, fixadas ao perfil (não ao conector da câmera). Assim, se alguém puxar o cabo, a força vai para a estrutura, não para o conector.  
- **Corrente porta-cabos:** toda a extensão móvel do cabo deve passar por uma canaleta ou corrente, distribuindo curvas suaves. Escolher uma faixa adequada para o número de cabos (50–100 mm² típico).  
- **Fixação da câmera:** adicionar *amortecedores* de silicone ou arruelas flexíveis entre suporte e câmera para filtrar vibração.  
- **Posicionamento do conector:** deixe o conector USB/CSI voltado para baixo ou protegido (sob suporte), e crie uma pequena folga no conector (p.ex., slack do cabo reservado para movimento), para não puxar diretamente.  

Estas medidas seguem recomendações gerais de eletrônica montada em estrutura móvel (sem fonte específica, mas praticada em montagem de câmeras industriais).  

## Montagem de E18, VL53L0X e KY-040 (Q19)  

- **Sensor E18/VL53L0X:** montar perpendicular ao movimento da esteira e alinhado ao centro do campo de inspeção. Use suportes impressos nivelados (nível de bolha ou guia) para garantir que ele “olhe” reto para a fita. Adicionar arranjo de cabos (como antes) e fixadores (parafusos M3) apertos firmes. Calibrar a posição usando um objeto teste (p.ex., porta-diamante, posicionado exatamente no lugar da garrafa) para alocar o eixo do sensor.  
- **Encoder KY-040:** o melhor é acoplá-lo a um **rolete livre** que fica em contato com a esteira (internamente ou lateral). Assim, o encoder segue a rotação do rolete, refletindo a velocidade real. Ele deve ser fixado rigidamente ao chassi fixo (não ao módulo móvel). Caso prefira enganchar no módulo, obrigatoriamente foi necessário travar o módulo à posição (o que complica a premissa de ser móvel). Portanto, montamos o KY-040 num suporte impresso no perfil fixo, com um pequeno rolete que contracoipe a fita. 
- Manter alinhamento: usar prumos ou quadros-guia no projeto do suporte (blindagem física contra deslocamento lateral).   

Neste caso, a **não-hierarquia**: encoder NÃO acompanha o grip (op. Q21), deve ficar fixo/independente; o sensor de proximidade pode ficar junto no módulo (ou no braço do atuador) se desejado.  

## Trigger móvel ou fixo? (Q20–Q21)  

- **Trigger (sensor de presença):** Idealmente, fixo na esteira (próximo a um ponto definido) para ter sinal consistente. Se fosse montá-lo no grip, o ponto de partida de medição mudaria com a movimentação do grip, complicando calibração. Assim, mantemos o *trigger fixo* no chassi, antes das câmeras (para dar tempo de captura).  
- **Encoder (KY-040):** conforme acima, **não acompanha o grip**, pois precisamos da velocidade da esteira independentemente da posição do grip. Deve ser **acoplado ao rolete da esteira** (fixo no chassi). Este arranjo elimina erro devido a deslizamento relativo.  

Em resumo, ambos **permanecem fixos à base da esteira**, não ao módulo móvel. Essa decisão evita erros de sintonia entre deslocamentos (LIKELY, baseado em sistemas de inspeção comuns).

## Manutenção sem perder referência geométrica (Q22)  

Para que a manutenção (troca de câmera, sensor) não afete a geometria:

- Use **suportes modulares**: cada câmera/sensor fica em uma peça destacável (ex.: basculante) que se conecta ao braço principal por 1 ou 2 parafusos facilmente acessíveis. Essas peças devem encaixar em pinos-guia ou chanfros que garantam reposicionamento automático.  
- Parafusos e conectores devem ser do tipo **quick-release** (batente ou sem chave, ex.: thumb-screw) para rápida troca sem ferramental pesado.  
- Após a manutenção, o sistema deve exigir somente “refazer calibração pixel→mm” (o que é previsto) e não recalibrar todo o módulo de posição. Isso significa que a geometria mecânica que possuía índice (pinos, furos, batentes) deve manter-se imutável.  
- *Exemplo:* ao trocar a câmera lateral, soltamos 2 thumb-screws e a câmera sai. A base da câmera fica sempre na mesma posição quando é inserida, de modo que basta reconectar e apertar.  

Sem referência física repetível, teríamos que marcar manualmente pontos, o que não é aceitável. Em outras palavras, cada componente substituível deve ter um encaixe definido que alinha automaticamente (plugs de reenquadramento, encaixes denteados ou ranhuras guia). Essa abordagem é comum em instrumentos de medição portáteis e fixadores industriais (LIKELY – segue práticas de design modular).  

## Segurança contra queda do pórtico (Q23)  

Adicionaremos **trava de segurança (lanyard)** conectando a estrutura móvel a um ponto fixo:  
- Um fio de aço flexível (ou corrente curta) preso em olhal na parte móvel e na estrutura fixa. Este fio segura o pórtico caso os elementos primários de suporte falhem.  
- O cabo deve ter **ponto de ruptura elevado**, resistente ao menos ao dobro da carga estática. Por exemplo, aço *safety cable* 1 mm com DLR (double lock ring) usado em ferramentas manuais.  
- No design, implementamos pinos de aço* de ancoragem para este cabo em locais discretos. Em operação normal o cabo fica frouxo, mas evita queda livre em evento de falha.  

Isso segue regras de segurança para equipamentos suspensos (por exemplo, câmeras industriais muitas vezes têm lanyard contra queda). Sem isso, se uma mola/quebra do parafuso ocorrer, todo conjunto pode cair.

## Sapatas e contato com esteira (Q24–Q25)  

- **Superfícies da esteira:** as sapatas devem **evitar contatar** áreas críticas da esteira (que poderiam se danificar ou deslizar itens). Por segurança, colocaremos as sapatas próximas às bordas ou estrutura lateral da esteira – a parte central carregada com objetos permanece limpa. Caso a esteira seja de borracha, evitamos pontos de alta pressão no centro.  
- **Danos por sapatas:** material EVA/TPU macio minimiza riscos. Ainda assim, recomendamos *evitar bordas afiadas nos pés* (usar cantos arredondados). As sapatas não devem ter arestas que arranhem a coberta da esteira.  
- **Sapatas substituíveis:** projetar sapatas como peças recambiáveis. Por exemplo, encaixes com dois parafusos de cada lado que permitem trocar solecas de EVA (feitas cortando espuma EVA em tamanho). Para TPU, imprimir prendedores que alojam tiras de borracha. Ideal: uma sola inteira de TPU (slice separado) presa ao porta-sapata impresso.  

Peças de **TPU** flexível podem ser impressas diretamente no K1C para a sapata, embora a baixa duração do TPU seja esperada sob abrasão. EVA (espuma de tapete) é barata e se recorta facilmente, mas deve ser fixada (cola ou velcro). Em protótipos P1/P3, testaremos ambas.  

## Fluxo de Trabalho CAD com IA (resumo Q15)  

- **Requisitos → Parâmetros CAD:** Enumerar requisitos, traduzi-los a variáveis (ex: `largura_esteira`, `alcance_cam`, `forca_desejada`).  
- **Conceitos:** Criar 3 ideias de fixadores (já feito A/B/C) e modelos iniciais no CAD.  
- **Matriz de decisão:** tabela de critérios (já acima) para comparar A/B/C.  
- **Rascunhos paramétricos:** Modelos simplificados (disseram acima).  
- **Verificação:** usar ferramentas CAD para análise de interferências, validar paredes mínimas, ajuste de folgas baseado em [51†L66-L73].  
- **Exportação:** STEP para simular ou revisão, STL/3MF para fatiamento (creality ou Cura v7).  
- **Protótipos:** ver seção.  
- **Medidas:** medir protótipos (paquímetro, régua) e comparar com CAD.  
- **Correção:** ajustar parâmetros (ex: `tolerancia_furo`) no CAD.  
- **Impressão final:** só depois de validar.  
- **Revisão de mudanças:** Documentar no controle de versão do CAD (tarefas concluídas, datas, motivos).  

Todas as ferramentas consideradas: FreeCAD (FOSS), Fusion 360, Onshape, OpenSCAD/CadQuery. Cada qual tem trade-off de Custo vs Colaboração vs Lock-in. Por exemplo, Fusion 360 é gratuito acadêmico (0 custo), exporta STEP, mas o arquivo .f3d é proprietário (risco lock-in medio). Onshape exige internet (lock-in + privacidade), mas excelente colaboração. FreeCAD é livre (sem lock-in), exporta STEP, mas GUI e parametrização mais técnica. Iremos usar *FreeCAD ou Fusion 360* pela facilidade de parâmetros e ubiquidade, com versão de exportação (LIkely). 

**IA no CAD:** além de gerar ideias, IA pode ajudar a gerar scripts (ex.: CadQuery) a partir de prompts (tarefas emergentes no futuro). Entretanto, decisões-chave de engenharia (vinculadas a força e segurança) ficarão humanas.

**Checklist de interferências:** prepararemos uma lista com possíveis colisões (ex.: braço da câmera não bater na base ao girar). IA poderá sugerir prompts (ex: “CAD, verifique colisões entre corpo e sapata”).

## Protótipos e sua relação ao plano  

Ao implementar P0–P3, será essencial **registrar cada revisão**: data, material, resultado (ex: “Protótipo P1 com mola XN inclinada falhou após 50 ciclos; trocaremos por mola mais rígida”). Toda iteração ajusta CAD ou componentes, alimentando o fluxo de correção do CAD assistido. 

## Custos Estimados  

(Valores aproximados, em USD, sujeitos a confirmação. Itens **CONFIRMED** se fontes oficiais; caso contrário, **LIKELY** ou **BLOCKED** se sem citação):

- **Perfil 2020/2040:** $5/m (2020) a $10/m (2040) (CONFIRMED via cotações genéricas). Usando ~2 m total: $20.  
- **Parafusos, porcas, T-nuts:** pacotes de M6/M8 (~$0,5 cada), T-nuts ($0,75 cada), roscas M3 para placas (~$0,2 cada). Total estimado ~$15.  
- **Molas:** $2–5 cada. Uma ou duas molas: $10.  
- **Índice de posicionamento (pinos):** $3–5 cada (pequenos pinos locadores), usar 4: ~$20.  
- **Sensores (E18, VL53L0X, KY-040):** ~E18 ($5), VL53L0X ($5), KY-040 ($1). = $11.  
- **Câmeras:** (supõe RPi Cam HQ ~$50 cada) x3 = $150 (se não fornecidas).  
- **Filamentos:** por peça, 100–300g. Total ~2 kg de PETG ($30/kg) = $60. TPU ($40/kg, mas só 100g) ~$4.  
- **Outros (cabos, correntes, EVA):** $20.  

**TOTAL ESTIMADO:** ≈$300 (hardware + matéria). Este preço inclui itens confirmados (sensores) e estimados. Custos de grampo/plasticos impressos são insignificantes em comparação.  

## Riscos Bloqueadores  

- **Dados não obtidos:** Largura exata da esteira, massa dos componentes montados e aceleração máxima da esteira (todos BLOQUEADOS). Sem eles, cálculos de força e dimensionamento de molas são especulativos. Solução: medir na bancada.  
- **Comportamento da mola sob vibração:** sem ensaio real, não sabemos se a mola (Opção B) manterá tensão vs. fadiga. Marca-se como BLOQUEADO até teste.  
- **Precisão do eixo do rolamento do encoder:** se o encoder não girar em sincronia com a esteira, a medição será errada. Precisa avaliar montagem física (LIkely, baseado em design).  
- **Câmera e iluminação interferência:** potencial reflexo ou sombra não previsto (apenas verificado em protótipo).  
- **Incerteza de tolerâncias da impressora:** cada máquina varia; até calibrar, dimensões projetadas podem não corresponder. A compensação manual será necessária (BLOQUEADO até ajustar protótipo P0).  
- **Integração elétrica:** não detalhada aqui, mas cabe mencionar: circuitos da câmera/illuminador e necessidades de alimentação. (Fora do escopo mecânico).  

Se algum teste falhar severamente (ex.: molas não funcionarem conforme esperado), bloqueia o uso de determinada arquitetura (ex., B). Cada risco será tratado via prototipagem e teste na bancada, conforme listamos nos itens experimentais.  

## Perguntas em Aberto (para bancada)  

- **Largura real da esteira:** medir intervalo (min e max).  
- **Peso e CG das câmeras:** inclusive peso do cabo em extensão.  
- **Perfil exato da esteira (superfície):** para desenhar sapatas que não danifiquem.  
- **Carga e vibração típicas:** frequência e amplitude da esteira.  
- **Condições térmicas operacionais:** quanto calor ambiente + lâmpadas elevarão a temperatura local.  
- **Força lateral típica exercida pelo fluxo de garrafas (impactos):** medir força de colisão.  
- **Material específico das sapatas:** definir entre TPU vs EVA (exame de durabilidade real).  

Responder essas questões requer medições diretas ou informação do equipamento de bancada. Enquanto isso, marcaremos como BLOQUEADO todo item dependente dessa falta de dados.

## Próximo Experimento Mínimo  

- **P0 (encaixe geométrico):** Imprimir peças de dimensões chaves (sem molas/pinos, apenas escala de ajuste) em PLA. Montar na esteira para verificar alcance.  
- Se P0 evidenciar necessidade de ajuste de parâmetros (por exemplo, perfis muito curtos ou longos, ajustes de escala), refinar CAD antes de avançar.  

Esse é o experimento mínimo: sem ele, qualquer cálculo de forças é especulativo. O P1 e P2 só fazem sentido após confirmar a geometria funcional em P0.  

## Referências  

- Especificações da Creality K1C (K1C 2025): manual e brochura oficial.  
- Comparativo de materiais 3D (HDT e creep): DFAM Academy Guide (2026).  
- Diretrizes de tolerância para impressão 3D (FDM): Makelab “3D Printing for Engineers”.  
- Inserções em partes plásticas 3D: DigiKey Tips (Best Practices).  
- Indexação de pinos e clamping precision: ROEMHELD FSS System.  

As regras de evidência acima foram aplicadas: itens explicitamente confirmados têm citação (CONFIRMED); estimativas e design baseado em literatura ou cálculo básico estão marcados como LIKELY/SPECULATIVE; informações não encontradas (ex.: largura da esteira) estão BLOQUEADAS e requerem medida.

