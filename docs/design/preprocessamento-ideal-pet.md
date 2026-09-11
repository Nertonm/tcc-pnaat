# Pré-processamento ideal para inspeção PET (consolidado)

Consolida o levantamento bibliografico com as
nossas restrições (2 câmeras obtusas, Pi 5 INT8, trigger E18-D80NK, calibração mm, sem atuação).
Números marcados **[meta]** são estimativa a medir, não fato.

## 1. Aquisição (onde mais ganha-se acurácia, a custo zero de CPU)

| Item | Decisão | Por quê |
|---|---|---|
| Câmera da tampa (alta-direita) | **Backlight difuso** (campo claro) | silhueta de alto contraste → geometria/dimensão da tampa; fundo é o próprio difusor |
| Câmera do corpo (baixa-esquerda) | **Frontal + polarização cruzada** e fundo **absorvedor escuro (<2%)** | mata especular; birrefringência revela tensão/amassado; evita refração do fundo |
| Sensor | **mono + global shutter** | mono evita CFA/demosaic e aliasing na borda; global evita skew em esteira |
| Lente | baixa distorção (<1%), calibração **Charuco** | telecêntrica ideal mas inviável em custo; calibrar intrínsecos e fixar Z |
| Abertura/exposição | f/8-f/11; exposição <1 ms com **LED estroboscópico** sincronizado ao shutter (GPIO) | DoF + congelar movimento **[meta]** |
| HDR | **não** fazer bracketing/fusão na borda | fusão >150 ms inviável; resolver na física (polarizador) ou sensor DCG |
| Gatilho | E18-D80NK (IRQ) abre a janela das duas câmeras | determinístico, sem tracking |

## 2. Pipeline por frame (ordem + orçamento **[meta]**)

1. **DMA/captura V4L2**: 1-2 ms
2. **Flat-field + dark-frame** (LUT fixa em ponto fixo): 1-2 ms: corrige vinheta e deriva térmica
3. **Alinhamento por template matching NCC piramidal** (âncora: anel do gargalo) 1/4→1/8: 3-5 ms
  : indispensável: modelos de anomalia são sensíveis a deslocamento
4. **Recorte de ROI** (<1 ms): terço superior = metrologia da tampa; 2/3 inferiores = modelo
5. **Geometria (determinística)**: Canny + **elipse por mínimos quadrados diretos (Halir)** com
   **RANSAC** para rejeitar outliers (rebarbas de PET no friso): ~4 ms
   → saída: presença de tampa, altura/inclinação (tilt), offset concêntrico, em mm
6. **CLAHE + normalização** nas ROIs: ~4 ms
7. **Máscara de especular** (limiar ~245): ~1 ms: passada **junto** ao modelo para anular
   penalidade de score na região (não usar inpainting: caro e impreciso)
8. **Inferência INT8** nas ROIs (PaDiM/EfficientAD/aluno leve): 35-50 ms
9. **Fusão em nível de decisão** (nosso PoC-04): cada vista entrega geometria + rótulo/confiança;
   discordância → análise humana; priorizar métrica de tampa na câmera backlight (sem excluir a outra)

Total **[meta]**: ~50-65 ms/item → ~10-15 garrafas/s (validar no Pi 5).

## 3. Métricas de qualidade a instrumentar (ligadas ao RNF-02)

- **CNR** (contraste/ruído na borda da silhueta): alvo ≥18, alerta <12: abaixo disso o Canny
  oscila e o ajuste de elipse degrada (falso positivo dimensional).
- **Tenengrad** (nitidez): monitorar tendência → early-warning de desfoque/vibração/condensação.
- **Cobertura especular** (px ≥245): alvo ≤3% na área texturizada: acima, o extrator de features
  distorce e gera anomalia fictícia.
- Recalibrar dark-frame/flat-field em loop ocioso (deriva térmica do maquinário).

## 4. Dataset e validação

- `normal` = frames classificadas/validadas; `defective` = **patch composto** no original (modo B).
- Gate de isolamento: ≤0,2% de pixels alterados fora do bbox (já implementado em `validar_pares.py`).
- Augmentation fisicamente coerente: gotículas/condensação, variação de iluminação/ângulo,
  reflexos: **não** ruído genérico; e evitar confiar em FID como prova de realismo.
- Casos que derrubam o método: reflexo/fundo refratado (FP), dupla reflexão no gargalo (FN de
  mal rosqueada), saturação escondendo amassado (FN), vibração (usar strobe curto).

## 5. O que NÃO fazer (ou só com evidência)

- Telecêntrica (custo), tele+HDR na borda, GrabCut/Watershed em linha (latência indeterminada),
  inpainting de especular em tempo real, bracketing HDR, e tratar os números do relatório de
  pesquisa (50-65 ms, CNR≥18, ±0,2 mm) como fato: são **metas** até medirmos no rig.

## 6. MVP implementável agora (ordem)

1. flat-field + correção de vinheta (LUT)
2. template matching piramidal + ROI
3. Canny + Halir + RANSAC (tilt/altura da tampa em mm)
4. CLAHE + normalização + máscara de especular
5. instrumentar CNR/Tenengrad/especular e registrar por item (dashboard)