---
tags: [type/report, theme/pnaat, theme/tcc]
aliases: []
lead: "Checklist adversarial consolidada de 5 auditorias independentes sobre a sessão CAD do pórtico PNAAT — 40 achados, sendo 21 bloqueadores de impressão."
created: 2026-09-11
modified: 2026-09-11
review_status: draft
---

# Checklist adversarial — sessão CAD PNAAT (consolidada de 5 auditorias)

Data: 2026-09-11. Fonte: 5 auditorias independentes rodadas em paralelo
(claims geométricos · arquitetura · plano de impressão · licenças · lacunas de escopo).
Workspace auditado: `/home/<usuario>/tcc-pnaat/github/cad-workspace` no <host>.
Nada foi alterado pelas auditorias.

## Veredito

**O pórtico não está pronto para imprimir.** Há 21 bloqueadores de pré-impressão
e 7 achados que invalidam números já publicados nos relatórios. A peça oficial
(22 762,885 mm³) **não é a peça que foi verificada** (11 522 mm³), a folga das
canaletas é **zero** onde o vendor prova que o certo é 0,18 mm/lado, e o caminho
de carga nunca foi verificado.

---

## Classe A — Metodologia de medição (invalida números usados para decidir)

| # | Achado | Evidência | Sev |
|---|---|---|---|
| A1 | O medidor de área por penetração mede **área projetada**, não área de contato. Erro sistemático **π/2 ≈ 1,57×** em superfícies curvas (eixo Ø20 em furo casante: real 1256,64 mm², medidor devolve 400,000). E é dependente do passo: 354,51 (0,02) → 298,05 (0,005) → 207 (0,001) | Task 1; `/tmp/pnaat_probe5.py` | P1 |
| A2 | O **diagnóstico central da rodada adversarial é falso**. `face.common` **não** é cego a faces coplanares com normais opostas (calibração: 400,000 mm²). A causa real do zero era folga de **1,001 µm** na construção (`yseat+GA−67.0`). Troquei um método exato por um enviesado | Task 1; `/tmp/pnaat_probe4.py` | P1 |
| A3 | **A peça verificada não é a peça oficial.** Adversarial 11 522,188 mm³ · DOS-JEITOS 11 740 mm³ · oficial 22 762,885 mm³ (bbox Y 32..107,4 vs 32..73) ⇒ os 354,509/881,009 mm² e a tabela CFG1/CFG2 **não se aplicam** ao que foi para o pórtico | Task 1; `/tmp/pnaat_probe10.py` | P1 |
| A4 | `0,0434 mm³` do mount v6 **sem lastro** — não existe em nenhum JSON/log/script, só no texto do R05. O placement do ensaio não foi registrado (reproduzir dá gap de 532 mm) | Task 1 | P1 |
| A5 | `insertion_depth: 5.5` é **literal hardcoded** em `mechanism_probe.py:7` — valor certo, mas o JSON não é evidência de medição | Task 1 | P2 |
| A6 | "colisão 0 em todos os pares" — o build testou **22 de C(15,2)=105**; `base-v2-checks.json` registrou **16 de 45**. Sobrevive à re-medição exaustiva, mas não pela evidência gravada | Task 1 | P2 |
| A7 | "seção tem perímetro **300,99 mm**" — o real é **93,536282 mm** (o próprio `build-measurements.json` registra) | Task 1 | P2 |
| A8 | `Shells[0]` **sem guarda** em 4 scripts; o único erro real é o Dyalec (`topside` tem 3 cascas e a `[0]` tem volume 0,000000). Nenhum script do workspace usa esses STLs ⇒ a escolha errada foi manual/invisível | Task 1; `/tmp/pnaat_probe12.py` | P2 |

## Classe B — Arquitetura e física (invalida decisão de projeto)

