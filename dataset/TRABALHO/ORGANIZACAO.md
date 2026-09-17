# Organização de `dataset/TRABALHO`

Estado: mapa de autoridade. Não autoriza apagar, mover ou executar scripts. Atualizado em 2026-09-15.

## Regra de leitura

`TRABALHO` contém material ativo, candidatos, ferramentas históricas e backups. Um arquivo existir não
prova que é parte da pipeline. Antes de executar, consultar este mapa e o fluxo em
`../../docs/design/fluxo-execucao-atual-pnaat.md`.

## Superfície ativa

| Grupo | Arquivos | Papel | Saída/autoridade |
|---|---|---|---|
| Contrato humano | `README.md`, `RUBRICA.md`, `RESPOSTAS-DO-RESPONSAVEL.md`, `anotadores.csv` | instruções e vocabulário | revisão humana |
| Filas | `wp-B`, `wp-E1`, `wp-E2`, `wp-F`, `wp-G`, `wp-J` | tarefas declaradas | Label Studio ou HTML, nunca treino direto |
> **Nota de caminho:** os scripts canônicos de export/frescor vivem em `src-production/treino/`; as cópias em `dataset/TRABALHO/` são histórico. Fluxo completo em `docs/reference/uso-do-label-studio.md`.

| Exportação | `exporta_anotacoes.py`, `anotacoes-ls.csv`, `_exportacoes/` | Label Studio para CSV canônico | `anotacoes-ls.csv` + recibo |
| Validação de fila | `gerar_filas.py`, `gerar_ferramenta.py`, `validar_entrega.py`, `juntar_entregas.py`, `bateria_validacao.py` | gera/consolida/confere entrega humana | CSV validado |
| Montagem lateral | `monta_v0_detector.py` | gera candidato YOLO lateral | dataset/manifest lateral separado |
| Treino lateral | `treina_v0_detector.py` | treina candidato v0 lateral | `<diretório de modelos>/...` |
| Montagem topo | `monta_v0_top.py` | gera candidato topo separado | dataset/manifest topo separado |
| Treino topo | `treina_v0_top.py` | treina candidato topo | `<diretório de modelos>/...` |
| Split | `t3b_split.py` | candidato de split, ainda deve ser reconciliado com o split canônico | receipt obrigatório |

## Candidatos e histórico, não executar por padrão

| Grupo | Arquivos/pasta | Motivo |
|---|---|---|
| Classificador legado | `treina_tampa.py`, `treina_prototipo.py`, `exporta_modelo.py`, `finetune.py` | escritores concorrentes de `modelo-inferencia.*` |
| Experimentos exploratórios | `ab_vista_topo.py`, `experimento_*.py`, `compara_extratores.py`, `calibra_abstencao.py` | resultados históricos, não pipeline canônica |
| Pré-anotação antiga | `pre_anota_filas.py`, `montar_deteccao_tampa.py`, `smoke_detector_tampa.py` | pesos/caminhos antigos e geometria previamente defeituosa |
| Corpo | `monta_corpo.py`, `treina_corpo.py`, `le_smoke_corpo.py` | candidato apenas; domínio próprio ainda não valida corpo |
| Runtime legado | `servico_inferencia3.py`, `pagina.html` | serviço anterior; não é o mesmo contrato do site v0 no rig |
| Metadados one-off | `atualiza_meta_lateral.py`, `atualiza_meta_run.sh`, `fecha_top_metadata.py`, `resume_v0_lateral.py` | efeitos no import ou redundância; preservar até migração deliberada |
| Auditorias one-off | `revisao*.py`, `inventario_sessao.py`, `quantifica_polygon.py`, `teste_fix_polygon.py` | evidência histórica, não ferramenta de runtime |
| Backup/patch/ferramenta gerada | `_backups/`, `_patches/`, `_ferramentas/` | preservação e reprodução histórica; não reclassificar como fonte |


## Pipeline medido v1 (2026-09-15): superfície ativa

Família que produz os números do relatório `docs/reference/resultados-deteccao-20260915.md`.
Regra de validade embutida: base limpa (pré-treino só externo) + split por item com
quase-duplicata + k-fold como medida de aceitação.

