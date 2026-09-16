# Decisão preliminar MDF/FDM e grip óptico: R01

```text
REFERENCE_ONLY=true
MEASURED=false
FABRICATION_ALLOWED=false
```

STATUS: PRELIMINARY_OPEN_PHYSICAL_GATES_BLOCKED. Data: 2026-09-09.

## 1. Veredito preliminar

SPECULATIVE; A: portal de MDF contraventado + mounts FDM + ferragens é a primeira hipótese de baixo desembolso para laboratório seco. Decisão OPEN. MDF não é escolhido como garantia de precisão e FDM total não é recomendado como estrutura comum sem evidência. A alternativa B pode vencer se já houver perfis adequados ou se a estabilidade requerida superar o MDF.

## 2. Evidência e restrições

OBSERVED; 12 anexos analisados: oito da grande e quatro da pequena. MEASURED_FROM_PHOTO: nenhum. Nenhuma escala válida e nenhum comprimento inferido da aparência. Os caminhos originais constam abaixo, sem leitura, cópia ou publicação das fotos. SHA-256 de cada original BLOCKED pela proibição de ler github/evidencias. O erro de anexação envolvendo Sem, título.jpg e - não constitui foto analisada; não se presume conteúdo de Sem título.jpg. Não houve operação Git, comando para impressora ou alteração fora do workspace.

## 3. Identificação

OBSERVED; A/grande e B/pequena são aliases desta análise, coerentes com os relatórios. Grande: equipamento com aparência metálica, faixa preta, guia e acionamento lateral. IN 150 e IN 150 Large são apenas candidatos REFERENCE; etiquetas não permitem identificação inequívoca. Pequena: conjunto didático aparente, placas pretas brilhantes e motorredutor amarelo/cinza. Acrílico e motor TT são hipóteses SPECULATIVE, não identificação de polímero, fabricante ou modelo. Nenhuma câmera instalada é inequivocamente visível. O suporte com dois orifícios não prova duas câmeras.

## 4. Arquitetura principal e caminho de carga

SPECULATIVE; Pórtico comum desmontável com travessa óptica, montantes largos e contraventamentos; Adapter-A e Adapter-B específicos. Caminho pretendido: câmera → mount curto → travessa/montante → base distribuidora → adaptador → estrutura fixa verificada. Na pequena, preferir base que suporte conjuntamente a esteira e o portal se as laterais não suportarem carga. O CAD não resolve o contato final ao chassi nem representa todos os contraventamentos/juntas; sua continuidade visual não valida resistência.

## 5. Fallback e alternativa dedicada

SPECULATIVE; B: perfis/metal com mounts FDM se deformação, fluência das juntas, ambiente ou vibração inviabilizarem A. D: dois módulos dedicados quando interfaces/envelopes/óptica divergirem ou remontagem consumir mais tempo que duplicação. D é uma estratégia de duplicação e pode usar A ou B; não é uma quarta classe de material.

## 6. Raspberry Pi e quantidade de câmeras

SPECULATIVE; Raspberry Pi em caixa fixa apoiada na base/chassi, fora do balanço óptico e fora de um gabinete elétrico existente não caracterizado. Reservar ventilação, portas e alívio de tração. Modelo, fonte, conectores e limites de cabos BLOCKED. Premissa do usuário: TCC prevê três câmeras; o texto original não foi acessado fora do escopo. O conceito contém três por cena. Duas câmeras não foram confirmadas nas fotos; qualquer redução 3→2 permanece decisão aberta, com revisão de cobertura e sincronismo, nunca escolha implícita.

## 7. MDF

SPECULATIVE; Portal, travessa larga, contraventamento e bases distribuidoras. Selecionar espessura e acabamento somente após inventário e ensaio. Evitar aperto concentrado em bordas, furos repetidamente desmontados e superfícies de datum sem inserto/batente adequado. Slots podem fornecer ajuste grosso, mas exigem trava e referência de retorno. Nenhum slot ou espessura de fabricação foi modelado.

## 8. FDM na K1C

SPECULATIVE; PETG candidato para mounts de pequeno braço, guias de cabo, espaçadores e caixa, sujeito a estoque, processo e condições reais. Avaliar anisotropia, fluência, temperatura, orientação, interfaces aparafusadas e tempo de máquina. Não foram usados limites dimensionais da K1C ou perfis externos de impressão. Nenhum G-code, fatiamento, ajuste de impressão ou suporte de câmera real foi criado; os STL são caixas de inspeção digital.

## 9. Ferragens e metal

SPECULATIVE; Reaproveitar ferragens disponíveis após identificar tamanhos/condição: arruelas largas, porcas, parafusos passantes, cantoneiras e batentes. Chapas metálicas somente para distribuição/retorno repetível quando justificadas; perfis primários condicionados ao fallback. Custo/rigidez não inferidos pela aparência metálica. Não especificados torque, mola, clamp, rosca, retenção aprovada ou força admissível.

## 10. Interface pequena

OBSERVED; Laterais apresentam rasgos, parafusos e suporte saliente. BLOCKED; material, espessura, rigidez fora do plano, distância de bordas, papel dos fixadores e acesso interno. SPECULATIVE; não descarregar momento do pórtico em uma única placa ou no suporte saliente. Base comum sob apoios fixos é alternativa prioritária se a inspeção não encontrar chassi resistente; cadeira das fotos não é base de ensaio.

## 11. Interface grande

OBSERVED; Longarinas/chapas laterais, pernas em perfis, travessa baixa e fixações aparentes. SPECULATIVE; capturar estrutura fixa confirmada com distribuição de carga e acesso para manutenção. Guia/manípulos são ajustes do transporte e não devem servir de referência óptica por padrão. BLOCKED; seções, espessuras, capacidade, parafusos de tensionamento versus estruturais e presença de equipamentos TIJ no uso real.

## 12. Ajustes e limites

BLOCKED; não há curso físico liberado. Ajuste pretendido: altura Z, afastamento Y e pequeno ajuste angular das câmeras; posição X do trigger e interface de posicionamento longitudinal. No CAD, zonas verdes laterais 100×70×180 mm e superior 100×100×100 mm são ocupações SPECULATIVE, não cursos, tolerâncias ou volumes varridos validados. Fixar mínimos/máximos após FOV, foco, produto, folgas, acesso e ensaio de retorno. Não extrapolar curso de guia de catálogo para curso do grip.

## 13. Datums candidatos

SPECULATIVE; coordenadas x=transporte, y=transversal, z=vertical. Propor datum primário em plano de base rígida verificada, secundário em batente longitudinal e terciário em batente transversal/pino para repetição; ainda sem materialização. Em A, inspecionar perfil fixo; em B, considerar base comum em vez de bordas flexíveis. Superfície da correia pode definir plano de processo para medição, nunca apoio estrutural ou datum de montagem rígido. Montagem comum deve separar ajuste óptico de posicionamento dos adaptadores.

