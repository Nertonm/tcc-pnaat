# Hardware, montagem e ligação

Manual de bancada do PNAAT. Diz o que o sistema usa, como o rig é montado, o que está ligado e
medido, o que está projetado e o que não foi medido. Cada afirmação traz a fonte no repositório; o
que não tem fonte aparece declarado como tal.

Estados usados neste documento: implementado (existe e foi exercitado), projetado (desenho aprovado,
sem bancada) e não medido (sem instrumentação no rig).

## 1. Lista de materiais

| # | Item | Especificação (fonte) | Papel no sistema | Estado |
|---|---|---|---|---|
| 1 | Raspberry Pi 5 | a instalação medida usa cartão de 119 GiB (`mmcblk0`); o repositório recomenda SSD ou NVMe para armazenamento (`docs/DECISIONS.md:1241-1247`) | nó de visão: captura, inferência, registro SQLite e dashboard | adotado (D-19) |
| 2 | ESP32-CAM | módulo AI-Thinker (`src-production/firmware/esp32cam-test/main/main.c:28`; `cad-produto/README.md:96-97`) | uma foto por disparo, câmera em standby entre fotos | implementado |
| 3 | ESP32 com MicroPython | nó de trigger separado, alimentado pelo USB do Pi (`docs/DECISIONS.md:1141`) | lê o sensor de presença e abre a janela de captura | implementado (PoC-01) |
| 4 | Sensor fotoelétrico E18-D80NK | 5 V, saída NPN, alcance de 3 a 80 cm; rótulo 5 VDC e 100 mA, fios bege, preto e azul, cerca de 5 V livre e 0 V com objeto (`docs/reference/ref-e18-d80nk-sensor.md:11-16,24-27`) | gatilho de presença do item | não medido com o sensor real |
| 5 | Adaptadores USB-serial | CP2102 ou CH340, portas resolvidas por `by-id` (`docs/DECISIONS.md:852,983,1149`) | ligam trigger e câmera ao Pi, em duas portas na mesma ponte | implementado |
| 6 | Câmeras | `topo` é a câmera CSI da Raspberry Pi apontada para baixo; `lateral1` é a ESP32-CAM; `lateral2` é a webcam USB UVC (`cad-produto/00-produto/composicao-esteira/contract.json`; `README.md:104`) | vistas do mesmo item | papéis definidos, e são dado da instalação |
| 7 | Cabo flat | FFC de 200 mm (`cad-produto/ATRIBUICOES.md:55`) | liga a câmera CSI à placa | |
| 8 | Trilho DIN e peças impressas | ver seção 3 | estrutura do rig | conferida geometricamente, com ressalvas na seção 3 |
| 9 | Encoder incremental KY-040 | candidato; não faz parte do implementado (`docs/DECISIONS.md:284,307-311`; `docs/arquitetura.md`, seção de expansões) | medição de movimento, na expansão | projetado (expansão) |
| 10 | Esteira | teto derivado de cerca de 107 mm/s, com passo de 80 mm e três vistas; o valor de operação segue a decidir e não medido (`docs/DECISIONS.md:610-616`, `docs/pocs/03-sincronizacao-fisica/CALIBRACAO-DELAY.md:60-64`) | movimento do item; o sistema não controla a esteira | fora do núcleo |
| 11 | Ferragens do trilho | furo passante Ø6,5 para M6, escareado Ø13×1,0, arruela Ø12, quatro furos Ø4,5 com rebaixo Ø9,0×5,0 (`cad-produto/02-impressao/base-trilho/README.md:12-19`) | fixação da base do trilho | medido |

As peças impressas estão em `cad-produto/02-impressao/`. A base do trilho é a única com números de
impressão publicados: um sólido, 241.237,2 mm³, 306,4 g, área de apoio de 11.952,0 mm² e envelope de
131,00 por 103,50 por 36,50 mm, dentro da K1C de 220 por 220 por 250 mm
(`cad-produto/02-impressao/base-trilho/README.md:21-22`, `DOCUMENTACAO-20260914.md:100`). O suporte
lateral da câmera tem 6 peças, o case da ESP32-CAM existe só em `.step`, sem STL
(`cad-produto/README.md:69`), e o case da Raspberry Pi 5 usa o encaixe de trilho DIN da própria
peça. Créditos e licenças de terceiros estão em `cad-produto/ATRIBUICOES.md`.

## 2. Pinagem e interfaces

Estas são as constantes de pino do firmware próprio, em
`src-production/firmware/esp32cam-test/main/main.c`:

| Sinal | Pino (GPIO) | Estado |
|---|---|---|
| Sensor de presença, `SENSOR_GPIO` | 13, active-low, borda de descida, pull-up interno (`main.c:21,702,704`) | declarado; níveis do sensor real não medidos |
| `PWDN` do sensor de imagem | 32, alto coloca o sensor em standby (`main.c:29,110,563`) | verificado na bancada |
| `XCLK` | 0, parado no standby com `ledc_stop` e pino em entrada com pull-down (`main.c:44,78-90,319`) | verificado |
| `SIOD` e `SIOC`, I²C da câmera | 26 e 27 (`main.c:45-46`) | implementado |
| `D0` a `D7`, barramento de dados | 5, 18, 19, 21, 36, 39, 34 e 35 (`main.c:47-54`) | implementado |
| `VSYNC`, `HREF` e `PCLK` | 25, 23 e 22 (`main.c:55-57`) | implementado |
| Chave de carga do rail 3V3 da câmera, `CAM_POWER_GPIO` | -1, ausente nesta placa; o firmware tem o caminho pronto (`main.c:38`) | não implementado no hardware |
| `RESET` da câmera, `CAM_PIN_RESET` | -1, não usado (`main.c:43`) | |
| Comunicação ESP32 e host | UART/USB, console e imagem no mesmo fio, demux por enquadramento com SOF `A5 5A`, CRC16 do cabeçalho e CRC32 do payload | medido no fio |
| Nó de trigger MicroPython (E18-D80NK) | `PRESENCE_PIN=27` active-low com pull-up e `CAPTURE_OUT_PIN=26`, declarados em `firmware/trigger-node/esp/main.py` | lógica implementada; ligação e níveis do sensor real a medir |

O contrato congelado em `src-production/firmware/README.md:78-88` declara apenas `TRIGGER_GPIO`, o
pino 13, e o modo elétrico esperado. Os outros pinos estão no firmware, não no contrato.

`GPIO4` não existe no firmware. Ele aparece uma vez como experimento de bancada em
`src-production/firmware/README.md:185` e não faz parte do trigger de produção.

### Ligação do sensor

O E18-D80NK é alimentado em 5 V e tem saída NPN, do tipo open-collector. A tensão de saída depende
do que existe do lado do módulo, e há dois casos documentados; o que decide entre eles é medição, não
suposição (`docs/reference/ref-e18-d80nk-sensor.md:27,45-49`):

1. Com resistor de pull-up para 5 V no módulo, a saída passa de 3,3 V e exige condicionamento de
   nível, com divisor ou transistor, antes do GPIO.
2. Sem pull-up para 5 V, a entrada pode ser ligada direto usando o `PULL_UP` interno do ESP32.

Nos dois casos, conferir a tensão de saída em bancada antes de ligar. Terra comum entre sensor,
ESP32 e host é obrigatório (`src-production/firmware/README.md:184`).

O esquemático de interligação atualizado está em `docs/diagramas/interligacao-eletrica.mmd`. O
projeto histórico `ESP32S3-Trigger.zip` usa um PIR genérico no Wokwi e **não** é a fonte normativa
da pinagem; sua limitação está registrada em `docs/reference/esquematico-trigger.md`. O firmware
declara GPIO27 e o modo elétrico. Falta medir, com o sensor real, os níveis de saída, o debounce, com
alvo de 50 ms, e o cooldown, com alvo de 250 ms (`main.c:23-24`;
`src-production/firmware/README.md:202`).

A montagem óptica do sensor segue o princípio IR difuso do E18-D80NK: posição e angulação são validadas em bancada; difusor e dois LEDs RGB de 5 mm fazem parte da iluminação de bancada (`docs/requisitos/05-hardware-ml.md:23-31`).
Uma alternativa em avaliação é o VL53L0X (`docs/DECISIONS.md:284`).

## 3. Montagem mecânica

As peças e a montagem de referência estão em `cad-produto/`, com o eixo Z como altura.

1. Pórtico: dois montantes DIN, `MontanteA` e `MontanteB`, mais `Travessa`, junções e chavetas, num
   total de 21 peças em `cad-produto/01-estrutura/` (`cad-produto/MANIFEST.json`).
2. Base do trilho, em `cad-produto/02-impressao/base-trilho/`: recebe o bracket já impresso, com furo
   passante Ø6,5 medido no conjunto em posição de uso, mais quatro furos de fixação
   (`cad-produto/02-impressao/base-trilho/README.md:12-19,24-31`).
3. Suporte lateral de câmera, em `cad-produto/02-impressao/camera-lateral/`: 6 peças em 12 arquivos
   entre `.stl` e `.step`. Três trazem marca de origem de terceiro no próprio nome
   (`Cover_SOURCE_REFERENCE`, `Housing_SOURCE_REFERENCE` e `Swivel_SOURCE_DERIVATIVE`), e
   `cad-produto/ATRIBUICOES.md:42-43` atribui quatro componentes: housing, tampa, swivel e braço.
