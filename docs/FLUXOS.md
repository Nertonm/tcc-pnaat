# Fluxos canônicos do TCC PNAAT (refinados em 2026-09-11)

Cada fluxo tem **gate** (o que precisa ser verdade) e **evidência** (o que fica registrado).
Fluxo sem gate é opinião; gate sem evidência é promessa.

## F1 — Ingestão e verificação de referência

```
usuário aponta a fonte
  → resolver o artefato NO CLONE VIVO (git fetch; behind = 0) antes de ler ou revisar
  → espelho/réplica de leitura só vale com carimbo (HEAD + hora do sync) no relatório;
     sem carimbo, re-sincronizar antes de ler e antes de delegar a auditoria
  → Source Worth Gate (vale ingerir? autoridade/originalidade/acessibilidade/valor/duração)
  → capturar (PDF/browser/clone; registrar URL + commit/SHA + data)
  → verificar material a material: existe? trecho confere (verbatim)? é do domínio certo?
  → conferir identidade do caminho: ele ainda é o vigente no HEAD?
     (documento movido ou apagado no remote invalida a revisão inteira)
  → classificar status (P/S/B/X/F/N) e registrar em docs/REFERENCIAS.md
  → (vault) C1 source card → C2 source map quando virar conhecimento
```

**Gate:** nenhuma referência entra em decisão sem status `P` e trecho verificado. Termo canônico
(cenário, classe, nome de PoC) não muda por pedido verbal: a renomeação só entra com a citação
`arquivo:linha` que hoje o define; sem citação, o texto normativo prevalece e a mudança vira decisão
registrada (D-nn), não edição de texto.
**Evidência:** linha no `REFERENCIAS.md` + documento de verificação quando houver suspeita.
**Armadilhas:** alias de arquivo (checar `pdfinfo`); citação fabricada; quote truncado; número de
terceiro virando nosso; revisar sobre cópia obsoleta (artefato movido ou reescrito no remote);
delegar auditoria sem declarar o commit lido.

## F2 — Dataset e pré-processamento

```
RAW canônico (datasets/pnaat/origem)
  → rig-<id>.yaml (rig_id, pipeline_version, roi, template, clahe, limiares de qualidade)
  → apply_pipeline()  [MESMA versão no treino e na inferência]
  → gate de isolamento (validar_pares.py --margin 1) para pares sintéticos
  → manifest (rig_id, pipeline_version, session_id, classe, sha256)
  → split por SESSÃO (nunca por frame) → dataset/{normal,defective}
  → amostra versionada: copiar com mover_verificado.sh e commitar a imagem JUNTO do
     dataset/MANIFEST.sha256 (caminho, sha256, classe, session_id, pipeline_version)
```

**Gate:** pares passam no gate; split declarado; `pipeline_version` muda quando qualquer parâmetro muda;
imagem versionada só é legítima com o manifest no índice e abaixo do teto de tamanho da política
(`code-workspace/scripts/politica_midia.py`).
**Evidência:** manifest + relatório do gate + contagens (geradas por script, não escritas à mão).
**Regra dura:** processado é cache descartável; RAW é a verdade; a cópia versionada é evidência de
método, nunca fonte de treino.

## F3 — Medição e evidência experimental

```
pergunta binária → harness determinístico (seed fixo) → ground truth conhecido
  → medir (não estimar) → comparar com o alvo do requisito → registrar
```

**Gate:** harness tem ground truth e um caso que **pode falhar** (teste de mutação); a evidência
registra o **código de saída** da execução, não só a saída textual.
**Evidência:** script + resultado + doc (ex.: `medir_vies_elipse.py` +
`medicao-vies-elipse-geometria.md`) + `rc=` do comando.
**Regra dura:** latência, acurácia e mm só valem se medidos no nosso setup declarado.
**Regra dura (execução remota):** verificação não termina em pipe de formatação. Forma canônica:

```bash
ssh <host> "runuser -u <usuario> -- bash -lc 'cd <caminho> && <comando>'" > /tmp/out.txt 2>&1
rc=$?; tail -20 /tmp/out.txt; [ $rc -eq 0 ] || exit 1   # o rc que importa é o do comando
```

