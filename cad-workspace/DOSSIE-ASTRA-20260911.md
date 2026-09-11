---
tags: [type/report, theme/pnaat, theme/tcc]
aliases: []
lead: "Dossie para o Astra: estado verificado do grip do portico PNAAT, modificacoes da peca e instrucoes de fabricacao."
created: 2026-09-11
modified: 2026-09-11
review_status: draft
---

# Dossiê para o Astra — grip do pórtico PNAAT

Sessão CAD de 2026-09-11. Host: <host>. Workspace: `/home/<usuario>/tcc-pnaat/github/cad-workspace`.
FreeCAD 1.1.1 headless. **Nada commitado, nada impresso.**

## 0. Regras de trabalho (o que aprendi doendo nesta sessão)

1. **A vertical do modelo é Y**, não Z. Um script que faça `Rot(Z,180)` vira o pórtico de cabeça para baixo — silenciosamente.
2. **Nenhum medidor vale sem controle positivo E negativo na mesma rodada.** O padrão de bug desta sessão é `vol = it.Volume if it.Solids else 0.0`, que mascara 2163,7 mm³ como 0,000000. A bateria `area > 300` do `adv4.py` está dentro da dispersão do instrumento.
3. **Medir a geometria antes de varrer o espaço de posições.** O canal do bracket esteve sempre em Y e eu procurei em X por ~1000 booleanos.
4. **Quando um número meu contradiz uma medição independente, a primeira suspeita é o meu setup.**
5. `face.common()` entre faces cruzadas devolve 0 — não serve para medir contato com interferência.
6. O guard `Part.makeSolid(Shells[0])` pega fragmento quando a malha tem mais de uma shell.

## 1. O que está VERIFICADO (com números)

| item | valor | como |
|---|---|---|
| bracket × trilho **lado A** | colisão **0,000000 mm³**, dist 0,000000 | `bracket` rot 90° Z, engate 5,5 mm, tz=8,0 |
| bracket × trilho **lado B** | colisão **0,000000 mm³**, dist 0,000000 | espelho em X (mantém Z) |
| controles do medidor | +3 mm → 137,30; +500 mm → 0,000000 | nos dois lados |
| **bracket × peça** | contato **791,665 mm²**, colisão **0,000000** | peça com rebaixo + furo |
| peça × trilho | 0,000000 | — |
| seção do trilho (vendor) | 45,768141 mm², 20 arestas, chapa 1,000 uniforme | Winford DINR135-007.5 |
| trilho reconstruído | oco, válido, 19070,15 mm³ em 450 mm | = 450×45,768 − 18×84,751 |
| canal do bracket | **35,360 mm** para trilho de 35,000 → folga **+0,18 mm/lado** | pares de planos antiparalelos |
| furo M6 do bracket | eixo **Z**, em (-30,50, 85,40) após rot 90°Z | — |
| bracket é simétrico em Y | symdiff 0,00% | — |

### Engrenagens que fecharam

- **Rotação do bracket: 90° em Z** → canal fica ⟂Y (trilho vertical) e o furo M6 fica ⟂Z, apontando para o topo da peça.
- **Engate: 5,5 mm** na ponta do trilho (o PDF do autor: *"5.5mm of the rail inserts into each end"*). Engate de 20,5 mm (o que eu fazia) dá 786,64 mm³ de colisão.
- **Assentamento: tz = 8,0** (janela estreita 7,9–8,1; 0,2 mm fora já dá 6,5 mm³).
- **Lado B: espelhar em X**, não rotacionar 180° — a rotação mapeia Z→−Z e o TS35 é assimétrico em Z (23,4 na base, 35,0 só na aba).

## 2. Modificações necessárias na peça oficial

A peça `peca-dupla-plataformas.step` (22 762,88 mm³) **não tem** furo Ø6,35 ⟂Z e tem
um degrau de 0,5 mm no topo (duas alturas: 19,5 com 787,83 mm² e 20 com 606,01 mm²).

Aplicado (em cópia, original intacto) — arquivo `peca-assento-nivelado-furo-M6.step`:

| # | operação | o que faz | remove |
|---|---|---|---|
| 1 | **rebaixo** — caixa 39,5 × 26,5 × 12 acima de Z=19,5 na pegada do bracket | nivela o assento (mata o degrau) | **16,81 mm³** |
| 2 | **furo Ø6,35 ⟂Z** em (-30,50, 85,40) | passagem do parafuso M6, alinhado ao furo do bracket | **98,175 mm³** |

