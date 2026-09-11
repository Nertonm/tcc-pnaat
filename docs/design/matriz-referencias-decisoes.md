# Matriz: referências × pontos de decisão (PNAAT, 2026-09-11)

Regra: só decidir depois de confrontar **todas** as referências que temos. Cada conflito é explicitado;
cada convergência vira recomendação. Números de terceiros com a métrica declarada.

## Referências (R)

| # | Referência | O que traz (verificado) |
|---|---|---|
| R1 | **Deep research PET** (ingest `deep-research-preprocessamento-pet-resultado.md`) | óptica antes do modelo; backlight difuso p/ geometria, polarização cruzada p/ corpo; flat-field, TM piramidal, Canny+elipse de **mínimos quadrados diretos (Halir)** com RANSAC; máscara de especular em vez de inpaint; fusão em nível de decisão; HDR bracketing inviável na borda; isolation gate p/ defeito sintético; pitfalls: deriva térmica, condensação, vibração |
| R2 | **ECA-EfficientDet** (J. Sensors 2022, DOI 10.1155/2022/9518910) | detecção **supervisionada** one-stage p/ defeitos de **tampa e rótulo**; mAP **99,16%** com 1200 amostras; transfer learning + mosaic + channel attention |
| R3 | **Pysource** (blog, inspeção em esteira) | pipeline **object detection + tracking** com ID único, evidência por item, banco SQL, dashboard e "% de erro por lote" |
| R4 | **PatchCore** (arXiv 2106.08265) | one-class sem treino no alvo; AUROC **até 99,6%** (ensemble MVTec); memory bank coreset; uso de features ImageNet |
| R5 | **FastFlow** (arXiv 2111.07677) | normalizing flow 2D; paper **99,4%** AUC; reimplementação Anomalib **0,916–0,947** (discrepância de protocolo) |
| R6 | **CutPaste** (arXiv 2104.04015) | **aprende anomalia a partir de irregularidade sintética** (cut-and-paste) com só OK: **95,2** AUC scratch / **96,6** transfer |
| R7 | **arXiv 2409.15980** (AD em Raspberry Pi) | no Pi: PatchCore com 20 fotos normais; **F1>0,95** com 10 normais; **CFlow/FastFlow mais lentos e menos eficazes** que PaDiM/PatchCore |
| R8 | **anomalib 2.6.1** (doc/instalado) | modelos disponíveis: `Patchcore`, `Padim`, `Fastflow`, `EfficientAd`; **não há CutPaste**; datamodule `MVTecAD` |
| R9 | **Nosso piloto** (empírico) | MVTec bottle: PatchCore image_AUROC **1,0**; PaDiM **0,999**; aplicado às **nossas 81 frames**: **todas ≈1,0** → *domain gap* |
| R10 | **DECISIONS D-01..D-22** | D-07 medição mm da tampa; D-11/12 detector evolutivo na borda; D-19 ESP32 (sensores/tempo real) × Pi 5 (inferência); D-20 E18-D80NK como presença; D-22 núcleo × evolutivo |

## Matriz de decisão

