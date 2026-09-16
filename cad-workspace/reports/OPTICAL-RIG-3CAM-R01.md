# PNAAT: esboço paramétrico de três vistas

Status: **REFERENCE_ONLY**. measured=false; fabrication_allowed=false. Decisão: conceito para inspeção digital e planejamento de montagem; compatibilidade real A/B OPEN/BLOCKED_G0. Nenhuma fabricação, publicação ou liberação mecânica.

C_TOP usa a referência oficial Module 3 standard e observa a tampa. C_LEFT usa wide e observa o corpo. C_RIGHT usa standard como referência mecânica com conversor CSI-to-USB **não selecionado**; não há modelo inventado de câmera USB. C_TOP e C_LEFT ocupam respectivamente CSI0 e CSI1 conceituais do Pi 5. A aquisição da terceira vista por USB/UVC depende de hardware, drivers, latência e sincronização ainda não demonstrados.

A base e o pórtico são envelopes de MDF/perfil, com braços metálicos. FDM é restrito a suportes leves, bandeja, protetores, guias e mockups de interface. Inserts, parafusos e ferragens são necessários nas interfaces carregadas; o dock impresso não demonstra capacidade de suportar a estrutura. Os adapters A/B aparecem afastados da cena como alternativas **sem furos**. A/B são rótulos solicitados para mini/industrial, sem atribuição de identidade às máquinas fotografadas.

## Fontes e interpretação

Todos os três STEP obrigatórios foram importados via CadQuery 2.8.0, sem modificação/reexportação. A cena completa é reconstruída em memória por `view_scene.py`; o diretório de exports contém STEP/STL apenas das peças conceituais marcadas imprimíveis. Não existe STEP/STL de conjunto incorporando geometria oficial. Os três STEP locais foram comparados byte a byte, via SHA-256, com as entradas dos ZIPs ingeridos: PASS. O índice vendor de ZIPs/PDFs também passou em `sha256sum -c`. Os modelos e desenhos pertencem à Raspberry Pi Ltd; licença e originais permanecem no diretório vendor.

Os três PDFs locais foram lidos com Ghostscript `txtwrite`; o desenho da câmera também foi renderizado e inspecionado. O desenho do Pi ressalva que as dimensões são aproximadas e não constituem dados de produção. O desenho standard da câmera indica placa 25 × 23,862 mm e furos Ø2,2 mm; os furos dos suportes aqui são externos ao envelope, não uma transferência presumida desses furos. O desenho do cabo representa **standard–standard, 15 pinos, passo 1 mm, comprimento 200 mm e largura 16 mm**. Ele não qualifica a conexão ao Pi 5 nem os raios e comprimentos deste conceito. Não há seleção de cabo compatível feita.

Os bounds importados dos modelos são registrados em `components.json`, incluindo diferenças entre variantes. A normal óptica nominal é −Z local; a face frontal do envelope é posicionada na altura/dimensão nominal. O centro do bounding box não é um principal point calibrado. Distância focal, foco e cobertura óptica não foram aprovados.

`COMMON-OPTICAL-INTERFACE-M0.md` e `REFERENCE-ENVELOPE-AB.md` fundamentam a interface comum e seus bloqueios. Suas dimensões de esteiras não foram reutilizadas como medições. `esteira-b-g0-photo-r03.yaml` mantém identificação e dimensões sem confirmação; o gate real foi executado e deve continuar bloqueado.

## Arquivos

```text
cad/cadquery/concepts/optical-rig-r01/
  rig.py                  gerador paramétrico e geometria
  view_scene.py           cena em memória para CQ-editor
data/concepts/optical-rig-r01.json
scripts/validate_optical_rig.py
exports/concepts/optical-rig-r01/
  components.json         parâmetros, fontes/hash, funções, bounds
  *.step + *.stl          somente peças conceituais imprimíveis
  overview.pdf            prancha escalável, não usar como gabarito
  overview.png            prévia das projeções dos envelopes
  validation.json         readback, colisões e testes negativos
  g0-validation.json      resultado do gate físico existente
reports/OPTICAL-RIG-3CAM-R01.md
reports/OPTICAL-RIG-3CAM-R01.sha256
```

