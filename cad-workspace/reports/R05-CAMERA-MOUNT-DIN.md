# R05 — Mount da câmera CM3 Wide para trilho DIN (v3)

Data: 2026-09-10 · Spec: `data/concepts/camera-mount-spec-v1.md`
Artefato: `exports/concepts/optical-rig-r05/camera-mount-din-v3.step`
(v1 superado — mantido só como histórico)

## O que é
Peça única que recebe a Raspberry Pi Camera Module 3 Wide, inclina o eixo
óptico em 49° e se fixa ao trilho DIN TS35. É a ÚNICA peça do rig que
precisou ser projetada — todo o resto é componente pronto (case Pi5 DIN,
angle adapter 90°, bracket M6, trilho).

**Decisão de design:** o clip DIN não foi redesenhado. O `.3mf` do
`DIN Rail Bracket Redux` (herr_brain) é importado como base e o berço da
câmera é fundido nele — elimina a maior fonte de erro (reproduzir o encaixe).

## Dados de entrada (todos de fonte primária)
| dado | valor | origem |
|---|---|---|
| PCB do CM3 Wide | 23.86 × 25.00 × 1.01 mm (Z −0.75..+0.26) | STEP oficial |
| furos de montagem | Ø2.2 em X{2.0,14.5} Y{1.3,2.7,22.3,23.7} | 8 faces cil. r=1.10 |
| lente | aponta −Z, centro (14.40, 12.50), Ø11, Z −8.81..−0.75 | faces r≈5.4 |
| conector FPC | borda X 18.0–23.5, Z 0.6–2.6 | faces planas |
| canal do clip | 34.2 mm (base) → 32.0 mm (ponta, chanfro) | rasterização do .3mf |
| vertical no sistema do clip | eixo **Y** | análise de seções |
| face de montagem do clip | **Z=0** (garras sobem em Z 4.5–7.6) | scan material×Z |

## Construção (ordem que importa)
1. clip Redux importado (mesh → sólido)
2. placa de fundo 4 mm + paredes 2.6×6 mm + nervura de fusão 24×14
3. 4 pinos Ø2.0 nos furos da câmera
4. **cortes por último**: furo da lente Ø13 passante + recuo do conector FPC
5. rotação 49° em X, posicionamento na face de montagem (Z=0 do clip)

A ordem importa: se o furo for cortado antes de fundir a nervura, a nervura
o bloqueia (erro real detectado no teste de integração).

## Gates — resultado (medidos)
| # | gate | resultado |
|---|---|---|
| G1 | sólido único e válido | **PASS** (1 sólido, isValid, 9 618 mm³) |
| G2 | envelope K1C 220×220×250 | **PASS** (60.0 × 27.8 × 36.0 mm) |
| G3 | canal DIN 33–36 mm | **PASS** (34.2 → 32.0 mm, chanfro) |
| G4 | caixa dos pinos = 12.50 × 22.40 | **PASS** (do STEP oficial) |
| G5 | eixo óptico livre | **PASS** (interf. lente = 0.000 mm³) |
| G6 | zona do conector FPC livre | **PASS** (interf. FPC = 0.000 mm³) |
| G7 | ângulo 49° | **PASS** (49.0°; vertical = Y local) |
| G8 | round-trip STEP | **PASS** (reimport: 1 sólido, mesmas dims) |
| **G-INT** | **montagem da câmera sem interferência** | **PASS** (PCB 0.000 / lente 0.000 / FPC 0.000 mm³) |

## Erros reais que os gates/testes pegaram (por que não iteramos mais)
1. **Berço no lado errado do clip** — 1ª tentativa em Z=7.6 (lado do trilho);
   o canal está em Z 4.5–7.6 e a face de montagem é Z=0. Detectado por
   `solids=2` (fuse não uniu).
2. **Gate de ângulo com eixo errado** — media `|n.z|` (41°). No sistema local
   do clip a vertical é **Y**: `asin(|n.y|)` = 49.0°. O modelo estava certo.
3. **Gate do canal medido por vértices** — dava 32 mm (arestas do chanfro);
   o valor real é 34.2 mm na base.
4. **Câmera afundada na placa** — posicionada com a face traseira na placa;
   o correto é a face **frontal** (lente para dentro do furo): offset
   DZ = BED_T + 0.75. Detectado por 487 mm³ de interferência na PCB.
5. **Furo da lente raso** — a lente (8 mm) atravessava fora do furo. Agora
   passante (24 mm).
6. **Nervura bloqueando o furo** — cortes executados antes de fundir a
   nervura. Reordenado.

## Pendente
- Teste de integração com o STEP completo do CM3 (631 sólidos) — em execução;
  a validação por representações fiéis (PCB com furos Ø2.2 + lente Ø11 +
  conector, todas com dimensões extraídas do STEP) já passa com 0.000 mm³.
- Pivot de ajuste fino de ângulo (previsto no doc `grip-extensivel`), v1 não inclui.
- Trava anti-deriva (parafuso M3) contra o trilho — prevista, ainda não modelada.
- Impressão de teste e verificação física no trilho.

## Nota de licença
A base deriva do `DIN Rail Bracket Redux` (CC BY-SA 4.0). Redistribuir a peça
obriga atribuição e share-alike. O berço e demais acréscimos são do projeto.
