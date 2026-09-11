<!-- preserve: deep research TCC PNAAT -->
<!-- fonte: paste do assistente (fora do repo): paste_6_225558.txt -->
<!-- sha256_origem: 69ef2e6025a3c12a52ea335414358930f308b57084180266a2e80108ecb85887 -->
<!-- rodada: v5 — priorização de diferenciais (existe? viável? impacto na banca?) -->

## Priorização Geral

| Ideia | Existe na indústria? | Viabilidade 2 meses | Impacto na banca |
|---|---|---|---|
| 1. Medida dimensional explicável (tampa) | CONFIRMADO — prática padrão | FACTÍVEL | Alto |
| 3. Injeção de defeito sob demanda (golden sample) | CONFIRMADO — prática padrão de validação de AOI | FACTÍVEL | Alto |
| 4. Relatório de lote automático (PDF) | CONFIRMADO — prática comum de QA | FACTÍVEL | Médio-alto |
| 2. Marcação física do item rejeitado | CONFIRMADO (laser/inkjet industrial) — "caneta+servo" é analogia de baixo custo | PARCIAL | Médio-alto |
| 5. Espelho virtual da linha | CONFIRMADO (conceito de MES/HMI real-time) | PARCIAL | Médio |
| 6. Inspeção multimodal visão+som | CONFIRMADO (linha de pesquisa ativa) | PARCIAL/INVIÁVEL no prazo com qualidade | Médio (alto risco) |

## Ideia 1 — Medida Dimensional Explicável para Tampa Mal Rosqueada

**Existe na indústria?** Sim, e é exatamente como sistemas comerciais reais resolvem esse problema. A Cognex descreve textualmente que seus sistemas In-Sight usam detecção de borda para medir "a distância entre o topo da tampa e o gargalo da garrafa, bem como a posição horizontal do topo da tampa" para confirmar aperto correto, rejeitando garrafas fora do limite programável **[CONFIRMADO]**. A Sinowon confirma medição óptica de altura de tampa com precisão de até ±1μm em sistemas de metrologia dedicados (nível industrial de alta gama, não replicável no TCC, mas confirma que altura/geometria de tampa é a métrica-padrão do setor) **[CONFIRMADO]**. A Roder Vision detalha que **backlight (silhueta) é a técnica mais precisa para medir tilt e altura de tampa** justamente porque a posição da borda é determinada pelo contorno da silhueta, não pela reflectância da superfície — texto quase idêntico ao já recomendado na metodologia anterior deste projeto **[CONFIRMADO]**. Um exemplo de linha real (iFactory) usa duas estações com geometrias de luz opostas — backlight colimado para altura de líquido, dome difuso para ângulo de assentamento da tampa — com tolerância de ±0,5mm a 600 garrafas/min e "catch rate" de ~99,2% **[CONFIRMADO — caso aplicado real com números]**. Um artigo técnico de 2015 sobre sistema real da EPIC Systems descreve o uso de detecção de bordas e ROI (regiões de interesse) posicionadas ao redor de área de tampa/tamper band, medindo "distância do ombro da tampa até a banda de segurança" em linhas de até 900 unidades/minuto com 3 câmeras — arquitetura conceitualmente idêntica à do projeto (múltiplas vistas, medição geométrica por ROI) **[CONFIRMADO]**.[^1][^2][^3][^4][^5]

**Como implementar no contexto:** já com a calibração pixel→mm planejada na metodologia anterior, basta adicionar ao classificador de topo/lateral uma etapa de medição geométrica explícita: detectar a borda superior da tampa (via detecção de contorno simples, ex. Canny + contornos do OpenCV, já disponível e leve no Pi 5) e calcular a distância vertical entre essa borda e uma referência fixa do gargalo, convertendo pixels para mm pelo fator de calibração já definido. Comparar contra um threshold (ex. "tampa correta = folga entre X e Y mm"), combinando esse resultado com a saída do classificador ML como segunda camada de decisão. **Custo: zero** (é processamento de imagem adicional em software, sem hardware novo). **Esforço: baixo-médio**, cabe facilmente dentro do PoC 1 (topo) já planejado, adicionando 2-3 dias ao invés de reabrir cronograma.

