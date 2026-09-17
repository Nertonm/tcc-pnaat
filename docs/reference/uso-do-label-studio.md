# Uso do Label Studio: como e por que o dataset foi anotado

> Estado deste checkout: a árvore `code-workspace/` citada em passagens históricas foi removida. O fluxo de treino disponível está em `src-production/treino/`; este documento não oferece os comandos removidos como rota de execução.

Base: clone limpo do repositório, branch `main`, HEAD `db57cd5`, lido em 2026-09-16. Critério deste
documento: só o que o próprio repositório sustenta. Onde a informação não existe no repositório, o
texto escreve "não consta no repositório" em vez de deduzir. Toda afirmação carrega origem
`arquivo:linha`, conforme a regra de documentação do projeto.

## 1. Papel: o Label Studio é a superfície de trabalho; o repositório é o canônico

O contrato está no cabeçalho do exportador:

> "o Label Studio e a superficie de trabalho; o REPOSITORIO e canonico";
> "este script puxa, VALIDA e grava; nada entra sem passar na validacao";
> "saida estavel (CSV) + recibo com contagens e sha, e o diff contra o ultimo recibo";
> "idempotente: rodar de novo nao duplica nem reescreve o que nao mudou"
> (`src-production/treino/exporta_anotacoes.py:1-14`)

A anotação humana acontece numa instalação de Label Studio (LS) fora do repositório. O que o
repositório reconhece como rótulo é o CSV exportado e validado. A posição da anotação na cadeia de
produção aparece duas vezes no repositório:

- `src-production/README.md:57-61`: `anotacao humana (Label Studio) -> treino/exporta_anotacoes.py
  (CSV canonico + recibo de frescor) -> treino/guarda_frescor.py -> treino/monta_v1_detector.py ->
  treino/treina_v1.py`;
- `src-production/treino/README.md:13-15`: os três passos "0" da cadeia, ou seja, exportador, trava
  de frescor e fingerprint.

Por que existe anotação humana neste projeto:

- D-13, expansão evolutiva do dataset (`docs/DECISIONS.md:213-226`). As opções eram (A) só sinais
  automáticos, (B) só anotação manual, (C) combinar; a direção adotada é C, com três regras:
  "nenhum rótulo produzido automaticamente deve ser promovido a confirmado sem rastreabilidade",
  "conflitos entre fontes de rótulo devem permanecer explícitos" e "o resultado do próprio sistema
  não deve ser utilizado automaticamente como verdade de referência".
- D-32, autoridade entre o processo determinístico e o processo de IA (`docs/DECISIONS.md:588-606`).
  O "processo B" (IA) decide as classes de aparência e sutileza: defeito fino de rosqueamento,
  estado de rótulo e domínio alheio. Ele "requer dado rotulado e o controle de domínio como gate"
  (`docs/DECISIONS.md:596-598`). É essa exigência que a anotação no LS atende.
- D-26, D-28 e D-25 (`docs/DECISIONS.md:428-471`). O vocabulário das classes é canônico e definido
  por domínio, `inconclusivo` é classe própria e a métrica por classe exige verdade anotada. Sem
  rótulo humano não há matriz de confusão nem RNF-02.

## 2. O que é anotado (e por quê)

O espaço de anotação é reconstruível a partir do que o exportador lê de cada anotação
(`src-production/treino/exporta_anotacoes.py:126-148`):

| Campo do LS (`from_name`) | Tipo | Domínio de valores | Origem |
|---|---|---|---|
| `vista` | choices | `lateral`, `topo`, `inconclusiva` | `exporta_anotacoes.py:34`, `:132-133` |
| `classe` | choices | `normal`, `tampa_ausente`, `defeito_tampa`, `deformidade`, `inconclusivo` | `exporta_anotacoes.py:35`, `:134-135` |
| `coerencia` | choices | `concorda_com_a_fonte`, `conflita_com_quase_duplicata`, `rotulo_da_fonte_errado`, `excluir_do_treino`, `imagem_ruim` | `exporta_anotacoes.py:36-37`, `:136-137` |
| `estado_tampa` | choices | valor livre registrado na linha | `exporta_anotacoes.py:138-139` |
| `estado_corpo` | choices | valor livre registrado na linha | `exporta_anotacoes.py:140-141` |
| `rectanglelabels` | caixas | rótulos `tampa`, `tampa_ausente`, `tampa_alterada`, `corpo_deformidade`, `corpo_regiao` | `exporta_anotacoes.py:142-146`, `monta_v1_detector.py:221`, `:248-249` |
| `textarea` | observação | texto livre, truncado em 200 caracteres no CSV | `exporta_anotacoes.py:147-148`, `:177` |

