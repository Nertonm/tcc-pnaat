# INDICE: workspace CAD PNAAT (`cad-workspace`)

Ordem de leitura: este arquivo, depois [`REVISAO-MODELOS-20260911.md`](REVISAO-MODELOS-20260911.md)
(a revisao que abriu os arquivos no FreeCAD e derrubou os claims antigos).

Organizacao aplicada em 2026-09-11: **nada foi apagado**; diretorios de staging
foram renomeados para nome funcional, um lixo de diagnostico foi arquivado, um
laudo foi copiado para junto do seu STEP, e arquivos novos foram adicionados
(este indice, `REPROVADO.md` em 2 diretorios). Backup e manifesto:
[`_fora-do-repo/_backup-organizacao-20260911/`](_fora-do-repo/_backup-organizacao-20260911/).

**Legenda de veredito**

| veredito | significa |
|---|---|
| **VALIDO** | STEP aberto no FreeCAD headless; 1 solido valido e gates passaram |
| **REPROVADO** | montagem invalida comprovada; nao usar como base |
| **CUPOM** | peca de diagnostico que corrige um defeito pontual; **nao e montagem** |
| **CONCEITO** | historico de projeto sem gate geometrico; nao prova nada |

---

## 1. Os tres artefatos VALIDOS (unicos que podem ser usados como base)

| artefato | caminho | veredito | por que (uma linha) |
|---|---|---|---|
| peca oficial dupla-plataformas | `iteracoes/base-estrutura-20260911T053435Z/peca-dupla-plataformas.step` | **VALIDO** | 1 solido valido, 22 762,9 mm3, assentamento 0; duas plataformas + encaixe do trilho integrado (STEP + STL + FCStd + manifest) |
| base v2 | `iteracoes/base-estrutura-20260911T053435Z/base-v2.step` | **VALIDO** | 10 solidos validos, zero colisoes; M6-trilho gap 0,000 mm / insercao 5,5 mm |
| mount de camera CM3 Wide v6 | `exports/concepts/optical-rig-r05/camera-mount-din-v6.step` | **VALIDO** | 1 solido, 8 787 mm3, 0,0434 mm3 de interferencia contra o CM3 completo (631 solidos); o unico mount de camera verificado |

Em `iteracoes/base-estrutura-20260911T053435Z/` convivem com esses dois o `base-candidate`
(10 solidos, 52 797 mm3; variante de teste, **nao** e a base v2) e os relatorios
`RELATORIO-BASE-V2.md` / `RELATORIO-DOIS-JEITOS.md`. A base boa e a `base-v2`.

### 1.1 Mount validado + seu laudo (reunidos)

| item | caminho |
|---|---|
| STEP validado | `exports/concepts/optical-rig-r05/camera-mount-din-v6.step` |
| STL do mesmo modelo | `exports/concepts/optical-rig-r05/camera-mount-din-v6.stl` |
| **Laudo (fonte, nao movido)** | `reports/R05-CAMERA-MOUNT-DIN.md` |
| Copia do laudo ao lado do STEP | `exports/concepts/optical-rig-r05/LAUDO-camera-mount-din-v6.md` |

A copia comeca com um cabecalho de proveniencia e o sha256 do original; o
original **nao foi movido** de `reports/`. As versoes `camera-mount-din-v1.step`
e `camera-mount-din-v3.step` ficam como historico (v3 e anterior ao v6).

## 2. REPROVADOS: ver `REPROVADO.md` dentro de cada pasta

| conjunto | caminho | veredito | por que |
|---|---|---|---|
| R06; estrutura | `exports/concepts/optical-rig-r06-estrutura/` | **REPROVADO** | cantoneira com **2 solidos** (nao e peca unica) e **sem STEP**; so STL |
| R07; estrutura | `exports/concepts/optical-rig-r07-estrutura/` | **REPROVADO** | **Redux perpendicular ao plano de engate**; "mordida de mola" nao provada; **sem STEP**; so STL |

Os dois receberam `REPROVADO.md` no topo avisando que os `RELATORIO.md` ali
dentro carregam claims retratados (mordida elastica de 182 mm3 nao e prova de
mola; "o bracket M6 nunca encaixa" estava errado; encaixa com gap 0 e insercao
5,5 mm; a cantoneira R07 era 2 solidos, nao peca unica). Os relatorios originais
**nao foram editados nem apagados**.

