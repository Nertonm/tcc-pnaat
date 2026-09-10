# R05 — bloco óptico compacto condicionado aos cabos

**STATUS: BLOQUEADO NO MCP / ENTREGA PARCIAL.** A modelagem e os caminhos foram executados no documento vivo, mas a validação excedeu 300 s e a consulta de recuperação também excedeu 300 s. Salvamento mínimo está em tentativa; `.FCStd` e screenshots ainda não estão confirmados. Não considerar os caminhos de saída abaixo como arquivos já entregues.

Última construção reportada: **71 objetos**, seguida por 14 criações na etapa dos cabos (85 esperados; consulta final indisponível). **12 peças impressas, todas sólidos únicos válidos**, na última resposta bem-sucedida. A etapa `finish` não foi executada: insertos M2.5, porcas de pan, arruelas de ajuste e ampliação final da boca CM3 para 24 mm são alterações preparadas em script, ainda não aplicadas no documento vivo. Os parágrafos que descrevem essas ferragens indicam o desenho final pretendido, não uma montagem concluída.

| Gate | Estado atual | Evidência/pendência |
|---|---|---|
| G1 — comprimento | PASS | caminhos curvos medidos; sobra mínima 22,49 mm após provisão de inserção |
| G2 — cabo completo/raio | FAIL | raio de fornecedor e acomodação de toda a sobra não resolvidos |
| G3 — case/eletrônica/cooler | FAIL | verificação de interferências não retornou; finalização dos insertos pendente |
| G4 — direção das câmeras | PASS | eixos centrais atingem tampa/corpo por geometria analítica; sem FOV |
| G5 — juntas | FAIL | finalização das ferragens e verificação de conectividade pendentes |
| G6 — K1C | FAIL | sólidos válidos, mas relatório dimensional final não retornou |

`FAIL` em gates não concluídos significa ausência de comprovação, não necessariamente uma colisão ou dimensão fora do limite. `validation.json` e `validation-blocked.json` registram explicitamente esse estado. A validação antiga R05ColumnV5 foi preservada em `validation-column-v5-legacy.json`.

Documento MCP: `R05OpticalBlock`. Arquitetura anterior descartada. A Pi 5 está no bloco elevado junto às duas câmeras; o pedestal inferior é apenas um primitivo de sustentação.

## Restrição física e evidência

O arquivo local `references/vendor/raspberry-pi/docs/standard-camera-cable-200mm-reference-drawing.pdf` foi lido antes da modelagem. Especifica comprimento **200 ±1 mm**, largura **16 ±0,1 mm**, 15 pinos e não fornece raio mínimo de curvatura. Seu título é **Standard–Standard**, portanto não documenta a terminação mini necessária à Pi 5. Não foi usado como prova de compatibilidade 15→22 pinos.

