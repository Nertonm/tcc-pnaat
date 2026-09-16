# Deep Research: Referências para CASE Pi5 + Câmeras + Grip AgNÓSTICO

Data: 2026-09-10. Modo: pesquisa na web por referências reais (não zero-shot). Objetivo do R05 do TCC: case impressa unitária para Raspberry Pi 5 + câmeras 3-vista, fixável por grip agnóstico em esteira. Impressora K1C (220x220x250), PETG.

## Decisão de escopo confirmada no repo
- RF-01 núcleo: 3 vistas sincronizadas (topo + 2 laterais). Câmeras: 2 CSI + 1 USB.
- Grip: D-17 registra fixação PENDENTE S1 (garra M6/M8 ou spring). "Twist-lock" é variante a registrar como decisão.
- Esteira NÃO impressa; só o grip/case varia.

## TOP cases Raspberry Pi 5

1. PiPiece (johnwebbcole, GitLab); https://gitlab.com/johnwebbcole/pipiece
   Case Pi5 + HQ Camera V3 + display; PDF Assembly guide; fonte JSCAD + OpenSCAD; PETG recomendado; 3 peças (cameraCaseTop/Bottom, picase). RELEVANTE: padrão de montar câmera na case com furo de ribbon retangular dedicado; orientação de impressão e recomendações PETG. License: GitLab, verificar lic_txt. setup: CONFIRMED_USED (assembly guide com fotos).

2. bandrewk.net RPi5 OpenSCAD case #1; https://bandrewk.net/rpi5-custom-case-openscad-1
   Case OpenSCAD iterativa P/ Pi5 com fan 80mm, ePaper, NVMe. Lição DIRECTA: não ler cotas direto do STEP (é assembly com sistemas locais); usar gmsh p/ bounding box. Testes de tolerância impressos (0.8-1.2mm lid; inserção M2.5 3.3-3.9mm). RELEVANTE MUITO: metodologia de calibração de tolerância e a advertência do STEP. setup: CONFIRMED_USED (várias iterações impressas).

3. MakerWorld Raspberry Pi 5 Case; https://makerworld.com/en/models/795430-raspberry-pi-5-case
   Remix Pi4->Pi5; inclui STEP e F3D (Fusion). ABERTURA de ventilação p/ cooler oficial. RELEVANTE: fornece STEP editável (base p/ abrir no FreeCAD/CadQuery). setup: REFERENCE_ONLY (mensão de remix, não confirma makes).

4. Raspberry Pi 5 Case 3D Print (raspberry.tips); https://raspberry.tips/en/3d-druck/raspberry-pi-5-case-3d-print
   Artigo com 5 decisões críticas de design de case (inclui pitfall do STEP/assembly e pinos centralizadores nos bosses M2.5). RELEVANTE: checklist de projeto de case Pi5. setup: REFERENCE_ONLY (artigo, não modelo standalone).

## TOP mounts câmera (rastrear 3-vista num módulo)

1. Camera Quick Release System (Unipasserby97, Printables); https://www.printables.com/model/1528052-camera-quick-release-system
   QR swappable: dovetail clamp OU cam-lever. Hardware: nuts 1/4-20 + 3/8-16, springs, M4/M3. RELEVANTE: mecanismo de troca de suporte (dovetail/cam) e BOM.
2. Raspberry Pi camera mount - Camera Module 3 (Printables); https://www.printables.com/model/368788-raspberry-pi-camera-mount-camera-module-3-version
   Housing remix p/ Camera Module 3. RELEVANTE: geometria de mount do CM3 (que vamos usar). setup: REFERENCE_ONLY.
3. Arducam / PiShop camera mounts; https://www.pishop.us/product-category/raspberry-pi/raspberry-pi-cameras/camera-mounts
   Brackets/tripods p/ CM3 e HQ. RELEVANTE: referência de posições/ângulos de câmera em fixtures. Comercial, referencia conceitual.
4. larsch/openscad-modules rpi-camera.scad; https://github.com/larsch/openscad-modules/blob/master/rpi-camera.scad
   Módulo OpenSCAD P/ placa de câmera (26x26, furos M2), CC BY-SA 2.0. RELEVANTE: componente paramétrico TC para embutir nos nossos mounts. setup: REFERENCE_ONLY.

## TOP grip agnóstico (fixação)

1. Bayonet Style Mount Groove (ROTHMECH, 3DSEARCH); https://3dsearch.net/...bayonet-style-mount-groove-push-and-twist-to-lock-1
   Ranhura bayonet push-twist-to-lock, STEP+STL, Inventor. Direto p/ nosso grip de torção. setup: REFERENCE_ONLY (sem attest encaixe real).
2. Bayonet Style Twist On Connector (Ben From Winnipeg, Printables); https://www.printables.com/model/673379-bayonet-style-twist-on-connector
   2 peças twist-to-lock, 40/50mm, STL+STEP, exige spacer de espuma compressível p/ segurar. RELEVANTE: base p/ twist-lock da case. setup: REFERENCE_ONLY.
