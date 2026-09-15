# Decisões de projeto

Este documento registra decisões arquiteturais, direções técnicas e questões ainda abertas do projeto. Cada decisão distingue o que já foi adotado do que ainda depende de prova de conceito, medição no hardware ou revisão técnica.

Uma direção adotada orienta os requisitos e a implementação, mas não representa validação do componente, atendimento de meta ou resultado medido. As decisões devem ser revisadas quando surgirem novas evidências, preservando o histórico das posições anteriores.

## D-01: Bancada de teste

- Opções:
  - A: trilho deslizante artesanal com carrinho em velocidade controlada, mecanismo de medição de movimento e trigger no ponto de captura.
  - B: esteira motorizada comercial.
- Direção adotada: A, documentada como bancada em escala reduzida.
- Regra: resultados obtidos na bancada não devem ser apresentados como validação em linha industrial real.
- A decidir: estabilidade mecânica, controle de velocidade, repetibilidade do disparo, tolerâncias de montagem e mecanismo definitivo de medição, validados na PoC 03.
- Fora do escopo atual integração com linha industrial real.

## D-02: Composição do dataset

- Opções:
  - A: dataset próprio, composto por fotografias de tampas e peças 3D com deformações controladas, como fonte primária.
  - B: utilizar apenas datasets públicos.
  - C: utilizar dataset público como fonte primária e o dataset próprio como complemento.
- Direção adotada: A, com datasets públicos utilizados apenas como apoio metodológico.
- Regra:
  - cada imagem deve preservar proveniência, classe, vista, setup e identificação da divisão de dados;
  - treino, validação e teste devem permanecer separados;
  - amostras derivadas do mesmo item não podem ser distribuídas entre conjuntos de forma que provoquem vazamento de dados;
  - métricas devem ser acompanhadas da população de teste e das condições de captura.
- A decidir: volume, balanceamento, cobertura das classes, critérios de exclusão e composição final dos conjuntos, confirmados nas PoCs 01 e 02.
- Alternativa não adotada B, por não garantir cobertura controlada das classes e das condições da bancada.

## D-03: Câmeras

- Opções:
  - A: duas câmeras CSI e uma câmera USB UVC.
  - B: câmera única com espelho.
  - C: módulo multicâmera comercial.
- Direção de implementação: A.
- Regra:
  - cada câmera deve possuir identificação estável;
  - disponibilidade, timestamp e qualidade devem ser preservados por vista;
  - uma vista ausente ou inválida não pode ser apresentada como captura completa;
  - a associação das três imagens ao mesmo `item_id` deve ser validada.
- A decidir: modelos definitivos, largura de banda, janela temporal, compatibilidade com o trigger e comportamento diante de falha de uma câmera, confirmados na PoC 03.
- Alternativas B e C permanecem como fallback, condicionadas à necessidade e à validação no hardware.

## D-04: Fusão multi-view por domínios

- Opções:
  - A: um classificador por vista, com decisões organizadas nos domínios da tampa e do corpo.
  - B: concatenação das imagens como canais de uma única entrada.
  - C: fusão por atenção entre as vistas.
- Direção adotada: A.
- Regra arquitetural:
  - ~~a vista superior decide isoladamente o domínio da tampa;~~ *(INCORRETO: ver emenda abaixo e D-23)*
  - as duas vistas laterais fornecem as evidências do domínio do corpo (e da tampa);
  - a vista de topo atua apenas como check dimensional independente;
  - não existe maioria global entre as três câmeras;
  - defeito detectado em qualquer domínio reprova o item;
  - o resultado de um domínio não pode cancelar defeito detectado pelo outro;
  - disponibilidade, qualidade, confiança e origem devem ser preservadas por vista;
  - quando nenhum defeito for detectado, mas a evidência necessária estiver ausente, inválida ou abaixo dos critérios mínimos, o domínio afetado e o item devem permanecer `inconclusivos`;
  - evidência insuficiente não pode ser convertida em aprovação silenciosa.
- A decidir: regra para combinar as duas vistas laterais, tratamento definitivo da discordância lateral e limiares mínimos de qualidade e confiança, validados nas PoCs 01 e 02.
- Alternativas não adotadas no núcleo B e C, por aumentarem o acoplamento entre vistas e dificultarem a preservação explícita da vista ausente e da decisão por domínio.

### Emenda a D-04 (2026-09-11): a vista superior NAO decide a tampa

A decisao original ("a vista superior decide isoladamente o dominio da tampa") esta **incorreta**: a
vista de topo nao tem informacao suficiente para decidir a tampa sozinha. A decisao da tampa passa a
rodar nas **duas vistas laterais**; a vista de topo permanece como **check dimensional independente**,
cuja unica funcao e verificar que a dimensao nao foi violada (pode escalonar, nunca aprovar sozinha).
Ver D-23.

## Nota de conformidade (2026-09-11):
o estado atual da implementação da PoC-04 usa uma vista como maioria global, o que contradiz a regra desta
decisão ("não existe maioria global entre as três câmeras"). Registrado
como não-conformidade aberta, não como mudança de direção. A regra
permanece D-04 (+ emenda); a implementação deve ser corrigida para
aderir, não o contrário.

## D-05: Topologia da demonstração

- Opções:
  - A: sensores físicos, um nó de visão e um hub central.
  - B: um único nó concentrador.
  - C: nós distribuídos completos.
- Direção de implementação: A, com possibilidade de extensão.
- Regra:
  - aquisição física, captura, classificação, combinação das decisões, persistência e telemetria devem permanecer observáveis;
  - a indisponibilidade de um nó deve produzir estado explícito;
  - a topologia deve preservar a associação dos eventos ao mesmo `item_id`.
- A decidir: número definitivo de sensores, distribuição dos serviços, carga da demonstração e política de fallback, confirmados nas PoCs 04 e 05.

## D-06: Separação do item reprovado para análise manual

- Opções:
  - A: mecanismo no fim do trilho que direciona o item reprovado para análise manual, com confirmação física por sensor independente.
  - B: apenas sinalização, sem separação física.
  - C: descarte automático do item.
- Direção adotada: A, preservando o ciclo detectar, separar, analisar, corrigir e registrar.
- Regra arquitetural:
  - a emissão da ordem de atuação não representa separação concluída;
  - os estados de decisão, comando, atuação e confirmação devem permanecer distintos;
  - a confirmação deve ser associada ao mesmo `item_id`;
  - a ausência de confirmação dentro do timeout deve produzir estado de falha;
  - o item separado deve permanecer disponível para análise humana;
  - nenhum item classificado como normal pode ser direcionado intencionalmente ao caminho de análise manual.
- A decidir: tipo de atuador, modelo e interface elétrica do sensor de confirmação, posicionamento físico, timeout, comportamento diante de falha e procedimento de parada manual. A decidir: PoC dedicada, ainda não numerada na lista atual (PoC-01 a PoC-07 + Final).
- Alternativa descartada C, por eliminar a análise humana e introduzir risco de descarte incorreto.

### Emenda a D-06 (2026-09-11):  separação física é Expansão, não núcleo
- A "Direção adotada: A" original está incoerente com docs/escopo.md, que
exclui ejeção, atuador, rotação mecânica e descarte automático do núcleo,
e com requisitos.md, que já marca RF-14 (encaminhamento sem controlar
atuação física) como Expansão.

- Direção corrigida: A passa a ser condicional (Expansão), sujeita a PoC
dedicada e aprovação de prazo — mesmo tratamento dado a D-10/D-11/D-12.
Fallback do núcleo: opção B (apenas sinalização, sem separação física),
que corresponde ao que RF-14 já permite.

A regra e o ciclo detectar → separar → analisar → corrigir → registrar
permanecem válidos como desenho da expansão, não como comportamento
exigido do núcleo.

## D-07: Medição dimensional da tampa

- Opções:
  - A: medição em milímetros com referência física, calibração pixel para milímetro e limite dimensional, mantendo o modelo como camada complementar.
  - B: utilizar apenas o classificador.
- Direção condicional: A, por permitir uma decisão dimensional rastreável, desde que a precisão seja validada.
- Regra:
  - a medição deve preservar unidade, referência, câmera, posição e versão da calibração;
  - calibração inválida ou geometria alterada deve impedir o uso conclusivo da medida;
  - a medição dimensional não pode ser apresentada como validada sem ensaio no setup.