## 3. CUPOM (diagnostico, nao montagem)

| artefato | caminho | veredito | por que |
|---|---|---|---|
| cantoneira-topology-only | `iteracoes/auditoria-r07-20260911T052357Z/cantoneira-topology-only.step` | **CUPOM** | 1 solido valido de 10 192 mm3 que so corrige a continuidade do canto; **nao e conjunto montado** |

## 4. CONCEITO: historico, sem gates geometricos

| conjunto | caminho | o que e |
|---|---|---|
| R01 | `exports/concepts/optical-rig-r01/` | primeiro rig (placas de adaptacao, docks, guides de cabo); sem gates |
| R02 | `exports/concepts/optical-rig-r02/` | rig de bancada (bench plate, clamps, cabo); sem gates |
| R03 | `exports/concepts/optical-rig-r03/` | portal aberto; `validation.json` de inspecao, sem gate volumetrico |
| R04 | `exports/concepts/optical-rig-r04/` | "print-ready" do rig antigo; sem gates |
| R05 montagens antigas | `exports/concepts/optical-rig-r05/optical-rig-r05-column-*` (draft, modules v2/v3/v4, v5, v6), `*-twocam-gclamp`, `*-optical-block*`, `*-v7-3cam-preview` | colunas/optical block/twocam: 11-17 solidos, montagens antigas, **sem gates**; nao sao o mount validado (esse e o `camera-mount-din-v6.step`) |
| grip MDF/FDM | `exports/concepts/grip-mdf-fdm-r01/` | envelopes conceituais (A_* e B_*) do grip; `reference_only`, nao medidos |
| fontes CadQuery | `cad/cadquery/` | codigo-fonte (conceitos r01-r03 + referencias de envelope) |

## 5. Diretorios do workspace

| caminho | o que e |
|---|---|
| `cad/` | fontes CadQuery/FreeCAD (`.gitignore` local barra STEP/STL) |
| `data/` | dados G0 (canario, templates, inventarios de foto) e contratos de conceito (`concepts/optical-rig-r05-contract.json`, `camera-mount-spec-v1.md`). **Nao sao medicoes fisicas** |
| `exports/` | CAD gerado (fora do git por `cad-workspace/.gitignore`). Contem o historico R01-R07 + grip |
| `prompts/` | prompts internos de agente (fora do git). Nao e CAD |
| `reports/` | laudos de referencia com estado de evidencia; inclui o laudo do mount |
| `scripts/` | validadores e geradores FreeCAD/CadQuery |
| `references/` | referencias de terceiros (`vendor/`, `freecad/`); **somente leitura** |
| `.venv/` | ambiente Python local; nao tocado |
| `iteracoes/auditoria-r07-20260911T052357Z/` | (ex `candidate-audit-...`) auditoria da R07: entradas STL, build/verify, `RELATORIO.md` e o cupom topologico |
| `iteracoes/base-estrutura-20260911T053435Z/` | (ex `structural-candidate-...`) base v2 + peca oficial + testes (`base-candidate`, probes, renders) |
| `iteracoes/stage0-referencias-20260911T032253Z/` | (ex `stage0-reference-review-...`) estagio 0: BRIEFING, inventario e relatorio de referencias |
| `iteracoes/stage1-referencias-20260911/` | (ex `stage1-references-20260911`) estagio 1: FINDINGS + evidencias baixadas (STEP/PDF/HTML das referencias) |
| `iteracoes/portico-montantes-20260911T063439Z/` | **workstream paralelo em andamento** (criado 06:34Z, depois da revisao): inputs + probe de montantes do portico. Fora do escopo desta organizacao; **nao avaliado** |
| `_fora-do-repo/_backup-organizacao-20260911/` | manifesto pre/pos, baseline.json, gitignore-context, este backup em tar.gz |
| `INDICE.md` | este arquivo |

## 6. Renomeacoes de 2026-09-11 (nome antigo -> nome novo)

