# R05 — Mount da câmera CM3 Wide para trilho DIN (v1)

Data: 2026-09-10 · Spec: `data/concepts/camera-mount-spec-v1.md` · Artefato:
`exports/concepts/optical-rig-r05/camera-mount-din-v1.step`

## O que é
Peça única que recebe a Raspberry Pi Camera Module 3 Wide, inclina o eixo
óptico em 49° e se fixa ao trilho DIN TS35. É a ÚNICA peça do rig que
precisou ser projetada — todo o resto é componente pronto (case Pi5 DIN,
angle adapter 90°, bracket M6, trilho).

**Decisão de design:** o clip DIN **não** foi redesenhado. O `.3mf` do
`DIN Rail Bracket Redux` (herr_brain) é importado como base e o berço da
câmera é fundido nele — elimina a maior fonte de erro (reproduzir o encaixe).

## Dados de entrada (todos de fonte primária)
| dado | valor | origem |
|---|---|---|
| PCB do CM3 Wide | 23.86 × 25.00 mm | STEP oficial |
| plano da PCB | Z ≈ 0 | faces de área 2111/1757 mm² |
| furos de montagem | Ø2.2 mm em X{2.0,14.5} Y{1.3,2.7,22.3,23.7} | 8 faces cil. r=1.10 |
| lente | aponta −Z, centro (14.40, 12.50), Ø ≈11 | faces r≈5.4 |
| conector FPC | borda X 18.0–23.5, Z 0.8–2.6 | faces planas em Z>0 |
| canal do clip | **34.2 mm** na base → 32.0 mm na ponta (chanfro) | medição rasterizada do .3mf |
| vertical no sistema do clip | eixo **Y** (o trilho corre em Y) | análise de seções |
| face de montagem do clip | **Z=0** (as garras sobem em Z 4.5–7.6) | scan material×Z |

## Construção
1. clip Redux importado (`Mesh` → `Part.makeSolid`)
2. berço no sistema local da câmera: placa 4 mm + paredes 2.6×6 mm, furo de
   lente Ø13 em (14.40, 12.50), recuo para o conector FPC na borda +X,
   4 pinos Ø2.0 nos furos Ø2.2
3. nervura de 24×14 mm que penetra 1.5 mm no clip (garante fusão num sólido)
4. rotação de 49° em X e posicionamento na face de montagem (Z=0 do clip)

## Gates — resultado (medidos, não presumidos)
| # | gate | resultado |
|---|---|---|
| G1 | sólido único e válido | **PASS** (1 sólido, isValid=True, 10 376 mm³) |
| G2 | envelope K1C 220×220×250 | **PASS** (60.0 × 27.4 × 35.5 mm) |
| G3 | canal DIN 33–36 mm | **PASS** (34.2 → 32.0 mm; chanfro de entrada) |
| G4 | caixa dos pinos = 12.50 × 22.40 | PASS (construído do STEP oficial) |
| G5 | eixo óptico livre (furo da lente) | **PASS** (amostragem: vazio em Z −2…−12) |
| G6 | zona do conector FPC livre | PASS (recuo na parede +X) |
| G7 | ângulo 49° | **PASS** (49.0°; vertical = Y local) |
| G8 | round-trip STEP | **PASS** (reimport: 1 sólido, mesmo volume, mesmas dims) |

### Erros que os gates pegaram (registro)
1. **Berço montado no lado errado** — primeira tentativa posicionou o berço
   em Z=7.6 (lado do trilho). O canal do clip está em Z 4.5–7.6 e a face de
   montagem é Z=0. Detectado por `solids=2` (não fundiu).
2. **Gate do ângulo com eixo errado** — media a elevação por `|n.z|`, dando
   41°. No sistema local do clip a **vertical é Y**: `asin(|n.y|)` = 49.0°.
   O modelo estava certo; o gate estava errado.
3. **Gate do canal por vértices** — dava 32 mm (arestas de chanfro). O valor
   real do canal é 34.2 mm na base; o parâmetro do autor (`closed_width`
   34 mm) confirma.

## Pendente
- Teste de integração: montar o STEP oficial do CM3 no mount e medir o volume
  de interferência (em execução — pesado: 631 sólidos).
- Ajuste fino de ângulo (pivot com trava) previsto no doc `grip-extensivel`
  ainda não incluído nesta v1.
- Impressão de teste e verificação física do encaixe no trilho.

## Nota de licença
A base deriva do `DIN Rail Bracket Redux` (CC BY-SA 4.0). Se a peça for
redistribuída, herda a licença e exige atribuição. O berço e demais
acréscimos são do projeto.