| # | Achado | Evidência | Sev |
|---|---|---|---|
| B1 | **Sem retenção anti-queda.** `grip-extensivel.md:82-83` exige cabo/cordão de retenção; ausente no CAD e no plano. Grip por atrito de mordente de 10 mm + parafuso **impresso** ⇒ pode cair sobre a esteira | Task 2 | P1 |
| B2 | **Trava do mount e da case não existe.** "a modelar" (`R05-CAMERA-MOUNT-DIN.md:57`); viola D-17 (`DECISIONS.md:254`) e RNF-20 | Task 2 | P1 |
| B3 | **Antirrotação demonstrada em UM só nível.** Junção↔montante↔travessa: 234,43/466,75/1031,39 mm³ a 1/2/5°. No grip: **só afirmada**. E o clamp medido tem **um** furo de tripé, não dois ⇒ rotação livre em torno do parafuso | Task 2 | P1 |
| B4 | **2 grips em lados opostos é fisicamente impossível como está.** Os lados são translação rígida, mas o clamp tem boca única (+X) e nenhuma peça espelhada foi modelada | Task 2 | P1 |
| B5 | **Largura (travessa) sem trava positiva nem referência de retorno.** A altura tem chaveta; a largura só tem parafusos sem pré-carga modelada. Viola D-17 | Task 2 | P1 |
| B6 | **FPC 200 mm impossível no layout montado.** Pi no montante B, câmera no A, vão 400 mm. O único cálculo existente é de distância de eixo (~187 mm), não de rota. Cabo é Standard–**Mini** (Pi 5), não documentado; G2 em FAIL por falta de raio mínimo | Task 2 | P1 |
| B7 | **Iluminação e trigger não existem no CAD do pórtico.** Nenhum objeto nos 15 corpos; sem previsão de backlight difuso, polarizador, fundo absorvedor ou fita retrorrefletiva (exigidos por HW-04, RF-30, RNF-21, D-18) | Task 2 · Task 5 (B3/B6) | P1 |
| B8 | **Ângulo fixo de 49° sem pivot.** A spec congelada exige "ajuste fino com trava"; o pior caso 2L pede 49° (Wide) / **69°** (Standard). Sem ajuste não há correção pós-medição | Task 2 | P1 |
| B9 | **Mount validado para sensor provavelmente errado.** v6 = CM3 **Wide** (rolling shutter); a spec de aquisição pede **mono + global shutter** | Task 2 | P1 |
| B10 | **Caminho de carga não verificado em nenhum ponto.** Sem massa/CG, sem M=F·e, e o peso superior é retido **só** por chaveta impressa apoiada na borda de **1,0 mm** da chapa do trilho = 16,8 mm² sob carga permanente (fluência de PETG) | Task 2 | P1 |
| B11 | **Folga zero converte antirrotação em jogo.** Derivado: folga 0,2–0,3 mm/lado ⇒ jogo 0,65–0,98° ⇒ **2,3–3,4 mm** na ponta a 200 mm e **5,1–7,7 mm** a 450 mm. Mata RNF-20/MAINT-01 e a meta D-07 de 0,5 mm | Task 2 | P2 |
| B12 | **"Chaveta de 1 mm em cisalhamento" mal descrito.** A chaveta tem **5,0 mm**; os 1,0 mm são a **chapa do trilho**. Cisalhamento real 31 mm², apoio 16,8 mm² — nada calculado | Task 2 · Task 3 | P2 |
| B13 | **Clamp: dois artefatos diferentes com o mesmo nome.** `clamp_frame.stl` (joehann) = **61,0 × 35,0 × 20,0** (manifold) × `G-clamp_Tripod.stl` = 71,0 × 35,0 × 20,0 (3 218 facetas). O plano credita um, o CAD usa outro, e nenhuma comparação existe | Task 2 · Task 3 | P2 |
| B14 | **Contradição de arquitetura não resolvida:** docs/backlog dizem "a decisão vigente é 2 câmeras"; o BRIEFING mais recente diz **3**. Não há documento normativo decidindo | Task 5 | P1 |

## Classe C — Fabricabilidade (a chapa única)

