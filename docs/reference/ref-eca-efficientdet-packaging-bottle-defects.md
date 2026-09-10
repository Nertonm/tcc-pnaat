# Referência: Fast Method of Detecting Packaging Bottle Defects Based on ECA-EfficientDet

## Fonte

- Título: Fast Method of Detecting Packaging Bottle Defects Based on ECA-EfficientDet
- Autores: Zhenwen Sheng, Guiyun Wang (Shandong Xiehe University, Jinan, China)
- Periódico: Journal of Sensors (Hindawi), Volume 2022, Article ID 9518910, 9 páginas
- DOI: 10.1155/2022/9518910
- Ano: 2022 (recebido 29/09/2021; publicado 23/02/2022). Open access (CC BY).
- PDF local: `/home/nerton/Downloads/Fast_Method_of_Detecting_Packaging_Bottle_Defects_.pdf`

## Método (fonte, CONFIRMED)

Detecção de defeito de embalagem de garrafa via **detecção de objetos one-stage**:

1. **Base**: EfficientDet (backbone EfficientNet + BiFPN), escolhido pelo autor como mais
   preciso que YOLOv4.
2. **Otimizações**: data augmentation **mosaic**; **Mish activation**; bloco **ECA-Convblock**
   com mecanismo de importância de canal (channel attention) para especificidade da extração.
3. **Transfer learning heterogêneo** para melhorar generalização com pouquíssimo dado defeituoso
   (cold start com amostras escassas).
4. **Dataset**: 1200 amostras de defeitos de **tampa (cap) e rótulo (label)**; anotação com LabelImg.

Categorias detectadas:
- **Tampa (cap)**: tampa deslocada (mislocated cap), tampa ausente (absent cap), tampa normal.
- **Rótulo (label)**: rótulo ausente, rótulo deslocado, rótulo danificado, rótulo normal.

## Resultados (fonte, CONFIRMED)

- **mAP geral 99.16%**.
- AP por classe: rótulo ausente 100%; rótulo normal 100%; rótulo danificado 99.04%; rótulo
  deslocado 96.47% (menor). Comparação com YOLOv4/YOLOv4-tiny: YOLOv4-tiny mais rápido, porém
  com acurácia inferior.

## Análise para o Cenário 1 (Inspeção de envase)

Coerências / relevância:

- **Tampa ausente e tampa deslocada** mapeiam diretamente nossos RF-02 (tampa ausente) e RF-03
  (tampa mal rosqueada). É a referência mais próxima do nosso alvo de tampa.
- **EfficientDet** como one-stage é um **encoder leve** (mobile-friendly) com bom balanço
  velocidade/acurácia e potencial de INT8 no Pi 5 — alinha com nossa restrição de borda.
- **Transfer learning com pouca amostra defeituosa** valida o caminho **supervisionado** para
  tampa (nossa opção A), e a técnica (mosaic + channel attention) é reutilizável no nosso treino.

Divergências / limites para adotar:

- **É supervised**: precisa de amostras defeituosas (mislocated/absent/damaged). Não cobre defeito
  *novo* sem dado; nossa direção one-class (CutPaste) segue complementando.
- **Defeito de rótulo e nível** fora do nosso escopo (nossos RF não cobrem rótulo/nível).
- **EfficientDet** é mais pesado que um aluno INT8 simples; se formos por detecção one-stage no
  Pi 5, prefira a variante **EfficientDet-Lite** (projetado para INT8/TFLite). Ainda assim exige
  validação no nosso dataset; não é modelo fechado.
- A métrica deles (mAP sobre 2 classes cap/label) não transfere direto ao nosso dataset; gate RNF-02
  (acurácia/confusão por classe) precisa medir no nosso próprio conjunto.

Estado: CONFIRMED como descrição do artigo (abstract/método/resultados lidos); relevância ao nosso
dataset SPECULATIVE até ensaio próprio. Arquivo é referência, não decisão de stack.

## Impacto em decisão

Reforça o uso de **detecção one-stage leve (EfficientDet)** como candidato do caminho supervisionado
para tampa (RF-02/03), com transfer learning e augmentação (mosaic/attention) reutilizáveis, e
mantém uma referência de acurácia por classe para comparar no nosso benchmark. Continuam válidos:
one-class leve (CutPaste) para anomalia/novidade e medição mm para geometria. Nenhuma decisão fechada.