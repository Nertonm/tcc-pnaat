# code-workspace: PoCs do Cenário 1 (Inspeção de envase)

Código de validação das PoCs do projeto. Foco: visibilidade e rastreabilidade de
anomalias (tampa ausente, tampa mal rosqueada, deformidade do corpo) em linha de envase.
Sem atuacao fisica, sem controle de velocidade da esteira; nucleo de nó unico + registro
local (MQTT/multi-nó são expansão).

Para preparar e gravar a Entrega 2, incluindo o estado real de cada PoC, limitações e roteiro de
narração, consulte [`src/pocs/ROTEIRO-GRAVACAO.md`](src/pocs/ROTEIRO-GRAVACAO.md).

Mapa PoC -> artefato de código
- PoC-01 captura multi-view   -> src/pocs/poc01_trigger (debounce + janela; ESP32: esp/main.py)
- PoC-02 classificacao de tampa  -> src/pocs/poc02_classificacao (matriz de confusao; RNF-02)
- PoC-03 deformidade lateral    -> src/pocs/poc03_deformidade (calibracao pixel->mm; RNF-11/RNF-14)
- PoC-04 identidade e fusao     -> src/pocs/poc04_fusao  (fusao POR DOMINIO: defeito nao e
                                 cancelado, topo so veta/escala, evidencia insuficiente -> inconclusivo)
- PoC-05 registro local         -> src/pocs/poc05_registro (upsert idempotente, reconcile)
- PoC-06 resiliencia            -> src/pocs/poc06_resiliencia (retry contado, alerta)
- PoC-07 dashboard              -> src/pocs/poc07_dashboard (consulta e recorrencia)
- PoC-08 pre-processamento      -> src/pocs/poc08_preproc (flat-field, alinhamento, extração de geometria)
- PoC-Final conjectura integrada -> src/pocs/pocfinal (trigger->fusao->registro->dashboard)

Comandos
- instalar: `make install` (cria o venv único na raiz do clone) ou `python3 -m venv ../.venv && ../.venv/bin/python -m pip install -e ".[dev]"`
- testar:   `make test`
- PoC-04:   `make poc04` (harness de casos declarados; sai != 0 se divergir do esperado)
- calibrar atraso trigger->captura: `make calibrar-delay` (física pura), `make calibrar-delay-integracao` (caminho do ensaio sem hardware) ou `make calibrar-delay-bancada DIST=150 PASSOS=5` (bancada real)

Ambiente de referencia: Python 3.11 em venv unico na raiz do clone do projeto (CPU, visao e serial).
O `Makefile` resolve o interpretador sozinho: usa `../.venv/bin/python` quando existe e cai para
`.venv/bin/python` ou `python3` caso contrario.
