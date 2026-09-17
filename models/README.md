# Modelos treinados: acervo, indice e publicacao

`INDEX.csv` e a lista de todo peso treinado deste projeto: id, familia, run, sha256, bytes,
imgsz/epocas quando o run declara, metrica de validacao quando existe e o caminho de origem.
Nao ha numero sintetizado: campo vazio significa que a medida nao foi encontrada ao lado do peso.

**Pacotes publicados:** [https://huggingface.co/Nerton/pnaat-modelos](https://huggingface.co/Nerton/pnaat-modelos). Detalhes e o recibo dos sha256 na seção
"Publicacao no Hugging Face", no fim deste arquivo.

Estado do indice: 158 pesos em 35 familias, gerado em 2026-09-16.

Para reindexar depois de treinar:

```sh
make -C src-production indice-modelos
```

## O peso nao entra no git, mas tem de ser publicavel

Peso e dado, nao codigo: nao vai para o git. Mas entregavel que ninguem consegue baixar nao e
entregavel. A ponte entre as duas coisas e o **DVC**: o git guarda um ponteiro pequeno
(`models/ENTREGA.dvc`) e o conteudo vive no *store* do DVC.

O que esta versionado por DVC: **os pacotes de entrega** (`models/ENTREGA/<pacote>/`), que sao
pequenos (~6 MB cada) e sao exatamente o que se entrega:

```text
models/ENTREGA/<pacote>/
    <peso>.pt                 o peso treinado
    modelo.json               contrato do modelo (classes, imgsz, limiar)
    <peso>.meta.json          metadados do treino
    preprocessamento.json     contrato de pre-processamento (quando existe)
    metadados-treino.json     proveniencia do run (quando existe)
    SHA256SUMS                conferencia do pacote inteiro
    LEIA-ME.md                como usar
```

Os runs brutos (o acervo de origem, varios GB) continuam fora do DVC: o que se publica e o
pacote, nao o historico de treino.

## Como publicar

```sh
dvc add models/ENTREGA      # cria/atualiza models/ENTREGA.dvc e models/.gitignore
git add models/ENTREGA.dvc models/.gitignore .dvc/config
dvc push                    # envia o conteudo para o store
```

## Como consumir

```sh
git clone <repo> && cd <repo>
dvc pull                                  # baixa os pacotes do store
sha256sum -c models/ENTREGA/<pacote>/SHA256SUMS
```

A conferencia em dois niveis e proposital: o DVC identifica o objeto por **md5** (convencao da
ferramenta), enquanto o projeto mede por **sha256** (`INDEX.csv` e o `SHA256SUMS` de cada pacote).
Depois do `dvc pull`, quem verifica integridade usa o `SHA256SUMS`, que viaja junto com o pacote.

## Store

O store e declarado em `.dvc/config` (`core.remote`). Hoje aponta para um diretorio local, o que
prova o mecanismo de ponta a ponta (add, push, apagar artefato e cache, pull, conferir sha256).
Trocar por um destino externo e mudar uma linha:

```sh
dvc remote modify local url <novo-destino>
```

Publicacao externa (para quem nao tem acesso a este host) ainda **pendente**: depende de escolher
o destino.

## Pendencias

- **`models/ENTREGA/v7a-lateral/SHA256SUMS` esta defasado**: o `LEIA-ME.md` do pacote foi editado
  depois do manifesto, entao `sha256sum -c` acusa FAILED nesse arquivo. O peso, o `modelo.json` e
  os metadados conferem. O defeito existe tambem no acervo de origem; a correcao e regerar o
  manifesto do pacote, decisao de quem e dono do entregavel.
- Destino externo do store (fora deste host).

## Publicacao no Hugging Face

Repositorio: `https://huggingface.co/Nerton/pnaat-modelos` (publico), enviado em
2026-09-16 (commit `b3f099b`). Contem os 7 pacotes de entrega com o peso, o contrato do
modelo, os metadados, o contrato de pre-processamento e o `SHA256SUMS` de cada pacote.

### Por que o peso publicado difere do interno

Os checkpoints originais carregam, no proprio arquivo, os caminhos de treino
(`<acervo-de-modelos>/...`, `<repositorio>/...`): e assim que o framework de treino grava os
argumentos. Publicar o arquivo como esta publicaria o caminho da instalacao. O peso
publicado foi re-serializado com esses campos trocados por marcador.

A prova de que o modelo **nao mudou** e a predicao: o mesmo quadro passa pelo peso original
e pelo saneado, e a diferenca maxima entre as saidas (caixas, confianca, classe) foi
**0.00e+00** nos 7 pacotes. Sem essa igualdade, nada seria publicado.

| pacote | sha256 no INDEX.csv | sha256 do arquivo interno | sha256 publicado | baixar |
|---|---|---|---|---|
| `corpo-cls` | ce537925c6553754... | ce537925c6553754... | c474243c9cd1b5d2...  [corpo-cls](https://huggingface.co/Nerton/pnaat-modelos/tree/main/corpo-cls) |
| `corpo-detector` | 06b81f85b40c10ec... | 06b81f85b40c10ec... | a32f9f1bd4b69f67...  [corpo-detector](https://huggingface.co/Nerton/pnaat-modelos/tree/main/corpo-detector) |
| `v7a-lateral` | b92be4f42ccfa58f... | b92be4f42ccfa58f... | 258879d60827877f...  [v7a-lateral](https://huggingface.co/Nerton/pnaat-modelos/tree/main/v7a-lateral) |
| `v8a-lateral` | 75fd0e3d1e79c75b... | 75fd0e3d1e79c75b... | 398d071e85bdd5f6...  [v8a-lateral](https://huggingface.co/Nerton/pnaat-modelos/tree/main/v8a-lateral) |
| `v9a-lateral` | ad4e16f4f6b016bf... | ad4e16f4f6b016bf... | 42c8b804f2417a2b...  [v9a-lateral](https://huggingface.co/Nerton/pnaat-modelos/tree/main/v9a-lateral) |
| `v9b-lateral` | ab05f35a63f68098... | ab05f35a63f68098... | d14d29b7c150bd1b...  [v9b-lateral](https://huggingface.co/Nerton/pnaat-modelos/tree/main/v9b-lateral) |
| `v9b-lateral-calibrado` | ab05f35a63f68098... | ab05f35a63f68098... | 941b19b9c83a4f0f...  [v9b-lateral-calibrado](https://huggingface.co/Nerton/pnaat-modelos/tree/main/v9b-lateral-calibrado) |

As duas primeiras colunas conferem entre si (o `INDEX.csv` descreve o arquivo interno; a
marca `=` confirma). A terceira e o que esta no Hub, e o `SHA256SUMS` de cada pacote
publicado descreve exatamente esses arquivos. Nao se compara a terceira com as duas
primeiras: sao dominios diferentes.