**Classificação: FACTÍVEL. Risco técnico principal:** dependência de segmentação de borda limpa — mitigada pela iluminação backlight já recomendada. **Impacto na nota: Alto** — transforma "o modelo achou" em "medi 3,2mm de folga, threshold é 2-4mm", que é literalmente o formato de KPI exigido por U1 ("acurácia mínima X%" já é número; agora a decisão em si também é numérica e explicável, não uma caixa-preta). **Go recomendado.**[^3]

## Ideia 2 — Marcação Física do Item Rejeitado

**Existe na indústria?** Sim, mas em escala e tecnologia muito superior à proposta de "caneta+servo": laser marking e inkjet contínuo (CIJ) são os dois métodos-padrão da indústria de bebidas/alimentos para codificação permanente de lote/data/serial em garrafas, com laser sendo preferido quando a marca precisa resistir a limpeza/reuso e ser à prova de adulteração, e CIJ sendo preferido para linhas rápidas com superfícies curvas em movimento **[CONFIRMADO]**. A SCHOTT confirma códigos DataMatrix a laser de 1mm² aplicados unidade a unidade em frascos farmacêuticos, resistentes a autoclave até 600°C **[CONFIRMADO — caso extremo de rigor, fora de escala de TCC]**. A Wipotec opera um sistema real com 3 lasers e 3 câmeras de verificação para codificar QR series em garrafas PET na velocidade da sopradora, validando a marcação por imagem depois de marcar **[CONFIRMADO]** — este é o padrão real mais próximo conceitualmente do que a ideia propõe (marcar + verificar com câmera), mas a tecnologia usada (laser industrial) está muito acima do orçamento e da segurança operacional viável em bancada de TCC.[^6][^7][^8][^9]

**Como implementar no contexto (adaptação de baixo custo):** a "caneta montada em servo SG90" é tecnicamente viável como analogia funcional pobre da marcação industrial — um servo SG90 tem torque e precisão angular suficientes para um movimento simples de "abaixar caneta e tocar item parado", mas **carimbo/marcação por cor exige contato físico controlado e repetível**, que é sensível a folga mecânica, ressecamento de caneta e posicionamento exato do item — riscos de instabilidade mecânica exatamente do tipo que a apostila cita como "Efeito Demonstração". **Classificação: PARCIAL** — o princípio (evidência física + digital) é correto e citável (linha direta com a prática real de marcação+verificação por câmera), mas a implementação mecânica de precisão em 2 meses tem risco de instabilidade desproporcional ao ganho. **Recomendação de escopo:** substituir "caneta" por um mecanismo de menor risco mecânico — ex. o servo aciona uma bandeirola/marcador de cor fixado a uma haste que se sobrepõe visualmente ao item na esteira de saída de rejeitados (não risco de contato/mancha), ou simplesmente usar o LED RGB já no ponto de ejeção como "marcação luminosa" instantânea de severidade (vermelho=crítico, amarelo=major) fotografada como evidência — mantém o princípio de "evidência física simultânea ao registro digital" com risco mecânico próximo de zero. **Impacto na nota: Médio-alto** (ideia original) / **Alto** (versão adaptada de baixo risco). **Go condicional: com a adaptação de LED, não com caneta física.**[^9]

## Ideia 3 — Injeção de Defeito Sob Demanda (Golden Sample)

**Existe na indústria?** Sim — este é, de fato, um dos poucos princípios de validação de AOI/machine vision citados de forma consistente na literatura técnica consultada (guias de fabricantes como NI/Cognex tratam "test with known good/bad samples" como etapa obrigatória de setup antes de deploy). Um caso real de linha de inspeção documentado envolve treinamento e validação do sistema contra "valores conhecidos como bons" (known good values) por peça, comparando a imagem capturada contra a referência para decidir aceite/rejeição **[CONFIRMADO]**. Isso é conceitualmente idêntico ao princípio de golden sample da indústria de teste: manter amostras físicas com defeito conhecido e classificado, usadas para validar que o sistema continua detectando corretamente ao longo do tempo.[^10][^11]

