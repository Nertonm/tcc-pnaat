# Esquemático do trigger ESP32-S3

Arquivos-fonte da simulação Wokwi recebida para o trigger. O original compactado permanece na raiz
como `ESP32S3-Trigger.zip`; os arquivos foram expostos aqui para revisão e versionamento legível.

## Arquivos

- `diagram.json`: ESP32-S3 DevKitC-1, protoboard, sensor PIR e resistores de 2,2 kΩ e 3,3 kΩ;
- `sketch.ino`: programa mínimo da simulação (serial e laço ocioso);
- `wokwi-project.txt`: origem do projeto no Wokwi.

## Conexões representadas

| Origem | Destino / função |
|---|---|
| ESP32-S3 `5V` | barramento positivo da protoboard e VCC do PIR |
| ESP32-S3 `GND` | barramento negativo e GND do PIR |
| PIR `OUT` | resistor de 2,2 kΩ |
| Nó de sinal | resistor de 3,3 kΩ para GND, formando divisor com 2,2 kΩ |

O `diagram.json` recebido não fecha de maneira inequívoca o nó do divisor em um GPIO usado pelo
`sketch.ino`, e o programa não lê o sensor. Portanto, este material documenta a **simulação
recebida**, não um circuito de produção validado.

## Montagem segura

1. Não conecte uma saída acima de 3,3 V diretamente ao GPIO.
2. Confirme no datasheet e por medição se o sensor real é NPN/open-collector ou saída ativa.
3. Use GND comum e condicionamento de nível compatível com o sensor e a placa.
4. Meça o nó com multímetro antes de conectá-lo ao GPIO.
5. Só então defina o GPIO no firmware, teste polaridade, debounce e cooldown.

O firmware ESP32-CAM atualmente documenta a hipótese do E18-D80NK em GPIO13, active-low, mas
declara que os níveis do sensor real não foram medidos. Veja `src-production/firmware/README.md`.

## Abrir a simulação

Crie um projeto ESP32-S3 no Wokwi e importe `diagram.json` e `sketch.ino`, ou use a URL registrada em
`wokwi-project.txt`. O resultado esperado do programa atual é apenas `Hello, ESP32-S3!` no monitor
serial; qualquer demonstração de trigger exige implementar e testar a leitura do GPIO.