A prévia representa bounding boxes nas projeções; curvas de cabo e recortes reais devem ser examinados na cena CadQuery/STEP de peças. O PDF não está em escala de fabricação.

## Parâmetros

Todos os defaults são **ASSUMPTIONS**, em mm salvo indicação. Arquivo de configuração: `data/concepts/optical-rig-r01.json`. Coordenadas: X transporte a jusante; Y transversal; Z para cima; plano genérico de correia Z=0.

| Parâmetro | Default | Efeito / restrição |
|---|---:|---|
| camera_count | 3 | Gate exige exatamente três vistas |
| camera_spacing | 400 | Separação nominal das faces das câmeras laterais |
| working_distance | 180 | Distância nominal tampa–face da câmera superior |
| product_envelope | [80, 80, 240] | Caixa de produto e altura do volume percorrido |
| cable_length | 2200 | Orçamento por rota, sem cabo físico homologado |
| top_height | 420 | Deve ser altura de produto + working_distance |
| side_angle | 0° | Rotação em planta das vistas/braços laterais; limite ±20° |
| dock_width | 140 | Largura de receiver e língua, limites 100–200 |
| cable_bend_radius | 25 | Raio nominal da linha central; não mínimo homologado de FPC |
| cable_service_allowance | 100 | Reserva adicional por rota para terminais/serviço |

Derivados: colunas Y=±(camera_spacing/2+80); travessa acima de top_height+60; altura lateral=metade do produto. A distância lateral nominal ao corpo é (camera_spacing−largura do produto)/2 = 160 mm no default. A independência entre distância lateral e working_distance superior é intencional.

| Rota | Comprimento geométrico | Reserva | Saldo do orçamento de 2200 mm |
|---|---:|---:|---:|
| C_TOP | 1552,350 mm | 100 mm | 547,650 mm |
| C_LEFT | 2054,350 mm | 100 mm | 45,650 mm |
| C_RIGHT | 1544,350 mm | 100 mm | 555,650 mm |

A pequena margem de C_LEFT e os longos percursos tornam a qualificação elétrica/mecânica dos cabos um bloqueio explícito. A reserva não comprova que os terminais físicos caberão.

Outras hipóteses explícitas no código: base 450 × 680 × 18 mm, seções de perfil 30 mm, correia genérica 600 × 160 × 20 mm, curso de produto de 600 mm, trigger X=−150 mm, rolete X=−260 mm. **Nenhuma é dimensão confirmada de esteira.** As folgas, furos de suporte, envelopes E18/VL53L0X/KY-040, conversor e luminárias são hipóteses geométricas. Alterar parâmetros exige novo diretório `--out` e gate próprio; só o default foi revisado. Em particular, rota terminal, ligação do braço ao perfil e campo visual requerem revisão para ângulos não nulos.

## Montagem e interfaces

A bandeja do Pi assenta na base; quatro bosses espaçadores e parafusos conceituais fixam a placa, com cantos de bumper e faces abertas para conectores e ventilação. Não é uma caixa térmica/EMC qualificada. O acesso lateral é uma região de serviço; tomada, cabo de alimentação e refrigeração real continuam pendentes.

O receiver do dock possui datum D1 na guia lateral e D2 no piso, batente transversal anti-rotação e furo para parafuso M5 cativo com porca/arruela metálica. A língua e os adapters são conceitos de ajuste, sem interface de furação de máquina. Folgas de 1 mm laterais da língua são escolhas de desenho, não tolerâncias aprovadas. O curso de inserção e o acesso à trava ainda exigem ensaio.

