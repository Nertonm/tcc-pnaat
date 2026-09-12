---
tags: [type/report, theme/pnaat, theme/tcc]
aliases: []
lead: "Revisão criteriosa da CHECKLIST-ADVERSARIAL v1 (40 achados): cada item reverificado no FreeCAD headless 1.1.1. 4 achados refutados, 12 corrigidos em número/alvo, 9 achados novos da rodada de correção reverificados (4 deles com erro de método) e 9 lacunas que nenhuma das duas rodadas abordou."
created: 2026-09-11
modified: 2026-09-11
review_status: revisada
---

# Checklist adversarial v2 — sessão CAD PNAAT (revisão da v1)

Revisão da `CHECKLIST-ADVERSARIAL-20260911.md` (v1). Fonte: 6 classes, ~40 achados.
Workspace auditado: `/home/<usuario>/tcc-pnaat/github/cad-workspace` no <host>.
**Nada foi alterado no workspace. Esta v2 vive em `/tmp/CHECKLIST-v2.md`.**

## 0. Como esta v2 foi feita (e o que ela NÃO cobre)

- Cada item da v1 foi reaberto: arquivo citado lido, número reconferido, e — quando
  havia número — remedido no **FreeCAD 1.1.1 headless**
  (`/home/<usuario>/.cache/qwen-mm-plugins/apps/freecad-1.1.1/squashfs-root/usr/bin/freecadcmd`,
  via `runuser -u <usuario> --`). Scripts de verificação: `/tmp/v2_*.py` no <host>
  (listados no Anexo A, com os valores que cada um produziu).
- Também foram lidos os artefatos brutos das auditorias em `/tmp` do <host>
  (`/tmp/k1c-audit/`, `/tmp/enc_work/`, `/tmp/pnaat_probe*.py`, `/tmp/r90.py`,
  `/tmp/rf1.py`, `/tmp/c90.py`, `/tmp/va1.log`, …) — inclusive os scripts da
  **rodada de correção**, para verificar os achados novos no método que os gerou.
- **O que esta v2 NÃO é:** não conserta o CAD, não imprime, não emite laudo de
  aprovação, não mede a esteira, não julga mérito do TCC. Não foi executado nenhum
  comando de escrita no workspace/git.

### Legenda de status (por item da v1)

| status | significa |
|---|---|
| **CONFIRMADO** | reproduzi o número/fato de forma independente; o item se sustenta como está |
| **PARCIAL** | o fundo do item se sustenta, mas um número, alvo ou inferência está errado |
| **REFUTADO** | o item é falso, ou é falso como está formulado (a substituição correta vai no campo) |
| **NÃO VERIFICÁVEL** | não há artefato no workspace que permita decidir; digo o que falta |

### Diff resumido

| movimento | itens |
|---|---|
| **REFUTADOS / substituídos** (4) | **B4** (2 grips impossíveis — falso), **A1a** (fator π/2 — é π), **C1b** (`peça oficial 0,01–0,02 mm/lado` — mede 0,180), **D4b** (`FCStd modificados in place com git status M` — não reproduz) |
| **REBAIXADOS a PARCIAL** (9) | A1b, A5, A7, A8b, B3, B6, B13, C1c, C5, D5, D7, D8 → (12 itens com número/inferência corrigidos) |
| **SOBEM** (severidade mantida P1, agora com prova nova) | C1a (folga zero da luva, medida), B10/B12 (o caminho de carga tem alvo agora), G1 (a "peça verificada" do adv4 é sintética) |
| **NOVOS** (esta rodada) | **G1–G7** (achados da rodada de correção, reverificados) + **H1–H9** (lacunas que nenhuma das duas rodadas abordou) |
| **integridade da v1** | A2, A3, A4, A6, A8a, B1, B2, B5, B7–B12, C2–C4, C6–C10, D1–D3, D6, D9, E1–E12, F1–F6: **CONFIRMADOS** como estão (número reconferido) |

### Os 5 erros mais graves da v1 (para não se repetirem)

1. **C1 atira no alvo errado.** A canaleta da peça/encaixe **já tem 0,180 mm/lado**
   (35,360 mm para trilho de 35,00) — o mesmo valor do bracket do vendor. A folga
   **zero** é exclusiva das **canaletas da luva (junções)**. Quem "não entra no
   trilho" é a luva, não o encaixe. (v1 dizia `peça oficial: 0,01–0,02`.)
2. **B4 é falso.** O grip nos dois lados é rotação rígida, o autor do bracket diz
   que a variante screw-through "can be printed twice", e o encaixe é simétrico.
3. **G1 (novo).** A bateria "REFERÊNCIA PASSA + 4/4 mutações" do `adv4.py` mediu uma
   **peça sintética de caixas** (12 541,0 mm³) e um **encaixe sintético** (11 916,6 mm³)
   que **não são** nem a peça adversarial (11 522,2), nem a oficial (22 762,885).
4. **G2 (novo).** O "vão de 34,65 mm" da rodada de correção é um par de **chanfros de
   entrada a 45°**, não o vão do trilho. O vão real (faces normais ±Y, 7,7 mm² cada,
   na zona de inserção de 5,5 mm) é **35,360 mm** — a leitura da auditoria 3 estava
   certa e a "correção" estava errada.
5. **A1 mede o viés errado.** O medidor por penetração devolve **área projetada**;
   no caso curvo medido o fator é **π = 3,14×**, não π/2 = 1,57×. E ele também
   devolve **0** quando a superfície casante é cilíndrica e a penetração é axial.

## Veredito v2

**O pórtico continua não pronto para imprimir.** A contagem de bloqueadores
**muda de 21 para 22** — e a composição muda: **cai** o bloqueador de arquitetura
"2 grips impossíveis" (falso); **entram** um bloqueador de método (a bateria
adversarial validou uma peça sintética, G1) e um de fabricação (o encaixe
bracket×trilho nunca é resolvido: nenhuma posição testada assenta, G4).
O resto do veredito da v1 se sustenta: a peça que foi verificada **não é** a peça
oficial; a folga das canaletas da luva é **zero**; e o caminho de carga nunca foi
calculado.

Números que sobrevivem intactos (todos remedidos):
`22 762,8846` (peça oficial) · `11 522,1885` (peça adversarial) · `11 490,6713`
(encaixe separado) · `0,0434 mm³` (mount v6 × CM3) · `35,360 mm` (canaleta do
vendor **e** da peça oficial) · `93,536282 mm` (perímetro da seção) · `196,0 cm³`
(volume impresso) · `234,43 / 466,75 / 1031,39 mm³` (antirrotação a 1/2/5°) ·
`16,8 mm²` (apoio da chaveta) · `7,069 mm²` (ponta do parafuso de trava).

---

## Classe A — Metodologia de medição

