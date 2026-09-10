# code-workspace — PoCs do Cenário 1 (Inspeção de envase)

Código de validação das PoCs da Entrega 1. Foco: visibilidade e rastreabilidade de
anomalias (tampa ausente, tampa mal rosqueada, deformidade do corpo) em linha de envase.
Sem atuacao fisica, sem controle de velocidade da esteira; nucleo de nó unico + registro
local (MQTT/multi-nó são expansão).

Mapa PoC -> artefato de código
- PoC-01 captura multi-view   -> (hardware) trigger de presenca + vistas; andaime em src/pnaat_pocs/events.py
- PoC-02 classificacao de tampa  -> (visao) matriz de confusao; RNF-02
- PoC-03 deformidade lateral    -> (visao) metrica dimensional; RNF-02
- PoC-04 identidade e fusao     -> src/pnaat_pocs/fusion.py  (regra deterministica; empate -> analise humana)
- PoC-05 registro local         -> src/pnaat_pocs/registry.py (upsert idempotente, reconcile)
- PoC-06 resiliencia            -> src/pnaat_pocs/resilience.py (retry contado, alerta)
- PoC-07 dashboard              -> src/pnaat_pocs/dashboard.py (consulta e recorrencia)
- PoC-Final conjectura integrada -> tests/ end-to-end (registro+dashboard)

Comandos
- instalar: python3 -m venv .venv && .venv/bin/pip install -e . pytest
- testar:   make test  (roda pytest)