Perguntas que a anotação responde no fluxo de treino: qual vista a imagem representa, qual classe o
item tem, se o rótulo de origem é confiável (`coerencia`, incluindo as marcas de exclusão
`excluir_do_treino` e `imagem_ruim`, respeitadas pelo montador em `monta_v1_detector.py:84` e
`:232-234`) e onde está a peça/defeito, nas caixas das quais deriva a ROI por câmera
(medição de 15/09/2026).

A configuração de interface do LS (XML de labeling, `label_config`) não consta no repositório. O que
consta é a leitura do resultado dessa configuração pelo exportador, nas linhas acima.

### 2.1 Recorte de rotulagem e vocabulário

O corpus anotado trabalha com quatro classes de interesse, `normal`, `tampa_ausente`,
`tampa_mal_rosqueada` e `deformidade`, mas o vocabulário canônico da decisão tem apenas três na
tampa, porque D-31 fundiu os detalhes:

- D-31, três classes na tampa (`docs/DECISIONS.md:557-579`). A decisão da tampa passa a usar
  `normal`, `tampa_ausente` e `defeito_tampa`; `defeito_tampa` funde mal rosqueada, danificada e
  aberta; `tampa:molhada` fica separada para avaliação (fila `wp-I`). O detalhe não se perde porque
  o catálogo `taxonomia_defeito` mantém `TAMPA_MAL_ROSQUEADA`, `TAMPA_DANIFICADA` e `TAMPA_ABERTA`
  apontando para a classe fundida (`docs/DECISIONS.md:565-567`).
- Contagens medidas do corpus na decisão de D-31: `normal` 3.898; `tampa_ausente` 821;
  `defeito_tampa` 1.327; em avaliação 394; inconclusivo 114 (`docs/DECISIONS.md:568-569`).
- D-28, vocabulário canônico (`docs/DECISIONS.md:457-471`). Por domínio, a tampa usa `normal`,
  `tampa_ausente`, `defeito_tampa` e `inconclusivo`; o corpo usa `normal`, `deformidade` e
  `inconclusivo`. `deformidade` não é classe válida no domínio da tampa.

Consequência prática para quem lê o CSV: a coluna `classe` do export usa `defeito_tampa`, enquanto o
`data.yaml` de conjuntos anotados antigos e nomes de arquivo ainda dizem `tampa_mal_rosqueada`. A
divergência está registrada em `docs/DECISIONS.md:866-882` ("o `data.yaml` do conjunto anotado diz
`tampa_mal_rosqueada`, o peso v0 emite `tampa_alterada` e o contrato do v7a declara `defeito_tampa`"),
com o alerta de que limiares indexados por nome de classe se perdem se o contrato for implementado ao
pé da letra. O nome granular sobrevive na camada de dados (`docs/DECISIONS.md:578-579`) e nos scripts
de PoC (`code-code-workspace/scripts/classificar_gemini.py:30`, `code-workspace/scripts/validar_pares.py:30`).

## 3. Onde o dado anotado vive e o que é versionado

A saída canônica é `dataset/TRABALHO/anotacoes-ls.csv`, com recibos em
`dataset/TRABALHO/_exportacoes/recibo-*.json` (`exporta_anotacoes.py:30-33`, `:301-302`).

Estado no Git deste clone (verificado): nem o CSV nem os recibos estão versionados.
`git ls-files --error-unmatch dataset/TRABALHO/anotacoes-ls.csv` falha, `git log --all --` para o CSV
e para `_exportacoes/` não devolve commits, e o arquivo não existe no disco deste clone. Os dois são
artefatos de execução, não conteúdo do repositório.

A regra escrita em `.gitignore:135-137` diz: "o dado PROPRIO (`dataset/nosso/`) e versionado (...)
Terceiros (CC BY 4.0), derivados, anotacoes e saidas de experimento vivem na arvore e NUNCA sao
versionados: sao grandes e nao sao nossos". O diretório `dataset/anotacao/**` é ignorado, com exceção
do README (`.gitignore:144-145`).

O volume do corpus no LS foi medido em 2026-09-15:
"Label Studio: 37.200 imagens em 12 projetos", com `dataset/anotacao` 3.145, `corpus capturas` 301,
`dataset/nosso` 124, uploads da equipe 16 (projeto 19); "anotações humanas submetidas: 180+ (p3 ·
p11 · p13 · p14 · p19)"; e "rascunhos não submetidos não entram no export canônico".

