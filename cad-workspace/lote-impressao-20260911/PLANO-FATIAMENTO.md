---
tags: [type/report, theme/pnaat, theme/tcc]
aliases: []
lead: "Plano de fatiamento para uma unica chapa K1C: 17 pecas do portico PNAAT, com cupons incluidas por nao haver segunda impressao."
created: 2026-09-11
modified: 2026-09-11
review_status: draft
---

# Plano de fatiamento — UMA CHAPA (K1C 220×220×250)

**Restrição:** uma única oportunidade de impressão. Por isso os **cupons vão junto** com
o lote — não existe ciclo separado para calibrar antes.

## 1. O que vai na chapa — 17 unidades

### Grupo A — estrutura do grip (2 jogos, um por lado da esteira)

| peça | qtd | arquivo | orientação | vol (mm³) |
|---|---:|---|---|---:|
| adaptadora dupla plataformas | 2 | `orientada-peca-A` / `orientada-peca-B` | **X+** | 22 762,88 |
| luva (junção da travessa) | 2 | `luva-0.25-JuncaoA` / `-JuncaoB` | **X+** | 41 595,93 |
| bracket DIN (encaixe no trilho) | 2 | `orientada-bracket` | **Z+** | 10 352,71 |
| G-clamp | 2 | `orientada-clamp` | **Z+** | 20 490,76 |
| sapata (protetor do mordente) | 2 | `orientada-sapata` | **Z+** | 1 438,38 |
| parafuso + manípulo | 2 | `orientada-parafuso` | **Z+** | 10 262,50 |
| chaveta da luva | 2 | `orientada-chaveta-A` / `-B` | **Z+** | 411,35 |

### Grupo B — cupons de calibração (vão junto; validar depois de imprimir)

| peça | qtd | arquivo | orientação | por que |
|---|---:|---|---|---|
| cupom da luva 0,25 | 1 | `cupom-luva-0p25` | **X+** | mede a folga que entra no trilho real |
| cupom da luva 0,30 | 1 | `cupom-luva-0p3` | **X+** | alternativa, se a 0,25 ficar apertada |
| cupom do bracket 0,25 | 1 | `cupom-bracket-0p25` | **Z+** | mede o encaixe de 35,36→35,00 no trilho |

**Diretórios:**
- lote final: `lote-impressao-20260911/`
- cupons: `validacao-astra-20260911/cupom-*.step|.stl`

## 2. Números da chapa

```
área das peças ......... 29 035 mm²  (60,0% da mesa; margens e gaps inclusos no layout)
altura máxima .......... 43,0 mm     (cupom da luva; limite 250)
volume sólido .......... 203,5 cm³
massa PETG ............. ~259 g a 100% sólido   |   116–168 g com infill 15–25%
tempo de extrusão ...... ~3,8 h pura            |   total estimado 8–20 h
validade dimensional ... todas: 1 sólido, isValid=True, malha fechada
```

**Layout sugerido** (5 prateleiras; o auto-arrange do fatiador ajusta):

```
Y   0..66   peca-A (75,4x66) | peca-B (75,4x66) | luva-A (43x43)
Y  76..119  cupom-luva-0p25 (60x43) | cupom-luva-0p3 (60x43) | luva-B (43x43) | sapata#1
Y 129..164  clamp#1 (71x35) | clamp#2 (71x35) | bracket#1 (39x26)
Y 174..200  bracket#2 | cupom-bracket-0p25 | sapata#2 | parafuso#1 | chaveta-A
Y 206..220  parafuso#2 (71,3x19,8) | chaveta-B      ← usar o auto-arrange; sobra 30% da mesa
```

## 3. Ordem de operação

1. **Fatiar** com os parâmetros que você já usa para PETG (o plano antigo não os fixava):
   altura de camada, perímetros, infill, temperatura. **Sugestão mínima:** 4 perímetros
   nas peças que trabalham sob carga (peca, luva, bracket, clamp), infill 20–25% grid,
   brim 5 mm nas peças de base pequena (chaveta, sapata).
2. **Câmara:** PETG em K1C — imprimir com **tampa/porta aberta**. A câmara fechada da K1C
   chega a 35–40 °C e o PETG sofre heat creep em impressão longa.
3. **Varrer a chapa** por região, não de uma vez: se algo soltar, o resto continua.
4. **Ao terminar:** medir os cupons ANTES de montar. O cupom da luva 0,25 deve entrar no
   trilho real com a mão e deslizar até o batente. Se **não entrar**, a peça final tem o
   mesmo vão — e aí não há segunda chance: rebaixar o cupom não ajuda o lote já impresso.
5. **Remover os suportes embutidos do bracket** com alicate (o STL do vendor os traz e eles
   colidem 1,385 mm³ com o trilho).

## 4. O que ainda não está resolvido (não é bloqueado pela chapa)

| item | estado |
|---|---|
| **Fixação M6** | furo Ø6,35 passante na peça; o Astra recomenda passante com **arruela + porca metálica**. Comprar 2× de cada. Envelopes medidos com colisão 0. |
| **Resistência da membrana** | o furo atravessa só **3,1 mm** de material. Não há FEM nem ensaio — **não afirmar que aguenta**. |
| **A folga de 0,25 mm** | medida em CAD (vão real de 0,25 mm: +0,24 passa, +0,26 colide). **Não** é prova de que o PETG impresso entra. |
| **Origem do clamp** | a peça usada é válida e fechada; a "2ª componente" do STL tem 0,000122 mm³ (lasca). Mas há **dois modelos diferentes** no projeto — `G-clamp_Tripod` (usado, 20 490,76 mm³) e `joehann clamp_frame_long` (22 025,24 mm³), mesmo bbox. Decidir qual antes de fatiar. |
| **Trigger, iluminação, FPC, FOV** | zero no CAD. Continuam nas classes B/E/H da checklist v2. |
| **Cotas da esteira** | G0 BLOCKED — nunca medida fisicamente. |

## 5. Arquivos

```
lote-impressao-20260911/
  orientada-peca-A.step|.stl          orientada-bracket.step|.stl
  orientada-clamp.step|.stl           orientada-sapata.step|.stl
  orientada-parafuso.step|.stl        orientada-chaveta-A|B.step|.stl
  luva-0.25-JuncaoA|B.step|.stl       ← COM a folga de 0,25 mm aplicada
  lote.json                            volume/validade/malha/bbox por peça
  plano-chapa.json                     layout e números
  LOTE.sha256                          manifesto

validacao-astra-20260911/
  cupom-luva-0p18|0p25|0p3.step|.stl
  cupom-bracket-0p18|0p25|0p3.step|.stl
  RELATORIO-ASTRA-20260911.md (em ../)
```

**Nada foi commitado. Os originais estão intactos.**
