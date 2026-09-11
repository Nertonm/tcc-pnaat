# Deep Research — CAD paramétrico scriptável para pipelines agênticos

Status: relatório de agente de pesquisa independente, recebido 2026-09-10.
Fonte: prompt autocontido `prompts/deep-research-cad-approach.md` (SHA a6a347d9).
Nota de ingest: claims preservados com a marcação original do autor
(CONFIRMED/LIKELY/SPECULATIVE). Pontos não verificáveis no momento do
ingest estão marcados [SOURCE-UNVERIFIED] abaixo.

## Resumo executivo

- CONFIRMED — OpenSCAD não atende R1: sem import STEP B-Rep nativo; STEP→STL
  perde a representação exata.
- CONFIRMED — CadQuery e build123d importam/exportam STEP/STL sobre OCP/OCCT,
  headless.
- LIKELY — melhor equilíbrio: build123d para DSL + OCP/OCCT como QA; CadQuery
  como plano B comparado no PoC.
- CONFIRMED — FreeCAD só se .FCStd for obrigatório; isolar em FreeCADCmd de
  empacotamento, não GUI/MCP como fonte da verdade.
- LIKELY/NÃO MEDIDO — sem benchmark primário para STEPs Pi5 77MB/CM3 30MB;
  qualquer alegação de performance antes do benchmark seria inventada.
- CONFIRMED — build123d/OCP tem QA determinístico: bbox, distância, validity,
  interseção volumétrica, eixo/shape, wire length.
- LIKELY — SHA-256 byte-a-byte de output não é critério primário entre
  máquinas (timestamp/UUID/version do writer variam). Usar hash dos inputs +
  fingerprint geométrico + round-trip.
- CONFIRMED — CM3 = conector 15 vias; Pi5 = mini 22 vias (Standard-Mini).
  Cabo oficial Pi5: 200/300/500mm.
- CONFIRMED — CM3 Wide: FoV H102° V67° diag120°, foco 5cm-∞, F/2.2;
  rolling shutter não é corrigido por calibração em movimento.
- LIKELY — spike de 30 min com os 2 STEPs falsifica rápido a recomendação.

## Comparação de stacks
| Stack | STEP real in/out | Headless | Param/assembly | STEP 30-80MB | QA geom | Julgamento |
|---|---|---|---|---|---|---|
| build123d+OCP | CONFIRMED import_step/export_step | CONFIRMED | CONFIRMED (joints rígido/revolute/linear/cyl/ball) | LIKELY/NÃO MEDIDO | CONFIRMED excelente | Recomendado, condicionado ao spike |
| CadQuery+OCP | CONFIRMED importStep/export | CONFIRMED | CONFIRMED Workplane | LIKELY/NÃO MEDIDO | CONFIRMED bom | Plano B |
| FreeCAD Python/FreeCADCmd | CONFIRMED | CONFIRMED mas complexo | CONFIRMED .FCStd nativo | CONFIRMED p/ import; perf não medida | CONFIRMED via OCCT | Adapter .FCStd secundário |
| OpenSCAD | **NÃO SATISFAZ R1** (sem STEP B-Rep) | CONFIRMED | CONFIRMED CSG | N/A (tesselação) | mesh, não B-Rep | REJEITAR principal |
| Blender bpy | LIKELY inadequado (sem fonte primária STEP B-Rep) | CONFIRMED --background | mesh/DCC | sem evidência | visual/render | REJEITAR principal |
| OCP/OCCT direto | CONFIRMED (XCAF/XDE) | CONFIRMED | baixo nível | LIKELY escape hatch | CONFIRMED máximo controle | Camada de autoridade |

Correções: build123d NÃO se autodescreve "sucessor oficial" do CadQuery
(repo diz derivado+refatorado; "sucessor" é caracterização da comunidade).
CadQuery 2.8.0 ativo; build123d ativo; FreeCAD 1.1.x ativo.
OpenSCAD stable oficial = 2021.01 (na data do acesso).

## Approach recomendado
Fonte da verdade = Python versionado, não .FCStd/MCP/GUI.