| Grupo | Arquivos | Papel | Saída/autoridade |
|---|---|---|---|
| Export canônico | `exporta_anotacoes.py`, `guarda_frescor.py` | Label Studio -> CSV + recibo; aborta se o LS avançou | `anotacoes-ls.csv` + recibo com fingerprint |
| Montagem | `monta_v1_detector.py` | split por ITEM + quase-duplicata (dHash) + ROI por câmera | `dataset/manifest.json` com gates |
| Domínio | `oversample_dominio.py` | listas por domínio (rig x externo) e super-amostragem | listas `*.txt` no dataset |
| Treino | `treina_v1.py` | base limpa -> ajuste fino; args versionados por tag | `pnaat-modelos/<tag>/model-meta.json` |
| Avaliação | `avalia_por_dominio.py`, `avalia_limiares.py` | mAP por domínio/classe; P/R/F1 por limiar | JSONs de avaliação |
| Aceitação | `kfold_por_item.py` | k-fold por item (listas separadas, asserção de disjunção) | `kfold-*.json` + listas em `dataset/kfold-listas/` |
| Evidência | `evidencia_candidato.py`, `leitor_resultados.py` | decisão por imagem, mosaico e leitura dos JSONs | `evidencia-*.{json,png}` |
| Aumento | `aumenta_offline.py` | 3x no split de treino, com proveniência e dedup | cópias + registro no manifest |
| Filas | `filas/fila_limpa.sh`, `filas/fila_final.sh`, `filas/fila_v7.sh` | encadeiam a cadeia sem disputar GPU | logs em `pnaat-modelos/fila-*.log` |
| Resultados | `_resultados-20260915/` | JSONs de evidência do dia + índice com shas | evidência com estado de validade |

## Guardas de execução (acrescentadas hoje)

7. Métrica só com listas de treino e validação **separadas e verificadas** (asserção de disjunção).
8. Nenhum peso que já viu o teste pode servir de base de avaliação (base limpa ou nada).
9. Descarte de item no montador é **contado por motivo**; descarte silencioso é bug.
10. Limiar se escolhe em validação, nunca no teste.

## Organização física futura, ainda não executada

Não mover agora, pois o worktree tem alterações de outras frentes. Quando houver allowlist e commit
separado, o destino é:

```text
TRABALHO/
  contratos/       # README, rubrica, vocabulário e decisão humana
  filas/           # wp-*.csv ativos
  exportacao/      # exportador, recibos, anotadores
  validacao/       # gerar/validar/juntar/bateria
  pipeline/
    lateral/       # monta + treina v0 lateral
    topo/          # monta + treina topo
    split/         # construtor e guard de split
  historico/       # scripts superados, revisões e one-offs
  _backups/        # preimages
  _patches/        # patches datados
  _ferramentas/    # HTML gerado
```

Antes de cada `mv`: preimage, lista de inbound references, atualização de links, teste do comando
canônico e readback. Nenhum backup ou fila com anotação é apagado.

## Guardas de execução

1. Script de treino só aceita manifest com SHA, classes ordenadas, vista única e split validado.
2. Treino não consome `anotacoes-ls.csv` diretamente: passa pelo estágio explícito de ingestão humana.
3. Uma rodada escreve somente em `dataset/_experimentos/<run_id>/` e `<diretório de modelos>/<model_id>/`.
4. Pesos, runs e dados derivados não entram no Git; receipts e contratos podem entrar, após revisão.
5. Antes de treino: RAM, load, VRAM, disco e processos; uma GPU/rodada.
6. Antes de promoção: canário em porta separada, SHA e rollback; nenhum deploy implícito.

## Lacunas que bloqueiam o fluxo

- ingestão canônica `anotacoes-ls.csv -> manifestos lateral/topo` ainda não existe;
- fotos próprias 2026-09-14 estão sem labels humanos;
- split atual contém leakage documentado;
- corpo não tem teste próprio independente;
- runtime v0 e fonte do site ainda precisam de promoção/versionamento governados.
