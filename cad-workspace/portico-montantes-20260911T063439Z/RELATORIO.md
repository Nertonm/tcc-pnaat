# Pórtico PNAAT — dois montantes DIN + travessa + junções

Data: 2026-09-11 · Diretório novo: `portico-montantes-20260911T063439Z/`
**Status: geometria verificada. NÃO é aprovação de fabricação.**
Nenhum `git add/commit/push/merge/revert`. Nada dos diretórios existentes foi sobrescrito.

```
gates geométricos   : 11/11 PASS
round-trip STEP+FCStd: 12/12 PASS
testes negativos     : 5/5 mutações detectadas
colisão máxima       : 0,000 mm³ (todos os pares)
```

---

## 1. Arquitetura construída

```
        TRAVESSA (trilho TS35 real, 600 mm, eixo X)
   ┌──────────────────────────────────────────────────────┐
   │        ┌──────────┐                  ┌──────────┐     │
   │        │ JUNÇÃO A │                  │ JUNÇÃO B │     │
   │        └────┬─────┘                  └────┬─────┘     │
   └─────────────┼─────────────────────────────┼───────────┘
                 │  ← montante DIN (450 mm, eixo Y)  →
            ┌────┴────┐                     ┌────┴────┐
            │  peça   │                     │  peça   │   ← peça oficial validada
            │ dupla   │                     │ dupla   │      (+ cópia transladada)
            └────┬────┘                     └────┬────┘
                 │ G-clamp                     │ G-clamp
```

- **Montantes**: o trilho TS35 real do fabricante (Winford, `dinr135-007.5.step`),
  **extrudado a partir da seção medida da face de topo** e com a **padronagem de
  ranhuras medida** repetida (passo 25 mm, obround 6,2 × 15,0 através da chapa de
  1,0 mm). Não é um cubo nem um bloco maciço.
- **Travessa**: o mesmo trilho, 600 mm, atravessando as duas junções.
- **Junção (peça nova, "luva de canto")**: um bloco com **duas canaletas fêmea do
  perfil**, ortogonais entre si:
  - canaleta vertical = montante; canaleta horizontal = travessa;
  - cada canaleta é o **prisma exato da mesma seção-fita** do trilho, então a peça
    fica cingida em X e Z (e no perfil) e **livre apenas no eixo** do trilho;
  - o vão interno do perfil é preenchido pela própria luva (núcleo), o que dá
    contato em toda a volta da fita e enrijece o canto.
- **Ajuste de altura**: a luva desliza no montante (±50 mm testados, colisão 0).
- **Ajuste de largura**: a travessa desliza através das duas luvas (±100 mm
  testados, colisão 0), com **sobras externas** de ~78 mm de cada lado.
- **Antirrotação**: **demonstrada**, não afirmada — rotação do montante em torno do
  próprio eixo gera colisão de 234,43 mm³ (1°), 466,75 mm³ (2°) e 1031,39 mm³ (5°);
  travessa idem (233,33 / 464,65 / 1028,96 mm³). A mesma rotação contra uma junção
  **sem** o furo da chaveta também colide (234,55 / 467,10 / 1035,17 mm³) → o bloqueio
  é da **canaleta perfilada**, não da chaveta.
- **Retenção positiva de altura**: **chaveta impressa** que entra na ranhura do
  trilho. Folga axial nominal **0,20 mm**; a 0,5 mm de deslocamento já há colisão de
  **1,86 mm³** (= 0,3 × 6,2 × 1,0 exato). É travamento por apoio, não por fricção.
  Quantiza a altura em degraus de 25 mm.
- **Travas candidatas (NÃO provadas)**: dois parafusos **M3** por luva (envelope
  cilíndrico Ø3,0 em furo Ø3,4), um prensando a parede do montante contra a canaleta
  e outro a da travessa. A ponta toca a face do trilho com **7,07 mm²** cada. Sem
  rosca modelada, sem torque, sem pré-carga, sem retenção do parafuso no furo.

## 2. Método: datums medidos, nunca varredura de translações

| datum | valor | como foi medido |
|---|---|---|
| eixo do montante (X) | −30,5 | centro do bbox em X do furo-perfil no bloco-soquete da peça |
| plano-base do trilho (Z) | 10,05 | centro do bbox em Z do furo (13,8) − centro do bbox da seção na altura (3,75) |
| fundo do soquete (Y) | 92,901999 | plano da face cega do soquete, lida na peça (não arredondada) |
| passe das ranhuras | 5,0 + 25 k | medido no corpo de prova de 75 mm do fabricante |
| face externa da parede do trilho | Z local 13,5 | deduzida da colisão medida da ponta do parafuso (7,069 = π·1,5²·1,0) |