- A decidir: viabilidade da meta de erro absoluto máximo de 0,5 mm, método de calibração, geometria de iluminação e limite dimensional, confirmados por PoC e medição de aceite.
- Fallback: B, caso a precisão dimensional não seja atingida de forma reproduzível.

## D-08: Kit de golden samples

- Opções:
  - A: kit de amostras normais e defeituosas conhecidas para injeção controlada na demonstração, isolado dos indicadores produtivos.
  - B: utilizar somente itens comuns do lote.
- Direção adotada: A.
- Regra:
  - cada amostra deve possuir identificação individual e classe esperada;
  - os eventos devem ser marcados com `is_golden`;
  - os resultados não devem compor os indicadores produtivos;
  - a quantidade de amostras deve seguir as classes aprovadas e a disponibilidade real, sem número arbitrário previamente fixado.
- A decidir: quantidade, taxonomia, rótulos, armazenamento e protocolo de uso na demonstração.

## D-09: Relatório de lote como evolução

- Opções:
  - A: relatório em PDF com indicadores, severidade, evidências, qualidade dos dados e tendência, acompanhado do status de envio da notificação.
  - B: manter somente o dashboard e os registros consultáveis.
- Direção condicional: A, desde que os requisitos essenciais e a integração do hub estejam validados e exista prazo disponível.
- Regra:
  - o relatório não pode preencher campos ausentes com valores estimados ou inventados;
  - registros parciais, inválidos ou inconclusivos devem permanecer identificados;
  - o relatório deve preservar a identificação do lote e a origem dos indicadores.
- A decidir: inclusão na demonstração, formato, conteúdo, canal, tratamento de dados parciais e orçamento de implementação.
- Fallback: B, caso o relatório não seja aprovado para a entrega atual.

## D-10: Camada evolutiva de descritores geométricos

- Opções:
  - A: descritores geométricos clássicos com score de anomalia calibrado sobre um conjunto de itens normais.
  - B: modelos de visão de maior custo computacional.
  - C: não incluir camada adicional de descritores ou generalização.
- Direção condicional: A, como camada evolutiva independente da decisão principal.
- Regra:
  - a camada não deve substituir os classificadores dos domínios da tampa e do corpo;
  - o resultado não deve alterar silenciosamente a decisão principal;
  - cada resultado deve preservar vista de origem, versão do algoritmo e versão da calibração;
  - alegações de generalização somente podem ser feitas dentro da população efetivamente testada.
- A decidir: descritores utilizados, limiar, taxa aceitável de falsos positivos, ganho mensurável e custo de execução no Raspberry Pi 5.
- Critério de continuidade aprovação em PoC isolada, atendimento ao orçamento de latência e decisão registrada.
- Fallback: C, mantendo somente os classificadores do núcleo.

## D-11: Detector evolutivo de anomalia

- Opções:
  - A: detector autossupervisionado treinado somente com imagens normais e transformações sintéticas versionadas.
  - B: abordagem baseada em reconstrução.
  - C: não incluir detector adicional de anomalia.
- Direção condicional: A, sujeita a PoC isolada e sem participação na regra principal de decisão por domínios.
- Regra:
  - o conjunto de treino deve preservar a proveniência e conter somente as amostras definidas como normais;
  - transformações sintéticas, configuração e sementes devem ser versionadas;
  - o detector deve produzir score e estado separados;
  - o resultado não pode cancelar reprovação produzida pelo núcleo;
  - treino, validação e teste devem permanecer separados.
- A decidir: método específico, métrica, alvo de desempenho, população de validação, orçamento de latência e forma de integração.
- Fallback: C, mantendo o núcleo supervisionado quando a camada não demonstrar ganho mensurável ou exceder o orçamento de desempenho.

## D-12: Execução evolutiva do detector de anomalia na borda

- Opções:
  - A: destilação professor-aluno, com o professor utilizado somente durante o treinamento e o aluno quantizado validado no hardware-alvo.
  - B: executar o modelo professor no hardware-alvo.
  - C: não implantar essa camada na borda.
- Direção condicional: A, somente após a validação do modelo professor e a aprovação da D-11.
- Regra
  - o modelo professor não integra a solução operacional no Raspberry Pi 5;
  - o modelo aluno deve possuir versão, runtime e parâmetros de quantização identificados;
  - resultados de outro hardware não substituem o benchmark no Raspberry Pi 5.
- A decidir formato de quantização, runtime, limite aceitável de perda de qualidade, latência, consumo de memória e comportamento de fallback.
- Critério de continuidade: benchmark reproduzível do modelo aluno no Raspberry Pi 5, dentro do orçamento definido antes do ensaio.
- Fallback: C, caso o aluno não preserve qualidade suficiente ou exceda o orçamento de execução.

## D-13: Expansão evolutiva do dataset

- Opções:
  - A: utilizar sinais produzidos pelo sistema, como medidas dimensionais, descritores, scores de anomalia e funções de rotulagem versionadas.
  - B: utilizar somente anotação manual.
  - C: combinar sinais automáticos e revisão humana.
- Direção condicional: C, preservando incerteza, conflitos e origem de cada rótulo.
- Regra:
  - nenhum rótulo produzido automaticamente deve ser promovido a confirmado sem rastreabilidade;
  - devem ser preservados a função de rotulagem, sua versão, peso, evidência e política de revisão;
  - conflitos entre fontes de rótulo devem permanecer explícitos;
  - o resultado do próprio sistema não deve ser utilizado automaticamente como verdade de referência.
- A decidir: funções de rotulagem, pesos, limiares, política de revisão humana, critérios de promoção e inclusão dessa evolução no prazo do projeto.
- Observação: a validação física do timestamp pertence ao núcleo de qualidade e correlação do rig e não depende da aprovação da expansão automática do dataset.

## D-14: Rigor de processo

- Opções:
  - A: testes de resiliência executados como experimentos com hipótese falsável, métrica prévia e revisão de logs.
  - B: testes ad hoc sem protocolo definido.
- Direção adotada: A, acompanhada de commits estruturados.
- Regra:
  - cada experimento deve registrar hipótese, estado inicial, estímulo, impacto máximo permitido, métrica e critério antes da execução;
  - o resultado deve registrar recuperação, perdas, estados observados e decisão;
  - teste sem hipótese, métrica ou evidência não comprova resiliência;
  - falha ou hipótese rejeitada deve permanecer registrada.
- A decidir: protocolo definitivo, cobertura dos cenários e critérios de interrupção, confirmados na PoC 06.

## D-15: Estabilidade mecânica e elétrica

- Opções:
  - A: conexões críticas fixadas, painel rígido, suportes parafusados e gabarito de posicionamento.
  - B: montagem baseada apenas em jumpers e suportes por fricção.
- Direção adotada: A, como pré-requisito físico para obtenção de métricas reproduzíveis.
- Regra:
  - conexões críticas devem permitir testes de continuidade, polaridade e isolamento;
  - câmeras, sensores e mecanismo de medição devem possuir fixação repetível;
  - a montagem deve preservar a geometria de captura e a calibração dentro da tolerância definida;
  - gabinetes devem ser desenvolvidos depois da estabilização das interfaces e dimensões.
- A decidir: tolerâncias, materiais, sequência de montagem e critérios de reposicionamento, confirmados na PoC 03 e nos ensaios mecânicos.

## D-16: Princípio transversal de testabilidade

- Opções:
  - A: design for testability como critério transversal, com controlabilidade e observabilidade explícitas.
  - B: definir a testabilidade somente depois da implementação.
- Direção adotada: A.
- Regra:
  - cada requisito deve possuir entrada ou condição controlável;
  - cada saída, estado e falha relevante deve ser observável;
  - a evidência deve seguir a sequência `fisica -> dados -> modelo -> teste -> documentacao`;
  - requisito sem estímulo controlável, resultado observável ou evidência reproduzível não pode ser considerado aceito;
  - evidência parcial, inválida ou inconclusiva deve manter seu estado explícito.
- A decidir: artefato final da matriz DFT e cobertura mínima exigida antes da demonstração.
- Verificação: revisão das fichas de requisitos, arquitetura, PoCs e evidências associadas.

## D-17: Grip de câmeras

