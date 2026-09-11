# Reconciliação com o GitHub — refs que não estavam integradas (2026-09-11)

Escopo: o que existia nos refs remotos do `origin` e não estava na `main` local. Método: `git cherry`
(patch-id), `git diff --diff-filter=A/M` contra a `main`, comparação por arquivo de três revisões
(merge-base, `main`, ramo) e `git log` de quem tocou cada documento. Leitura apenas, exceto o que
está declarado como integrado abaixo.

## 1. Refs remotas e situação

| ref | commits exclusivos | situação verificada |
|---|---|---|
| `origin/main` | 0 | ponto de partida |
| `codex/gravar-videos-das-pocs-funcionando` | 0 | já contida na `main` |
| `codex/gravar-videos-das-pocs-funcionando-q9uv89` | 1 (`d1cd46c`) | **integrada nesta rodada** (roteiro detalhado + índice de vídeos) |
| `codex/localizar-partes-concluidas-do-cad` | 0 | já contida na `main` |
| `codex/localizar-partes-concluidas-do-cad-2idh2t` | 2 (`4a7bbde`, `6bc0f64`) | conteúdo superado; ver §3 |
| `miguelw11-patch-1`, `-1-1`, `-1-2`, `-1-5`, `-1-6`, `-1-8` | 7 commits sem equivalente por patch-id | parcialmente superado; ver §3 e §4 |
| `miguelw11-patch-1-3`, `-1-4`, `-1-7`, `-1-9`, `-1-10` | 0 | mergeados na `main` pelos PRs #13, #15, #17 e seguintes (`b487d34`, `b5a46cd`, `5ef04b8`) |

O commit `d8ec1e5` (`docs: consolidar decisões de fusão e sensores candidatos`) tem gêmeo na `main`
(`01f4cb3`, mesmo assunto) — a mesma rodada de trabalho entrou por outro caminho.

## 2. Integrado nesta rodada

| arquivo | origem | evidência |
|---|---|---|
| `code-workspace/src/pocs/ROTEIRO-GRAVACAO.md` | `d1cd46c` | a versão da `main` (215 linhas) é **subconjunto** da do ramo (569 linhas): 1 linha divergente, 264 linhas de detalhe que só existiam no ramo |
| `evidencias/videos/README.md` | `d1cd46c` | stub de 2 linhas na `main` → convenção de índice de evidência de vídeo (31 linhas), com manifesto, hash e estado `MEASURED`/`VALIDATED` |
| `latex-workspace/referencias.bib` | `92ca071` | arquivo ausente na `main` |
| `latex-workspace/texto/aceite.tex` | `92ca071` | arquivo ausente na `main` (seção de critérios de aceite) |
| `latex-workspace/main.tex` | `92ca071` | adicionadas as 4 linhas de bibliografia: `\addbibresource`, `\input{texto/aceite}`, `\nocite`, `\printbibliography` (as demais linhas da `main` foram preservadas) |
| `latex-workspace/preamble.tex` | `92ca071` | adicionado o pacote `biblatex` (`backend=biber`, `style=authoryear`); o resto do preâmbulo da `main` foi preservado (o ramo remove `etoolbox`, `xcolor[table]` e os ajustes de tabela — não foram revertidos) |

**Não verificado:** o build LaTeX. Não há `pdflatex`, `latexmk` nem `biber` no host de trabalho, então a
integração acima é sintática e por dependência declarada, não compilada.

## 3. Não integrado — `main` é a sucessora

| arquivo | merge-base | `main` | ramo | por quê |
|---|---|---|---|---|
| `docs/arquitetura.md` | 165 | 39 | 516 | a `main` encurtou de propósito em `2e32af5` (57 inserções / 290 deleções em escopo+arquitetura) |
| `docs/escopo.md` | 142 | 35 | 215 | idem |
| `docs/requisitos.md` | 128 | 67 | 137 | substituído pelo conjunto `docs/requisitos/*.md` |
| `docs/DECISIONS.md` | 184 | 439 | 301 | `main` é sucessora (D-01 a D-28 + emendas) |
| `docs/requisitos/01-funcionais.md` | 296 | 371 | 296 | ramo não avançou sobre a base |
| `docs/requisitos/02-nao-funcionais.md` | 181 | 236 | 181 | idem |
| `docs/requisitos/04-atuacao-seguranca.md` | 95 | 98 | 66 | idem |
| `docs/dados-telemetria.md` | 174 | 194 | 179 | idem |
| `README.md`, `docs/README.md` | — | — | — | reescritos na `main` em `49513ba` |
| `cad-workspace/scripts/freecad_r05_v7_preview.py` | ausente | 141 | 127 | entrou na `main` pelo PR #18 (`cfccb9a`) e evoluiu depois |
| `docs/pocs/README.md` | 69 | 50 | 71 | a `main` tem o estado verificado do ensaio; o ramo traz um protocolo de PoC (conteúdo distinto, não superior) |

## 4. Não integrado — higiene de publicação

| arquivo | o que o ramo tem | decisão |
|---|---|---|
| `cad-workspace/reports/GRIP-MDF-FDM-DECISION-R01.md` e `.json` | caminhos absolutos `/home/<usuario>/...` de fotos de bancada | mantidos fora: a `main` removeu esses caminhos de propósito |
| `cad-workspace/data/g0/photo-inventory-r02.json`, `-r03.json`, `esteira-b-g0-photo-r02.yaml` | idem | idem |
| `latex-workspace/tabelas/requisitos.tex` | arquivo novo no ramo | órfão no próprio ramo: nenhum `\input` aponta para ele |

## 5. Preservação

Nenhuma branch foi apagada, renomeada ou reescrita; nenhum ref remoto foi alterado; nada foi
empurrado para o `origin` nesta rodada. Os refs acima continuam disponíveis para consulta item a item.