| # | Achado | Evidência | Sev |
|---|---|---|---|
| C1 | **A folga desenhada é ZERO.** Luva: **0,000 mm/lado** (deslocar 0,002 mm já interfere 1,19 mm³). Peça oficial: 0,01–0,02. O bracket do vendor prova o certo: **35,36 mm para trilho de 35,00 = 0,18 mm/lado**. Déficit de 0,18–0,30 mm/lado ⇒ **a peça não entra no trilho de aço** | Task 3 | **P1** |
| C2 | **A Fase 1 do plano é inexequível.** Nenhum arquivo com folga/clearance/cupom existe; criar folga é alterar geometria congelada e validada | Task 3 | P1 |
| C3 | **A folga não pode ser calibrada sem o trilho** — §2 lista os trilhos como ainda **a comprar** | Task 3 | P1 |
| C4 | **Zero orientação de impressão** para as 12 peças. Como modelada, a luva tem **duas pontes de 23,4 mm** (1 006,20 mm² cada) sobre vão de 1,0 mm; girando para +X cai para 658,05 mm² (4,10%) com maior vão de 3,9 mm | Task 3 | P1 |
| C5 | **O conjunto do clamp é mutuamente exclusivo.** O parafuso impresso tem rosca **Ø12,00** contra furo **Ø6,45** do clamp do CAD (não passa); e o mesmo plano lista 4× parafuso **1/4"-20**. `G-clamp_Tripod.stl` é **non-manifold** (10 arestas); o do joehann é fechado. Há 2 variantes de sapata (justa e **0,6 mm folgada**) e o plano nomeia só a justa | Task 3 | P1 |
| C6 | **Sem parâmetros de fatiamento, sem G-code, sem tempo.** Volume real 196 cm³ ⇒ 3–4,5 h de extrusão pura, total 10–25 h. A estimativa do cupom está errada por **4–10×** ("~30–40 min" vs ≥3 h) | Task 3 | P1 |
| C7 | **A orientação da chaveta está certa por sorte** (0,000 mm² de overhang como modelada), nunca justificada. A orientação alternativa põe a carga **através das camadas** (perda 40–60%) | Task 3 | P2 |
| C8 | **Câmara fechada contradiz PETG** — a K1C chega a 35–40 °C com a tampa; a prática é PETG com tampa fora/porta aberta | Task 3 | P2 |
| C9 | **Scope das "12 peças" omite** o mount v6 (o único verificado) e a caixa DIN do Pi (16 725,8 + 15 959,3 mm³, ambas fechadas). Numa chance única, o rig sai **sem câmera** | Task 3 | P2 |
| C10 | **Sem sobressalentes** (só 2 chavetas, 1 variante de sapata), sem plano de retomada, sem plano-B | Task 3 | P2 |

## Classe D — Licenças e rastreabilidade

| # | Achado | Evidência | Sev |
|---|---|---|---|
| D1 | **Obra derivada não declarada.** `build_base.py` funde o bracket M6 (ADSRMedia, **CC BY-NC-SA 4.0**) dentro do `SocketSaddleAdapted` → `base-v2` e `encaixe-separado`. Herda NC+SA e nenhum artefato nosso declara licença | Task 4 | P1 |
| D2 | **Camera Module 3 STEP sem licença** — base de referência do único mount validado | Task 4 | P1 |
| D3 | **CAD Winford sem licença** — é a fonte da seção dos montantes/travessa (o gate exige volume idêntico) e é reexportado em r06/r07 | Task 4 | P1 |
| D4 | **GPL-2.0 misturado.** Sub-shape `Fillet` do pi-camera-mounts copiado para peças nossas; **e** os `*.FCStd` foram **modificados in place** (`git status: M`), com o laudo registrando o hash pristino | Task 4 | P1 |
| D5 | **Zero NOTICE/atribuição e zero licença do projeto** — 8+ obrigações BY não cumpridas | Task 4 | P1 |
| D6 | **r06/r07 e `inputs/` redistribuem malhas de terceiros** sem arquivo de licença ao lado | Task 4 | P1 |
| D7 | Redux e angle adapter com licença divergente entre `REFERENCES.md` (UNVERIFIED) e `PROVENANCE.md` | Task 4 | P2 |
| D8 | `TRANSFER-MANIFEST.sha256` **desatualizado** (2/30 falham); `raw/SHA256SUMS.txt` com entrada autorreferente | Task 4 | P2 |
| D9 | `PROVENANCE` afirma "nenhuma geometria de terceiro foi copiada para produção" — **falso** para o bracket M6 | Task 4 | P2 |

