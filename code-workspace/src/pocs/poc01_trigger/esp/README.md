# PoC-01: Trigger de presença (E18-D80NK) no ESP32

## Objetivo

Validar que a detecção de presença abre uma janela de captura que cobre o mesmo
item em mais de uma vista (PoC-01). Foco: visibilidade e rastreabilidade; sem
atuação física e sem controle da esteira.

## Sensor

- **E18-D80NK**: sensor IR difuso (emissor + receptor), saída digital NPN NO.
- Lógica da saída: **LOW = objeto dentro do alcance** (active low); HIGH fora.
- Tensão de alimentação do sensor: VCC 5V; a saída segue esse nível, então NÃO
  ligue o sinal direto em pino de 3.3V sem divificar (divisor de tensão ou módulo
  de lógica/level shifter).

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
4. **Janela de captura**: ao estabilizar, abre a janela com as vistas definidas
   (`VIEWS`) por `WINDOW_MS`, e aciona a saída `CAPTURE_OUT_PIN`.
5. **Fechamento**: após `MISS_READS` leituras estáveis de ausência, fecha a janela
   e volta a aguardar uma nova borda de subida.

Relação com o código de desktop: `src/pocs/poc01_trigger/presence.py` é a lógica
pura (testada por pytest, agnóstica de hardware). `esp/main.py` é a mesma lógica
sem dependência de `dataclasses`, rodando em MicroPython no ESP32.

## Testar no ESP32 (hardware)

1. Grave MicroPython no ESP32.
2. Copie `esp/main.py` como `main.py` no dispositivo (Thonny, `ampy` ou `mpremote`).
3. Ajuste `PRESENCE_PIN`/pinos se necessário.
4. Suba com o monitor serial. Aproxime um objeto da frente do sensor: deve sair
   `CAPTURE_WINDOW_OPEN views=topo,lateral1,lateral2`; afaste até sair
   `CAPTURE_WINDOW_CLOSE`.
5. O LED/relé em `CAPTURE_OUT_PIN` liga durante a janela.

## Testar em desktop (CI, sem hardware)

```
cd code-workspace
make test        # inclui tests/test_trigger.py
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
2. Copie o firmware: `mpremote connect /dev/ttyUSB0 cp src/pocs/poc01_trigger/esp/main.py :main.py`
   (ou Thonny: salvar como `main.py` no dispositivo).
3. Abra o monitor: `mpremote connect /dev/ttyUSB0 repl` (ou `screen /dev/ttyUSB0 115200`).
4. Aproxime/afaste o objeto. Esperado no serial:
   `POC01_READY pin=27 out=26 ...` → `CAPTURE_WINDOW_OPEN n=1 views=topo,lateral1,lateral2`
   → `CAPTURE_WINDOW_CLOSE`.
5. **Critério de passagem**: 10 passagens → 10 janelas, sem duplicidade; objeto parado →
   1 janela só; pulso curto (ruído) → nenhuma janela.
6. Compare com a simulação sem hardware (`make simular-poc01`), que usa as MESMAS regras:
   se o firmware e a simulação divergirem, um dos dois está errado: investigue antes de seguir.

## Simular o fluxo sem hardware (roda hoje)

```bash
cd code-workspace
make simular-poc01                 # todos os casos
python3 scripts/simular_trigger.py --niveis 1,1,0,0,0,0,0,0,1,1
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
