# R05 v7 — três câmeras para IN 150 nominal

Status: `CONTRACT_UPDATED / GEOMETRY_REFERENCE_ONLY`. Esta revisão restaura o
arranjo do TCC com três vistas: `C_TOP` e `C_LEFT` usam câmeras Raspberry Pi
por CSI; `C_RIGHT` é uma câmera USB-C/UVC. O modelo exato da câmera USB-C e o
comprimento/raio de dobra de seu cabo permanecem bloqueados para compra e
medição.

## Cenário de referência

- Esteira selecionada: IN 150 compacta, correia nominal de 190 mm e
  comprimento nominal de 1500 mm.
- Guia com curso informado de 150 mm; folga lateral de referência de 80 mm.
- Os dados foram fornecidos como aproximações pela equipe e estão registrados
  em `data/g0/esteira-a-reference-r01.yaml`. Eles não são uma coleta G0 e não
  liberam fabricação ou fixação ao chassi.
- Produto de referência: garrafas PET de 130–370 mm de altura e 50–120 mm de
  diâmetro. As cotas e eixos oficiais estão em
  `data/concepts/optical-rig-r05-contract.json`.

## Layout CAD

`C_TOP` mira -Z para a tampa. `C_LEFT` está no lado negativo de Y e mira +Y;
`C_RIGHT` está no lado positivo de Y e mira -Y. A ponte lateral é mantida
acima do envelope de 370 mm da garrafa e desce somente fora da correia. A
coluna alta contém o Pi e fornece rotas CSI para `C_TOP`/`C_LEFT`; a rota
USB-C/UVC é independente e deve receber alívio de tração.

## Clamp de tripé externo

O G-clamp de tripé indicado pela equipe é apropriado como candidato a
protótipo, não como dependência do repositório. O arquivo de terceiros e as
imagens do anúncio não foram versionados: é necessário confirmar licença,
autoria e permissão de redistribuição. O candidato deve ser conectado por um
adaptador do projeto com interface 1/4-20 e flange 60 × 44 mm com quatro M4;
essa interface ainda depende de medição física da borda/chassi.

## Gates que continuam obrigatórios

1. Executar build, core gate, refine e validate no FreeCAD/OCCT.
2. Medir G0 da interface estrutural da IN 150: espessura, largura e material
   da borda, zonas móveis, acesso ao aperto e distância da guia.
3. Selecionar a câmera USB-C/UVC e medir corpo, lente, conector e cabo.
4. Validar FOV, iluminação, carga, vibração, repetibilidade, slicing e
   retenção secundária. Nenhum deles é concluído apenas por este contrato.
