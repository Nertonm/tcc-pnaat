# Deep research — pré-processamento ótimo para inspeção de garrafas PET

## Objetivo

Levantar, com fontes primárias e tradeoffs, qual é o **melhor pipeline de aquisição +
pré-processamento** para inspecionar garrafas **PET** (transparentes, reflexivas, com líquido)
em linha de envase, para as nossas classes: `tampa_ausente`, `tampa_mal_rosqueada`,
`deformidade do corpo`, `normal`.

## Contexto do projeto (não pesquisar isso; usar como restrição)

- Cenário 1: inspeção de envase; foco em **visibilidade/rastreabilidade** (sem atuação na esteira).
- **Multi-view** (mais de uma câmera; hoje 2 câmeras em ângulos obtusos: baixa-esquerda e alta-direita).
- Sensor de presença **E18-D80NK** (ESP32) abre a janela de captura por item.
- Inferência **na borda: Raspberry Pi 5, modelos leves/INT8**, com orçamento de latência.
- Medição dimensional por **calibração pixel→mm** (RF-15) para mal rosqueada e deformidade.
- Dataset: fotos do próprio rig (frames) + defeitos sintéticos gerados por IA (pares com
  máscara/região), validados por gate de isolamento.
- Já implementado: patchcore/padim/efficientad (anomalib 2.6.1) para anomalia; fusão multi-view
  determinística; registro local + dashboard.

## Perguntas de pesquisa (responder TODAS, com evidência)

1. **Física da imagem em PET**: como transparência, refração, dupla reflexão e reflexo especular
   confundem a detecção de defeito de tampa/corpo; que artefatos imitam cada defeito (falso
   positivo/negativo).
2. **Iluminação**: comparar (com evidência) difusa (dome/diffuser), backlight difuso para
   silhueta/dimensional, dark-field vs bright-field, **luz polarizada / polarizadores cruzados**
   para matar especular, luz coaxial, estroboscópica, multispectral (NIR/UV) para friso de tampa.
   Ranking por eficácia para cada classe e por custo/complexidade.
3. **Fundo/contraste**: fundo, retroprojeção, cores e superfícies recomendadas para PET
   (transparente e colorido); como separar garrafa de fundo sem depender de cor.
4. **Câmera/ótica**: mono vs cor; global vs rolling shutter; telecêntrica (medição) vs
   convencional; resolução x FOV x tamanho mínimo de defeito; profundidade de campo; foco.
5. **Exposição/HDR**: bracketing, exposure fusion, saturação, ganho; quando HDR ajuda de verdade.
6. **Pré-processamento** (o núcleo): correção de iluminação/flat-field, subtração de fundo,
   máscara de especular e inpainting, ROI/recorte, alinhamento/registro por template (itens
   variam de posição), correção de distorção, calibração pixel→mm (alvo, método, incerteza),
   normalização, realce de borda, segmentação (threshold/Canny/watershed/GrabCut), ajuste de
   elipse para inclinação de tampa.
7. **Multi-view**: registro entre vistas, consistência cross-view, oclusão parcial da tampa,
   como combinar sem introduzir viés.
8. **Robustez/dataset**: augmentation para PET (simular transparência/reflexo), domain
   randomization, balanceamento, e **validação de defeito sintético** (como provar que o defeito
   é realista e isolado sem viciar o modelo).
9. **Borda (Pi 5)**: o que desse pré-processamento roda em CPU (OpenCV) sem estourar latência;
   o que simplificar/eliminar; pipeline recomendado com ordem e custo estimado por etapa.
10. **Métricas de qualidade do pré-processamento**: SNR/contraste/nitidez/cobertura de máscara
    especular e como correlacioná-las com acurácia do classificador (RNF-02).
11. **Pitfalls** conhecidos em inspeção de PET em linha (documentados em papers/patentes/indústria).
12. **Referências**: papers (com DOI/arXiv), datasets públicos de garrafa/PET, normas/guia
    industriais e patentes relevantes; citar trecho exato ao afirmar algo.

## Formato da entrega

1. Sumário executivo com a **recomendação de pipeline** em ordem (aquisição → pré-process → modelo).
2. Tabela comparativa das opções (eficácia por classe x custo x complexidade x evidência).
3. Pipeline recomendado para o **nosso cenário** (2 câmeras obtusas, Pi 5, INT8, mm), com etapas,
   parâmetros iniciais e o que medir.
4. Plano de validação: experimentos com métrica e critério de passagem (ligar a RNF-02/RNF-14).
5. Riscos e limitações, com o que ainda falta medir.
6. Referências com link + trecho exato citado.

## Regras de qualidade

- Distinguir **CONFIRMED** (fonte primária/medição) de **LIKELY** e **SPECULATIVE**.
- Não afirmar resultado de paper sem citar o trecho exato e a métrica.
- Quando não houver evidência, dizer explicitamente o que falta e como medir.
- Priorizar o que é implementável no nosso hardware e barato de testar primeiro.