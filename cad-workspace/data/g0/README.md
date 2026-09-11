# Dados G0

Este diretório recebe medições reais da bancada. O arquivo `canary.yaml` é sintético e serve somente para verificar o pipeline.

## Convenção

```text
<equipment>-<revision>.yaml
```

Exemplos:

```text
esteira-b-g0-r01.yaml
esteira-a-g0-r01.yaml
```

Cada entrada deve registrar unidades, sistema XYZ, instrumento, método, repetições, incerteza, fotos e estado de evidência. Não substituir medições brutas; criar nova revisão quando houver correção.

## Bloqueio

A coleta deve parar se faltarem dados necessários ao gate. Não usar dimensões genéricas de relatórios comerciais para preencher este arquivo.
