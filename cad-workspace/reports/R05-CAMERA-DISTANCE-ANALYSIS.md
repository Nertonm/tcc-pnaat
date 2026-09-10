# R05 — Distancia de câmera para captura da garrafa (foco <= 2L)

STATUS: analise optica formal, dados oficiais + contratto R05.

## FOV oficiais (product brief Raspberry Pi, jan/2023)
- CM3 Standard: diag 75 deg, H 66 deg, V 41 deg, f=4.74mm, foco 10cm-inf
- CM3 Wide:     diag 120 deg, H 102 deg, V 67 deg, f=2.75mm, foco 5cm-inf

Formula: d = S / (2 * tan(theta/2)), margem 10% para folga.

## Garrafas (contrato R05)
vol | H (max) | D (max, base)
2000 | 345 | 105 |  (pior caso)
1500 | 330 | 95
1000 | 300 | 85
600  | 240 | 75
200  | 140 | 55

## C_SIDE (garrafa inteira de lado)
Standard (V 41deg):  2L -> 508mm / 1.5L 485 / 1L 441 / 600 353 / 200 206
Wide (V 67deg):      2L -> 287mm / 1.5L 274 / 1L 249 / 600 199 / 200 116
(worst-case: 2L)

## C_TOP (Wide)
- disco topo: d=105mm -> 47mm, mas foco min 50mm -> 50mm cobre 123mm
- garrafa 2L inteira de cima: ~68mm

## Consequencias para o design
1. C_TOP Wide: distancia >=50mm do topo (basta Z_garrafa + 60..70mm).
2. C_SIDE: restricao OPTICA domina. Standard ~510mm, Wide ~287mm p/ 2L.
   Ambos > 20cm do cabo flat standard. Portanto a C_SIDE nao pode ficar
   no mesmo bloco compacto da Pi com cabo de 200mm preservando foco de
   garrafa inteira - precisa de braco/extensao ou cabo mais longo
   (Standard-Mini 300/500mm) e estrutura correndo o risco de vibracao.
3. O grip (G-clamp tripod Cults3D) nao resolve a distancia optica;
   resolve a ACOPLACAO mecanica. A distancia da C_SIDE define o braco.

## Decisao pendente
- C_SIDE em Standard (menos distorcao, mais distancia ~510mm, mais braco)
  ou Wide (mais proximo ~287mm, mais distorcao de borda)?
- A distorcao Wide afeta a metrica de inspecao (medir diametro)?

---

# REVISAO 2026-09-10 — 2 cameras em angulo obtuso (baixa-esquerda + alta-direita)

Proposta: 2 cameras, cada uma cobre MEIA garrafa, eixos obtusos opostos.
Revisado com formula d = S_proj / (2*tan(theta/2)), S_proj = S*cos(E),
restricao cabo: d_eixo * 1.10 (dobra) <= 190mm (cabo Standard-Mini 200).

## Cenario A — cada camera cobre meia garrafa (S = H/2)
2L (H345 D105):
  E=30  Standard 200mm >CABO | Wide 113mm OK
  E=45  Standard 163mm OK    | Wide 92mm  OK
  E=60  Standard 115mm OK    | Wide 65mm  OK
1L (H300): Standard E>=45 OK (142m), Wide sempre OK.
600ml: Standard E>=30 OK (139m); 200ml sempre OK.

Resolucao (2L, E=45): Standard 163mm -> 20.4 px/mm; Wide 92 -> 20.9 px/mm.
3mm de inclinacao de tampa -> ~43 px. Detectavel com folga.

## Cenario B — camera ALTA dedicada a tampa (S=55mm)
2L Standard 81mm / Wide 43mm — folga ABSURDA; cabo 200mm tranquilo.
A distancia da tampa e dominada pelo FOV horizontal (D), nao pela elevacao.

## Conclusao da revisao
1. A config de 2 cameras com meia garrafa ELIMINA o bloqueio dos 20cm:
   Standard 2L a E45° = 163mm de eixo (<=190 pratico). Wide = 92mm.
2. Resolucao MELHORA (20 px/mm vs 6.5 da garrafa inteira a 508mm).
3. Trade-off identifica: a elevacao alta desambiguiza a tampa (rank-2)
   mas reduz o campo vertical; com meia garrafa a E=45 sobreposicao
   de ~10% na costura entre as duas vistas e obrigatoria.

## Decisao recomendada
- Adotar Cen A (2 cameras, meia garrafa, E>=45°, Standard OU Wide)
  com overlap 10% na costura. Distancia de trabalho da camera:
  2L: ~165mm eixo (Standard) / ~95mm (Wide).
- Elevacao real do eixo deve ser >=45° para garantir cabo OK no pior caso.
- Resolver overlap: posicionar o limite das duas vistas ~55% H/45% H.

---

# CORRECAO 2026-09-10 — lados distintos: cada camera ve a LATERAL INTEIRA

A premissa "meia garrafa por camera" estava ERRADA: como sao lados
distintos (esq-baixo + dir-alto), CADA camera precisa cobrir a altura
inteira H (em angulo obtuso). Recalculado com H_proj = H*cos(E).

## Resultado (gate: d_eixo*1.10 <= 190mm, cabo Standard-Mini 200)
vol | cam | E_min | deixo | lat | resV (px/mm) | 3mm tampa -> px
2000 | standard | 69deg | 165mm | 59 | 7.2 | 22
2000 | wide     | 49deg | 171mm |112 | 7.4 | 22
1500 | standard | 67deg | 172mm | 67 | 7.5 | 23
1500 | wide     | 47deg | 170mm |116 | 7.7 | 23
1000 | standard | 65deg | 170mm | 72 | 8.3 | 25
1000 | wide     | 41deg | 171mm |129 | 8.5 | 26
600  | standard | 58deg | 170mm | 90 |10.3 | 31
200  | standard | 23deg | 172mm |159 |17.7 | 53

Pior caso 2L: Standard precisa E>=69deg (quase vertical, 21deg da
vertical); Wide E>=49deg. Distancia de eixo ~165-172mm em ambos ->
DENTRO do cabo 200mm (folga ~12%).

## O que a correcao muda (revisao critica)
1. A elevacao minima sobe MUITO para garrafa alta: 2L Standard = 69deg.
   Nao e mais "lateral obtusa suave"; e um eixo quase vertical.
2. O angulo entre os eixos: 2L Standard 2E=138deg (obtuso) ✓;
   Wide 2E=98deg (quase reto). Satisfaz "obtuso" para Standard.
3. Resolucao baixa na tampa para a camera BAIXA: com E=-69 a tampa cai
   no canto do fov (dist 239-243mm) -> 13.9/7.9 px/mm. Ainda detecta 3mm
   (~22-42px) mas a geometria da tampa e distal na vista baixa.
4. A "desambiguacao rank-2" continua valida: os 2 eixos opostos separam
   pitch e roll da tampa, mais forte com 2E>90.

## Recomendacao
- Manter 2 cameras lados opostos, cada uma com a lateral inteira.
- Elevacoes: Standard E>=69deg (2L), Wide E>=49deg. Wide e mais
  compativel com a "vista lateral obtusa" descrita (E~49 = 41deg da
  vertical) e oferece folga lateral (lat=112mm vs 59).
- Distancia de trabalho: ~170mm eixo (ambas), OK no cabo 200.
- Se a mal rosqueada precisar de melhor geometria de tampa na vista
  baixa, avaliar Wide (E menor -> tampa menos distal).
