# Medição: viés do ajuste de elipse e o que limita a metrologia da tampa

Data: 2026-09-11. Harness: `code-workspace/scripts/medir_vies_elipse.py` (determinístico, seed 1234,
200 trials por célula). Teste de regressão: `code-workspace/tests/test_vies_elipse.py`.

Motivo: o paper de Halir & Flusser (1998),
avisa que o ajuste por distância **algébrica** tem viés sistemático que encolhe a elipse. Como o
RF-15/RNF-14 mira 0,5 mm, era preciso saber se esse viés cabe no orçamento.

Escala assumida (estimativa até haver calibração Charuco): tampa nominal **28 mm** (PCO 1881) sobre
**45,8 px** medidos nas nossas frames → **0,611 mm/px**. Logo **0,5 mm ≈ 0,82 px**.

## Resultado (semi-eixos verdadeiros a=22,9 px, b=21,0 px, ângulo=30°)

| Arco visível | ruído σ | viés a (px) | viés a (mm) | viés b (px) | erro de ângulo (°) |
|---|---|---|---|---|---|
| 360° | 0,0 | −0,0000 | 0,0000 | 0,0000 | 0,000 |
| 360° | 0,25 | +0,0028 | 0,0017 | 0,0039 | 0,321 |
| 360° | 0,5 | +0,0100 | 0,0061 | 0,0147 | 0,643 |
| 360° | 1,0 | +0,0377 | 0,0230 | 0,0571 | 1,297 |
| 360° | 2,0 | +0,1489 | 0,0910 | 0,2211 | 2,679 |
| 270° | 0,0 | −0,0000 | 0,0000 | 0,0000 | 0,000 |
| 270° | 0,5 | −0,0123 | −0,0075 | −0,0045 | **1,332** |
| 270° | 1,0 | −0,0334 | −0,0204 | −0,0220 | **4,135** |
| 270° | 2,0 | −0,0040 | −0,0024 | −0,1023 | **12,825** |

RANSAC não muda o quadro (σ=1, 270°: 3,61°; σ=2: 13,68°): ele rejeita outliers, não recupera arco
ausente.

## Leitura

1. **O viés algébrico do Halir não é o gargalo.** Com contorno completo e ruído plausível de borda
   (σ=1 px), o encolhimento é **0,038 px = 0,023 mm**; em σ=2 px, 0,091 mm. Ambos **dentro** do
   orçamento de 0,5 mm. Refino geométrico não é obrigatório para o semi-eixo: fica como margem.
2. **O gargalo é oclusão do contorno.** Faltando 25% do arco (270° visível, ex.: anel de suporte
   escondendo parte da tampa), o **erro de ângulo** sobe de 1,30° → **4,13°** (σ=1) e a 12,8° (σ=2).
   A precisão angular não depende do ajuste, depende de **ver a maior parte do contorno**.
3. **Tradução para mm (o que importa para `tampa_mal_rosqueada`)**: com raio da tampa R≈14 mm,
   `Δh ≈ R·sin(θ)`. Erro de 1,3° ≈ **0,32 mm** (dentro dos 0,5 mm); erro de 4,1° ≈ **1,00 mm**
   (fora). Ou seja, **a classe tampa_mal_rosqueada só é decidível em mm se o contorno estiver
   suficientemente visível**.
4. **Resolução é limite físico separado**: 1 px = 0,611 mm hoje; como 0,5 mm ≈ 0,82 px, a meta exige
   **localização subpixel de borda** (~0,1-0,2 px) ou aproximar/alongar a óptica da tampa. O contorno
   atual vem de `cv2.findContours` (pixel inteiro) → σ≈1 px é justamente o cenário do caso 360°/σ=1.

## Consequências práticas (acionáveis)

- **Checklist de captura da tampa**: garantir ≥300° de contorno visível da tampa (mover o anel de
  suporte fora do campo ou usar a vista em que a tampa não é ocluída): vale mais que qualquer
  melhoria de algoritmo.
- **Subpixel obrigatório** para a meta de 0,5 mm: próximos passos são (a) medir o σ real de
  localização de borda nas nossas frames e (b) avaliar extração subpixel (ajuste de borda por
  gradiente/parabólico) antes de prometer número em mm.
- **Métrica de qualidade nova** a instrumentar: **fração de arco visível da tampa**. Sem ela, um
  resultado de tilt não é interpretável: é a versão "ângulo" do que já fazemos com CNR/especular.
- **Não** gastar esforço em refino geométrico da elipse agora (o viés está sob controle); o esforço
  vai para visibilidade do contorno + subpixel.
