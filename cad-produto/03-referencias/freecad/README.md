# Referências

Modelos oficiais e de terceiros usados para dimensionar o pórtico. Autor, fonte e
licença de cada um estão em `../../ATRIBUICOES.md`.

## Atenção ao link do vendor

`../vendor/` é um link simbólico para uma área de referências que fica fora
deste diretório. Hoje ele aponta para uma pasta com 1338 arquivos e funciona nesta
máquina. Uma cópia do projeto, um clone ou uma publicação não levam o conteúdo,
e o link fica apontando para o nada. A decisão entre copiar o conteúdo para dentro
do projeto ou remover o link está em aberto.

## O que existe atrás do link

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

Na raiz de `../vendor/` ficam as peças extraídas do modelo 301598 (`03-referencias/vendor/cam_cover.stl`,
`03-referencias/vendor/cam_housing.stl`, `03-referencias/vendor/cam_swivel.stl`, `03-referencias/vendor/camera_arm.stl`, `03-referencias/vendor/camera-reference-only.step`
e `03-referencias/vendor/camera-reference-only.FCStd`) e quatro arquivos de conferência.

## Modelos oficiais da Raspberry Pi

Baixados da Raspberry Pi Ltd, com licença MIT. O pacote traz o modelo do Pi 5, os
da Camera Module 3 nas versões padrão e wide, e três desenhos mecânicos, entre
eles o do cabo flexível de 200 mm.

O aviso que acompanha o modelo diz que ele serve só como orientação, sem garantia
de exatidão, e que quem for usá-lo para ajuste deve medir o produto físico.

## Ferramenta

FreeCAD. Os modelos foram lidos em STEP e exportados para `.stl` e `.FCStd` em
`../../00-produto/composicao-esteira/`, que também traz os scripts de montagem e
de conferência.
