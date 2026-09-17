# Hardware, iluminação, ambiente e machine learning

## Hardware e ambiente

### HW-01: Geometria repetível

- Entrada: posições de câmeras, trigger e encoder.
- Critério: montagem repetida mantém enquadramento e calibração dentro da tolerância definida antes do ensaio.
- Critério de reprovação: mover o grip e obter drift sem registro. Evidência: desenho, cotas, calibração antes/depois.

### HW-02: Conexões críticas fixas

- Critério: trigger, encoder e sensores móveis são soldados ou presos em breakout; continuidade passa no multímetro.
- Critério de reprovação: circuito aberto ou jumper solto. Evidência: checklist e medição.

### HW-03: Mounts e jig

- Critério: suportes parafusados e jig posicionam item repetidamente; réplicas de deformidade são parametrizadas.
- Critério de reprovação: reposicionamento altera medida/enquadramento além da tolerância. Evidência: desenho e ensaio repetido.

### HW-04: Arranjo de iluminação por vista e difusão óptica

- Entrada: 2x LEDs RGB de 5 mm de alto brilho, lente difusora (PLA 3D branco translúcido, acrílico ou papel vegetal), fita retrorrefletiva 3M e sinais PWM de controle.
- Critério: acionamento direto dos LEDs RGB em potência máxima (luz branca) operados em modo estroboscópico via trigger do ESP32; obrigatoriedade do uso de lente difusora frontal para eliminação de hotspots rígidos em garrafas de PET/Vidro; alinhamento óptico do sensor E18-D80NK inclinado em 10°–15° mirando no anteparo retrorrefletivo oposto.
- Critério de reprovação: iluminação contínua gerando aquecimento e descarregamento de bateria, ou ausência de difusor provocando reflexos saturados.
- Evidência: fotos pareadas com e sem lente difusora, relatório de temperatura e logs de consumo das fonte de alimentação declarada no BOM (USB/serial; sem bateria no núcleo).

### HW-05: BOM e interfaces

- Critério: cada placa, câmera, sensor, atuador, alimentação e cabo tem modelo, interface e quantidade.
- Critério de reprovação: “câmera USB” ou “sensor” sem identificação reproduzível. Evidência: BOM versionada.

### HW-06: Segurança física e térmica

- Critério: alimentação, ventilação, cabos, partes móveis e parada segura são inspecionados antes da demo.
- Critério de reprovação: atuador acessível sem parada ou Pi superaquecendo sem alerta. Evidência: checklist e medição.

### ENV-01: Condições do ensaio

- Critério: registrar iluminação, velocidade, resolução, câmera, posição, temperatura e versão do modelo.
- Critério de reprovação: comparar resultados de setups diferentes sem qualificação. Evidência: manifest do ensaio.

## Machine learning e dataset

### ML-01: Taxonomia e rótulos

- Critério: classes, severidade e exemplos são definidos antes do treino e ligados à vista esperada.
- Critério de reprovação: rótulo ambíguo ou erro técnico classificado como defeito físico. Evidência: taxonomia e exemplos.

### ML-02: Splits sem vazamento

- Critério: treino, validação e teste não compartilham fotos do mesmo item/replicação.
- Critério de reprovação: hash ou grupo de item aparece em splits distintos. Evidência: manifest e script de verificação.

### ML-03: Proveniência de imagens

- Critério: cada imagem registra origem, licença/uso, classe, câmera, data e hash.
- Critério de reprovação: imagem sem origem ou dataset público tratado como fonte primária. Evidência: manifest.

### ML-04: Generalização honesta

- Critério: classificador de garrafa não sustenta claim de generalização; objetos novos só testam a camada geométrica, se aprovada.
- Critério de reprovação: objeto fora do treino aceito pelo classificador específico como prova geral. Evidência: protocolo separado.

### ML-05: Camadas condicionais

- Critério: CutPaste/NSA, descritores, cross-view, teacher-student e weak supervision têm PoC própria, métrica, latência e fallback.
- Critério de reprovação: camada entra no núcleo somente por existir no documento. Evidência: ficha de PoC.

### ML-06: Modelo no hardware alvo

- Critério: inferência INT8 e latência são medidas no Pi 5, com runtime, resolução e modelo registrados.
- Critério de reprovação: benchmark de Jetson/GPU usado como resultado do Pi. Evidência: benchmark no alvo.
