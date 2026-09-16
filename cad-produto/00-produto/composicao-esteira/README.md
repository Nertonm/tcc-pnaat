# Composição r03: três câmeras e case Pi com DIN nativo

Revisão ilustrativa, não liberada para fabricação. Preserva r02 e arquivos anteriores.

## Correções 
- RPi-Cam superior, sobre a garrafa, com eixo óptico -Z; USB e ESP permanecem laterais.
- Case Raspberry Pi5 usando o clip DIN lateral ORIGINAL, sem modificar a geometria do fabricante.
- Removidos bandeja Pi, colar externo Pi e seus parafusos.
- Canal nativo localizado na lateral +X da case fonte, com limites Y -66,848747..-31,34853 mm.
  A case gira 90 graus em Z e recebe translação (-248,899; -89,5256; 1145) mm.
  O trilho percorre o canal na direção Z do conjunto. Não é mais alinhamento pelo envelope do fundo.

## Evidência geométrica
Limites conferidos entre FCStd/STEP/STL; 
Contato/distância zero no clip nativo; interferência residual nominal medida:
base 0,032059 mm³; tampa 0,009163 mm³. Não chamamos esses valores de zero.
As micro-shells da fonte foram preservadas na composição. O verificador limita o volume excluído
no teste do clip a aproximadamente 0,004257 mm³ na base; detalhes no JSON.
Controle deslocado 1 mm para dentro: 98,386387 mm³ de colisão.
Controle deslocado 1 mm para fora: 10,256758 mm³ contra o gancho nativo.
Controle afastado: zero. Isso demonstra que o teste detecta penetração e captura geométrica,
não força de retenção ou deformação de snap-fit. Compatibilidade física foi confirmada pelo usuário.

RPi-Cam: eixo medido (0,0,-1), alinhamento com a garrafa dot=1; lente 110,2836 mm acima
do topo da garrafa de referência. Isso NÃO valida foco, FOV ou enquadramento.
Suporte superior toca a case e tem interferência zero medida contra a travessa.
Nenhuma interferência acima de 0,1 mm³ no conjunto de pares testados, com o par Pi/trilho
avaliado separadamente por janela geométrica da interface. 

## Fontes e limites
Case Pi5: Printables 660057, alec/Diyalec, remix de mdkendall, CC BY-SA 4.0.
RPi-Cam: housing e cover reais da referência Printables 301598 existente no projeto.
PCB e lente são ilustrações dentro da case; não é validação dimensional de Camera Module 3 Wide.
Suporte da câmera superior é conceitual; não liberado para imprimir ou carregar equipamento.
ESP-CAM, webcam genérica, esteira e demais limites seguem a revisão r02, cuja documentação
é ../composicao-esteira-usb-esp-ilustrativa-r02/README.md. Licença ESP segue não verificada.
FPC, alimentação e alívio de tração não foram roteados. Não há aprovação estrutural, térmica,
metrológica ou de fabricação. Não se afirma compatibilidade universal de câmeras.
Imagens geradas, mas não certificadas por inspeção visual: ferramenta de visão falhou por configuração do provedor.