A compra prevista permanece **dois cabos de câmera Standard–Mini 200 mm**, conforme [produto oficial Raspberry Pi](https://www.raspberrypi.com/products/camera-cable/) e [instruções oficiais de conexão](https://www.raspberrypi.com/documentation/accessories/camera.html). Não substituir por cabo de display. A documentação recomenda evitar ângulos agudos, mas não estabelece um raio numérico para este cabo.

O alcance de 20 cm é um limite de comprimento, não uma esfera de montagem utilizável: distância euclidiana não inclui curvas, inserção nem sobra. Os caminhos foram construídos e medidos como `Part.Wire` com retas e arcos tangentes, em planos YZ, conservando a largura em X. O critério usa o pior comprimento de estoque, **199 mm**.

| Cabo | Caminho entre bocas CSI/CM3 | Reserva para inserção, total | Comprimento requerido | Sobra em 199 mm | Raio central mínimo |
|---|---:|---:|---:|---:|---:|
| C_TOP Wide | 166,5089 mm | 10 mm | 176,5089 mm | **22,4911 mm** | 15 mm |
| C_SIDE Standard | 115,5665 mm | 10 mm | 125,5665 mm | **73,4335 mm** | 14,4425 mm |

As bocas CSI são datums extraídos das posições dos corpos dos conectores no STEP; a tolerância interna de inserção não é fornecida pelo STEP. Os 10 mm são uma provisão geométrica explícita, não uma dimensão de conector certificada. O início de cada guia fica 8 mm após a boca. Seções livres: largura 17 mm, com seção U e folga para o span de 16 ×0,35 mm. A espessura de 0,35 mm e raio de projeto de 12 mm são hipóteses de projeto.

**Limite importante:** os sólidos coloridos representam o trecho requerido, não um cabo integral de exatamente 200 mm. As caixas ocultas `FPC_*_SlackEnvelope` reservam espaço preliminar para a sobra; não provam a acomodação dos 200 mm nem a transição real para a terminação mini. Sem resolver essa sobra e obter o raio mínimo do fornecedor, G2 deve permanecer FAIL. Não confundir 20 cm de alcance com raio de curvatura de 20 cm.

## Composição e fontes adaptadas

- **PiPiece, John Cole, ISC:** `pipiece/stl/case.stl` foi convertido de malha fechada em sólido OCCT no FreeCAD. A envoltória e topologia das aberturas/ventilação são reais. A cavidade foi recortada, os bosses reconstruídos sobre os quatro eixos do STEP, as aberturas de portas ampliadas, duas saídas para ribbon abertas e orelhas M4 adicionadas. A topologia de `PiCase` e `CameraCase` em `PiPiece.jscad` orienta bosses, pads, paredes e recortes de ribbon. Não é uma caixa genérica representando uma case.
- **Pi 5 oficial:** `rpi-5b_no_graphics.step`, 2.689 sólidos importados, placa horizontal em Z350. Furos de fixação em (3,5;3,5), (61,5;3,5), (3,5;52,5), (61,5;52,5) no sistema nativo. Bosses M2.5 com envelopes de insertos; SKU final de inserto e tolerância de impressão não selecionados.
- **pi-camera-mounts, James Pilgrim, GPL-2.0:** `Camera Mount - Bottom.FCStd`, geometria `Fillet`, usada diretamente nos dois gimbals. `Master Document.FCStd` foi inspecionado: abertura 58 mm, pan M5, tilt M4. O eixo de tilt foi orientado transversalmente à saída do ribbon para evitar cortar as abas. Carrier 57,6 mm e arruelas de ajuste de 0,2 mm em cada lado. Derivados/adaptadores desta composição usam GPL-2.0; preservar licença e atribuições na redistribuição.
- **CM3 oficial:** Wide no topo e Standard na lateral. Furos efetivos Ø2,2 mm e padrão extraído dos cilindros das placas. São usados **M2 nas PCBs**, pois M2.5 não passa por Ø2,2 mm; M2.5 une cassette/backplate ao carrier. Janelas de 12×12 mm, profundidades específicas por variante, derivadas dos envelopes das lentes nos STEPs.
- **pcb-enclosure-generator / pcb-generator:** foram lidas as referências de encaixes e tolerâncias. O gerador contém encaixe OpenLock, mas não há necessidade de copiá-lo para esta união aparafusada. Não se atribui a esses projetos geometria que não foi incorporada.

Os hashes das fontes usadas estão em `exports/concepts/optical-rig-r05/optical-block-sources.json`. As licenças e fontes completas permanecem em `references/vendor/`. Os relatórios antigos foram lidos apenas como histórico de falhas; não governam este projeto.

## Geometria, montagem e escopo

C_TOP tem centro frontal da lente **(-19,5;55;397) mm**, direção **−Z**; a tampa ilustrativa termina em Z370, resultando em 27 mm de separação axial. C_SIDE tem centro **(-19,5;−31,155;300) mm**, direção **+Y**, apontando para o corpo. São verificações de eixo, **não de FOV**, distância focal útil ou cobertura de imagem.

O quadro impresso único suporta case, pan/tilt TOP e pan/tilt SIDE. A case é retida por dois M4; os carriers usam M4 e os cassettes M2.5. Pan M5 com dois parafusos M3 adicionais por mount para impedir rotação. A base do quadro tem furo Ø5,5 e parafuso M5 para prender à elevação. A geometria de roscas é representada por envelopes; nenhuma análise de carga ou segurança foi realizada.

O keep-out do Active Cooler é um envelope conservador de projeto, não seu STEP oficial nem validação térmica. As portas mantêm túneis de acesso; a montagem deve conectar os ribbons antes do cooler conforme a orientação oficial. A case é aberta em cima para acesso ao cooler e ventilação.

O contexto é bancada/trilho artesanal D-01 conforme a restrição desta tarefa. Não foi encontrado um desenho D-01 dimensional nas referências consultadas; portanto o pé e pedestal estão explicitamente nomeados `PLACEHOLDER` e não certificam interface com bancada existente. Não há esteira industrial modelada. O pedestal não faz parte das peças impressas, nem leva a Pi para a base.

## Gates e entregáveis

A tabela final de gates, contagem e interferências é preenchida a partir da medição MCP em `validation.json`; a aprovação global depende de todos os gates, incluindo G2.

Arquivo CAD: `exports/concepts/optical-rig-r05/optical-rig-r05-optical-block.FCStd`.

Vistas: `exports/concepts/optical-rig-r05/optical-block-screenshots/{bloco,top,side,cabos,contexto}.png`. A vista `cabos` usa transparência das peças para mostrar o trajeto; não é uma vista sem obstruções da montagem física.

Reprodução: executar `scripts/freecad_r05_optical_bootstrap.py` pela ferramenta **MCP execute_code** em instância FreeCAD ativa, depois de fechar o documento de mesmo nome. As etapas `block`, `cables`, `finish`, `validate`, `save` rodam no FreeCAD. Não se usa CadQuery, processo headless alternativo, commit ou push.

## Erros MCP observados

1. Consulta inicial: `Failed to get objects: <Fault 1: "<class 'NameError'>:Unknown document 'R05OpticalBlock'">`. Resolvido criando o documento solicitado.
2. Biblioteca opcional: `Failed to get parts list: <Fault 1: "<class 'FileNotFoundError'>:Not found: /home/nerton/.local/share/FreeCAD/v1-1/Mod/parts_library">`. Foram usadas as referências locais, mantendo toda a modelagem no MCP.
3. Criação de datum: `Failed to execute code: AttributeError: module 'Part' has no attribute 'makeVertex'`. Corrigido para `Part.Vertex` e etapa reconstruída.

4. Validação: `qwen-mm-plugins-freecad/execute_code — timed out awaiting tools/call after 300s`.
5. Recuperação: `qwen-mm-plugins-freecad/list_documents — timed out awaiting tools/call after 300s`.

A tentativa pesada pode ainda estar ocupando o processo FreeCAD; não foi encerrada a instância nem alterados os demais documentos. O bootstrap foi preparado para salvar antes de validar em uma próxima execução. Seu fluxo completo não foi testado nesta sessão.