Contadores parciais não são evidência: citar a linha de resultado completa e o código de saída
(ex.: `RESULTADO: 0 achado(s)` com `rc=0`), nunca um subconjunto de categorias.

## F4 — Higiene do repositório

```
antes de escrever: saber QUEM sou (root vs dono do repo) e quem é o dono do arquivo
  → criar dirs como o dono do repo (nunca mkdir root + cp de terceiro)
  → scp para nome novo + runuser cp (nunca sobrescrever arquivo de terceiro como root)
  → mover com scripts/mover_verificado.sh (sha256 antes de remover)
  → antes de editar: o arquivo é coberto por receipt (.sha256/manifest que CONFERE)?
     se sim, editar e regenerar o receipt no MESMO commit
  → mexi no Makefile? rodar TODOS os alvos antes de commitar (make test test-vision doctor
     demo poc04 sanitizar) e conferir que nenhum alvo aponta para arquivo fora do índice
  → commit: um commit = uma intenção; sem mídia; sem -A
  → make doctor (0 FAIL) e hook pre-commit BLOQUEANTE (instalar com make hooks; hooksPath é
     config local e não é herdada por clone)
  → bypass só com motivo declarado: PNAAT_HOOK_BYPASS='<motivo>' + trailer `Bypass: <motivo>`
     na mensagem do commit (o pre-commit registra a linha em .git/pnaat-bypass.log)
```

**Gate:** `make doctor` sem FAIL; nenhuma mídia rastreada fora da exceção declarada em
`docs/SANITIZACAO.md`; `.git/objects` gravável pelo dono do repo; `make sanitizar` sem achado
**novo** (dívida antiga é reportada como dívida, não como bloqueio) salvo o que estiver
**coberto por receipt** (arquivo com `.sha256` ou listado em manifest não é saneado — o produtor
regenera o receipt); nenhum caminho citado em alvo do Makefile existe fora do índice;
`core.hooksPath` aponta para `code-workspace/scripts/git-hooks`.
**Evidência:** `docs/reference/runbook-erros-e-guardas.md` + `docs/SANITIZACAO.md` + `.git/pnaat-bypass.log`.

## F5 — Auditoria de perdas (repetível)

```
scripts/auditar_referencias.py
  → pastes PNAAT x docs/reference   (paste relevante sem captura?)
  → sessões x REFERENCIAS.md        (termo citado em sessão e ausente do registro?)
  → vault PNAAT x mapa do repo      (nota canônica sem índice?)
  → higiene (mídia/dono/objetos)
```

**Gate:** script sai com código ≠ 0 quando há achado; `--selftest` prova que ele **detecta** um
achado sintético (senão é teatro).

## F6 — Escrita no vault (canônico do projeto)

```
preflight_check()  (camada do agente, fora do repo)
  → CHANGE_RECORD completo (schema_version, change_id, idempotency_key, artifact_type,
     operation, target, expected_preimage, content, readback_token, provenance, index_policy)
  → sha256 do content EXATO (sem newline final) → validate_change
  → submit_change → get_receipt (gates) → readback físico do arquivo no owner
```

**Gate:** receipt com promoção e sha físico igual ao submetido.
**Regra dura:** sem preflight/preimage/digest/readback não há `WRITE_COMPLETE`; SSH é sonda, não
writer; nunca criar cache local no lugar da escrita canônica.

## F7 — Documentação e histórico

```
achado → doc em docs/ (com data e evidência) → índice em docs/README.md
  → decisão → docs/DECISIONS.md (D-nn) com estado e critério de fechamento
  → histórico preservado: rótulo/índice/mapa, nunca reescrever commit
  → toda afirmação de documento entregável carrega origem (arquivo:linha) ou é marcada
     como meta/roadmap; nome próprio, contagem e capacidade sem origem não entram no texto
```

**Gate:** todo doc novo entra no índice; toda decisão tem critério de fechamento; README e índice são
artefatos avaliados e seus números (contagem de decisões, o que existe e o que não existe) são
conferidos contra o repositório antes de entregar.