| Ponto | R1 | R2 | R3 | R4-R7 | R8 | R9 | R10 | Conflito? | Recomendação (simples + eficiente + SOTA-consistente) |
|---|---|---|---|---|---|---|---|---|---|
| **1. Dataset: raw + pipeline versionado** | pipeline determinístico é o núcleo | — | — | — | — | — | D-16 testabilidade | não | **adotar** (raw canônico + `rig_id`/`pipeline_version`; cache descartável) |
| **2. Origem do defeito: sintético** | isolation gate exige verificação | 1200 amostras reais → supervisionado funciona | — | **CutPaste prova que anomalia sintética treina** | — | proxy não transfere | D-02 composição | R1 alerta realismo × R6 apoia síntese | **patch composto (modo B) + gate**; validar realismo com 2-3 defeitos reais quando houver |
| **3. Camada de geometria (Halir/silhueta)** | Canny+LS+RANSAC <1 ms | DL p/ multi-categoria | tracking p/ ID | — | — | — | **D-07 mm da tampa** | R1/R10 (determinístico) × R2 (DL) | **geometria determinística** para tampa/deformação; DL só para aparência |
| **4. Camada de aparência** | — | EfficientDet-Lite p/ tampa/rótulo | detecção+classificação | PatchCore/PaDiM SOTA one-class | EfficientAd (borda) | domain gap | D-11 detector evolutivo | R2 (supervisionado precisa rótulo) × R4 (OK-only, sem classe) | **começar com one-class anomalib (PatchCore/PaDiM)** como baseline; aluno leve/EfficientDet-Lite quando houver rótulo |
| **5. Classe do defeito (RF-02/03/04)** | — | classificador supervisionado | — | one-class **não dá classe** | — | — | D-07 | **conflito real**: one-class não atende RF-02/03/04 sozinho | **híbrido**: classe por geometria + classificador leve; one-class = novidade/incongruência |
| **6. Modelo na borda** | HDR/bracketing inviável | — | Jetson/laptop no blog | PatchCore pesado; CutPaste leve | EfficientAd p/ borda | — | D-12 execução evolutiva | R7 (Pi: evitar flow) × R4 (SOTA pesado) | **PatchCore/PaDiM só como baseline; alvo de borda = aluno INT8 + EfficientAd** |
| **7. Rig/óptica** | backlight + polarização cruzada | — | webcam única | — | — | domain gap medido | D-19/D-20 | R1 pede óptica dedicada × simplicidade R3 | **rig-v0 (atual)** para dataset; **v1** (backlight tampa + polarizado corpo) só após validar inclinação com 1 vista |
| **8. Nº de câmeras** | métrica de tampa priorizada na câmera alta-direita | — | 1 câmera | — | — | — | **2 câmeras obtusas (vigente)** × reports CAD 3CAM | **sim** (CAD 3CAM × decisão 2) | manter **2**; 3ª (topo) só se a tampa não separar no gate (critério declarado) |
| **9. Fusão** | nível de decisão | — | tracking dá ID | — | — | — | D-04 fusão multi-view | R1 "tampa só numa câmera" × nossa fusão usa as duas | **decisão determinística nas duas** (priorizando a de tampa), discordância → análise humana |
| **10. Rotulagem** | validação rigorosa, sem métrica-lisonja | — | — | — | — | 2 FP da IA | — | nenhuma referência apoia IA como verdade | **IA = triagem**; `defective` só por par validado; revisão visual no volume pequeno |
| **11. Avaliação** | métricas de qualidade (CNR/Tenengrad/especular) | mAP por classe | erro por lote | AUROC | — | domain gap | D-14 rigor de processo | não | **AUROC/mAP no nosso dataset + gate RNF-02**, split por sessão (declarar exceção com 1 sessão) |
| **12. Histórico do repo** | — | — | — | — | — | — | — | — | **aditivo** (rótulo/índice/mapa), sem reescrever (decisão do usuário) |

## Convergências (o que todas as referências sustentam juntas)

1. **Óptica e geometria antes do modelo** — R1 + R10(D-07) + o custo medido no Pi (R7). DL é a camada de aparência, não a de medição.
2. **OK-only é viável e barato** — R4/R6/R7/R9 (com a ressalva do domain gap, R9).
3. **Modelo leve para borda, pesado só como baseline** — R7 + R8 (EfficientAd disponível) + R5 (flow penalizado no Pi).
4. **Sintético é legítimo, desde que verificado** — R6 (método) + R1 (gate de isolamento) → nosso gate já mede isso.
5. **Rastreabilidade por item (ID/evidência/banco/dashboard)** — R3 + RF-05/07 entregues.
6. **Classe exige supervisão** — R2 + nossos RF-02/03/04 → geometria + classificador, não só anomalia.

## Divergências que permanecem (e como ficam)

- **R1 manda iluminação assimétrica dedicada; R3 usa webcam simples** → adotamos o esqueleto de R1, mas **em duas etapas** (v0 agora, v1 depois) para não travar o dataset.
- **R2 (DL supervisionado, 99,16% mAP) vs nosso cenário sem defeitos rotulados** → DL entra quando houver dado; até lá, geometria + one-class.
- **R1 diz "métrica de tampa só na câmera alta-direita"** → adotamos como *prioridade*, não exclusão (R10/D-04 manda fundir).
- **R4 (PatchCore 99,6%) vs R7 (Pi limitado)** → PatchCore fica como teto de referência, não como alvo de borda.

## Decisão mínima coerente com tudo (o que sobra depois de confrontar)

- Dataset: raw + `rig-v0` + manifest + patch composto + gate (R1, R6, R9, R10).
- Núcleo do modelo: **geometria determinística (R1/D-07) + one-class anomalib como baseline (R4/R9) + classe por geometria/classificador (R2)**; borda = INT8/EfficientAd (R7/R8).
- Rig: **2 câmeras** agora; v1 assimétrico após validação (R1); 3ª câmera só por critério (D-22/R10).
- Avaliação: RNF-02 no **nosso** dataset, split por sessão, métricas de qualidade do pré-processamento (R1).
---

# Revisão 2 (2026-09-11) — correções após auditar as próprias fontes