## 14. Zonas proibidas

SPECULATIVE; excluir correia superior/retorno, roletes, eixos, tensionadores, motor, transmissões, proteções amarelas, controles, alimentação, passagem total do produto e espaço para limpeza/ajustes. Guias e cabos existentes não podem receber carga do grip. CAD contém correia/proibição coincidentes, exclusões simbólicas de roletes/motor e passagem de produto. Distâncias de segurança reais BLOCKED; nenhuma margem regulatória é alegada.

## 15. Riscos mecânicos

SPECULATIVE; tombamento da mini-esteira, flexão das placas laterais, esmagamento do MDF, deformação/fluência de polímeros, folgas, torção da travessa, juntas sem referência de retorno e carga acidental por cabo. Aumentar braços piora momento: DERIVED M=F·e (força vezes excentricidade), sem resultado numérico pois massa/CG ausentes. Rigidez depende de material, seção e vão; não usar cubagem do envelope como massa/BOM real. Ensaiar caminho de carga com massa fictícia controlada somente após plano P0 revisado.

## 16. Vibração e calibração

SPECULATIVE; motor, roletes, emenda da correia, pés e juntas podem produzir movimento relativo. Massa menor no alto é favorável como hipótese, não garantia de frequência natural adequada. Medir deslocamento e desfoque com motor parado/ligado e velocidades de operação; observar deriva após tempo e desmontagens. Evitar isoladores macios escolhidos sem análise, pois podem introduzir movimento relativo entre câmeras e produto. B tem rigidez potencial maior; D elimina uma troca física mas duplica calibrações.

## 17. Cabos

SPECULATIVE; encaminhar pela estrutura fixa com alívio de tração antes de cada câmera e da caixa; folga controlada nos ajustes, sem laços próximos a faixa/eixos. Separar percursos de potência e sinal conforme interfaces reais. Comprimento, raio mínimo, conectores, sincronismo e interferência BLOCKED. Cabos do CAD são ocupações locais/descontínuas, não rotas completas ou verificação elétrica. Se cabos impuserem Pi próxima às câmeras, reavaliar localização em prateleira fixa antes de carregar a travessa.

## 18. Ambiente e química

SPECULATIVE; MDF exposto pode alterar geometria com umidade/limpeza; polímeros, acabamentos e adesivos dependem de agentes, temperatura e duração de exposição. Não há química compatível aprovada nem confirmação de inox 202 na unidade. BLOCKED; produtos de limpeza/processo, concentração, contato e umidade. Se houver lavagem/respingos incompatíveis com MDF, considerar B e proteção/material qualificados; FDM não é automaticamente solução química.

## 19. Reutilização externa

REFERENCE; Referências comparadas individualmente abaixo. Aproveitar conceitos de modularidade, mounts pequenos e separação de eletrônica; nenhum arquivo externo foi baixado, copiado ou adaptado. Nada foi qualificado como clamp ou suporte pronto. MakerWorld permanece BLOCKED para conteúdo primário/licença. Catálogos não substituem G0.

## 20. Valores de referência e conceito

REFERENCE; YAML A: compacto 1500×190 mm, Large 1470×300 mm; novo CAD usa somente cenário Large para ampliar comparação anterior. YAML B: nominal 450×200 mm, intervalos externos 350–550 mm de comprimento e 100–300 mm de largura não validados. SPECULATIVE; todos os outros números do novo CAD são escolhas de exibição registradas por componente, incluindo bases, caixa Pi 100×65×45 mm, espessuras e posição do motor. Câmeras genéricas: superior 60×60×40 mm, laterais 60×40×40 mm; posição/layout deliberadamente diferentes do envelope anterior, sem representarem câmera real. Geometria original anterior preservada. DERIVED; bounds e volumes em components.json calculados pelo kernel a partir dessas caixas; não medições. Deslocamento B em y=1200 mm é somente apresentação. Não há massa, orçamento, carga, torque ou tolerância mecânica numérica.

## 21. Medições ausentes e documentos

BLOCKED; Não presentes no workspace: AGENTS.md, docs/agent/context.md, docs/agent/workflow.md; tentativas de leitura registradas nesta sessão, busca de nomes limitada ao workspace. Não buscar equivalentes fora do escopo. Seis demais documentos obrigatórios foram lidos. Ausentes: identificação, escala, largura/comprimento reais, plano da faixa/retorno, interfaces, seções, espessuras/material, furos/roscas, condição, apoios, cargas/CG, produto, câmera/lente/FOV/foco, iluminação, trigger, encoder, cabos, química e requisitos de precisão. O README G0 exige dados reais com instrumento/método/repetições/incerteza; nenhum arquivo G0 foi preenchido com estimativas.

## 22. Próximo P0

BLOCKED para execução física; plano proposto SPECULATIVE: primeiro inventário e levantamento da mini-esteira apoiada em superfície estável, desenergizada conforme procedimento do laboratório; caracterizar laterais, travessas, apoios e fixações sem desmontagem não autorizada. Repetir na grande e definir caminho de carga. P0 seguinte: verificar envelope com gabarito sem carga óptica, acessos, ajustes, passagem do produto e pontos candidatos; depois planejar ensaio com massa/CG representativos e critério de parada por folga/deformação/interferência. Sem fabricar clamp ou montar câmeras antes desses dados.

## 23. Critérios para M0

BLOCKED; recuperar documentos obrigatórios; fechar rastreabilidade das fotos por hashes fornecidos ou leitura explicitamente autorizada em tarefa futura; registrar G0 real com sistema XYZ, instrumento, método, repetições e incerteza; confirmar três câmeras ou decisão formal de mudança; congelar produto/FOV/foco/iluminação/trigger; medir massa/CG e cabos; definir tolerâncias de deriva, repetibilidade e vibração a partir da resolução óptica e ensaiar. Verificar suportes fora das partes móveis, retenção, acesso e compatibilidade ambiental. Aprovação geométrica digital não libera M0 físico, fabricação ou segurança. Carga/repetibilidade P1/P2 e revisão humana permanecem gates subsequentes conforme fluxo disponível, sem inventar limiares.

## 24. Artefatos e validação

DERIVED; source CadQuery, STEP de conjunto, STEP/STL por envelope, components.json, validation.json e manifest sem circularidade. Releitura STEP/STL em processo separado passou com 60 componentes nas duas cenas, três câmeras e três luzes por cena; volumes positivos/finitos, malhas watertight/orientadas, bounds comparados e montagem STEP conferida por multiplicidade. Caixa Pi apoiada integralmente em base separada abaixo de z=0; nenhum componente funcional usa faixa como suporte e nenhum invade as exclusões representadas na posição nominal. Ajustes completos, FOV, carga, vibração, juntas, cabos completos e contato real ao chassi não validados. Todos os formatos carregam flags: comentários STEP, cabeçalho STL, campos JSON e texto/source. Manifest contém hashes de payloads e script, não de si próprio. MD lista hashes de artefatos; JSON contém hash do MD; índice SHA-256 cobre ambos e não a si próprio. Nenhum hash circular.

