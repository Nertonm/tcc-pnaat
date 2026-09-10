# R05 — leitura dos gates e diagnóstico

**Status: BLOCKED_READ_GATE. Refinamento geométrico não executado.**

O documento `R05Refined` contém um snapshot verificável de `R05Refs`, o STEP da coluna desmembrado em seus oito sólidos originais, o envelope de garrafa H370/D120 e uma planilha de parâmetros de auditoria. O nome solicitado do arquivo foi mantido; ele **não representa uma arquitetura refinada ou aprovada**.

A instrução desta tarefa condiciona o refinamento à aprovação dos gates. Cinco gates falharam. Não foram alteradas posições, malhas, ombros, backplates ou arquitetura para ocultar essas falhas. `R05Refs` permanece aberto e inalterado.

## Evidência e método

- Leitura prévia de `R05-REAL-COMPOSITION.md`, `R05-COLUNA-MODULAR-DESIGN.md` e do contrato JSON.
- Inspeção do documento vivo por `qwen-mm-plugins-freecad.get_objects`; cálculos e criação do snapshot por `execute_code` na thread GUI do FreeCAD. Sem CadQuery.
- `Part.Shape.read` carregou o STEP da coluna, incluindo as transformações de assembly. Ele contém cinco componentes superiores e oito sólidos válidos. Dois componentes de módulo e o crossbar são compounds com sólidos desconectados.
- Interseções de sólidos calculadas por OCCT `common().Volume`; distância por `distToShape`. Caixas delimitadoras servem apenas para dimensões/separação, não como prova de colisão de sólidos.
- Garrafa de referência centrada em **X=Y=0, base Z0**, hipótese explícita porque não há objeto de produto nem transformação de registro da coluna em `R05Refs`. As coordenadas originais do STEP e do documento foram preservadas. As colisões internas ao STEP independem dessa hipótese.
- Malhas abertas não foram convertidas artificialmente em sólidos. Vértices de malha dentro do envelope são evidência de ocupação do corredor; não são volume de interferência.
- Inspeção visual isométrica via MCP e releitura de `STEP_MODULE_2_BODY` confirmaram forma e propriedades aplicadas. As três imagens são do documento de diagnóstico.

## Gates

| Gate | Resultado | Evidência |
|---|---|---|
| Interferência | **FAIL** | Plinth × módulo 1: **4.140 mm³**; ombro superior × barra: **17.600 mm³**; ombro superior × pad: **3.480 mm³**. Os oito sólidos da coluna intersectam a garrafa na hipótese de registro adotada. |
| Altura | **FAIL** | Barra Z307–317; pad Z318–326. Mount existente tem origem Z430 e envelope Z415–469, sem conexão ao crossbar. Não existe referência CM3 que estabeleça o centro óptico. |
| Encaixe | **FAIL** | Corpos em Z−38–62, Z62–162, Z162–262: apenas contato plano nas juntas, engajamento axial zero. Ombros em Z205–219 e Z305–319 estão 43 mm acima dos respectivos corpos. |
| Canal FPC | **FAIL** | Uma passagem central de diagnóstico de 20×10 mm fica completamente preenchida (200 mm² de seção) nos ombros e elementos superiores. Nenhuma rota alternativa contínua foi estabelecida. |
| Grip trocável | **FAIL** | Não há receiver/adapter modelado que comprove troca do light-clamp. Plinth termina Z17; case começa Z102,5, com 85,5 mm de separação vertical. Objetos independentes não comprovam interface mecânica. |
| K1C por peça | **PASS dimensional** | Todos os oito sólidos e as seis malhas visíveis de assembly cabem em 220×220×250 mm pelos eixos atuais. Isto não aprova fatiamento, integridade da malha, suportes ou união dos sólidos desconectados. |

Detalhes de todos os pares, dimensões individuais e amostras FPC estão em `validation.json`.

### Altura e correção estimada

O pedido menciona Z430–520 para o gate; o contrato e o design estabelecem **centro óptico Z520–560**. Foram registrados ambos, sem alterar o contrato. O topo geométrico do STEP, Z326, não atende a nenhum deles.

- Faltam **104 mm** para suporte em Z430 e **194–234 mm** para suporte em Z520–560.
- A alternativa que preserva os **três módulos** é distribuir um acréscimo líquido total de 194–234 mm: aproximadamente **64,7–78 mm por módulo**.
- Como estimativa aritmética alternativa, **dois passos líquidos adicionais de 100 mm** colocariam o suporte em Z526. Essa alternativa não foi implementada porque a arquitetura fixa três módulos.
- Esses valores referem-se somente ao suporte. O deslocamento do centro óptico em relação ao crossbar e a profundidade efetiva dos encaixes devem entrar no recálculo. Não basta mover o mount ou empilhar os sólidos defeituosos atuais.

