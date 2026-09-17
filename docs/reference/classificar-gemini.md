# `classificar_gemini.py`: rotulagem assistida do dataset (não é runtime)

Este texto preserva o histórico do rotulador assistido usado na criação do dataset. A fonte
`code-code-workspace/scripts/classificar_gemini.py` foi removida deste checkout junto com a árvore de PoCs. As
citações `arquivo:linha` abaixo descrevem essa fonte histórica, não um comando disponível para executar
agora. O rotulador não faz parte do runtime de `src-production/`.

Base da leitura: `main` em `db57cd5`, com as alterações locais da árvore de trabalho. O script difere do `HEAD` só em detalhe cosmético, conforme `git diff -- code-code-workspace/scripts/classificar_gemini.py`: as supressões `# noqa: E402` e `# noqa: BLE001` foram removidas e `re.S` virou `re.DOTALL`. Nenhuma linha citada aqui muda de comportamento entre as duas versões.

## 1. Fronteira, em uma frase

O script é ferramenta de bancada de rotulagem assistida (triagem por modelo generativo de visão), usada na criação e na expansão do dataset. Ele fica fora do runtime: `src-production/`, a árvore do produto, não o importa nem o chama, e o script não decide item em operação.

As provas seguem com o comando e a saída vazia, rodados na raiz do repositório:

```sh
git ls-files -- code-code-workspace/scripts/classificar_gemini.py
#   code-code-workspace/scripts/classificar_gemini.py        -> versionado

git grep -n "classificar_gemini"
#   code-code-workspace/scripts/classificar_gemini.py:9      -> só a própria docstring de uso
#   (nenhuma outra ocorrência no repositório inteiro)

grep -rnI -e classificar_gemini -e classificar_rest -e auxiliary_client -e PNAAT_AGENTE src-production/
#   (sem saída; rc=1)                                   -> nenhum módulo do produto importa ou cita

grep -rnI -e classificar_gemini -e classificar_rest -e gemini -e auxiliary_client code-workspace/tests/
#   (sem saída; rc=1)                                   -> nenhum teste o exercita

grep -rnI -e classificar_gemini -e classificar_rest --include=Makefile --include='*.sh' \
    --include='*.toml' --include='*.cfg' . --exclude-dir=.git --exclude-dir=.venv
#   (sem saída; rc=1)                                   -> nenhum alvo de build, fila ou hook o chama
```

A varredura de `gemini` (case-insensitive) cobre o repositório inteiro e encontra 11 ocorrências em 4 arquivos, todas fora do código de produto: este script, o irmão
`code-code-workspace/scripts/classificar_rest.py` e dois documentos de trabalho que saíram da árvore.

O produto classifica por outro caminho, e o repositório declara qual: `src-production/classificador.py` é um classificador medido, com extrator congelado, cabeça rasa treinada na hora e sem peso binário versionado por decisão (`src-production/classificador.py:1-13`). A fiação de quem consome o quê está em `src-production/README.md:35-37`, que marca como defeito o consumidor não declarado. Nada ali aponta para o rotulador.

A fonte do script, seus testes e seus alvos foram removidos deste checkout. O produto não importa essa ferramenta; as referências a `workspace/` abaixo são evidência histórica da fase de criação do dataset.

## 2. O que o script faz

O script fala com o Gemini free tier (`auxiliary.vision`) pelo cliente auxiliar do agente, com pool de credenciais e rotação automática (`classificar_gemini.py:2,4`). A chamada é `agent.auxiliary_client.async_call_llm` com `task="vision"` (`classificar_gemini.py:28,72`). A biblioteca do agente vem do ambiente, em `PNAAT_AGENTE_LIB`, e o diretório de dados do agente é herdado do host; nenhum dos dois fica no repositório (`classificar_gemini.py:8-9,22-26`).

A entrada é `--dir DIR`, obrigatória, com varredura recursiva (`rglob`) por `.jpg .jpeg .png .webp .bmp` (`classificar_gemini.py:31,86,94`). Há fatiamento e limitação para rodar em pedaços, com `--shard I N`, `--limit N` e `--sleep` no padrão de 4 s entre imagens (`classificar_gemini.py:88-90,95-99,108`). Cada imagem entra no pedido embutida como data URL base64, em `image/jpeg` ou `image/png` (`classificar_gemini.py:45-48`).

