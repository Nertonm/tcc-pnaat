# Plano de impressão: K1C (uma oportunidade)

Data: 2026-09-11 · Workspace: `cad-workspace` (<host>)
Status: **planejamento**. Nada foi fatiado, nenhum G-code existe, nada impresso.

---

## 0. A impressora do laboratório

**Creality K1C**; referenciada no projeto em `reports/GRIP-MDF-FDM-DECISION-R01.md`
(seção "8. FDM na K1C"), que registra PETG como candidato e alerta que *"não foram
usados limites dimensionais da K1C"*.

Especificações conferidas em **5 fontes independentes** (RoboCore, Creality, filament2print, 3D Prime, Jaycar, PrintTuner):

| parâmetro | valor |
|---|---|
| Volume de impressão | **220 × 220 × 250 mm** |
| Temperatura máxima do bico | 300 °C (bico tri-metálico) |
| Temperatura máxima da mesa | 100 °C |
| Velocidade máxima | 600 mm/s (aceleração 20 000 mm/s²) |
| Câmara | **fechada** (enclosure) |

⚠️ **O que ainda NÃO é fato:** a máquina é a mesma que está no lab agora? Estado de
manutenção, bico montado (0,4 mm?), folga dos eixos, adesão da mesa, filamento em
estoque e umidade. **Isso só se resolve olhando a máquina.**

---

## 1. Inventário: o que é IMPRESSO (12 peças)

| peça | dimensões (mm) | qtd | observação |
|---|---|---|---|
| `PecaDuplaPlataformasOFICIAL` | 66,0 × 75,4 × 20,0 | **2** | a peça oficial validada (1 sólido, 22 763 mm³) |
| `JuncaoA/B` (luva de canto) | 43,0 × 43,0 × 25,4 | **2** | peça nova; canaleta = prisma da seção do trilho |
| `ClampFunctionalSource` (G-clamp) | 71,0 × 35,0 × 20,0 | **2** | do ZIP do joehann (é modelo de impressão) |
| `ChavetaA/B` | 6,2 × 14,6 × 5,0 | **2** | trava de altura; **1 mm em cisalhamento** |
| Sapata `clamp_protector` | (do ZIP) | 2 | protege a superfície da esteira |
| Parafuso de aperto `screw_and_knurled_knobHD` | (do ZIP) | 2 | mecanismo de aperto do clamp |

Todas caem dentro de 220 × 220 × 250 → **viável em uma chapa**, com sobra.

## 2. O que é COMPRADO (não imprime)

| item | medida | qtd | observação |
|---|---|---|---|
| Trilho DIN TS35 | 450 mm | 2 | montantes; aço |
| Trilho DIN TS35 | 600 mm | 1 | travessa; aço |
| Parafuso 1/4"-20 |; | 4 | 2 por clamp (os dois furos) |
| Parafuso M3 |; | 8 | 2 por luva (trava); **envelope no CAD, parafuso real a escolher** |

**Custo estimado: BLOCKED**; sem inventário, preços ou disponibilidade do lab.

---

## 3. CHECKLIST PRÉ-IMPRESSÃO: o que precisa ser revisado

### A. Geometria e ajuste (crítico)

| # | item | estado | por que importa |
|---|---|---|---|
| A1 | **Folga de impressão não modelada** | ✗ ABERTO | cada canaleta é a **fêmea exata** do trilho (folga 0 nominal). Na impressão são precisos **0,2–0,3 mm por lado**. Se imprimir como está, **não entra**; ou entra e não desliza |
| A2 | **Folga zero cancela a antirrotação** | ✗ ABERTO | a antirrotação demonstrada (colisão a 1°) depende do contato nominal. Com folga real, a luva gira **até encostar na chaveta**; a chaveta passa a ser o único bloqueio |
| A3 | Encaixe do trilho comprado | ✗ ABERTO | o CAD usa a seção **nominal** do fabricante. O trilho comprado tem tolerância de laminação; **medir o trilho real** antes de fechar a folga |
| A4 | Furos fecham na impressão | ✗ ABERTO | FDM contrai/fecha furo. Ø3,4 para M3 e Ø6,35 para 1/4" precisam de compensação (~0,1–0,2 mm) |
| A5 | Chaveta: 14,6 mm × 6,2 mm × **1 mm de espessura** | ✗ ABERTO | ver D1 |
| A6 | Sobreposição de fusão de 0,6 mm | ✓ fechado | usada para garantir sólido único (sem ela, a peça saía com 2 sólidos) |

### B. Material

