# base-bracket-20260914

Base de chao do trilho: vao para a peca ja impressa + furo do parafuso.

## O que a base tem

    1. VAO para o bracket impresso entrar com a barra
       retangular, no envelope do bracket + 0,3 mm
       X -50,30..-10,70 (39,60)   Z 7,70..19,80 (12,10)
       de Y=16,00 (topo da placa, onde a peca assenta) ate Y=36,50 (fundo do trilho)

    2. CIRCULO VAZIO para o parafuso prender a peca
       furo passante O6,5 ao longo de Z, em X=-30,50 / Y=29,00
       escareado O13 x 1,0 de um lado (arruela M6 O12 + cabeca)
       o parafuso entra por um lado, atravessa o corpo, passa pelo vao,
       atravessa o bracket e sai do outro lado

    3. corpo subindo ate o fundo do trilho, placa com 4 furos passantes O4,5
       com rebaixo O9,0 x 5,0, e face inferior plana em Y=0

    BASE: 131,00 x 103,50 x 36,50 mm · 1 solido unico
          241 237,2 mm3 -> 306,4 g PETG · area de apoio 11 952,0 mm2

## De onde vem a posicao do furo (medido, nao suposto)

    conjunto M6 em posicao de uso (6 solidos, 34 741,2 mm3), 13 faces cilindricas:
       m6-haste-HW   X -33,50..-27,50   Y 82,40..88,40   Z -18,00..12,00
          -> eixo do M6:  X = -30,50   Y = 85,40   ao longo de Z
       m6-cabeca-HW  Z 12,00..18,00      -> a cabeca fica em +Z
       furos O6,35 do conjunto em (-30,50, 85,40, -4,95) e (-30,50, 73,00, -1,50)
    o bracket desceu 56,40 mm nesta base -> eixo vira Y = 85,40 - 56,40 = 29,00

## A peca de origem (intacta, ja impressa pelo usuario)

    composicao-corrigida-20260911/gripA-bracket.step   10 352,7 mm3 · 1 solido
    unico final de trilho que engata no MontanteA sem interferir (engate 5,50 mm,
    colisao 0,000000). gripA-clamp colide 183,4384; gripA-peca colide 16,4972;
    peca-dupla-plataformas / m6-peca tem plataformas = tem perna.

## Revisao

    isValid() ................ True          menor aresta .............. 4,9900 mm
    check(True) BOP .......... SEM ERRO      area de apoio em Y=0 ....... 11 952,0 mm2
    n. solids ................ 1
    base x bracket ........... 0,000000 mm3
    base x trilho ............ 0,000000 mm3
    bracket x trilho ......... 0,000000 mm3
    furo livre (cilindro O6,5 de ponta a ponta contra a base): 0,0000 mm3
    o mesmo cilindro contra o bracket: 4,3131 mm3 (roca a borda do furo dele
       -> as duas pecas estao alinhadas)

## Pendencias

1. Y=0 e suposicao, nao medicao: assumi que o piso esta em Y=0 no frame do projeto.
2. O furo O6,5 e folga para M6. Nao conferi se o parafuso real e M6 nem o
   comprimento: a haste medida tem 30 mm (Y -18..12 na composicao).
3. Nao calculei o caminho de carga nem o torque de aperto.
4. O trilho verga antes da base (35 mm contra 7,48 mm de parede fina).