| # | item v1 | status | verificação independente (minha) | o que muda na v2 |
|---|---|---|---|---|
| A1a | medidor por penetração mede **área projetada**; erro sistemático **π/2 ≈ 1,57×** em superfícies curvas (Ø20 em furo casante: real 1256,64, medidor 400,000) | **PARCIAL** | Reproduzido: eixo Ø20×20 em furo casante, penetração **radial** → medidor **400,0000 mm²**; área lateral real **1256,6371 mm²**; razão **3,14159 = π**. O fator **não é π/2** (`/tmp/v2_metod.py`) | o fundo está certo (área projetada, e o mesmo 400,000), mas **o fator é π = 3,14×**, não 1,57×. Corrigir o texto |
| A1b | dependente do passo: 354,51 (0,02) → 298,05 (0,005) → **207 (0,001)** | **PARCIAL** | Reproduzido no par real encaixe×peça: 0,02 → **354,5095** · 0,01 → 335,4778 · 0,005 → **298,0547** · 0,002 → 186,2970 · 0,001 → **0,2124** · 0,0005 → 0,0000. O "207 em 0,001" **não se reproduz** | a dependência do passo é real e **pior** que o declarado (colapsa para ≈0,2 em 0,001). Substituir "207" por "≈0,21" |
| A1c | (não existia) | **NOVO** | Penetração **axial** num furo casante cilíndrico devolve **0,0000** (booleano degenerado), não 400 nem 314 | acrescentar: além do viés, o medidor é **cego na direção axial** de superfícies casantes cilíndricas |
| A2 | o diagnóstico central era falso: `face.common` **não** é cego a faces coplanares opostas (calibração 400,000); a causa era folga de 1,001 µm | **CONFIRMADO** | Três casos medidos (`/tmp/v2_a2.py`): cubos com face comum → `face.common` devolve **400,0000** (type Shell); faces **coincidentes** → **400,0000**; faces a **1,001 µm** → **0,000000** | está certo como está. É a autocorreção mais importante da v1 — manter em destaque |
| A3 | a peça verificada não é a oficial: 11 522,188 / DOS-JEITOS 11 740 / oficial 22 762,885, bbox Y 32..73 vs 32..107,4 | **CONFIRMADO** | `peca-2-plataformas.step` = **11 522,1885 mm³**, bbox X −72..−6 **Y 32..73,001** Z 0..20 · `peca-dupla-plataformas.step` = **22 762,8846 mm³**, bbox **Y 32..107,402** · `encaixe-separado.step` = 11 490,6713 | está certo. Acrescentar: o STL `peca-2-plataformas.stl` mede 11 522,2634 (bate) e o `encaixe-separado.stl` 11 490,7202 |
| A4 | `0,0434 mm³` do mount v6 **sem lastro**: não existe em JSON/log/script, só no texto do R05 | **CONFIRMADO** | `grep -rn "0.0434"` no workspace: 4 ocorrências, **todas .md** (`reports/R05-CAMERA-MOUNT-DIN.md:15`, `LAUDO-camera-mount-din-v6.md:20`, `REVISAO-MODELOS`, `INDICE`). `validation-v6-core.json` contém só `collisions: []`, `invalid: []`, `pass: true` | está certo. Reforço: o único JSON de validação do v6 **não tem nenhuma área/volume** — o número é uma afirmação de prosa |
| A5 | `insertion_depth: 5.5` é literal hardcoded em `mechanism_probe.py:7` | **PARCIAL** | Confirmado o literal `'insertion_depth':5.5`, mas está na **linha 8**, não 7 (`sed -n 1,20p`). O arquivo também grava `'normal_dot':1` como literal | corrigir a linha (8). O fundo (o JSON não é evidência de medição do encaixe) está certo |
| A6 | "colisão 0 em todos os pares": o build testou **22 de C(15,2)=105**; `base-v2-checks.json` registrou **16 de 45** | **CONFIRMADO** | `build-measurements.json` → `pairs` tem exatamente **22** chaves; o pórtico tem 15 objetos ⇒ C(15,2)=105. `base-v2-checks.json` tem **10** peças ⇒ C(10,2)=45 e **16** pares gravados | está certo. Acrescentar que `base-checks.json` (v1) registrou `base_collision_pass: **false**` com `ClampFunctionalSource__SpineCap = 0,7249 mm³` — a colisão não-zero da tentativa anterior ficou preservada no JSON e a v1 não a citou |
| A7 | "seção tem perímetro 300,99 mm" — o real é 93,536282 | **PARCIAL** | Confirmado que `portico-montantes/RELATORIO.md:86` diz 300,99. O perímetro real da face de seção do trilho é **93,536280** (1 wire, 20 edges; reconferido no STEP do vendor), área **45,7681**; `build-measurements.json` grava 93,536282. Varri **todas** as faces do pórtico procurando perímetro 295–310 → **nenhuma** | 93,536 está certo; **300,99 é órfão** (sem fonte em nenhum artefato). Trocar "o real é" por "o real é 93,536282 e 300,99 não tem origem rastreável" |
| A8a | `Shells[0]` **sem guarda** em 4 scripts; o único erro real é o Dyalec (`topside` tem 3 cascas e a `[0]` tem volume 0,000000) | **CONFIRMADO** | 11 ocorrências de `Shells[0]` em 7 arquivos. **Com guarda** (`assert len(...)==1`): `freecad_r05_v5.py`, `freecad_r05_v6_build.py`, `freecad_r05_optical_bootstrap.py`. **Sem guarda (4)**: `mechanism_probe.py`, `probe_geom.py`, `auditoria-r07/build.py`, `auditoria-r07/inputs/r07-source.py` (2×). Dyalec `raspberry_pi_5_din_topside.stl`: 3 componentes, `Shells[0]` = 6 faces, **vol 0,0000**, e **não é a maior** (a maior é `Shells[1]`, 15 959,3074) | está certo, inclusive o alvo. Explicitar que só 3 dos 7 arquivos têm a guarda |
| A8b | Nenhum script do workspace usa esses STLs ⇒ a escolha errada foi manual/invisível | **PARCIAL** | Os STLs da case Dyalec e o `clamp_frame.stl` **não são usados** por script nenhum (só mencionados). Mas `G-clamp_Tripod.stl` **é usado**: `auditoria-r07/build.py:29` o lê, e o `G-clamp_Tripod-component0.stl.brep` derivado dele é lido por `build_base.py`, `mechanism_probe.py`, `adv4.py` | precisar: a afirmação vale para os STLs do Dyalec e do `clamp_frame`, **não** para o G-clamp |

---

## Classe B — Arquitetura e física