- Opções:
  - A: módulo ajustável em trilhos com trava.
  - B: painel fixo de bancada.
- Direção condicional: A, desde que a estabilidade mecânica seja validada após montar, calibrar, mover, reposicionar e medir.
- Regra:
  - o grip deve preservar posição, orientação e distância da câmera dentro da tolerância definida;
  - os ajustes devem possuir mecanismo de travamento;
  - a estrutura não deve ser descrita como compatível com qualquer esteira sem validação dimensional;
  - as interfaces devem ser parametrizadas sempre que possível no FreeCAD.
- A decidir: mecanismo de fixação, faixa de ajuste, tolerância de calibração, material, orientação de impressão e método de travamento, validados no laboratório.
- Detalhes em `docs/design/grip-extensivel.md`.

### Emenda a D-17 (2026-09-11): fixação por trilho DIN TS35 de 50 cm
- Direção corrigida: o rig R05 adota trilho DIN TS35 (IEC 60715, 35 mm),
comprimento de 50 cm, como mecanismo de fixação — com peças já
construídas (case Pi5 DIN, angle adapter 90°, bracket M6). Isso
substitui a direção anterior de perfil T-slot de alumínio (2020/2040)
descrita em D-17 e em docs/design/grip-extensivel.md.

- Consequência: as opções A (garra M6/M8) e B (spring-loaded) de
grip-extensivel.md ficam sem objeto — o mecanismo de fixação já não é
mais uma decisão em aberto, é o trilho DIN TS35 de 50 cm.
grip-extensivel.md deve ser marcado como proposta supersedida por esta
emenda, preservando o documento como histórico.

- A decidir: posicionamento do trilho na esteira/bancada, fixação do
próprio trilho DIN à estrutura, e se as SPECs futuras de mount (como a
do CM3 Wide) devem referenciar esta emenda em vez de tratar o DIN TS35
como premissa silenciosa.

## D-18: Iluminação sincronizada à captura

- Opções:
  - A: iluminação contínua controlada.
  - B: iluminação pulsada sincronizada ao trigger, com intensidade, duração e canais configuráveis.
  - C: iluminação pulsada com elemento difusor candidato.
- Direção condicional: avaliar B e C na PoC 03, comparando-as com A quando aplicável.
- Regra elétrica:
  - os LEDs devem possuir limitação de corrente dimensionada;
  - cargas acima da capacidade da interface não devem ser alimentadas diretamente pelos GPIOs;
  - o circuito de acionamento deve ser compatível com a corrente, tensão e frequência previstas;
  - duração do pulso, corrente, tensão e temperatura devem ser observáveis.
- Regra óptica:
  - canais, intensidade e duração devem ser calibrados pelas imagens;
  - saturação, reflexos, uniformidade e estabilidade da exposição devem ser avaliados;
  - o difusor deve ser tratado como alternativa candidata, e não como garantia de eliminação de hotspots;
  - a ativação simultânea dos canais RGB em potência máxima não deve ser presumida como iluminação branca adequada.
- A decidir: fonte de iluminação, quantidade e modelo dos LEDs, circuito de acionamento, alimentação, duração do pulso, intensidade, combinação dos canais, necessidade de difusor, material e geometria.
- Critério de continuidade: a configuração somente pode ser aprovada se atender aos limites elétricos e térmicos e produzir imagens adequadas à extração das evidências necessárias.

## D-19: Divisão de responsabilidades entre ESP32 e Raspberry Pi 5

- Opções:
  - A: conectar sensores e atuadores diretamente ao Raspberry Pi 5.
  - B utilizar o ESP32 para aquisição dos sinais físicos e controle temporal, mantendo captura, visão computacional, persistência e serviços do hub no Raspberry Pi 5.
- Direção adotada B.
- Responsabilidades previstas do ESP32:
  - ler o sinal do sensor de presença adotado;
  - aplicar debounce e detectar eventos duplicados;
  - registrar timestamps monotônicos locais;
  - ler o mecanismo de medição de movimento aprovado;
  - comandar iluminação e atuação por interfaces elétricas dimensionadas;
  - transmitir eventos e estados ao Raspberry Pi 5.
- Responsabilidades previstas do Raspberry Pi 5
  - coordenar a captura das câmeras;
  - associar as vistas ao `item_id`;
  - executar os classificadores;
  - combinar as decisões por domínio;
  - persistir dados;
  - disponibilizar telemetria, dashboard e demais serviços do hub.
- Justificativa: separar aquisição e controle temporal das tarefas de captura, inferência e persistência reduz o acoplamento entre o processamento de visão e os sinais físicos.
- A decidir: protocolo entre as placas, sincronização dos relógios, política de retransmissão, tratamento de reinicialização, latência da comunicação e comportamento de fallback.
- Observação: E18-D80NK, VL53L0X, KY-040 e demais componentes somente devem aparecer como dispositivos operacionais definitivos depois que sua função estiver definida e sua adequação for validada na PoC correspondente.

## D-20: Validação do E18-D80NK como sensor de presença

- Caracterização do componente: o E18-D80NK é um sensor fotoelétrico infravermelho de reflexão difusa e deve ser tratado como componente candidato.
- Opções:
  - A: utilizar o E18-D80NK em sua operação por reflexão difusa, ajustando distância e sensibilidade para o setup.
  - B: ensaiar um arranjo experimental com anteparo refletivo, documentando que isso não transforma o componente em sensor de barreira ou retrorrefletivo dedicado.
  - C: substituir o E18-D80NK por sensor de princípio mais adequado caso as condições ópticas da bancada impeçam detecção confiável.
- Direção de ensaio: avaliar A e, se necessário, B na PoC 03, mantendo C como alternativa de substituição.
- Regra: nenhuma configuração pode ser declarada confiável para garrafas transparentes, translúcidas, coloridas, opacas, vazias ou com líquido antes da medição no setup.
- A decidir: posição, distância, orientação, sensibilidade, debounce, influência do fundo, desempenho por tipo de garrafa e componente alternativo.
- Critérios mínimos da PoC:
  - registrar falsos positivos, falsos negativos e eventos duplicados;
  - ensaiar as variações de garrafa previstas no projeto;
  - preservar setup, distância, orientação e regulagem;
  - verificar repetibilidade;
  - produzir decisão `go`, `adaptar`, `substituir` ou `repetir`.
- Observação: fita refletiva, anteparo e inclinação devem permanecer como parâmetros experimentais, e não como características validadas do E18-D80NK.

## D-21: Mecanismo de medição de movimento

- Opções:
  - A: utilizar inicialmente o módulo KY-040 como encoder incremental candidato, mecanicamente acoplado ao elemento móvel.
  - B: utilizar encoder incremental óptico, magnético ou industrial com montagem adequada ao rig.
  - C: estimar o movimento somente por timestamps de passagem, sem encoder contínuo.
- Direção de ensaio: A na PoC 03, sem considerar o KY-040 aprovado antecipadamente.
- Justificativa: o KY-040 permite testar a cadeia de leitura incremental disponível, mas sua adequação à medição contínua do rig depende de resolução, acoplamento, estabilidade e comportamento dinâmico.
- A decidir: método de acoplamento, resolução necessária, conversão entre pulsos e deslocamento, sentido de rotação, velocidade máxima, limiar de perda de pulsos e componente definitivo.
- Critérios mínimos da PoC:
  - executar deslocamentos conhecidos e repetidos;
  - medir a variação entre repetições;
  - verificar pulsos falsos e perda de pulsos;
  - verificar escorregamento e estabilidade da montagem;
  - ensaiar as velocidades previstas;
  - detectar desconexão ou sinal inválido;
  - produzir decisão `go`, `adaptar`, `substituir` ou `repetir`.
- Fallback: adotar a opção B se o KY-040 não demonstrar qualidade suficiente para a correlação das vistas e a estimativa do throughput.

## D-22: Separação entre núcleo e requisitos evolutivos

- Núcleo mínimo:
  - captura das três vistas;
  - associação das imagens ao mesmo `item_id`;
  - classificação dos domínios da tampa e do corpo;
  - decisão final por domínio;
  - tratamento de evidência insuficiente;
  - rastreabilidade;
  - telemetria;
  - persistência;
  - dashboard;
  - separação confirmada para análise manual.
