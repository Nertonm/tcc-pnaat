# Conjunto de dados: composição, captura, anotação e síntese de defeito

Este diretório não é uma pasta de imagens. É o **ciclo** que produz o dado do projeto:

```
captura própria  ->  anotação humana  ->  conjunto de treino  ->  modelo  ->  medição
       ^                          |                                             |
       |                          v                                             |
       +------  síntese de defeito (pares validados)  ----  o erro diz o que capturar
```

O diagnóstico medido em 2026-09-14 é o que organiza tudo aqui: **o gargalo não é compute, é
anotação e disciplina de dados**. Extrair 15,5 mil recortes com DINOv2-S leva 73 s; a decomposição
SVD de 12.368x576 leva 0,9 s; retreinar o detector de tampa leva 856 s. No mesmo momento, o domínio
próprio tinha **zero itens independentes em teste**. O volume de imagens nunca foi o problema.

## 1. Mapa dos blocos

| bloco | caminho | versionado | o que é |
|---|---|---|---|
| próprio | `nosso/rig/` | **sim** | 81 quadros de 640x480 da bancada, garrafas íntegras |
| próprio | `nosso/tampa/` | **sim** | 43: 9 de deformidade do corpo, 14 de tampa ausente, 20 de tampa mal rosqueada |
| próprio | `nosso/<campanha>/` | **sim** | capturas por campanha, só as que viraram evidência anotada |
| externo | `externo/<fonte>/` | não (só `INDEX.md`) | cinco conjuntos públicos + um de detecção por nível de defeito, com crédito registrado |
| derivado | `derivado/classify224/` | não | recortes 224x224 na taxonomia do projeto, reproduzíveis |
| anotação | `anotacao/ls/` | não (só `README.md`) | o que a equipe marcou, no formato canônico de exportação |
| anotação | `anotacao/deteccao_tampa/` | não | rótulos de caixa convertidos para treino de detector |
| síntese | `_experimentos/` | não | pares de defeito sintético aprovados, controles e saídas de experimento |
| benchmark | `benchmark/` | não | referência pública para comparar método |
| quarentena | `_copias/` | só o duplicado declarado | cópia byte-idêntica e cópias de auditoria, sempre com motivo |
| pipeline | `TRABALHO/` | **sim** | os scripts do pipeline e as filas de anotação |

Regra que vale para todos os blocos: **nada de dado bom é excluído**. O único caso em que uma imagem
não conta duas vezes é a cópia byte-idêntica (mesmo sha256): ela vai para `_copias/duplicatas/` com o
motivo escrito e continua no repositório.

## 2. Fluxo de captura de imagens

A fonte própria é uma bancada com a esteira, o suporte de câmera e a iluminação controlada. A captura
sai **por sessão**, e uma sessão corresponde a um item identificado.

### 2.1 Pré-requisitos (não pular)

| # | Item | Critério de aceite |
|---|---|---|
| 1 | tolerância de geometria declarada **antes** do ensaio | posição, distância, orientação e enquadramento com tolerância numérica; mover o suporte e obter desvio sem registro reprova |
| 2 | lente difusora instalada | obrigatória para PET: ponto de luz rígido vira defeito de medição; evidência é foto pareada com e sem difusora |
| 3 | iluminação fixa e registrada | modo, posição e intensidade |
| 4 | uma câmera por vista, identificada | modelo, lente, resolução, ganho, balanço de branco e distância na lista de materiais; não misturar câmeras entre vistas |
| 5 | exposição, foco e balanço de branco travados | depois da calibração, sem automático contínuo |
| 6 | a mesma garrafa é um grupo | definir como o identificador do item se forma e como as vistas se associam a ele |
| 7 | teste reservado | separar antes de qualquer treino os itens que serão teste, registrar a lista e não tocar mais |

### 2.2 O que fotografar

| classe | como obter | mínimo |
|---|---|---|
| garrafa íntegra | garrafa tampada corretamente | 20 a 50 itens |
| tampa ausente | garrafa sem tampa, com boca e rosca visíveis | 20 a 50 itens |
| defeito de tampa | tampa solta, deformada ou aberta | 20 a 50 itens |
| cena vazia | bancada sem item, para separar "sem detecção" de "sem objeto" | conforme a vista |

### 2.3 Como a captura é organizada

Cada passagem gera uma pasta de sessão com uma imagem por vista, e o índice do gatilho registra
horário, evento e identificador de série ao lado das capturas.