## Classe E — Lacunas de escopo (não abordadas no CAD)

| # | Lacuna | Requisito | Sev |
|---|---|---|---|
| E1 | **Só 1 mount (49°) e ele foi abandonado** — faltam topo (vertical) e lateral B. Sem 2 mounts **não há 3 vistas** | BRIEFING:6; R05:59,62 | Bloqueador |
| E2 | **FOV / distância / altura não determinados.** O próprio CAD diz que as alturas foram chutadas | HW-01; RNF-11/14 | Bloqueador |
| E3 | **Trigger E18-D80NK: zero no CAD** — sem suporte, posição, distância, inclinação 10–15°, sem anteparo retrorrefletivo | HW-04; RF-01.1; IF-01; D-20 | Bloqueador |
| E4 | **FPC 200 mm: sem rota, raio de curvatura, alívio, guia** | BRIEFING:7; HW-02; RNF-20 | Bloqueador |
| E5 | **ESP-CAM: sem envelope, posição, mount, alimentação** (64×27,5×5,5 informado, não confirmado) | BRIEFING:6,8 | Bloqueador |
| E6 | **Iluminação: sem suporte de LED, difusor, espaço reservado** (backlight declarado BLOCKED) | HW-04; RF-30; RNF-21 | Bloqueador |
| E7 | **Cabos em geral: nenhuma rota, fixação ou alívio** | HW-02/06; RNF-20; DOC-04 | Bloqueador |
| E8 | **Acesso de ferramenta não modelado** — cabeçote dos M3 dentro da canaleta perfilada | OPS-01; MAINT-01 | Bloqueador |
| E9 | **Case do Pi: engate no trilho não verificado** (posicionada visualmente); acesso a portas/refrigeração/2 FPC não comprovado | R05-OPTICAL-BLOCK:11 | Bloqueador |
| E10 | **BOM e esquemático do rig inexistentes** para a arquitetura atual | HW-05; DOC-04 | Bloqueador |
| E11 | **Encoder KY-040: sem acoplamento, suporte ou relação com rolete** | RF-10; IF-02; D-21 | Bloqueador |
| E12 | **Mudança de arquitetura não registrada em DECISIONS** (49° descartado, 3 câmeras, DIN em vez de T-slot) | MAINT-02; ACC-01 | Bloqueador |

## Classe F — Correções dos meus próprios erros (declaradas)

| # | Erro meu | Correção |
|---|---|---|
| F1 | Tratei "colisão zero" como prova de "encaixa" em vários pontos ⇒ onde não havia contato medido, o claim é **falso por construção** (peça flutuando) | Exigir **distância ≈ 0 E contato > 0**; para encaixe por mola, aceitar colisão pequena de projeto |
| F2 | Chamei o aperto do Redux (141–177 mm³) de "não encaixa" | É **mola apertando**. Medido no critério certo: colisão **7,96 mm³** em `dz=-6` com distância 0 ⇒ LIKELY encaixa |
| F3 | O `closed_width 34 mm` do autor é evidência **documental** (PROVENANCE), não medição da mola | Registrar como **LIKELY**, não CONFIRMED |
| F4 | Escolhi `Shells[0]` cegamente | Escolher a shell de **maior área** + guarda que falha se houver >1 shell inesperada |
| F5 | "Diagnóstico" da cegueira do `face.common` era **invenção** | A causa era folga de 1,001 µm — método correto era o original |
| F6 | Apresentei 354,509 e 881,009 mm² como áreas de contato | São **áreas projetadas** enviesadas; não citar como contato |

---

## Dependência-raiz

**A seção real da esteira nunca foi medida (G0 BLOCKED).** Dependem disso:
mordente de 10 mm e acesso ao parafuso · largura da correia → distância de trabalho e
altura do mount (FOV) · simetria dos dois lados · vão 400/600 e altura 450/362,5 ·
massas/CG → momento na garra e na chaveta · zonas proibidas · posição do trigger ·
acoplamento do encoder · rota do FPC · seção do trilho comprado.
