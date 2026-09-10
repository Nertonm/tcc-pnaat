# Referência: Real-time defect identification of products on a conveyor belt (Pysource)

## Fonte

- Título: Real-time defect identification of products on a conveyor belt
- Autor: Sergio Canu (Pysource)
- Data: 2023-02-14
- URL: https://pysource.com/blog (postagem "Real-time defect identification of products on a conveyor belt")
- Tipo: artigo de blog, proof-of-concept de inspeção de garrafas plásticas em esteira

## Pipeline descrita (fonte)

Abordagem básica de visão computacional em vídeo: **object detection + object tracking**.

1. **Object detection**: bounding box em volta da garrafa (e do rótulo), treinado com
   deep learning para reconhecer o objeto; dá posição e classe.
2. **Object tracking**: associa um **ID único** a cada garrafa para evitar conferir a
   mesma garrafa mais de uma vez e manter o histórico.
3. **Classificação de defeito**: cada garrafa é classificada; se danificada, o defeito é
   registrado e a garrafa fotografada (a imagem é salva em pasta).
4. **Database**: defeitos e IDs são gravados em banco SQL; permite estimar o **percentual
   de erro por lote** e monitorar a produção.
5. **Atuação opcional**: pode-se adicionar atividade física (ex.: gate para descartar a
   garrafa defeituosa).

Defeitos considerados na demo: (1) nível de água; (2) defeito/dano do plástico da garrafa;
(3) problema de rótulo (danificado ou ausente); (4) garrafas diferentes ou problemas gerais.

Hardware sugerido pelo autor para processamento não muito pesado: NVIDIA Jetson Nano /
Jetson Xavier, ou laptop com GPU NVIDIA.

Referência acadêmica citada no post: "Research and implementation of machine vision
technologies for empty bottle inspection systems".

## Análise para o Cenário 1 (Inspeção de envase)

Coerências com a nossa proposta (validam o desenho):

- ID único por garrafa + fotografia como evidência + banco + erro por lote/dashboard: é
  exatamente a nossa camada de **rastreabilidade** (PoC-05 registro local e PoC-07
  dashboard/recorrência).
- Multi-class de defeito por item: análogo aos nossos RF-02/03/04 (tampa ausente, mal
  rosqueada, deformidade do corpo).
- Atuação (gate) tratada como acréscimo opcional: coerente com o nosso recorte (sem
  atuação no núcleo; só visibilidade).

Divergências (por que não é o modelo/stack a adotar):

- **Mecanismo de ID**: eles usam object detection + tracking de vídeo para atribuir o ID.
  No nosso caso, com esteira e sensor de presença (E18-D80NK), o **trigger determinístico +
  janela multi-view** é mais simples e exato; tracking de vídeo pode ser registrado como
  alternativa/expansão de referência, não como núcleo.
- **Tipo de defeito**: nível de água e rótulo são alvos deles, fora do nosso escopo
  (nossos requisitos não cobrem rótulo/nível).
- **Hardware**: sugerem GPU/Jetson; nós rodamos no Pi 5 com inferência leve INT8. Mais
  restrito, reforçando a via de modelo leve (teacher-student + one-class leve).
- **Método de classificação**: eles seguem o caminho supervisionado (object detection +
  CNN), que não cobre defeito novo sem dados defeituosos. Complementa (não substitui) a
  nossa direção com one-class (CutPaste) + medição mm determinística.

Estado: CONFIRMED como descrição da fonte; relevância ao nosso dataset SPECULATIVE até
ensaio próprio. Arquivo é referência, não decisão de stack.

## Impacto em decisão

Não fecha decisão. Serve de referência para: (a) o caminho supervisionado (baseline) em
benchmark no nosso dataset; (b) o padrão ID+evidência+banco+dashboard por lote (nosso
PoC-05/07). Combinar com os candidatos já mapeados (one-class leve + medição mm +
professor-aluno) na decisão final de stack.