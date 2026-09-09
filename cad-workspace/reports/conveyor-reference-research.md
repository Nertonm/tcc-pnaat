# Pesquisa de referências das esteiras

Data: 2026-09-08
Estado: REFERENCE ONLY
Uso: envelope preliminar e planejamento de caracterização
Fabricação autorizada: não

## Esteira industrial IN 150

Fonte de descoberta: Casa do Datador, página do produto IN 150.
URL: https://www.casadodatador.com/datadores-ink-jet/esteira-transportadora-em-inox-para-datadores-inkjet-modelo-in-150

Claims da página do fornecedor, não datasheet primário do fabricante:

- largura de lona declarada: 190 mm;
- comprimento declarado: 1,5 m;
- capacidade declarada: até 9 kg de arraste;
- velocidade máxima declarada: 21 m/min;
- motor declarado: indução monofásico, 220 V, 60 W;
- rotação declarada: até 130 rpm;
- peso líquido declarado: 20 kg;
- curso de guia declarado: 150 mm;
- material declarado: Inox 202;
- uma ou duas guias laterais.

Estado: LIKELY REFERENCE. Confirmar modelo, revisão e unidade física antes do CAD.

## Esteira industrial IN 150 Large

Fonte de descoberta: Casa do Datador, página do produto IN 150 Large.
URL: https://www.casadodatador.com/datadores-ink-jet/esteira-transportadora-em-inox-202-para-datadores-inkjet-modelo-in-150-large-220v

Claims da página do fornecedor:

- dimensão declarada: 1,47 m x 300 mm;
- altura declarada: 750 mm;
- capacidade declarada: até 12 kg de arraste;
- velocidade máxima declarada: 21 m/min;
- motor declarado: indução monofásico, 220 V, 120 W;
- rotação declarada: até 130 rpm;
- peso líquido declarado: 24 kg;
- curso de guia declarado: 150 mm;
- material declarado: Inox 202;
- uma ou duas guias laterais.

Estado: LIKELY REFERENCE. Não usar como geometria da unidade sem confirmar etiqueta e interfaces.

## Esteira didática

Nenhum modelo exato foi identificado. Projetos abertos semelhantes servem apenas como referência de arquitetura.

Fonte: https://github.com/simonlansing/conveyor-belt

O projeto aberto descreve uma mini esteira com:

- TT motor DC 3-6 V;
- Raspberry Pi;
- perfil de alumínio 20 x 40 x 290 mm;
- rolamentos 608 e 6800;
- correia elástica;
- sensores e servo.

Estado: REFERENCE ONLY. Não prova que a mini esteira do laboratório tenha essas dimensões ou componentes.

Fonte de referência para TT motor: https://thepihut.com/products/dc-gearbox-motor-tt-motor-200rpm-3-to-6vdc

Claims do fornecedor do motor:

- 3-6 V;
- redução 1:48;
- corpo aproximado 70 x 22 x 18 mm;
- massa aproximada 30,6 g;
- velocidade sem carga aproximada de 200 rpm em 6 V;
- corrente de stall aproximada de 1,5 A em 6 V.

Estado: REFERENCE ONLY. O motor real deve ser identificado e pesado.

## O que pode ser usado agora

- gerar envelopes visuais preliminares;
- estimar espaço de montagem;
- preparar lista de medições;
- definir interfaces candidatas;
- testar scripts CadQuery;
- comparar custo de adaptadores;
- planejar o M0.

## O que continua bloqueado

- furos e datums reais;
- espessura real do acrílico;
- chassi e interfaces da mini esteira;
- posição real dos roletes e motor;
- massa e centro de gravidade do módulo;
- vibração e aceleração;
- compatibilidade química do IN 150;
- carga admissível do ponto de montagem;
- tolerância de montagem;
- autorização de fabricação estrutural.

## Regra de uso no pipeline

```text
reference report → envelope/reference CAD only
physical G0      → Adapter/P0/M0 candidate
P1/P2            → load and repeatability evidence
```

Não copiar estes números para `data/g0/esteira-b-g0-template.yaml` como se fossem medições.
