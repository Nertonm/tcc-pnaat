# PRONTAS PARA IMPRIMIR

Peças com **gate fechado**. Copiadas de `lote-impressao-20260911/` com o prefixo
`orientada-` removido, para fatiar direto.

**Atualizado 2026-09-11, fim da sessão.** O clamp foi decidido (TRIPOD) e entrou.
Sapata e parafuso saíram para `../NAO-USAR-sistema-joehann/`.

## As 7 peças

| arquivo | qtd | orientação | volume (mm³) | gate |
|---|---:|---|---:|---|
| `peca-A.stl` | 1 | **X+** | 22 762,88 | interface peça↔bracket: contato 791,66 mm², colisão 0 |
| `peca-B.stl` | 1 | **X+** | 22 762,88 | idem (espelhada, lado B) |
| `luva-0.18-JuncaoA.stl` | 1 | **X+** | 41 889,52 | **folga 0,18 validada no trilho real** |
| `luva-0.18-JuncaoB.stl` | 1 | **X+** | 41 889,52 | idem |
| `clamp.stl` | 2 | **Z+** | 20 490,76 | G-clamp **Tripod** — é o que o CAD, a peça e o bracket assumem |
| `chaveta-A.stl` | 1 | **Z+** | 411,35 | geometria fechada; overhang **0** |
| `chaveta-B.stl` | 1 | **Z+** | 411,35 | idem |

Volumes conferidos: `clamp.stl` = 20 490,7559 mm³, idêntico ao
`G-clamp_Tripod-component0.stl.brep` → **é o Tripod**, confirmado por comparação.
Os `.step` acompanham todas.

**Impressão desta chapa — 8 unidades:** peca ×2, luva ×2, clamp ×2, chaveta ×2.
Volume sólido **≈ 130 cm³** (45,5 + 83,8 + 41,0 + 0,8).

## Parâmetros

- **PETG na K1C:** tampa/porta **aberta** (câmara fechada → 35–40 °C → heat creep).
- **Perímetros:** 4 nas que trabalham sob carga (peca, luva, clamp).
- **Brim:** 5 mm nas de base pequena (chaveta).
- **Suporte:** nenhuma destas 7 exige. As que exigiam (cases) já foram impressas.

## Por que o clamp é o Tripod

Medido: o Tripod tem **furo de tripé Ø6,45** (eixo X) que casa com os **furos Ø6,35**
da adaptadora. O parafuso do sistema joehann tem rosca **Ø12** — não passa nesse furo.
Os dois sistemas são mutuamente exclusivos:

```
TRIPOD   → clamp + fixação M6 COMERCIAL (comprar 2× parafuso, 2× arruela, 2× porca)
JOEHANN  → clamp_frame_long (ausente no lote) + sapata + parafuso impresso
```

Escolhido o Tripod porque é o que o CAD, a peça e o bracket já assumem — e porque o
joehann exigiria gerar e imprimir mais uma peça que nunca foi verificada.

## Quarentena — `../NAO-USAR-sistema-joehann/`

`orientada-sapata.step|.stl`, `orientada-parafuso.step|.stl` — são do sistema
joehann e **não acoplam** no clamp do lote (rosca Ø12 × furo Ø6,45). Não fatiar
junto; se um dia quiser o segundo sistema, ele precisa do `clamp_frame_long`.

## Estado verificado nesta sessão

| item | resultado |
|---|---|
| **bracket × trilho** | impresso e testado por você: **encaixou** com folga 0,18 |
| **luva × trilho** | colisão 0; folga medida 0,18 (trilho +0,18 passa, +0,20 colide) |
| **peça × bracket** | contato 791,66 mm², colisão 0 |
| **case × trilho** | **tampa colisão 0,000** · base 0,944 mm³ (ajuste fino, não incompatibilidade), com CTL+ 70,89/87,41 e CTL− 0 |
| **conjunto M6** | peça + bracket + arruela + porca + cabeça + haste: **todos os pares colisão 0** |

## O que continua aberto (não bloqueia esta chapa)

- **Resistência do furo M6:** atravessa 3,1 mm de membrana. **Sem FEM, sem ensaio** —
  não afirmar que aguenta tração.
- **Trava do mount/case, antirrotação do grip, trava de largura:** não modeladas
  (violam D-17), fora do escopo desta rodada.
- **Trigger, iluminação, ESP-CAM, FPC, FOV:** zero no CAD (classes B/E/H da checklist v2).
- **Cotas da esteira:** G0 BLOCKED — nunca medida fisicamente.