| # | item v1 | status | verificação independente | o que muda na v2 |
|---|---|---|---|---|
| B1 | **Sem retenção anti-queda**: `grip-extensivel.md:82-83` exige cabo/cordão; ausente no CAD e no plano | **CONFIRMADO** | `docs/design/grip-extensivel.md` linhas **82–83**: "Segurança: o corpo impresso não é o único elemento contra queda do pórtico; prever cabo/cordão de retenção" (numeração conferida com `sed -n 78,90p`). Nem `PLANO-IMPRESSAO-K1C.md` nem `portico-montantes`/`composicao-completa` mencionam retenção | está certo. O grip por atrito de mordente de 10 mm + parafuso impresso continua sendo o ponto frágil |
| B2 | **Trava do mount e da case não existe**: "a modelar" (`R05-CAMERA-MOUNT-DIN.md:57`); viola D-17 e RNF-20 | **CONFIRMADO** | `R05-CAMERA-MOUNT-DIN.md` linha **57**: "Trava anti-deriva **impressa** (a modelar)". D-17 (`DECISIONS.md`, seção "D-17: Grip de câmeras"): "os ajustes devem possuir mecanismo de travamento". RNF-20 = "Estabilidade mecânica sem recalibração indevida após movimentação prevista" (`docs/requisitos.md:64`) | está certo |
| B3 | antirrotação demonstrada em **um só nível** (234,43/466,75/1031,39 na junção); no grip só afirmada; **e** o clamp medido tem **um** furo de tripé, não dois | **PARCIAL** | Os três números da junção se reproduzem exatos em `build-measurements.json → kinematics.upright_rot_{1,2,5}.0deg` (234,432879 / 466,747777 / 1031,388867) — **CONFIRMADO**. O "um furo de tripé": o `G-clamp_Tripod-component0.stl.brep` usado pelo pipeline tem **zero faces cilíndricas** (3 218 facetas → todas planas), então **não é possível contar furos por faces cilíndricas**; a única evidência documental de furo é `/tmp/montar2.py:15` ("mordente 10mm; furo 6.45 eixo Y em (X−30.5, Y67, Z10)") — um furo. Nada no workspace mede um segundo furo (−X) que o `RELATORIO-DOIS-JEITOS` pressupõe | separar as duas metades. A liberdade de rotação em torno do parafuso é **inferida**, não medida; e o "dois parafusos em eixos perpendiculares (furo +Y e furo −X do clamp)" do relatório do peça **não tem lastro geométrico** |
| B4 | **2 grips em lados opostos é fisicamente impossível como está** | **REFUTADO** | (a) o `G-clamp` é assimétrico em X (12,02%), mas girar 180° em Z é transformação **rígida** da mesma peça física — a boca vai de −X para +X (é o que os scripts `r90/rf1` já fazem); (b) o PDF do autor (`references/vendor/din-rail-parts/m6-bracket/573570-…pdf`, texto lido por `pdftotext`) diz literalmente: *"The keyhole version comes with a left and right side, while the screw-through **can be printed twice**"*; (c) o encaixe é simétrico em X. Além disso `build-measurements.json → premises.second_grip` já declara a segunda montagem como **translação rígida de +400 mm em X** | **Item cai.** Substituir por: **"a montagem nunca foi testada com o grip rotacionado 180° em Z"** — a premissa gravada diz que a orientação do segundo grip em relação aos dois lados reais **não é validada** (a esteira nunca foi medida). O que falta é o teste do espelhamento, não a viabilidade |
| B5 | **Largura (travessa) sem trava positiva nem referência de retorno**; D-17 | **CONFIRMADO** | `build-measurements.json`: a travessa desliza com `crossbar_shift_X_*` em 0,000 (5 posições), e as únicas travas são `ParafusoTravaH_{A,B}` = envelopes cilíndricos Ø3,0 em furo Ø3,4 com `premises.fasteners = "no thread, no torque, no preload and no retention"`. A `Chaveta` (retenção positiva) só existe na vertical | está certo. A altura tem chaveta quantizada em degraus de 25 mm; a largura não tem nada equivalente e o retorno não é referenciado |
| B6 | **FPC 200 mm impossível no layout montado**; Pi no montante B, câmera no A, vão 400 mm; o único cálculo é ~187 mm de eixo; cabo Standard–**Mini** não documentado; G2 FAIL | **PARCIAL** | `R05-OPTICAL-BLOCK.md` mede **caminhos curvos** (`Part.Wire`, retas+arcos): C_TOP **166,5089 mm** (sobra 22,4911 em 199); C_SIDE **115,5665 mm** (sobra 73,4335); G2 = **FAIL** por falta de raio mínimo do fornecedor; o desenho local é **Standard–Standard** e não qualifica a terminação mini — tudo **CONFIRMADO**. Mas **"~187 mm" não existe** em nenhum artefato (grep em `docs/`, `reports/`, `data/concepts/`): o `R05-CAMERA-DISTANCE-ANALYSIS` dá 163 mm (Standard 2L, E=45°) e a spec congela **~171 mm** de distância de trabalho | trocar "~187 mm" pela fonte real (163 mm de eixo / 171 mm de trabalho) e dizer que **a montagem do pórtico não usa nenhum dos dois caminhos medidos**: `composicao-completa` posiciona o mount à mão e não traça rota |
| B7 | **Iluminação e trigger não existem no CAD do pórtico** (15 corpos, sem backlight/polarizador/fundo/retrorrefletivo; HW-04, RF-30, RNF-21, D-18) | **CONFIRMADO** | `verify-results.json` → 15 objetos (`ChavetaA/B`, `ClampFunctionalSource/B`, `JuncaoA/B`, `MontanteA/B`, `ParafusoTrava*`, `PecaDuplaPlataformas*`, `Travessa`) — nenhum objeto de luz, difusor, fundo ou trigger. HW-04 exige "2× LEDs RGB… lente difusora… fita retrorrefletiva 3M… E18-D80NK inclinado 10°–15° mirando no anteparo" | está certo |
| B8 | **Ângulo fixo de 49° sem pivot**; a spec congela exige "ajuste fino com trava"; pior caso 2L pede 49° (Wide) / **69°** (Standard) | **PARCIAL** | O conflito é **CONFIRMADO**: `data/concepts/camera-mount-spec-v1.md` tem "ajuste fino de ângulo \| **pivot com trava** (do doc grip-extensivel)" e `R05-CAMERA-MOUNT-DIN.md:58` diz "Ângulo **fixo em 49°** (sem pivot — decisão do usuário)". Os **69°** não existem em lugar nenhum (grep em `reports/`, `data/concepts/`) | manter o conflito; remover o 69° (ou citar a fonte). O 49° é o pior caso 2L com CM3 **Wide** |
| B9 | mount validado para sensor provavelmente errado: v6 = CM3 **Wide** (rolling shutter), a spec de aquisição pede **mono + global shutter** | **CONFIRMADO** | `docs/design/preprocessamento-ideal-pet.md:13` → "Sensor \| **mono + global shutter** \| mono evita CFA/demosaic e aliasing na borda; global evita skew em esteira"; `deep-research-preprocessamento-pet-resultado.md:19` → "**global shutter obrigatório**". O mount v6 é o berço da **CM3 Wide** | está certo. Nota de precisão: isso é conflito **doc de design × CAD**, não requisito numerado (HW-01..HW-06 não citam sensor) |
| B10 | **Caminho de carga não verificado**: sem massa/CG, sem M=F·e; o peso superior retido só por chaveta impressa apoiada na borda de **1,0 mm** = **16,8 mm²** sob carga permanente (fluência de PETG) | **CONFIRMADO** | `build-measurements.json → premises.load_path`: "a carga vertical chega ao montante só pela chaveta apoiada na ponta de uma ranhura; **essa chapa de 1,0 mm em cisalhamento NÃO é dimensionada aqui**". `pairs.ChavetaA__MontanteA.contact_area = **16,8 mm²**` (toda em X). `PLANO-IMPRESSAO-K1C.md` D2/D3/D4 marcados ✗ ABERTO | está certo. A chaveta é **o único** caminho vertical: não há segundo apoio |
| B11 | folga 0,2–0,3 mm/lado ⇒ jogo 0,65–0,98° ⇒ **2,3–3,4 mm** a 200 mm e **5,1–7,7 mm** a 450 mm | **CONFIRMADO** | Trigonometria reconferida com engate **L=35 mm** (a largura do trilho, implícita no item): 0,2 mm → 0,65° → 2,29 mm / 5,14 mm; 0,3 mm → 0,98° → 3,43 mm / 7,71 mm. Os três pares batem | está certo — mas com L=35 mm, que **não está declarado** no item. Declarar L (ou refazer para o engate real de cada canaleta, que não é o mesmo) |
| B12 | "chaveta de 1 mm em cisalhamento" mal descrito: a chaveta tem **5,0 mm**; os 1,0 mm são a chapa do trilho; cisalhamento real 31 mm², apoio 16,8 mm² | **CONFIRMADO** | `ChavetaA` bbox = 6,2 × 14,6 × **5,0** mm (volume 411,354); seção transversal 6,2 × 5,0 = **31 mm²**; apoio medido = **16,8 mm²** = 2 × 8,4 × 1,0. Nada dimensionado | está certo. E o texto do `PLANO-IMPRESSAO-K1C.md` (D1 e o inventário) **ainda diz "1 mm de espessura" / "1 mm em cisalhamento"** — o erro está vivo no plano, não só na v1 |
| B13 | dois artefatos com o mesmo nome: `clamp_frame.stl` (61,0 × 35,0 × 20,0, manifold) × `G-clamp_Tripod.stl` (71,0 × 35,0 × 20,0, 3 218 facetas); o plano credita um, o CAD usa outro, **nenhuma comparação existe** | **PARCIAL** | Medido: `clamp_frame.stl` = 39 896 facetas, **1 componente, fechada**, 61,0 × 35,0 × 20,0; **existe também** `clamp_frame_long.stl` = 39 894 facetas, fechada, **71,0 × 35,0 × 20,0** — ou seja, o ZIP traz o par 61/71, não só o 61. `G-clamp_Tripod.stl` = 3 218 facetas, **2 componentes, NÃO fechada**, 71,0 × 35,0 × 20,0 (confere com `g-clamp-tripod/PROVENANCE.md`) | o conflito real **não é comprimento**, é **origem e solidez**: o CAD usa a malha do vendor (**aberta, 2 componentes**) e não a `clamp_frame_long.stl` do joehann (**fechada**), que está no mesmo ZIP. Corrigir o texto: a comparação que falta é de **manifold e origem**, e o par certo é `clamp_frame_long.stl` |
| B14 | docs/backlog dizem "2 câmeras"; o BRIEFING mais recente diz **3**; não há documento normativo | **CONFIRMADO** | `docs/design/matriz-referencias-decisoes.md:32` → "**2 câmeras obtusas (vigente)** × reports CAD 3CAM · manter **2**; 3ª (topo) só se a tampa não separar no gate". `stage0-…/BRIEFING.md` → "CM3 Wide topo vertical… CM3 Wide lateral A… ESP-CAM lateral B oposta" = **3**. E os **requisitos numerados** também dizem 3: RF-01 ("as três vistas"), RF-01.2, RF-05, D-04 (vista superior + duas laterais) | está certo, e é pior: o conflito é **requisito numerado (3) × doc de design (2)**, não "docs/backlog × BRIEFING". Nada em `docs/backlog/` decide — o único arquivo lá é um README |

---

## Classe C — Fabricabilidade (a chapa única)

