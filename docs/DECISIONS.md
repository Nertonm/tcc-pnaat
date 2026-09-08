# Decisões de projeto (em aberto)

Registro de posições de decisão. Nenhuma posição está fechada: cada item apresenta a direção forte, as alternativas consideradas e o que é necessário para confirmar (ensaio de PoC, medição no hardware ou revisão). As posições são revisadas a cada prova de conceito.

## D-01: Bancada de teste

- Opções:
  - A: trilho deslizante artesanal com carrinho em velocidade controlada, encoder e trigger no ponto de captura.
  - B: esteira motorizada comercial.
- Direção forte: A, documentada como bancada em escala reduzida.
- A decidir: estabilidade mecânica, controle de velocidade e repetibilidade do disparo, validados na PoC 3.
- Alternativas descartadas por enquanto: integração com linha industrial real.

## D-02: Composição do dataset

- Opções:
  - A: dataset próprio (fotos de tampa e peças 3D com deformação controlada) como fonte primária.
  - B: apenas datasets públicos.
  - C: dataset público como fonte primária.
- Direção forte: A, com públicos genéricos como validação metodológica.
- A decidir: volume, balanceamento e cobertura das classes, confirmados na PoC 1 e 2.
- Alternativa descartada: B, por não cobrir as três classes com controle de defeito.

## D-03: Câmeras

- Opções:
  - A: duas CSI nativas e uma USB UVC, dentro do orçamento indicado.
  - B: câmera única com espelho.
  - C: módulo multicâmera comercial.
- Direção forte: A.
- A decidir: largura de banda, captura simultânea e compatibilidade com o trigger, confirmadas na PoC 3.
- Alternativa descartada: C, por captura sequencial.

## D-04: Fusão multi-view

- Opções:
  - A: um classificador por vista com votação.
  - B: concatenação de imagens como canais.
  - C: fusão por atenção entre vistas.
- Direção forte: A, preservando vista ausente, discordância e confiança.
- A decidir: regra de votação e tratamento de discordância, validados na PoC 1 e 2.

## D-05: Topologia da demonstração

- Opções:
  - A: dois sensores, um nó de visão e um hub.
  - B: um único nó concentrador.
  - C: nós distribuídos completos.
- Direção forte: A, extensível.
- A decidir: número de nós e carga da demo, confirmados na PoC 4 e 5.

## D-06: Destino do item defeituoso

- Opções:
  - A: atuador no fim do trilho, separando para análise manual, com confirmação por sensor.
  - B: apenas sinalização, sem separação física.
  - C: descarte automático.
- Direção forte: A, fechando o ciclo detectar, separar, analisar, corrigir e registrar.
- A decidir: mecanismo, confirmação, timeout e parada manual, validados na PoC 7.
- Alternativa descartada: C, por risco e ausência de análise humana.

## D-07: Medida dimensional da tampa

- Opções:
  - A: medição em milímetros com backlight e limite dimensional, com o modelo como segunda camada.
  - B: apenas classificador.
- Direção forte: A, por decisão explicável.
- A decidir: precisão de 0,5 mm e calibração, confirmadas na PoC 2 e na medição de aceite.

## D-08: Kit de golden samples

- Opções:
  - A: kit com defeitos conhecidos para injeção sob demanda, isolado das estatísticas.
  - B: sem kit, usando itens do lote.
- Direção forte: A.
- A decidir: quantidade de peças, rótulos e protocolo de uso na demonstração.

## D-09: Relatório de lote

- Opções:
  - A: relatório em PDF com indicadores, severidade, evidências e tendência, enviado por notificação.
  - B: apenas dashboard.
- Direção forte: A.
- A decidir: formato, conteúdo e canal, confirmados na integração do hub.

## D-10: Camada de generalização

- Opções:
  - A: descritores geométricos clássicos com score de anomalia calibrado sobre o conjunto normal.
  - B: backbones pesados de visão para detecção zero-shot.
  - C: sem camada de generalização.
- Direção forte: A, demonstrada apenas com objetos de teste na camada geométrica.
- A decidir: custo abaixo de 10 ms por vista e threshold, confirmados em PoC isolada.
- Alternativas descartadas: B, por inviabilidade na borda.

## D-11: Detecção de anomalia

