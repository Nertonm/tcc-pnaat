# PoC-01: Trigger de presença (E18-D80NK) no ESP32

## Objetivo

Validar que a detecção de presença abre uma janela de captura que cobre o mesmo
item em mais de uma vista (PoC-01). Foco: visibilidade e rastreabilidade; sem
atuação física e sem controle da esteira.

## Sensor

- **E18-D80NK**: sensor IR difuso (emissor + receptor), saída digital NPN NO.
- Lógica da saída: **LOW = objeto dentro do alcance** (active low); HIGH fora.
- Tensão de alimentação do sensor: VCC 5 V. Meça a saída: se ela chegar a 5 V, NÃO
  ligue o sinal direto ao pino de 3,3 V; use divisor ou conversor de nível. Se for
  open-collector pura, use o pull-up de 3,3 V do GPIO.

## Fiação (sensor → ESP32)

| Sensor E18-D80NK | ESP32                           |
|------------------|---------------------------------|
| VCC = **bege** (confirmado; equivale ao marrom do padrão) | fonte 5V (mesma referência GND) |
| Azul (GND)       | GND                             |
| Preto (Sinal)    | GPIO (com `PULL_UP`; divisor **só** se medir 5 V no pino) |

Pinos no código: `PRESENCE_PIN` (entrada, pull-up) e `CAPTURE_OUT_PIN` (GPIO
opcional de saída, usado como sinal de "capturando" para LED/release em teste).

## Como funciona (lógica)

1. Lê o sinal do sensor a cada `DEBOUNCE_MS`.
2. Converte nível em presença: `present = (level == 0)` (active low).
3. **Debounce**: só considera presença estável depois de `STABLE_READS` leituras
   consecutivas de presença; um pulso isolado (ruído/reflexo) não abre a janela.
4. **Janela de captura**: presença confirmada abre a janela e aciona a saída
   `CAPTURE_OUT_PIN`; mas só se o sensor esteve LIVRE por `GUARD_MS` contínuos
   antes (`EV OPEN ... livre_ms=`). Isso é o que impede o mesmo item, piscando na
   borda de detecção, de abrir duas janelas. Custo aceito: dois itens separados
   por menos de `GUARD_MS` contam como um.
5. **Fechamento**: após `MISS_READS` leituras estáveis de ausência, fecha a janela
   (`EV CLOSE ... dur_ms=`) e volta a aguardar presença.

Relação com o código de desktop: `../presence.py` contém o subconjunto portável de debounce,
testado por pytest e agnóstico de hardware. `main.py` acrescenta warm-up, armamento, guarda,
heartbeat, GPIO e persistência no flash; portanto o simulador não substitui o teste na placa.

## Testar no ESP32 (hardware)

1. Grave MicroPython no ESP32.
2. Copie `esp/main.py` como `main.py` no dispositivo (Thonny, `ampy` ou `mpremote`).
3. Ajuste `PRESENCE_PIN`/pinos se necessário.
4. Suba com o monitor serial. Esperado: `EV READY pin=27 ...`, `EV ARMED`, um
   `EV PING` a cada 2 s com o nível do pino. Aproxime um objeto: sai
   `EV OPEN n=1 ... livre_ms=...`; afaste até o nível voltar a 1: sai
   `EV CLOSE n=1 ... dur_ms=...`. Objeto parado na frente abre UMA janela só
   (flicker de borda gera `EV SUPPRESSED motivo=guarda`, não uma segunda).
5. O LED/relé em `CAPTURE_OUT_PIN` liga durante a janela.

## Testar em desktop (CI, sem hardware)

```bash
make -C src-production test-trigger
make -C src-production trigger-simular
```

O teste cobre: abertura após debounce, pulso isolado não abre e fechamento após
ausência estável, além da conversão `present_from_sensor` (LOW = presente).

## Critério de passagem (do núcleo)

A `PoC-01` passa se o evento de presença abre a janela para mais de uma vista por
item, sem duplicidade, com identidade e timestamps associados.

## Bancada: testar o COMPONENTE antes do firmware (multímetro)