3. Bayonet Tube O50x60 quarter-turn (Miloslav Brožek, Printables); https://www.printables.com/model/1694754-bayonet-tube-o50-x-60-mm-with-quarter-turn-locking
   Parâmetrico SCAD, 35° twist lock sem hardware, sem suporte. As inversas protocolo de impressão (cap top-down). MELHOR opção p/ mecanismo bayonet torcional puro (OpenSCAD paramétrico, sem material extra, testes de impressão descritos). setup: CONFIRMED bowd (descrição de impressão detalhada).
4. Quarter-Turn Quick Release Pin & Clip (legrandbleu, Printables); https://www.printables.com/model/1719864-quarter-turn-quick-release-pin-clip
   Pin + clip bayonet 90°, com orifícios p/ lanyard; orientação de impressão do pino vertical e clip flat. RELEVANTE: trava positiva de segurança no twist. setup: REFERENCE_ONLY.
5. Universal Spring-Loaded Phone Cradle (MakerWorld); https://makerworld.com/en/models/1184780-universal-spring-loaded-phone-cradle
   Spring-loaded, PETG p/ elasticidade da mola, sem suporte, sem hardware. MESMA família da Opção B do repositório (spring phone grip). setup: CONFIRMED bowd (132 boosts, perfil 100% infill).

## Parametric enclosure generators (base de organização)

1. pcb-enclosure-generator (hadencain, GitHub); https://github.com/hadencain/pcb-enclosure-generator
   Snap-fit body+lid a partir de dims da PCB, keepouts e portas; exporta STL + OpenSCAD editável. Browser React+Vite, kernel manifold-3d WASM. setup: REFERENCE_ONLY.
2. dmitriy718/pcb-generator (GitHub); https://github.com/dmitriy718/pcb-generator
   App desktop open-source, gerador paramétrico de enclosure PCB, importadores PCB, FDM optimization, export multi-formato. Um dos mais completos. setup: REFERENCE_ONLY.
3. ghbalf/freecad-ai skills/enclosure SKILL.md; https://github.com/ghbalf/freecad-ai/blob/master/skills/enclosure/SKILL.md
   RECEITA de enclosure no FreeCAD p/ agent (base+lid, screw/press/snap, posts M3, passos exatos PartDesign). RELEVANTE MUITO: roteiro de criação de case paramétrica no FreeCAD nativo (mesma rota do MCP que usamos). setup: REFERENCE_ONLY.

## Padrões extraídos (do que é relevante ao nosso caso)

- Sempre abrir cotas de STEP como *assembly* (sistemas locais por corpo), jamais capacidade direto; usar gmsh/bounding-box. Aplicável à Pi5 e CM3.
- Case PETG recomendado para Pi5 (PLA amolece com calor); permitir abertura de ventilação e acesso a todos os portas, com portas recuados p/ proteger plugs.
- Usar pinos centralizadores nos bosses (2.4mm chamfered) em vez de só parafusos p/ prender placa SEM movimento.
- Furo de ribbon dedicado (adjusta rectangular hole); a câmera monta fora, ribbon atravessa a parede da case. Exatamente o que queremos na saída da case.
- Twist/bayonet: espuma compressível fina como spacer p/ absorver folga e segurar; slots em L vertical+arco horizontal p/ trava; imprimir cap top-down com ramp 37° sem suporte; pin vertical p/ shaft redondo.
- Para grip agnóstico: usar padrão de receptor comum (dovetail OU bayonet) e adaptadores de clamp separados que variam por esteira; não caso da esteira.

## Antipadrões (evitar)

- Case que fecha lente/visão da câmera sem janela óptica. Abri.
- Fixar câmera por fricção ou cola; usar M2/M2.5 parafusados com boss/pinos.
- Ribbon preso direto no conector sem alívio de tração: crease permanente do FPC.
- Depender só de mola/torção sem trava positiva (pino passante/quarter-turn) em fixação estrutural do módulo.
- Reusar case fechada vendida sem arquivo editável (não dá p/ abrir janela de câmera exata).
- Modelos sem licença / sem fonte (STEP não editável para TCC).
- Não ler cotas de STEP de assembly direto (dedo erro de 140mm que é 1.4mm).

## Candidatos recomendados

- Caso: PiPiece (padrão cam-on-case + PETG + assembly guide) e o artigo raspberry.tips (checklist de design).
- Grip: bayonet tube paramétrico (Brožek) como mecanismo twist + quarter-turn pin (legrandbleu) como trava de segurança.
- Setup de organização: dmitriy718/pcb-generator (ou pcb-enclosure-generator) e a receita FreeCAD (ghbalf) p/ gerar a case paramétrica nativa no FreeCAD.
- Metodologia: testes de tolerância impressos no estilo bandrewk.net antes do-case final.

## Links a verificar licença

- PiPiece (GitLab): confirmar LICENSE (JSCAD).
- Bayonet Tube Brožek: confirmar licença Printables.
- camera-module-3 mount (Printables): confirmar licença.