- Opções:
  - A: autossupervisão com anomalias sintéticas por recorte e colagem, treinada somente com itens normais.
  - B: autoencoder puro.
  - C: dataset anotado de defeitos reais como requisito de treino.
- Direção forte: A, no formato original de classificação binária real/sintético.
- A decidir: área sob a curva e latência, confirmadas em PoC isolada.
- Alternativa descartada: B, por reconstruir a anomalia.

## D-12: Execução da anomalia na borda

- Opções:
  - A: destilação professor-aluno, com o professor apenas no treino e o aluno quantizado no hardware alvo.
  - B: executar o professor na borda.
- Direção forte: A.
- A decidir: latência real do aluno no hardware alvo; fallback documentado caso estoure o orçamento.

## D-13: Auto-supervisão a partir do sistema

- Opções:
  - A: usar o sinal produzido pelo próprio sistema (defeito sintético, discrepância professor-aluno, supervisão fraca, física do rig).
  - B: depender de anotação manual para expandir o dataset.
- Direção forte: A, com validação física de timestamp no núcleo e clustering de drift condicionado.
- A decidir: quais camadas entram no núcleo e quais ficam como extensão, revisado a cada PoC.

## D-14: Rigor de processo

- Opções:
  - A: testes de resiliência como experimentos com hipótese falsável, métrica prévia e revisão de logs.
  - B: testes ad-hoc.
- Direção forte: A, com commits estruturados.
- A decidir: protocolo e cobertura, confirmados na PoC 6.

## D-15: Estabilidade mecânica

- Opções:
  - A: conexões críticas soldadas, painel rígido, suportes parafusados e jig de posicionamento.
  - B: montagem por jumpers e suportes de fricção.
- Direção forte: A, como pré-requisito físico das métricas.
- A decidir: tolerâncias e sequência de montagem, confirmadas na PoC 3.

## D-16: Princípio de testabilidade

- Opções:
  - A: design for testability como critério transversal, com controlabilidade e observabilidade explícitas.
  - B: sem princípio unificador.
- Direção forte: A, refletida na ordem física, dados, modelo, teste e documentação.
- A decidir: aplicação em cada requisito, revisada na entrega de requisitos.

## D-17: Grip de câmeras

- Opções:
  - A: módulo ajustável em trilhos com trava, que se encaixa em qualquer esteira.
  - B: painel fixo de bancada.
- Direção forte: A, se a estabilidade mecânica for validada após montar, calibrar, mover e medir.
- A decidir: mecanismo de fixação e tolerância de calibração, validados no laboratório.
- Detalhes em `docs/design/grip-extensivel.md`.

## D-18: Sistema de iluminação estroboscópica RGB com lente difusora 3D

- Opções:
  - A: Iluminação contínua comercial sem difusor.
  - B: 2x LEDs RGB de 5 mm de alto brilho operados em potência máxima (luz branca) acionados estroboscopicamente via trigger do ESP32, com lente difusora frontal em PLA 3D translúcido, acrílico ou papel vegetal.
- Direção forte: Opção B.
- Justificativa: Evita o superaquecimento dos LEDs, economiza a carga das baterias 18650, atua como estroboscópio para congelar o movimento no trilho e elimina hotspots saturados em garrafas PET/Vidro.
- A decidir: Largura precisa do pulso PWM e espessura da parede em PLA 3D da lente difusora, validadas na PoC 3.

## D-19: Divisão de tarefas de tempo real entre ESP32 e Raspberry Pi 5

- Opções:
  - A: Conectar todos os sensores diretamente nas GPIOs do Raspberry Pi 5.
  - B: Usar ESP32 para gerenciar interrupções, debounce do E18-D80NK/VL53L0X, leitura do encoder KY-040 e acionamento estroboscópico da iluminação, enviando timestamps e triggers processados para o Raspberry Pi 5.
- Direção forte: Opção B.
- Justificativa: Isola tarefas determinísticas de tempo real e debounce no ESP32, mantendo a capacidade computacional do Raspberry Pi 5 focada exclusivamente na inferência dos modelos de visão computacional e gerenciamento do hub.

## Regra de atualização

Uma posição só sai do estado "a decidir" quando houver evidência de PoC, medição ou revisão registrada no repositório. O registro de cada revisão entra como novo item, sem apagar o histórico da posição anterior.