O formato pedido é um JSON só, sem texto em volta, com o vocabulário de quatro classes mais confiança e observação (`classificar_gemini.py:30,33-42`):

```json
{"classe": "normal|tampa_ausente|tampa_mal_rosqueada|deformidade", "confianca": 0.0, "observacao": "curta"}
```

O prompt define cada classe e inclui uma regra de exceção: se não houver garrafa visível, a resposta usa a classe `normal` com confiança 0.0 e explica na observação (`classificar_gemini.py:41`).

Os parâmetros de chamada são `temperature=0.0`, `max_tokens=2000` e `timeout=120`, com até 2 tentativas e 3 s de espera entre elas (`classificar_gemini.py:67-80`).

O parsing recorta o primeiro trecho entre chaves da resposta. Resposta vazia, sem JSON ou com classe fora do vocabulário vira um JSON de classe `erro` e confiança 0.0 (`classificar_gemini.py:51-64`). `erro` é sentinela do script, e não classe do domínio.

A saída é um JSON por imagem em `--out`, nomeado pelo `<stem>` do arquivo de entrada, com as chaves `arquivo`, `origem` (caminho de origem), `classe`, `confianca` e `observacao` (`classificar_gemini.py:104-105`). No terminal sai uma linha por imagem, no formato `nome  classe  confianca`, mais um `RESUMO` com a contagem por classe (`classificar_gemini.py:107,110`). O processo termina com código 0 quando o laço acaba (`classificar_gemini.py:111`), então imagem que falhou vira classe `erro` no JSON e não derruba o processo.

Nenhum script do repositório lê esse formato: as chaves `classe`, `confianca` e `observacao` do rotulador não reaparecem em nenhum consumidor, e a ocorrência delas em `code-code-workspace/scripts/avaliar_poc02.py:15` é de outro arquivo, com outro esquema, de outra PoC. Pasta e volume de saída dos JSONs gerados não constam no repositório.

## 3. Em que fase foi usado: criação/expansão do dataset

O repositório trata o script como ferramenta de rotulagem:

- A tabela de evidências locais do projeto o descrevia como "rotulador (versão local)" e apontava a versão de repositório em `code-workspace/scripts/`.
- O controle do rotulador saiu inconclusivo por quota diária do free tier (429 em 5/5), com estado
  `BLOCKED` no registro de erros do projeto.
- O mesmo controle sobre imagens do MVTec somou 40 imagens com erro 0.00 (quota 429 do pool), resultado
  inconclusivo que não vale como evidência de qualidade.
- A classificação por IA entra como opcional, com preflight de quota e limite de chamadas.

A decisão do projeto sobre esse tipo de rótulo é clara: IA serve como triagem, `defective` só entra por par validado, e a revisão visual acontece no volume pequeno. O erro que originou a regra foram rótulos errados (deformidade em garrafa normal) vindos de tratar
"IA de visão como verdade", com 2 falsos positivos comprovados na auditoria do projeto.

O catálogo de requisitos traz a expansão do dataset como linha de trabalho em RF-23, "Aplicar supervisão fraca ao dataset como evolução", com saída "dataset semi-rotulado e relatório de conflito" e critério de reprovação "regra discordante não pode virar rótulo confirmado sem rastreio" (`docs/requisitos/01-funcionais.md:284,290-291`). Ressalva de escopo: o RF-23 não cita este script, e a implementação de rotulagem que existe hoje no repositório é a do Label Studio, descrita na seção 5. Quantos itens o `classificar_gemini.py` rotulou, com qual modelo e em que datas, não consta no repositório.

O vocabulário de quatro classes (`classificar_gemini.py:30`) é o mesmo do corpus no mapeamento declarado do produto (`src-production/README.md:101-109`): `normal`, `tampa_ausente`, `tampa_mal_rosqueada` e `deformidade`. Isso confirma que a saída alimentava a anotação do dataset, e não a decisão de linha.

## 4. Limites e riscos do uso de modelo generativo para rotular

Os itens abaixo são os que o próprio repositório registra, sem hipótese acrescentada.