### Encaixes e FPC

Os furos cilíndricos do plinth e dos dois ombros têm Ø4,4 mm: equivalem geometricamente a 0,2 mm de folga **radial** para um cilindro nominal Ø4. Isso não comprova folga macho/fêmea de 0,2 mm. Os três corpos de módulo não possuem faces cilíndricas de furos M4. Não há trajeto de parafuso montado aprovado.

O corpo superior termina Z262, a barra começa Z307 (45 mm de separação), e há 1 mm entre barra e pad. Os ombros precisam ser reposicionados e integrados às peças correspondentes antes de testar engajamento e continuidade.

A sonda FPC 20×10 mm é somente um diagnóstico central explícito; não é uma largura de cabo aprovada nem valida raio de dobra, torção ou passagem dos conectores. O resultado demonstra obstrução dessa passagem, não impossibilidade de desenhar outra rota.

### Case, grip e corredor

`PIPIECE_CASE` mede aproximadamente **104,85×65,44×33,14 mm**, em Z102,5–135,64. `Mesh.isSolid()` retorna falso para a case e para ambas as peças do light-clamp. Isso impede certificar ausência de interferência volumétrica case/coluna ou encaixe da placa com bosses. Não foi aplicado reparo automático às malhas fornecidas.

Na hipótese de garrafa na origem, 11.962 vértices da case estão dentro do envelope do produto, além de vértices dos grips e dos mounts laterais. É necessário registrar a coluna na lateral e estabelecer a ligação do crossbar ao eixo da garrafa. Nenhum backlight ou corredor traseiro dimensional está modelado: sua desobstrução permanece **BLOCKED**.

## O que foi entregue e o que permanece bloqueado

Entregue: documento de diagnóstico com **23 objetos** — 12 copiados de `R05Refs`, um grupo, oito sólidos STEP, uma garrafa de referência e a planilha `Params`. A planilha registra contrato e medições; ela não transforma o STEP importado em modelo paramétrico nem dirige as geometrias originais.

**STEPs oficiais Pi5/CM3 importados: nenhum**, porque a importação e reconciliação fazem parte da fase explicitamente condicionada aos gates. Os arquivos locais foram localizados e permanecem disponíveis:

- `references/vendor/raspberry-pi/pi5/step/rpi-5b_no_graphics.step`
- `references/vendor/raspberry-pi/camera-module-3/step/Camera_module_3_std_model_simple.stp`
- `references/vendor/raspberry-pi/camera-module-3/step/Camera_module_3_wide_model_simple.stp`

Continuam **BLOCKED**: registrar essas referências e validar bosses/portas da case pipiece; substituir os três backplates mantendo a cinemática de `pi-camera-mounts`; janela Wide no topo e Standard nas laterais; conectar os mounts à coluna/crossbar e comprovar eixos −Z e ±Y; receiver/adapter intercambiável do grip. A janela óptica exata depende da geometria aplicável e da lente real. A fixação original com M2.5 mencionada nas referências também precisa ser reconciliada com a restrição atual a M4/M5/M6/M8, sem simplesmente adicionar esses parafusos menores.

As fontes continuam pipiece/light-clamp (ISC) e pi-camera-mounts (GPL-2.0); não houve redesenho ou substituição por caixas. Nenhuma esteira foi criada, nenhum uso de `larsch/rpi-camera.scad`, nenhuma validação de FOV/calibração/carga/safety real, nenhum commit/push.

## Arquivos

- [Documento FreeCAD](../exports/concepts/optical-rig-r05/optical-rig-r05-refined.fcstd)
- [Gates e medições JSON](../exports/concepts/optical-rig-r05/validation.json)
- [Vista isométrica](../exports/concepts/optical-rig-r05/optical-rig-r05-refined-isometric.png)
- [Vista frontal](../exports/concepts/optical-rig-r05/optical-rig-r05-refined-front.png)
- [Vista superior](../exports/concepts/optical-rig-r05/optical-rig-r05-refined-top.png)
- [Script executado via MCP](../scripts/freecad_r05_read_gate.py)

O JSON inclui hashes dos principais insumos. O STL agregado foi preservado como insumo de rastreabilidade; as medições foram feitas nos objetos individuais do documento vivo e no STEP, sem duplicar o STL dentro da cena.
