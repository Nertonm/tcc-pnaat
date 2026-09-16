# Atribuições de modelos e referências de terceiros

Modelos e projetos baixados da internet e usados ou consultados neste trabalho.
A licença de cada um foi lida do arquivo que veio no próprio download, não de
busca na web.

## Modelos que entraram no produto

### Raspberry Pi 5 Din Rail

```
Autor ....... Diyalec
Fonte ....... Thingiverse, thing:6335141
Licença ..... Creative Commons Attribution-ShareAlike
Evidência ... LICENSE.txt do arquivo baixado
Uso ......... 02-impressao/case-pi-din/pi5-din-topside.stl
              e pi5-din-bottom-side.stl
```

O mesmo modelo está publicado no Printables 660057, listado lá com o autor alec, e
essa página declara que é remix de "Raspberry Pi DIN Rail Case", de mdkendall. O
desenho do autor em PDF que acompanha a pasta veio dessa página. Os nomes de autor
diferem entre as duas publicações.

### DIN Rail Bracket for M6 Bolts

```
Autor ....... ADSRMedia
Fonte ....... Printables, model 573570
Licença ..... Creative Commons Attribution-NonCommercial-ShareAlike 4.0
Evidência ... PDF da página do modelo, dentro do arquivo baixado
Uso ......... 02-impressao/base-trilho/, que expande o bracket já impresso
```

### Raspberry Pi 4B case with RPi camera 2 arm

```
Autor ....... Dominik Chuchlík
Fonte ....... Printables, model 301598
Licença ..... Creative Commons Attribution 4.0
Evidência ... PDF da página do modelo, dentro do arquivo baixado
Uso ......... 02-impressao/camera-lateral/
              housing, tampa, swivel e braço do suporte lateral
```

## Modelos oficiais da Raspberry Pi

```
Autor ....... Raspberry Pi Ltd
Licença ..... MIT, Copyright (c) 2026 Raspberry Pi Ltd
Evidência ... LICENSE.txt do pacote baixado
```

O pacote traz o modelo do Pi 5, os da Camera Module 3 nas versões padrão e wide, e
três desenhos mecânicos, entre eles o do cabo flexível de 200 mm. O aviso que
acompanha o modelo diz que ele serve só como orientação, sem garantia de exatidão,
e que quem for usá-lo para ajuste deve medir o produto físico.


### DIN-rail angle adapter

```
Autor ....... Shroamer
Fonte ....... Printables, model 1757341
Licença ..... Creative Commons Attribution-NonCommercial-ShareAlike 4.0
Evidência ... PDF da página do modelo, dentro do arquivo baixado
Uso ......... referência de adaptador de ângulo, não entrou no produto
```

### Breadboard din rail mount

```
Autor ....... Fellesverkstedet
Fonte ....... Thingiverse, thing:2705849
Licença ..... Creative Commons Attribution
Evidência ... LICENSE.txt do arquivo baixado
Uso ......... referência de fixação em trilho DIN, não entrou no produto
```

### Raspberry Pi Cam Holder for 30mm Alu Profile

```
Autor ....... DOMin8or
Fonte ....... Thingiverse, thing:5355988
Licença ..... Creative Commons Attribution
Evidência ... LICENSE.txt do arquivo baixado
Uso ......... referência de suporte de câmera, não entrou no produto
```

## Referências de software

### qwen-mm-plugins

```
Projeto ..... qwen-mm-plugins
Licença ..... Apache License 2.0
Evidência ... LICENSE na raiz do projeto baixado
Uso ......... plugin de FreeCAD usado durante o trabalho
```

## Modelos sem licença verificada

Estes foram baixados e não trazem licença dentro do pacote. A licença não foi
confirmada, e eles não devem ser redistribuídos sem essa confirmação.

```
Ender 5 Raspberry Pi camera case          pacote com 4 arquivos .stl
Case with Kodak thread for ESP32CAM CH340 pacote com 2 arquivos .stl
G-Clamp Tripod                            pacote sem licença
```

## Como as referências estão organizadas

`03-referencias/vendor/` é um link simbólico para uma área de referências que
fica fora deste diretório. Por isso ele não é copiado junto quando o projeto é
publicado, e o link deixa de funcionar em qualquer cópia.

O que está atrás do link, hoje:

```
raspberry-pi/               12 arquivos    modelos oficiais e desenhos mecânicos
din-rail-case/              13 arquivos    case do Pi 5 para trilho DIN
din-rail-parts/             18 arquivos    bracket M6, adaptador de ângulo, brutos
din-rail-standoff-2020/      4 arquivos    standoff para perfil 2020
g-clamp-tripod/              4 arquivos    referência de clamp
pi5-case-refs/             267 arquivos    projetos de referência de case para Pi 5
ender5-rpi-camera-case/      6 arquivos    case de câmera para Ender 5
qwen-mm-plugins/          1004 arquivos    plugin de FreeCAD
```


Dentro de `pi5-case-refs/` há quatro projetos distintos. O único com licença
explícita é `pcb-enclosure-generator`, MIT de Haden Cain. O diretório `pipiece`
tem um arquivo `LICENSE.sha256` cujo conteúdo é a palavra `no-LICENSE-file`, ou
seja, o próprio projeto declara não ter licença.

## Modelos próprios

O pórtico, os montantes, a travessa, as junções e a case da ESP32-CAM são geração
própria do projeto e não têm atribuição de terceiro.