## Comparação das arquiteturas

Todas as avaliações desta tabela são SPECULATIVE. Nenhuma é resultado de ensaio ou orçamento.

| Arquitetura | Custo/tempo | Rigidez | Ajuste | Calibração/decisão |
|---|---|---|---|---|
| A; MDF + FDM + ferragens | Provavelmente menor desembolso com estoque e corte disponíveis | Depende de contraventamento, juntas e ambiente | Slots grossos + mount fino; retorno exige batentes | Candidata inicial; estabilidade deve ser ensaiada |
| B; metal/perfis + FDM | Pode custar mais; estoque metálico pode inverter | Maior potencial; seção/juntas ainda bloqueadas | Canais de perfis, se disponíveis; ferragens extras | Fallback para maior estabilidade ou ambiente incompatível |
| C; integral FDM | Filamento, tempo K1C, falhas e ferragens podem superar A | Fluência, anisotropia e muitas juntas exigem ensaio | Parametrização fácil, ajuste físico depende de juntas | Somente estudo de vão/carga pequenos; não selecionada |
| D; dois módulos | Duplicação estrutural, montagem e calibração; menos tempo de troca | Depende de usar A/B/C em cada módulo | Ajuste dedicado por bancada; dispensa adaptar toda troca | Considerar se transferência comprometer requisitos |

desembolso = compras de material + ferragens + consumíveis + usinagem terceirizada; esforço = corte + impressão + montagem + ajuste + calibração + retrabalho. Valores numéricos BLOCKED: inventário, preços, tempos e consumo ausentes.

## Respostas às 17 perguntas

### 1. As duas disposições permitem pórtico acoplado às partes fixas?

**SPECULATIVE**; Sim como hipótese espacial, pois há partes aparentes externas à faixa. Grande oferece candidatos mais claros; pequena pode exigir base comum independente que receba esteira e pórtico. Capacidade e acesso não demonstrados.

### 2. Mini-esteira: pontos adequados para MDF/FDM/ferragens?

**OBSERVED**; Há placas, rasgos, parafusos e suporte de dois orifícios. Adequação estrutural BLOCKED; não apertar MDF ou clamp diretamente sobre placa não caracterizada. Preferir distribuir carga e capturar elemento estrutural confirmado ou base independente.

### 3. Grande: barras/perfis/chapas/fixações?

**OBSERVED**; Perfis nas pernas, travessa inferior, longarinas/chapas laterais e parafusos/aberturas. Guia possui ajustes e não é datum confiável demonstrado. Não usar caixa elétrica ou capas amarelas como suporte.

### 4. Estrutura MDF, FDM, metal ou híbrida?

**SPECULATIVE**; Priorizar A híbrida: portal MDF contraventado, mounts FDM pequenos e ferragens metálicas. B metálica se rigidez/ambiente/repetibilidade exigirem ou se já houver perfis disponíveis.

### 5. Mais barata?

**SPECULATIVE**; A tem menor desembolso provável se MDF, PETG, ferragens e ferramentas de corte já disponíveis. Inventário, horas de oficina, consumo e retrabalho podem inverter resultado; FDM total não é automaticamente barato.

### 6. Melhor rigidez?

**SPECULATIVE**; B tem maior potencial com seções e juntas adequadas. Não existe ranking validado sem vãos, cargas, espessuras e ensaio. Contraventamento e folga das juntas podem dominar o material.

### 7. Mais simples de ajustar?

**SPECULATIVE**; B com perfis de canal pode facilitar reposicionamento, se esse tipo de perfil existir. A com slots de ajuste grosso e mounts curtos de ajuste fino também é simples; slots não definem repetibilidade.

### 8. Melhor preservação de calibração?

**SPECULATIVE**; Frame óptico comum rígido, batentes/pinos metálicos e ajustes travados. B tem vantagem potencial; D evita remontagem entre máquinas mas exige duas calibrações mantidas. Toda transferência exige verificação.

### 9. Peças MDF?

**SPECULATIVE**; Montantes largos, travessa, contraventamentos, placas-base e distribuição de carga em ambiente seco; não interfaces finas sujeitas a aperto pontual ou referência de precisão por borda nua.

### 10. Peças FDM?

**SPECULATIVE**; Mounts curtos PETG, espaçadores não críticos, adaptadores geométricos, difusores/anteparos conforme óptica, guias de cabos e caixa eletrônica ventilada. Sem suporte real de câmera até conhecer modelo/furação/massa.

### 11. Peças metálicas?

**SPECULATIVE**; Parafusos, porcas, arruelas/chapas de distribuição, pinos/batentes e cantoneiras existentes. Perfis primários apenas no fallback ou se estoque/ensaio justificar. Nenhuma rosca ou força de aperto especificada.

### 12. Raspberry Pi fora?

**SPECULATIVE**; Sim, caixa fixa na base/chassi, apoiada, acessível e ventilada. Reduz carga, momento, calor e tração de cabos no frame óptico; benefício quantitativo BLOCKED. Exceção apenas se interface/distância de cabos e sincronismo exigirem e houver avaliação mecânica.

### 13. Câmeras, iluminação e trigger?

**SPECULATIVE**; Reservar três câmeras: superior e duas laterais como hipótese herdada, não layout óptico validado. Luzes próximas dos campos úteis, evitando reflexos/oclusões. Trigger no mesmo frame, a montante da inspeção conforme sentido real; encoder separado no acionamento/interface própria após medição.

### 14. Adaptadores dependentes de medidas?

**BLOCKED**; Adapter-A: seção, paredes, superfícies, acessos, função/furação e carga do chassi. Adapter-B: material/espessura, posição/condição dos rasgos, parafusos e travessas. Ambos: datums, CG/carga, exclusões, ferragens, cabos e repetibilidade.

### 15. Um módulo, dois ou pórtico adaptável?

**SPECULATIVE**; Pórtico óptico comum com adaptadores específicos A/B como hipótese principal; manter geometria relativa das três câmeras. D se troca frequente, bases incompatíveis, campo de visão ou vibração impedirem plataforma comum.

### 16. Modelos reutilizáveis como referência?

**REFERENCE**; Relatórios/YAMLs locais para proveniência e envelopes; GitHub para organização de mounts e controle. Catálogos para variantes e planejamento de levantamento. Nenhum modelo existente qualificado como adaptador pronto.

### 17. Apenas inspiração, sem copiar?

**REFERENCE**; MakerWorld permanece descoberta com conteúdo/licença bloqueados; esteiras completas não equivalem a grip óptico. Rolos, correia, clamp e mounts externos não devem ser transplantados sem requisitos, licença e verificação dimensional.

## Registro individual das fotos