| campanha | sessões | arquivos | composição |
|---|---|---|---|
| 14/09, bancada | 65 | 269 | 187 nas séries de três câmeras + 82 no caminho de gatilho |
| 15/09, esteira em movimento | 328 | 1.599 | 933 nas séries de três câmeras + 666 no caminho de gatilho |
| versões de orientação | | 209 | 144 conteúdos distintos: versões anteriores ao giro e ao recorte |
| **arquivos no nó de captura** | **393** | **2.077** | contagem de arquivo, não de imagem |
| **capturas distintas** | | **1.535** | capturas consideradas distintas, fora as versões de orientação |
| cópia de preservação | | 1.653 | cópia de segurança guardada fora da contagem |

A contagem que importa para treino é a última: **1.535 capturas distintas**. Arquivo não é imagem,
e imagem não é item independente.

Por vista, nas séries: 391 arquivos da câmera CSI, 375 da câmera USB e 354 da câmera de captura
dedicada. Nem tudo o que o nó produz entra no acervo de rotulagem: a rodada de 15/09 virou 664
imagens na cópia.

Três decisões que valem registrar:

- **uma passagem, uma sessão, um item.** Isso é o que permite dividir treino e teste sem vazamento.
- **capturar direto para o destino.** Numa rodada longa de esteira em movimento (6 h 38 min, 1.599
  imagens: 666 no caminho de gatilho e 933 nas séries de três câmeras) as capturas ficaram
  acumuladas no cartão do nó e apenas a primeira hora havia sido copiada; o cartão falhou antes da
  cópia e o conjunto só foi recuperado porque o nó reiniciou a tempo. Acumular no dispositivo é dívida.
- **o gatilho é independente da captura.** O evento de presença abre a janela; a janela é o que
  define o que entra na sessão.

## 3. Fluxo de anotação

A anotação acontece em ferramenta de rotulagem com o acervo exposto como arquivos locais.

### 3.1 O que a equipe marca, por imagem

- **caixas**: tampa, tampa alterada, tampa ausente, região do corpo, deformidade do corpo;
- **vista**: lateral, topo ou inconclusiva;
- **classe canônica**: normal, tampa ausente, defeito de tampa, deformidade, inconclusivo;
- **coerência com a fonte**: concorda, conflita com quase-duplicata, rótulo de origem errado.

### 3.2 Regras de importação

- o caminho da imagem tem de ser **relativo à raiz de documentos** da ferramenta
  (`...?d=corpus/<campanha>/<arquivo>.jpg`). Caminho absoluto, ou o caminho interno de upload, falha
  na hora de exibir a imagem mesmo com o arquivo presente;
- a raiz de documentos pode expor **mais de uma origem** ao mesmo tempo (o acervo de captura e o
  próprio diretório de dados do projeto). Todo resolvedor de caminho precisa tentar as duas, senão
  metade das imagens some silenciosamente;
- **um projeto por campanha**, com a configuração de rótulos clonada da campanha anterior.
  Configuração divergente invalida a comparação entre rodadas;
- a anotação automática por serviço de IA serve para **triagem**, nunca como rótulo de verdade. Ela
  reduz fila; ela não substitui o julgamento humano.

### 3.3 Exportação canônica

O export tem formato fixo de 22 colunas, uma linha por anotação, mais um arquivo com a visão por
imagem (projetos, vistas, classes, quantidade de caixas, anotadores). O que não couber nas colunas
canônicas vai para um campo de observação em JSON, sem perder informação. O resultado da última
campanha está em `anotacao/ls/`.

## 4. Síntese de imagens de defeito

Complementa a captura: em vez de esperar o defeito aparecer na esteira, ele é **produzido** sobre uma
imagem real e entra no conjunto apenas se passar por um portão geométrico.

### 4.1 O que é um par sintético

Uma imagem editada mais um JSON de metadados com três campos obrigatórios: a classe, a região afetada
(retângulo) e o nome do arquivo de saída, além de máscara opcional. O par é sempre referenciado à
**imagem original**, porque é contra ela que o portão confere.

### 4.2 O portão de validação

| # | checagem | o que reprova |
|---|---|---|
| 1 | existência do JSON e esquema mínimo | metadado ausente ou incompleto |
| 2 | classe válida e retângulo dentro da imagem | classe fora da taxonomia, caixa vazando a borda |
| 3 | nome do arquivo de saída confere com o arquivo real | renomeação silenciosa depois da geração |
| 4 | máscara com o mesmo tamanho da imagem e contida no retângulo | máscara desalinhada |
| 5 | **isolamento**: comparando com a foto original, as diferenças ficam dentro do retângulo | edição vazando para o resto da cena |
| 6 | duplicatas por sha256 e balanceamento por classe | par repetido ou classe desbalanceada |

O isolamento é a checagem que dá valor às outras: sem ela, uma edição que altera o fundo inteiro
passa como "defeito localizado" e o modelo aprende a diferença de fundo. Os limites usados são
declarados na chamada (tolerância em níveis de cinza e fração máxima de diferença fora do retângulo).