| # | item v1 | status | verificação independente | o que muda na v2 |
|---|---|---|---|---|
| C1a | **Luva: folga 0,000 mm/lado** (deslocar 0,002 mm já interfere 1,19 mm³) | **CONFIRMADO** (número corrigido) | Luva × montante no `portico-montantes.FCStd`: deslocar **0,0005 mm em Z → 0,689457 mm³**; 0,001 → 1,378919; **0,002 → 2,757797**; 0,005 → 6,894493. Em X, 0,002 mm → **29,646040 mm³**. Os deslocamentos anteriores são lineares (fração da face de 1 378,9 mm²) | a folga zero é fato medido. O "1,19 mm³ a 0,002 mm" **não se reproduz** (2,76 em Z; 29,6 em X): o número depende do eixo. Trocar por "0,5 µm já colide 0,69 mm³" |
| C1b | **Peça oficial: 0,01–0,02 mm/lado** de folga | **REFUTADO** | Todos os pares de planos opostos da peça oficial entre 33 e 37,5 mm: **33,310000** (−0,845/lado) · **34,648232** (−0,176/lado, par de **chanfros 45°**) · **35,360000** (+0,180/lado) · 36,352766 · 36,950000. O par de 35,36 são duas faces **nx=±1, 7,700 mm² cada, em X = −48,18 e −12,82, ambas em Y 92,90..98,40 (a zona de inserção de 5,5 mm)** | o número "0,01–0,02" não existe em nenhum par da peça. A **canaleta que recebe o trilho tem 35,360 mm = 0,180 mm/lado** |
| C1c | **O bracket do vendor prova o certo** (35,36 para 35,00 = 0,18/lado) e **"déficit de 0,18–0,30 mm/lado ⇒ a peça não entra no trilho"** | **CONFIRMADO** (o bracket) / **PARCIAL** (o alvo) | No STL do vendor, o único par de faces normais ±Y com 35,36 são as duas faces de **7,700 mm²** (5,5 × 1,4) em Y = ±17,68, Z 6,30..7,70 — exatamente a "zona de 5,5 mm" que o PDF do autor descreve. E a peça oficial tem o **mesmo** par (mesma área, mesmo 35,360, mesma zona Y 92,90..98,40) | dois ajustes: (1) o alvo do déficit são as **canaletas da luva** (zero), **não** o soquete da peça — que **já tem** 0,180/lado, herdado do bracket do vendor; (2) "a peça não entra no trilho de aço" vale para **luva/montante/travessa**, não para o encaixe |
| C2 | a Fase 1 do plano é inexequível: nenhum arquivo com folga/clearance/cupom existe | **CONFIRMADO** | `find` por `*folga*`, `*clearance*`, `*cupom*`, `*coupon*` no workspace (fora `.venv`) → **0 resultados** | está certo |
| C3 | a folga não pode ser calibrada sem o trilho — §2 lista os trilhos como ainda **a comprar** | **CONFIRMADO** | `PLANO-IMPRESSAO-K1C.md` §2 "O que é COMPRADO (não imprime)": 2× trilho TS35 450 mm + 1× 600 mm, custo "BLOCKED"; §3 A3 "o trilho comprado tem tolerância de laminação — medir o trilho real antes de fechar a folga" | está certo |
| C4 | zero orientação de impressão; a luva tem duas pontes de 23,4 mm (1 006,20 mm² cada) sobre vão de 1,0 mm; girando para +X cai para 658,05 mm² (4,10%) | **CONFIRMADO** | `/tmp/k1c-audit/overhang.json` → `JuncaoA`: +Z 4 327,049 mm² (26,96%), −Z 4 497,952 (28,02%), +X 1 706,629 (10,63%). `/tmp/k1c-audit/ov2.txt:2` → **"+X true_overhang 658,05 mm² (4,10%)"**; `ov2.txt:47,48,55` → faces **1 006,20 mm² com bbox 43,00 × 23,40** (a ponte de 23,4 mm) | está certo. Ressalva: 658,05 vem do overhang **verdadeiro** (faces horizontais para baixo), enquanto o 1 006,20 é a área da face; a razão 4,10% **é** reproduzida no artefato |
| C5 | o conjunto do clamp é **mutuamente exclusivo**: parafuso impresso Ø12,00 contra furo Ø6,45 (não passa); o mesmo plano lista 4× 1/4"-20; `G-clamp_Tripod.stl` é non-manifold; há 2 variantes de sapata e o plano nomeia só a justa | **PARCIAL** | Confirmado: `screw_and_knurled_knobHD.stl` = 40 878 facetas, 19,8 × 19,8 × 71,3; perfil radial por fatia → 0–30% do eixo **D 19,80** (o manípulo), **35–85% D 12,00** (o trecho roscado), 90–95% D 8,00, ponta D 0,36 → **a rosca é Ø12,00**. Os furos que o CAD corta são **Ø6,35** (`Part.makeCylinder(3.175,…)` em `build_base.py`) e o "6,45" é estimativa de malha (`REVISAO-MODELOS` já diz: "6,45 mm no clamp é inferência; a malha é facetada e não prova rosca"). `G-clamp_Tripod.stl` = **2 componentes, não fechada**; `clamp_frame.stl`/`clamp_frame_long.stl` = **fechadas**. As duas sapatas existem: `clamp_protector.stl` e `clamp_protector_0.6_loose.stl` (ambas 20×20×8, 33 014 / 33 022 facetas) | o mismatch dimensional é fato; mas **"mutuamente exclusivo" é enganoso**: o parafuso Ø12 é o aperto **do próprio clamp** (rosca interna Ø12 do modelo do vendor) e os 1/4"-20 são a **interface de tripé** do adaptador — são interfaces diferentes. Os defeitos que sobram, esses sim verificados: nenhuma rosca modelada (só envelopes), nenhum torque/pré-carga, a malha do vendor é **aberta** e o plano nomeia **uma** das duas sapatas |
| C6 | sem parâmetros de fatiamento/G-code/tempo; volume real **196 cm³** ⇒ **3–4,5 h** de extrusão pura, total 10–25 h; a estimativa do cupom erra por **4–10×** ("~30–40 min" vs ≥3 h) | **CONFIRMADO** | Volume somado das 12 peças (fonte: `build-measurements.json` + `mechanism-probe.json`): 2×22 762,885 + 2×42 636,720 + 2×20 490,756 + 2×411,354 + 2×1 438,383 + 2×10 262,498 = **196 005,2 mm³ = 196,0 cm³** (bate exato). A 12–14 mm³/s → **3,9–4,5 h** (a 10 mm³/s, 5,4 h). Cupom da Fase 1 com 3 luvas = 127,9 cm³ → **≈3,6 h** contra os "~30–40 min" prometidos = **5,3–7,1×** | está certo, dentro da faixa declarada. Fixar a hipótese de vazão (nada foi fatiado, então "3–4,5 h" depende dela) |
| C7 | a orientação da chaveta está certa **por sorte** (0,000 mm² de overhang como modelada), nunca justificada | **CONFIRMADO** | `overhang.json` → `ChavetaA`: +Y e −Y = **0,000 mm²**; +Z/−Z = 82,271; −X = 139,389; +X = 42,0 | está certo. Sem justificativa escrita em nenhum plano |
| C8 | câmara fechada contradiz PETG — a K1C chega a 35–40 °C com a tampa | **CONFIRMADO** (documento) | `PLANO-IMPRESSAO-K1C.md` C6 ✗ ABERTO e §0 registra "Câmara **fechada** (enclosure)"; o próprio plano diz "a prática é PETG com tampa fora/porta aberta" | está certo como conflito de processo; o 35–40 °C é valor de prática, não medido nesta bancada |
| C9 | o escopo das "12 peças" omite o mount v6 (o único verificado) e a caixa DIN do Pi (16 725,8 + 15 959,3 mm³, ambas fechadas) | **CONFIRMADO** | Mount v6: 8 787 mm³, fora do inventário do plano. Medido agora: `raspberry_pi_5_din_rail_bottom_side.stl` → `Shells[0]` **16 725,8420 mm³** (75,4 × 100,5 × 10,3); `raspberry_pi_5_din_topside.stl` → `Shells[1]` **15 959,3074 mm³** (73,8 × 96,3 × 12,5) | está certo. Ressalva: **não são "fechadas" de forma limpa** — cada uma traz 2 cascas espúrias (topside: 0,0000 e 0,0000; bottom: 0,0006 e 0,0037 mm³). O volume citado é o **principal**, não o total do arquivo |
| C10 | sem sobressalentes (só 2 chavetas, 1 variante de sapata), sem plano de retomada, sem plano-B | **CONFIRMADO** | Plano: 2+2+2+2+2+2; "Plano B" do §4 existe mas é **de ajuste pós-falha** (raspar, parafuso passante, cunha), não de sobressalente | está certo. Precisão: existe **plano B**, não existe **sobressalente** |

## Classe D — Licenças e rastreabilidade

| # | item v1 | status | verificação independente | o que muda na v2 |
|---|---|---|---|---|
| D1 | **Obra derivada não declarada**: `build_base.py` funde o bracket M6 (ADSRMedia, CC BY-NC-SA 4.0) no `SocketSaddleAdapted` → `base-v2` e `encaixe-separado` | **CONFIRMADO** | `base-estrutura…/build_base.py`: `b = Part.read('DIN Rail Bracket 4mm-component0.stl.brep')` → `b = b.fuse(...).cut(...)` → `saddle = saddle.fuse(b)`. O PDF do autor diz "Attribution—Noncommercial—Share Alike". E a geometria da canaleta da **peça oficial** é idêntica à do bracket (par de 7,7 mm² a 35,360 mm, mesma zona de 5,5 mm) | está certo — e **pior**: a peça oficial também é derivada, então a obrigação SA/NÃO-comercial alcança a peça que está no plano de impressão e no laudo |
| D2 | **Camera Module 3 STEP sem licença** | **CONFIRMADO** | `references/vendor/raspberry-pi/camera-module-3/` contém só o ZIP e `step/` (2 STP) — **nenhum LICENSE.txt**. O LICENSE.txt MIT existe **só** em `pi5/step/`. (`R05-OPTICAL-BLOCK` também nota que a licença da CM3 não deve ser presumida a partir da MIT do Pi5) | está certo |
| D3 | **CAD Winford sem licença** — fonte da seção dos montantes/travessa e reexportado em r06/r07 | **CONFIRMADO** | `dinr135-007.5.step` presente em `base-estrutura/inputs/` e `portico-montantes/inputs/`; a evidência é a **página/catálogo** do fabricante (`stage1-referencias…/evidence/winford-dinr135.html`, `winford-catalog.pdf`) — sem arquivo de licença. E o gate `section_fidelity` exige Δvolume **0,000000** contra o STEP do vendor ⇒ o montante **é** a geometria Winford reextrudada | está certo. Acrescentar que é o único caso em que a peça final é **byte-equivalente em volume** à fonte comercial |
| D4a | **GPL-2.0 misturado**: sub-shape `Fillet` do pi-camera-mounts copiado para peças nossas | **CONFIRMADO** (com nuance) | `R05-OPTICAL-BLOCK.md`: "pi-camera-mounts, James Pilgrim, **GPL-2.0**: `Camera Mount - Bottom.FCStd`, geometria `Fillet`, **usada diretamente nos dois gimbals**… Derivados/adaptadores desta composição usam GPL-2.0" | a obrigação é real. Nuance: **está declarada** no laudo R05 e nos `*-sources.json` — não é "licença silenciosa". O que falta é a atribuição **no artefato** (NOTICE) e o fato de o gimbal não estar no plano das 12 peças |
| D4b | **e** os `*.FCStd` foram **modificados in place** (`git status: M`), com o laudo registrando o hash pristino | **REFUTADO como está** | `git ls-files \| grep -i fcstd` → **0 arquivos**. `git status --short \| grep -i fcstd` → **0 linhas**. `git log --all --diff-filter=D --name-only \| grep -i fcstd` → **6 FCStd deletados** (R05Refs-v3-BLOCKED, column-v5, column-v6, optical-block, twocam-gclamp, v7-3cam-preview) | não é possível reproduzir "modificado in place com M": hoje **nenhum FCStd está no índice**. O que o git mostra é **remoção** dos 6 FCStd do rastreamento. Manter a consequência (a dívida de licença não muda), trocar o mecanismo |
| D5 | **Zero NOTICE/atribuição e zero licença do projeto** — 8+ obrigações BY não cumpridas | **PARCIAL** | Confirmado: não existe `LICENSE*` nem `NOTICE*` na raiz do repo pai (testado). Mas **não é zero atribuição**: existem `references/vendor/*/PROVENANCE.md` (g-clamp-tripod, din-rail-case, ender5-rpi-camera-case, din-rail-standoff-2020), `din-rail-parts/REFERENCES.md` + `raw/PROVENANCE.md`, e o laudo R05 cita PiPiece (**ISC**), pi-camera-mounts (**GPL-2.0**), CM3/Pi5. Levantei **7 titulares** com cláusula de atribuição: ADSRMedia (BY-NC-SA), Charlie Gallo / joehann (BY-NC-SA), Diyalec (BY-SA), herr_brain Redux (BY-SA ou UNVERIFIED), Shroamer (UNVERIFIED), James Pilgrim (GPL-2.0), PiPiece/John Cole (ISC) | manter "não existe licença de projeto nem NOTICE" (fato), mas **remover "zero atribuição"**: a atribuição existe em arquivos de referência e em 1 laudo — o que falta é **NOTICE consolidado** e atribuição **nos entregáveis** |
| D6 | r06/r07 e `inputs/` redistribuem malhas de terceiros sem arquivo de licença ao lado | **CONFIRMADO** | `base-estrutura…/inputs/` tem `License.txt` de 104 bytes — verificar: é o do ZIP do G-clamp; **não há licença ao lado** dos arquivos do vendor nas pastas de trabalho `r06-estrutura/`, `r07-estrutura/` nem em `portico-montantes/inputs/` | está certo; precisar que **um** License.txt existe em `base-estrutura/inputs/` (104 B), o que não cobre as demais cópias |
| D7 | Redux e angle adapter com licença divergente entre `REFERENCES.md` (UNVERIFIED) e `PROVENANCE.md` | **PARCIAL** | Redux: `REFERENCES.md` §4 → "UNVERIFIED_FROM_PRIMARY"; `raw/PROVENANCE.md` A) → "**CC BY-SA 4.0** (confirmar antes de uso comercial)" ⇒ **divergem, CONFIRMADO**. Angle adapter: os **dois** dizem UNVERIFIED_FROM_PRIMARY ⇒ **não divergem** | manter só o Redux; o angle adapter é uniformemente não verificado |
| D8 | `TRANSFER-MANIFEST.sha256` desatualizado (**2/30** falham); `raw/SHA256SUMS.txt` com entrada autorreferente | **PARCIAL** | `sha256sum -c TRANSFER-MANIFEST.sha256` → **3 FAILED de 30**: `Makefile`, `data/g0/README.md`, `data/g0/esteira-a-reference-r01.yaml`. Entrada autorreferente em `raw/SHA256SUMS.txt`: a linha 2 é o hash do **próprio** `SHA256SUMS.txt` | corrigir para **3/30**. O resto está certo |
| D9 | `PROVENANCE` afirma "nenhuma geometria de terceiro foi copiada para produção" — **falso** para o bracket M6 | **CONFIRMADO** | `din-rail-parts/REFERENCES.md` linha 3 e `raw/PROVENANCE.md` linha 3 repetem "Nenhuma geometria… foi copiada para produção". O `build_base.py` funde o bracket no `SocketSaddleAdapted` e a peça oficial herda a canaleta | está certo. É a **mesma** frase em dois arquivos ⇒ corrigir nos dois |