Volume final: **22 647,90 mm³**. `solids=1`, `isValid=True`. Nenhuma dimensão externa mudou.

## 3. Montagem (na ordem)

```
1. bracket rot 90° em Z
2. engatar 5,5 mm na ponta inferior do trilho (YMin do trilho + 5,5)
3. assentar: base do bracket = YMin do trilho − 2 (tz=8,0 no frame do construído)
4. centrar em X no trilho (centro X do bracket = centro X do trilho)
5. peça: topo rebaixado (Z=19,5) na base do bracket, centrada pelo furo
6. parafuso M6 atravessa o furo novo da peça e entra no bracket
7. lado B: espelhar o conjunto em X (não rotacionar)
```

## 4. O que está PENDENTE (não fechei)

**Bloqueadores de impressão (da checklist v2, 22 itens):**

- **Interfaces com o mundo físico**: trigger E18-D80NK (zero no CAD), encoder KY-040, iluminação/difusor/anteparo, ESP-CAM (sem envelope), cabo FPC (sem rota).
- **FOV / distância de trabalho / altura**: nunca calculados por requisito. A altura do mount e a distância ao item **são** a geometria impressa.
- **Retenção anti-queda**: exigida por `grip-extensivel.md:82-83`, ausente. O pórtico pode cair sobre a esteira.
- **Anti-rotação no grip**: afirmada, não testada. O clamp tem 2 furos de tripé (não 1).
- **Trava do mount/case**: "a modelar"; viola D-17.
- **A largura (travessa) não tem trava positiva** (a altura tem chaveta).
- **Folga zero na luva** (medida: 0,5 µm → 0,69 mm³), enquanto o precedente validado do próprio projeto tem 0,18 mm/lado.
- **O plano de impressão não tem orientação, parâmetros de fatiamento, G-code nem tempo.** O cupom de 3 luvas está subestimado 4–10×.
- **Licenças**: bracket M6 (CC BY-NC-SA) fundido na nossa peça = obra derivada; CM3 e Winford sem licença; GPL-2 misturado; zero NOTICE. Ver classe D da v2.
- **Os 4 suportes embutidos do STL** do bracket colidem 1,385 mm³ com o trilho — sem removê-los com alicate, o trilho não entra.

**Dependência-raiz:** a seção real da esteira nunca foi medida (G0 BLOCKED). Dela dependem o mordente de 10 mm, a distância de trabalho, o vão 400/600, a altura 450/362,5 e as massas/CG.

## 5. Arquivos

```
cad-workspace/composicao-corrigida-20260911/
  composicao-corrigida.FCStd          cena completa (abre no FreeCAD)
  corrigida-iso.png · -frente.png · -lado.png
  gripA-bracket.step / gripB-bracket.step
  gripA-clamp.step / gripB-clamp.step
  gripA-peca.step  / gripB-peca.step
  repro-montagem.py                   reproduz a montagem e as medições

cad-workspace/interface-peca-bracket-20260911/
  peca-assento-nivelado-furo-M6.step  ← A PEÇA CORRIGIDA (com rebaixo + furo)
  conjunto-fechado.step               ← peça corrigida + bracket (contato 791,665 mm²)
  peca-assento-nivelado.step          (só o rebaixo)
  bracket-rot90Z-no-trilho.step

cad-workspace/CHECKLIST-ADVERSARIAL-v2-20260911.md   (64 KB, 445 linhas)
```

## 6. O que eu pediria ao Astra

1. **Reproduzir** a montagem do `repro-montagem.py` e confirmar os 0,000000 independentemente.
2. **Revisar a peça corrigida** (rebaixo + furo) quanto a: esforço no furo novo (o parafuso M6 tração), espessura remanescente no topo rebaixado, e se o rebaixo enfraquece a plataforma.
3. **Fechar o furo da fixação**: eu abri Ø6,35 (clearance). O bracket pede M6 — verificar se cabe porca/inserto ou se é rosca direta no PETG.
4. **Traduzir para o formato de impressão**: orientação por peça, overhangs medidos, suportes, tolerâncias, e o cupom de encaixe (o bracket é 35,360 para trilho 35,000 — em FDM pode não entrar).