**Como implementar no contexto:** já que o projeto usa peças impressas 3D com deformação controlada e fotografia própria de tampa (decisão já tomada), basta **rotular e reservar formalmente um pequeno conjunto dessas peças como "kit de amostras golden"** (ex. 1 peça OK, 1 tampa ausente, 1 tampa mal rosqueada, 1 deformidade leve, 1 deformidade severa) — sem necessidade de mecanismo de injeção automática complexo. Na demonstração, o operador simplesmente coloca a peça golden no trilho manualmente quando a banca solicitar "mostre um defeito", e o sistema detecta/ejeta/registra em tempo real. **Custo: zero** (reutiliza peças já produzidas para o dataset). **Esforço: baixíssimo** — é uma prática de organização/documentação, não uma feature de engenharia nova.

**Classificação: FACTÍVEL, esforço mínimo. Risco técnico:** nenhum risco novo — usa componentes já validados nos PoCs 1 e 2. **Impacto na nota: Alto** — resolve diretamente o maior risco da apostila ("Efeito Demonstração"), pois dá ao apresentador controle total sobre o momento crítico da demo, em vez de depender de sorte para um item real passar com defeito durante a janela de tempo da banca. **Go recomendado — prioridade máxima de implementação por ser praticamente gratuito.**

## Ideia 4 — Relatório de Lote Automático

**Existe na indústria?** Sim, é prática padrão de controle de qualidade — a geração de relatórios de lote (batch reports) com estatísticas de defeito, comparação histórica e evidência fotográfica é o formato esperado por gestores de qualidade em qualquer linha com inspeção automatizada, conforme confirmado no caso da Corpex, que descreve que "cada resultado é registrado, criando um registro digital rastreável para análise e garantia de qualidade" **[CONFIRMADO]**.[^12]

**Como implementar no contexto:** WeasyPrint (conversão HTML→PDF via Jinja2) é confirmado como a opção mais simples e rápida de implementar para relatórios com tabelas e gráficos incorporados, exigindo poucas dependências e sendo adequado a relatórios templatizados **[CONFIRMADO — comparação direta de bibliotecas]**; ReportLab é a alternativa para controle de layout mais preciso, mas com curva de aprendizado maior **[CONFIRMADO]**. Para o volume de dados deste projeto, a recomendação é WeasyPrint: um template HTML simples (tabela de KPIs do lote, gráfico de distribuição de defeito por severidade gerado com matplotlib e embutido como imagem, 3-5 fotos de evidência de itens defeituosos) renderizado a partir dos dados já persistidos no SQLite ao fim de cada lote (ex. 50 itens), disparado automaticamente e enviado via ntfy (já confirmado como infra existente) como anexo ou link.[^13][^14]

**Classificação: FACTÍVEL. Esforço:** baixo-médio, ~2-3 dias de implementação, perfeitamente encaixável na semana de polimento final (semana 7-8) sem tocar o núcleo já congelado. **Risco técnico:** mínimo — é uma camada de apresentação sobre dados já coletados, não uma nova fonte de risco funcional. **Impacto na nota: Médio-alto** — reforça diretamente o critério de "documentação como produto" (U3) e dá à banca um artefato tangível e profissional para folhear, além de reforçar a tradução para linguagem de gestão de qualidade já recomendada (FPY/PPM) com evidência concreta em PDF. **Go recomendado.**

## Ideia 5 — Espelho Virtual da Linha (Réplica Animada em Tempo Real)

**Existe na indústria?** O conceito de HMI/dashboard de linha em tempo real é padrão em MES real, mas "réplica virtual sincronizada item a item" na literatura de nível industrial normalmente é chamado de digital twin — tecnologia legítima, mas de escopo tipicamente muito maior que uma tela reativa. A busca não retornou um caso de "espelho leve" equivalente ao proposto aqui em ferramentas como Grafana com stream via WebSocket — a comunidade Grafana confirma suporte a "Live Measurement"/streaming via Telegraf, mas para métricas numéricas em tempo real, não para animação de objetos posicionados espacialmente **[CONFIRMADO — funcionalidade existe, mas não é o padrão de uso descrito]**.[^15]