Este clone não contém o dado de bancada, que fica fora do Git: o corpus de mídia do LS, a instalação
do LS, `dataset/TRABALHO/README.md`, `RUBRICA.md`, `RESPOSTAS-DO-RESPONSAVEL.md`, `anotadores.csv` e
as filas `wp-*`. Todos eles são citados como existentes na superfície de trabalho em
`dataset/TRABALHO/ORGANIZACAO.md:15-18`, mas estão ausentes daqui.

`dataset/MANIFEST.csv` é lido pelo exportador para enriquecer cada linha com `bloco`, `classe_fonte`,
`sessao` e `sha256` (`exporta_anotacoes.py:72-79`); o arquivo não existe neste clone e não está no
índice do Git.

## 4. Fluxo operacional real

### 4.1 Instalação do LS

Não consta no repositório: não há `docker-compose`, `Dockerfile`, versão do LS nem documento de
instalação. A única evidência versionada de que o LS roda como container é um comentário de código em
`src-production/firmware/esp32cam-test/esp32cam_site.py:1338`, sobre a porta ter passado a ser do
container do Label Studio. Instalar e manter o LS é operação de bancada, fora do repo.

### 4.2 Criar lote e importar imagens

O material de trabalho registra "Filas | `wp-B`, `wp-E1`, `wp-E2`, `wp-F`, `wp-G`, `wp-J` | tarefas
declaradas | Label Studio ou HTML, nunca treino direto" (`dataset/TRABALHO/ORGANIZACAO.md:16`), e o
contrato humano (`README.md`, `RUBRICA.md`, `RESPOSTAS-DO-RESPONSAVEL.md`, `anotadores.csv`) aparece
como "instruções e vocabulário | revisão humana" (`dataset/TRABALHO/ORGANIZACAO.md:15`). Nenhum
desses arquivos está versionado neste clone, e o procedimento de criação de fila e importação não
consta no repositório.

### 4.3 Anotar

Critério de classe: D-31 e D-28, acima. Existe um cuidado de ordem, com consequência sobre a qualidade
do rótulo: "o corpus do Label Studio e do visual ATUAL de captura: decidir iluminacao antes de anotar,
senao as anotacoes descrevem uma aparencia que a bancada nao vai mais produzir"
(`docs/DECISIONS.md:1008`). A concordância entre anotadores foi medida em 8 tarefas com 2+ anotações,
e as 8 concordam: 100% (medição de 15/09/2026). A amostra é pequena, e o
próprio relatório diz isso. O export registra quantas anotações o task tem, quem anotou e quando
(`exporta_anotacoes.py:175-179`) e marca `anotacao_multipla` quando há mais de uma
(`exporta_anotacoes.py:243`).

### 4.4 Exportar: por API, não manualmente

O caminho documentado é um script contra a API REST do LS, não export pela interface web:

- descoberta dos projetos que têm anotação, lendo o banco do LS somente leitura
  (`exporta_anotacoes.py:43-63`). O motivo está no próprio código: "Lista fixa já falhou uma vez
  (projeto 22, 139 anotações, ficou de fora e o export saiu calado com dado velho)"
  (`exporta_anotacoes.py:46-47`). Há fallback fixo `(3, 11, 13, 14, 19)` se o banco não responder
  (`exporta_anotacoes.py:39`, `:63`), e o projeto 4 (corpus) é excluído por não ser fila
  (`exporta_anotacoes.py:40`);
- download via HTTP com cabeçalho de token e `exportType=JSON` (`exporta_anotacoes.py:100-104`), com
  timeout de 300 s;
- validação que reprova linha a linha, com motivo registrado: vista e classe dentro do vocabulário,
  coerência conhecida, caixas dentro de 0..100% e com área > 0, e classe de defeito/objeto sem caixa
  é reprovada (`exporta_anotacoes.py:183-207`, `:233-239`);