### Imagem 1: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/1.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista lateral oblíqua: correia preta, estrutura de aparência metálica, pés, travessa inferior, caixa lateral e controle; etiqueta 220 V aparente, sem identificação inequívoca.

**Interfaces fixas candidatas:** Longarinas, montantes e travessa inferior; parafusos laterais aparentes.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Guia regulável ao fundo; lateral oposta e underside ocultos; encurtamento longitudinal.

### Imagem 2: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/2.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista girada e oblíqua: motor sob extremidade, terminais amarelos, pernas e guia com manípulos.

**Interfaces fixas candidatas:** Perfis das pernas e longarina; barra de guia é regulável, não datum estável demonstrado.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Rotação da câmera e perspectiva acentuada; cabos ocultam regiões; nenhuma dimensão dedutível.

### Imagem 3: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/3.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista longitudinal pelo acionamento: motor externo, caixa lateral, terminais amarelos, pés e guia.

**Interfaces fixas candidatas:** Longarinas e estrutura inferior; acesso candidato por fora da faixa.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Profundidade fortemente comprimida; face traseira e contatos sob a correia não visíveis.

### Imagem 4: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/4.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista oblíqua oposta: duas estruturas de pernas, travessa baixa, parafusos/aberturas laterais e guia elevada.

**Interfaces fixas candidatas:** Montantes e travessa; chapas laterais apenas candidatas após verificar função e espessura.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Perspectiva; parede, piso e cadeira não são escala conhecida.

### Imagem 5: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/5.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista pela extremidade livre: correia, terminais amarelos, guia com duas hastes, travessa entre pés.

**Interfaces fixas candidatas:** Perfis das pernas e travessa inferior.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Longarinas em fuga; pontos de fixação ao fundo não resolvidos.

### Imagem 6: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/6.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista pelo motor: motor sob rolete, chapa lateral com aberturas, guia ajustável, estrutura inferior.

**Interfaces fixas candidatas:** Longarina e montantes; evitar região do motor e regulagem da correia.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Parte traseira próxima da parede; acesso para ferramenta não demonstrado.

### Imagem 7: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/7.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista longitudinal próxima da parede: motor, caixa, seta de transporte aparente e guia.

**Interfaces fixas candidatas:** Pés/montantes e longarinas visíveis parcialmente.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Parede limita acesso nesta disposição; não prova instalação definitiva; forte fuga longitudinal.

### Imagem 8: grande

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-grande/8.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Esteira de bancada com estrutura de aparência metálica; modelo/fabricante BLOCKED

Vista lateral mais abrangente: chapa longitudinal com sequência de aberturas, parafusos, pernas, travessa baixa e guia com manípulos.

**Interfaces fixas candidatas:** Perfis e travessa inferior priorizados; furos aparentes não têm diâmetro, rosca ou função confirmados.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Ainda oblíqua, sem régua; etiquetas não resolvem fabricante/modelo; lado oculto desconhecido.

### Imagem 9: pequena

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-pequena/1.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Mini-esteira didática aparente; modelo/fabricante BLOCKED

Vista inclinada: placas pretas brilhantes com rasgos e parafusos, correia clara, motorredutor amarelo/cinza e fonte externa; peça pequena solta sobre região central.

**Interfaces fixas candidatas:** Placas laterais, parafusos e possíveis travessas internas; material não identificável pela aparência.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Esteira está apoiada sobre cadeira; orientação não define posição operacional ou base estável.

### Imagem 10: pequena

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-pequena/2.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Mini-esteira didática aparente; modelo/fabricante BLOCKED

Vista lateral: placas recortadas/rasgadas, fixadores e suporte saliente com dois orifícios circulares, além da fonte e cabos.

**Interfaces fixas candidatas:** Fixações das placas e suporte saliente como candidatos leves; função do suporte não confirmada.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Ocultação interna e reflexos; suporte não comprova sensor instalado nem capacidade de carga.

### Imagem 11: pequena

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-pequena/3.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Mini-esteira didática aparente; modelo/fabricante BLOCKED

Vista voltada para faixa clara: placas laterais com parafusos/rasgos, suporte com dois orifícios; parte amarela do acionamento visível.

**Interfaces fixas candidatas:** Placas e fixadores; suporte com dois orifícios pode inspirar interface de sensor, ainda sem identificação.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Equipamento inclinado; largura e espessura física não recuperáveis sem escala.

### Imagem 12: pequena

Caminho original (não acessado): `/home/<usuario>/tcc-pnaat/github/evidencias/fotos/esteira-pequena/4.jpg`

**SHA-256: BLOCKED (null).** Usuário proíbe ler github/evidencias; analisada somente imagem anexada. Hash exige bytes originais, não pixels exibidos.

**OBSERVED; identificação:** Mini-esteira didática aparente; modelo/fabricante BLOCKED

Vista superior oblíqua: faixa clara contínua, laterais pretas com rasgos, motorredutor lateral e suporte de dois orifícios ao fundo.

**Interfaces fixas candidatas:** Laterais e união aos apoios de extremidade, condicionadas à inspeção física.

**Zonas móveis:** Correia e retorno, roletes/eixos, acionamento. Foto estática não demonstra movimento.

**Zonas proibidas:** Proposta SPECULATIVE: não apoiar na correia, roletes, eixos, proteções de extremidade, motor, controles, cabos ou guia móvel; preservar passagem do produto e manutenção.

**Escala:** BLOCKED: nenhuma escala física válida. Parafusos, piso, cadeira, plugue e pessoas não são padrões dimensionais.

**Perspectiva:** Interior, eixos e verso dos parafusos incompletos; aparência não identifica polímero ou modelo.

## Referências de descoberta e limites

