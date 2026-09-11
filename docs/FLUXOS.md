# Fluxos canônicos do TCC PNAAT (refinados em 2026-09-11)

Cada fluxo tem **gate** (o que precisa ser verdade) e **evidência** (o que fica registrado).
Fluxo sem gate é opinião; gate sem evidência é promessa.

## F1 — Ingestão e verificação de referência

```
usuário aponta a fonte
  → Source Worth Gate (vale ingerir? autoridade/originalidade/acessibilidade/valor/duração)
  → capturar (PDF/browser/clone; registrar URL + commit/SHA + data)
  → verificar material a material: existe? trecho confere (verbatim)? é do domínio certo?
  → classificar status (P/S/B/X/F/N) e registrar em docs/REFERENCIAS.md
  → (vault) C1 source card → C2 source map quando virar conhecimento
```

**Gate:** nenhuma referência entra em decisão sem status `P` e trecho verificado.
**Evidência:** linha no `REFERENCIAS.md` + documento de verificação quando houver suspeita.
**Armadilhas:** alias de arquivo (checar `pdfinfo`); citação fabricada; quote truncado; número de
terceiro virando nosso.

## F2 — Dataset e pré-processamento

```
RAW canônico (datasets/pnaat/origem)
  → rig-<id>.yaml (rig_id, pipeline_version, roi, template, clahe, limiares de qualidade)
  → apply_pipeline()  [MESMA versão no treino e na inferência]
  → gate de isolamento (validar_pares.py --margin 1) para pares sintéticos
  → manifest (rig_id, pipeline_version, session_id, classe, sha256)
  → split por SESSÃO (nunca por frame) → dataset/{normal,defective}
```

**Gate:** pares passam no gate; split declarado; `pipeline_version` muda quando qualquer parâmetro muda.
**Evidência:** manifest + relatório do gate + contagens.
**Regra dura:** processado é cache descartável; RAW é a verdade.

## F3 — Medição e evidência experimental

```
pergunta binária → harness determinístico (seed fixo) → ground truth conhecido
  → medir (não estimar) → comparar com o alvo do requisito → registrar
```

**Gate:** harness tem ground truth e um caso que **pode falhar** (teste de mutação).
**Evidência:** script + resultado + doc (ex.: `medir_vies_elipse.py` +
`medicao-vies-elipse-geometria.md`).
**Regra dura:** latência, acurácia e mm só valem se medidos no nosso setup declarado.

## F4 — Higiene do repositório

```
antes de escrever: saber QUEM sou (root vs nerton) e quem é o dono do arquivo
  → criar dirs como nerton (nunca mkdir root + cp nerton)
  → scp para nome novo + runuser cp (nunca sobrescrever arquivo de nerton como root)
  → mover com scripts/mover_verificado.sh (sha256 antes de remover)
  → commit: um commit = uma intenção; sem mídia; sem -A
  → make doctor (0 FAIL) e hook pre-commit (warn-only)
```

**Gate:** `make doctor` sem FAIL; nenhuma mídia rastreada; `.git/objects` gravável por `nerton`;
`make sanitizar` sem achado salvo o que estiver **coberto por receipt** (arquivo com `.sha256`
ou listado em manifest não é saneado — o produtor regenera o receipt).
**Evidência:** `docs/reference/runbook-erros-e-guardas.md` + `docs/SANITIZACAO.md`.

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
```

**Gate:** todo doc novo entra no índice; toda decisão tem critério de fechamento.