Ordem obrigatória: medir, não presumir:

1. **Identifique os fios**: marrom = VCC, azul = GND, preto = sinal.
2. **Alimente com 5V** e GND comum (a dev board tem saída 5V; não use 3,3V para alimentar).
   O LED do módulo deve acender.
3. **Meça o sinal** (multímetro VDC, ponta vermelha no PRETO, preta no GND):
   - sensor livre: leitura alta (~5V se houver pull-up no módulo; ~0V/instável se for
     open collector puro);
   - objeto a 10-30 cm: a leitura **cai para ~0V** (LOW = detectado).
   Essa medida decide a fiação: se o pino chega a 5V, use divisor ou level shifter;
   se é open collector puro, ligue direto no GPIO com `PULL_UP` (3,3V): o nível nunca
   passa de 3,3V.
4. **Repetibilidade**: 10 aproximações → conte quantas detecções. Ajuste o potenciômetro
   do módulo até 10/10 na distância de trabalho (comece em ~15 cm).
5. **Registre**: distância de detecção, ponto do potenciômetro (marca/foto) e a contagem
   10/10. Isso é evidência da PoC: sem isso é impressão.

**Ponto crítico e honesto**: o E18-D80NK é IR difuso; **garrafa PET transparente é o caso
difícil**. Teste com a garrafa VAZIA e CHEIA, e registre os dois resultados. Se não detectar
de forma repetível, o fallback declarado (D-20) é o VL53L0X ou barreira retrorrefletiva -
não force o resultado.

## Fluxo no hardware (depois do componente aprovado)

1. Grave MicroPython no ESP32 (`esptool.py --chip <seu chip> write_flash -z 0x1000 <fw.bin>`).
2. Da raiz, copie o firmware com
   `make -C src-production/firmware flash-trigger PORTA_TRIGGER=/dev/serial/by-id/<ESP32-trigger>`
   (ou use Thonny para salvar `src-production/firmware/trigger-node/esp/main.py` como `main.py`).
3. Abra o monitor: `mpremote connect /dev/ttyUSB0 repl` (ou `screen /dev/ttyUSB0 115200`).
4. Aproxime/afaste o objeto. Esperado no serial:
   `EV READY pin=27 out=26 ...` → `EV OPEN n=1 ... livre_ms=...` → `EV CLOSE n=1 dur_ms=...`
   (mais `EV PING nivel=...` a cada 2 s, inclusive durante o armamento).
5. **Critério de passagem**: 10 passagens espaçadas ≥ `GUARD_MS` → 10 janelas;
   objeto parado na frente (inclusive com flicker) → 1 janela só; pulso curto
   (ruído) → nenhuma janela. Sensor bloqueado no boot → `EV ARM_WAIT` + `EV PING`
   (o nó avisa, não arma, e continua vivo no serial).
6. Compare abertura e fechamento com `make -C src-production trigger-simular`. O simulador cobre o
   debounce básico; warm-up, guarda temporal, flash e GPIO só são validados na placa.

## Simular o fluxo sem hardware (roda hoje)

```bash
make -C src-production trigger-simular
.venv/bin/python src-production/firmware/trigger-node/host/simular_trigger.py \
  --niveis 1,1,0,0,0,0,0,0,1,1
```


## Nosso exemplar (medido/informado)

- Label do sensor: **5VDC: 100mA** → reserve **≥100 mA em 5 V**; alimente pelo rail 5 V da placa
  (USB) e **nunca** pelos 3,3 V. Em fonte de bancada, limite a corrente (~150 mA) no primeiro teste.
- Fios (confirmado): **bege = +5V**, **preto = sinal**, **azul = GND** (o padrão do datasheet usa
  marrom no lugar do bege; em outro lote, reconfirme medindo).
- Faixa ajustável **3 cm a 80 cm**; tempo de resposta < 2 ms; saída **NPN NO**, `0 = objeto detectado`
  (nossa conversão `level == 0` está correta).
- Detalhes, divergências de datasheet e procedimento de identificação:
  `docs/reference/ref-e18-d80nk-sensor.md`.
