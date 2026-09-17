# Pipeline de treino (arvore de producao)

Este diretorio e a receita canonica do detector: monta o dataset, treina, avalia, calibra o limiar,
mede k-fold, empacota o candidato e produz o artefato `.npz` que a cadeia consome.

Historico (filas antigas, candidatos v0, experimentos pontuais e servico de borda) fica em
`dataset/TRABALHO/` e em `dirty-workspace/`. Aqui esta so o que a cadeia usa hoje.

## Cadeia, na ordem

| # | script | o que faz |
|---|---|---|
| 0 | `exporta_anotacoes.py` | Label Studio -> CSV canonico + recibo |
| 0 | `guarda_frescor.py` | aborta (rc=3) se o Label Studio avancou depois do export |
| 0 | `fingerprint_ls.py` | fingerprint do Label Studio usado pelo export |
| 1 | `monta_v1_detector.py` | monta o dataset: split POR ITEM, quase-duplicata (dHash), ROI por camera |
| 1 | `roi_por_camera.py` | deriva a ROI por camera das caixas anotadas |
| 1 | `validacao_dataset.py` | gate independente do YAML efetivo: listas, labels, disjuncao por item |
| 2 | `treina_v1.py` | base limpa externa (`--tag ext`) e ajuste fino no dominio; gate obrigatorio no `--data` |
| 3 | `avalia_por_dominio.py` | mAP por dominio e por classe no split pedido |
| 3 | `avalia_limiares.py` | precisao, recall e F1 por limiar de confianca |
| 4 | `calibra_limiar_val.py` | escolhe o limiar por classe NA VALIDACAO e grava no contrato |
| 5 | `evidencia_candidato.py` | decisao por imagem, mosaico e JSON de evidencia |
| 5 | `decisao_operacional.py` | acuracia da decisao com limiar, contando o que vai para revisao |
| 6 | `kfold_por_item.py` | metrica de aceitacao: k dobras por item, listas disjuntas |
| 7 | `pacote_entrega.py` | pacote do candidato: peso + contrato + metadados + checksums (dry-run por padrao) |
| - | `contrato/preprocessamento.json` | fonte unica de ROI, rotacao, imgsz, classes e limiares |
| - | `contrato/roi-por-camera.json` | ROI medida por camera, com a cobertura das caixas |
| - | `contrato/treino-v1-args.yaml` | hiperparametros do ajuste fino |

Apoio: `preflight_preproc.py` (confere o contrato antes de rodar), `gera_contrato_preproc.py`
(gera/atualiza o contrato), `aumenta_offline.py` (aumento 3x no split de treino, com procedencia),
`oversample_dominio.py`, `leitor_resultados.py`.

Verificacao e operacao: `auditoria_dataset.py` (auditoria adversarial do dataset montado) e
`guardiao_treino.sh` (porta de recursos com watchdog).

Frente CORPO (modelo separado): `monta_corpo_detector.py`, `monta_corpo.py`, `treina_corpo.py`,
`treina_corpo_cls.py`, `le_smoke_corpo.py`, `monta_deformidade.py`.

## Produtor do artefato `.npz` (receita medida, D-37)

`compara_extratores.py` monta o conjunto canonico (`carrega()`), compara extratores e **grava o artefato
ele mesmo** (`np.savez` em `main()`: `dataset/modelo-inferencia.npz` + `.json`). O canario da cadeia
(`../canario_modelo_artefato.py`) **reusa** esse `carrega()` de proposito: se cada lado montasse a sua
lista, a comparacao nao provaria nada sobre o port. (`exporta_modelo.py` tem um `carrega()` proprio,
legado da primeira versao; nao participa desta receita.)

Os pacotes já publicados estão em https://huggingface.co/Nerton/pnaat-modelos, com `SHA256SUMS` por pacote: baixar de lá dispensa
o treino para consumir o detector.

## Contrato de caminhos

| variavel | aponta | default |
|---|---|---|
| `PNAAT_MODELOS` | pesos, runs, datasets derivados | irmao do diretorio pai do clone |
| `PNAAT_DADOS` | dados fora do repo (`dataset/`, `det_runs/`, `modelos/`) | pai do clone |
| `dataset/split.csv`, `dataset/MANIFEST.csv`, `dataset/normalizado/` | insumos da receita medida do artefato (D-37) | dado de instalação, fora do clone |
| instalação do Label Studio (banco, `credenciais.env`, porta e raiz de mídia) | export de anotações (`monta_v1_detector.py`, `exporta_anotacoes.py`, `fingerprint_ls.py`) | dado de instalação |

Resolvidos por `caminhos.py` (ancestral que tem `docs/` e `dataset/`, sem ancestral fixo), e
exportados pelo `Makefile` da arvore. Nenhum script carrega nome de usuario, exceto o `chown` do export
do Label Studio (`exporta_anotacoes.py`), que roda na maquina do rotulador.

## Como invocar

```sh
cd src-production
make treino-dataset TAG=v10          # monta o dataset
make treino-run     TAG=v10 EPOCHS=150
make treino-avalia  TAG=v10          # exige `oversample_dominio.py` rodado antes
make treino-kfold   TAG=v10 K=5
make pacote         TAG=v10 PACOTE=<dir> APLICAR=1     # sem APLICAR=1 o alvo e dry-run
```

Passos 4 (calibracao do limiar na validacao) e 5 (evidencia do candidato) sao chamada direta, fora do
`Makefile`: `src-production/treino/calibra_limiar_val.py` e `src-production/treino/evidencia_candidato.py`
(cada um com `--help`).

Chamada direta de um modulo:

```sh
../.venv/bin/python treino/monta_v1_detector.py --vista lateral --roi --somente-dominio \
    --out "$PNAAT_MODELOS/v10-lateral-detector-roi/dataset"
```

## Regras que a cadeia assume 

- metrica so com listas separadas e verificadas: split por ITEM, nunca por imagem;
- nenhum peso que ja viu o teste serve de base de avaliacao;
- descarte de item no montador e sempre contado por motivo;
- limiar se escolhe na validacao, nunca no teste;
- o mesmo pre-processamento no treino e na inferencia, vindo do MESMO contrato
  (`../preparo_detector.py` e a unica implementacao do recorte);
- intermediario nunca em `/tmp` compartilhado; uma rodada por vez na GPU.
