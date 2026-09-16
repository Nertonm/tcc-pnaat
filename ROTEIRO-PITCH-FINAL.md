# Entrega 5 — plano e roteiro do vídeo pitch com demo

Este documento adapta o roteiro técnico das PoCs para a **apresentação final de até 15 minutos**.
Ele foi escrito a partir da rubrica fornecida para a Entrega 5 e do estado versionado deste
repositório. O objetivo não é apenas produzir um vídeo bonito: é deixar visíveis, na mesma
narrativa, o problema, a função dos elementos tecnológicos, a sequência de funcionamento e o
resultado do protótipo.

## 1. Veredito sobre o plano da equipe

Com o esclarecimento de que cada fotografia será relacionada à função do componente e de que os
vídeos mostram a cadeia física funcionando até o site, o dashboard e o Grafana, o plano é **válido e
suficiente para disputar a nota máxima da rubrica apresentada**. A sequência cobre problema,
elementos tecnológicos, funcionamento e resultado — exatamente os artefatos solicitados.

O único sentido em que não é possível “garantir” a nota é literal: a banca também julgará execução,
clareza, tempo e se aquilo que é narrado fica comprovado na tela. Isso não significa que o formato
de fotos esteja errado. Fotos comentadas são apropriadas para explicar componentes que não precisam
estar em movimento; a demonstração em vídeo é que deve provar a operação integrada.

Ainda há quatro riscos de execução a controlar:

1. uma montagem longa de fotos, repositório e código pode parecer documentação, não funcionamento;
2. vídeos separados podem esconder a relação causal entre garrafa, sensor, captura, inferência e
   resultado no painel;
3. a filmagem de uma indústria genérica não prova o cenário real do protótipo da equipe;
4. algumas integrações narradas pela equipe ainda aparecem como pendentes no código/documento
   versionado, portanto a fala pode prometer mais do que o repositório prova.

Controlados esses riscos, o plano fica **fortemente alinhado ao nível avançado**: apresentação clara,
fluida e profissional, dentro do tempo, demo irrefutável e cenário real de bancada que represente a
linha industrial.

### Como usar as fotos sem perder pontos

A ideia proposta pela equipe — mostrar o sensor fotoelétrico enquanto se explica sua participação,
por exemplo — é uma boa escolha didática. Aplicar a mesma fórmula a cada imagem:

1. **nome:** “Este é o sensor fotoelétrico”;
2. **função:** “Ele detecta a passagem da garrafa”;
3. **relação com o fluxo:** “Esse evento inicia a janela de captura”;
4. **evidência posterior:** “Na demo, observem este indicador mudar quando a garrafa passar”.

Cada foto deve responder “o que é?”, “por que existe?” e “onde aparecerá funcionando?”. Usar setas,
legendas e destaque visual. Para evitar que a introdução pareça um catálogo, limitar esse bloco a
aproximadamente 60–90 segundos e agrupar os elementos por função:

- **entrada física:** esteira, garrafa e sensor;
- **captura:** câmeras, iluminação e estrutura;
- **processamento:** ESP/controlador e Raspberry Pi, respeitando a função real de cada um;
- **software:** dataset, inferência, persistência, site/dashboard e Grafana.

Fotografias de códigos e do repositório também podem aparecer, mas como confirmação rápida da
implementação, não como atração principal. Para código, preferir um trecho legível que represente a
regra narrada; para o dataset, mostrar exemplos rotulados; para o repositório, mostrar a organização
dos módulos. Em seguida, a demonstração deve recuperar esses elementos em movimento.

### Mudança central

Estruturar as fotos e os vídeos como capítulos de uma mesma história de um item rastreável:

```text
garrafa identificada
  -> cruza o sensor
  -> abre a janela de captura
  -> câmeras produzem imagens
  -> Raspberry executa a decisão
  -> resultado recebe o mesmo ID
  -> dashboard e Grafana exibem esse evento
```

A demonstração deve ocupar a maior parte do vídeo. Arquitetura, código, dataset e repositório entram
somente para explicar **como** o resultado que acabou de ser visto foi produzido.

## 2. O que é necessário para buscar o nível avançado