---

## Classe E — Lacunas de escopo

| # | lacuna v1 | status | verificação independente | o que muda na v2 |
|---|---|---|---|---|
| E1 | só 1 mount (49°) e ele foi abandonado — faltam topo (vertical) e lateral B; sem 2 mounts **não há 3 vistas** | **CONFIRMADO** | `REVISAO-MODELOS`: "o único mount de câmera verificado" é o v6; o BRIEFING exige topo + lateral A + ESP-CAM lateral B. `composicao-completa/RELATORIO.md` posicionou o mount **à mão** ("rotacionado 90° em Z e colocado… por posição aproximada") | está certo |
| E2 | FOV / distância / altura não determinados; o próprio CAD diz que as alturas foram chutadas | **CONFIRMADO** | `composicao-completa/RELATORIO.md` §3: "colocados 'no alto' e 'no meio'… **nenhum dos dois foi calculado aqui**". `R05-OPTICAL-BLOCK` faz verificação de **eixo**, explicitamente "não de FOV, distância focal útil ou cobertura de imagem" | está certo |
| E3 | **Trigger E18-D80NK: zero no CAD** — sem suporte, posição, distância, inclinação 10–15°, sem anteparo retrorrefletivo | **CONFIRMADO** | HW-04 exige "E18-D80NK inclinado em **10°–15°** mirando no anteparo retrorrefletivo oposto"; RF-01.1 detalha. Os 15 corpos do pórtico não incluem trigger | está certo |
| E4 | **FPC 200 mm: sem rota, raio, alívio, guia** | **CONFIRMADO** | `composicao-completa` §4: "O caminho do FPC não foi traçado… A restrição de 200 mm **não foi verificada** nesta composição". O único caminho medido é o do `R05-OPTICAL-BLOCK` (bloco antigo), não o do pórtico | está certo |
| E5 | **ESP-CAM: sem envelope, posição, mount, alimentação** (64×27,5×5,5 informado, não confirmado) | **CONFIRMADO** | BRIEFING: "ESP fornecida: 64 x 27.5 x 5.5 mm… Isto **NÃO** confirma modelo, PSRAM, pinout ou envelope da lente/conectores" | está certo |
| E6 | **Iluminação: sem suporte de LED, difusor, espaço reservado** (backlight declarado BLOCKED) | **CONFIRMADO** | HW-04 (2× LEDs RGB 5 mm, lente difusora, fita 3M), RF-30, RNF-21, D-18. Nenhum objeto no build de 15 corpos | está certo |
| E7 | **Cabos em geral: nenhuma rota, fixação ou alívio** | **CONFIRMADO** | `freecad_r05_optical_cables.py` existe mas pertence ao bloco R05 antigo; o pórtico atual (`portico-montantes`) não tem etapa de cabos | está certo |
| E8 | **Acesso de ferramenta não modelado** — cabeçote dos M3 dentro da canaleta perfilada | **CONFIRMADO** | Os furos de trava do pórtico são Ø3,4 com parafusos-envelope Ø3,0 cuja ponta toca a face do trilho em 7,069 mm²; a canaleta é a fêmea exata do perfil ⇒ não há espaço de cabeçote entre a parede da peça e a aba do trilho | está certo |
| E9 | **Case do Pi: engate no trilho não verificado** (posicionada visualmente); acesso a portas/refrigeração/2 FPC não comprovado | **CONFIRMADO** | `composicao-completa` §2: "os dois STLs foram posicionados no montante B **visualmente**. Não há medição de engate, folga ou interferência" | está certo |
| E10 | **BOM e esquemático do rig inexistentes** para a arquitetura atual | **CONFIRMADO** | HW-05 exige BOM versionada. Existe BOM parcial no `PLANO-IMPRESSAO-K1C.md` (§1/§2, sem SKU, sem preço: "Custo estimado: BLOCKED") e nenhum esquemático | está certo |
| E11 | **Encoder KY-040: sem acoplamento, suporte ou relação com rolete** | **CONFIRMADO** | RF-10, IF-02, D-21 exigem acoplamento e validação física. No CAD atual: zero | está certo |
| E12 | **Mudança de arquitetura não registrada em DECISIONS** (49° descartado, 3 câmeras, DIN em vez de T-slot) | **CONFIRMADO** | `DECISIONS.md` D-17 remete a `docs/design/grip-extensivel.md`, que ainda descreve **T-slot** ("Perfil estrutural em T-slot (alumínio 2020/2040)") enquanto o CAD usa **DIN TS35**. D-04 fala em 3 vistas; a matriz de referências diz 2. O 49° não aparece em nenhuma decisão | está certo — a contradição T-slot×DIN está **dentro** do próprio doc que o D-17 cita como detalhe |

## Classe F — Erros declarados do próprio relatório adversarial

| # | erro declarado | status | verificação | o que muda |
|---|---|---|---|---|
| F1 | tratou "colisão zero" como prova de "encaixa" ⇒ onde não havia contato medido, o claim é falso por construção | **CONFIRMADO** | `base-v2-checks.json` grava pares com `common = 0,0` **sem área de contato**; `RELATORIO-DOIS-JEITOS` chama isso de "encaixa" e depois admite (§ não resolvido, item 4) que o engate do trilho não foi testado | está certo. A regra "distância ≈ 0 **E** contato > 0" continua sendo o critério correto |
| F2 | chamou o aperto do Redux (141–177 mm³) de "não encaixa"; é mola apertando (7,96 mm³ em dz=−6) | **NÃO VERIFICÁVEL** | Não há artefato no workspace com 141–177 mm³ nem com 7,96 mm³: `grep` em `*.json/*.py` não retorna nenhum dos dois (`auditoria-r07` guarda `redux-sections.json` de 2 MB, sem esses agregados). O próprio `REVISAO-MODELOS` já retrata a "mordida de mola" como não-provada | manter a retratação, mas marcar que **os números de F2 não têm lastro gravado** — nem o 141–177 nem o 7,96 |
| F3 | o `closed_width 34 mm` do autor é evidência documental, não medição ⇒ LIKELY, não CONFIRMED | **CONFIRMADO** | `REFERENCES.md` §4 e `raw/PROVENANCE.md` A) listam os parâmetros **do autor** (`closed_width 34`, `spring_width 1.6`, `slide_clearance 0.2`); não há medição nossa da mola | está certo |
| F4 | escolheu `Shells[0]` cegamente ⇒ escolher a shell de maior área + guarda | **CONFIRMADO** | O caso Dyalec `topside` prova o custo (`Shells[0]` = 0,0000 mm³). A regra está correta, mas **não foi aplicada**: 4 scripts continuam sem guarda (ver A8a) | está certo, e **continua aberto** no código |
| F5 | o "diagnóstico" da cegueira do `face.common` era invenção; a causa era folga de 1,001 µm | **CONFIRMADO** | Reproduzido: `face.common` devolve 400,0000 em faces coincidentes e 0,000000 a 1,001 µm (`/tmp/v2_a2.py`) | está certo |
| F6 | apresentou 354,509 e 881,009 mm² como áreas de contato | **CONFIRMADO** | Os dois valores estão em `adversarial-pecaB/RELATORIO.md` como "áreas de contato". E o 354,509 é **função do passo** (0,02 → 354,5095; 0,005 → 298,0547; 0,001 → 0,2124) | está certo — e a dependência do passo, medida agora, era **pior** do que a v1 registrou |

