# PoC-01: Trigger de presença (E18-D80NK + ESP32)

Verifica o critério de captura do núcleo: **cada passagem do item abre UMA janela de captura, com mais de
uma vista e timestamps, sem duplicar e sem janela espúria.**

## Arquivos e responsabilidades

| Camada | Arquivo | Papel |
|---|---|---|
| Firmware (roda no board) | `esp/main.py` | ISR de presença com debounce, arming só em repouso, guarda anti-duplicação, log `EV ...` e CSV no board |
| Documentação do sensor | `esp/README.md` + `docs/reference/ref-e18-d80nk-sensor.md` | fiação (bege=+5V, preto=sinal, azul=GND), datasheet, procedimento de bancada |
| Lógica pura (testada) | `presence.py` | mesma máquina de estados, sem hardware (usada pelos testes de desktop) |
| Simulador sem hardware | `scripts/simular_trigger.py` | roda o fluxo no PC (`make simular-poc01`) para comparar com o board |
| **Lane de host** | `scripts/poc01_supervisor.py` | **dono único da porta serial**; republica em `~/poc01/stream.log`; solta a porta quando existe `~/poc01/PAUSA` |
| | `scripts/poc01_escopo.py` | escopo ao vivo do 1 bit + taxa de bordas (ver como o sensor capta) |
| | `scripts/poc01_teste.py` | harness com protocolo de N passagens e **veredito PASS/FAIL** + JSON de evidência |
| | `scripts/poc01_watch.py` | visualizador legível (passivo: lê o stream, nunca a porta) |
| | `scripts/esp_tool.py` | upload/pull/rm/run no board via raw REPL (pausa o supervisor automaticamente) |

> Nota de organização: o firmware vive **dentro** de `src/pocs/poc01_trigger/`; as ferramentas de host
> estão em `code-workspace/scripts/` (versionadas, com prefixo `poc01_`). Consolidação em
> `src/pocs/poc01_trigger/host/` fica como melhoria: depende de recriar as unidades systemd do
> ambiente em uso.

## Arquitetura de operação (por que não há mais conflito)

```
ESP32 (main.py, roda sozinho)
   └─ serial /dev/ttyUSB0 ──► poc01_supervisor.py   (ÚNICO dono da porta)
                                   └─ ~/poc01/stream.log ◄── poc01_escopo.py   (passivo)
                                                         ◄── poc01_teste.py    (passivo)
                                                         ◄── poc01_watch.py    (passivo)
                                                         ◄── tail -f           (passivo)
   upload de firmware: esp_tool cria ~/poc01/PAUSA → supervisor solta a porta → grava → remove PAUSA
```

Lição de método registrada: a porta serial é recurso exclusivo; antes, subir firmware exigia parar o
visualizador (e a janela de quem acompanhava morria). Agora existe **um dono** e **N visualizadores
passivos**, e o upload é coordenado por sentinela: nunca matando processos de terceiros.

## Como rodar o teste (evidência isolada)

```bash
cd ~/tcc-pnaat/github/code-workspace
$HOME/.venvs/esp/bin/python scripts/poc01_teste.py --passagens 10 --espera 6 --separacao 3
```

Saída: tabela por passagem (`OK` / `PERDIDA` / `DUPLICATA`), janelas fora de passagem, descartes da
guarda e **VEREDITO**. Evidência em `~/poc01/evidencia-poc01.json`.

Roteiro de gravação do vídeo com esteira: O roteiro de gravacao fica fora do repositorio.
evidência: PoC-01 isolada").

---

# PoC-01: Captura multi-view (gatilho de presença)

| | |
|---|---|
| **Ideia isolada** | se a passagem do item nao abrir exatamente UMA janela de captura, com as vistas associadas ao mesmo item, toda a cadeia a jusante trabalha sobre dado errado |
| **Pergunta** | o evento de presenca abre janela para mais de uma vista do mesmo item, sem duplicidade? |
| **Hipotese** | sensor de presenca com janela nao bloqueante e debounce produz uma janela por item, mesmo com ruido de borda e itens proximos |
| **Metodo** | 10 passagens na esteira; contar janelas abertas, janelas espurias, duplicatas e vistas por evento; registrar timestamp por item |
| **Criterio de passagem** | mais de uma vista do MESMO evento com identidade e timestamp; uma janela por passagem, sem janela espuria |
| **Evidencia** | log de eventos por item (timestamp, vistas) + as imagens associadas |
| **Limite atual** | a coleta do ensaio e por bancada; sincronizacao com a esteira e multi-no ficam fora deste recorte; o sensor e componente candidato (D-20) e o gatilho esta simulado no demo |
| **Dependencias** | RF-01, RF-01.1, RNF-08; D-19 (papel do ESP32), D-20 (sensor candidato) |
| **Codigo** | `esp/main.py`, `presence.py`, `scripts/poc01_teste.py`, `scripts/poc01_escopo.py`, `scripts/simular_trigger.py` |