- [github](https://github.com/simonlansing/conveyor-belt); REFERENCE. Consultado em 2026-09-09 Projeto didático documenta perfil de alumínio, peças impressas, mounts de câmera/sensores e controle Raspberry Pi. Reutilizar organização modular e separação das funções como referência; nenhuma peça foi importada. Não comprova interface da mini-esteira nem rigidez óptica. Repositório indica MIT; conferir licença do arquivo específico e atribuição antes de reutilização literal.

- [makerworld_modular](https://makerworld.com/en/models/1980909-modular-conveyor-wi-fi-servo-tt-motor-manual); BLOCKED. Abertura retornou HTTP 402; pesquisa não confirmou conteúdo primário desta página. Título fornecido sugere modularidade e alternativas de acionamento; apenas descoberta/inspiração. Não validar geometria, licença, compatibilidade K1C ou parâmetros de impressão a partir do título. Não copiar arquivos.

- [makerworld_generator](https://makerworld.com/en/models/2188718-conveyor-generator-poop-conveyor); BLOCKED. Abertura retornou HTTP 402; conteúdo primário não confirmado. Título fornecido sugere gerador de esteira para resíduos de impressão; finalidade distinta da metrologia óptica. Somente pista de parametrização, sem geometria ou licença verificadas. Não copiar arquivos.

- [in150](https://www.casadodatador.com/datadores-ink-jet/esteira-transportadora-em-inox-para-datadores-inkjet-modelo-in-150); REFERENCE. Abertura falhou por decodificação; valores provenientes exclusivamente do relatório local obrigatório. 1500 mm de comprimento e 190 mm de lona no relatório de fornecedor. Candidato comercial, nunca identificação da máquina ou furação real. Não usado no novo cenário A Large.

- [large](https://www.casadodatador.com/datadores-ink-jet/esteira-transportadora-em-inox-202-para-datadores-inkjet-modelo-in-150-large-220v); REFERENCE. Página comercial consultada em 2026-09-09; valores geométricos do cenário rastreados ao YAML local. Catálogo apresenta IN 150 Large, 30 cm de largura e altura de 75 cm. Usado apenas como descoberta e comparação. Envelope 1470 x 300 mm vem do YAML de referência, não das fotos. Não identifica liga metálica, modelo ou capacidade da fixação da unidade real.

## Próximas medições, em ordem

1. Mini-esteira: material/espessura e condição das laterais; seção das travessas/apoios; função e coordenadas dos fixadores/rasgos, acesso interno e plano de base.
2. Largura útil, comprimento e alturas reais; correia de retorno, roletes, motor, guias e percurso do produto, com escala física no plano e instrumento adequado.
3. Grande: seções/espessuras dos perfis e chapas, identificação das fixações estruturais versus ajustes e acessos; confirmar etiqueta/modelo.
4. Conjunto óptico real: três câmeras, lentes, luzes e trigger; dimensões, massas/CG, campo de visão, distância de trabalho, conectores e flexibilidade de cabos.
5. Estoque de MDF/PETG/ferragens/perfis, ferramentas, tempo disponível, ambiente e requisitos de deriva/repetibilidade; ensaios comparativos após levantamento.

## Arquivos criados e SHA-256

Relatórios: `reports/GRIP-MDF-FDM-DECISION-R01.md`, `reports/GRIP-MDF-FDM-DECISION-R01.json`; índice final `reports/GRIP-MDF-FDM-DECISION-R01.sha256`. Hash do MD está no JSON e no índice; hash do JSON somente no índice. O índice exclui a si próprio. Hashes de fotos não foram substituídos por hashes destes relatórios.

| Arquivo | SHA-256 |
|---|---|
| `cad/cadquery/concepts/grip-mdf-fdm-r01.py` | `1175de374e9ae0b8d9c67878a5051a4740bb8a144ad21c199dd7a50dd9aedc10` |
| `exports/concepts/grip-mdf-fdm-r01/A_adapter_left.step` | `bb8bfbf34f1f1925406e45cbb95b2d8bc18b916b6b20829ace04695b31baff39` |
| `exports/concepts/grip-mdf-fdm-r01/A_adapter_left.stl` | `8e5632c0d4d860f54ac5a761f7acfe2e8a026d84f130d3f973b6dee6964bff19` |
| `exports/concepts/grip-mdf-fdm-r01/A_adapter_right.step` | `a7e56f76e96647ea4501a28d171907691a9f8cb068836f56e234e08de4b28906` |
| `exports/concepts/grip-mdf-fdm-r01/A_adapter_right.stl` | `cdc1ba5bd6236483842ec5e676baab1891c42e5acaa59652ccc35b4c130e0ef7` |
| `exports/concepts/grip-mdf-fdm-r01/A_adjust_left.step` | `82c5bba8d51300304fac7854e126f581defdb07bd7e826915da084804c933040` |
| `exports/concepts/grip-mdf-fdm-r01/A_adjust_left.stl` | `2bd69720b10eb005e7431fc638cbe5ca58321fd23fbe182259512c9f66369600` |
| `exports/concepts/grip-mdf-fdm-r01/A_adjust_right.step` | `c554581918f4a9c7138b7f8713617e4dda0600e3190a8e955d1da8f19edfddd3` |
| `exports/concepts/grip-mdf-fdm-r01/A_adjust_right.stl` | `4a18916fde767c489fd08927734759b2a3a9a8680cb4e933d90c8ff188d85560` |
| `exports/concepts/grip-mdf-fdm-r01/A_base_left.step` | `82c755c4deb4a2939666390dec3234b255c37bf5297ca9927d5fbf530384e25b` |
| `exports/concepts/grip-mdf-fdm-r01/A_base_left.stl` | `9177928fbdfb1300820b4184e1a4269d0968b1ec75dfec2539a85bc9fcca801b` |
| `exports/concepts/grip-mdf-fdm-r01/A_base_right.step` | `032cc1ce731831e95465cc3886acb0d9dfbe39d95ace4635c46e1b4a01cbc3bf` |
| `exports/concepts/grip-mdf-fdm-r01/A_base_right.stl` | `113d95d4c9c95331606cc6253893055421783fdef1ca6e2ec1217376fb8548d3` |
| `exports/concepts/grip-mdf-fdm-r01/A_belt.step` | `ab52a53c38918988f0c723bb9462c13c4336b2b40dc9e53dda89eef69a96b872` |
| `exports/concepts/grip-mdf-fdm-r01/A_belt.stl` | `0cafc788875a47213613fe5a38cc84ae369e2abb7d03f37764b7919be18ab3ae` |
| `exports/concepts/grip-mdf-fdm-r01/A_belt_exclusion.step` | `e219f18bb095d2244c523a55f3abb3ad5662268e98fc56e8f62c84502174856a` |
| `exports/concepts/grip-mdf-fdm-r01/A_belt_exclusion.stl` | `0cafc788875a47213613fe5a38cc84ae369e2abb7d03f37764b7919be18ab3ae` |
| `exports/concepts/grip-mdf-fdm-r01/A_cable_left.step` | `8581e39efbaa04409a29af3f925dfd06c26c333f10e1bb4c4bb4093804cba221` |
| `exports/concepts/grip-mdf-fdm-r01/A_cable_left.stl` | `8b7f455008acb35667edc59dd4907c3bf8f4b672823e9898a6340cd3fe53ee44` |
| `exports/concepts/grip-mdf-fdm-r01/A_cable_right.step` | `2cbc0edccfa3dea765dc27cceafa492aa52d0567f8b402e1bd9ad958963327c2` |
| `exports/concepts/grip-mdf-fdm-r01/A_cable_right.stl` | `308c4f8ed8992633fe4ac799ddd53a30429955b59f1843222f32a3abbebd5474` |
| `exports/concepts/grip-mdf-fdm-r01/A_cable_top.step` | `761b38a866a0a36fdc334a62053352070ffb479e812471084562c6bee07dfe24` |
| `exports/concepts/grip-mdf-fdm-r01/A_cable_top.stl` | `07f25e1904dab5e5c5f5ab544db1cbe7e6a93b14a7b49ce02cc45ecd4b15fe2e` |
| `exports/concepts/grip-mdf-fdm-r01/A_camera_left.step` | `822d68ad150f3f4186085fe75e125f3b4c905a9f37c357ebfae24cbe034ba031` |
| `exports/concepts/grip-mdf-fdm-r01/A_camera_left.stl` | `ebcf12cd74143eaf0b1aa2ed6ab79500efdd7895669bea73c5c0f7f1c6c2c693` |
| `exports/concepts/grip-mdf-fdm-r01/A_camera_right.step` | `045d064915b2e040a0cdfe61ba5bbf01e6e8b9f3a6977e932b1828ebc0aec626` |
| `exports/concepts/grip-mdf-fdm-r01/A_camera_right.stl` | `481ae47f9dea66b5aea8a88abbcc161b32ab69de5c20910de94195b4cc2d8771` |
| `exports/concepts/grip-mdf-fdm-r01/A_camera_top.step` | `bfbab0563407a98c2d23a161f608e7589ccb56ff6d13427017401da758dd9940` |
| `exports/concepts/grip-mdf-fdm-r01/A_camera_top.stl` | `e82f6ac4550564422eb19fac1a111eecb83f0a9aefed38e6365b77f75caf02f7` |
| `exports/concepts/grip-mdf-fdm-r01/A_crossbar.step` | `04723600d952e888b36cbe3ab17a53a894e5b7d5af09d01d00a0019a55467cbb` |
| `exports/concepts/grip-mdf-fdm-r01/A_crossbar.stl` | `a4133bdf92a29b3a7f87f7fe162593e233de835b12bb7ab07029b4ca74a49698` |
| `exports/concepts/grip-mdf-fdm-r01/A_lighting_left.step` | `1e101daa3b519affe983aaa46ba7eced33f9573ca380fb62c35d116525ea25c0` |
| `exports/concepts/grip-mdf-fdm-r01/A_lighting_left.stl` | `605722d8dcdf9691373e81fe58cbe41c83ea17f83b425e8ca41b000f31e9e11a` |
| `exports/concepts/grip-mdf-fdm-r01/A_lighting_right.step` | `805b923e66e3e67c224a776ee4b1c6f7a1c4244bfaacb014ef102f4f3bcb4152` |
| `exports/concepts/grip-mdf-fdm-r01/A_lighting_right.stl` | `0c46a5ae5053619e2255987925764e02ef211e74465b1fc3c28d9c1941b79fa0` |
| `exports/concepts/grip-mdf-fdm-r01/A_lighting_top.step` | `0d1333b657ce86dc9790923f21bdaf863ada2950f38ccf56911ea01768a49920` |
| `exports/concepts/grip-mdf-fdm-r01/A_lighting_top.stl` | `ba14c4a07fb2602634260f65c3e8c796b26cb8bee75a64164f01bcc96c4bd1c0` |
| `exports/concepts/grip-mdf-fdm-r01/A_motor_exclusion.step` | `497efff95aeed2e558868bbea6a30b1d78a2ea48d16701b07468f6656d538e5b` |
| `exports/concepts/grip-mdf-fdm-r01/A_motor_exclusion.stl` | `5a8a4ef4a24248dd59b0eff458050ccde8c9d497cb78dd186b3295609cce12eb` |
| `exports/concepts/grip-mdf-fdm-r01/A_mount_left.step` | `46bf12f3a4708633bd0a4e1b2a341d9cb18334610cae215e506ee676ff79f6e9` |
| `exports/concepts/grip-mdf-fdm-r01/A_mount_left.stl` | `daa0bf5efb1c68d43c89e8387f48c8602f90e97170d04827fc5be06c5085b4c4` |
| `exports/concepts/grip-mdf-fdm-r01/A_mount_right.step` | `8f9da72b9fcf1da760fa5fb170471f7c0a465ee511f4a3b3477cbb4341a6c770` |
| `exports/concepts/grip-mdf-fdm-r01/A_mount_right.stl` | `5933f77635734c90e0b7d5ad2962199af065bda25629f50a4e988c2dd2ee8113` |
| `exports/concepts/grip-mdf-fdm-r01/A_pi_box.step` | `25d037f8cb4a4dc1c7f5c4d948222a302abca5e318d81430743fba1e4f5d06e8` |
| `exports/concepts/grip-mdf-fdm-r01/A_pi_box.stl` | `1cf72a7075853c0d1094a000fadfd2603766bde489dcf1ed4932ab068e762885` |
| `exports/concepts/grip-mdf-fdm-r01/A_post_left.step` | `7e86a09bd52ff7901051459887d1d7a4f19eee4e6a5c91593e9f4be9a91ce549` |
| `exports/concepts/grip-mdf-fdm-r01/A_post_left.stl` | `0c4aa968ae6d58cdfd06fd951d6c76f0a1bbf3f7a5cea87d1bba7ae6f4b2f7cc` |
| `exports/concepts/grip-mdf-fdm-r01/A_post_right.step` | `910ffba36ad07b4fdc15866d03c504ad560f21cd1e0c76292389399fe89fc29c` |
| `exports/concepts/grip-mdf-fdm-r01/A_post_right.stl` | `c6f07a7e72b58848af657486377b750164b1ef60c73e204e68f619df2d36a11b` |
| `exports/concepts/grip-mdf-fdm-r01/A_product_sweep.step` | `bfd2ec4b7077ced8050342c2e6808c0b329e6e2847adb84e87b65a30457c806d` |
| `exports/concepts/grip-mdf-fdm-r01/A_product_sweep.stl` | `805e8b21effe36d91b5b07373d84cc6a2e7989848dbd79bd8765fee6861b0a41` |
| `exports/concepts/grip-mdf-fdm-r01/A_roller_exclusion_-1.step` | `3394e685c59c25c2c4f99be8d37b3f22a96013947a878c7a33a8ee89ca512607` |
| `exports/concepts/grip-mdf-fdm-r01/A_roller_exclusion_-1.stl` | `68f9790a46b3f1090100d7a3d343abe5377116a8a86cc315049a94629c397ce7` |
| `exports/concepts/grip-mdf-fdm-r01/A_roller_exclusion_1.step` | `27f6f656f3de59ffbd4704d2513634d9fb247ef8c2fde79f2d3c405d764c76dd` |
| `exports/concepts/grip-mdf-fdm-r01/A_roller_exclusion_1.stl` | `b18f64e5e31ede58a1aca6a3bd73b5d39e177a2d805cdea87d03b3b8ad6f9f9e` |
| `exports/concepts/grip-mdf-fdm-r01/A_top_adjust.step` | `a56a845741bf82162b6a1eb0c36accb1300c31f8bb86944d7bfb6a410619fa20` |
| `exports/concepts/grip-mdf-fdm-r01/A_top_adjust.stl` | `b15b73f5685e906e1b6277c6269b7ba713e4de81b079b89577860814b13cbe37` |
| `exports/concepts/grip-mdf-fdm-r01/A_top_mount.step` | `c9a83e479ee70cc8b2bbeabbbbcd71795b3baf5cce78cd91ccbb62e1694cb2b7` |
| `exports/concepts/grip-mdf-fdm-r01/A_top_mount.stl` | `5bf0addf629fe93633504b29d927fa44411546bed1fbf442bb7323adeef23531` |
| `exports/concepts/grip-mdf-fdm-r01/A_trigger.step` | `1bc3d72c4b8a9a91f18bac48eec0817c01ee79fcbd8e158ddd35452cc898e913` |
| `exports/concepts/grip-mdf-fdm-r01/A_trigger.stl` | `29563320c40fb83b95da9b6427395d829f1fe2b6948eea484da02bec913e1945` |
| `exports/concepts/grip-mdf-fdm-r01/B_adapter_left.step` | `5e03c4f7702022a4ab7e9cf21cfb7cb2431d59f320267a92996828834c7aef39` |
| `exports/concepts/grip-mdf-fdm-r01/B_adapter_left.stl` | `333bf158f017ef15bfd646ded8b0380d197db87fc6a11aefe3d6f0bffcaedf0e` |
| `exports/concepts/grip-mdf-fdm-r01/B_adapter_right.step` | `c7448a6a5938aca4f07171647d36028463e28ebb82df670126601341b8745896` |
| `exports/concepts/grip-mdf-fdm-r01/B_adapter_right.stl` | `91fe3d0f454f37a15a2a7e05de67c1c325bcc2f65e19b56e6a53ad5ba92f09c8` |
| `exports/concepts/grip-mdf-fdm-r01/B_adjust_left.step` | `8152defafef0d52d77c58f008ee4f27b84764ade633250262f73d5f2e511b8c8` |
| `exports/concepts/grip-mdf-fdm-r01/B_adjust_left.stl` | `88cc0691ecfb3c0e463d6a4676d78a2ee121acd53a8358b6429d6c07aa202176` |
| `exports/concepts/grip-mdf-fdm-r01/B_adjust_right.step` | `96a9df88dd0f7463cc9373772be3bd2edd5b80f7c4d93e6b104b01aa8c857d2f` |
| `exports/concepts/grip-mdf-fdm-r01/B_adjust_right.stl` | `eed29e0b2134dbd0aa35195d1bae36b7233fb0a69bb1f2b7e73165ba63305031` |
| `exports/concepts/grip-mdf-fdm-r01/B_base_left.step` | `fae04cad3e562e8f2177bb422f512c5584bb93bca707ded9eff932c6cbe53c48` |
| `exports/concepts/grip-mdf-fdm-r01/B_base_left.stl` | `4d20e96f1a37050f779d05c7e5153348208ca2bf8e8f6625dee08446c496bf5a` |
| `exports/concepts/grip-mdf-fdm-r01/B_base_right.step` | `223c0f250d26abba3f7e268bc97327b4255245422aa8cf082e6cf7991a8135ca` |
| `exports/concepts/grip-mdf-fdm-r01/B_base_right.stl` | `4233839602f6e2384a7502d667344885719c2bda7cfa82c96d2cdd8daa02498d` |
| `exports/concepts/grip-mdf-fdm-r01/B_belt.step` | `c0dc7e2d3479ea9fcb57127f0f8f9087e5c55d08d64e7e9d12817e35ed304d57` |
| `exports/concepts/grip-mdf-fdm-r01/B_belt.stl` | `dd38dcfb72234711afbe60ab4d6c90e0037a9acf23f6e7871214886ffce4ff1d` |
| `exports/concepts/grip-mdf-fdm-r01/B_belt_exclusion.step` | `75938b8e4278d3f01f1c0d63bfc203b4e43a22e936fc4b6411612bb7887999a0` |
| `exports/concepts/grip-mdf-fdm-r01/B_belt_exclusion.stl` | `dd38dcfb72234711afbe60ab4d6c90e0037a9acf23f6e7871214886ffce4ff1d` |
| `exports/concepts/grip-mdf-fdm-r01/B_cable_left.step` | `3e0f2242ec2f2f00f5b27dc64249d6807628b119911c41d7e0bc9879f1afd491` |
| `exports/concepts/grip-mdf-fdm-r01/B_cable_left.stl` | `808af8470505c2fefdcfbcde25e0bedc24b4db049623a5362eafb08e1519b306` |
| `exports/concepts/grip-mdf-fdm-r01/B_cable_right.step` | `c803630ef074aa19f3fedcaf025c80b50d7b4ee9158de17021be0b2290bcb0b0` |
| `exports/concepts/grip-mdf-fdm-r01/B_cable_right.stl` | `15ea39580180c2ce69cccab543117da4c351f1d711de9fa7bfa9b5cac1f99af1` |
| `exports/concepts/grip-mdf-fdm-r01/B_cable_top.step` | `34bc2157bb729dc8cd4252c5401b950f825369990d9c06fa67ca99b006b99310` |
| `exports/concepts/grip-mdf-fdm-r01/B_cable_top.stl` | `217503372e7780fead8630e4c0b71871dbeb90cee91247a1201a44381dafe4d0` |
| `exports/concepts/grip-mdf-fdm-r01/B_camera_left.step` | `b063fc6992adedab79a217f9a9141fc9e623bcedee41599525142bed92900279` |
| `exports/concepts/grip-mdf-fdm-r01/B_camera_left.stl` | `43f08f665c8873f84d5f9c644ce24a3c8981d5ffab6d77e943d79fcde00f62fb` |
| `exports/concepts/grip-mdf-fdm-r01/B_camera_right.step` | `28e1df6bd88bad7b6188517570cdae6974409a995300f79bd4fe77d83b56d8b1` |
| `exports/concepts/grip-mdf-fdm-r01/B_camera_right.stl` | `242186404cc70caf6d39374b4f48336eb865aaa19e24facb29aa256fa4ed20fa` |
| `exports/concepts/grip-mdf-fdm-r01/B_camera_top.step` | `954826e4bf145382099562db19a4c61c6d779573c5df7bc371f805644e0fa4aa` |
| `exports/concepts/grip-mdf-fdm-r01/B_camera_top.stl` | `83e5c607150d434046bfdf95b1ea01f51a750dfb43f18702924d3cd17f8c09cb` |
| `exports/concepts/grip-mdf-fdm-r01/B_crossbar.step` | `b5edece74c53339f748d2145d744694e7b44dcde662f76877967f2e1790e9d60` |
| `exports/concepts/grip-mdf-fdm-r01/B_crossbar.stl` | `ff30cafdd78121d57822c9ccdda319a94b821e4422e5f5b35b3b0aebb06630e6` |
| `exports/concepts/grip-mdf-fdm-r01/B_lighting_left.step` | `a58b1a0bbeadc7eee46890a1d81ffe49611bd042399052586c55cd9ea7b4b6d6` |
| `exports/concepts/grip-mdf-fdm-r01/B_lighting_left.stl` | `2a30cb65ea78f77c2bb83b30ba004434525f278ad02a852db307dd0f2753b815` |
| `exports/concepts/grip-mdf-fdm-r01/B_lighting_right.step` | `8833054b572f0852906e012e2f367d1534f34db986e35188a98123ce4838299d` |
| `exports/concepts/grip-mdf-fdm-r01/B_lighting_right.stl` | `5e2d42aa914ddbda761af1383a4338ba4045316c31e36f36e890cf56612592e4` |
| `exports/concepts/grip-mdf-fdm-r01/B_lighting_top.step` | `3f2029bd5ccab5caf56f6ebf48b10068f5e5f1253774d6dea197e942a3772262` |
| `exports/concepts/grip-mdf-fdm-r01/B_lighting_top.stl` | `530b89796debd68f31cc64c5908af862a1f2aebe8df2699a6bec04b94a38e6fc` |
| `exports/concepts/grip-mdf-fdm-r01/B_motor_exclusion.step` | `7b83f1dee49b7911e9fc528c122954bb8d247f86ddc71aa241af30fc40363903` |
| `exports/concepts/grip-mdf-fdm-r01/B_motor_exclusion.stl` | `ee28e9fdc5b0b406d46fcef05c4a0b19e95f28238e0283906256049e2f664772` |
| `exports/concepts/grip-mdf-fdm-r01/B_mount_left.step` | `8aac67ff7af66c34bd794d38f2a1c1f55ae9bb98175344ab1e4dda20f9d74edf` |
| `exports/concepts/grip-mdf-fdm-r01/B_mount_left.stl` | `7316eecef71bf91a136a6400d1be932d66bf7aa54dc7d5d67bf8d967aead4b61` |
| `exports/concepts/grip-mdf-fdm-r01/B_mount_right.step` | `7501462d88f3a85b3c316147b34d5f7699951860f269761a3b211b95706820c0` |
| `exports/concepts/grip-mdf-fdm-r01/B_mount_right.stl` | `e2cb203ece5208c2f180dd7b85deb976dbb734abfbe34f90a6878fb6cae1bc76` |
| `exports/concepts/grip-mdf-fdm-r01/B_pi_box.step` | `dcee7d7a2fa008c6bef126a2bc5e52e94ae223537a0f2c342fd8351276b49382` |
| `exports/concepts/grip-mdf-fdm-r01/B_pi_box.stl` | `8db240e24a0641235c7337d90877f920070eaf8ca81bb35b6fa2c602c2ca7198` |
| `exports/concepts/grip-mdf-fdm-r01/B_post_left.step` | `1d166f055df1ab8732b9b66a80bdf06d625c79d4683f9419349a0f31581a75df` |
| `exports/concepts/grip-mdf-fdm-r01/B_post_left.stl` | `d3d1a1da8ad54aeb9800c4ed7e70546d06e667a9399285b0d2005249e4e3ce35` |
| `exports/concepts/grip-mdf-fdm-r01/B_post_right.step` | `94bbbe4c7673757c19bd9378339a6e5cc0b4c5234a09e67044c5110a8303b4c8` |
| `exports/concepts/grip-mdf-fdm-r01/B_post_right.stl` | `ce31c617f2e63dec44c7bb37b8d628423c75598a68b8126f82f29b0ce45d455f` |
| `exports/concepts/grip-mdf-fdm-r01/B_product_sweep.step` | `59a6882dbfda419c9a569ee2c11ac507962cdbe165b4b2d0f48d578dfb1e69d2` |
| `exports/concepts/grip-mdf-fdm-r01/B_product_sweep.stl` | `c56b6dd79c24461a1500ea8ff8791d402326d85251a0a62b9b6408adbd9abff7` |
| `exports/concepts/grip-mdf-fdm-r01/B_roller_exclusion_-1.step` | `85e755e200c9856e7296df8dc9c4ccfb35668560b61d5ab869041187959e57f7` |
| `exports/concepts/grip-mdf-fdm-r01/B_roller_exclusion_-1.stl` | `f05e38f3d0b53525cdd07405dc549b095d12855e7f617ba0ab32e582ee30dfb4` |
| `exports/concepts/grip-mdf-fdm-r01/B_roller_exclusion_1.step` | `cc6aeb23767206ffdffdd68c55f87435e5749cafa2ff9f3c365275e8cc131b4e` |
| `exports/concepts/grip-mdf-fdm-r01/B_roller_exclusion_1.stl` | `d9fe10d2c0bbcb2837c023cd6ad1fd957b9a158bef99eddda368d57f8c573086` |
| `exports/concepts/grip-mdf-fdm-r01/B_top_adjust.step` | `2f33562b4cf9550d7ab0bbc6e7fb8e56221955588f2e3354c673065a4369ded1` |
| `exports/concepts/grip-mdf-fdm-r01/B_top_adjust.stl` | `f6a272f0ed1c5af974d4778fccec71288e0c85e1bbaf36cd2d90569577e83e27` |
| `exports/concepts/grip-mdf-fdm-r01/B_top_mount.step` | `9d9c59ae6bb1ed51b83c235ba75b68b2c2d86a955d6331b7e30c2ddfab615270` |
| `exports/concepts/grip-mdf-fdm-r01/B_top_mount.stl` | `2159f30b2369a6498c9ae0d80cdb97b7f1ddedb9d9492e40ec95f877be06e891` |
| `exports/concepts/grip-mdf-fdm-r01/B_trigger.step` | `f99a5119dc62f14318b58a67ad360ed511f2861390025658364ccf60cb5a30ec` |
| `exports/concepts/grip-mdf-fdm-r01/B_trigger.stl` | `f9a8f11f53891b835ab7a5ba697c63a296666a7cd9dcd7f123cc56f74406e79c` |
| `exports/concepts/grip-mdf-fdm-r01/REFERENCE_ONLY_NOT_FOR_FABRICATION.step` | `4e9af3d9c72fe360d15bf9d6f72cd274ee897d55ced2b604900c1ccfd8c80842` |
| `exports/concepts/grip-mdf-fdm-r01/components.json` | `38fe264cb92c43cf859d202c13203f4fe0f5e336d5b7eb6b913a3df1dc7a2958` |
| `exports/concepts/grip-mdf-fdm-r01/manifest.json` | `244b1fd0873990a1c85b1b5c039f091a7f913b65997f070a1fc33db456a0086a` |
| `exports/concepts/grip-mdf-fdm-r01/validation.json` | `78f18d4c0c0acb7322a121dfa2851ac568cf5fbe28e7e1f4b5a780ad6e531bfc` |