| # | item | estado | por que importa |
|---|---|---|---|
| B1 | **Escolha do filamento** | ✗ ABERTO | PETG é o candidato do projeto. PLA é rígido mas flui e é frágil sob carga; ABS/ASA resiste mais mas exige câmara e empena |
| B2 | **Fluência (creep) do polímero** | ✗ ABERTO | o pórtico fica com carga **permanente**. PETG flui sob tensão constante; um ajuste apertado pode afrouxar em semanas |
| B3 | Anisotropia | ✗ ABERTO | a resistência na direção das camadas é uma fração da direção da extrusão. **A orientação de impressão da luva e da chaveta decide se elas quebram** |
| B4 | Estoque/umidade do filamento | ✗ ABERTO | filamento úmido = bolhas, delaminação, peça inútil |

### C. Processo e máquina

| # | item | estado |
|---|---|---|
| C1 | Bico realmente montado (0,4 mm?) | ✗ ABERTO; conferir na máquina |
| C2 | Nivelamento / mesh da mesa | ✗ ABERTO |
| C3 | Calibração de fluxo e temperatura para o filamento escolhido | ✗ ABERTO |
| C4 | Adesão (PEI? cola?) e primeira camada | ✗ ABERTO |
| C5 | Tempo total de impressão vs disponibilidade da máquina | ✗ ABERTO; estimar por fatiamento |
| C6 | Câmara fechada: temperatura interna para PETG/ABS | ✗ ABERTO |

### D. Resistência (nada foi calculado)

| # | item | estado | por que importa |
|---|---|---|---|
| D1 | **Chaveta de 1 mm em cisalhamento** | ✗ ABERTO | **toda a carga vertical do pórtico passa por essa chapa de 1 mm**. Nunca dimensionada |
| D2 | Peso real das câmeras + Pi + cabos | ✗ ABERTO | nunca pesado; sem massa não há momento |
| D3 | Momento no pórtico (braços, excentricidade) | ✗ ABERTO | o relatório de decisão cita M = F·e, sem números |
| D4 | Rigidez do trilho DIN como coluna de 450 mm | ✗ ABERTO | trilho é chapa dobrada de 1 mm; **não foi feito cálculo de flambagem** |
| D5 | Torção da travessa de 600 mm | ✗ ABERTO | idem |

### E. Montagem

| # | item | estado |
|---|---|---|
| E1 | Parafusos M3: tipo, cabeça, comprimento, aço | ✗ ABERTO |
| E2 | Parafuso de 1/4": comprimento correto para a peça dupla | ✗ ABERTO |
| E3 | Sequência de montagem (o que entra primeiro) | ✗ ABERTO |
| E4 | Ferramentas e acessos (chave allen curta?) | ✗ ABERTO |
| E5 | **Seção real da esteira** | ✗ ABERTO; **nunca medida**. O clamp agarra um cupom, não a máquina |

---

## 4. Estratégia para UMA oportunidade de impressão

Como só há uma chance, a ordem importa:

### Fase 1: CUPOM (antes de qualquer peça final)
Imprimir **1 chapa de cupons** (~30–40 min):
- luva **com a folga real** (0,2 / 0,25 / 0,3 mm por lado) → **qual desliza e trava**
- chaveta nos 3 comprimentos (14,6 / 15,6 / 16,6 mm) → medir o engate real na ranhura
- 1 amostra de furo Ø3,4 e Ø6,35 → medir o quanto fechou

**Isso torna a folga uma MEDIÇÃO, não um chute.** Sem essa fase, a chance de a peça grande não encaixar é alta.

### Fase 2: Peças críticas, uma por vez
1. `JuncaoA` + `ChavetaA` → **testar no trilho comprado** antes de imprimir as outras
2. só então `PecaDuplaPlataformasOFICIAL`

### Fase 3: Restante
G-clamp, sapata, parafuso de aperto, segunda luva e chaveta.

### Critérios de aceitação (definidos ANTES de imprimir)
- a luva desliza no trilho **com a mão** e não tem jogo angular perceptível
- a chaveta entra na ranhura e **para** o deslizamento axial
- o furo de 1/4" passa o parafuso **com a mão** (não precisa ser reaberto com broca)

### Plano B (se o encaixe falhar)
- raspar/limar a canaleta é aceitável em PETG
- se a chaveta quebrar: **plano B é parafuso passante** através da ranhura do trilho (o trilho já tem furos obround de 6,2 × 15 mm medidos); isso dispensa a peça impressa de trava
- se a luva girar: substituir por **cunha** (o trilho tem perfil que aceita)

---

## 5. As 3 incertezas que mais ameaçam a impressão

1. **Folga zero nominal → peça trava ou não entra.** É a mais provável de todas.
2. **Chaveta de 1 mm em cisalhamento.** A carga toda passa por ela; sem cálculo, é fé.
3. **Seção da esteira nunca medida.** O clamp pode simplesmente não agarrar a máquina real.

---

## 6. O que este plano NÃO afirma

- Nenhum G-code, fatiamento, tempo de impressão medido ou perfil de impressão foi criado.
- Nenhum cálculo de resistência, flambagem, fluência ou momento.
- Nenhuma verificação de que a K1C do lab está operacional hoje.
- Nenhum custo, estoque ou disponibilidade de material.