**Como implementar no contexto (versão viável, não digital twin completo):** em vez de uma "réplica animada" fiel (que exigiria motor de renderização e sincronismo fino de posição, aproximando-se de digital twin real), a versão de custo/risco compatível com 2 meses é uma **visualização simplificada tipo "trilha de itens"**: uma página web leve (framework tipo Dash/Streamlit, consumindo dados via MQTT/websocket do hub) mostrando uma linha horizontal com marcadores representando itens recentes, coloridos por status (verde=ok, vermelho/amarelo=defeito por severidade), avançando conforme novos eventos chegam — não uma simulação física da posição real do encoder, mas uma representação em tempo real do fluxo de itens e decisões. Isso entrega a mesma sensação de "linha viva" para a banca sem o risco de sincronismo fino entre posição real do encoder e posição de um objeto virtual renderizado.

**Classificação: PARCIAL** — a versão "espelho fiel" (posição do encoder → posição virtual exata) é desproporcional ao ganho e arrisca instabilidade adicional (mais uma camada de sincronismo em tempo real, competindo por atenção de desenvolvimento com o núcleo já crítico); a versão simplificada de "trilha de itens com status" é FACTÍVEL e entrega grande parte do valor visual. **Risco técnico:** médio na versão fiel (esforço de engenharia de sincronismo adicional que pode empurrar prazo); baixo na versão simplificada. **Impacto na nota: Médio** (a versão simplificada já é essencialmente o "dashboard vivo" já recomendado na análise anterior — não é um diferencial totalmente novo, é uma variação de apresentação do mesmo dashboard). **Go condicional: versão simplificada sim, réplica fiel com sincronismo de posição não.**

## Ideia 6 — Inspeção Multimodal: Visão + Som

**Existe na indústria/pesquisa?** Sim, como linha de pesquisa ativa e não como prática comercial madura para este caso específico. Detecção de anomalia acústica é bem estabelecida para monitoramento de máquinas rotativas (rolamentos, motores) usando autoencoders e espectrogramas Mel — mas todos os casos de referência encontrados são sobre som da **máquina** (vibração/motor), não do **produto** passando por ela **[CONFIRMADO]**. O dataset MIMII, referência padrão da área, é especificamente sobre sons de máquinas industriais malfuncionando (bombas, ventiladores, válvulas), não sons de produto **[CONFIRMADO]**. Um pipeline de TinyML para classificação binária de som anômalo usando MFCC + rede leve quantizada TFLite Micro atinge 91% de acurácia em dataset de sons urbanos (UrbanSound8K) **[CONFIRMADO — mas domínio de aplicação é ambiente urbano, não inspeção de produto]**.[^16][^17][^18][^19]

**Avaliação crítica para o caso específico do projeto:** nenhuma fonte encontrada confirma ou nega que uma garrafa com tampa mal rosqueada produza assinatura acústica mensurável e distinguível ao passar/impactar em velocidade de bancada — essa é uma hipótese de física de produto não testada na literatura consultada **[SPECULATIVE quanto à existência de sinal acústico distinguível para este defeito específico]**. Mesmo que o sinal exista, o microfone do BitDogLab (RP2040) exigiria captura de áudio, extração de features (MFCC/espectrograma) e inferência de um classificador leve — pipeline tecnicamente possível em microcontrolador segundo a literatura de TinyML acústico, mas isso é um projeto de engenharia paralelo inteiro (captura, dataset de áudio próprio a ser coletado do zero, treinamento, quantização, validação), competindo diretamente pelo tempo já apertado do núcleo de visão.[^19]

**Classificação: PARCIAL/INVIÁVEL com qualidade dentro do prazo** — o esforço de validar a própria hipótese (existe sinal acústico?) já consumiria uma fração relevante do tempo disponível, com risco real de retornar "não há sinal distinguível" depois de gastar 1-2 semanas, ferindo o congelamento da semana 5. **Risco técnico principal:** validação de hipótese física não confirmada + pipeline de ML paralelo completo. **Impacto na nota: Médio, mas com risco alto de consumir tempo sem entregar valor**. **Recomendação: No-go para implementação completa. Alternativa de baixo risco:** citar a linha de pesquisa (fusão visão+áudio para inspeção industrial) na fundamentação teórica como extensão futura tecnicamente informada, e opcionalmente rodar um teste exploratório de 1-2 dias (não uma PoC formal do plano de 6) apenas para registrar no repositório se há ou não sinal perceptível — se houver indício forte, promover a extensão pós-defesa; se não, documentar como hipótese testada e descartada (mesmo valor de rigor documental que a análise negativa de Re-ID já recomendada).

