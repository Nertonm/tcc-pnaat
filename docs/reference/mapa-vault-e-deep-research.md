# Mapa: vault PNAAT, prompts de deep research e o que o repositório captura

Data: 2026-09-11. Motivo: o repositório só captura **parte** da linhagem do projeto. Sem este mapa,
notas e rodadas de pesquisa ficam órfãs (e foi exatamente o que aconteceu com a referência Jarvis e
com a rubrica da Entrega 1).

## Linhagem de deep research (6 prompts, 1 resultado capturado)

| Prompt | Tema | Resultado no repositório? |
|---|---|---|
| `prompt-deep-research-tcc-pnaat.md` (v1) | escopo + critérios de pontuação do TCC | **não** |
| `...-v2.md` | SOTA de inspeção multi-view + rastreabilidade; critérios que maximizam nota | **não** |
| `...-v3-metodologia.md` | como a indústria real faz (linhas de envase) → refinamento de metodologia | **não** |
| `...-v4-fora-da-caixa.md` | soluções fora da caixa + camada de telemetria/dados | **não** |
| `...-v5-destaque.md` | validação de 6 diferenciais (existe? viável? custo/risco?) | **não** |
| `...-v6-generalizacao.md` | generalização: grandezas universais + IA de borda | **não** |
| *(rodada avulsa)* **PET / pré-processamento** | pipeline ótimo de aquisição e pré-processamento PET | **SIM** — `docs/reference/deep-research-preprocessamento-pet-resultado.md` + verificação material-por-material |

Localização das cópias de trabalho: `/root/prompt-deep-research-tcc-pnaat*.md` (14/08/2026).
Canônico: vault `10-Projects/pnaat-residencia/` (a confirmar — as cópias em `/root` **não** são canônicas).

## Notas do vault que sustentam as decisões (`10-Projects/pnaat-residencia/`)

| Nota | Conteúdo (lead verificado em cópia de 14-15/08) | Onde o repo usa |
|---|---|---|
| `moc-pnaat-residencia.md` | MOC do programa: fases, bolsas, anexos, links oficiais | não referenciado |
| `pnaat-tcc-escopo-2026.md` | escopo: inspeção multi-view de envase + rastreabilidade multi-nó | `docs/escopo.md` (derivação) |
| `pnaat-tcc-requisitos-artefatos-2026.md` | RF/RNF, diagrama, mapa de valor, pitch, cronograma, aceite | `docs/requisitos*.md` + `latex-workspace/` |
| `pnaat-tcc-dados-telemetria-2026.md` | schema SQLite, taxonomia AQL-inspired, eixos fora da caixa | `docs/dados-telemetria.md` |
| `edit-pnaat-analise-estrategica-2026.md` | critérios de avaliação, caminho crítico, riscos, ações | `docs/` (parcial) |
| `edit-pnaat-ciclo-1.md` | hub do Ciclo 1: aulas, materiais, entregas, log | não referenciado |
| `edit-pnaat-minha-participacao.md` | tracking da participação (aprovado, fases) | não referenciado |
| `edit-pnaat-referencias-tecnicas-2026.md` | ESP-IDF/Kconfig, Heltec LoRa 32 V3, Edge Impulse (todas HTTP 200 em 10/08) | não referenciado |
| `pnaat-apostila-tcc-2026` (Calibre 278) | apostila do módulo TCC | citada no entregue |
| `pnaat-cenarios-tcc-2026` (Calibre 279) | cenários de projeto do TCC | origem do "Cenário 1" |
| `pnaat-apostila-embarcados-iot-2026` | apostila de Sistemas Embarcados e IoT (MQTT/edge) | não referenciado |

## Evidências locais (fora do git por política, mas registradas)

| Artefato | O que é | Estado |
|---|---|---|
| `/root/pnaat/mvtec_ctrl.log` (+ `mvtec_ctrl/`) | controle do rotulador no MVTec: 40 imagens, **todas com erro 0.00** (quota 429 do pool) → **inconclusivo**, não é evidência de qualidade | registrado no relatório de perdas |
| `/root/pnaat/origem/` | cópia local das 81 frames (o canônico é `datasets/pnaat/origem`) | duplicata de trabalho |
| `/root/pnaat/classificar_gemini.py`, `classificar_rest.py` | rotulador (versão local) | versão do repo: `code-workspace/scripts/` |
| `/root/pnaat-act2-test_camera.jpg`, `pnaat-aula1-*evidencias.txt` | evidências das atividades do Ciclo 1 (câmera/LED) | fora do git (mídia) — manter |
| `/root/pnaat-stage0/`, `pnaat-stage1-evidence/`, `pnaat-din-parts/` | evidência CAD (DIN rail, clamps, Winford/Printables com SHA-256) | fora do repo de código |

## Ação

Este mapa é o índice que faltava: a partir de agora, citar no repositório a nota de vault de origem
de cada decisão (e registrar aqui quando uma rodada de deep research não tiver resultado capturado).

---

# Revisão 2 (2026-09-11) — inventário canônico e correções

## Correções

1. **Os resultados das rodadas v2–v6 existiam** (pastes do assistente, fora do repo) — o repo é que não os tinha.
   Agora estão em `docs/reference/deep-research-tcc-pnaat/` (verbatim + sha256 em `INDEX.md`).