- Requisitos condicionais: RF-13, RF-14, RF-17, RF-18, RF-19, RF-21, RF-23 e RF-30.
- Direção adotada requisitos condicionais somente entram na implementação depois da aprovação da PoC aplicável, da verificação do orçamento de desempenho e da confirmação de prazo.
- Regra:
  - requisito condicional não pode bloquear a validação do núcleo;
  - documentação ou código inicial não representa aprovação;
  - inclusão, adaptação, retirada ou adiamento deve ser registrado;
  - requisitos condicionais devem possuir fallback que preserve o funcionamento do núcleo;
  - requisito condicional sem evidência suficiente deve permanecer aberto ou ser adiado.
- A decidir: quais requisitos condicionais serão promovidos para a demonstração após as PoCs essenciais.

## D-23: Vista decisoria da tampa (duas laterais + topo como check)

- Contexto: RF-03 exige "composicao multi-view" (`requisitos.md`); D-04 afirmava que a vista superior
  decidia isoladamente, o que o usuario corrigiu como erro.
- Decisao: a classificacao da tampa roda nas **duas vistas laterais** (medida de tilt/arco por vista,
  fusao determinista preservando discordancia, D-04 no que segue valido). A vista de **topo** e um
  **check dimensional independente**: sua unica funcao e verificar que a dimensao nao foi violada; ela
  **nao aprova** o item e, quando violada, **escalona** o caso.
- Consequencia: a matriz da PoC-02 e por item, com a vista lateral como via decisoria e o topo como
  veto/flag dimensional; a taxa de escalonamento por motivo entra no resultado.
- A calibrar empiricamente: qual grandeza do topo constitui "dimensao violada" e o limiar dela.

## D-24: Nenhum limiar de aceitacao sem fonte ou validacao empirica

- Contexto: `politica_tampa.py` fixa `tilt_incerto=2,0`, `tilt_reprova=4,0` e `altura_ausente_px=3,0`;
  os dois primeiros vem de **erro de medicao** (`reference/medicao-vies-elipse-geometria.md`) e o
  terceiro nao tem fonte. A regra do arquivo exige criterio definido antes do ensaio.
- Decisao: todo limiar usado como criterio de aceitacao precisa de (a) fonte primaria citada com
  `arquivo:linha`, ou (b) **validacao empirica registrada** (protocolo, `n` e resultado). Limiar sem
  nenhum dos dois **nao pode ser usado como criterio**: serve apenas como parametro provisorio, marcado
  como tal. Toda avaliacao registra o bloco de limiares usado (versionado).
- Estado atual: `arco_visivel_min_graus` tem fonte; tilt e altura **nao tem** (parametros provisorios).

## D-25: Metrica da PoC-02 por classe, com IC, FP separado e imagem anotada

- Contexto: `classificacao.py` devolvia acuracia **global** com limiar unico, sem IC e sem FP: nao
  atende RNF-02 ("acuracia com intervalo de confianca", por classe) nem RNF-03 (FP separado de FN).
- Decisao: a avaliacao passa a produzir, **por classe**: recall com IC de Wilson 95% (e
  Clopper-Pearson quando disponivel), `n` declarado, FP separado de FN e de erro tecnico, taxa de
  inconclusivo e taxa de escalonamento por motivo. Alem disso, cada item avaliado gera **imagem
  anotada** mostrando o que discriminou a decisao (classe prevista x verdadeira, confianca, medidas e
  motivos).
- Implementado em: `code-workspace/scripts/avaliar_poc02.py` (+ `tests/test_avaliar_poc02.py`).
- Consequencia: a acuracia global agregada deixa de ser criterio; nenhum numero pode ser publicado como
  "RNF-02 atendido" sem o limite inferior do IC.

## D-26: Fronteira entra no conjunto; inconclusivo e classe propria

- Decisao: amostras de fronteira (rosca parcial/alinhamento limitrofe) entram no conjunto de teste e a
  confusao que produzem e reportada; `inconclusivo` e classe propria da matriz e **conta como erro** para
  o recall da classe verdadeira. Inconclusivo acima de 10% dos itens torna o resultado
  **nao decidivel** (nunca aprovacao silenciosa).
- Consequencia: o manifest registra quantos itens sao de fronteira e a definicao operacional usada.

## D-27: Composicao de fontes com procedencia por numero

- Decisao: a PoC-02 usa uma **composicao de todas as referencias e datasets disponiveis** (conjunto
  proprio + corpus publico + referencias bibliograficas), mas **metrica nunca e agregada entre fontes**:
  cada `fonte` tem seu proprio bloco (recall/IC/FP), e todo numero publicado carrega a sua origem.
- Consequencia: resultado de dataset publico nao responde ao RNF-02 do projeto; serve a metodo,
  convencao de rotulo e bootstrap. O conjunto proprio continua sendo o unico que responde ao RNF.

## D-28: Vocabulario canonico das classes

- Decisão: as classes são declaradas **por domínio**, e nenhuma classe pode ser emitida fora do seu domínio.
  - domínio da tampa (PoC-02): `normal`, `tampa_ausente`, `defeito_tampa`, `inconclusivo`
    (**emendada pela D-31**: `tampa_mal_rosqueada` deixou de ser classe e passou a ser código do
    catálogo, que agrupa mal rosqueada, danificada e aberta);
  - domínio do corpo (PoC-03, RF-04): `normal`, `deformidade`, `inconclusivo`. O vocabulário é fixado aqui
    para o domínio não ficar sem nome; `deformidade` não é classe válida no domínio da tampa, e as classes
    de tampa não são válidas no domínio do corpo;
  - `analise_humana` **não é classe**: é estado de roteamento do item (D-06/D-30) e não entra em matriz de
    confusão;
  - `suspeita` não é termo canônico: o que o material de apresentação chamou de "suspeita" (ROTEIRO-VIDEO,
    CHECKLIST-RUBRICA, Roteiro.tex) é, na norma, `escalonado` com motivo declarado, ou `inconclusivo`.
- Consequência: relatórios e matrizes usam apenas esse vocabulário, por domínio; o enum do código passa a
  carregar o domínio e a recusar par classe x domínio incoerente (a fazer em `events.py`).

## D-29: Regra de fusao por dominio implementada (PoC-04)

- Contexto: `fusion.py` votava por **maioria global** entre vistas e, com empate, mandava para analise
  humana. Isso contradiz D-04 ("nao existe maioria global entre as tres cameras") e D-11 (a camada
  secundaria nao cancela reprovacao): uma vista reprovando podia ser **cancelada** pelas outras.
- Decisao: a fusao passa a ser por **dominio** (`fundir()`), com estas regras declaradas:
  - o **papel** da vista e declarado no rig: `lateral1`/`lateral2` = decisorias, `topo` = check
    dimensional. Vista fora desse conjunto e **erro** (fail closed), nao suposicao;
  - cada vista emite uma medida por dominio (tampa/corpo) e o par dominio x classe e validado: classe
    incoerente com o dominio e recusada na criacao da medida;
  - **defeito detectado em qualquer vista do dominio reprova** o item, com precedencia declarada
    (`tampa_ausente` > `defeito_tampa`; empate de classe resolvido por maior confianca) [D-31];
  - **aprovacao exige todos os dominios medidos emitindo `normal` com qualidade ok**; qualquer
    ausencia, qualidade insuficiente ou inconclusivo produz `inconclusivo` -- nunca aprovacao silenciosa;
  - o **check dimensional** (topo) nao classifica nem aprova: `escalona`/qualidade ruim/motivo
    declarado escalam o item para analise humana;
  - **discordancia lateral** = as vistas decisorias de um dominio NAO emitiram a mesma classe
    (cobre "defeito x normal" e "defeito x defeito de outra classe"; vista unica nunca e
    discordancia). Fica em `discordancia_lateral` e nos `motivos`, junto com
    `classes_divergentes_<dominio>` quando as classes de defeito diferem;
  - a **origem** de cada medida (`view_id`, dominio, classe) e registrada no resultado;
  - o rig e **declarado** em `ConfiguracaoFusao` (numero de vistas decisorias por dominio, se o check
    e obrigatorio, quais dominios sao medidos): configuracao menor nao vira aprovacao -- dominio nao
    medido bloqueia a aprovacao e entra como motivo.
