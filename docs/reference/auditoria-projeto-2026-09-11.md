# Auditoria do projeto PNAAT — incongruências e melhores abordagens (2026-09-11)

Base: estado real do repo em `cd54d98` (12 commits à frente do origin, nada pushed).

## Panorama (5 frentes)

| Frente | Onde | Estado |
|---|---|---|
| Documento entregue | `latex-workspace/` | Entrega 1 publicada (12 pág.), visibilidade/rastreabilidade |
| Normativos | `docs/` | **duas gerações** convivendo (núcleo entregue × versão rica antiga) |
| CAD/rig | `cad-workspace/` | workstream paralelo (R05 óptico, stages novos) |
| Código | `code-workspace/` | PoCs 01–07 + final, `preproc.py`, scripts (gate/doctor), 16 testes |
| Dados | `datasets/pnaat/` (fora do git) | origem 81, normal 81, defective 0, gerados 0 |

## Incongruências (com evidência)

**P1**
1. **Duas gerações de requisitos.** `docs/requisitos.md` (núcleo: 30 RF/21 RNF, visibilidade) coexiste com
   `docs/requisitos/01-funcionais.md` (29 KB) e `04-atuacao-seguranca.md`, que descrevem **atuação, encoder
   KY-040, iluminação estroboscópica, fita retrorrefletiva, 3 câmeras** — contradiz a Entrega 1 entregue
   ("sem atuação física", "não controla a velocidade da esteira") e o rig atual (2 câmeras).
2. **PoCs defasados nos docs.** `docs/pocs/` tem `01-classificador-topo`, `03-sincronizacao-fisica`,
   `04-correlacao-multi-no`, `07-atuacao-confirmada`; o entregue usa 01 captura multi-view, 02 tampa,
   03 deformidade, 04 identidade/fusão, 05 registro, 06 resiliência, **07 dashboard**. Rastreabilidade quebrada.
3. **Imagens de resultado dentro do repo, não ignoradas.** `code-workspace/notebooks/results/**` (centenas de
   PNG do MVTec) aparece como untracked — o `doctor` só checa **arquivo rastreado**, então isso passaria.
4. **Commit mal rotulado.** `80df6e9` tem mensagem de guards mas conteúdo = untrack de um `.step`
   (128.749 linhas); `cd54d98` repete a mesma mensagem. Dois commits com o mesmo título, um deles mentindo.
5. **Arquivos normativos root-owned** (`docs/requisitos/01-funcionais.md`, `02-nao-funcionais.md`) → edição
   por `nerton` falha (mesma classe do erro de `.git/objects`).

**P2**
6. **Ambiente duplo sem regra única:** `code-workspace/.venv` (py3.14, rota do `make test`) × `github/.venv`
   (py3.11, anomalib/visão). Já causou execução no venv errado. `doctor` cobre só o segundo.
7. **Notebooks não versionados** (`*.ipynb` ignorado) e agora **duplicando** o que os scripts testados fazem
   — risco de drift; o canônico tem que ser o script com teste.
8. **`preproc.py` na raiz do pacote `pocs`**, quebrando a convenção "um diretório por PoC", e **sem PoC
   registrado** de pré-processamento/geometria nos docs.
9. **Dataset não treinável ainda:** `defective = 0`; `entrada` só tem pares rejeitados; labels de IA são
   triagem (2 falsos positivos comprovados) — a classe `defective` depende dos patches compostos.
10. **Sem calibração mm** (Charuco/objeto de referência) → RF-15/RNF-14 **não mensuráveis**; sem rig v1
    (backlight/polarização) → robustez PET não medida.
11. **Split por sessão impraticável hoje** (81 frames de 1 sessão): split por frame vaza (mesma garrafa/cena).
12. **Symlink `dataset/`** no repo (conveniência) só documentado no `.gitignore`.

## Melhores abordagens (decisões recomendadas)

1. **Uma fonte de verdade por domínio.** Manter `docs/requisitos.md` + `docs/requisitos/02-nao-funcionais`
   como **núcleo**; mover o resto (atuacao/encoder/estroboscopia/3 câmeras) para `docs/backlog/` com header
   "fora do escopo entregue". Não apagar (é evidência de análise), mas parar de tratá-lo como normativo.
2. **Reconciliar PoCs:** renomear `docs/pocs/*` para os PoCs entregues (ou criar `docs/pocs/MAPA.md` com
   de-para), preservando histórico — a rubrica olha o PDF, mas a rastreabilidade interna precisa fechar.
3. **Higiene automatizada:** `.gitignore` para `notebooks/results/` + hook `pre-commit` que roda
   `doctor --rapido` (mídia rastreada, `.git` gravável, root-owned). Guarda onde a falha acontece.
4. **Reescrever os 2 commits locais** (não pushed) para consertar a mensagem do `80df6e9` e/ou squashear —
   janela segura: nada foi publicado.
5. **`chown -R nerton` nos arquivos root-owned** e adotar a regra "todo artefato nasce como nerton"
   (já usamos `runuser -u <usuario> -- cp`; falta varrer o legado).
6. **Unificar venv:** aposentar `code-workspace/.venv` (3.14) e rodar tudo no `github/.venv` (3.11), com
   `make test` usando o mesmo `AI_PY`. Menos superfície de erro, um `doctor` só.
7. **Mover `preproc.py` → `src/pocs/poc08_preproc/`** e registrar o PoC-08 (pré-processamento/geometria
   determinística) no doc de PoCs — é o que a rubrica chama de "função prevista dos recursos".
8. **Fechar a decisão de modelo em `DECISIONS.md`** (híbrido: geometria determinística → classificador
   leve → one-class condicional), com estado e critério de fechamento — hoje está como recomendação solta.
9. **Dataset como código:** raw canônico + `rig-<id>.yaml` + `pipeline_version` no manifest + cache
   descartável; composição do patch no raw; gate de isolamento; split por sessão (quando houver >1).
10. **Prioridade técnica:** (a) gerar patches (modo B) → compor → gate → `defective`; (b) treinar e medir no
    **nosso** dataset; (c) calibrar mm (Charuco) para destravar RNF-14; (d) só então rig v1 (backlight +
    polarização) conforme o deep research. Não inverter essa ordem: sem dado próprio, qualquer métrica é
    sobre MVTec (domain gap já comprovado) ou sobre defeito sintético não validado em realismo.

## Ordem sugerida de execução (curta)

1. Higiene (P1-3, P1-4, P1-5) — 1 commit.
2. Reconciliar docs (P1-1, P1-2) — 1 commit por frente.
3. Unificar venv + mover `preproc.py` (P2-6, P2-8) — com revisão.
4. Retomar o esqueleto do dataset (rig-v0 → manifest → split) e o fluxo dos patches.

> Nota de namespace (2026-09-16): o diretorio mecanico se chamava `cad-workspace` na
> data deste documento; hoje e `cad-produto`. O texto abaixo foi preservado como registro.
