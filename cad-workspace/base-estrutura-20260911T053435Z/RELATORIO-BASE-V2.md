# Base v2 — conjunto DIN verificado

Data: 2026-09-11 · Candidato: `structural-candidate-20260911T053435Z/`
**Status: gates da BASE passaram. NÃO é aprovação de fabricação.**

## Resultado dos gates

```
base_parts_pass      : true    todas as peças válidas, 1 sólido cada
base_collision_pass  : true    ZERO colisões (nenhum par não-zero)
m6_rail_fit          : common 0.000 · distance 0.000
```

## Correção de um erro meu (registrado)

Na R07 eu descartei o bracket M6 alegando que ele "nunca encaixa (mordida de
151–250 mm³)". **Isso estava errado** — eu o montava na orientação errada.
O auditor já havia apontado que o M6 tem **suportes removíveis** (5 componentes)
que eu não havia separado.

Separando o `component0` (o corpo real) e orientando pelo datum correto:

```
M6 × trilho:  overlap 0,000 mm³ · gap 0,000 mm · inserção 5,5 mm
```

**5,5 mm de inserção** é exatamente o que o PDF do autor declara. O M6 é a
interface de trilho, não o Redux.

## O que foi corrigido nesta rodada

| defeito | correção |
|---|---|
| `SpineCap` colidia com o clamp (0,725 mm³) | varredura de 14 posições → Y 52..55 (colisão 0) |
| `SocketSaddle` sem os furos de fixação (erro meu) | furos Ø4,4 cortados na sela |
| cabeçote do parafuso (Ø7) colidia com o cap (44 mm³) | escareado Ø7,5 no cap |
| G-clamp vinha como 2 componentes / `isSolid=false` | `component0` isolado → 1 sólido válido, fechado |

## Peças do conjunto (11 objetos)

| peça | origem |
|---|---|
| ClampFunctionalSource | `G-clamp_Tripod` component0 (do usuário) |
| SocketSaddleAdapted | peça nova — sela que abraça o clamp em Z nas duas laterais |
| SpineCap | peça nova — tampa com escareado |
| Rail75Actual | STEP Winford real (seção preservada, não substituída por cubo) |
| 2× SaddleBolt/Nut Envelope | **envelopes Ø4** — não são parafusos reais, não afirmam rosca |
| RailRetentionBolt/Nut | retenção do trilho |
| Parafuso de aperto original | `screw_and_knurled_knobHD.stl` do ZIP 1673030 (joehann) |

**Mecanismo de aperto:** encontrado o ZIP original no Downloads com
`clamp_frame`, `clamp_protector` (sapata) e `screw_and_knurled_knobHD`
(parafuso com manípulo). Não foi preciso inventar rosca.

## Testes negativos

- `negative_extraction_pin_overlap = 2,817 mm³` — deslocando o trilho 2 mm, o
  pino de retenção ainda interfere: **o trilho não é extraído livremente**.
  Comportamento esperado de retenção; **não** é medição de força.
- Varredura do cap: 14 posições testadas, o teste negativo detecta a posição
  antiga (Y 54) como colisão e a nova (Y 52) como limpa.

## O que NÃO está validado

1. **Seção real da lateral da esteira** — nunca medida (G0 pendente). O contato
   é um cupom dimensional, não a máquina.
2. **Fixadores** — os envelopes Ø4 são candidatos M4; não há rosca modelada,
   torque, nem parafuso real escolhido.
3. **Cargas, vibração, fadiga, repetibilidade** — nada avaliado.
4. **Rigidez do trilho em balanço** — sem cálculo.
5. **Montantes e travessa** — a base é o primeiro elemento; o pórtico
   (2 montantes + travessa com ajuste de altura/largura) ainda não foi construído.
6. **Câmeras, Pi, cabos, trigger** — não iniciados (por decisão de sequência).

## Arquivos
```
base-v2.FCStd · base-v2.step · base-v2-checks.json
base-v2-iso.png · base-v2-topo.png · base-v2-lado.png
inputs/  (ZIP original 1673030, STEP do trilho, componentes separados)
build_base.py · mechanism_probe.py (do subagente) · fixb4.py (correções)
```

Nenhum commit, push ou merge. Originais preservados (SHAs em `checks-*.json`).
