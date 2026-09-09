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
  - a vista superior decide isoladamente o domínio da tampa;
  - as duas vistas laterais fornecem as evidências do domínio do corpo;
  - não existe maioria global entre as três câmeras;
  - defeito detectado em qualquer domínio reprova o item;
  - o resultado de um domínio não pode cancelar defeito detectado pelo outro;
  - disponibilidade, qualidade, confiança e origem devem ser preservadas por vista;
  - quando nenhum defeito for detectado, mas a evidência necessária estiver ausente, inválida ou abaixo dos critérios mínimos, o domínio afetado e o item devem permanecer `inconclusivos`;
  - evidência insuficiente não pode ser convertida em aprovação silenciosa.
- A decidir: regra para combinar as duas vistas laterais, tratamento definitivo da discordância lateral e limiares mínimos de qualidade e confiança, validados nas PoCs 01 e 02.
- Alternativas não adotadas no núcleo B e C, por aumentarem o acoplamento entre vistas e dificultarem a preservação explícita da vista ausente e da decisão por domínio.

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
- A decidir: tipo de atuador, modelo e interface elétrica do sensor de confirmação, posicionamento físico, timeout, comportamento diante de falha e procedimento de parada manual, validados na PoC 07.
- Alternativa descartada C, por eliminar a análise humana e introduzir risco de descarte incorreto.

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
- Requisitos condicionais: RF-13, RF-17, RF-18, RF-19, RF-21, RF-23 e RF-30.
- Direção adotada requisitos condicionais somente entram na implementação depois da aprovação da PoC aplicável, da verificação do orçamento de desempenho e da confirmação de prazo.
- Regra:
  - requisito condicional não pode bloquear a validação do núcleo;
  - documentação ou código inicial não representa aprovação;
  - inclusão, adaptação, retirada ou adiamento deve ser registrado;
  - requisitos condicionais devem possuir fallback que preserve o funcionamento do núcleo;
  - requisito condicional sem evidência suficiente deve permanecer aberto ou ser adiado.
- A decidir: quais requisitos condicionais serão promovidos para a demonstração após as PoCs essenciais.

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
