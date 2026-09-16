# Modelos treinados: acervo e indice

`INDEX.csv` e a lista de TODO peso treinado deste projeto: id, familia, run, sha256, bytes,
imgsz/epocas quando o run declara, metrica de validacao quando existe e o caminho de origem.
Nao ha numero sintetizado: campo vazio significa que a medida nao foi encontrada ao lado do
peso.

O peso NAO entra no repositorio (dado, nao codigo). O acervo canonico fica fora do clone, no
diretorio irmao:

```text
<pai do clone>/modelos/<familia>/<tag>/<peso>.pt     copia conferida por sha256
<pai do clone>/modelos/ENTREGA/<pacote>/            pacotes de entrega como estao
```

A origem (o diretorio de runs em `PNAAT_MODELOS`) e somente leitura: nada e movido nem
apagado de la. Para reindexar depois de treinar:

```sh
make indice-modelos
```

Estado do indice: 158 peso(s) em 35 familia(s), gerado em 2026-09-16T21:10:30+00:00.
