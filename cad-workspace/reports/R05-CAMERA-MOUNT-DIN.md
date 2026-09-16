# R05: Mount da câmera CM3 Wide para trilho DIN (v6; validado)

Data: 2026-09-10 · Spec: `data/concepts/camera-mount-spec-v1.md`
Artefato: `exports/concepts/optical-rig-r05/camera-mount-din-v6.step`
(v1/v3/v4/v5 superados; mantidos apenas como histórico no git)

## O que é
Peça que recebe a Raspberry Pi Camera Module 3 Wide, inclina o eixo óptico
em 49° e se fixa ao trilho DIN TS35. Base = clip do `DIN Rail Bracket Redux`
(importado, não redesenhado) + berço da câmera fundido.

## Validação final (medida com o modelo COMPLETO da câmera, 631 sólidos)
| métrica | valor |
|---|---|
| **interferência mount × câmera** | **0.0434 mm³** (limite 0.1); PASS |
| sólido | 1, válido, 8 787 mm³ |
| bbox | 60.0 × 27.7 × 35.8 mm (K1C 220×220×250 ✓) |
| canal DIN | 34.2 → 32.0 mm (chanfro de entrada) |
| ângulo do eixo óptico | 49.0° (vertical = Y local) |
| round-trip STEP | PASS |

## Dimensões críticas extraídas do STEP oficial (não estimadas)
| dado | valor |
|---|---|
| PCB | 23.86 × 25.00 × 1.01 mm (Z −0.75..+0.26) |
| carcaça da lente | **18.1 × 11.15 mm, desce 2.31 mm atrás da PCB** |
| furos Ø2.2 | 8 faces em X{2.0,14.5} × Y{1.3,2.7,22.3,23.7}; **dois conjuntos deslocados 1.4 mm** (ambíguos) |
| conector FPC | X 16.95–23.49 · **Y 1.04–23.96** · Z 0.03–2.60 |
| componentes acima da PCB | 12 sólidos (sensor 29.8 mm³, 3 chips, 3 pinos) |

## Decisões de design (e por quê)
1. **Recesso retangular 19.3 × 12.3 mm** (não furo circular); a carcaça da
   lente tem 18 mm de largura; um furo Ø13 não cobre.
2. **Sem pinos de alinhamento**; os furos do STEP vêm em dois conjuntos
   deslocados 1.4 mm; qualquer escolha erra 50%. Retenção pelo encaixe da
   PCB na cavidade (folga 0.25 mm/lado).
3. **Parede da borda do conector FPC removida** (o conector ocupa 23 mm dessa
   borda) + lip de 0.7 mm abaixo dele.
4. **Cortes por último**; se cortados antes, a nervura de fusão os bloqueia.
5. **Câmera apoia pela face frontal** (lente para dentro do recesso):
   offset DZ = BED_T + 0.75.

## Os 5 defeitos que os testes acharam (e que a validação visual não pegaria)
| # | defeito | como apareceu |
|---|---|---|
| 1 | berço no lado errado do clip (lado do trilho) | `solids=2` no fuse |
| 2 | câmera com a face traseira apoiada (afundada 4 mm) | 487 mm³ na PCB |
| 3 | furo da lente raso (lente saía do furo) | 445 mm³ na lente |
| 4 | nervura bloqueando o furo da lente | ordem das operações |
| 5 | parede colidindo com o conector FPC de 23 mm | 112.96 mm³ |
| 6 | furo Ø13 não cobre a carcaça da lente | 100.03 mm³ |
| 7 | pinos raspando nos furos ambíguos | 2.2 → 0.04 mm³ após remover |

## Arquitetura alinhada com o usuário (2026-09-10)
- Pi no **alto do trilho**, equidistante das câmeras (cabo FPC 200 mm alcança)
- Laterais nas **duas faces do trilho** → 1 STL impresso 2× (um espelhado)
- Trava anti-deriva **impressa** (a modelar)
- Ângulo **fixo em 49°** (sem pivot; decisão do usuário)
- Câmera de topo sai na travessa via angle adapter 90°

## Pendente
- mount do topo (travessa)
- trava impressa anti-deriva
- verificação física: impressão + teste no trilho real
- confirmar se a garrafa passa entre o trilho e a câmera frontal

## Licença
Base derivada do `DIN Rail Bracket Redux` (CC BY-SA 4.0) → derivado herda
share-alike + atribuição.