- Consequencia: a demonstracao com o rig v0 (1 vista de corpo) reporta `inconclusivo` para item normal
  em vez de aprovar por uma vista unica. E o comportamento correto pela regra, e o proximo passo
  declarado e a bancada de 2 laterais + topo.
- Implementado em: `code-workspace/src/pocs/poc04_fusao/fusion.py`,
  `code-workspace/src/pocs/events.py` (vocabulario D-28 + dominio/qualidade),
  `code-workspace/scripts/avaliar_poc04.py`, `code-workspace/tests/test_fusion.py`.
- Evidencia: harness `make poc04` (casos declarados com ground truth; falha se divergir) e o teste de
  mutacao que reverte a regra e exige que o harness acuse.

## D-30: Assento decisório da tampa (o classificador decide; a geometria é auxiliar)

- Contexto: D-07 e D-23 colocaram a camada geométrica (tilt, altura, arco) no assento decisório da tampa,
  com o classificador como segunda camada. A avaliação no conjunto próprio, sem confundimento classe x
  domínio, mostra o inverso: as features geométricas somam **+0,068** sobre o preditor constante (total
  0,523 em n=44), enquanto o classificador no recorte da vista soma **+0,523** (0,977; LB95 0,882). O tilt
  produzido não separa: nas 80 capturas normais do rig varia de 0,008 a 85,2 graus (p97,5 = 83,6).
- Decisão: a decisão da tampa é do **classificador no recorte da vista**, por domínio. A geometria passa a
  ser **auxiliar**, em dois papéis declarados:
  - **(a) explicação, sempre**: as medidas (tilt, altura relativa, arco, CNR na escala do produtor) entram
    no evento como rastro do que sustentou a decisão. Medida registrada não é voto;
  - **(b) fallback declarado**: acionado **somente** quando o classificador não pode decidir — indisponível
    ou inconclusivo. O resultado do fallback sai marcado como fraca confiança e **escala para análise
    humana**, com o motivo declarado.
- Travas duras:
  - a geometria **nunca aprova** e **nunca reprova sozinha**;
  - ausência de evidência continua `inconclusivo` — jamais aprovação silenciosa (D-04 preservada);
  - o fallback não pode ser apresentado como decisão: ele roteia.
- Medição dimensional: as capturas atuais não têm escala conferida, logo **não existe medida em
  milímetro**. Até haver referência dimensional no setup, a camada reporta grandeza **relativa**, e o
  diferencial de "medida dimensional explicável" é declarado como relativo, nunca como mm.
- Condição para o fallback virar confiável: aquisição controlada (fundo de contraste, câmera fixa,
  iluminação dedicada, escala conferida e piso de ruído medido **antes** de qualquer limiar). Enquanto isso
  não existir, o fallback existe como rastro e roteamento, não como critério de aceitação.
- Emenda: D-07 e D-23 perdem o **poder decisório** da geometria; o resto de ambas permanece — as medidas
  seguem obrigatórias como evidência e a vista de topo continua sem decidir (D-23). Histórico preservado.
- A decidir: (i) confiança mínima do classificador que dispara o fallback; (ii) se o fallback lê as duas
  vistas laterais ou apenas a disponível; (iii) o vocabulário do domínio do corpo (D-28).
- Implementado em (a fazer): `code-workspace/src/pocs/poc02_classificacao/` (papel das duas camadas) e
  `code-workspace/src/pocs/poc04_fusao/fusion.py` (precedência dentro do domínio, já compatível com D-29).
- Evidência: `aval_sem_confundimento.py` (mesmo domínio, n=44, recall por classe com IC de Wilson e baseline
  de preditor constante) e `aval_cnn_sem_conf.txt`, **a versionar no repositório**.

## Regra de atualização

Uma questão somente deixa o estado `a decidir` quando houver evidência de PoC, medição no hardware ou revisão técnica registrada no repositório.

Cada atualização deve registrar:

- decisão afetada;
- data e responsável;
- hipótese ou questão avaliada;
- setup e versões utilizados;
- métrica e critério definidos antes do ensaio;
- resultado observado;
- evidências;
- decisão `go`, `no-go`, `adaptar`, `substituir` ou `repetir`;
- impacto nos requisitos, arquitetura, dados e testes.

A nova evidência deve atualizar a posição sem apagar o histórico anterior. Direção adotada, componente instalado e meta numérica não equivalem a resultado validado. Evidência ausente, inválida ou inconclusiva não pode ser promovida a aprovação.

## D-31: Três classes na tampa (o detalhe vai para o catálogo)

- Contexto: o vocabulário da tampa tinha `normal`, `tampa_ausente`, `tampa_mal_rosqueada` e `inconclusivo`,
  e as classes de terceiros não mapeadas (tampa danificada 363, aberta 311, molhada 394, não conferida 114)
  ficavam paradas por falta de destino. Isso espalhava o dado por muitos rótulos com poucos itens cada.
- Decisão: a decisão da tampa passa a usar **três classes** — `normal`, `tampa_ausente`, `defeito_tampa`.
  `defeito_tampa` **funde** mal rosqueada, danificada e aberta. `tampa:molhada` fica **separada para
  avaliação** (394 imagens, fila `wp-I`): depende do caso, não é automaticamente defeito.
- O detalhe **não se perde**: o catálogo (`taxonomia_defeito`) mantém `TAMPA_MAL_ROSQUEADA`,
  `TAMPA_DANIFICADA` e `TAMPA_ABERTA` — os três apontando para a classe `defeito_tampa`. Decide-se
  simples; reporta-se detalhado; desdobrar depois é só mudar a projeção.
- Dado medido (imagens, origens únicas): `normal` 3.898 · `tampa_ausente` 821 · `defeito_tampa` 1.327 ·
  em avaliação 394 · inconclusivo 114. A classe de defeito passa de 653 para 1.327 (**2,03x**).
- Emenda: **RF-05/RNF-02** — o alvo `>=90%` passa a valer para `defeito_tampa` em vez de
  `mal_rosqueada`. Gate mais fácil de atingir e menos informativo; a granularidade fica nos códigos.
- Histórico preservado: a medição de 0,977 (n=44) continua interpretável — as 44 imagens têm exatamente
  os três estados, então a fusão **renomeia** uma classe sem tirar nem pôr imagem.
- Consequência técnica: o `CHECK` da coluna `classe` no esquema muda, e o esquema não migra (decisão
  declarada) — o banco é recriado. Feito em 2026-09-13, quando o banco não tinha dado de produção.
- Implementado em: `src-production/dominio.py` (enum + `VOCABULARIO`), `conformidade.py` (precedência),
  `registro.py` (`MAPA_CODIGO`), `esquema.sql` (CHECK + catálogo), `classificador.py` (prefixo ->
  `DEFEITO_TAMPA`). Os arquivos de dado mantêm o nome granular (`tampa_mal_rosqueada_frame_*`): é a
  camada 1 (célula) do desenho de nomes.

---

## D-32 — Autoridade entre o processo determinístico e o processo de IA

**Data:** 2026-09-13 · **Substitui, na parte de autoridade:** a D-30 (que dava a decisão ao
classificador com a geometria como auxiliar).

**Decisão:** o sistema passa a ter **dois processos** com autoridade declarada por classe:

- **Processo A (determinístico, com restrição)** — válido somente com rig fixo, câmera calibrada
  (intrínsecos + extrínsecos), iluminação estável, ROI declarada e profundidade fixa. Extrai a
  referência (a silhueta da peça), a escala em **mm**, a pose e as métricas de qualidade. Decide as
  classes que têm **assinatura física mensurável** (ausência de tampa, folga do anel acima do limite
  de especificação, altura/diâmetro fora da faixa da peça). Quando não consegue medir, devolve
  `inconclusivo` **com o motivo** — nunca um número inventado. Não requer imagem de defeito rotulada.
- **Processo B (IA generalista)** — recebe o mesmo **recorte canônico** no treino e na inferência (o
  padrão de dados). Decide as classes de **aparência e sutileza** (defeito fino de rosqueamento,
  estado de rótulo, domínio alheio). Requer dado rotulado e o **controle de domínio** como gate.
- **Discordância:** se A mede e B discorda, o item **não é aprovado** — vai para `inconclusivo` com as
  duas evidências no registro. Nunca se escolhe a evidência mais conveniente.