Motivo: a v1 acima foi escrita apoiada em (a) snippets de busca, (b) **títulos** das decisões D-xx e
(c) um relatório de IA com citações não verificadas. Auditado o que dava para auditar, há erros meus.

## 1. Status de verificação de cada referência

| R | Status real | Evidência |
|---|---|---|
| R1 deep research | **SECUNDÁRIO NÃO VERIFICADO — contém citação fabricada** | `arXiv 2404.08401` citado para "elipse por mínimos quadrados (Halir)" é, de fato, **PnLCalib — Sports Field Registration** (verificado por `web_extract`). A citação do SACD (`MDPI Sensors 25(12):3721`) **confere** (`web_search`). Ou seja: mistura de real e falso → **não serve como fonte de fato**, só de hipótese. |
| R2 ECA-EfficientDet | **primário** (PDF no Downloads, lido) | DOI 10.1155/2022/9518910 |
| R3 Pysource | **blog prático** (não é SOTA) | — |
| R4 PatchCore / R5 FastFlow / R6 CutPaste | **snippet de busca** (abstract/README), não texto completo | — |
| R7 arXiv 2409.15980 (AD no Pi) | **snippet de busca** | — |
| R8 anomalib 2.6.1 | **verificado por execução** (API real, modelos listados) | nosso venv |
| R9 piloto próprio | **primário** (medimos) | AUROC 1,0 / 0,999; ≈1,0 nas 81 frames |
| R10 D-01..D-22 | **títulos apenas** na v1 → conteúdo lido agora | ver §2 |

## 2. Erros da v1 (corrigidos)

**Erro 1 — li errado o D-04.** Eu escrevi "D-04 manda fundir nas duas vistas". O texto normativo diz:
um classificador por vista; **a vista SUPERIOR decide isoladamente o domínio da tampa**; as **duas
vistas laterais** cobrem o domínio do corpo; **"não existe maioria global entre as três câmeras"**;
defeito em qualquer domínio reprova; evidência insuficiente → `inconclusivo`. Ou seja, o domínio da
tampa é **de uma vista só** — o que, aliás, está mais próximo de R1 do que do que eu escrevi.

**Erro 2 — diagnostiquei a incongruência de câmeras ao contrário.** Não é "reports CAD 3CAM
desatualizados × decisão vigente de 2 câmeras". O normativo (**D-04 + D-22** — este último lista
literalmente "captura das **três vistas**") **e** os CAD concordam: **3 vistas**. O que conflita é a
**proposta mais recente de 2 câmeras obtusas**, que não está registrada em lugar nenhum.
→ Portanto é **decisão aberta** (D-23 deve *escolher e registrar*), não faxina de rótulo.

**Reforço — D-11 já normatiza o híbrido e o sintético:** A = detector autossupervisionado treinado
**somente com normais + transformações sintéticas versionadas**, e **sem participação na regra
principal de decisão por domínios**. Isso significa: (i) one-class é, por decisão, camada
**secundária** (igual à minha recomendação); (ii) o **versionamento das transformações sintéticas já é
exigido** (casa com `pipeline_version`/seed); (iii) o uso de "sintético" no treino já está autorizado
normativamente.

**Precisão que eu omiti — D-07:** calibração px→mm com referência física, **meta de 0,5 mm de erro
absoluto máximo**, medida só é conclusiva com calibração válida, fallback B = apenas classificador.

**Referência relevante subestimada — SACD (verificado):** teacher-student com *reverse distillation*
treinado com **pares sinteticamente corrompidos** e otimização de tamanho de modelo → mesma família do
`EfficientAd` do anomalib e alinhada a D-07/D-11. Reforça a camada de borda (INT8/distilação) em vez
do one-class pesado.

## 3. Lacunas de análise que continuam abertas (declaradas, não resolvidas)

- **Referências internas não confrontadas:** apostila do TCC (Calibre 278) e material "Aula 7"
  (observabilidade) citados no entregue; deep research de SOTA anterior (notas do escopo/posse do TCC);
  `D-08` kit de golden samples; inventário de posse.
- **Nenhuma latência medida por nós** no Pi 5 — todos os números de custo são de terceiros (R7) ou
  estimativas. Tradeoff "eficiência" da v1 é **estimativa**, não medição.
- **Realismo do defeito sintético** não verificado contra defeito real (nenhum real disponível).
- **R4/R5/R6/R7 são snippet-level** — antes de decidir modelo, ler o texto completo dos que sobrarem.

## 4. Status da decisão

A matriz v1 vale como **hipótese de trabalho**, não como decisão. Para decidir com rigor faltam:
confrontar as referências internas da §3, tratar **2 × 3 vistas** como decisão aberta (D-23) e medir
latência real antes de afirmar eficiência.
