# Grip extensível de câmeras: módulo de captura plug-and-play

> Proposta 2026-08-16 (Nerton). Direção de design atual do hardware do TCC.
> Complementa a decisão 13 (estabilidade mecânica) e o escopo (`docs/escopo.md`).

## Problema que resolve

O escopo original pina o rig a uma bancada fixa: painel de base rígido com
furos fixos para as 3 câmeras, trigger e encoder. Isso é estável, mas serve
a um único trilho/esteira. A proposta: **módulo de captura extensível** que
se encaixa em qualquer esteira: o mesmo sistema se desloca entre linhas ou
é apresentado como "grip de inspeção" instalável, não como bancada embutida.

## Conceito

- Perfil estrutural em T-slot (alumínio 2020/2040) formando um **grip/pórtico**
  que se prende à esteira por garras de travamento (braçadeiras com atrito
  ajustável), em vez de parafusar na bancada.
- Trilhos deslizantes com trava (T-slot nuts + parafuso de fixação) permitem
  ajustar **largura** (entre laterais), **altura** (travessa superior) e
  **distância ao item** (profundidade): sem trocar peças.
- 3 câmeras em suportes ajustáveis: `C_TOP` e `C_LEFT` são câmeras Raspberry
  Pi por CSI; `C_RIGHT` é uma câmera USB-C/UVC. `C_TOP` fica na travessa
  superior e as laterais ficam em lados opostos da esteira, cada uma com
  ajuste fino de ângulo (pivot com trava) antes da fixação final.
- Trigger E18-D80NK/VL53L0X + encoder KY-040 montados no mesmo grip, alinhados
  à linha de captura; strobing LED integrado à travessa.
- Cabos organizados por canaleta/esteira de cabo no perfil: nada solto ao
  longo da esteira.

## Decisão de design (DFT aplicada)

- **Estabilidade pós-ajuste**: ajuste livre durante montagem, TRAVA após
  calibração. Calibração pixel→mm documentada por posição de trava: o grip
  garante repetibilidade enquanto a configuração não for mexida.
- **Tradeoff explícito**: rigidez absoluta (painel único) vs portabilidade
  (grip ajustável). Risco: folga nas travas → deriva de calibração. Validação
  de laboratório obrigatória antes das PoCs de visão: montar → calibrar →
  mover (simular troca de esteira) → re-medir; registrar drift em mm.
- **Versão docente**: o grip extensível É a demonstração do Efeito Demonstração
  invertido: se sobrevive a desmontar/remontar sem recalibrar, prova
  estabilidade mecânica real para a banca. (Também é a resposta para
  "funciona só na bancada?")

## Relação com o escopo vigente

- Substitui/evolui o item 2 da decisão 13 ("painel de base rígido"): o painel
  vira o grip; os furos fixos viram trilhos com trava.
- Mantém os itens 1 (solda crítica), 3 (mounts parafusados) e 4 (gabinetes).
- Reflexo nos requisitos (aplicar quando o design for aprovado):
  - RF-27 passa a "construir grip extensível em T-slot com travas: largura/
    altura/distança ajustáveis" + calibração por posição documentada.
  - RNF-20 ganha "recalibração NÃO necessária após desmontar/remontar na mesma
    posição de trava".
- Conflito potencial: custo e tempo do T-slot + travas vs painel MDF cortado a
  laser (mais barato/rápido). Decisão de S1 com o laboratório disponível.

## Mecanismo de fixação à esteira: duas opções

### Interface de clamp/tripé candidata (2026-09-10)

O time considera imprimir o modelo externo “G-clamp tripod”, publicado no
Cults3D. Ele pode ser um bom **protótipo de fixação removível**, pois combina
uma garra mecânica e uma interface de tripé. Contudo, o modelo não é fonte
canônica deste repositório: não foi copiado, redistribuído nem convertido em
peça de produção porque sua licença e o arquivo de origem precisam ser
confirmados pelo time antes de qualquer inclusão.

