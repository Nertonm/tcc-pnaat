# Entrega 2: apresentação da PoC

Apoio ao vídeo da Entrega 2 (PNAAT, TCC Ciclo 1). Cada bloco declara entrada, funcionamento,
resultado e função na arquitetura. Onde aparece `<PREENCHER>`, entra o valor que está no vídeo.

## 1. Antes de apresentar: divergência no firmware

O arquivo `code-workspace/src/pocs/poc01_trigger/esp/main.py` usa a constante
`PRESENCE_PIN = 33`, e o docstring do mesmo arquivo escreve "sinal em P27 (PULL_UP)". Os dois não
podem estar certos ao mesmo tempo. No vídeo, cite apenas o que aparece na tela; se precisar falar do
pino, use `<PREENCHER pino que aparece no video>`. Corrija o arquivo depois.

## 2. Artefato entregue

- Link de vídeo não listado no YouTube: `<PREENCHER link>`
- Duração: `<PREENCHER>`
- O vídeo mostra a tecnologia central em execução, com os rótulos "PoC-01: gatilho de presença" e
  "PoC-02/03: tampa e corpo" visíveis

| Campo pedido | Onde está no vídeo | Evidência |
|---|---|---|
| Entrada ou início da execução | Bloco 1, a garrafa chegando na esteira | cena da esteira e o sensor no suporte |
| Funcionamento da tecnologia principal | Bloco 1, a janela de eventos do canal | eventos ARMED, OPEN, CLOSE e SUPPRESSED |
| Resultado produzido | Bloco 1, pulso de saída e resumo | CAPTURE_OUT pulsando 50 ms por passagem |
| Entrada, no caso da visão | Bloco 2, a captura | foto da câmera do Pi |
| Processamento, no caso da visão | Bloco 2, comparação com a referência | imagem anotada com a região detectada |
| Resultado, no caso da visão | Bloco 2, veredito | classe e motivo na tela |

## 3. Problema que o conceito central endereça

A linha precisa de duas coisas que hoje não estão garantidas de forma automática: saber quando existe
um item novo na posição de inspeção e decidir sobre o estado da garrafa (tampa ausente, tampa mal
rosqueada ou corpo deformado). O conceito central demonstrado aqui é esse par. De um lado, um gatilho
que transforma a passagem física em um evento que os outros sistemas consomem. Do outro, uma inspeção
local que transforma uma captura em uma decisão sobre o item. O vídeo comprova a viabilidade técnica
desse par, não o produto final.

Para citar na apresentação, se for o caso: `<PREENCHER como a inspeção é feita hoje>`.

## 4. Descrição do vídeo (YouTube, não listado)

Demonstração da viabilidade técnica das duas frentes da PoC. No primeiro bloco, o gatilho de presença
detecta a passagem da garrafa pela esteira e produz um sinal de mudança de estado (armado, desligado,
armado), que é o evento do qual os demais sistemas da esteira dependem. No segundo bloco, a inspeção
por captura estática, executada localmente na Raspberry Pi, classifica a garrafa como normal, tampa
ausente, tampa mal rosqueada ou corpo deformado, sem nuvem e sem treino prévio. O vídeo mostra, em
sequência única, a entrada, o processamento e o resultado de cada frente, e aponta a próxima etapa:
unificar o gatilho com a captura para inspecionar item a item de forma automática.

## 5. Bloco 1: PoC-01, gatilho de presença (tempo: `<PREENCHER>`)

Entrada: a garrafa trafega pela esteira e passa pelo sensor de presença infravermelho E18-D80NK
montado no suporte, ligado a um pino digital da placa ESP32 com PULL_UP (0 = objeto à frente, 1 =
repouso).

Elementos de IoT mostrados:
- Sensor: E18-D80NK, saída digital, ativa em nível baixo, com debounce de 20 ms no firmware.
- Placa: ESP32 v4 rodando firmware em MicroPython.
- Processamento: máquina de estados no firmware, com aquecimento de 1 s, arme seguro e guarda
  anti-duplicação; no host, um supervisor mantém o histórico.
- Conectividade: o firmware publica os eventos na porta serial a 115200 baud, o host lê esse canal
  (dono único da porta) e republica em arquivo de stream, que é por onde o sinal chega aos demais
  sistemas.