---

## Classe G — NOVO: achados da rodada de correção, reverificados

A rodada de correção (scripts em `/tmp` do <host>: `enc_01..04`, `va1`, `r90`, `rf1`,
`c90`, `bt1`, `gd1`) produziu achados que **não estão na v1**. Cada um foi
reverificado por medição própria.

| # | achado novo (rodada de correção) | status | verificação independente | comentário |
|---|---|---|---|---|
| G1 | (novo, meu) a bateria adversarial `adv4.py` valida **peça sintética**, não as peças reais | **CONFIRMADO — e é o achado mais grave desta rodada** | `adv4.py` não lê STEP nenhum: `build_peca()` monta **2 caixas** (`box(66,GA,ALT)` + `box(GA,41,ALT)`) e fura; medi **12 541,0343 mm³**. O `encaixe` é o bracket do vendor + 1 caixa fundida − 1 caixa cortada → **11 916,6060 mm³**. Os artefatos reais: adversarial **11 522,1885** / encaixe **11 490,6713** / oficial **22 762,8846** | a "REFERÊNCIA PASSA + 4/4 mutações" prova apenas que **o checador é coerente com a peça que ele mesmo constrói**. Nenhuma das 5 medições tocou a peça que foi para o pórtico, nem a oficial, nem a peça B. O laudo do `adversarial-pecaB/RELATORIO.md` ("REFERÊNCIA PASSA ✓") precisa ser lido com essa ressalva |
| G2 | (rodada de correção) o bracket do vendor tem vão de **34,65 mm** (eixo Y) contra trilho de 35,00 ⇒ **interferência de 0,35 mm**; o bracket impresso em FDM pode **não entrar** no trilho | **REFUTADO** | O par de planos separado por 34,648 mm tem normais **(0, ±0,71, ±0,71)** — são os **chanfros de entrada a 45°**, com áreas 33,941 e 17,324 mm² (f1: X −12..12, Y −19,5..−18,5, Z 8,5..9,5; f311: X −12,5..12,5, Y 19..19,5, Z −2..−1,5). A distância perpendicular entre dois planos a 45° **não é a largura em Y**. O par de normais **±Y** é **35,360 mm**, entre duas faces de **7,700 mm²** (5,5 × 1,4) em Y = ±17,68 | a leitura da auditoria 3 (**35,36 ⇒ 0,18 mm/lado de folga**) estava **certa**; a "correção" mediu o chanfro. O risco de "não entrar no trilho" **não** vem daí — vem de C1a (canaletas da luva com folga zero) |
| G3 | o STL do bracket tem **5 shells**: a peça (788 faces) + **4 suportes embutidos de 1,94 mm³** que o autor manda remover com alicate ("supports built-in") | **CONFIRMADO** | `Mesh.getSeparateComponents()` → **5 componentes**: comp0 = 788 facetas, **10 352,711976 mm³** (26,0 × 39,0 × 11,5); comps 1–4 = **12 facetas cada**, volumes **1,938001 / 1,937998 / 1,938001 / 1,937998 mm³**, em X 7,5..13, Y ±(4,15..4,45) e ±(12,15..12,45), Z −0,1..1,6. Soma dos suportes = **7,752 mm³** (48 facetas) | CONFIRMADO, com a precisão: são **1,938 mm³ cada** (7,752 no total, não 1,94 no total). O PDF do autor confirma a prática ("come with supports built-in but they are easily removed with small pliers"). Consequência: **todo laudo que mediu o STL inteiro incluiu 7,752 mm³ e 48 facetas de material que não existe na peça usada** — irrelevante para volume (0,075%), mas relevante para contagem de facetas/shells e para qualquer análise por *feature* que confunda os pinos de suporte com geometria |
| G4 | o teste de encaixe do bracket contra o **TRILHO nunca existiu** no workspace: o `adv4.py` só mede encaixe × **PEÇA** | **CONFIRMADO** | `adv4.py`: `bateria()` calcula `area_por_penetracao(enc_,peca_)` e `eixos(peca_,…)` — o STEP do trilho **não é lido em nenhuma linha**. E `RELATORIO-DOIS-JEITOS` afirma "**trilho×bracket 0,0000 (encaixa)**" para CFG1 enquanto seu próprio §"O que NÃO está resolvido" item 4 diz "o engate do trilho nessa orientação **não foi testado com o trilho**" | o relatório **se contradiz**. Medi por conta própria: trilho de 35,00 mm centrado em Y, Z varrido de −4,0 a +8,0 mm (0,25 em 0,25) e 4 rotações (0/90/180/270) → **nenhuma** das 49 posições por rotação zera a colisão. Mínimo encontrado **5,8311 mm³** (rot 90/270, dz=+8,0, na borda da varredura) e **315,81 mm³** (rot 0) / **413,81 mm³** (rot 90) no alinhamento centrado por bbox. Não sei — e nenhum artefato define — qual é o assentamento correto. Fica provado que **o encaixe bracket×trilho não está estabelecido por nada**, e que ele **não** é o caso simples "vão 35,36 × trilho 35,00" |
| G5 | o `component0.brep` usado pelo `adv4.py` tem **391 faces** e o STL tem **788** — verificar se são a mesma peça e se isso invalida laudos | **CONFIRMADO (mesma peça) / NÃO INVALIDA** | `DIN Rail Bracket 4mm-component0.stl.brep` = shape **Solid**, 391 faces, **1 shell**, 1 sólido, **10 352,711976 mm³**, bbox 26,0 × 39,0 × 11,5 — **delta de volume 0,000000000 e delta relativo 1,8e−16** contra a componente principal do STL. 788 é a contagem de **facetas/triângulos**; 391 é a contagem de **faces** após a conversão (que já funde coplanares; `removeSplitter` não muda: 391 → 391) | **são a mesma peça**; 391 × 788 é facetas × faces, não duas geometrias. **Não invalida os laudos geométricos do adv4.py.** O que invalida é outra coisa: o brep **exclui os 4 suportes** (7,752 mm³) que o STL inclui — e o `adv4.py` usa o brep, ou seja, ele é o único artefato do pipeline que já mede a peça "sem suportes" |
| G6 | a rotação correta do bracket para o trilho é **90° em Z** (o vão está em Y e precisa ir para X) | **CONFIRMADO** | É exatamente o que o pipeline já faz: `build_base.py` e `adv4.py` definem `move(s, ang=90)` e giram em Z. Faz sentido geométrico: o montante medido tem a **largura (35 mm) em X** (bbox X −48..−13, Y 90,9..542,9, Z 10,05..17,55), então o canal de 35,36 do bracket (local Y) precisa ir para X. Conferi também que 26 mm (a dimensão X nativa) **não** acomodaria o trilho — o que confirma ser 90° e não 0° | a premissa está certa e já aplicada. O problema **não** é a rotação; é que, **com** a rotação certa, o assentamento em Z nunca zera (ver G4) |
| G7 | (novo, meu) a canaleta do trilho na **peça oficial** mede 35,360 mm = 0,180 mm/lado — o **mesmo** do bracket do vendor | **CONFIRMADO** | Faces planas da peça oficial com \|n\| em X, na zona Y 92,90..98,40 (os 5,5 mm de inserção): X=−48,18 (nx=+1, 7,700 mm²) e X=−12,82 (nx=−1, 7,700 mm²) ⇒ **35,360 mm**. Assinatura idêntica à do bracket | reescreve C1: o soquete **já tem** a folga do vendor; o que tem folga **zero** são as canaletas da **luva**. Não existe "déficit de 0,18–0,30 mm/lado" na peça |
| G8 | (novo, meu) o perímetro **300,99 mm** não tem origem em nenhum artefato | **CONFIRMADO** | Varri todas as faces de todos os 15 objetos do `portico-montantes.FCStd` procurando perímetro entre 295 e 310 mm → **nenhuma face**. O valor real da seção é 93,536280 mm (1 wire, 20 edges) | o número de `RELATORIO.md:86` é **órfão**. Não é "o real é 93,53 e o relatório errou por digitação": é um número sem fonte |
| G9 | (novo, meu) a bateria do `adv4.py` **não cobre o trilho nem o segundo grip**, e o `RELATORIO-DOIS-JEITOS` baseia CFG1/CFG2 em contatos que ele mesmo não mediu | **CONFIRMADO** | `adv4.py` mede apenas 5 casos (ref + M1..M4) sobre peça/encaixe sintéticos. `RELATORIO-DOIS-JEITOS` tabela "peca 0,0000 · clamp 0,0000 · **trilho×bracket 0,0000 (encaixa)**" sem script que produza a terceira coluna | em rigor, **a tabela CFG1/CFG2 da v1 estava certa em dizer que não se aplica** — e agora tem prova: nenhum script do workspace mediu aquele par |

---

## Classe H — NOVO: o que **nenhuma das duas rodadas** abordou

Nove pontos. Os quatro primeiros são os que o pedido nomeia; os cinco seguintes
saíram da releitura dos requisitos, dos design docs e dos laudos do workspace.