- escrita do CSV ordenado por `task_id`, com `valido`/`motivo` em cada linha
  (`exporta_anotacoes.py:247-256`), e do recibo com contagens por vista/classe/domínio, sha256 curto,
  `fingerprint_ls` e delta contra o recibo anterior (`exporta_anotacoes.py:277-302`). O recibo é o
  elo entre o CSV gravado e o estado do LS no instante do export.

### 4.5 Gate de frescor

`guarda_frescor.py` é um wrapper de 12 linhas que delega a `fingerprint_ls.main()`
(`src-production/treino/guarda_frescor.py:1-12`). O contrato de retorno
(`src-production/treino/fingerprint_ls.py:51-86`):

| Situação | Retorno |
|---|---|
| LS igual ao export de referência | `0`: "estado igual ao export: pode montar dataset" (`:85-86`) |
| LS avançou (drafts/anotações/uploads/tarefas) | `3`: "LS AVANÇOU DESDE O EXPORT; montagem deve parar" (`:80-84`) |
| não há recibo de export | `3`: "SEM RECIBO de export: rode antes o exportador canônico" (`:65-68`) |
| recibo sem `fingerprint_ls` (export anterior à trava) | `3`: "tratado como desatualizado" (`:72-75`) |
| `--simular <json>` | usa um fingerprint falso, para provar o caminho de aborto (`:55`, `:59-61`) |

O consumidor é o montador: `monta_v1_detector.py:202-210` executa a guarda em subprocesso e, se o
retorno não for 0, imprime "ABORTADO pela trava de frescor: o Label Studio avancou desde o export
(rode src-production/treino/exporta_anotacoes.py e tente de novo)" e devolve rc=4. Existe escape
rotulado como não recomendado: `--ignorar-frescor` (`monta_v1_detector.py:196-197`).

### 4.6 Montar o dataset e treinar

O montador consome o CSV canônico, `CSV_HUMANO = dataset/TRABALHO/anotacoes-ls.csv`
(`monta_v1_detector.py:43`), aceita apenas linhas com `valido == sim`, com a vista pedida
(`--vista lateral|topo`), sem coerência de exclusão, e resolve a mídia, inclusive caminhos de mídia
do próprio LS (`/data/upload/<id>/<nome>`), que em disco têm prefixo uuid (`monta_v1_detector.py:64-83`,
`:226-239`). O split é por item, nunca por imagem (`monta_v1_detector.py:2-13`, `:96-119`). Depois vêm
aumento, treino com base limpa externa, avaliação, calibração de limiar na validação, k-fold e pacote;
a ordem completa está em `src-production/treino/README.md:11-29` e `src-production/README.md:57-70`.

### 4.7 Runner de lote novo

`docs/reference/MODO-NOVO-LOTE.md:23-33` descreve o runner de 7 passos com a trava de cada passo. O
comando é `bash dataset/TRABALHO/filas/novo_lote.sh <TAG> [--kfold]` (`docs/reference/MODO-NOVO-LOTE.md:14-19`).
No script (`dataset/TRABALHO/filas/novo_lote.sh`):

- passo 1: export (`:40-41`) e checagem de frescor por idade do arquivo, com `LOTE_HZ` padrão de 2 h
  (`:30`, `:42-44`); a mensagem de aborto é "ABORTA: nenhum export com menos de ${HZ}h: a equipe
  publicou o lote?";
- passo 2: montagem do dataset (`:46-50`);
- passos 3-7: aumento 3×, treino sob guardião, limiares, k-fold, pacote (`:52-84`);
- produção é passo de operador, não do runner (`:85-88`, `docs/reference/MODO-NOVO-LOTE.md:35-44`).

Divergência de caminho: o runner procura o export recente em `$DS/export` (`novo_lote.sh:42`),
enquanto o exportador grava o CSV e os recibos em `dataset/TRABALHO/` e `dataset/TRABALHO/_exportacoes/`
(`exporta_anotacoes.py:32-33`). O diretório `dataset/TRABALHO/export` não existe neste clone e não
consta no repositório. A checagem de frescor do runner e a do montador não olham o mesmo artefato.

## 5. Por que o frescor importa: o número que muda em silêncio invalida a medição

O próprio módulo conta o dano que originou a trava:

> "Serve de trava: antes de montar dataset, comparar o estado ATUAL do LS com o estado no momento
> do export canônico. Se algo avançou (anotação submetida, rascunho novo, upload novo), a montagem
> para; foi essa checagem que faltou e fez o v1 ser montado com retrato velho, deixando de fora 16
> imagens novas e 8 rascunhos da equipe."
> (`src-production/treino/fingerprint_ls.py:2-9`)