| Exigência da entrega/rubrica | Evidência que precisa aparecer no vídeo |
|---|---|
| problema compreensível | impacto da inspeção manual e os defeitos-alvo: tampa ausente, tampa mal rosqueada e deformidade |
| função dos elementos | legenda sobre sensor, ESP, câmeras, Raspberry, modelo, banco, dashboard e Grafana |
| sequência de funcionamento | uma animação curta e, principalmente, uma passagem acompanhada de ponta a ponta |
| protótipo completo | plano aberto do rig/esteira e detalhe dos componentes realmente utilizados |
| função prevista em execução | garrafa real passa; sensor muda; imagem é capturada; decisão é gerada |
| resultado relacionado ao problema | normal e defeito aparecem com ID, classe, horário e evidência visual |
| cenário real/simulado robusto | bancada com iluminação e condições controladas, sem fingir que é uma fábrica real |
| integração hardware/software/IA | tela dividida ou edição sincronizada ligando evento físico, log e painel |
| clareza e profissionalismo | áudio limpo, textos grandes, cortes identificados e duração alvo de 10 a 12 minutos |

“Robustez” não é mostrar muitos produtos de software. É demonstrar casos relevantes e comprovar que
o resultado pertence ao mesmo item físico. O conjunto mínimo recomendado é:

- uma garrafa normal;
- uma com tampa ausente;
- uma com tampa mal rosqueada;
- uma com deformidade visível, se essa classe estiver realmente conectada ao modelo demonstrado;
- opcionalmente, um caso de captura ruim ou falha, encerrado como `inconclusivo`, para mostrar que o
  sistema não aprova silenciosamente quando não há evidência suficiente.

Se uma classe ainda não estiver integrada, não encenar sua detecção: retire o caso da demo e diga
que ele é uma extensão/validação futura.

## 3. Roteiro recomendado — 10 a 12 minutos

Os tempos deixam margem suficiente abaixo dos 15 minutos. As falas entre aspas podem ser usadas
quase literalmente, mas devem soar naturais e não ser lidas depressa.

### 0:00–0:20 — abertura forte

**Imagem:** em vez de começar por nomes, mostrar por 2–3 segundos uma garrafa defeituosa passando
e o painel acusando o defeito. Depois, título do projeto e nomes da equipe.

**Fala:**

> “Em uma linha de envase, uma tampa ausente, mal rosqueada ou uma deformidade pode passar em
> segundos e chegar ao consumidor. Nosso projeto transforma cada passagem em uma inspeção visual
> rastreável, conectando sensor, captura, processamento e acompanhamento em tempo real.”

### 0:20–1:20 — problema e contexto

**Imagem:** até 10–15 segundos de uma linha industrial devidamente licenciada, seguida rapidamente
pelo cenário real da equipe. Destacar velocidade, repetição e dificuldade da inspeção contínua.

**Fala:**

> “Em linhas com alto fluxo, depender apenas da inspeção humana torna difícil observar todas as
> unidades com o mesmo critério e manter evidências de cada decisão. O problema que atacamos é a
> identificação rastreável de anomalias de tampa e corpo. O vídeo industrial ilustra o contexto;
> nossa validação acontece neste cenário de bancada, que reproduz a passagem, o disparo e a captura.”

Não afirmar custos, percentuais de perda, acurácia ou velocidade industrial sem uma fonte ou uma
medição do projeto na tela. Se forem usados números, colocar fonte e ano em texto legível.

### 1:20–2:15 — proposta de valor e arquitetura

**Imagem:** diagrama animado simples com oito blocos no máximo. Iluminar um bloco por vez.

**Fala:**

> “Quando a garrafa interrompe o sensor fotoelétrico, o controlador registra o disparo e inicia a
> janela de captura. As câmeras geram as vistas do mesmo item. No Raspberry Pi, o pipeline valida a
> captura, executa a classificação por domínio e combina as evidências. O evento recebe identidade,
> horário, origem, decisão e evidências. O dashboard mostra o item ao operador; o Grafana apresenta
> a visão histórica e operacional.”

Usar “após a janela/atraso calibrado” no lugar de “após um delay determinado”. Exibir na tela o valor
medido usado na tomada. Isso demonstra engenharia; “delay” sem justificativa parece improviso.

### 2:15–3:10 — protótipo físico e papel de cada peça

**Imagem:** plano geral estável e closes curtos. Inserir setas/legendas, não apenas fotografias.

**Fala:**