- **Rastro:** o registro grava **qual processo decidiu** e com que evidência (o campo `papel` das
  evidências passa a distinguir `decisorio` e `auxiliar`).
- **Avaliação separada:** cada processo é avaliado no seu domínio de validade (A: erro da medida em mm
  contra paquímetro numa amostra; B: matriz de confusão por classe com o controle de domínio). Métrica
  combinada só se publica com a base declarada: quantos itens cada um decidiu e quantos ficaram
  inconclusivos.

**Por que:** separar autoridade por assinatura física permite **atribuir o erro a quem errou** (hoje,
num número só, não se sabe se foi medição, recorte ou modelo), e **desbloqueia entrega**: A não
precisa de imagem de defeito, então pode ser construído e validado enquanto a coleta de B acumula.

**Critério de fechamento:** A validado com a medida em mm contra paquímetro numa amostra; B com o
controle de domínio abaixo do limiar declarado; e a taxa de inconclusivo publicada por motivo.

## D-33: Calibração do atraso trigger → captura medida pelo próprio rig (sem encoder)

- Contexto: o sensor de presença está a `d` mm do centro da ROI da câmera e a captura precisa
  ocorrer no atraso `tau* = d / v`. Nem a velocidade da esteira nem a escala mm/pixel do
  enquadramento são conhecidos a priori.
- Opções:
  - A: encoder (KY-040) para medir `v`, régua para `d`, cálculo de `tau* = d/v`.
  - B: rajada de quadros por passagem do item; a reta `offset(tau) = v*tau - d` medida na imagem dá a
    velocidade pela inclinação, o atraso pela raiz e a escala mm/pixel pelo intercepto com `d` da régua.
  - C: ajuste manual por tentativa e erro até a garrafa "parecer centralizada".
- Direção adotada: B em `src/pocs/expansao_sincronizacao/` (instrumento
  `scripts/calibrar_delay_trigger.py`). O encoder permanece como verificação cruzada quando
  disponível — vira teste independente, não pré-requisito da captura.
- Regra:
  - nada é aplicado sem veredito PASS (`n >= 5` amostras, `r2 >= 0,9`, resíduo <= tolerância, `tau* > 0`);
  - a janela da rajada tem de cobrir `tau*`; fora disso o número é extrapolação e o relatório avisa;
  - `d` é medido a régua e declarado no comando — é a única entrada que o método não mede sozinho.
- A decidir: rodada de bancada com a esteira real. O ensaio sem hardware (log de eventos real +
  câmera sintética) confere com a verdade injetada com erro de 0,0% a 0,5% em `tau*` e `v`.
- Alternativa não adotada C, por não produzir nem número nem incerteza.
- Alternativa A não descartada: se o encoder entrar, o confronto encoder × reta passa a ser a
  evidência de que a escala mm/pixel está correta.

## D-34: Medição fail-closed: amostra cortada não entra no ajuste e o atraso é por vista

- Opções:
  - A: usar o centróide de toda massa que aparecer na banda, inclusive item cortado pela borda.
  - B: descartar a amostra cujo item toque a borda do quadro e calibrar uma vez por vista.
  - C: manter um atraso global único para as três câmeras.
- Direção adotada: B.
- Regra:
  - item com massa na primeira ou na última coluna da banda é **descartado**: o centróide mediria
    apenas o pedaço visível. Medido em 2026-09-14: o mesmo ensaio dava 50% de erro em `tau*` com as
    amostras cortadas e 0,0% sem elas;
  - o atraso é gravado **por vista** (`~/poc03/delay.json`, chave `vistas`), porque cada câmera tem a
    sua distância ao trigger; calibrar uma vista não apaga as outras;
  - o consumidor é fail-closed: vista não calibrada devolve `FileNotFoundError`/`KeyError`, nunca zero;
  - ensaio reprovado com corte na borda é diagnóstico de trigger **fora do campo de visão**, não bug.
- A decidir: se na montagem final o trigger ficar fora do campo de visão, escolher entre aproximar a
  câmera, abrir a lente ou reduzir a distância trigger→ROI.
- Alternativa não adotada A, por contaminar a medida de forma invisível (o ajuste "passa" com número
  errado — pior que falhar).
- Alternativa não adotada C, porque as distâncias ao trigger são diferentes por construção.

## D-35: Teto de velocidade da esteira derivado do firmware do trigger

- Contexto: "concordar a velocidade da esteira com o trigger" tem três limites independentes, e o
  menor deles manda.
- Opções:
  - A: escolher a velocidade por percepção (a esteira "parece" adequada).
  - B: derivar o teto dos parâmetros reais do firmware (`esp/main.py`) e do orçamento de captura.
- Direção adotada: B, com os valores do firmware atual: `DEBOUNCE_MS=20` e `STABLE_READS=5` exigem
  **100 ms** de presença estável para abrir a janela; `ARM_MS=500` e `GUARD_MS=500` impõem **0,5 s** de
  re-armadura após cada item.
- Regra: o teto é `min(passo / (vistas*77 ms + rearme + margem), passo / 0,5 s, comprimento / 0,1 s)`.
  Com passo de 80 mm e três vistas: **~107 mm/s, ditado pelo orçamento de captura**; a 100 mm/s o
  intervalo é 800 ms com 49 ms de folga (apertado).
- Consequência operacional: para correr mais rápido é preciso aumentar o passo (mais espaço entre
  itens) ou reduzir o número de vistas. Aumentar a velocidade sem mexer nisso faz o trigger perder
  garrafas — e a perda é silenciosa, porque a janela simplesmente não abre.
- A decidir: passo e velocidade definitivos da bancada, medidos no ensaio real (o número acima é
  calculado com os parâmetros do firmware, não medido com a esteira em movimento).

## D-36: O site le da API canonica; os mocks do draft sao retirados

- Contexto: o draft do site (`site/`) trazia dados inventados em `js/data.js` (`mockCapturas`,
  `mockStats`, `mockHealth`) e nenhuma chamada de rede. O registro ja grava, o painel ja responde e
  o relatorio ja apresenta; faltava o elo que o navegador consome.
- Opções:
  - A: manter os mocks como fallback e preencher com a API quando ela responder.
  - B: servir uma API sobre o `src-production/` e o site consumir dela, sem mock nenhum.
  - C: montar um servidor de dashboard separado (segunda pipeline) so para a tela.
- Direção adotada: B, em `src-production/api.py` (biblioteca padrão, sem framework novo), servindo
  `/api/*` e os arquivos do site **na mesma origem** — sem CORS, sem CDN, sem build.
- Regra:
  - GET usa conexão read-only (`mode=ro`); POST passa pela API do `Registro` (caminho único);
  - ausência declarada: consulta sem base devolve `null` + motivo, nunca 0;
  - `status_item` e `status_vista` são campos distintos com nomes distintos — a linha `corpo/ok` de
    um item `defeito` não pode ser lida como defeito (achado da primeira rodada de revisão);
  - os chips da tela de capturas contam **linhas de vista** e passam a dizer isso ("Linhas OK"),
    porque "OK 15" se lia como 15 garrafas aprovadas;
  - evidência ausente vira placeholder **local** (SVG declarando a ausência), nunca imagem externa
    de placeholder e nunca imagem quebrada silenciosa.
  - a rota de evidência só lê **imagem dentro da raiz declarada** (`--evidencias`, padrão: a pasta do
    banco). O caminho vem do banco, e o banco é dado: sem a fronteira, uma linha apontando para
    `/etc/passwd` fazia a API servir o arquivo (sonda da revisão: HTTP 200 com 2435 bytes).
- Alternativa não adotada A, por ser exatamente o defeito: número inventado sobrevive à queda da API
  e é acreditado. Com B, API fora = tela vazia + aviso com o motivo.
- Alternativa não adotada C: uma segunda pipeline de tela repetiria a divergência que a D-30 fecha.
- Nota operacional: a porta 8080 do host já é do dashboard anterior (`ctgit-dashboard-site-1`). A API
  do hub sobe na **8090** para não colidir; unificar as duas telas é decisão em aberto.

## D-37: O modelo da cadeia e o artefato medido (pet-infer-3), portado com fidelidade verificada