Nada foi posicionado por busca de translação. A única família testada foi a das
**4 dobras do perfil em torno do próprio eixo** mais as duas direções de
comprimento — todas as hipóteses estão registradas em `probe4.json` e só uma
(`len_up_f0`, det = +1, sem espelhamento) fecha com colisão 0 e folga 0.

## 3. Fidelidade da seção (gate `section_fidelity`)

| | reconstruído da seção | STEP do fabricante |
|---|---|---|
| volume (75 mm) | **3178,358451 mm³** | **3178,358451 mm³** |
| bbox | [0, 0, −17,5, 75, 7,5, 17,5] | [0, 0, −17,5, 75, 7,5, 17,5] |
| ranhuras | 3 | 3 |
| sólidos / válido | 1 / sim | 1 / sim |

Δ volume = **0,000000000 mm³**. A seção tem área 45,768 mm², perímetro 300,99 mm,
20 arestas; é uma **fita aberta em "chapéu"** (chapa de 1,0–1,2 mm), com base de
23,4 mm, paredes e aba de 35 mm — por isso a canaleta fêmea tem de ser o prisma da
fita e não um rasgo retangular.

## 4. Medições por par (volume de interseção + área de contato de face)

O medidor foi calibrado antes de medir: dois cubos de 20 mm com face comum dão
**400,000 mm²** (toda em X) e 0,000 mm³; afastados 2 mm dão **0,000 mm²**
(`measurer_self_test.pass = true`). Contato é medido **face a face** com filtro AABB,
não por `common(sólido, sólido).Area`.

| par | tipo | interseção (mm³) | folga (mm) | área de contato (mm²) | por eixo |
|---|---|---|---|---|---|
| JuncaoA ↔ MontanteA | contato | 0,000 | 0,000 | **3760,778** | X 1450,181 · Z 2310,597 · **Y 0** |
| JuncaoA ↔ Travessa | contato | 0,000 | 0,000 | **3673,978** | Y 1450,181 · Z 2223,797 · **X 0** |
| JuncaoB ↔ MontanteB | contato | 0,000 | 0,000 | 3760,778 | idem |
| JuncaoB ↔ Travessa | contato | 0,000 | 0,000 | 3673,978 | idem |
| ChavetaA ↔ MontanteA | contato | 0,000 | 0,000 | **16,800** | X 16,800 (= 2 × 8,4 × 1,0) |
| ChavetaA ↔ JuncaoA | contato | 0,000 | 0,000 | **149,471** | X 67,200 · Z 82,271 |
| ParafusoTravaV_A ↔ MontanteA | contato | 0,000 | 0,000 | **7,069** | X 7,069 (= π·1,5²) |
| ParafusoTravaH_A ↔ Travessa | contato | 0,000 | 0,000 | **7,069** | Y 7,069 |
| **MontanteA ↔ Peça oficial** | contato | 0,000 | 0,000 | **45,768** | **Y 45,768** |
| Clamp ↔ Peça oficial | contato | 0,000 | 0,000 | 1340,268 | X 473,024 · Y 867,244 |
| ParafusoTravaV_A ↔ JuncaoA | folga | 0,000 | **0,200** | 0,000 | — |
| MontanteA ↔ Travessa | sem contato | 0,000 | 2,450 | 0,000 | — |
| JuncaoA ↔ Clamp | sem contato | 0,000 | 366,901 | 0,000 | — |
| JuncaoA ↔ Peça | sem contato | 0,000 | 326,500 | 0,000 | — |
| JuncaoA ↔ MontanteB | sem contato | 0,000 | 361,000 | 0,000 | — |
| (4 pares B espelhados) | — | 0,000 | idem | idem | idem |

Leituras que a tabela sustenta:
- **A canaleta prende transversalmente e solta axialmente**: em Juncao↔Montante a
  área em Y é **exatamente 0** — não há contato axial, é isso que permite o ajuste
  de altura. Em Juncao↔Travessa a área em X é **exatamente 0** — idem para a largura.
- **Montante ↔ peça**: o contato é **toda a face de topo do trilho** (45,768 mm² =
  a área da seção, toda em Y). O trilho **assenta de topo** no fundo do soquete da
  peça oficial — o "trilho encaixa 0,0000" do `peca-oficial-manifest.json` se
  reproduz, agora com área de face positiva e posição derivada de datum.
- Contatos nominais de folga zero (ver §6): a medição de área **só é possível nessa
  convenção** de projeto.