### 4.3 Montagem do conjunto

Só o par que passa entra no conjunto de treino; o que falha vai para o relatório, com o motivo, e
opcionalmente para um diretório de rejeitados. A montagem reusa o mesmo portão da validação, de modo
que não existe caminho de entrada que pule a checagem.

### 4.4 Proveniência de cada par, e o papel do modelo gerador

A geração usa ferramenta de edição e geração de imagem a partir de um quadro real: o defeito é
inserido ou alterado sobre a cena verdadeira, por isso o par continua ancorado na captura. Cada
arquivo sintético carrega origem (sha256 da imagem base), região afetada, qual ferramenta gerou e a
semente usada. Sem esse registro não há como auditar depois o que foi gerado, nem repetir a geração.

A mesma IA entra em outro ponto do ciclo, sem virar verdade: a classificação automática serve para
**triagem de fila**, priorizando o que a equipe deve olhar primeiro. Rótulo de triagem não é rótulo
de conjunto; quem decide é o humano, e é essa decisão que o export registra.

O critério de aceitação de um par **não depende da aparência**. Um defeito convincente gerado por
modelo, com edição vazando para fora da região, é reprovado; um defeito sintético simples, bem
delimitado, é aprovado. O portão é geométrico de propósito: é ele que impede o modelo de aprender
diferença de fundo no lugar de aprender defeito.

### 4.5 Perturbação de controle

Além do defeito sintético existe a **perturbação de controle**: uma alteração conhecida (oclusão ou
risco) aplicada a um quadro real, com máscara e proveniência, que **não é defeito real**. Ela existe
para provar que o sistema reage a uma anomalia conhecida e para comparar a região afetada com o mapa
do modelo. Controle não é dado de treino e não pode ser contado como defeito.

### 4.6 Aumentação por colagem

Para treino de detecção usa-se também colagem de recortes (tampa ou garrafa recortada sobre outro
fundo **do mesmo domínio**), técnica de aumentação para objeto pequeno, com fração e parâmetros
registrados. Ela aumenta variabilidade de treino; não cria evidência de defeito e não entra em teste.

### 4.7 Limite que não se negocia

**Sintético treina; teste é real e reservado.** Nenhum número de desempenho pode ser medido sobre
imagem gerada: o valor medido em dado sintético mede a si mesmo. A mesma régua vale para o domínio
externo: o detector que alcança 0,966 de mAP em conjunto público acerta 5 de 124 no rig próprio.
Isso não é falha de arquitetura, é lacuna de dado próprio.


## 5. Estado atual

```
capturado no nó de captura ....... 2.077 arquivos em 393 sessões
  14/09, bancada ................. 65 sessões: 187 nas séries + 82 de gatilho
  15/09, esteira em movimento .... 328 sessões: 933 nas séries + 666 de gatilho
  versões de orientação .......... 209 arquivos (versões anteriores ao giro e ao recorte)
  captura distinta ............... 1.535
  cópia de preservação ........... 1.653 arquivos (cópia de segurança, não soma)

carregado na ferramenta .......... 38.220 imagens em 14 projetos
anotado .......................... 394 tarefas, 407 anotações, 394 imagens distintas (6 projetos)
rascunhos não submetidos ......... 15 em 15 tarefas
próprio versionado ............... 124 imagens (81 da bancada + 43 de tampa) + 1 duplicata declarada
síntese .......................... pares aprovados no portão, controles e rejeitados com motivo
externo .......................... cerca de 6,7 mil imagens públicas com crédito registrado
derivado ......................... cerca de 4,5 mil recortes 224x224 na taxonomia do projeto
```

Leitura correta destes números. **capturado** é o que o nó produziu, e vale a contagem de conteúdo
distinto, não de arquivo: 1.535. **carregado** é o que está na ferramenta de rotulagem, incluindo dado
externo e recortes derivados espelhados lá: 38.220. **anotado** é o que a equipe marcou de fato: 394
tarefas. Os três não se somam, e só o terceiro mede trabalho humano. Comparar 1.535 com 38.220 para
concluir "temos muito dado" é o erro que este parágrafo existe para impedir.

## 6. Como verificar

```bash
sha256sum -c dataset/MANIFEST.sha256                  # imagens do bloco próprio
sha256sum -c dataset/anotacao/ls/MANIFEST.sha256      # imagens do export de anotação
make verificar                                        # produto, firmware e PoCs
```

Os portões do pipeline ficam no diretório de trabalho: validação de par, montagem do conjunto com
apenas aprovados, e verificação de integridade por sha256 em cada bloco.