- Decisao: a autoridade do modelo de visao da cadeia e o artefato congelado
  `dataset/modelo-inferencia.npz` (+ `.json`), reproduzido por
  `src-production/classificador_artefato.py`. `SemModelo` continua existindo como fallback
  **declarado**: `criar_classificador` devolve sempre um motivo, e `main` imprime qual dos dois rodou.
- Receita portada (identica no produtor `dataset/TRABALHO/compara_extratores.py` e no consumidor
  `dataset/TRABALHO/servico_inferencia3.py`): BGR->RGB -> Resize(size) -> ToTensor ->
  Normalize(ImageNet) -> extrator congelado (declarado em `config_extrator`) -> `z = (e - mu0) @ P`
  -> `z = (z - mu_fonte) / sd_fonte` -> softmax da logreg -> classe do argmax; confianca abaixo do
  limiar => `inconclusivo` (D-26).
- Regras que o port nao afrouxa: vintage, extrator, limiar, avaliacao e aviso vem **do json** (nunca
  de constante no codigo); npz sem as chaves da receita ou json sem vintage/extrator/limiar e erro;
  fonte sem estatistica no artefato e erro (o proprio json avisa: "camera nova = recalibrar"); classe
  fora do vocabulario do dominio e erro (D-28); dominio CORPO devolve `None` declarado e **nao embute
  nada**.
- O que o artefato declara sobre si mesmo viaja junto: a `Medida` carrega uma evidencia
  `limitacao_declarada_pelo_artefato` **sem fonte** (provisoria, D-24) com o aviso literal —
  "PROTOTIPO, NAO VALIDADO: avaliacao = 43 de desenvolvimento, nao teste; sem verificacao de presenca;
  escopo = recorte de gargalo". A cadeia nao registra mais do que o artefato assina.
- Verificacao (fail-closed de verdade, nao "parece certo"):
  - `src-production/canario_modelo_artefato.py` monta o **mesmo** conjunto que o json declara, reusando
    o `carrega()` do produtor, e recomputa as metricas: dominio `nosso`, split val+test, n=43 ->
    recall macro 0,8519 (declarado 0,8518518), inconclusivo 0,0698 (declarado 0,0697674), e n/recall/fn/fp
    identicos por classe. Zero divergencias.
  - `--cadeia` roda um item por `executar` e le o rastro de volta do SQLite: 3 evidencias de origem
    `classificador`, incluindo o sha256 do artefato e o aviso de prototipo.
  - Mutacao: tirar a padronizacao por fonte derruba 2 testes; tirar a projecao PCA derruba 2; usar
    limiar fixo no codigo em vez do metadado derruba 2. A primeira versao do teste de fidelidade era
    **teatro** (fixture com PCA e padronizacao identidade: a mutacao passava) — o fixture passou a ser
    nao degenerado e o proprio teste confere que as transformacoes mudam o vetor.
- Alternativas nao adotadas: (B) treinar na hora com `ClassificadorDeTampa.treinar_no_conjunto` — o que
  entraria na cadeia nao e o que foi medido; (C) bridge para o servico de bancada `:8099` — exigiria
  endpoint novo que aceite imagem e acoplaria a cadeia ao servico da bancada.
- Limite conhecido: uma vista so nao aprova item (`vistas_insuficientes_*` na conformidade), mesmo com
  o modelo decidindo; e o artefato e prototipo declarado, entao a decisao dele entra como evidencia
  com essa ressalva, nao como validacao.

## D-38: O site roda no Pi 5 (porta 8091) e a auditoria proposicao-por-proposicao

- Deploy: `pnaat-hub-site.service` no host do Pi 5 (Debian 13 ARM64), porta **8091**, `User=nerton`,
  `Restart=on-failure`, habilitado no boot. Codigo: os 19 `.py` do `src-production` (sem os
  subdiretorios) numa pasta `codigo/` do deploy, o site em `site/` e o registro `hub.db` com
  `evidencias/`, todos sob a MESMA raiz de deploy. Link (rede interna): `http://(host interno):8091/`.
- Por que a raiz de deploy e a mesma do host de origem: `evidencia.fonte` guarda **caminho absoluto** no
  banco. Instalar em outro prefixo deixaria a raiz de evidencias sem os arquivos (403 na rota de
  evidencia) sem reescrever dado do registro — e reescrever dado do registro para caber no deploy e o
  caminho errado.
- A porta 8090 do mesmo host e do servico da camera (`pnaat-vision`) e a 8080 e do docker: **nao usar**.
- O registro no host do site e um **snapshot** (copia de 2026-09-15; sha256 `a626de378a0c...`); a API do
  host de origem continua sendo a que escreve. O site nao inventa dado: le o snapshot.
- Auditoria de ponta a ponta do site (12 achados, todos corrigidos e reverificados no navegador):
  1. `Lote #L2024-89` e `14 Out 2024` fixos no template (vista Lote e cartao da Operacao) — **lote que
     nao existe no registro**. Passa a usar lote/datas reais; o header do `index.html` idem.
  2. Os totais GLOBAIS apareciam sob o cabecalho de um lote unico — agora sao os numeros DAQUELE lote,
     com tabela de todos e soma de conferencia contra o resumo.
  3. Chips contavam `status_item` (repetido por linha) sob rotulo "Linhas": "Linhas OK 15" com 17
     linhas de vista ok. Agora contam `status_vista` (17/4/6 = 27) e a contagem de ITENS (3/2/1)
     aparece declarada.
  4. Feed rotulado "Ultimas capturas" fazia `.slice().reverse()`: mostrava as **mais antigas** primeiro,
     todas as 27. Agora sao as 5 mais recentes, na ordem da API.
  5. "ESTADO GERAL Offline" vinha do adaptador do modelo (`camera.porta_aberta`): com o modelo fora do
     ar a tela dizia tudo "ok" e o sistema "Offline". Agora o estado geral vem do heartbeat; o
     adaptador e um servico da lista, com URL e motivo.
  6. Vista Qualidade era placeholder ("Integracao pendente") e o payload de `/api/qualidade` era
     **buscado e descartado** (nao existia global). Agora renderiza os indicadores reais, com "nao
     instrumentada" + motivo onde nao ha dado.
  7. Botoes **mortos**: "Exportar CSV" e "Abrir Grafana" sem handler nenhum. O CSV exporta de verdade
     (3544 bytes, conferido por interceptacao do Blob); o Grafana vira nota declarada (nao se inventa
     endereco).
  8. Badge do cartao mostrava so o estado do ITEM: agora diz "item" e mostra "vista inconclusivo"
     quando divergem.
  9. Sino do painel: `renderNotifications()` so rodava no construtor (lista vazia) e ao marcar como
     lido — com 10 notificacoes reais a tela dizia "Nenhuma notificacao". Remonta na carga e a cada
     navegacao. E a notificacao escrevia "(item <lote>)": rotulo trocado no proprio texto.
  10. Investigacao pedia `/api/item/null` quando aberta sem param (o detalhe vinha de outro item) e o
      callback assincrono re-renderizava a Investigacao **por cima da vista atual** (Saude/Qualidade/
      Lote apareciam como Investigacao). Regra unica `cartaoDaInvestigacao` + guarda de vista.
  11. Selo "Sistema operacional" era verde fixo e a temperatura dizia "faixa de operacao normal" sem
      faixa declarada — ambos passam a depender do que o registro declara.
  12. Selo do header com lote fixo -> `#lote-atual` preenchido com o lote da captura mais recente.
- Verificacao: seis vistas conferidas uma a uma (cada uma mostra o proprio conteudo), troca rapida de
  vista respeitando a vista atual, CSV conferido, zero erro de console, e sha256 do JS servido por HTTP
  identico ao do repo nas tres copias (repo -> deploy -> HTTP).
- Limites conhecidos e declarados: o adaptador do modelo aponta para `127.0.0.1:8099` **do host do
  deploy** — no host do site aparece "sem resposta" com o motivo (o modelo roda no host de origem, que
  e quem tem a camera); e o `index.html` carrega Tailwind e Lucide de **CDN externo**, o que contradiz a
  afirmacao do docstring do `api.py` ("nao depende de CDN") — ou se corrige a afirmacao, ou se embutem
  os arquivos.

## D-39: Revisao paralela por feature do site (5 frentes) e o que cada achado virou