## 5. Testes negativos (mutações) — `negative-results.json`

| mutação | o que ela quebra | check que acusa | resultado medido |
|---|---|---|---|
| **N1** luva cortada em duas | peça única | `parts_single_valid_solid` | **3 sólidos** com `isValid = true` — a validade B-Rep sozinha **não vê** o defeito (o erro do R07) |
| **N2** rasgo retangular 36,5 × 8,5 no lugar da canaleta perfilada | antirrotação | `rotation_blocked` | rotação a 1,0° → **colisão 0,000** (a 2° ainda dá 7,25) → o gate cai |
| **N3** chaveta 2 mm mais curta (12,6) | retenção positiva | `key_positive_stop` | deslocamento 0,5 mm → **0,000 mm³** com a chaveta curta contra **1,860 mm³** com a chaveta de projeto |
| **N4** chaveta 0,6 mm mais estreita | contato de face | `face_contact_on_declared_pairs` | contato na ranhura **0,000 mm²** contra **16,800 mm²** na de projeto |
| **N5** luva montada 12,5 mm fora do passe (entre duas ranhuras) | interferência | `zero_interference` | a chaveta invade a chapa do trilho em **66,837 mm³** |

`all_mutations_caught = true`. Cada mutação nomeia o gate que a pega — e o gate
correspondente é o mesmo que roda no build.

## 6. Round-trip independente — `verify-results.json`

Processo novo, sem nada em memória:

| check | resultado |
|---|---|
| STEP: nº de sólidos (15) | PASS |
| STEP: volume total 236 396,791 mm³ | PASS |
| STEP: bbox idêntica à do build | PASS |
| STEP: válido | PASS |
| STEP: volumes por corpo (ordem livre) iguais | PASS |
| FCStd: conjunto de 15 nomes idêntico | PASS |
| FCStd: volume por objeto igual | PASS |
| FCStd: 1 sólido por objeto | PASS |
| FCStd: todos válidos | PASS |
| FCStd: bbox idêntica | PASS |
| Interferência re-medida nos corpos reabertos | PASS (0,000) |

## 7. GUI real

Autorizado porque todos os gates geométricos passaram.

```
shots/iso.png         28 713 B   vista axonométrica (modelo visível)
shots/lado.png        28 687 B   vista lateral
shots/frente.png      15 717 B   vista frontal
shots/topo.png         9 159 B   planta — SAIU EM BRANCO (ver §8.9)
shots/janela-real.png 726 467 B  captura do desktop real (grim)
```

`gui-shots.json` registra: `GuiUp = true`, documento `portico_montantes` com 15
objetos, título da janela real **"[*] portico-montantes - FreeCAD 1.1.1"**, janela
1500 × 950 visível. A captura do desktop real mostra a janela do FreeCAD com a
árvore (MontanteA/B, Travessa, JuncaoA/B, Chavetas, Clamp, Parafusos) e o pórtico
desenhado no viewport. O processo da GUI foi encerrado ao fim da captura.

## 8. O que falhou nesta rodada (registro honesto)

1. **1ª passada da chaveta com o obround transposto** (8,8 mm no eixo X em vez de
   6,2): colisão de **16,12 mm³** com o trilho. Corrigido.
2. **Pontas dos parafusos 1,0 mm dentro da parede do trilho** (7,069 mm³ cada).
   Diagnóstico: a face **externa** da parede do trilho está em **Z local 13,5**, não
   em 12,5 (deduzido do valor exato da colisão). Pontas recuadas para a face medida.
3. **Teste de deslizamento errado**: media a travessa estacionária enquanto a luva
   subia, e acusava colisão de ~790 mm³. O movimento é a luva **com** a travessa;
   separado em dois testes corretos (luva↔montante; travessa↔luvas; ambos juntos).
4. **Datums arredondados a 3 decimais** davam folga residual de 1e-6 mm e **área de
   contato 0** no soquete. Corrigido lendo o plano exato da face na peça
   (Y = 92,901999): o contato de topo passou a 45,768 mm².
5. **`Part.export`/`Import` e documentos**: `App.newDocument` pode devolver `None` e
   `App.getDocument` levanta exceção em headless; `FreeCADGui.openDocument` não
   existe. Resolvido com `Part.read` para o STEP e `App.openDocument` para o FCStd.
6. **`removeSplitter` não existe em `Part.Compound`** — as mutações precisaram de um
   helper que só achata quando o kernel devolveu um sólido.
