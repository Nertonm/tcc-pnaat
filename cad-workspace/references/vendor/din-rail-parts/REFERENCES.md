# Inventário de peças DIN rail — referências para o rig R05

Registrado 2026-09-10. Nenhuma geometria de terceiro foi copiada para produção;
estas são referências de função/dimensão. Licenças marcadas como UNVERIFIED onde
não foram lidas na fonte primária.

## 1. Case Raspberry Pi 5 com clip DIN  — ADOTADA
- Autor: Diyalec · Thingiverse `thing:6335141` (remix de `thing:2492974`)
- Licença: **CC BY-SA 4.0** (copyleft — share-alike em derivados)
- Arquivo local: `references/vendor/din-rail-case/` (2 STLs + fotos + PROVENANCE)
- Medidas medidas: base+clip 75.4×100.5×10.3mm · tampa 73.8×96.3×12.5mm · montada ~75×100×23mm
- Engate: trilho passa pela face traseira; gancho fixo + lingueta de mola (snap-fit) com aba de liberação

## 2. Bracket trilho→M6 (extremidade) — CANDIDATO p/ fixação na esteira
- Autor: ADSRMedia · Printables `573570`
- Licença: **CC BY-NC-SA 4.0** (NC — ok p/ TCC acadêmico; share-alike em derivados)
- Função: encaixa nas extremidades do trilho (5.5mm por lado) e converte em furação M6
- Variantes: screw-through e keyhole (engate rápido em parafuso existente, L/R)
- Nota do autor: feito p/ trilho de alumínio com pés na base; deve funcionar em aço padrão

## 3. Adaptador de ângulo 90° deslizante — RESOLVE a travessa perpendicular
- Autor: Shroamer · Printables `1757341`
- Licença: UNVERIFIED_FROM_PRIMARY (verificar na página antes de derivar)
- Função: **segmento de trilho DIN com clips impressos integrados** que monta SOBRE
  outro trilho DIN em **90°** — e desliza. É a peça que permite a barra horizontal
  correr nas verticais mantendo perpendicularidade.
- Tamanhos: 100 / 120 / 150mm (centrados no trilho portador) e 73mm (curto, off-center)
- Print: ABS, 0.2mm, 3 perímetros (arachne); suportes de 0.6mm embutidos (romper com alicate)

## 4. DIN Rail Bracket Redux (clip paramétrico) — BASE p/ mount da câmera
- Autor: herr_brain · Printables `472505`
- Licença: UNVERIFIED_FROM_PRIMARY (verificar na página); tags incluem `freecad`
- Variantes: selftap (furo 2.8mm), heatset (inserto M3x5x4), unibody (base p/ remix)
- **Parâmetros documentados pelo autor** (usáveis como spec do clip):
  - `closed_width` 34 mm — distância entre pontas fixa/móvel fora do trilho
  - `spring_width` 1.6 mm · `spring_radius` 0.4 mm
  - `slide_clearance` 0.2 mm · `chamfer` 0.4 mm
  - espaçamento de furos 51 mm (compatível com o design original de Fabian)
- Print-in-place; 16 arquivos; 1.777 likes (referência madura)

## 5. Parametric DIN Rail Bracket Generator — alternativa p/ gerar o mount
- Autor: projeto grbl.org · modelo FreeCAD paramétrico
- Licença: UNVERIFIED_FROM_PRIMARY
- Função: gera bracket DIN 35mm com comprimento/largura/altura e **furos customizáveis**
  (diâmetro/profundidade) + boss de folga; slot de alavanca p/ liberação com chave de fenda
- Recomendação do autor: comprimento ≥60mm, largura 8–10mm, altura ≥3mm (5mm ideal),
  impresso de lado sem suporte; espelhar um dos dois p/ deixar os slots p/ fora

## 6. Adafruit 4557 — bracket DIN comercial (Pi/BeagleBone/Arduino)
- Comercial, US$19.95 (out of stock na consulta)
- Alumínio + pernas adaptadoras DIN + standoffs M2.5; sem solda
- Alternativa caso não se queira imprimir

## Norma
- Trilho TS35 / EN 50022 / IEC 60715: 35 mm de largura × 7.5 mm de profundidade.
  Perfil comercial em aço ou alumínio; cortável; comprimentos usuais 1–2 m.

## Síntese para o design
| Necessidade | Peça | Status |
|---|---|---|
| Host Pi 5 no trilho | #1 Diyalec | pronta |
| Fixar trilho na esteira | #2 ADSRMedia (M6) | pronta (falta baixar STL) |
| Travessa perpendicular deslizante | #3 Shroamer (90°) | pronta (falta baixar STL) |
| Clip DIN p/ mount da câmera | #4 Redux ou #5 gerador | usar como base |
| Mount da câmera CM3 (49°) | — | **projetar** (nosso) |