- Metodo: snapshot congelado (site + modulos do runtime + respostas reais da API) revisado em 5 frentes
  independentes (Operacao+Capturas, Investigacao+Lote, Saude+Qualidade, backend, infra do frontend),
  com escopo fechado e obrigacao de citar arquivo:linha. Todo achado foi reverificado por sonda propria
  antes de virar correcao — parecer de revisor nao e prova.
- Corrigido e reverificado (o que importa):
  1. Laco da Investigacao: uma abertura da vista disparava 1968 navegacoes e 1967 pedidos de detalhe (o
     cache chamava o callback, o callback re-renderizava, o render pedia o item de novo — tudo sincrono).
     Medido antes e depois: 1968 para 2. O callback so dispara depois de ir a rede, 404 e veredito que
     nao se repete e resposta velha nao desenha por cima.
  2. Filtro de vista: o select carregava o rotulo "Lateral" e o cartao o rotulo da vista ("Lateral 1"),
     com o estado guardando o valor do select — filtrar escondia os 27 cartoes. Agora o atributo leva o
     valor cru (lateral1), o rotulo fica no texto; medido: lateral1 -> 11 cartoes.
  3. Contrato da API no erro do cliente: limite=abc respondia 500 falha_interna; agora 400
     filtro_invalido, com teto de 500 declarado no payload de filtros.
  4. Fronteira HTTP: Content-Length -1 prendia a thread (sem resposta ate o cliente desistir) e chunked
     desincronizava o keep-alive; agora 400/411 declarados. Verbo fora do contrato virava 501 com a
     pagina HTML do http.server; agora 405 JSON (HEAD/OPTIONS inclusos).
  5. POST do gatilho: aceitava timestamp "ontem" (200) e gravava texto onde o dominio exige instante com
     fuso; agora 400, e tipo errado em ponto_id/debounce_ms tambem deixa de virar 503 de banco.
  6. Ausencia lida como aprovacao: taxa de discordancia sem base saia 0.0 (agora None), e a taxa do lote
     sem itens idem.
  7. Texto fixo que mentia na tela: "450 itens" mais barra de 72 por cento (lote sem meta no registro),
     miniatura de placehold.co (rede externa) e caixa "RISCO" pintada com coordenadas fixas (geometria
     que nao existe no registro) — os tres removidos ou trocados por dado/ausencia declarada.
  8. Estados de servico: a API declara 7 literais e o adaptador conhecia 2, entao o proprio Site e a
     raiz de evidencias entravam como alerta (2 notificacoes falsas por carga).
  9. API fora: as globais ficavam vazias e a tela imprimia undefined/NaN e chegava a afirmar leitura;
     agora tem forma declarada (ausencia) e a conta so roda com numero.
  10. CSV: exportava as linhas carregadas com rotulo de tela, dizendo no comentario que exportava o
     filtro; agora exporta as linhas VISIVEIS, com valor cru do registro, ausencia vazia, BOM e
     neutralizacao de formula.
  11. Topbar: "sem leitura" virava "no offline" e as faixas de 75/65 C e 250/100 ms eram inventadas (a
     propria vista Saude diz que nao ha faixa declarada); agora o estado sai do que o registro declara.
     O "Latencia 12ms" fixo no HTML tambem saiu.
  12. Recarga de 15 s: remontava a area e apagava o texto digitado na busca (medido: o texto digitado
     sobrevive a recarga agora); imagens com loading lazy e decoding async.
- Pendente, com a razao (nao e esquecimento):
  - Decisao humana da D-30 na tela: os botoes "Forcar aprovacao"/"Confirmar defeito" nao tem handler e
    nao existe rota de escrita de correcao no backend. Falta a rota unica (via Registro) — tranche
    propria, com teste de mutacao.
  - Escrita do gatilho sob concorrencia: sem WAL nem fila, um escritor segurando o lock faz o POST
    perder o evento depois do timeout. Tranche propria (journal_mode + retry + Retry-After).
  - Desempenho: correlacao_ambiental faz 1 consulta por item (N+1) e o detalhe do item lia a tabela de
    correcoes inteira (o indice foi criado; a query filtrada ainda nao). O listado do site varre o join
    com b-tree temporario por request.
  - Fronteira de evidencia por dominio: a URL identifica (item, vista) e a evidencia e (item, vista,
    dominio) — hoje o registro tem o mesmo caminho nos dois dominios, entao e latente, nao ativo.
  - Escape de HTML nos templates: nenhuma interpolacao escapa dado do banco. Hoje nao e exploravel (os
    campos exibidos vem de vocabulario fechado ou de coluna que nao recebe texto livre), mas e divida
    real: quem escrever texto livre num campo exibido ganha injecao.
  - Acessibilidade: cartao so por mouse (sem tabindex/teclado), filtros sem rotulo, selo de API
    indisponivel sem aria-live, sem noscript.
  - Carga do site: 5 GETs e cerca de 17 KB a cada 15 s com no-store (sem 304), inclusive nas vistas que
    nao usam capturas.

## D-40: A serie do rig vira item do registro (mapa camera->vista declarado + ingestao unica)

- Decisao: o conjunto de captura do rig (`serie` = 3 fotos + manifesto) passa a ser ingerido como ITEM
  do registro, pela ferramenta `src-production/ingerir_serie.py`, que usa a cadeia que ja existe
  (`orquestracao.executar`). Nao ha segundo caminho de decisao.
- O que faltava e agora existe:
  1. **mapa camera -> vista DECLARADO** (`src-production/mapeamento_rig.py`): o rig nomeia cameras
     (os papeis `csi`, `usb`, `espcam`) e o registro fala por vista (`topo`, `lateral1`,
     `lateral2`), e nada ligava os dois. O mapa e declaracao da instalacao (constante `MAPA_PADRAO` ou
     `--mapa camera=vista,...`), com validacao: vista repetida e erro, camera fora do mapa e erro, e a
     ORDEM do manifesto nao define vista (a associacao vem do mapa).
  2. **item com evidencia rastreavel**: as fotos sao COPIADAS para a raiz de evidencia do hub
     (`<raiz>/series/<carimbo>/<camera>.jpg`) com `sha256` de cada uma, e o registro guarda
     `caminho_evidencia` + `sha256_evidencia` por vista. A prova passa a viajar com o registro (a serie
     do rig pode ser apagada sem perder evidencia) e a rota de evidencia continua servindo so o que
     esta dentro da raiz declarada.
  3. **identidade gerada no caminho**: o `item_id` sai de `SequenciaDeItens.reservar(lote)` DENTRO da
     transacao que grava o item (nunca digitado), e o evento de gatilho e vinculado ao item quando o id
     do evento e informado.
- Fail-closed mantido: serie sem vista / camera fora do mapa / serie sem manifesto sao recusadas com
  motivo; sem janela declarada NADA e utilizavel e o item sai inconclusivo; alinhamento SO e declarado
  como OK quando o operador informa `--alinhamento declarado` (o padrao e `nao_verificado`).
- Onde roda: onde o modelo vive. O classificador da cadeia e o artefato medido (D-37), que exige torch;
  o runtime do hub e stdlib. Entao a ingestao roda na estacao que tem o artefato, e o hub le o resultado.
- Canario (serie montada com recortes reais + artefato medido): item `CANARIO-000001`, `status_final`
  `defeito` (tampa 0,993 na lateral1 e 1,000 na lateral2), `status_corpo` inconclusivo (nao existe
  modelo do corpo — declarado), `qualidade_registro` completo, evidencias com `probabilidade`,
  `limiar` e a **limitacao que o artefato declara sobre si** ("PROTOTIPO, NAO VALIDADO..."), arquivos
  copiados com hash conferido contra o original.
- Testes: `src-production/tests/test_ingestao.py` (12) — serie completa, ordem do manifesto invertida,
  serie parcial declarando a vista faltante, sem janela (nada utilizavel), alinhamento nao verificado,
  camera fora do mapa, vista repetida, vista desconhecida, duas cameras para a mesma vista, serie sem
  manifesto, vinculo do gatilho e sequencia do lote (dois itens ingeridos nao repetem id).
- Pendente e declarado: a leitura da serie direto do rig (URL) ainda nao existe — a ferramenta le um
  diretorio local; e a ingestao nao decide o CORPO (nao ha modelo do corpo) nem mede a janela (o
  `t_ms`/`dur_ms` do firmware continuam sendo descartados pela ponte).
