# Runbook: erros encontrados e guardas implementadas (PNAAT)

---

## Erros 18-25 — sessao 2026-09-11 (forense + auditoria)

Formato: erro -> causa -> guarda. Os oito primeiros vem da forense da sessao (`sa-0`), os demais da
auditoria de autoridade (`sa-1`) e do levantamento de dados da PoC-02 (`sa-2`).

| # | Erro observado | Causa | Guarda |
|---|---|---|---|
| 18 | Afirmar "PoC-01 e o trigger" | arquivo da geracao antiga (`pocs/01-classificador-topo/`) lido pelo numero da pasta | aviso de geracao em `pocs/README.md` e `MAPA.md`; regra 1 do protocolo |
| 19 | "81 normais sao quase-duplicatas" | score de alinhamento de template em 3 frames promovido a similaridade par-a-par de 81 | regra 3 (mesma grandeza) e regra 4 (numero com `n`, unidade e selo) |
| 20 | "nao medimos a banda de ruido da geometria" | lacuna afirmada sem varrer `reference/` (o doc existia e estava indexado desde 01:50) | regra 6 (lacuna exige varredura declarada) |
| 21 | Alargar para projeto/entregas/conjectura | unidade de trabalho nao estava declarada em lugar nenhum | regra 2 + cabecalho "PoC em execucao" em `pocs/README.md` |
| 22 | "PoC-02 bloqueada pela placa USB" | bloqueio operacional de uma PoC transportado para outra | regra 7 (bloqueio nao se transporta) |
| 23 | Expansao tratada como nucleo | marca `Expansao` do catalogo ignorada; codigo escrito antes da medida | regra 8 + regra 9 |
| 24 | Commit com suite vermelha | gate ad-hoc em `/tmp`, nao versionado | regra 10 + `commit_gate.sh` versionado e ligado via `core.hooksPath` |
| 25 | Hostname do homelab commitado | hook warn-only (nao bloqueava) | regra 10 (gate bloqueante, com escape consciente) + sanitizador no gate |

Cada linha: erro → causa → guarda (onde). Atualizado 2026-09-11.

| # | Erro | Causa | Guarda |
|---|---|---|---|
| 1 | `ModuleNotFoundError: Cutpaste` / `MVTec` inexistente | anomalib 1.x vs 2.x (2.x usa `MVTecAD`, não tem CutPaste, não usa imgaug) | `scripts/doctor.py` checa versão 2.x + imports; skill registra |
| 2 | `FileNotFoundError: .../MVTecAD/bottle` no setup | download ocorre em `prepare_data()`, não em `setup()` | scripts chamam `prepare_data()` antes |
| 3 | `PermissionError: /root/results` | `default_root_dir` relativo + cwd herdado `/root` | scripts passam `default_root_dir` explícito; rodar com `cd $HOME` |
| 4 | anomalib não instala (imgaug/numpy) | python 3.14 do host | `AI_PY` fixo (py3.11) no Makefile + doctor checa versão |
| 5 | `AttributeError: ndarray.ptp` removido | numpy 2.x | usar `np.ptp()` (corrigido) + doctor WARN |
| 6 | `tenengrad = 0` | `cv2.Sobel` do OpenCV 5.0 retorna zeros | tenengrad em numpy (diferenças centrais) + doctor mostra cv2 |
| 7 | 400 `MissingSessionID` no meio da classificação | pool Gemini marcado "unhealthy" (429) → fallback opencode-go | REST direto `classificar_rest.py` + rotação de chaves/modelos + preflight `pool_disponivel()` + `--max-calls` + **aborta com código 3** se pool exausto |
| 8 | rótulos errados (deformidade em garrafa normal) | IA de visão como verdade | rótulo de IA = triagem; `defective` vem de par sintético (classe no JSON) + gate; revisão visual humana |
| 9 | `scp: Permission denied` ao sobrescrever arquivo do usuário | arquivo do dono do repo + scp como root | scp para nome novo em /tmp + `runuser -u <usuario> -- cp` |
| 10 | `zip: command not found` | não instalado no <host> | usar `tar.gz` |
| 11 | `insufficient permission ... .git/objects` | objetos root-owned | `chown -R nerton:nerton .git` |
| 12 | mídia entrando em commits | `git add -A` em dirs com imagens | `doctor.py` FAIL se houver mídia rastreada; untrack + `.gitignore` |
| 13 | symlink de dados não ignorado | `.gitignore` tinha `dataset/` (só dir) | `/dataset` explícito |
| 14 | **perda de arquivos** (2.jpg + JSONs) | `cp` falhou silencioso e `rm -rf` apagou depois | `scripts/mover_verificado.sh` (confere sha256 antes de remover) + regra: nunca `rm` antes de verificar cópia |
| 15 | contagem por classe errada no validador | usava prefixo do nome do arquivo | usa `classe` do JSON |
| 16 | gate reprovava edição perfeita por 1 px | convenção inclusiva/exclusiva de bbox | `--margin 1` no gate + convenção `x..x+w-1` documentada no prompt |
| 17 | controle do rotulador inconclusivo | quota diária free tier (429 em 5/5) | BLOCKED: reexecutar após reset (ou credencial paga/provider alternativo) |

## Estado dos fluxos após refino

- `make doctor` — ambiente/API/dados/higiene do repo (0 FAIL agora; 1 WARN informativo do numpy2).
- `make test-vision` — 16 testes (pré-processamento + gate do validador).
- `make validar` / `make dataset` / `make treino` — fluxo do dataset (gate → `defective` → treino).
- `make test` — testes das PoCs (venv do projeto).
- Classificação por IA: opcional, com preflight de quota e limite de chamadas.
- Movimentação de arquivos sensível: `mover_verificado.sh`.