O CAD do projeto deve usar somente um adaptador próprio, paramétrico, entre a
coluna e uma interface de tripé **1/4-20**, com quatro parafusos M4 no lado da
coluna, alívio de torque e ponto para retenção secundária. A garra não pode
ser considerada segura ou compatível com a IN 150 até que espessura, formato e
resistência do ponto real de contato sejam medidos no G0.

### Opção A: Garra com parafuso M6/M8 + manípulo (preferida)

- Abertura útil: 50-80 mm, parametrizada no CAD por `jaw_opening`.
- Carga: parafuso metálico M6/M8 com manípulo, arruela larga e sapata de
  TPU/EVA para não marcar a esteira.
- Corpo: PETG/ABS, 5-6 paredes; se possível, corpo impresso + chapa de
  alumínio cortada a laser.
- Segurança: o corpo impresso não é o único elemento contra queda do pórtico;
  prever cabo/cordão de retenção.
- Prós: força de aperto determinística, independente de mola; trava absoluta
  após ajuste.
- Contras: instalação/remoção lenta (apertar 2 parafusos), mais peças, risco de
  aperto desigual.

### Opção B: Spring-loaded, estilo grip de celular (nova proposta 2026-08-16)

Mecanismo inspirado nos grips de suporte de celular que se ajustam ao tamanho
do aparelho: duas peças deslizantes + mola de compressão que pressiona para
fora, e a PRÓPRIA TENSÃO da extensão prende na esteira. Sem parafuso de trava.

- Duas peças deslizantes em trilho (base comum), como o clamp de celular do
  PasCV (Thingiverse 4676545: "duas partes que deslizam, presas por molas com
  M4").
- Mola de compressão entre as peças empurra as pontas para fora.
- Pontas com sapata TPU/EVA (atrito + não risca), como as borrachinhas do grip
  de celular.
- Instalação: comprime as pontas uma contra a outra, encaixa na largura da
  esteira, solta. A mola expande e prende por atrito.
- Remoção: comprime e tira. Troca de esteira em segundos, sem ferramenta.
- O pórtico das câmeras monta na base do grip (furos M4).
- Hardware: 1 mola de compressão (diâmetro ~10-12 mm, k moderada), 0 parafusos
  de trava.
- Prós: instalação instantânea, autoajuste a qualquer largura, mecânica simples
  e à prova de erro (não depende de aperto humano); narrativa de demo imediata
  ("se ajusta a qualquer esteira como um suporte de celular").
- Contras: prende por atrito, não por força estrutural: mola fraca desliza,
  mola forte dificulta instalar; calibração da mola é empírica.
- Referências do mecanismo (verificar licença antes de usar):
  - Printables 1159270: Spring Phone Holder V1 (mola prende, 4 peças)
  - Thingiverse 4676545: Phone holder clamp (deslizante + molas M4)
  - Thingiverse 1083987: Spring Loaded Phone Holder (molas traseiras + furos
    de montagem para outras peças)
  - MakerWorld 1184780: Universal Spring-Loaded Phone Cradle

### Decisão pendente (S1)

Escolher A ou B após testar com a esteira real do laboratório:
- Se a demo pede troca rápida de esteira e narrativa forte: B.
- Se a estabilidade absoluta da calibração manda: A (ou B + trava secundária,
  ex: pino passante opcional que impede a mola de soltar: híbrido dos dois).

## Perguntas em aberto

1. Grip inteiro em T-slot de alumínio, ou híbrido (base MDF/impressão 3D +
   trilhos T-slot só nas travessas)? Custo vs rigidez.
2. Travamento à esteira: Opção A (garra M6/M8), Opção B (spring-loaded) ou
   híbrido B + trava secundária? (Esteira real do laboratório disponível para
   testar?)
3. Trigger e encoder fixos ao grip ou ao trilho da esteira? (Se a esteira varia,
   faz sentido o grip carregar o trigger com ele.)