4. Cases: `case-esp32cam`, desenhada a partir das medidas de catálogo do módulo e só em `.step`, e
   `case-pi-din`, que usa o encaixe de trilho da própria peça de origem girada um quarto de volta em
   Z. O autor e a licença estão no diretório.
5. Câmeras: uma CSI no topo apontada para baixo, uma webcam USB em uma lateral e uma ESP32-CAM na
   lateral oposta (`cad-produto/README.md:87-88`;
   `cad-produto/00-produto/composicao-esteira/contract.json`).

As conferências feitas e o que elas valem estão em
`cad-produto/00-produto/composicao-esteira/verification-build.json` e
`cad-produto/00-produto/composicao-esteira/verification-readback.json`:

| Medida | Valor |
|---|---|
| Corpos, sólidos STEP e triângulos STL | 51, 57 e 80.212 |
| Envelope do conjunto | 600,0 por 1300,0 por 1302,902 mm |
| Eixo óptico da câmera de topo | `[0, 0, -1]`, com `target_dot` de 1,0 |
| Folga do topo até o topo da garrafa | 110,2836 mm |
| Encaixe da case no trilho, controle | 98,386387 mm³ para dentro, 10,256758 mm³ para fora no gancho e 0 mm³ afastado |
| Interferência residual do par case e trilho | 0,0320589710 mm³ na base e 0,0091627391 mm³ na tampa; o limite declarado é 0,1 mm³ e nenhum par passa dele |
| Erro relativo de volume do STEP | 1,6e-10 |

O CAD não chamou esses resíduos de zero. O README do conjunto diz que eles existem e ficam abaixo do
limite declarado (`cad-produto/00-produto/composicao-esteira/README.md:15-16,27`), e o status do
conjunto é `CANDIDATE_GEOMETRY`, ilustrativo e não liberado para fabricação
(`cad-produto/00-produto/composicao-esteira/verification-build.json:2`; `cad-produto/MANIFEST.json:5`;
`cad-produto/00-produto/composicao-esteira/contract.json:10`).

O teste do encaixe tem controle: empurrar a case acusa colisão e afastar zera. Isso mostra que o teste
detecta penetração, não que a case esteja travada
(`cad-produto/00-produto/composicao-esteira/README.md:19-22`).

As pendências do CAD, registradas: o suporte da câmera de topo é conceitual e não está liberado para
imprimir (`cad-produto/00-produto/composicao-esteira/README.md:34`); PCB e lente são ilustrativos e o
CM3 Wide não foi validado
(`cad-produto/00-produto/composicao-esteira/verification-build.json:51`); a inspeção visual não foi
realizada, por falha do provedor de visão
(`cad-produto/00-produto/composicao-esteira/verification-readback.json:29`,
`cad-produto/00-produto/composicao-esteira/README.md:39`); a compatibilidade física está confirmada
pelo usuário, não medida (`cad-produto/00-produto/composicao-esteira/README.md:22`); e a licença do
modelo da ESP não foi verificada (`cad-produto/00-produto/composicao-esteira/README.md:36`;
`cad-produto/ATRIBUICOES.md:101-110`). Na base do trilho, Y igual a 0 é suposição, o M6 não foi
conferido e o caminho de carga e torque não foi calculado
(`cad-produto/02-impressao/base-trilho/README.md:52-58`). Não há layer height, número de paredes,
infill nem orientação publicados para nenhuma peça.

## 4. Alimentação

A ESP32-CAM é alimentada pela porta USB ou serial. Entre fotos o módulo continua alimentado, e o que o
firmware faz é standby do sensor com `PWDN` alto, não corte de 3V3
(`src-production/firmware/README.md:96-102`). O trigger é um ESP32 separado, alimentado pelo USB do Pi
(`docs/DECISIONS.md:1141`). O sensor trabalha em 5 V com consumo de 100 mA ou mais, pelo rótulo
do componente (`docs/reference/ref-e18-d80nk-sensor.md:11-16`), e o GND é comum entre sensor, ESP32 e
host (`src-production/firmware/README.md:184`).

Corrente e temperatura em idle, wake e captura não foram medidas
(`src-production/firmware/README.md:204`). O repositório não declara modelo de fonte para o Pi; a
instalação segue a alimentação própria da placa.

## 5. Verificação de bancada

