# Checklist de campo G0 - Esteira B

Provenance e manifest deste formulário: `reports/G0-ESTEIRA-B.md`; revisão `template-r01`. Nenhuma medição preenchida.

Visita/data: ______  Responsável: ______  ID da máquina: ______  Sessão: ______

Copiar a ficha de cada item para cada grandeza/ponto. Manter leituras brutas e unidade por leitura; transferir para uma nova revisão YAML. Desconhecido = `null`/`BLOCKED`. Relatório comercial e r03 são `REFERENCE`, nunca `MEASURED`. Não montar suporte nem enviar comandos de impressora.

Catalogar fotos/arquivos com ID, caminho, autor, data, descrição e SHA-256 dos bytes originais (`sha256sum caminho`). Não estimar dimensão em foto sem escala, método e incerteza documentados.

## 1. Identificação

Registrar etiqueta, identificação local, fabricante/modelo verificados, responsável, data e local. Ausência de etiqueta é observação; fabricante desconhecido continua null.

Campos YAML: `machine_id, manufacturer, model`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 2. Fotos gerais

Vistas superior, laterais, entrada/saída e base acessível; etiqueta e detalhes. Registrar sentido da correia, XYZ e origem física recuperável, sem assumir datum.

Campos YAML: `files, xyz_directions, physical_origin`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 3. Dimensões do chassi

Medir comprimento, largura e altura entre extremos físicos identificados. Marcar pontos e posição de cada leitura na foto.

Campos YAML: `chassis_length, chassis_width, chassis_height`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 4. Furos existentes

Inventariar IDs, centro XYZ, diâmetro, espaçamento derivado e acesso à porca/ferramenta. Preservar ordem e associação das listas. Não supor rosca ou criar furo.

Campos YAML: `hole_inventory, hole_centres_xyz, hole_diameters`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 5. Espessura do acrílico

Verificar material; medir espessura em pontos identificados. Registrar trincas, flexão, distância às bordas e limitação do instrumento. Não aplicar aperto experimental.

Campos YAML: `acrylic_thicknesses, interface_material_evidence`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 6. Interfaces fixas

Separar chassi fixo de peças móveis. Documentar candidatos A/B/C, material e repetibilidade observável, sem aprovação estrutural. Registrar caminho de carga e retenção somente como candidatos.

Campos YAML: `fixed_interfaces, interface_bounds_xyz, interface_thicknesses, fastener_access, datum_A_candidate, datum_B_candidate, datum_C_candidate`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 7. Partes móveis e zonas proibidas

Mapear correia, roletes, motor, transmissão, cabos móveis, acesso e manutenção. Registrar limites XYZ e condições de movimento; nunca prender na correia.

Campos YAML: `belt_width, belt_bounds_xyz, moving_parts_and_forbidden_zones, forbidden_bounds_xyz`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 8. Envelope das câmeras

Registrar separadamente topo, lateral esquerda/direita, iluminação, conectores/cabos, linhas de visão e espaço livre. Envelopes de hardware real ou dummy identificado; mock-up r03 não fornece medidas.

Campos YAML: `camera_top_bounds_xyz, camera_left_bounds_xyz, camera_right_bounds_xyz, lighting_bounds_xyz, cable_bounds_xyz, retention_candidate`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 9. Trigger

Identificar sensor e montagem, plano de detecção, direção e distância até captura no XYZ documentado. Registrar limitação e repetibilidade do disparo.

Campos YAML: `trigger_identification, trigger_bounds_xyz, trigger_to_capture_distance`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 10. Encoder

Identificar montagem independente, mecanismo de leitura, contagens versus deslocamento físico de referência e slip. Não tratar encoder como datum óptico.

Campos YAML: `encoder_identification_and_mount, encoder_bounds_xyz, encoder_distance_per_count, encoder_slip`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 11. Velocidade e tracking

Registrar condição de carga, trechos/tempos, partida, frenagem, deriva lateral e vibração. Preservar séries brutas e referências; não inferir velocidade por ajuste do controlador.

Campos YAML: `belt_speed, startup_acceleration, braking_acceleration, tracking_lateral_displacement, vibration_amplitude, vibration_frequency`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 12. Massa/CG do dummy ou hardware

Identificar cada componente e configuração, medir massa e CG em XYZ com método descrito. Separar dummy de hardware; incluir iluminação, cabos e suportes quando presentes.

Campos YAML: `load_configuration, dummy_mass, dummy_cg_xyz, hardware_masses, hardware_cg_xyz`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 13. Instrumentos e incerteza

Inventariar ID, resolução, faixa, calibração/verificação, método, repetições brutas e base da incerteza por medição. Para observação qualitativa justificar not_applicable, nunca incerteza zero por padrão.

Campos YAML: `instrument_inventory_and_calibration`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |

## 14. Observações e anomalias

Registrar temperatura e local/condição de leitura, trincas, folgas, aquecimento, ruído, interferências, conflitos e inacessibilidade. Ausência de ocorrência deve ser observação explícita, nunca preenchimento automático.

Campos YAML: `observations_and_anomalies, temperature`.

| Registro | Preenchimento |
|---|---|
| Valor/observação e ID do ponto | ______ |
| Unidade | ______ |
| Instrumento/ID | ______ |
| Método e condição de ensaio | ______ |
| Repetição: número e leituras brutas | ______ |
| Incerteza, unidade e base | ______ |
| ID da foto/arquivo | ______ |
| Limitações/conflitos | ______ |
| Estado de evidência | BLOCKED |
