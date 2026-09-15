# Resultados medidos — 2026-09-15

Evidência por NÚMERO e sha256 do arquivo original (o JSON bruto contém caminho absoluto
e nome de host, por isso não entra no repositório — a política de sanitização proíbe).
Originais em `<diretório de modelos>/` (ver RECEITA). Contaminados do dia (base que viu o
teste, split antigo) NÃO estão aqui: seguem marcados como inválidos no relatório.

## Candidato v5 (base limpa, sem as imagens da equipe) — teste próprio 18 imagens

| classe | mAP50 | mAP50-95 |
|---|---|---|
| normal | 0.695 | 0.254 |
| tampa_ausente | 0.995 | 0.474 |
| defeito_tampa | 0.636 | 0.267 |

Origem: v5/avaliacao-teste-limpo.json · sha256 `aa3c90d024fddd8d`

## Candidato v6a (com as imagens da equipe) — teste próprio 18 imagens

| classe | mAP50 | mAP50-95 |
|---|---|---|
| normal | 0.738 | 0.199 |
| tampa_ausente | 0.693 | 0.223 |
| defeito_tampa | 0.448 | 0.201 |

Origem: v6a/avaliacao-teste-proprio.json · sha256 `149ec3e6d948140e`

## Tabelas de limiar (F1 macro por limiar)

| modelo | 0,05 | 0,15 | 0,30 | origem / sha256 |
|---|---|---|---|---|
| v5 (3 classes) | 0.525 | 0.692 | 0.806 | `limiares-teste-limpo.json` · `a5c17a66c00cbb0f` |
| v6a (3 classes) | 0.524 | 0.711 | 0.605 | `limiares-teste.json` · `793585653a7ee6d1` |
| v6b (4 classes, corpo) | 0.492 | 0.594 | 0.696 | `limiares-teste-corpo.json` · `eac9fefe451de763` |

## Decisão por imagem (candidato v6a)

| limiar | acurácia |
|---|---|
| 0.15 | 11/18 = 0.611 |
| 0.3 | 10/18 = 0.556 |

Origem: `evidencia-v6-3-rig-test.json` · sha256 `6470dd50c211dc0d`

## k-fold por item (protocolo de entrega: base limpa + ajuste fino em cada dobra)

- dobras: 5
- mAP50 média ± desvio: **0.6708 ± 0.1487** [0.5123–0.9187]
- mAP50-95 média: 0.2743 ± 0.1018
- listas das dobras em `<dataset>/kfold-listas/` (auditáveis)
- sha256 do JSON: `03f64114df0c7272`

## Topo (modelo KMITL medido nas nossas 40 capturas)

| entrada | acurácia |
|---|---|

Origem: `avaliacao-nossas-capturas.json` · sha256 `4266c01c4fbfc7e4`