## Priorização Final e Combo Recomendado

| Ranking | Ideia | Racional |
|---|---|---|
| 1 | Ideia 3 — Golden samples | Impacto altíssimo, custo zero, resolve diretamente o maior risco da apostila (Efeito Demonstração) |
| 2 | Ideia 1 — Medida dimensional explicável | Alto impacto, alinhado a como a indústria real resolve exatamente este defeito[^4][^3][^2], baixo custo/esforço |
| 3 | Ideia 4 — Relatório de lote em PDF | Médio-alto impacto, baixo esforço, reforça U3 com artefato tangível |
| 4 | Ideia 2 (versão adaptada com LED) — Marcação por cor | Médio-alto impacto na versão de baixo risco, zero custo adicional |

**Combo recomendado: Ideias 3 + 1 + 4 + versão adaptada de 2.** Nenhuma delas compete por tempo com o núcleo do plano de 6 PoCs já congelado — são complementos de baixo esforço que podem ser paralelizados nas semanas 6-8 (documentação/polimento) sem risco ao cronograma. Ideia 5 (versão simplificada) pode ser incorporada ao dashboard já planejado como refinamento de apresentação, não como item separado. Ideia 6 fica como nota de rodapé teórica, não implementação.

## Ideias Adicionais Encontradas na Pesquisa

- **Verificação por câmera da própria marcação/evidência (double-check), como no caso real da Wipotec:** aplicado à versão adaptada da Ideia 2, uma segunda captura confirmando que o LED de severidade realmente acendeu na cor esperada antes de fechar o registro do evento — reforça resiliência (U4) com esforço mínimo.[^9]
- **Duas geometrias de luz por estação, como no caso real da iFactory:** já implícito na metodologia anterior (backlight/dark field por vista), mas vale registrar explicitamente no repositório a analogia direta com um caso comercial documentado — fortalece a fundamentação teórica com exemplo real citável.[^2]
- **Comparação com lote anterior no relatório automático (Ideia 4):** adicionar ao PDF gerado uma linha de tendência simples (taxa de defeito do lote atual vs média dos lotes anteriores) — trivial de calcular a partir do schema já proposto, e transforma o relatório de "foto do momento" em "sinal de tendência", que é exatamente o tipo de insight que SPC industrial busca entregar sem implementar SPC formal completo.

## O Que Não Fazer

- **Laser marking ou CIJ real:** tecnologia correta da indústria, mas totalmente fora de orçamento, segurança e escopo de 2 meses — citar como referência teórica no repositório, nunca tentar implementar ou simular com equivalente de risco (ex. ferro de solda, X-Acto) que introduziria risco de segurança na demonstração.[^8][^6]
- **Réplica virtual fiel com sincronismo de posição do encoder (versão completa da Ideia 5):** um verdadeiro digital twin com posição espacial sincronizada é over-engineering — a versão simplificada de "trilha de status" já entrega o essencial do valor de apresentação.
- **Pipeline completo de áudio (Ideia 6) sem validação prévia de hipótese:** implementar captura + dataset + treino + quantização de modelo acústico antes de confirmar que existe sinal distinguível é o tipo de aposta de alto risco que pode consumir semanas sem retorno, ameaçando o congelamento da semana 5.
- **Mecanismo de marcação por contato físico (caneta original da Ideia 2) sem mitigação:** risco mecânico desproporcional ao ganho — qualquer solução que dependa de contato físico preciso e repetível com o item deve ser tratada com o mesmo rigor de teste de estresse já exigido para os demais componentes do rig, e só deve seguir adiante se testes preliminares (fora do plano de 6 PoCs, não bloqueantes) confirmarem repetibilidade alta.
- **SPC formal completo para o relatório de lote (Ideia 4):** cartas de controle estatístico exigem histórico e tamanho de amostra maiores do que o projeto vai gerar em 2 meses — a comparação simples de tendência entre lotes (sugerida como ideia adicional) já entrega o princípio sem o overhead metodológico.

---

## References