### H1 — A divisão "2 câmeras × 3 câmeras" nunca foi levada a uma decisão (e o CAD assumiu 3)

- **Requisito numerado = 3**: RF-01 ("capturar uma imagem da vista superior e duas
  imagens das vistas laterais"), RF-01.2, RF-05 e D-04 (vista superior + 2 laterais;
  "não existe maioria global entre as três câmeras"). `docs/pocs/03` também pede
  "três câmeras".
- **Design doc = 2**: `docs/design/matriz-referencias-decisoes.md:32` —
  "**2 câmeras obtusas (vigente)** × reports CAD 3CAM … manter **2**; 3ª (topo) só
  se a tampa não separar no gate"; `docs/design/preprocessamento-ideal-pet.md:4,17`
  — "2 câmeras obtusas"; `docs/reference/analise-cronologica-2026-09-11.md:24` —
  "rig mudou de 3 → 2 câmeras… **o que contradiz os reports**".
- **CAD/BRIEFING = 3**: `BRIEFING.md` fixa CM3 Wide topo + CM3 Wide lateral A +
  ESP-CAM lateral B; o mount v6 e a peça oficial foram projetados para isso.
- **Nenhuma das duas rodadas percebeu** que a contradição sobrevive **entre dois
  documentos normativos diferentes** (requisitos numerados × matriz de referências)
  e que a matriz cita como normativos "**D-04 + D-22**" — e **D-04 diz 3 vistas**.
  A matriz, portanto, contradiz o próprio normativo que ela invoca.
- **Impacto no CAD**: se a decisão vigente é 2 câmeras obtusas (ambas laterais,
  meia garrafa cada), então (i) **não existe** câmera de topo ⇒ a peça oficial e o
  mount v6 (49°, berço da CM3 Wide "topo vertical para baixo") pressupõem uma
  arquitetura que a decisão vigente não tem; (ii) o `PecaDuplaPlataformas` (2
  plataformas para o clamp) resolve outro problema; (iii) o CAD inteiro do pórtico
  (mount + 3 câmeras) estaria **desalinhado do escopo**. Isso é bloqueador de
  arquitetura, e é maior que qualquer item das classes A–D.

### H2 — As peças que serão impressas **não são** as peças verificadas (por origem, não por dimensão)

Verificação item a item do §1 do `PLANO-IMPRESSAO-K1C.md` contra o que foi
efetivamente medido:

| peça do plano | qtd | de onde vem | foi verificada? |
|---|---|---|---|
| `PecaDuplaPlataformasOFICIAL` | 2 | `base-estrutura…/peca-dupla-plataformas.step` (22 762,885) | **sim** (FACE, bbox, 1 sólido) — mas as **2× são a mesma peça**, uma translação rígida de +400 mm, **nunca espelhada/rotacionada** (é o que B4 deveria cobrar) |
| `JuncaoA/B` (luva) | 2 | extraída do **FCStd do pórtico** | **sim**, no conjunto — mas **não existe** STEP/STL por peça em `portico-montantes/exports/` (só o STEP do conjunto de 15 sólidos, 7,3 MB, sem manifesto por peça) |
| `ClampFunctionalSource` (G-clamp) | 2 | "do ZIP do joehann (é modelo de impressão)" | **não**. O CAD usa `G-clamp_Tripod-component0.stl.brep`, convertido da malha do **vendor** (ABSRT/Charlie Gallo), que é **não-fechada, 2 componentes**. O arquivo fechado de 71 mm do ZIP é `clamp_frame_long.stl` — outro arquivo. Ninguém mediu o clamp como peça imprimível |
| `ChavetaA/B` | 2 | pórtico | **sim** (411,354 mm³ cada, 6 × 2,75 × 5,0) |
| Sapata `clamp_protector` | 2 | "do ZIP" | **não**. Duas variantes no ZIP (`clamp_protector.stl` e `_0.6_loose`); o plano nomeia uma. Nenhuma medição de encaixe |
| Parafuso `screw_and_knurled_knobHD` | 2 | "do ZIP" | **não**. Rosca Ø12,00 medida; o CAD corta Ø6,35. Nenhuma verificação de que aperta o clamp |

- E o plano **omite** o mount v6 (8 787 mm³, o único mount verificado) e a case DIN
  do Pi (16 725,8 + 15 959,3 mm³) — C9, confirmado.
- **Consequência prática:** dos 6 itens do plano, **3 não têm verificação nenhuma**
  e **2 dos verificados não têm artefato de impressão por peça**. Com uma única
  oportunidade de impressão, o rig sai sem câmera (não há mount no plano) e com
  peças de origem não medida.
- **O que falta para fechar:** congelar um **conjunto de impressão** com STEP/STL
  por peça + SHA-256 + orientação, tirado de arquivos **fechados e validados**;
  e declarar, por peça, o arquivo-fonte e o hash.

### H3 — Tudo o que depende de **medição física da esteira** (e que o CAD não pode fechar)

Nenhuma das duas rodadas consolidou a lista. Dependem do G0/esteira real:

1. **mordente de ~10 mm** do clamp contra a espessura real da borda da esteira —
   é o que decide se o grip agarra (o `RELATORIO-DOIS-JEITOS` diz: "Qual
   configuração é a certa para a sua esteira — isso exige **medir a máquina**").
2. **largura da correia** → distância de trabalho do C_SIDE e altura do mount (FOV).
3. **simetria dos dois lados** → se o segundo grip precisa de espelho/rotação
   (a premissa do build diz explicitamente "**NOT validated (the conveyor was never
   measured)**").
4. **vão 400 mm / altura 450 · 362,5** → as duas premissas de layout do pórtico.
5. **massas e CG** → momento na garra e na chaveta (o plano marca D2/D3 ✗ ABERTO).
6. **zonas proibidas** (partes móveis, quadro) → posição do grip e do trigger.
7. **posição do trigger** e o **anteparo retrorrefletivo oposto** (HW-04) → distância
   e inclinação de 10–15°.
8. **acoplamento do encoder KY-040** a um rolete real (RF-10).
9. **seção real do trilho comprado** (tolerância de laminação) → a folga das
   canaletas; e o padrão de ranhuras medido é de um **corpo de prova de 75 mm**,
   extrapolado para 450 e 600 mm.
10. **espessura/forma/resistência do ponto real de contato** — o `grip-extensivel.md`
    condiciona: "a garra não pode ser considerada segura ou compatível com a IN 150
    até que espessura, formato e resistência do ponto real de contato sejam medidos
    no G0".
11. **estado real da impressora** (bico, mesa, adesão, filamento, umidade, câmara):
    o próprio plano diz "**isso só se resolve olhando a máquina**".

### H4 — O que o template de entrega do TCC exige e o CAD **não** cobre

- **Entrega 1** (`docs/reference/rubrica-entrega1.md`) exige um **PDF** com:
  identificação; tema por nome/número; escopo (situação, resultado, limites);
  levantamento de requisitos técnicos viáveis e aderentes; e, para nível máximo,
  análise aprofundada + visão crítica + justificativa das escolhas tecnológicas.
  O entregue é `latex-workspace/PNAAT-TCC-REQ-001-template.pdf` (12 p).
  **O CAD não é exigido por nenhum critério da rubrica.**
- **Entrega 2** (`docs/entrega2/CHECKLIST-RUBRICA.md`) exige um **vídeo** de uma
  execução acompanhável: entrada → execução → resultado + **outro elemento da
  arquitetura** além do núcleo, e o **próximo passo / o que não está integrado**.
  O CAD do pórtico **não aparece** como evidência: o material do ensaio registra
  "rig **v0 sem backlight**", "**Pi 5/ESP32 não plugados** na bancada atual",
  "**defeito real não existe** no dataset". Isto é, o pórtico do CAD não é o rig
  da Entrega 2.
- **Lacunas entre o CAD e o que a banca pode cobrar:**
  1. **Nenhuma figura/planta do pórtico no documento.** `latex-workspace/figuras/`
     tem só um README; `texto/` não tem figura do rig. Todo o CAD (400+ arquivos)
     está fora do entregável.
  2. **A rubrica exige justificativa das escolhas tecnológicas.** O CAD congelou
     decisões (49° fixo, PETG, DIN TS35, clamp de tripé) que **não estão em
     `DECISIONS.md`** (E12) — não há como citá-las como decisão registrada.
  3. **Requisito × evidência.** A rubrica cobra "requisitos tecnicamente viáveis e
     aderentes". O mount v6 tem 0,0434 mm³ **sem lastro** (A4) e o encaixe
     bracket×trilho não assenta em nenhuma posição testada (G4): se a banca pedir
     a medição, não há artefato.
  4. **Pendências editoriais do próprio entregável** (de
     `docs/entrega1-estado-final.md`): resíduo "hub" em `contexto.tex` que
     contradiz o núcleo de nó único; referências órfãs `DAT-*`/`IF-*`; figura 3.1
     usando "fusão por votação" contra o léxico "regra determinística"; nome do
     arquivo contendo "**template**" (`PNAAT-TCC-REQ-001-**template**.pdf`), que
     sugere rascunho; en-dash em "pixel–milímetro".
  5. **Licenças (D5).** Se o PDF ou o repositório for publicado com o CAD, a
     peça oficial é derivada **CC BY-NC-SA** (D1) e o gimbal R05 é **GPL-2.0**
     (D4a) — sem NOTICE, isso vira passivo de atribuição dentro do entregável.

### H5 — O clamp não é uma peça imprimível verificada (e o laudo o trata como uma)

O `G-clamp_Tripod.stl` do vendor tem **2 componentes e não é fechado**; o CAD o
converteu em sólido por `Part.makeSolid(Shells[0])` **sem guarda** (A8a). Ninguém
verificou se o sólido convertido é impressível (paredes, espessuras, furos). O plano
o lista como "é modelo de impressão" citando o ZIP do **joehann** — cujo arquivo
fechado equivalente é `clamp_frame_long.stl`. **Falta:** decidir o arquivo (vendor
aberto × joehann fechado), medir espessuras mínimas e fechar.

### H6 — Nada testa o requisito que o grip existe para atender: RNF-20 / RF-27 / HW-01

O `grip-extensivel.md` define o teste que dá sentido ao design — montar, calibrar,
**mover, remontar** e medir o drift em mm — e o RNF-20 exige "recalibração **não**
necessária após desmontar/remontar na mesma posição de trava". Nenhuma das duas
rodadas notou que **esse teste é inalcançável hoje**: as canaletas da luva têm folga
zero (C1a), então a peça **não monta** — logo não há como remontar. Não existe no
workspace: procedimento, cotas de posição de trava, registro de drift, nem o desenho
com cotas do RF-27.

### H7 — A antirrotação medida não é a antirrotação que o projeto precisa

A v1 (B3) já diz que a demonstração é de um nível só; o que ninguém mediu é **qual
restrição importa**. `premises.load_path` diz que **toda** a carga vertical chega ao
montante pela chaveta. Mas a antirrotação foi demonstrada girando o **montante**
dentro da luva — e a chaveta está na vertical. Ninguém mediu:
(a) rotação do **conjunto grip** em torno do parafuso do clamp (a "rotação livre"
que a v1 imputa); (b) rotação da **travessa** em torno do próprio eixo com a chaveta
engatada (só com a chaveta ausente: `upright_axial_*_key_hole_empty`); (c) o modo
**flambagem/balanço** do trilho de 450 mm (o plano marca D4 ✗ ABERTO). Ou seja:
o `rotation_blocked` da luva é real e reprodutível, mas **não é o modo de falha
mais provável** — o mais provável é a chaveta + a coluna, e esses não têm número.

### H8 — O "peça verificada × peça impressa" tem uma terceira peça no meio

Além da oficial (22 762,885) e da adversarial (11 522,188), existe a **`base-v2`**
(10 sólidos, 52 664,32 mm³, com `SocketSaddleAdapted` de 23 242,207 fundido ao
bracket do vendor) e a `base-candidate` (10 sólidos, 52 797,70). A v1 trata a
`base-v2` como "VÁLIDO" no `INDICE.md` (é a base boa) e a peça oficial como outra
coisa — mas **não diz em nenhum lugar qual das duas é a linhagem da peça oficial**.
Ninguém reconstruiu a cadeia `bracket do vendor → SocketSaddleAdapted → base-v2 →
PecaDuplaPlataformasOFICIAL`. Sem essa cadeia não há como dizer de qual arquivo
veio cada face da peça que se pretende imprimir — que é exatamente o que a
obrigação SA/NÃO-comercial (D1) exige saber.

### H9 — Nenhuma estimativa de risco/custo para "uma oportunidade de impressão"

O plano diz "só há uma chance" e define Fase 1/2/3 e critérios de aceitação — bem.
O que falta: (a) **orçamento de filamento** (196 cm³ + cupom ≈ 128 cm³ = 324 cm³
≈ 400 g a 1,24 g/cm³, sem purga nem brim); (b) **tempo total** (10–25 h, sem
G-code); (c) **lista de risco** com o que fazer se a luva não entrar (existe plano B
de ajuste, mas não de reimpressão); (d) **nenhum sobressalente** (C10). Nenhuma das
duas rodadas fez a conta de material nem mediu o custo — o próprio plano diz
"Custo estimado: BLOCKED".

---

## Dependência-raiz (atualizada)

**A seção real da esteira nunca foi medida (G0 BLOCKED)** — confirmado; e agora se
sabe que a dependência é **dupla**, não única:

- **Física (não muda):** mordente de 10 mm e acesso ao parafuso · largura da correia →
  distância de trabalho e altura do mount (FOV) · simetria dos dois lados → orientação
  do segundo grip (a premissa do build diz "NOT validated") · vão 400 / altura 450 e
  362,5 · massas e CG → momento na garra e na chaveta · zonas proibidas · posição do
  trigger e do anteparo · acoplamento do encoder · rota da FPC · seção do trilho
  comprado · espessura/resistência do ponto de contato real (a condição da IN 150).
- **Normativa (nova):** **qual arquitetura está vigente** — 2 câmeras obtusas
  (matriz de referências + design docs) ou 3 vistas com topo (RF-01/RF-05/D-04 +
  BRIEFING). Enquanto isso não for decidido em `DECISIONS.md`, o mount v6, a peça
  oficial e o escopo do CAD estão pendurados em uma premissa não registrada (H1 + E12).

Sem as duas, não há como fechar folga, altura, ângulo, retenção, carga ou o próprio
conjunto de impressão.

## Anexo A — artefatos de verificação desta v2

Todos os scripts foram escritos em `/tmp` do <host> (nada no workspace) e rodados com:

```
SR=/home/<usuario>/.cache/qwen-mm-plugins/apps/freecad-1.1.1/squashfs-root
runuser -u <usuario> -- env LD_LIBRARY_PATH=$SR/usr/lib/x86_64-linux-gnu:$SR/usr/lib \
  QT_PLUGIN_PATH=$SR/usr/lib/x86_64-linux-gnu/qt5/plugins $SR/usr/bin/freecadcmd <script>
```

| script | o que ele prova |
|---|---|
| `/tmp/v2_bracket.py` | 5 componentes do STL do bracket (peça 788 facetas / 10 352,712 + 4 suportes de 1,938); brep = mesma peça (Δvol 0,0; 391 faces); pares de planos opostos; 34,648 é par de chanfro 45° e 35,360 é o par ±Y |
| `/tmp/v2_fit.py` | identidade face a face dos pares (f334/f341 = 7,700 mm² em Y ±17,68 → 35,360); teste focal trilho × bracket |
| `/tmp/v2_metod.py` | A1 (cubos 400,000 exato e independente do passo; eixo Ø20 → 400,0000 vs 1256,6371 = π; axial → 0,0000); A2 (400,0000 coincidente / 0,000000 a 1,001 µm); A7 (perímetro 93,536280); pares do encaixe×peça em 6 passos |
| `/tmp/v2_parts2.py` | família do clamp (dims/manifold); **zero faces cilíndricas** no clamp; rosca do parafuso Ø12,00 por perfil radial |
| `/tmp/v2_adv.py` | A3 (11 522,1885 / 11 490,6713 / 22 762,8846); adv4 sintético (12 541,0343 / 11 916,6060); Dyalec (15 959,3074 e 16 725,8420; `Shells[0]` = 0,0000); varredura de perímetro 295–310 → nenhuma |
| `/tmp/v2_last.py` | luva × montante com micro-deslocamentos; perfil completo trilho × bracket em dz; pares de planos da peça oficial (33,31 / 34,648 / **35,360**) |
| `/tmp/v2_peca.py` | identidade das faces da peça oficial na zona de inserção (X −48,18 e −12,82, 7,700 mm² cada, Y 92,90..98,40) |
| `/tmp/v2_a2.py` | o teste limpo do `face.common` (400,0000 / 0,000000) |

Artefatos das auditorias anteriores reaproveitados (lidos, não gerados agora):
`/tmp/k1c-audit/{overhang.json,ov2.txt,vendorlip.log,probeclear.log}`, `/tmp/enc_work/out04.txt`,
`/tmp/{r90,rf1,va1,bc1,bt1,gd1}.log`, `/tmp/c90.log`, `/tmp/montar2.py`.

## Anexo B — o que eu **não** consegui verificar (e o que falta)

| ponto | por que não fecha | o que falta |
|---|---|---|
| F2 (Redux 141–177 mm³ × 7,96 mm³) | nenhum arquivo do workspace grava esses agregados; `redux-sections.json` (2 MB) não os contém | reexecutar a medição do Redux ou retirar os números do texto |
| origem do `300,99 mm` | nenhuma face do pórtico tem esse perímetro; não há log com o número | apagar o número ou achar o cálculo que o gerou |
| o assentamento correto do bracket no trilho | nenhuma posição testada zera a colisão; não existe datum de assentamento declarado para esse par | definir o datum (plano de apoio + batente axial) e só então medir encaixe |
| espessura real da chapa do trilho (1,0 vs 1,2 mm) | o `RELATORIO do pórtico` cita "chapa de 1,0–1,2 mm" e `section` dá área/desenvolvido compatíveis com 0,979 mm médio, mas o STEP não tem essa cota | medir no trilho comprado (é a mesma dependência C3) |
| 35–40 °C da K1C com tampa | valor de prática, não medido nesta bancada | termopar na câmara |
| 2 câmeras × 3 câmeras | não é medível: é decisão de projeto | registrar em `DECISIONS.md` (H1) |
| RF-10/RF-27/RNF-20 (encoder, cotas, drift) | não existe artefato | desenho com cotas + ensaio de remontagem — **inalcançável enquanto a luva tiver folga zero** |

---

*Revisão concluída em 2026-09-11. Nenhum arquivo do workspace foi alterado; nenhum
comando de escrita no git foi executado. Esta v2 existe apenas como
`/tmp/CHECKLIST-v2.md`.*