| Verificação | Resultado | Origem |
|---|---|---|
| `PWDN` funcional | `SENSOR_TEST pwdn=1 detect=0`: o sensor não responde com PWDN alto | `src-production/firmware/README.md:191` |
| Uma foto por trigger | 3 triggers geram exatamente 3 fotos; nenhuma foto em 15 s de ociosidade | idem |
| Frame íntegro | tamanho, sequência e CRC conferidos, com o CRC do firmware batendo com o `zlib` do host | idem |
| Frame parcial ou corrompido | nunca publicado, por CRC por mensagem, CRC do frame, marcadores `FF D8` e `FF D9` e lacuna de chunk | idem |
| Standby | em todos os caminhos: fim de captura, falha de init e fim do teste de energia | idem |
| Transporte no fio, frame JPEG de cerca de 13 kB | texto base64 com 27.233 bytes na linha em 292 ms; binário com 14.921 bytes em 191 ms; binário a 1,5 Mbps em 145 ms (`src-production/firmware/README.md:66-70`) | medido |
| Baud de operação | firmware arranca em 921600 (`SERIAL_BAUD`, `main.c:22`) com negociação até 1,5 Mbps; medida no fio a 921600 e 1,5 Mbps (`src-production/firmware/README.md:66-70`). O histórico D-40 registra falha a 921600 e operação em 460800 (`docs/DECISIONS.md:848-851`) | medido |
| Latência do enlace serial | cerca de 0,75 s de ponta a ponta (`docs/DECISIONS.md:1257`) | medido |

A parte de software se reproduz com `make -C src-production test-firmware`, que roda 17 testes, e
`make -C src-production verificar`, que roda a suíte do produto mais o firmware.

## 6. Serviços em operação

O rig não roda em sessão de terminal. A operação usa units systemd no Pi
(`docs/DECISIONS.md:911-918,745-747,1043`):

| Unit | Papel |
|---|---|
| `pnaat-ponte.service` | dono das duas portas seriais, trigger e câmera, resolvidas por `by-id` |
| `pnaat-gatilho-posboot.service` | estado do gatilho depois do boot |
| `pnaat-hub-site.service` | site e hub do Pi na porta 8091, usuário `nerton` |

O serviço de captura do rig responde em `127.0.0.1:8090`, configurado por `PNAAT_RIG`; a ponte fica
em `127.0.0.1:8094`, por `PNAAT_PONTE`; e o adaptador de modelo em `127.0.0.1:8093`, por
`PNAAT_MODEL_API` (`src-production/api.py:63-68`). Esse runtime
fica fora do repositório por decisão, porque carrega caminho pessoal, host e a tabela de ROI da
instalação.

## 7. Limites de validação e pendências de bancada

1. O sensor de proximidade E18-D80NK está declarado no firmware e no mapa de GPIO, sem medição
   registrada da ligação física (seção 2).
2. Níveis elétricos do E18-D80NK e ligação física ao GPIO27 do nó de trigger não foram medidos
   (seção 2). O GPIO13 da ESP32-CAM é somente uma entrada local alternativa, sem fio na topologia
   adotada com o nó dedicado.
3. Debounce, com alvo de 50 ms, e cooldown, com alvo de 250 ms, não foram medidos com o sensor real.
4. O firmware aceita comando de bancada de qualquer origem. A restrição por origem em modo de
   produção é um modo de segurança documentado, a ser habilitado na instalação
   (`src-production/firmware/README.md:203`).
5. Corrente e temperatura em idle, wake e captura não foram medidas.
6. A cadeia de trigger tem código no repositório: o nó MicroPython (`firmware/trigger-node/`), a ponte
   serial (`esp32cam_site.py`), o gateway (`api.py`) e o registro idempotente por `item_id`. Níveis
   elétricos do sensor real e latência física seguem como medição de bancada pendente conforme as
   seções 2 e 5; essa pendência é de validação, não de código ausente. O contrato está em
   `docs/operacao-pipeline.md`.
7. O corte de energia da câmera tem o caminho pronto no firmware, em `CAM_POWER_GPIO`, e exige chave de
   carga no rail 3V3; nesta placa o GPIO está ausente.
8. No CAD, o suporte da câmera de topo não está liberado para impressão, a inspeção visual não foi
   feita e a licença do modelo da ESP não foi verificada (seção 3).

## 8. Onde cada assunto é aprofundado

| Assunto | Documento |
|---|---|
| Especificação do produto e do evento | `docs/arquitetura.md` |
| Requisitos de hardware, iluminação e ML | `docs/requisitos/05-hardware-ml.md` |
| Sensor de presença, características e identificação de fios | `docs/reference/ref-e18-d80nk-sensor.md` |
| Decisões D-19, D-20, D-21, D-23 e D-38, e o histórico do baud | `docs/DECISIONS.md` |
| CAD, peças, atribuições e conferências | `cad-produto/README.md`, `cad-produto/ATRIBUICOES.md` e `cad-produto/00-produto/composicao-esteira/README.md` |
| Firmware, contrato congelado, protocolo e critérios de aceite | `src-production/firmware/README.md` |
| Política de mídia e higiene do repositório | ferramenta removida deste checkout; revisar `.gitignore` e o diff antes de publicar |
| Instalação e execução | `README.md` |