> “Aqui está o protótipo completo. A esteira reproduz o deslocamento; o sensor detecta a passagem;
> o controlador trata o gatilho; estas câmeras registram as vistas; a iluminação reduz variações; e
> o Raspberry concentra processamento, decisão e envio dos resultados. Cada componente tem uma
> função observável na demonstração a seguir.”

Mostrar também limitações físicas relevantes: proteção elétrica, fixação, iluminação e posição das
câmeras. Não chamar uma placa de “Raspberry” ou “ESP” de forma genérica: colocar modelo e função em
legenda. Não dizer que o ESP classifica; no desenho versionado, a decisão pertence ao Pi.

### 3:10–3:50 — IA, dados e software sem virar tour de código

**Imagem:** quatro quadros rápidos: amostras rotuladas do dataset, transformação/ROI, saída do modelo
e evento persistido. O repositório pode aparecer por poucos segundos com os módulos destacados.

**Fala:**

> “As imagens são organizadas por classe e usadas no treinamento e na validação. Na execução, a
> imagem passa pelos controles de qualidade e pelo classificador. A decisão é separada por domínio:
> tampa e corpo. Evidência insuficiente não vira aprovação; o resultado é inconclusivo. Por fim, o
> sistema registra o evento de forma rastreável para consulta.”

Não rolar arquivos de código. Se um trecho for indispensável, mostrar no máximo 8–12 linhas, com
zoom, por 5–8 segundos, e explicar a regra de negócio — por exemplo, “qualquer defeito decisório
reprova; ausência de evidência torna o resultado inconclusivo”. GitHub prova organização, não prova
operação. Informar número de imagens, divisão treino/validação/teste e métricas **somente** se esses
valores tiverem sido medidos e puderem ser apresentados.

### 3:50–7:30 — demo principal, contínua e rastreável

Esta é a parte decisiva. Usar tela dividida ou sincronizar três fontes com relógio comum:

1. plano da garrafa e do sensor;
2. log/indicador do trigger e da inferência;
3. dashboard filtrado pelo item.

Antes da primeira passagem, filmar uma claquete simples: commit, data, configuração e identificador
do ensaio. Limpar ou filtrar eventos antigos e mostrar o contador inicial. Para cada caso:

1. exibir o rótulo conhecido da garrafa **antes** da inferência, sem revelar apenas depois do erro;
2. mostrar a garrafa inteira e o marcador físico/ID;
3. realizar a passagem sem corte no trecho causal;
4. realçar a mudança de estado do sensor;
5. mostrar captura e inferência;
6. localizar no dashboard o mesmo ID, horário, classe e imagem;
7. comparar predição e rótulo conhecido em uma sobreposição: `esperado` versus `obtido`.

**Fala da primeira passagem:**

> “Este é o item [ID], previamente marcado como [rótulo conhecido]. A garrafa cruza agora o sensor.
> O sinal abre a janela de captura; observem o mesmo ID no log. As imagens foram recebidas e o
> pipeline produziu [resultado]. No dashboard, o evento [ID] contém horário, decisão e evidência da
> captura. Portanto, este resultado pertence à garrafa que acabamos de acompanhar.”

**Fala nas passagens seguintes:**

> “Repetimos o mesmo fluxo com [defeito]. O esperado é [classe]. O sensor dispara, as imagens são
> processadas e o item [ID] aparece como [resultado].”

É melhor mostrar três casos muito claros do que oito passagens aceleradas. Não cortar entre sensor e
resultado. Se a inferência demora, manter um cronômetro ou log visível e acelerar apenas uma cópia
posterior claramente marcada como “trecho acelerado”; preservar ao menos uma execução em tempo real.

### 7:30–8:35 — dashboard e Grafana

**Imagem:** começar no registro gerado na demo, não em dados simulados ou antigos. Navegar apenas
por telas que respondam a perguntas operacionais.

**Fala:**

> “O dashboard operacional permite consultar o item e sua evidência. Aqui filtramos o ID da demo e
> vemos a classe, o horário e a imagem. No Grafana, os eventos persistidos são agregados por período,
> permitindo acompanhar volume, defeitos, inconclusivos e saúde do sistema. O painel não realiza a
> classificação; ele torna os resultados consultáveis.”

Mostrar a fonte de dados e atualizar o painel após a passagem. Se o Grafana usa dados simulados,
rotular explicitamente “dados simulados” e apresentá-lo como visualização futura, não como evidência
da execução. Não somar `inconclusivo` a aprovado.

