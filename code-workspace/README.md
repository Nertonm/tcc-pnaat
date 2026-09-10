# code-workspace — PoCs do Cenário 1 (Inspeção de envase)

Código de validação das PoCs da Entrega 1. Foco: visibilidade e rastreabilidade de
anomalias (tampa ausente, tampa mal rosqueada, deformidade do corpo) em linha de envase.
Sem atuacao fisica, sem controle de velocidade da esteira; nucleo de nó unico + registro
local (MQTT/multi-nó são expansão).

Mapa PoC -> artefato de código
- PoC-01 captura multi-view   -> src/pocs/poc01_trigger (debounce + janela; ESP32: esp/main.py)
- PoC-02 classificacao de tampa  -> src/pocs/poc02_classificacao (matriz de confusao; RNF-02)
- PoC-03 deformidade lateral    -> src/pocs/poc03_deformidade (calibracao pixel->mm; RNF-11/RNF-14)
- PoC-04 identidade e fusao     -> src/pocs/poc04_fusao  (regra deterministica; empate -> analise humana)
- PoC-05 registro local         -> src/pocs/poc05_registro (upsert idempotente, reconcile)
- PoC-06 resiliencia            -> src/pocs/poc06_resiliencia (retry contado, alerta)
- PoC-07 dashboard              -> src/pocs/poc07_dashboard (consulta e recorrencia)
- PoC-Final conjectura integrada -> src/pocs/pocfinal (trigger->fusao->registro->dashboard)

Comandos
- instalar: python3 -m venv .venv && .venv/bin/pip install -e . pytest
- testar:   make test  (roda pytest)