1. Custo e quota. O free tier estourou em 5/5 tentativas (429) e o controle saiu inconclusivo. O script não tem preflight de quota nem teto de chamadas, já que `classificar_gemini.py:84-91` expõe apenas diretório, saída, shard, limite e sleep; esses limites existem só na variante REST (`code-code-workspace/scripts/classificar_rest.py:107-135`), com `pool_disponivel()`, `--max-calls` e aborto de código 3 quando o pool está exausto.
2. Dependência de serviço externo e de biblioteca não declarada. O erro 7 do runbook registra `400 MissingSessionID` no meio da classificação, porque o pool Gemini foi marcado como unhealthy (429) e a chamada caiu no fallback do agente. O cliente do agente não é dependência declarada do workspace: `code-workspace/pyproject.toml:12-18` lista `numpy`, `opencv-python`, `scipy`, `Pillow` e `pyserial`.
3. Variabilidade e modelo não fixado. O script declara `temperature=0.0` (`classificar_gemini.py:72`), mas qual modelo atende a tarefa `vision` não consta no repositório, porque essa escolha é do cliente auxiliar do agente. O irmão REST é o único que nomeia modelos, `gemini-3.6-flash` e `gemini-2.5-flash`, em `code-code-workspace/scripts/classificar_rest.py:33`.
4. Viés e erro de rótulo. Está comprovado: 2 falsos positivos, com deformidade rotulada em garrafa normal.
5. Rastreabilidade fraca. O JSON gravado tem só `arquivo`, `origem`, `classe`, `confianca` e `observacao` (`classificar_gemini.py:104-105`), sem identificação do modelo, hash do prompt, horário ou recibo de chamada. Depois de rodado, não se reconstrói qual chamada produziu qual rótulo. O export canônico que substituiu esse fluxo grava recibo com contagens, sha256 e fingerprint do Label Studio (`src-production/treino/exporta_anotacoes.py:278-302`).
6. Defeitos de desenho do próprio prompt. Item sem garrafa visível é forçado a `normal` com confiança 0.0 (`classificar_gemini.py:41`), e o resumo por classe (`classificar_gemini.py:110`) mistura esse caso com normais reais; `erro` é uma sentinela que não existe no vocabulário do domínio (`classificar_gemini.py:53-63`). Sem revisão humana, os dois casos entram na contagem como se fossem rótulo.
7. Nenhum gate automático entre o rótulo da IA e o dataset. O que entra no conjunto é o rótulo humano do Label Studio, validado linha a linha (`src-production/treino/exporta_anotacoes.py:183-207`); o JSON do rotulador não passa por gate no repositório, porque nenhum consumidor o lê.

Consequência prática, já registrada no projeto: rótulo de IA só serve como triagem e precisa de revisão humana.

## 5. O que veio no lugar

O caminho atual não usa modelo generativo para decidir classe de imagem do nosso domínio. Ele tem dois eixos, ambos com gate versionado.

**(a) Rótulo canônico: Label Studio para CSV canônico e dataset, com split por item e quase-duplicata.**

| etapa | script | citação |
|---|---|---|
| 0 | `exporta_anotacoes.py`: Label Studio para CSV canônico, com validação por linha, recibo com sha256 e contagens, idempotência | `src-production/treino/exporta_anotacoes.py:1-14,183-207,252-302` |
| 0 | `guarda_frescor.py` + `fingerprint_ls.py`: aborta (rc=3) se o Label Studio avançou depois do export | `src-production/treino/README.md:13-15` |
| 1 | `monta_v1_detector.py`: consome os rótulos humanos do CSV canônico, com split por item, quase-duplicata por dHash, ROI por câmera e gates antes de escrever | `src-production/treino/monta_v1_detector.py:1-25,96-119,224-262,304-349,366-391` |
| 1 | `validacao_dataset.py`: gate independente do YAML efetivo | `src-production/treino/README.md:18` |
| 2-6 | `treina_v1.py` (base limpa só externa, depois ajuste fino), `avalia_por_dominio.py`, `avalia_limiares.py`, `calibra_limiar_val.py`, `kfold_por_item.py` | `src-production/treino/README.md:19-29,82-90` |

A cadeia na ordem exata e as regras que ela faz valer estão em `dataset/TRABALHO/RECEITA-20260915-pipeline-limpo.md:19-59` e `:68-75`. O mapa de autoridade, com a superfície ativa e o histórico, está em `dataset/TRABALHO/ORGANIZACAO.md:39-56`.

