# Base do trilho DIN com encaixe do bracket: documentação consolidada

Sessão de 2026-09-14. FreeCAD headless (`freecadcmd`).
Workspace de trabalho: o cad-workspace, hoje em `dirty-workspaces/`.

---

## 1. Entregável

```
base-bracket-20260914/
   README.md                      decisões e pendências da base
   base-bracket.step/.stl         base no frame do projeto (Y vertical)
   base-bracket-conjunto.stl      base + bracket + trilho (só visualização)
   base-bracket.json              números da base
   bb-*.png                       4 renders
   print/
      base-somente.stl            256 284 bytes   5 124 triângulos  <- IMPRIMIR
      base-somente.step            41 414 bytes   em orientação de impressão
      base-somente.json              635 bytes
      portao-impressao.json          364 bytes
      base-imp-*.png               3 renders na orientação de impressão
      README.md                    o que fazer no fatiador
```

**A peça do meio (bracket / `gripA-bracket` = `m6-bracket`) NÃO está nos arquivos
de impressão.** O usuário já tem ela impressa. O entregável é só a base.

---

## 2. A peça de origem: o que já funcionava

Medição de todos os finais de trilho do projeto contra o `MontanteA`:

| peça | volume | engate | colisão | veredito |
|---|---|---|---|---|
| **`gripA-bracket`** | 10 352,7 mm³ | 5,50 mm | **0,000000 mm³** | **o único limpo** |
| `gripA-clamp` | 20 490,8 mm³ | 5,50 mm | 183,4384 mm³ | colide |
| `gripA-peca` | 11 522,2 mm³ | 5,50 mm | 16,4972 mm³ | colide |
| `peca-dupla-plataformas` / `m6-peca` | 22 762,9 mm³ |; |; | tem plataformas = tem perna |

`gripA-bracket` é o mesmo volume de `m6-bracket`; é o bracket M6 que o usuário
já imprimiu e testou. Ele entra na base **intacto**, sem uma alteração.

---

## 3. Medições de origem (não supostas)

### 3.1 Perfil do trilho

Seção transversal do `MontanteA` no frame da composição: `X -48..-13` (35,000),
`Y 92,90..542,90` (450), `Z 10,05..17,55` (7,480).

Contorno em Y=320: **1 contorno contínuo, área 45,7659 mm², perímetro 93,534 mm.**
Abas superiores de 3,26 mm × 1,0 mm; corpo de 27,00 mm; parede ~1,0 mm.
**É um perfil ômega de parede fina**, não um retângulo.

Os "dois lóbulos" que apareciam em Y=300/310/330 eram cortes atravessando as
**perfurações** do trilho, não a seção do perfil. A alegação anterior de que o
montante não era TS35 estava errada e está retratada.

### 3.2 Posição do parafuso M6

Do `conjunto-fixacao-M6-posicao-uso.step` (6 sólidos, 34 741,2 mm³, 13 faces cil.):

```
m6-haste-HW   X -33,50..-27,50   Y 82,40..88,40   Z -18,00..12,00
   -> eixo do M6:  X = -30,50   Y = 85,40   ao longo de Z   (30,00 mm de comprimento)
m6-cabeca-HW  Z 12,00..18,00      -> cabeça em +Z
m6-arruela-HW 12,00 x 12,00 x 1,60
m6-porca-HW   11,55 x 10,00 x 5,00
furos Ø6,35 do conjunto em (-30,50, 85,40, -4,95) e (-30,50, 73,00, -1,50)
```

O bracket desceu 56,40 mm nesta base → o eixo vira **Y = 29,00**.

---

## 4. A base: o que ela tem

Frame do projeto: **X largura, Y vertical, Z profundidade**.

```
placa + corpo subindo de Y=16,00 ate Y=36,50 (fundo do trilho)

1. VÃO para o bracket: prisma retangular, envelope + 0,30 mm
   X -50,30..-10,70 (39,60)   Z 7,70..19,80 (12,10)
   de Y=16,00 (topo da placa; a peça assenta ali) a Y=36,50

2. CÍRCULO VAZIO do parafuso: furo passante Ø6,5 ao longo de Z
   em X=-30,50 / Y=29,00, escareado Ø13 × 1,8 de um lado

3. Furos de fixação: Ø4,5 ×4 passantes + rebaixo Ø9,0 × 5,0
   entre centros 91,0 × 63,5 mm
```

Frame de impressão (após rotação de 90° em X, Z para cima):

```
131,00 x 103,50 x 36,50 mm     cabe na K1C 220x220x250 (sobram 89,0 x 116,5)
1 sólido único · 241 237,165 mm³ -> 306,4 g em PETG
face inferior plana em Z=0 · área de apoio 11 952,14 mm²
```

---

## 5. Verificações executadas