1. [Precision Optical Measurement Solutions for Bottle Cap Inspection - Sinowon Vision Measuring Machines](https://www.sinowon.com/sinowon-vision-measuring-systems-optical-precision-in-bottle-cap-dimension-inspection.html) - Discover how Sinowon's OMM technology and video measuring systems ensure ±1μm accuracy in geometric ...

2. [Pilot Scoping](https://ifactoryapp.com/blog/ai-vision-fill-level-inspection-food-beverage) - Guarantee fill accuracy with iFactory AI vision — underfill, overfill, missing caps and label defect...

3. [Precision Bottle Cap Inspection](https://rodervision.com/vision-systems-for-industrial-application/precision-bottle-cap-inspection-machine-vision-led-lighting-solutions/) - LED illumination for bottle cap inspection: presence detection, alignment, tamper evidence, colour v...

4. [Bottle Cap Inspection - Food & Beverage](https://www.cognex.com/en-au/industries/food-and-beverage/assembly-verification/cap-height-and-skew-inspection) - Detect bottle cap placement issues and help prevent spillage by inspecting each food and beverage ca...

5. [Industrial Inspection: Smart cameras check bottles at high- ...](https://www.vision-systems.com/factory/article/16738272/industrial-inspection-smart-cameras-check-bottles-at-high-speed) - EPIC Systems developed a vision system that uses smart cameras to inspect 6oz plastic bottles of fru...

6. [Laser Marking vs Inkjet Printing: Traceability Guide](https://www.lumenfuture.sg/laser-marking-vs-inkjet-printing/) - Compare laser marking and industrial inkjet printing for traceability, including durability, code qu...

7. [Laser marking - SCHOTT](https://www.schott.com/en-gb/expertise/technology-and-processing/laser-marking) - Discover how to identify, evaluate and monitor your pharmaceutical packaging throughout the producti...

8. [CODING AND MARKING](https://www.linxglobal.com/wp-content/uploads/2023/06/linx-beverages-white-paper-web.pdf)

9. [Laser coding bottles](https://www.wipotec.com/en/track-trace/laser-marking-bottles)

10. [System checks plastic molding consistency](https://www.vision-systems.com/factory/consumer-packaged-goods/article/16738898/system-checks-plastic-molding-consistency) - A combination of off-the-shelf hardware and software allows plastic containers to be inspected consi...

11. [Vision system inspects bottle caps at high speed](https://www.vision-systems.com/cameras-accessories/article/16737324/vision-system-inspects-bottle-caps-at-high-speed) - Custom LED lighting combined with off-the-shelf cameras, software and a patented separator conveyor ...

12. [Bottle Inspection System](https://www.corpex.biz/bottle-inspection-system/) - CORPEX Bottle Inspection System uses AI and vision to detect cap, label, and fill-level defects in r...

13. [Python PDF Generation: ReportLab and WeasyPrint - Techoral](https://techoral.com/python/pdf-generation.html) - Generate PDFs in Python with ReportLab for programmatic control and WeasyPrint for HTML-to-PDF conve...

14. [Generate PDFs in Python: WeasyPrint vs ReportLab - DEV Community](https://dev.to/claudeprime/generate-pdfs-in-python-weasyprint-vs-reportlab-ifi) - A comparison of PDF generation libraries in Python with code examples for common use cases.

15. [Grafana Dashboard For Live Data](https://community.grafana.com/t/grafana-dashboard-for-live-data/134899) - Hi, I am using Grafana version 10.2.2 (Windows OSS). I have a question: can I use the WebSocket API ...

16. [Deploying Real-Time Vibration & Audio Anomaly Detection on ...](https://www.adaptnxt.com/blogs/edge-anomaly-detection-tinyml-jetson-orin) - Running machine learning models directly on the shop floor enables sub-millisecond anomaly detection...

17. [Acoustic Anomaly Detection for Machine Sounds based on ...](https://www.scitepress.org/Papers/2021/101858/101858.pdf)

18. [Assignment TinyML Devansh Sahney_231230020 | PDF - Scribd](https://www.scribd.com/document/998147705/Assignment-TinyML-Devansh-Sahney-231230020) - The document presents a report on the MIMII Dataset, which is designed for Unsupervised Anomaly Dete...

19. [TinyML for Acoustic Anomaly Detection in IoT Sensor ...](https://arxiv.org/html/2603.26135v1)

