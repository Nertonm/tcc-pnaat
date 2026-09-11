# Peça de duas plataformas — dois modos de montagem (R08)

Data: 2026-09-11 · Candidato: `structural-candidate-20260911T053435Z/`
Status: **geometria verificada** · não é aprovação de fabricação

## O pedido

*"tem que ter um approach pros dois jeitos pq dependendo da esteira um é viável e o
outro não"* — ou seja: a interface não pode depender de uma só configuração de clamp.

## A solução: UMA peça, DUAS plataformas

A peça abraça o canto do clamp e oferece **duas superfícies de montagem planas**, em
planos perpendiculares:

```
        plataforma H  (66 × 20 mm)  → em Y = 73,00
   ┌──────────────────────────┐
   │                          │
   │        CLAMP             ├── plataforma V  (41 × 20 mm)  → em X = −72,00
   └──────────────────────────┘
```

O mesmo bracket M6 engata em **qualquer uma** delas — e o trilho sobe nos dois casos.

## Verificação (booleans, com sólidos válidos)

| configuração | contatos medidos |
|---|---|
| **CFG1 — bracket na plataforma superior** | peça 0,0000 · clamp 0,0000 · **trilho×bracket 0,0000** (encaixa) |
| **CFG2 — bracket na plataforma lateral** | peça 0,0000 · clamp 0,0000 |
| peça | **1 sólido válido**, 11 740 mm³ |

Nenhuma colisão em nenhuma das duas. O contato é de face (assentamento), não de aresta.

## Quando usar cada um

| se a esteira... | usar | por quê |
|---|---|---|
| tem a espessura deitada (mesa, chapa horizontal) | **CFG1** (topo) | o clamp fica normal, a plataforma superior fica livre e para cima |
| tem a borda em pé, ou o topo fica obstruído pela máquina | **CFG2** (lateral) | a plataforma lateral fica acessível sem depender do topo |
| tem espaço só de um lado | a plataforma daquele lado | as duas são independentes |

A peça também pode ser **girada 180°** para usar os mesmos furos do lado oposto da
máquina — os furos são simétricos nos dois braços.

## O que a peça resolve

1. **Antirrotação** — dois parafusos em eixos perpendiculares (furo +Y e furo −X do clamp).
2. **Versatilidade** — duas plataformas na mesma peça, sem peça extra.
3. **Caminho de carga** — a força vai para duas faces do clamp, não para uma.

## O que NÃO está resolvido

1. **Qual configuração é a certa para a sua esteira** — isso exige **medir a máquina**
   (espessura da borda, acesso, espaço). Enquanto não medirmos, as duas ficam como
   opções válidas no papel.
2. **Fixadores** — os furos são Ø6,35 (1/4") para o clamp e Ø3,4 para o bracket;
   nenhum parafuso real foi escolhido, sem torque, sem rosca modelada.
3. **Cargas, vibração, rigidez, fadiga** — nada calculado.
4. **O bracket na CFG2** — a geometria foi verificada, mas o engate do trilho nessa
   orientação não foi testado com o trilho (só o assentamento do bracket).
5. **Montantes e travessa** — o pórtico completo ainda não foi construído.

## Arquivos
```
doisjeitos-iso.png · doisjeitos-topo.png · doisjeitos-frente.png
(SL do render no <host>; cena aberta no FreeCAD como 'DoisJeitos')
```

Nenhum commit, push ou merge. Originais preservados.