O mesmo defeito está no relatório do dia, com o número medido: "Imagens dos colegas descartadas em
silêncio. As 16 imagens do projeto 19 (...) nunca entraram em treino: o filtro de classe do montador
usava a lista de 3 classes e descartava as linhas `classe=deformidade` sem aviso. (...) Efeito medido
no ensaio: domínio próprio de 125 → 137 imagens, anotações humanas de 168 → 180, e a classe
`corpo_deformidade` de 6 → ~15 instâncias de treino"
(medição de 15/09/2026). A trava também detectou rótulos novos
submetidos durante o dia (medição de 15/09/2026).

A razão de método é curta. Se o export é um retrato de um instante e alguém continua anotando, o CSV
deixa de descrever o corpus que o LS tem, e um treino rodado sobre o retrato velho produz um número
novo para o mesmo dado: "parece progresso e não é" (`docs/reference/MODO-NOVO-LOTE.md:8-10`). Pior que
isso: rótulo humano que entra no meio da cadeia muda a verdade do conjunto sem deixar rastro no
manifesto, o que invalida a medição em silêncio. Por isso a checagem é um gate com código de saída, e
não um aviso.

O fingerprint mede seis coisas (`fingerprint_ls.py:34-41`), em leitura somente (`sqlite ... mode=ro`,
`fingerprint_ls.py:9`, `:28`): total de `task`, total de `task_completion`, `max(updated_at)` das
anotações, total de `tasks_annotationdraft`, `max(updated_at)` dos rascunhos e total de
`data_import_fileupload`. A comparação é campo a campo contra o recibo (`fingerprint_ls.py:44-48`), e
o relatório imprime `no_export -> agora` por campo divergente (`fingerprint_ls.py:80-84`). Rascunho
entra na conta porque rascunho não submetido não entra no export canônico
(medição de 15/09/2026): é trabalho humano que ainda vai mudar o corpus.

## 6. Reprodução por terceiro

A cadeia não roda sem pré-requisitos fora do repositório: uma instalação de Label Studio com os
projetos de anotação; o arquivo de credenciais de onde o token é lido em tempo de execução
(`exporta_anotacoes.py:68-69`); o banco do LS acessível para a descoberta de projetos e para o
fingerprint (`exporta_anotacoes.py:50-55`, `fingerprint_ls.py:23`); o corpus de mídia apontado pelas
anotações; e `dataset/MANIFEST.csv` (`exporta_anotacoes.py:73`). Nada disso é versionado (§3 e §7).

Interface de linha de comando conferida neste clone em 2026-09-16:

```bash
# 0) rótulos: export canônico + trava de frescor  (RECEITA, §2)
$PY src-production/treino/exporta_anotacoes.py     # sem argparse: roda direto (grep -c argparse = 0)
$PY src-production/treino/guarda_frescor.py         # sem argparse: rc=0 libera, rc=3 aborta

# conferência da interface dos que TÊM argparse (saída real, rc=0):
$ ./.venv/bin/python src-production/treino/fingerprint_ls.py --help
usage: fingerprint_ls.py [-h] [--db DB] [--recibo RECIBO] [--simular SIMULAR]
  --db DB
  --recibo RECIBO    recibo de export a comparar (default: o mais novo)
  --simular SIMULAR  JSON com fingerprint falso (teste do caminho de aborto)

$ ./.venv/bin/python src-production/treino/monta_v1_detector.py --help
usage: monta_v1_detector.py [-h] [--vista {lateral,topo}] [--dry-run] [--out OUT] [--com-corpo]
                            [--sem-phash] [--somente-dominio] [--permitir-classe-ausente]
                            [--ignorar-frescor] [--roi]
```

Sequência canônica do dia, adaptada de `dataset/TRABALHO/RECEITA-20260915-pipeline-limpo.md:19-27`,
que usa os caminhos `dataset/TRABALHO/*`:

```bash
$PY src-production/treino/exporta_anotacoes.py
$PY src-production/treino/guarda_frescor.py                 # rc=3 => NÃO montar; exportar de novo
$PY src-production/treino/monta_v1_detector.py --vista lateral --roi --somente-dominio \
    --out <diretorio de modelos>/<tag>-lateral-detector-roi/dataset
```