| nome antigo | nome novo | por que esse nome |
|---|---|---|
| `candidate-audit-20260911T052357Z` | `iteracoes/auditoria-r07-20260911T052357Z` | era auditoria da R07, nao um "candidato" |
| `structural-candidate-20260911T053435Z` | `iteracoes/base-estrutura-20260911T053435Z` | e a base estrutural (base v2 + peca oficial) |
| `stage0-reference-review-20260911T032253Z` | `iteracoes/stage0-referencias-20260911T032253Z` | estagio 0 = revisao de referencias |
| `stage1-references-20260911` | `iteracoes/stage1-referencias-20260911` | estagio 1 = referencias coletadas |

O carimbo `20260911T...Z` foi **mantido como sufixo** de proposito: ele e a unica
informacao de ordem de geracao entre estagios do mesmo dia (052357Z < 053435Z) e
torna a renomeacao reversivel e auditavel. Nomes funcionais iguais sem carimbo
colidiriam em uma proxima rodada.

Detalhes e justificativa tambem em `_fora-do-repo/_backup-organizacao-20260911/RENOMEACOES.md`.

## 7. Diagnostico arquivado (movido, nao apagado)

| de | para | por que |
|---|---|---|
| `exports/concepts/optical-rig-r05/camera-mount-din-v1-interferencia.step` | `exports/concepts/optical-rig-r05/_diagnostico/camera-mount-din-v1-interferencia.step` | **174 solidos**; resultado bruto de ensaio de interferencia do v1, nao e peca. Explicacao em `_diagnostico/LEIA-ME.md` |

## 8. Backup / manifesto

`_fora-do-repo/_backup-organizacao-20260911/` contem:

| arquivo | o que e |
|---|---|
| `pre-manifest.tsv` | 2 157 arquivos com caminho, kind, bytes, mtime_ns, modo, uid/gid e **sha256 antes** de qualquer mudanca |
| `pos-manifest.tsv` | o mesmo conjunto depois, mais os arquivos novos |
| `baseline.json` | HEAD do git, `git status`, contagens e `du` por diretorio |
| `verificacao-pos.json` | as 3 provas de que nada se perdeu (ver secao 8.1) |
| `probe-solids-freecad.json` | saida bruta do FreeCAD headless da secao 9 |
| `gitignore-context.txt` | porque os diretorios de staging nao apareciam no `git status` |
| `RENOMEACOES.md` | mapa nome antigo -> nome novo e por que `mv` (nao `git mv`) |
| `pos-rename-untracked.txt` | `git status` do repo pai depois das renomeacoes |
| `manifest-organizacao-20260911.tar.gz` | este diretorio empacotado (241 kB) |

### 8.1 Prova de que nada se perdeu

- **Caminho a caminho**: os 2 157 arquivos de antes continuam existindo (ja com o
  nome novo, quando aplicavel), com **tamanho e sha256 identicos**. Ausentes: 0.
  Divergentes: 0. Unica excecao esperada: o STEP de diagnostico, que mudou de
  caminho (foi movido, hash identico).
- **Multiset de sha256**: todo hash que existia antes existe depois. **0 hashes sumiram.**
- **Contagem CAD** (`.step/.stp/.stl/.3mf/.fcstd/.fcbak/.brep`): **569 antes, 569 depois**.
- **Total de arquivos**: 2 157 -> 2 168 (+11). Todos os 11 sao adicoes: 5 desta
  organizacao e 6 de workstreams paralelos (o `portico-montantes-*`). Nenhuma remocao.
- **Git**: HEAD `5ca5ec9fabdcc02867c1cd8d327b1d96851033e8` intacto, nenhum
  `add/commit/push/merge/revert/reset`, nenhum `git clean`, nenhum arquivo
  rastreado alterado ou removido.
- O `RELATORIO.md` dos reprovados (R06/R07) tem sha256 identico ao de antes: o
  aviso foi **adicionado ao lado**, nao dentro.

## 9. Verificacao independente (FreeCAD headless 1.1.1, 2026-09-11)

Medido com `Part.Shape().read(<STEP>)`; nao pelos relatorios:

