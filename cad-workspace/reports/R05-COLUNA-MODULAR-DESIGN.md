# R05 — Design da Coluna Modular "Pi=Haste" (conjectura travada)

Status: DESIGN_REFERENCE / LIKELY. Não é validação estrutural nem liberação de fabricação.

## Arquitetura (decidida com Nerton)

A Pi 5 é a HASTE: a sua case impressa é uma coluna modular que envolve a Pi na base e sobe
em módulos encaixáveis até a C_TOP. Nada de torre metálica externa. O cabo flat desce POR DENTRO
da coluna (canal impresso). Backlight fica atrás da garrafa, coluna fica na lateral (não ocluir o
corredor óptico traseiro).

```
esteira borda
  └─ CLAMP (pé trocável: C-clamp / through-bolt / split; M6/M8 metálico)
       └─ PI_CASE_COLUMN  = A HASTE (coluna modular)
            ├─ MÓDULO BASE: Pi5 + Active Cooler + bosses M2.5, CG baixo
            ├─ MÓDULO 2/3: encaixe macho/fêmea + pinos + M4, canal interno ⊞
            ├─ CM3 Lateral esq (cabo curto) na coluna
            ├─ CM3 Lateral dir (cabo curto) na coluna
            └─ MÓDULO TOPO: C_TOP (CM3 Wide) apontando -Z, FPC 500mm blindado descendo

Cada módulo ≤ 220×220×250mm (cabe K1C). Encaixe recursivo: 1 interface inferior + 1 superior iguais.
```

## Dados reais de produto (escopo fixo)

- Apenas garrafas PET de refil. Envelope: H máx 370mm, H mín 130mm, D máx 120mm, D mín 50mm.
- C_TOP acima da maior garrafa: ponto óptico ~Z 520-560mm. Altura vinda dos módulos, não peça única.

## Optica — decisões

- C_TOP = CM3 WIDE (DFOV 120°/102°H/67°V, f=2.75mm, Z=12.4mm) => menor altura massiva.
- Histórico v5: C_LEFT/C_RIGHT = CM3 STANDARD (DFOV 75°/66°H/41°V, f=4.74mm)
  ou Wide (decisão: Standard). Para o escopo vigente R05 v7, C_LEFT permanece
  Raspberry Pi CSI e C_RIGHT passa a USB-C/UVC, ainda como envelope até a
  seleção de compra; ver `R05-V7-3CAM-NOMINAL.md`.
- Backlighting obrigatório p/ PET transparente; corredor traseiro 100% desobstruído.

## Parâmetros congelados (contrato ~7def7953)

- Alias no CAD: CM3_* (board 25×23.862, hole Ø2.2, lens envelope por variante),
  Pi5 bosses (2.7mm hole, central 3.5mm), rod/module column params, jaw_opening.
- Abertos (ativar c/ G0): jaw_opening, spacer, working distances finais, backlight angle.

## Estratégia de composição (modelos existentes → elementos)

Cada peça da coluna tem 2 interfaces de encaixe (um padrão recursivo). Fontes:
- Pi5: STEP oficial rpi-5b_no_graphics.step (ref, não produção).
- CM3: STEP oficial camera-module-3 (std + wide) p/ todos os backplates e janelas.
- Cinemática tilt/pan: model ref pi-camera-mounts/Master Document.FCStd (FCStd paramétr., GPL-2.0)
  → trocar backplate HQ/GS por backplate CM3 oficial.
- Encaixe/snap-fit: pcb-enclosure-generator (Apache) e Bandrewk OpenSCAD → ombro+pinos+M4.
- C-clamp topologia: Tasp3D (pé) com parafuso M6/M8 metálico (não rosca impressa).
- Airflow/Active Cooler: OpenPiCase apenas INSPIRAÇÃO (licença MIT não confirmada, redesenhar).
- ORP: filosofia de saída limpa do ribbon.

Regra de licença: incorporar e derivar com fonte reconhecida; sem arquivo de licença = inspiração, não base.