As rotas de cabo são sólidos varridos com curvas, passando fora do volume de produto e acima do pórtico. São corredores circulares Ø6 mm, **não uma representação física de FPC de 16 mm de largura**. Os pontos finais de fixação dos guias à estrutura ainda precisam de ferragens/apoios medidos; a cena posiciona os guias sem detalhar essas ancoragens. Os guias U têm abertura de 16 mm nominal e rasgos para tiras macias; essa largura sem folga não qualifica o cabo do desenho. O alívio atua longe do conector, sobre proteção/apoio apropriado, jamais comprimindo o conector FPC. Os trechos finais param em zonas de serviço; pinagem, adaptação, largura com folga, orientação de dobra, torção, blindagem e comprimento elétrico permanecem bloqueados. Sobreposição entre corredores partilhados é documentada como ocupação conceitual, sem afirmar separação física dos cabos.

E18 fica a montante, em suporte e braço próprios. VL53L0X ocupa somente função de diagnóstico/PoC. KY-040 está junto ao eixo do rolete com envelope de acoplamento, sem fixação à travessa óptica. Relação pulsos/distância, escorregamento, shaft real e tensão de sinais não foram definidos. A iluminação é um envelope por vista, sem marca, componente ou potência selecionada; seus suportes e oclusões continuam pendentes.

## Verificações digitais

O gate relê cada STEP e STL imprimível, exige um sólido STEP válido por peça, malha fechada com volume positivo, bounds/volume coerentes e chama `scripts/validate_mesh.py` em cada STL. Reconstrói a cena com os STEP oficiais e compara o manifest, inclusive fontes/hash e geometria dentro das tolerâncias declaradas. Os bounds analíticos usam BRepBndLib sem triangulação, evitando a expansão numérica causada pelo cache STL. Rejeita exports adicionais, incluindo conjuntos/vendor. Os testes negativos removem cada câmera, Pi, trigger, cada canal e dock, além de substituir REFERENCE_ONLY por estados inválidos.

Colisões são calculadas por interseção volumétrica BRep. Para os modelos oficiais são usados bounding boxes conservadores derivados dos STEP importados; não equivalem a uma análise fina de encaixe. Todas as peças ativas são verificadas contra correia genérica, volume percorrido pelo produto e rolete. Pares físicos potencialmente sobrepostos passam por interseção BRep; a lista completa de volumes está em `validation.json`. O acesso do Pi é testado contra os envelopes estruturais; interferências de câmera/Pi e sobreposições não previstas fazem o gate falhar. Somente cinco pares de encaixe conceitual de ferragens e corredores partilhados de cabo são exceções explicitamente classificadas. Contatos sem penetração não são colisões. Peças alternativas A/B ficam fora da análise da montagem ativa.

Tolerâncias numéricas de readback: bounds STEP 1e−5 mm, volume STEP 1e−3 mm³, bounds STL 0,1 mm, volume STL até 1% ou 1 mm³. São tolerâncias de serialização, não tolerâncias de fabricação. O gate não aprova resistência, foco, oclusão, vibração, raio admissível de FPC, movimentação de serviço ou encaixe real.

## BOM preliminar e teste de montagem

| Item | Quantidade | Estado |
|---|---:|---|
| Pi 5 | 1 | Referência STEP oficial; placa física a verificar |
| Camera Module 3 standard / wide | 2 / 1 | Referências oficiais; óptica a validar |
| Conversor CSI-to-USB/UVC | 1 | Sem componente selecionado; bloqueado |
| Cabos para duas conexões CSI e terceira via USB | 3 rotas | Tipo/comprimento elétrico bloqueados |
| Base MDF / postes / travessa | 1 / 2 / 1 | Envelopes; dimensionamento estrutural pendente |
| Braços metálicos e ferragens/inserts | conjunto | Seção, cargas e fixações pendentes |
| Suportes de câmera / mounts | 3 / 3 | Mockups FDM de baixa consequência |
| Bandeja Pi / bumpers | 1 / 2 | Conceituais |
| Guias de cabo | 3 | Conceituais; revisar folga do FPC real |
| E18 / VL53L0X / KY-040 | 1 cada | Envelopes; variantes/interfaces não confirmadas |
| Suportes de trigger / diagnóstico | 1 / 1 | Conceituais |
| Dock / língua / adapters A e B | 1 / 1 / 1 cada | Sem interface real de máquina |
| Iluminação | 3 envelopes | Sem seleção de componente |

