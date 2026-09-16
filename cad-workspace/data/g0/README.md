# Dados G0

Este diretório guarda o instrumento de coleta do G0: o formulário, o checklist de campo, um canário sintético e as referências comerciais. **Ainda não há medição da bancada aqui.** O `canary.yaml` é sintético e só verifica o pipeline.

## Convenção

```text
<equipment>-<tipo>-<revision>.yaml      tipo: reference | g0 | g0-photo
```

Exemplos reais deste diretório:

```text
esteira-a-reference-r01.yaml
esteira-b-g0-template.yaml
esteira-b-g0-photo-r02.yaml
```

Cada entrada deve registrar unidades, sistema XYZ, instrumento, método, repetições, incerteza, fotos e estado de evidência. Não substituir medições brutas; criar nova revisão quando houver correção.

## Bloqueio

A coleta deve parar se faltarem dados necessários ao gate. Não usar dimensões genéricas de relatórios comerciais para preencher este arquivo.

## Vocabulário de estado

Um estado por grandeza, em um campo só: `measured` · `reference` · `speculative` · `BLOCKED`.
Sem triades de negação no mesmo registro (não declarar `measured: false` ao lado de
`fabrication_allowed: false` e um terceiro booleano dizendo o mesmo). Desconhecido é `null`.

`reference` é dado de catálogo ou relatório comercial: nunca vira `measured`, e não se transfere
para a seção de medições. Foto sem escala física não produz valor dimensional, só observação;
e observação vai como `BLOCKED`, com o motivo em uma linha.

## O que não pertence a estes arquivos

Estas regras são do diretório, não de cada registro: identidade não confirmada, ausência de escala,
dado comercial que não é da unidade, datum que é candidato, estado de evidência que não equivale a
aprovação de gate. Não repetir em cada YAML. O arquivo carrega o dado; a ressalva fica aqui.
