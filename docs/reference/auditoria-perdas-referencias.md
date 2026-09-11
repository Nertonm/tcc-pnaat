# Auditoria de perdas: sessões, pastes, vault e repositório (2026-09-11)

Pergunta: *nenhuma referência ou informação foi perdida?*

## Método (o que foi efetivamente varrido)

| Fonte | Volume | Como |
|---|---|---|
| Banco de sessões do assistente (fora do repo) | **1452 sessões** (06/07→11/09); **450 mencionam PNAAT** | SQL direto no banco |
| Pastes em disco | 675 arquivos | inventário + leitura dos relevantes |
| Cópias de notas do vault em `/root` | 8 notas PNAAT + 6 prompts de deep research | leitura dos leads |
| Repositório (`github`) | `docs/`, `latex-workspace/`, `code-workspace/` | grep termo a termo das referências citadas nas sessões |
| Downloads do <host> | PDFs do período | inspeção de metadados/texto |

## Perdas confirmadas e remediação

| # | O que | Evidência de que estava perdido | Remediação |
|---|---|---|---|
| 1 | **`Jarvis-BITS/bottle-defect-detection`** (referência pedida em 08/09: "faça a analise disso também") | aparecia só como resultado de busca em 1 sessão (27/08) e em nenhum arquivo do repo | **ingerido agora**: `docs/reference/ref-jarvis-bits-bottle-defect-detection.md` (commit SHA `80c68a9`, 740 imagens, Mask-RCNN + CNN 87,7%/72%) |
| 2 | **Rubrica da Entrega 1** (paste de 08/09, 70 linhas) | não existia no repo; só na pasta de pastes | **recuperada**: `docs/reference/rubrica-entrega1.md` + conferência item a item do entregue |
| 3 | **Notebook `02_classificador_leve_int8.ipynb`** (MobileNetV3-Small INT8) | `*.ipynb` está no `.gitignore` → os 3 notebooks não eram versionados | **versionados** (negation no `.gitignore`), 01/02/03 commitados |
| 4 | **Linhagem de deep research v1–v6** (5 rodadas sem resultado capturado) | existem os 6 prompts, mas só **1** resultado (PET) está no repo | **mapeado**: `docs/reference/mapa-vault-e-deep-research.md` declara qual rodada tem resultado e qual não |
| 5 | **Notas de vault** (escopo, requisitos-artefatos, dados-telemetria, análise estratégica, ciclo-1, minha-participação, referências técnicas, apostilas 278/279) | nenhuma era referenciada no repo | **indexadas** no mesmo mapa (com caminho e lead) |
| 6 | **Evidência do controle MVTec** (40 imagens, todas "erro" por quota 429) | só em `/root/pnaat/mvtec_ctrl.log` | **registrada** no mapa (inconclusivo — não é evidência de qualidade) |

## Investigado e **não** era perda (evitar retrabalho)

| Item | Conclusão |
|---|---|
| `Fast_Method_of_Detecting_Packaging_Bottle_Defects_.pdf` (Downloads) | **é o mesmo artigo** já ingerido: metadata `JS_9518910` = J. Sensors vol. 2022, Article ID 9518910, "Fast Method of Detecting Packaging Bottle Defects Based on ECA-EfficientDet" (Sheng & Wang) → alias do `ref-eca-efficientdet-packaging-bottle-defects.md` |
| `pnaat-research.py` / `pnaat-search-results.json` (11/09) | são do workstream **CAD** (DIN rail, clamps Winford/Printables), não do TCC |
| `pnaat-act2-test_camera.jpg` e JPGs de referência | mídia — fora do git por política declarada ("não suba as fotos") |
| Sessões antigas (jul/ago) com "jarvis" | 11 sessões, mas o termo aparece como *personalidade de agente* (`soul-dot-md`) na maioria — só 1 sessão tinha o repo de garrafas |

## Lacunas que permanecem (com dono)

| Lacuna | Dono | Como fechar |
|---|---|---|
| Canonicidade das notas: `/root/*.md` são **cópias de trabalho**, não o vault | usuário/agente no host do vault | confirmar no vault `10-Projects/pnaat-residencia/` que as notas estão publicadas com o mesmo conteúdo |
| Resultados das rodadas v2–v6: ou foram destilados nas 4 notas de TCC, ou não existem | usuário | se existirem colados em sessões, ingerir; se não, marcar como "não executada" |
| Nome do PDF entregue contém "template" | usuário | renomear antes da submissão |
| Push do repositório (17+ commits à frente do origin) | usuário | requer credencial |
| 450 sessões de PNAAT não são auditáveis uma a uma por leitura | — | o banco de sessões é a fonte; este relatório indexa as referências, não o histórico completo |

## Veredito

**Três perdas reais** (referência Jarvis, rubrica da Entrega 1, notebooks não versionados) e **duas
lacunas de rastreabilidade** (linhagem de deep research e notas de vault sem índice) — todas
remediadas nesta auditoria. **Nenhuma referência citada no entregue ficou sem origem verificável**
(as citações do deep research PET estão verificadas material a material em
`verificacao-materiais-deep-research.md`).