2. **Cópias em `/root` não são canônicas e podem enganar.** Comparação sha256 com o vault:
   `pnaat-tcc-escopo-2026`, `pnaat-tcc-requisitos-artefatos-2026` e `pnaat-tcc-dados-telemetria-2026`
   **diferem apenas por uma linha `moc: moc-pnaat-residencia`** no frontmatter (o vault tem, a cópia
   não); o conteúdo é o mesmo. `moc-pnaat-residencia` é idêntico. **Regra:** comparar hash e olhar o
   diff antes de afirmar defasagem.
3. **Regra de autoridade (do próprio vault)**: `pnaat-tcc-workspace-2026` estabelece que *o
   repositório é a autoridade para o estado de implementação e decisão; as notas do vault são
   contexto e devem ser lidas como proposta quando não houver receipt no repositório*. Mantida.

## Inventário canônico (vault do projeto, 36 notas PNAAT)

**10-Projects/pnaat-residencia/** (14): moc-pnaat-residencia · pnaat-analise-estrategica-2026 ·
pnaat-ciclo-1 · pnaat-minha-participacao · pnaat-tcc-cad-approach-deep-research-2026-09-10 ·
pnaat-tcc-dados-telemetria-2026 · pnaat-tcc-escopo-2026 · pnaat-tcc-grip-extensivel-2026 ·
pnaat-tcc-requisitos-artefatos-2026 · pnaat-tcc-sessao-2026-08-31 · pnaat-tcc-trigger-deteccao-passagem-2026 ·
pnaat-tcc-trigger-sensores-followup-2026 · pnaat-tcc-workspace-2026

**30-Resources/** (6): pnaat-datasets-tcc-2026 · pnaat-centro-execucao-2026 ·
pnaat-entrega-1-documento-requisitos-2026 · pnaat-notebook-mobilenet-transfer-learning-reference-analysis ·
pnaat-subapostila-bno085-mqtt-2026

**50-Sources/** (17): apostila-tcc (+source-map) · apostila-embarcados-iot · aula2-containers ·
aula3-mlops-ci-cd · aula4-streaming-datasets · aula6-arquiteturas-visao · aula7-observabilidade-edge-ai ·
tools-map-aulas-4-5 · manual-laboratorio · calendario-intensivo · pi5-gpu-compositing ·
referencias-tecnicas · desafio-mqtt-led · edital-residencia-tic-47 · anexos-completos ·
anexo-iii / anexo-xix · aprovados-cariri · agenda-publica · materials/ (source cards de aula 6 e do
notebook MobileNet)

**00-System/reports/** (2): pnaat-ciclo1-ingest-rotas-20260810 · pnaat-closeout-sessao-20260810

## Quais notas importam para o estado atual do repo

| Nota do vault | Por que importa agora |
|---|---|
| `pnaat-tcc-workspace-2026` | contrato de workspace (CTGit = fonte operacional, `github/` = publicação) e regra de autoridade |
| `pnaat-datasets-tcc-2026` | desenho de dataset anterior ao nosso pipeline atual → confrontar com `datasets/pnaat/README.md` |
| `pnaat-notebook-mobilenet-transfer-learning-reference-analysis` + source card/map | base do nosso notebook 02 (classificador leve INT8) |
| `pnaat-aula7-observabilidade-edge-ai-2026` | normativo de observabilidade (CPU/RAM/temperatura/**tempo de inferência**; Prometheus/Grafana) |
| `pnaat-tcc-trigger-*` (2 notas) | decisão do trigger (E18/VL53L0X/KY-040) que sustenta a PoC-01 |
| `pnaat-tcc-cad-approach-deep-research-2026-09-10` + `docs/design/grip-extensivel.md` | toolchain CAD (build123d+OCP) e o grip |
| `pnaat-entrega-1-documento-requisitos-2026` | requisitos da Entrega 1 (par da rubrica recuperada) |
| `pnaat-centro-execucao-2026` | centro de execução (referência de operação) |

## Notas técnicas do vault indexadas nesta revisão (source cards e mapas)

| Nota | Conteúdo |
|---|---|
| `pnaat-notebook-mobilenet-transfer-learning-reference-source-card` | C1 do notebook MobileNet (transfer learning) — base do nosso notebook 02 |
| `pnaat-notebook-mobilenet-transfer-learning-reference-source-map` | C2 do mesmo material |
| `pnaat-aula-6-arquiteturas-visao-computacional-source-card` | C1 da aula 6 (arquiteturas de visão computacional) |
| `pnaat-source-map-2026` | mapa de fontes do programa |

Notas de programa (edital, anexos, agenda, atividades de aula, apostilas) ficam registradas como
**contexto fora do escopo do repo de engenharia** — o auditor as lista em bucket separado (`VP`).

## Nota canônica criada nesta revisão (vault)

| Nota | Conteúdo | Commit no vault |
|---|---|---|
| `50-Sources/pnaat-tcc-referencias-verificadas-2026` | Casos que mudam decisão (misatribuição, erro físico, não verificável, quote truncado, alias) + 5 regras de uso + onde está o material completo | `41aed00` (6/6 gates, readback verificado) |

Regra de leitura: o vault é autoridade de **contexto**; o repositório é autoridade de **estado de
implementação e decisão** (ver `pnaat-tcc-workspace-2026`).
