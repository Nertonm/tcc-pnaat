---
tags: [type/reference]
aliases: []
lead: "Datasets de tampa do Roboflow: contagens reais por classe, licenca e digest."
created: 2026-09-11
modified: 2026-09-11
review_status: reviewed
---

# Datasets externos Roboflow (tampa): pull de 2026-09-11

Baixados via CLI (`roboflow version create` raw + `version download -f yolov8`) no host de trabalho, em
`datasets/externos/` (midia fora do git; aqui ficam so as contagens e digests).
Licenca **CC BY 4.0** confirmada via API e no `data.yaml` de cada export.

| projeto | imagens | splits (tr/va/te) | classes: instancias |
|---|---|---|---|
| `bottle-defect-detection-c6ts8` | 262 | 262/0/0 | label=266, not-crumbled=203, cap=180, no-cap=146, crumbled=120 |
| `bottle-lte35-abhgw` | 103 | 72/21/10 | Missing cap=35, Unclosed=35, Closed=35 |
| `bottle_cap_sdp-3v0vj-qzaan` | 3554 | 1303/1211/1040 | good_cap=2020, wet_cap=394, open_cap=311, damaged_cap=309, no_cap=270, misplaced_cap=248 |
| `dataset-joren-newest-a4vuy` | 570 | 399/114/57 | Good Cap=218, No Cap=162, Loose Cap=124, Broken Cap=54, Broken Ring=48 |
| `original-zotc7-1j0kr` | 685 | 480/107/98 | defect=360, good=138, ring-missing=111, loos-cap=77, no-cap=46 |

## Leitura para a PoC-02

- `bottle_cap_sdp` e `dataset-joren-newest` sao os que tem as classes que decidem a tampa:
  `no_cap`, `misplaced_cap`, `Loose Cap`, `Good Cap`: juntos passam de 600 instancias de ausencia/ma posicionamento.
- `original-zotc7` acrescenta `ring-missing` (anel de lacre) e `defect`.
- `bottle-defect-detection` e o dataset do paper IJARCCE (deteccao de `no-cap` em agua).
- Uso correto: benchmark de metodo (a arquitetura leve separa `good` / `loose` / `no_cap`?) e bootstrap.
  A validacao do RNF-02 continua sendo a matriz de confusao na nossa bancada.