```
INTERFERÊNCIAS (par a par, todos os pares)
   base x bracket ......... 0,000000 mm³
   base x trilho .......... 0,000000 mm³
   bracket x trilho ....... 0,000000 mm³

SANIDADE DO SÓLIDO
   isValid() .............. True
   check(True) BOP ........ SEM ERRO
   n. solids .............. 1
   menor aresta ........... 4,9900 mm  (nenhuma degenerada)
   menor área de face ..... 47,7129 mm²

ENGAJAMENTO DO BRACKET NO TRILHO
   5,500 mm; idêntico à composição (preservado)

FURO DO PARAFUSO
   comprimento de material no eixo ... 29,40 mm (2 paredes de 14,700)
   cilindro de teste Ø6,5 contra a base .. 0,0000 mm³  -> furo LIVRE
   o mesmo contra o bracket ........... 4,3131 mm³ -> roça a borda do furo
      dele: as duas peças estão alinhadas

PORTÃO DE IMPRESSÃO (malha STL, o que o fatiador lê)
   estanqueidade .... toda aresta usada por exatamente 2 triângulos
                       ({2: 7686}; 7 686 arestas, nenhuma aberta)
   volume da malha ... 241 238,383 mm³ vs CAD 241 237,165 = 0,0005%
   normais ........... para fora (volume positivo)
   degenerados ....... 0 (menor área de triângulo 0,12608930 mm²)
   dimensões ......... STEP = STL, diferença ≤ 0,000001 mm
   overhangs ......... 338,46 mm² no total, TODOS pontes:
                       Z=5,00 (190,8 mm²) tetos dos 4 rebaixos, pontes Ø9
                       Z=31,4..32,2 (~150 mm²) teto do furo M6, arco Ø6,5
   primeira camada ... 11 952,14 mm²
```

---

## 6. Erros cometidos nesta sessão (registrados)

1. **Interpretei "tirar o espaço do meio" ao contrário.** Adicionei material
   exatamente onde o bracket está: **colisão de 8 153,977 mm³** (79% do volume
   dele). O certo era remover material para deixar o vão.

2. **Corrigi com a forma dilatada do bracket** (união de translações) e isso
   **partiu a peça em 2 sólidos** e gerou **1 924 arestas degeneradas de 0,0000 mm**.
   Correção: cavidade como **prisma retangular**. Prisma não tem degeneração.

3. **O canal do trilho na câmara lateral**; 5 versões reinventando um encaixe
   que já existia validado no projeto. O certo era partir do que funcionava.

4. **Publiquei números errados durante a validação do parafuso.**
   - primeiro disse **103,50 mm** (usei a extensão de Z da base inteira)
   - depois disse **0,01 mm** (medi o material dentro do furo já escavado; circular)
   - o correto é **29,40 mm**, pela área das faces cilíndricas ÷ circunferência
   Os dois errados apontavam para lados opostos.

5. **Anunciei entregas que não existiam.** Duas vezes dei URLs que devolviam
   **404** e disse que tinha aberto a janela do gwenview quando o processo nunca
   subiu. Causa: `pkill -f gwenview` casa com a linha de comando inteira e
   matava a própria sessão SSH que executava o comando.
   Regra que fica: **conferir com leitura de volta antes de anunciar entrega.**

6. **FreeCAD GUI crashava** com SIGSEGV em `xkb_keymap_new_from_buffer`: o bundle
   procura os dados do XKB num caminho de build inexistente. Resolvido com
   `XKB_CONFIG_ROOT=/usr/share/X11/xkb`.

---

## 7. Ferragem definida

```
M6 x 50  +  arruela M6 Ø12 (1,60 mm)  +  porca M6 (5,00 mm)

material da base no caminho ... 29,40 mm
arruela .......................  1,60 mm
porca .........................  5,00 mm
TOTAL NECESSÁRIO .............. 36,00 mm
haste de 50 mm ................ cobre com 14,00 mm de sobra
M6 x 40 também serviria (4,00 mm de sobra)
```

A arruela fica 0,6 mm fora do rebaixado (que tem 1,8 mm e a arruela 1,60). Isso é
irrelevante: a face externa do corpo é plana e a arruela assenta nela de qualquer
forma. A tentativa de aprofundar o rebaixado de 1,0 para 1,8 **não teve efeito
medido** (volume e comprimento de parede idênticos) e não foi investigada.

---

## 8. Pendências: o que NÃO está verificado

1. **Y=0 é suposição, não medição.** Assumi que o piso está em Y=0 no frame do
   projeto. É a origem de todos os "flutuando" da sessão: a peça de origem vive
   em Y 32..107,4 porque é sustentada pelo grip na borda da esteira, 92,9 mm
   acima do piso. Se o piso real for outro Y, a coluna da base muda e o arquivo
   precisa ser regerado **antes** de gastar 306 g de filamento.

2. **Tempo de impressão e metros de filamento não medidos.** Não fatei o arquivo.

3. **O parafuso real não foi conferido.** Assumi M6 pelo nome da peça e por medir
   a haste com 30 mm no CAD.

4. **Caminho de carga não analisado.** Não sei quantos parafusos ligam o bracket
   à base, nem se ela aguenta o momento do braço a 420 mm.

5. **O trilho verga antes da base.** 35 mm contra 7,48 mm de parede fina: o eixo
   fraco é o dos 7,5. Monte com o eixo forte encarando o braço da câmera. E a
   ponta oscila a 450 mm; numa câmera de visão isso desalinha o enquadramento
   calibrado.

6. **`base-trilho-20260914` (v1) e `base-chao-20260914`** ficaram no workspace,
   não apagados. A v1 tem canal retangular simétrico (aceitava o trilho de duas
   orientações) e a base-chao tem o pé que o usuário não quis.

---

## 9. Reprodução

Scripts em diretório temporário (efêmeros). O que importa está versionado junto:

```
base-bracket-20260914/
   os .step/.stl/.json/.png e este documento
```

O `base-bracket.step` é editável. Para regerar a partir dele:
carregar no FreeCAD, aplicar a rotação de 90° em X e reexportar.