Funcionamento: depois do aquecimento, o sistema só ARMA quando a linha fica estável em repouso por 10
leituras seguidas, perto de 500 ms; isso elimina a janela espúria do boot. Com o sistema armado, a
passagem da garrafa abre a janela: 5 leituras estáveis em nível de objeto geram o evento OPEN e o
pulso na saída de captura. Na saída da garrafa, 5 leituras estáveis em repouso fecham a janela
(CLOSE) e o firmware calcula o tempo de permanência. Depois de cada CLOSE existe uma janela morta de
500 ms. Uma detecção dentro dela é registrada como SUPPRESSED, o que mostra que a duplicata foi
bloqueada e não abriu uma segunda leitura.

Resultado: a transição armado, desligado, armado no instante da passagem, com duas evidências ao mesmo
tempo. A primeira é o pulso de saída: CAPTURE_OUT em nível alto por 50 ms a cada passagem, que é o
sinal físico que outros sistemas consomem. A segunda é a sequência de eventos no log da janela de
canal, com uma passagem por garrafa. O bloco entrega o evento "há um item novo na posição de
inspeção".

Função na arquitetura: é o elemento que dá o tempo do sistema. Sem o gatilho, a inspeção não sabe
quando olhar.

Evidência no vídeo: a janela de eventos do canal (nível, histórico, bordas por segundo, percentual em
detecção, janelas, descartes e estado armado) e o resumo: passagens = `<PREENCHER>`, descartadas =
`<PREENCHER>`, tempo de permanência = `<PREENCHER>`.

## 6. Bloco 2: PoC-02/03, tampa e corpo por captura estática (tempo: `<PREENCHER>`)

Entrada: uma captura da garrafa pelo gancho de capturas estáticas servido pela própria Raspberry Pi.
Na demonstração, o operador dispara essa captura; o disparo automático pelo gatilho é a próxima etapa.

Funcionamento: o processamento roda localmente no Pi, sem nuvem. A garrafa boa é capturada como
referência (silhueta, topo e brilho) e cada captura seguinte é comparada com ela em três frentes:
forma do corpo, altura e alinhamento do topo (tampa) e desvio na parte inferior (corpo). Não há
treino de modelo: a decisão é comparativa, contra o padrão da própria cena.

Resultado: uma classe por captura: normal, tampa ausente, tampa mal rosqueada, deformidade do corpo,
além de inconclusivo quando a imagem está fora de foco e de sem_garrafa quando não há objeto no
quadro. No vídeo: normal com coincidência de silhueta de `<PREENCHER>`%, seguida de uma captura com
defeito e o motivo na tela (topo mais baixo que a referência, topo fora do eixo, corpo diferente da
referência).

Função na arquitetura: é o bloco que decide sobre o item: recebe o instante do gatilho e devolve o
estado da garrafa para a linha.

Evidência no vídeo: a imagem anotada com a região detectada, o veredito em destaque e a lista de
motivos. Como corroboração, um corte curto do autoteste do próprio sistema, com 8 de 8 casos conforme
o esperado: normal, sem tampa, tampa torta, corpo deformado, mais 25% de exposição, imagem desfocada,
sem garrafa e cena trocada.

## 7. Integração, a parte central desta etapa

As duas frentes aparecem em sequência única no mesmo vídeo: o gatilho produz o evento de passagem e a
inspeção produz a decisão sobre o item. A ligação entre eles, com o pulso de captura disparando a
captura, é a parte central desta etapa e está declarada no vídeo, na narração e no fechamento.

## 8. Próxima etapa técnica

1. Ligar o pulso de captura (CAPTURE_OUT) ao gancho de captura, para a passagem disparar a análise sem
   clique. O pulso de 50 ms já existe para isso.
2. Devolver o resultado para a linha, como sinal de aceite ou rejeite que a esteira consome.
3. Calibrar os limiares para a cena de produção. O limite de inclinação da tampa está marcado como
   provisório no código.
4. Medir repetibilidade com uma série de itens conhecidos passando na esteira.

## 9. Mapa campo a campo da rubrica