**(b) Expansão por defeito sintético, com gate objetivo.** O caminho de aumentar o dataset por geração mantém o humano no meio. `docs/reference/prompt-gerar-defeitos-dataset.md` define o formato (patch PNG 1:1 com alfa e JSON de controle), as proibições e o critério objetivo de aceitação: isolamento com no máximo 0,2% de pixels alterados fora do bbox, dimensões idênticas e schema válido (`docs/reference/prompt-gerar-defeitos-dataset.md:10-11,47-60`). A classe do par vem do JSON declarado e do gate, e não do julgamento do modelo. A execução do gate e a montagem são alvos versionados, `make validar` (com `validar_pares.py`) e `make dataset` (com `montar_dataset.py`), em `code-workspace/Makefile:9,35-41`.

**(c) A variante irmã.** `code-code-workspace/scripts/classificar_rest.py` faz a mesma rotulagem por REST direto na API, com pool de chaves, rotação de chaves e modelos, e retomada; foi a resposta ao erro 7. A variante é da mesma fase e tem os mesmos limites, com a diferença no lado operacional: é resumível, tem `--max-calls` e aborta com código 3 no pool exausto (`code-code-workspace/scripts/classificar_rest.py:1-11,107-135`). Nenhum arquivo da árvore atual declara qual dos dois substituiu o outro; as duas fontes foram removidas junto com a árvore de PoCs.

## 6. Como reproduzir (e o que não fazer)

**Requisitos de ambiente.** O script não é instalável pelo `make install` do workspace.

1. Um interpretador Python com a biblioteca do agente disponível, no uso declarado `<python do agente>` com `PNAAT_AGENTE_LIB=<lib do agente>` (`classificar_gemini.py:8-9,22-26`).
2. O diretório de dados do agente precisa existir no host, porque é herdado e não parametrizado (`classificar_gemini.py:22-23`).
3. A biblioteca do agente e o cliente Gemini que ela usa não estão declarados em `code-workspace/pyproject.toml:12-18`, então provisioná-los é passo de ambiente; o script falha no import se `PNAAT_AGENTE_LIB` não resolver `agent.auxiliary_client` (`classificar_gemini.py:24-28`).
4. O pacote Python do projeto não é necessário para este script, que não importa nada de `src/`.

**Chamada.** O formato é o da própria docstring, em `classificar_gemini.py:8-9`:

```sh
PNAAT_AGENTE_LIB=<lib do agente> <python do agente> classificar_gemini.py --dir DIR --out DIR \
    [--shard I N] [--limit N] [--sleep 4]
```

Como o free tier estoura (seção 4, item 1), o uso responsável é por fatias, com `--shard`, `--limit` e `--sleep` alto, em vez de job longo.

**O que não deve ser feito.**

- Não colocar chave, token ou arquivo de credenciais no repositório. Credenciais e `.env` ficam na
  máquina de trabalho, fora do repositório, e a checagem roda antes do commit (`commit_gate.sh`,
  chamado pelo hook `pre-commit`).
- Não usar a saída do rotulador como rótulo confirmado: IA serve como triagem.
- Não ligar o script em runtime, no site ou no serviço de inferência: nada de `src-production/` o importa, e a prova está na seção 1.

**Segredos: nenhum valor hardcoded encontrado.** A varredura dos dois scripts de rotulagem cobriu padrões de chave e token (`AIza`, `sk-` com 8 ou mais caracteres, `ghp_`, `xoxb-`, `Bearer` com token, `-----BEGIN`, `password|senha|secret`):

```sh
grep -nE "AIza|sk-[A-Za-z0-9]{8,}|ghp_|xoxb-|Bearer [A-Za-z0-9._-]{8,}|-----BEGIN|password|senha|secret" \
    code-code-workspace/scripts/classificar_gemini.py code-code-workspace/scripts/classificar_rest.py
#   (sem saída; rc=1)
```

O `classificar_gemini.py` recebe apenas o caminho da biblioteca do agente pelo ambiente (`classificar_gemini.py:24`). O irmão REST lê as chaves de um arquivo de credenciais fora do repo, cujo caminho vem de `PNAAT_AGENTE_AUTH` e cujo valor o script não imprime (`code-code-workspace/scripts/classificar_rest.py:4,25-31,47-49`). Risco residual a registrar, esse sim: na variante REST a chave viaja na query string da URL (`code-code-workspace/scripts/classificar_rest.py:74`), formato que costuma aparecer em log de proxy e em histórico de processo; a variante `auxiliary` não tem esse problema, porque autentica pelo cliente do agente. Nenhum arquivo deste repositório contém o valor de chave.