| STEP | solidos | volume (mm3) | BREP valido |
|---|---|---|---|
| `peca-dupla-plataformas.step` | 1 | 22 762,88 | sim |
| `base-v2.step` | 10 | 52 664,32 | sim |
| `base-candidate.step` | 10 | 52 797,70 | sim |
| `camera-mount-din-v6.step` | 1 | 8 787,23 | sim |
| `camera-mount-din-v1.step` | 1 | 10 375,88 | sim |
| `camera-mount-din-v3.step` | 1 | 9 617,56 | sim |
| `camera-mount-din-v1-interferencia.step` | **174** | 91,76 | sim |
| `cantoneira-topology-only.step` | 1 | 10 192,52 | sim |

Os numeros batem com a revisao. A leitura de 174 solidos foi o que classificou
`camera-mount-din-v1-interferencia.step` como lixo de diagnostico.

## 10. Pendencias e avisos que esta organizacao NAO resolve

1. **`.gitignore` do repo pai**: as renomeacoes tiram os dois diretorios de
   staging do ignore (`cad-workspace/candidate-audit-*/` e
   `cad-workspace/structural-candidate-*/` nao casam mais). Eles passam a
   aparecer como nao rastreados no `git status` do repo pai. **Nenhum comando
   git de escrita foi executado.** Se quiser preservar o comportamento antigo,
   acrescentar ao `/home/<usuario>/tcc-pnaat/github/.gitignore`:
   `cad-workspace/auditoria-r07-*/` e `cad-workspace/base-estrutura-*/`.
   `stage0-referencias-*` e `stage1-referencias-*` continuam ignorados
   (`**/stage0-*/`, `**/stage1-*/`). Lista do que ficou visivel:
   `_fora-do-repo/_backup-organizacao-20260911/pos-rename-untracked.txt`.
2. **Nomes antigos ainda citados dentro de arquivos** (conteudo preservado por
   instrucao; o mapa de renomeacao esta na secao 6): `stage0-referencias-*/`:
   `git-status-before.txt`, `execution.log`,
   `verification.json`; `auditoria-r07-*/`: `baseline.json`, `build.log`,
   `closeout.json`; `base-estrutura-*/`: `baseline.json`, `probe.log`,
   `RELATORIO-BASE-V2.md`, `RELATORIO-DOIS-JEITOS.md`. Sao registros historicos.
3. **Itens de projeto abertos** (nao sao divida de arquivo): medir a esteira
   (decide CFG1/CFG2), montantes + travessa do portico (workstream paralelo),
   fixadores reais (rosca/torque), cargas/vibracao/rigidez/fadiga, ensaio
   fisico, cameras/Pi/cabos/trigger.

---

## 11. Hashes (sha256) dos artefatos citados

| artefato | bytes | sha256 |
|---|---|---|
| `iteracoes/base-estrutura-20260911T053435Z/peca-dupla-plataformas.step` | 492062 | `640823f4ea1c08b17f0f842219ac1891e9128945a9fb91ffd368377842db53d2` |
| `iteracoes/base-estrutura-20260911T053435Z/base-v2.step` | 3387939 | `1c0d526d0e20ba866ffd8fba378a11a96448979e7f0ea1fa5d22de787238b8be` |
| `exports/concepts/optical-rig-r05/camera-mount-din-v6.step` | 5705015 | `8a3b9f45192a9187df5d8d1d4fc9f8154dda136e5e18c601b5a05fdd66c932f4` |
| `iteracoes/auditoria-r07-20260911T052357Z/cantoneira-topology-only.step` | 15252 | `0a9be691c8e90e7b0fc852c4633ec9e1e9c60f3056f376e10cd4deb623e54fad` |
| `exports/concepts/optical-rig-r05/_diagnostico/camera-mount-din-v1-interferencia.step` | 7806129 | `465d35962ffe23a1b4470d18fdf7f5c966aba57d6fd32f8f013dbadf5246c9d6` |
| `reports/R05-CAMERA-MOUNT-DIN.md` (laudo, original) | 3399 | `495bfb5e4f314a634a8ff0d6758e47b6118a712872b68c64950bf8acac3bc4bb` |

---

## 12. Camera lateral no trilho DIN (trabalho de 2026-09-12 a 09-14)