Para um lote novo da equipe, o caminho escrito no repositório é o runner de 7 passos
(`docs/reference/MODO-NOVO-LOTE.md:14-19`), cujo passo 1 é justamente o export seguido de checagem de
frescor por idade (`novo_lote.sh:39-44`), mas veja a divergência de caminho em §4.7. Um terceiro
também pode testar o caminho de aborto sem tocar no LS, com `fingerprint_ls.py --simular <json>`
(`fingerprint_ls.py:55`, `:59-61`).

Não há alvo `Makefile` versionado para esses três passos "0": a receita invoca os scripts direto
(`src-production/treino/README.md:64-73` mostra os alvos de treino; os passos de rótulo aparecem
apenas na tabela da cadeia, `:13-15`).

## 7. Dados de instalação que nunca entram no repositório

Regra: nunca entra no repositório credencial (token, chave de API, arquivo de credenciais) nem
dado de instalação (IP privado, hostname, usuário de sistema, caminho pessoal). Onde o valor precisa
aparecer, usa-se marcador: `<host>`, `(host interno)`, `$HOME`, `<TCC_HOME>`. A mesma regra está em
`CONTRIBUTING.md:29-33` ("Não incluir credenciais, tokens, dados pessoais ou caminhos de máquina") e
em `.gitignore:135-137` (anotações nunca versionadas). A checagem roda antes de cada commit.

Aplicação a este documento:

- Token do LS: é lido em tempo de execução de um arquivo de credenciais que fica fora do repo
  (`exporta_anotacoes.py:68-69`, chave `LABEL_STUDIO_USER_TOKEN`). O valor nunca é versionado, e este
  documento não reproduz o caminho nem o conteúdo. Redigido.
- URL, host e porta do LS: o código monta a URL local da API (`exporta_anotacoes.py:100-104`). Este
  documento não replica host, IP ou porta; para reproduzir, aponte o script para a sua instalação (o
  valor default do código é substituível).
- Caminhos do volume do LS (banco, mídia): são o default em `fingerprint_ls.py:23`,
  `monta_v1_detector.py:61` e `exporta_anotacoes.py:50`. Citados aqui por `arquivo:linha`, sem copiar
  o literal para dentro da documentação.
- Identidade de anotador: o CSV guarda o e-mail de quem anotou (`anotador`, `anotadores_distintos`,
  `exporta_anotacoes.py:175-179`). É dado pessoal: fica no conjunto de trabalho e não é reproduzido
  em documento.
- Nome de host de bancada: este documento não nomeia host. O identificador usado como rótulo de
  câmera fica restrito ao mapeamento local de instalação.
- O que o repositório versiona sobre o LS: os scripts (`exporta_anotacoes.py`, `fingerprint_ls.py`,
  `guarda_frescor.py`), os documentos que descrevem o contrato (`ORGANIZACAO.md`, `RECEITA-20260915-pipeline-limpo.md`,
  `MODO-NOVO-LOTE.md`) e as referências externas de dataset
  com licença verificada (`docs/reference/datasets-externos-roboflow.md:12-14`). Não versiona o CSV de
  anotações, os recibos, a mídia, a credencial nem a definição da instalação (§3).

## 8. Limites declarados no próprio repositório