Teste executado: montagem digital, readback e exclusões estáticas do default. Teste físico **não executado**, sem autorização de fabricação. Sequência futura: medir placas/interfaces e G0; conferir espaçadores e ferragens em bancada; testar inserção/retirada e repetibilidade do dock; encaixar câmeras sem tocar lente/conectores; conectar cabos corretos com alívio e raio do fabricante; comprovar acesso ao Pi e refrigeração; passar gabarito de produto manualmente com máquina isolada; calibrar vistas/luz; medir trigger–captura, latência USB/CSI e KY-040 sob escorregamento; só então revisão de cargas/vibração e eventual liberação externa.

Bloqueios G0: identidade e dimensões A/B, datums reais, espessuras/material/capacidade de apoio, furos, zonas móveis e proibidas, acessos, massas/CG, hardware de retenção, vibração, curso de ajuste, distâncias ópticas e repetibilidade. O validador real retornou `BLOCKED_G0_INCOMPLETE` (exit 1), com 205 registros de bloqueio e P0/M0/P1 INCOMPLETE, incluindo estados de revisão fotográfica incompatíveis com o schema de coleta medida. O gate físico continua INCOMPLETE; PASS_REFERENCE_ONLY nunca altera esses bloqueios.

## Resultado executado

`make validate-optical-rig`: **PASS_REFERENCE_ONLY**, exit 0. Foram aprovados 18 pares STEP/STL, 120 verificações de exclusão e 13 testes negativos. O validador de malha existente passou nos 18 STL. A cena contém 47 componentes, dos quais 40 são considerados físicos ativos pelo gate. O schema canary existente também passou, sem regenerar seus artefatos.

| Pares com sobreposição volumétrica | Interpretação |
|---|---|
| post_LEFT / metal_arm_C_LEFT; post_RIGHT / metal_arm_C_RIGHT | Encaixes simbólicos de perfis, 6000 mm³ cada; juntas/ferragens pendentes |
| trigger_mount / trigger_metal_arm | Engaste simbólico, 850 mm³; detalhamento de suporte pendente |
| trigger_metal_arm / trigger_post; trigger_metal_arm / diagnostic_metal_arm | Junções simbólicas, 2000 mm³ cada; ferragens pendentes |
| channel_C_TOP / channel_C_RIGHT; channel_C_LEFT / channel_C_RIGHT | Corredores compartilhados, aproximadamente 27662 e 27638 mm³; separação física e torção de cabo pendentes |

Não houve penetração nas três exclusões genéricas verificadas, interferência volumétrica dos envelopes de câmera/Pi com os demais componentes ativos, nem invasão estrutural do acesso reservado ao Pi. Isso descreve somente a cena estática assumida; as sete exceções não são juntas fabricáveis resolvidas.

## Reprodução e integridade

```sh
cd /home/<usuario>/tcc-pnaat/github/cad-workspace
make generate-optical-rig    # apenas se diretório de saída vazio/inexistente
make validate-optical-rig
.venv/bin/python scripts/validate_g0_real.py data/g0/esteira-b-g0-photo-r03.yaml
sha256sum -c reports/OPTICAL-RIG-3CAM-R01.sha256
```

O gerador recusa sobrescrever artefatos existentes. O índice SHA-256 cobre os arquivos novos e o Makefile modificado; não inclui a si próprio. Os hashes das fontes obrigatórias são fixados no manifest. `exports/` permanece ignorado pelo Git conforme convenção existente. Nenhum commit/push foi feito; READMEs de PoCs e latex-workspace não foram alterados nesta tarefa.