vendor STEP → SHA-256+manifest → OCP/build123d import → rig paramétrico →
QA determinístico (bbox/pose/óptica/cabo/BRep validity/colisão/clearance) →
export STEP+STL → re-import+fingerprint → FreeCADCmd→FCStd derivado.

- Por que build123d: API explícita, pouca statefulness, expõe is_valid/
  distance/bounding_box/find_intersection_points/do_children_intersect.
  (Inferência de engenharia, não benchmark de velocidade.)
- CadQuery concorrente sério: mesmo script de ingest nos 2; se CadQuery
  vencer em robustez/RAM, troca-se só a camada de modelagem.
- .FCStd derivado não é a representação paramétrica original do código.
  Se "FCStd editável com PartDesign nativo" for requisito, FreeCAD participa.

## Pipeline de validação determinística
(Compactado; exemplos de código preservados no workspace: promp→report original)
- Input integrity: SHA-256 + tamanho + versão/URL em vendor_manifest.json
- STEP ingest: import, registrar solids/faces/bbox/tempo; zero solids = fail
- B-Rep validity: is_valid (BRepCheck_Analyzer) / BOPAlgo_CheckerSI
- Bounding boxes, distância/clearance, interferência volumétrica
- Ótica: eixo óptico transformado + dot com alvo + ray casting primeiro hit
- FPC: comprimento de wire <= orçamento; caminho não atravessa sólidos
- Round-trip STEP: export → processo novo → reimport → fingerprint
- FCStd smoke: FreeCADCmd abre/fecha/reabre
- Booleans com broad phase (AABB) antes de Common exato
- Lente -Z local do STEP CM3 = regression test permanente (constante+hash)

## Referências verificadas
| Ref | Fonte | Licença/status | Dado-chave |
|---|---|---|---|
| G-Clamp 1673030 | Thingiverse | LIKELY CC-BY-4.0 (primary não legível) [autor johann517, não "joehann"] | sem dimensão primária |
| G-Clamp Notched remix | Printables | CONFIRMED CC BY-NC-SA 4.0 | notch 40mm 5×10, rosca M12, inclui STEP |
| ISO 1222:2010 tripod | ISO | norma copyright | conexão roscada câmera/tripé |
| ASME B1.1-2024 | ASME | norma copyright | rosca Unified |
| 1/4-20 UNC | definição | CONFIRMED aritmética | 6.35mm, pitch 1.27mm |
| CM3 | Product Brief 2023 | oficial | PCB 25×24, 12.4mm Wide, FPC 200mm 15×1mm |
| CM3 Wide ótica | Product Brief | oficial | f=2.75, H102 V67 diag120, foco 5cm, F/2.2 |
| Pi5 Camera Cable | raspberrypi.com | oficial | shielded, 22-way, 200/300/500mm |
| Topologia conectores | RPi docs | oficial | 15-pin câmera / 22-pin mini Pi5 |
| R_min FPC | — | SPECULATIVE (sem fonte numérica) | não inventar valor |
| OpenCV calibração | docs 4.13 | oficial | >=10 padrões, RMSReproj |
| Fisheye OpenCV | docs | oficial | cv::fisheye disponível |

Sanity FOV a 171mm (pinhole idealizado): W~422mm H~226mm — NÃO valida
garrafa inteira no rig real (elevação 49°, distorção Wide). Validação
correta: projetar pontos 3D com intrínsecos+distorção calibrados.

## Integração agêntica
- LLM fora do processo CAD: escreve texto → worktree git → runner subprocess
  (build/validate/export) → qa-report.json → agente reporta.
- Sem objeto compartilhado persistente entre agentes; cada execução =
  commit + inputs hashados → arquivos + report JSON.
- MCP CAD: existem (FreeCAD MCP jan/2026, 82+ tools; CadQuery MCP diretório
  MCP) — conveniência p/ exploração, NÃO executor autoritativo de CI.