Organizacao aplicada em 2026-09-14: as 12 versoes tentadas foram movidas
para `iteracoes/camera-lateral-p5v04a-20260913T223424Z/versoes-descartadas/`, cada uma
com um `REPROVADO.md`. **Nada foi apagado.** Backup e manifesto reversivel:
[`_backup-organizacao-20260914/`](_backup-organizacao-20260914/).

### 12.1 Conjuntos no topo

| conjunto | caminho | veredito | por que |
|---|---|---|---|
| candidato lateral | `iteracoes/candidato-lateral-20260914T093302Z/` | **PASS_GEOMETRY_ONLY** | 41 gates geometricos; 6 pecas separadas, malhas fechadas, maior 213x79x40 mm. **Nao liberado fisicamente** |
| auditoria da v12 | `iteracoes/revisao-impressao-20260914T092304Z/` | **AUDITORIA** | reprovou a v12 por leitura real: M5 sem material ao redor, parafuso perpendicular a rachadura, inercia no eixo errado |
| projeto camera lateral | `iteracoes/camera-lateral-p5v04a-20260913T223424Z/` | **FONTES** | malhas do 3MF, Redux, e as 12 versoes descartadas |

### 12.2 Veredito por versao (detalhe em `versoes-descartadas/INDICE.md`)

| versao | veredito | por que |
|---|---|---|
| `din-case` (v1) | REPROVADO | exportacao com o `camera_arm` rotacionado 90 em X; nao encaixa no swivel |
| `din-case-v3` | VAZIO | sem artefatos |
| `din-case-v4` | REPROVADO | frame errado: camera apontando para cima, sobre a esteira |
| `din-case-v5` | REPROVADO | mount colidia com o trilho; M5 sem material ao redor |
| `din-case-v6` | SUPERSEDIDO | usava o arm; mount ia para tras e voltava (88 913 mm3) |
| `din-case-v7` | SUPERSEDIDO | 25 745 mm3, mas placa em paisagem |
| `din-case-v8` | SUPERSEDIDO | um unico labio; lado -X do trilho aberto |
| `din-case-v9` | SUPERSEDIDO | enquadramento errado: paisagem cobre 204 mm |
| `din-case-v10` | DESCARTADO | experimento de retrato, interface nao resolvida |
| `din-case-v11` | SUPERSEDIDO | retrato 376 mm com tirante chato (91 054 mm3, f1 63 Hz) |
| `din-case-v12` | REPROVADO | reprovada pela auditoria de 09-14 |
| `mount-braco-20260912` | REPROVADO | primeira tentativa; frame errado |

### 12.3 Achados que corrigem claims anteriores

1. **A junta do autor funciona.** `camera_arm` + `cam_swivel` na pose do 3MF:
   contato **28,8852 mm2**, colisao **0,000000 mm3**. Era essa a junta a usar.
2. **O montante NAO tem perfil incompativel.** Secao em Y=320/340: contorno
   unico continuo **35 x 7,5 mm, area 45,768141 mm2**. Os "dois lobulos"
   eram cortes atraves das perfuracoes. O claim contrario, que eu escrevi,
   esta retratado aqui.
3. **O 2L tem 345 mm**, nao os 240 mm do `product_envelope` do contrato.
   Com o FOV real da OV5647 (53,50 x 41,41 graus) e distancia ao centro,
   o minimo condicional para H345/D105 e **394,733729 mm**; 376 mm nao serve
   para esse envelope.
4. **A inercia da v12 estava no eixo errado**: 6 858,666667 mm4 com gravidade
   em Y, nao 128 610,666667. Nenhuma alegacao de frequencia ou de "113x"
   feita antes disso se sustenta.

### 12.4 Pendencias que esta organizacao NAO resolve

1. Encaixe fisico da P5V04A: a placa nunca foi medida; o housing fonte e da
   familia v2. Sem isso nao ha como fechar a case.
2. Datum real do produto: `base Y=150` e `Z=-5` sao poses de preview,
   nunca medidas. Sem eles nao se fecha a distancia.
3. Retencao interna housing-swivel da referencia nao qualificada.
4. Tolerancias de impressao, cupom de encaixe, carga, torque, vibracao e
   percurso do cabo FPC.

### 12.5 Hashes dos artefatos citados