### 8:35–9:20 — resultado quantitativo honesto

**Imagem:** tabela curta com quantidade por classe, acertos/erros e latência, se essas medições
existirem. Diferenciar “resultado desta demo” de “avaliação do modelo”.

**Fala:**

> “Nesta demonstração executamos [N] passagens, com [resultados observados]. Este número demonstra o
> funcionamento integrado, mas não substitui uma avaliação estatística. Na base separada de teste,
> quando aplicável, obtivemos [métricas verificáveis].”

Uma sequência de poucos acertos não autoriza dizer “100% de precisão”. Para alegar desempenho do
modelo, mostrar matriz de confusão, tamanho do conjunto de teste, separação dos dados e, idealmente,
intervalo de confiança. Caso isso não esteja pronto, omitir a alegação e focar na integração.

### 9:20–10:10 — diferenciais e limites

**Imagem:** lista lado a lado “comprovado nesta execução” e “próximas validações”.

**Fala:**

> “A entrega comprovada é o encadeamento entre passagem física, captura, decisão e rastreabilidade
> por item. O sistema também evita aprovação silenciosa quando falta evidência. Como próximos passos,
> vamos ampliar a validação com mais amostras e condições de iluminação, medir desempenho contínuo
> na velocidade-alvo e concluir as integrações que ainda não estiverem presentes nesta versão.”

Limitações bem delimitadas aumentam a credibilidade. Elas não devem dominar o final nem contradizer
o que foi mostrado.

### 10:10–10:50 — conclusão com integrante em quadro

**Imagem:** integrante ao lado do protótipo, e não diante de uma parede neutra. Encerrar com uma
última visão do dashboard e do rig.

**Fala:**

> “Partimos de um problema concreto de inspeção em linhas de envase e construímos um protótipo que
> acompanha a garrafa desde o sensor até o resultado. A demonstração mostrou hardware, software e
> processamento trabalhando de forma integrada, com uma decisão associada à evidência do mesmo
> item. Assim, entregamos uma base rastreável para tornar a inspeção mais consistente e mensurável.
> Obrigado.”

## 4. Ajustes específicos ao plano original

### Manter

- vídeo industrial curto como contextualização;
- narração sobre imagens, desde que o áudio seja limpo e as imagens correspondam à fala;
- imagens da estrutura física, sensores, dataset e arquitetura;
- casos normais e defeituosos na esteira;
- dashboard e Grafana;
- conclusão presencial com integrante da equipe.

### Alterar

- trocar a sequência longa de fotos/código por um diagrama e poucos recortes funcionais;
- colocar o protótipo real logo após o contexto industrial;
- apresentar a verdade conhecida de cada garrafa antes da passagem;
- manter sensor, log e resultado visíveis/sincronizados;
- provar a ligação pelo mesmo `item_id` e timestamp;
- separar claramente classificação operacional, visualização no dashboard e observabilidade no
  Grafana;
- falar “cenário de bancada que representa a linha” em vez de sugerir implantação industrial real;
- usar a conclusão para sintetizar problema, prova e valor, não para introduzir novas funções.

### Evitar

- banco de imagens com defeito “perfeito” e sem licença/origem;
- efeitos, música ou transições que escondam o fluxo do protótipo;
- telas ilegíveis do VS Code/GitHub;
- resultados preparados no dashboard sem mostrar que nasceram daquela passagem;
- chamar fotos do dataset de demonstração do sistema;
- dizer “tempo real”, “alta eficiência”, “preciso” ou “robusto” sem números medidos;
- atribuir ao sistema uma rejeição física automática se ele apenas detecta/registra;
- esconder falha ou refazer a fala como se a tomada tivesse sido contínua.

## 5. Auditoria entre a fala e o repositório

Antes de gravar, a equipe precisa resolver esta diferença: os vídeos relatados podem comprovar uma
integração física mais nova, mas o estado versionado ainda descreve partes dela como pendentes.

### O que o código versionado sustenta

- contrato tipado para tampa, corpo, classes, evidência, origem e qualidade;
- associação das vistas `topo`, `lateral1` e `lateral2` a um mesmo item;
- regra fail-closed: evidência ausente/ruim leva a `inconclusivo`;
- classificação nas laterais e check auxiliar no topo;
- conformidade por domínio, sem votação que apague um defeito;
- persistência SQLite idempotente e consultas analíticas para painel;
- firmware/receptor de captura com validação de tamanho, sequência e CRC;
- testes automatizados dessas regras.