| Campo da rubrica | Como é atendido | Onde ver |
|---|---|---|
| Demonstração prática inicial, link não listado | vídeo único com os dois blocos | Artefato entregue |
| Entrada utilizada ou início da execução | garrafa chegando na esteira, captura da garrafa | Blocos 1 e 2 |
| Funcionamento da tecnologia principal | máquina de estados com arme seguro e guarda, comparação com a referência | Blocos 1 e 2 |
| Resultado produzido | pulso de 50 ms com a transição armado, desligado, armado, e a classe da tampa e do corpo | Blocos 1 e 2 |
| IoT: sensores, placas, processamento ou conectividade | E18-D80NK, ESP32 com MicroPython, firmware e serial 115200 | Bloco 1 |
| Visão computacional: entrada, processamento e resultado | captura, comparação local, veredito com motivo | Bloco 2 |
| Integração: mostrar a parte central desta etapa | as duas frentes no mesmo vídeo e a ligação declarada | Integração |
| Adequado: verificar integralmente a tecnologia central | cada bloco com entrada, execução e resultado identificáveis | Blocos 1 e 2 |
| Adequado: produzir evidência do conceito ligado ao problema | problema enunciado e cada bloco mostrando o conceito que o resolve | Problema e Blocos 1 e 2 |
| Avançado: entrada, execução e resultado em sequência acompanhável | ordem sensor, evento, captura, decisão, sem corte do fluxo | Blocos 1 e 2, Integração |
| Avançado: tecnologia central com outro elemento da arquitetura | gatilho de presença operando junto do módulo de visão | Blocos 1 e 2, Integração |
| Avançado: explicar entrada, funcionamento, resultado e função | os quatro itens descritos por bloco, na narração e no texto | Blocos 1 e 2 |
| Avançado: identificar a próxima etapa ou a parte não integrada | fechamento no vídeo e bloco de próxima etapa | Próxima etapa técnica |

## 10. Riscos que rebaixariam o nível

Dois critérios de Nível Básico pedem atenção na edição. O primeiro é erro que interrompe a operação
antes do resultado: grave cada bloco até o resultado aparecer e, se algo falhar durante a gravação,
corte o trecho e regrave, porque o vídeo final não deve mostrar tentativa interrompida. O segundo é
intervenção manual que impede acompanhar parte do fluxo: no Bloco 2, apresente a captura como a
entrada declarada do bloco e diga que o disparo automático é a próxima etapa, para o clique não ler
como falha de fluxo.

Na gravação, capture a garrafa parada, espere o resultado estabilizar e só então comente. Mostre uma
captura normal e uma com defeito, as duas com o motivo visível na tela. Se algum `<PREENCHER>` não
tiver valor no vídeo, remova a linha inteira em vez de estimar.

## 11. Perguntas prováveis na apresentação

- "Isso já está pronto?" Não. Esta entrega prova a viabilidade técnica dos dois mecanismos centrais. A
  integração automática é a próxima etapa, declarada no vídeo.
- "Qual a taxa de acerto da classificação?" O sistema é comparativo e devolve inconclusivo quando a imagem não
  permite decidir. A taxa em produção depende da calibração dos limiares para a cena fixa.
- "Roda onde?" O gatilho no ESP32 da esteira; a inspeção localmente na Raspberry Pi, sem nuvem.
- "Precisa treinar modelo?" Nesta demonstração, não: a referência é capturada na própria cena e cada
  medida sai da comparação com ela.
- "Se a garrafa parar na frente do sensor?" A guarda de 500 ms depois de cada fechamento registra
  SUPPRESSED e não abre uma segunda leitura do mesmo item na esteira.
- "Qual a próxima etapa?" Integrar o pulso de captura ao gancho de captura e medir a repetibilidade
  com uma série de itens conhecidos passando na esteira.

## 12. Checklist antes de publicar

- [ ] Vídeo publicado como não listado no YouTube, com o link aberto para quem avalia a entrega
- [ ] Áudio audível nos dois blocos, com os rótulos "PoC-01" e "PoC-02/03" visíveis na tela
- [ ] Cada `<PREENCHER>` preenchido com o valor que aparece no vídeo, ou a linha removida
- [ ] Nenhum número de pino citado antes de resolver a divergência descrita no item 1
- [ ] Bloco 2 trazendo uma captura normal e uma com defeito, as duas com o motivo na tela
- [ ] Fechamento dizendo em voz alta qual é a próxima etapa técnica do projeto
- [ ] Nenhum trecho do vídeo mostrando erro que interrompe a operação antes do resultado