| artefato | bytes | sha256 |
|---|---|---|
| `iteracoes/camera-lateral-p5v04a-20260913T223424Z/reference-recovery/camera_arm.stl` | 96384 | `ed205891675b87b73ecc04cae2a39cbc75171f3c7f9cd117dcea1f9a371b0e52` |
| `iteracoes/camera-lateral-p5v04a-20260913T223424Z/reference-recovery/cam_swivel.stl` | 124484 | `0b826eb188d232d502d84d1f6300e36f5de8ec17e9c3907a5280ac01f400adae` |
| `iteracoes/camera-lateral-p5v04a-20260913T223424Z/reference-recovery/cam_housing.stl` | 147284 | `6ada55f7aa3e5ec33666412fa0ea86331a662c474b26d7eb89aa69803fe7d19d` |
| `iteracoes/camera-lateral-p5v04a-20260913T223424Z/reference-recovery/cam_cover.stl` | 9284 | `b34a1a07032188aea094893d275c19d1c092ba712d1b1e74c848df98ca329813` |
| `iteracoes/revisao-impressao-20260914T092304Z/audit-readback.json` | 13509 | `7d53e15875c335cef14cbbde61eba12249a05bd3d24d5a9fe6cae71cd5b92dc7` |
| `iteracoes/revisao-impressao-20260914T092304Z/closeout.json` | 816 | `c05c4b6caecfd39d4ecf6170b196a87f40fef8374071ad9d4a8a8ad71c9d5a8b` |
| `iteracoes/candidato-lateral-20260914T093302Z/verification.json` | 17211 | `abb4797f274c08638534c5daf682ef9ffa91deed1d35c30349f0e26e444ef71b` |
| `iteracoes/candidato-lateral-20260914T093302Z/closeout.json` | 3320 | `cb5b6cab9cd532832a950f30b3c5faa00c8faada831680ead8bd0a3ace598bf8` |

---

## 13. Base do trilho com encaixe do bracket (trabalho de 2026-09-14)

Documentacao consolidada: [`iteracoes/base-bracket-20260914/DOCUMENTACAO-20260914.md`](iteracoes/base-bracket-20260914/DOCUMENTACAO-20260914.md)

### 13.1 Entregavel para impressao

| artefato | caminho | estado |
|---|---|---|
| base (para fatiar) | `iteracoes/base-bracket-20260914/print/base-somente.stl` | 256 284 bytes, 5 124 triangulos, estanque |
| base (STEP) | `iteracoes/base-bracket-20260914/print/base-somente.step` | em orientacao de impressao |
| base (frame do projeto) | `iteracoes/base-bracket-20260914/base-bracket.step` | Y vertical, 1 solido |

    131,00 x 103,50 x 36,50 mm · 241 237,165 mm3 -> 306,4 g PETG · cabe na K1C
    face de apoio 11 952,14 mm2 · vao do bracket com 0,30 mm/lado
    furo do parafuso Ø6,5 eixo Z em X=-30,50 / Y=29,00

### 13.2 Partiu do que funcionava

`gripA-bracket` (= `m6-bracket`, ja impresso pelo usuario) entrou INTACTO:
unico final de trilho que engata no MontanteA com colisao 0,000000 mm3 e
engate de 5,50 mm. `gripA-clamp` colide 183,4384; `gripA-peca` colide 16,4972;
`peca-dupla-plataformas` / `m6-peca` tem plataformas = tem perna.

### 13.3 Ferragem

    M6 x 50 + arruela M6 O12 (1,60) + porca M6 (5,00)
    material no caminho 29,40 mm + arruela + porca = 36,00 mm necessarios

### 13.4 Portao de impressao

    estanque, normais para fora, 0 degenerados
    volume da malha vs CAD: 0,0005% de diferenca
    overhangs 338,46 mm2, TODOS pontes (4 rebaixos O9 + arco do furo M6)
    VEREDITO: PRONTO PARA IMPRESSAO

### 13.5 Pendencias

    Y=0 e suposicao de piso, nao medicao; regerar se a altura real for outra
    tempo de impressao nao medido (nao fatiado)
    parafuso real nao conferido (assumido M6 pelo nome e pela haste de 30 mm)
    caminho de carga nao analisado
    o trilho verga antes da base (7,48 mm de parede contra 35 mm de largura)