## 7. Limites declarados

- Reexecutar o controle do rotulador depois do reset de quota, ou usar credencial paga ou provider alternativo. Hoje o estado é `BLOCKED`, e o mesmo controle é "inconclusivo, não é evidência de qualidade".
- Ingestão canônica de `anotacoes-ls.csv` para manifestos (lateral e topo) ainda não existe (`dataset/TRABALHO/ORGANIZACAO.md:98-100`).
- Fotos próprias de 2026-09-14 sem labels humanos, e split atual com leakage documentado (`dataset/TRABALHO/ORGANIZACAO.md:101-102`).
- RF-23 (supervisão fraca) é evolução, com o critério de que regra discordante não vira rótulo confirmado sem rastreio (`docs/requisitos/01-funcionais.md:284,290-291`).
- O script não tem consumidor no produto e sua fonte não está neste checkout. Este documento preserva o histórico de uso, não um procedimento executável.
- Não consta no repositório: quantidade de imagens rotuladas por este script, pasta ou volume de saída usados, e o modelo exato que atendeu a tarefa `vision`.

## 8. Índice das fontes citadas

| arquivo:linha | o que prova |
|---|---|
| `code-code-workspace/scripts/classificar_gemini.py:2,4` | modelo/API e cliente auxiliar (Gemini free tier, `auxiliary.vision`) |
| `code-code-workspace/scripts/classificar_gemini.py:8-9,22-26` | uso, `PNAAT_AGENTE_LIB`, diretório de dados do agente herdado |
| `code-code-workspace/scripts/classificar_gemini.py:28,30,31` | import do cliente do agente; vocabulário de classes; extensões aceitas |
| `code-code-workspace/scripts/classificar_gemini.py:33-42` | prompt, formato JSON e regra de exceção (sem garrafa: `normal` 0.0) |
| `code-code-workspace/scripts/classificar_gemini.py:45-48,67-80` | imagem em base64; `temperature=0.0`, `max_tokens`, `timeout`, 2 tentativas |
| `code-code-workspace/scripts/classificar_gemini.py:51-64,88-91,94,104-105,107,110,111` | parsing com sentinela `erro`; CLI; saída JSON por imagem; resumo; rc=0 |
| `code-code-workspace/scripts/classificar_rest.py:1-11,25-33,47-49,68-74,107-135` | variante REST: credenciais por `PNAAT_AGENTE_AUTH`, modelos nomeados, preflight/teto/`return 3`, chave na query string |
| `code-workspace/Makefile:9,35-41` | `validar`/`dataset` (gate e montagem dos pares); nenhum alvo chama o rotulador |
| `code-workspace/pyproject.toml:12-18,40-42` | dependências declaradas (sem cliente do agente); PoCs como história congelada |
| `code-workspace/scripts/git-hooks/pre-commit:7` | hook chama `commit_gate.sh` |
| `src-production/README.md:3-6,35-37,101-109` | produto não importa `workspace/`; fiação declarada; mapa de classes corpus × domínio |
| `src-production/classificador.py:1-13` | classificador medido do produto (sem peso binário versionado) |
| `src-production/treino/README.md:13-29,82-90` | cadeia canônica atual e regras assumidas |
| `src-production/treino/exporta_anotacoes.py:1-14,183-207,252-302` | export canônico: contrato, validações por linha, CSV + recibo |
| `src-production/treino/monta_v1_detector.py:1-25,96-119,224-262,304-349,366-391` | split por item, quase-duplicata por dHash, rótulos humanos do CSV, gates |
| `docs/reference/prompt-gerar-defeitos-dataset.md:10-11,47-60` | expansão sintética com gate de isolamento (≤ 0,2% fora do bbox) |
| `docs/requisitos/01-funcionais.md:284,290-291` | RF-23 supervisão fraca: saída semi-rotulada e critério de reprovação |
| `code-workspace/scripts/git-hooks/pre-commit:7` | credenciais ficam fora do repositório; o gate roda antes do commit |
| `dataset/TRABALHO/ORGANIZACAO.md:39-56,98-102` | superfície ativa (export + montagem) e lacunas que bloqueiam o fluxo |
| `dataset/TRABALHO/RECEITA-20260915-pipeline-limpo.md:19-59,68-75` | cadeia atual na ordem exata e regras que não podem ser quebradas |