- Regra de governança: agente não transforma WARN em PASS; só QA decide.
  [pontos MCP generalizáveis = SPECULATIVE; incidentes do projeto =
  CONFIRMED como incidentes, não como verdades universais FreeCAD]
- Worktrees separados por agente (git worktree add) — sem cwd/processo
  compartilhado.
- Contrato PASS := exit 0 AND hashes ok AND solids>0 AND breps valid AND
  interferência<=tol AND óptica ok AND fpc ok AND roundtrips ok.

## Git/LFS
- GitHub: warning >50MiB, bloqueio >100MiB. Pi5 77MB na faixa de warning.
- Git LFS: pointer + OID SHA-256; Free/Pro até 2GB/objeto.
- gitattributes: *.step *.stp *.FCStd → filter=lfs
- Scripts/manifest/baseline/reports em Git normal; STEPs em LFS ou storage
  externo com SHA-256 (se licença impedir redistribuição).
- Releases para binários grandes (recomendação GitHub).

## Licenças
- build123d Apache-2.0; OCCT LGPL-2.1+exception; FreeCAD LGPL-2.1-or-later;
  OpenSCAD GPL (rejeitado por R1).
- THIRD_PARTY.md por artefato: autor, fonte, retrieved, license
  (UNVERIFIED_FROM_PRIMARY permitido), derived YES/NO, SHA-256.

## Literatura CAD agêntico
[SOURCE-UNVERIFIED — IDs arXiv relatados pelo agente, não re-verificados no
ingest; verificar antes de citar academicamente]
- ArtisanCAD (2026, arXiv:2607.05750): representação intermediária
  procedural + invariantes + execução em backend CAD (CATIA/MCP).
- IterCAD (2026, arXiv:2606.13368): agente sobre CAD sandbox, mede
  validade/precisão geométrica.
- Anvil (2024, arXiv:2407.02519): automação FreeCAD paramétrico dirigida
  por configuração.
- Contribuição acadêmica do TCC: geração probabilística + aceitação
  determinística como hard gates de CI.

## Cadência de PoC
Spike 30min: /usr/bin/time -v bench_import.py nos 4 casos (build123d×2
cadquery×2), relatar wall/maxRSS/compound/solid/face/bbox/validity; round-
trip; falsificar se STEP real não importar, geometria vazia, crash, ou
perda no round-trip.
3 dias: D1 matriz ×5 execuções; D2 núcleo R05 (mount CM3, pose, eixo -Z,
garrafa, clamp, FPC wire) com asserts; D3 rig completo 2 agentes worktrees
separados + STEP/STL/FCStd + round-trip.
Aceite: R1-R5 + "export+reopen+fingerprint == sucesso" e "arquivo parseia
+ geometria esperada == sucesso".

## Fontes
CadQuery import/export, releases (2.8.0); build123d import/export, repo;
OCCT STEP Translator, BRepCheck_Analyzer, BOPAlgo_CheckerSI (todos docs
oficiais OCCT); FreeCAD repo; OpenSCAD repo; Raspberry Pi Camera docs;
CM3 Product Brief (2023); Raspberry Pi Camera Cable; ISO 1222:2010;
ASME B1.1-2024; OpenCV calibration/fisheye; GitHub large-file guidance;
Git LFS. Acessadas 2026-09-10 pelo agente de pesquisa.

## Lacunas honestas
- sem benchmark primário CadQuery/build123d com STEPs Pi5 77MB/CM3 30MB
- sem R_min numérico oficial do FPC
- licença primária do G-Clamp 1673030 não legível (UNVERIFIED)
- sem remix G-Clamp 1/4-20 com fonte primária verificável
- sem mount CM3+2020/4040 com página primária confirmada
- propriedades de concorrência/timeout dos MCPs não confirmadas em repo
- [SOURCE-UNVERIFIED] IDs arXiv ArtisanCAD/IterCAD/Anvil

## Confiança final
Alto p/ eliminar OpenSCAD/Blender como núcleo B-Rep; alto p/ tirar GUI/MCP
do caminho crítico; moderado p/ build123d vs CadQuery antes do benchmark.