### O que não deve ser afirmado apenas com base neste commit

- integração completa do trigger físico E18-D80NK com a pipeline do Pi;
- câmeras, inferência, registro, dashboard e Grafana conectados numa única execução de produção;
- acurácia industrial das três classes;
- processamento sustentado na velocidade de uma linha industrial;
- atuação física de rejeição da garrafa;
- que o Grafana está configurado neste repositório — não há configuração versionada identificável.

Se os vídeos realmente mostram a cadeia completa, versionar antes da entrega o código/configuração
correspondente e gravar o hash do commit na claquete. Caso a gravação combine subsistemas distintos,
usar “demonstração composta” e identificar os cortes; não chamar de execução ponta a ponta.

## 6. Plano de gravação e edição

### Captação mínima

- câmera A: plano geral fixo da esteira, sensor e garrafa;
- câmera B: close opcional do sensor/câmeras;
- captura de tela: log e dashboard em 1080p, zoom de 125–150%;
- gravação do Grafana com o intervalo temporal já ajustado;
- microfone próximo, ambiente silencioso e teste de pico antes da tomada;
- palmas/claquete e relógio visível para sincronizar vídeo físico e tela.

### Identidade visual

- uma cor para entrada, outra para processamento e outra para resultado;
- legendas persistentes com nomes corretos dos componentes;
- fonte grande e alto contraste;
- selo discreto: `CONTEXTO INDUSTRIAL`, `CENÁRIO DE BANCADA`, `EXECUÇÃO EM TEMPO REAL` ou
  `DADOS SIMULADOS`, conforme o caso;
- música apenas na abertura/fechamento e bem abaixo da voz.

### Plano B sem enfraquecer a prova

Gravar uma tomada contínua limpa de cada caso antes de editar. Se dashboard/Grafana falhar durante a
captação, preservar o vídeo da falha e refazer a tomada inteira. Não inserir resultado de outra
garrafa. Guardar os arquivos brutos, o banco e as imagens associados aos IDs exibidos.

## 7. Checklist final de nota máxima

### Conteúdo e prova

- [ ] problema, público e consequência estão claros em menos de um minuto;
- [ ] defeitos-alvo são nomeados sem exagerar o escopo;
- [ ] protótipo completo aparece em plano aberto;
- [ ] função de cada componente é explicada;
- [ ] ao menos uma passagem é mostrada sem corte, em tempo real;
- [ ] cada caso tem rótulo esperado declarado antes da execução;
- [ ] o mesmo ID liga garrafa, log, imagem, decisão e painel;
- [ ] há ao menos um caso normal e casos defeituosos realmente suportados;
- [ ] dashboard usa dados da própria demo;
- [ ] Grafana tem fonte/período identificáveis ou está marcado como simulação;
- [ ] resultado observado é comparado ao esperado;
- [ ] limitações são honestas e não contradizem a demonstração;
- [ ] a conclusão retoma problema, prova e valor.

### Qualidade audiovisual

- [ ] duração medida fica entre 10 e 12 minutos e nunca ultrapassa 15;
- [ ] voz está clara, sem clipping, eco excessivo ou música competindo;
- [ ] textos permanecem legíveis em tela de notebook/celular;
- [ ] não há dados pessoais, senhas, tokens, IP público ou abas irrelevantes;
- [ ] mídia externa tem licença/crédito e aparece apenas brevemente;
- [ ] cada corte ou aceleração relevante é sinalizado;
- [ ] todos os integrantes são identificados;
- [ ] o vídeo final foi assistido inteiro por alguém que não desenvolveu o sistema;
- [ ] link final foi testado em janela anônima e tem permissão correta.

## 8. Regra de decisão antes de publicar

Assistir ao vídeo sem áudio. Deve ser possível apontar onde a garrafa entra e onde o resultado dela
aparece. Depois, ouvir sem imagem. Deve ser possível entender problema, solução, funcionamento,
resultado e limite. Por fim, conferir quadro a quadro os IDs da demo. Se essas três verificações
passarem e o vídeo ficar dentro do tempo, a apresentação terá evidência muito mais forte para o
nível avançado do que uma sequência de slides, fotos e telas independentes.