7. **Tolerância de resíduo**: contatos nominais de folga zero produzem resíduo de
   booleano (5e-06 mm³) ao encaixar superfícies cilíndricas coincidentes. Em vez de
   esconder, a chaveta ganhou 0,20 mm de folga nominal por ponta (que é folga de
   impressão real) → resíduo **0,000** e o gate continua a pegar mm³ (N3/N5).

## 9. PREMISSAS (assunções explícitas — não são medições)

- Alturas e vão do contrato: montante **450 mm**, travessa **600 mm**, vão entre
  montantes **400 mm** (do `contract.json` anterior). Nada disso foi imposto pela
  esteira, que não foi medida.
- **Altura da junção: 362,5 mm** acima do fundo do soquete, e não os 350 mm da
  premissa: a chaveta só engata no passe de 25 mm, e o passe mais próximo é 362,5.
- **Segunda montagem = translação rígida +400 mm em X** (peça e clamp incluídos).
  A orientação dela em relação aos **dois lados reais** da esteira **não foi
  validada**. Nenhuma reflexão (peça espelhada) foi usada.
- **Seção real da esteira: NUNCA medida.** O contato peça↔clamp é um cupom
  dimensional herdado, não a máquina.
- **Folga de impressão não modelada**: cada canaleta é a fêmea exata do trilho
  (folga zero nominal). Na impressão real são precisos ~0,2–0,3 mm por lado, e isso
  **converte os contatos nominais desta rodada em ajustes com folga**.
- **Parafusos são envelopes** Ø3,0 sem rosca; sem torque, sem pré-carga, sem
  retenção do parafuso no furo.
- **Caminho de carga vertical**: a carga chega ao montante apenas pela chaveta
  apoiada na ponta da ranhura. Essa chapa de **1,0 mm em cisalhamento não foi
  dimensionada**.

## 10. ABERTO (não validado — nada disso pode ser afirmado)

1. **Esteira não medida (G0)**: espessura/geometria da lateral fixa, acesso ao
   parafuso de aperto, envelope móvel. O vão de 10 mm do clamp **não** é capacidade.
2. **Ajuste e retenção físicos**: nada foi ensaiado; só há geometria nominal.
3. **Rigidez, cargas, vibração, fadiga, repetibilidade, deslizamento por vibração**:
   nada calculado. O trilho em balanço e o torque no grip continuam abertos.
4. **Cisalhamento da chaveta** (1,0 mm de chapa) — candidata, não dimensionada.
5. **Trava por parafuso** (fricção) — não provada; a retenção provada é a chaveta.
6. **Montagem real**: verificar acesso para introduzir a chaveta por baixo e para
   passar o montante pelo soquete da peça (entra pela ponta do trilho).
7. **Altura contínua**: com a chaveta montada o ajuste é em degraus de 25 mm.
8. **Volume de impressão da luva**: 42,6 cm³ (42574 → 42637 mm³). Grande; não houve
   verificação de caber na mesa nem de tempo de impressão.
9. **Vista de planta** (`topo.png`) renderizou em branco — artefato de render/câmera,
   não foi investigado a fundo; as demais vistas e a captura da janela real mostram a
   composição.
10. **Cabeçote/acesso de ferramenta** dos parafusos de trava não modelado.
11. **Câmeras, Raspberry Pi, cabos, trigger**: fora de escopo por decisão de sequência.

## 11. Arquivos e reprodução

```
run.sh                     executa qualquer script com o freecadcmd existente (sem instalar nada)
lib_geo.py                 medidores (stats, overlap, gap, contact_area + autoteste), matrizes, trilho
build_portico.py           gera a composição, roda os 11 gates e exporta STEP + FCStd
verify_portico.py          processo NOVO: reabre STEP e FCStd e confere volume/bbox/sólidos
negative_tests.py          as 5 mutações
gui_shots.py               render das vistas + captura da janela real
probe1..probe4.py/.json    descoberta e registro dos datums (inclui as hipóteses descartadas)
inputs/                    STEPs e BREP de origem + SHA-256
exports/portico-montantes.step   (7 341 973 B, 141 584 entidades)
exports/portico-montantes.FCStd  (1 706 494 B, 15 objetos)
build-measurements.json    todas as medições do build
verify-results.json        round-trip
negative-results.json      mutações
gui-shots.json             estado da GUI e capturas
SHA256SUMS.json            integridade de todos os artefatos
```

Reprodução: `./run.sh build_portico.py && ./run.sh verify_portico.py && ./run.sh negative_tests.py`
(≈ 25 s + 20 s + 30 s). Não instalar nada. Não abrir a GUI se os gates falharem.