- Ingestão canônica do CSV para manifestos ainda não existe: "ingestão canônica
  `anotacoes-ls.csv -> manifestos lateral/topo` ainda não existe" (`dataset/TRABALHO/ORGANIZACAO.md:100`);
  ver também `:92` ("Treino não consome `anotacoes-ls.csv` diretamente: passa pelo estágio explícito
  de ingestão humana").
- Fotos próprias sem rótulo humano: "fotos próprias 2026-09-14 estão sem labels humanos"
  (`dataset/TRABALHO/ORGANIZACAO.md:101`).
- Corpo precisa de mais anotação: "a decisão de manter `deformidade` no escopo precisa de mais
  anotação de corpo (o piso é ~20 por split)" (medição de 15/09/2026);
  a 4ª classe é experimental, com ~15 instâncias (`:460-461`).
- Topo fora de escopo até haver captura e anotação próprias
  (medição de 15/09/2026, seções 238-239 do relatório do dia).
- Drift de caminho entre o que os documentos citam e o que está versionado:
  `dataset/TRABALHO/RECEITA-20260915-pipeline-limpo.md:25-27` cita explicitamente
  `dataset/TRABALHO/exporta_anotacoes.py` e `dataset/TRABALHO/guarda_frescor.py`, e
  `dataset/TRABALHO/ORGANIZACAO.md:47` lista o par `exporta_anotacoes.py` + `guarda_frescor.py` na
  família "pipeline medido v1" desse mesmo diretório. No HEAD, porém, `guarda_frescor.py` e
  `fingerprint_ls.py` existem apenas em `src-production/treino/` (verificado com
  `git ls-files --error-unmatch`, que falha para `dataset/TRABALHO/guarda_frescor.py` e
  `dataset/TRABALHO/fingerprint_ls.py`). As cópias de `exporta_anotacoes.py` e `monta_v1_detector.py`
  em `dataset/TRABALHO/` estão versionadas e divergem das de `src-production/treino/` na importação de
  `caminhos.py` e na forma de resolver a raiz do repositório.
- Duas trilhas de dados convivem: `dataset/TRABALHO/` (trilha antiga, ainda versionada) e
  `src-production/treino/` ("receita canônica do detector", `src-production/treino/README.md:1-7`, com
  o histórico em `../revisar/treino/`). Os documentos datados de 2026-09-15 ainda apontam para os
  caminhos antigos.
- Não consta no repositório: instalação e versão do LS (imagem, compose, backup do banco); a
  configuração de interface (XML de labeling) do LS; o procedimento de criar lote e importar mídia; a
  política de quem pode anotar (rubrica, instruções, lista de anotadores, citados em
  `ORGANIZACAO.md:15`, ausentes do clone); critério de quantos itens por classe fecham um lote; e
  qualquer medida de concordância entre anotadores além das 8 tarefas de
  Medição do corpus em 15/09/2026.

## 9. Fontes citadas

Código (trilha canônica):

- `src-production/treino/exporta_anotacoes.py:1-14, 30-40, 43-63, 66, 68-69, 72-79, 82-97, 100-104,
  107-112, 115-180, 183-207, 210-226, 241-256, 268-276, 277-302, 308-312`
- `src-production/treino/fingerprint_ls.py:1-10, 23-24, 27-41, 44-48, 51-86`
- `src-production/treino/guarda_frescor.py:1-12`
- `src-production/treino/monta_v1_detector.py:2-13, 16-18, 43-45, 56-61, 64-83, 84, 96-119, 196-210,
  221, 226-239, 248-249`
- `src-production/README.md:57-70` · `src-production/treino/README.md:1-7, 11-29, 64-90`
- `src-production/firmware/esp32cam-test/esp32cam_site.py:1338`
- `code-code-workspace/scripts/classificar_gemini.py:30` · `code-workspace/scripts/validar_pares.py:30`

Documentos e dados:

- `docs/DECISIONS.md:156-170 (D-13), 428-446 (D-25/D-26), 457-471 (D-28), 557-579 (D-31),
  588-606 (D-32), 944-946, 1067-1068`
- `CONTRIBUTING.md:29-33` · `.gitignore:135-137, 144-145`
- `docs/reference/MODO-NOVO-LOTE.md:1-10, 14-19, 23-33, 35-50`
- Medição do corpus em 15/09/2026, no relatório de detecção do dia (documento de trabalho, fora da árvore entregue).
- `docs/reference/datasets-externos-roboflow.md:10-31`
- `dataset/TRABALHO/ORGANIZACAO.md:11-18, 39-56, 89-104`
- `dataset/TRABALHO/RECEITA-20260915-pipeline-limpo.md:7-17, 19-27, 68-75, 77-82`
- `dataset/TRABALHO/filas/novo_lote.sh:1-16, 30, 39-50, 52-88`

Verificações feitas neste clone (comando → resultado): `git rev-parse HEAD` = `db57cd5`;
`git ls-files --error-unmatch dataset/TRABALHO/anotacoes-ls.csv` = falha (não versionado);
`git log --all -- dataset/TRABALHO/anotacoes-ls.csv` e `-- dataset/TRABALHO/_exportacoes` = vazio;
`ls dataset/TRABALHO/anotacoes-ls.csv dataset/TRABALHO/export` = inexistentes;
`grep -c argparse src-production/treino/exporta_anotacoes.py src-production/treino/guarda_frescor.py`
= 0 em ambos; `--help` de `fingerprint_ls.py` e `monta_v1_detector.py` executados com rc=0 (saída
reproduzida em §6).
