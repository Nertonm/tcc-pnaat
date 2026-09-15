# Expansão: sincronização física (trigger → captura)

Sistema de calibração do **atraso entre o trigger e a captura** e do **casamento entre a
velocidade da esteira e o ritmo do trigger**.

## Por que este módulo não tem número de PoC

O `docs/pocs/MAPA.md` registra `docs/pocs/03-sincronizacao-fisica` como **sem código**
("sincronização física com a esteira saiu do núcleo") e, no código entregue, `poc03_*` já é
**deformidade lateral**. Dar número novo criaria uma segunda numeração incompatível com o mapa;
por isso o módulo vive fora da série `pocNN_`, nomeado pelo que faz.

## O que ele resolve

```text
trigger (E18-D80NK) --d mm--> centro da ROI da câmera
                 garrafa anda a v mm/s

offset(τ) = v·τ − d        # posição da garrafa em relação ao centro da ROI
τ* = d / v                 # atraso que centra a garrafa
```

Uma rajada de quadros por passagem gera muitos pontos `(τ, offset)`. A reta ajustada entrega:

| Da reta | O que sai |
|---|---|
| inclinação | velocidade da esteira (no espaço da imagem) |
| raiz | **τ\***: o atraso de captura |
| intercepto + `d` medida a régua | escala mm/pixel do enquadramento |

Sem encoder e sem conhecer o mm/pixel de antemão.

## Arquivos

| Arquivo | Papel |
|---|---|
| `delay.py` | física, ajuste, orçamento de captura, janela de presença, veredito, leitura do delay |
| `tests/test_sincronizacao.py` | 15 testes; guardas de mutação e fail-closed do consumidor |
| `scripts/calibrar_delay_trigger.py` | instrumento (modos `log` e `simulado`) |
| `scripts/calibrar_delay_ensaio.sh` | ensaio de integração sem hardware (`make calibrar-delay-integracao`) |
| `docs/pocs/03-sincronizacao-fisica/CALIBRACAO-DELAY.md` | procedimento de bancada |

## Integração com quem captura

O resultado vai para `~/poc03/delay.json`, **por vista** (cada câmera tem a sua distância ao
trigger, logo o seu próprio atraso):

```json
{ "schema": "delay-trigger.v1",
  "vistas": { "topo": {"tau_s": 1.5005, "distancia_mm": 150, "velocidade_mm_s": 100.0,
                       "escala_mm_por_px": 0.5000, "residuo_mm": 0.33, "n_amostras": 114,
                       "passagens_com_amostra": 2} } }
```

Consumo pelo capturador (fail-closed: vista não calibrada **estoura**, não vira zero):

```python
from pocs.expansao_sincronizacao.delay import carrega_delay, tau_da_vista

delay = carrega_delay("~/poc03/delay.json")          # FileNotFoundError se não calibrado
t = tau_da_vista(delay, "topo")                      # KeyError se a vista não foi calibrada
captura_agendada(t)                                  # dispara t segundos após a borda do trigger
```

## Comandos

```bash
make calibrar-delay                  # física pura contra verdade conhecida (sem hardware)
make calibrar-delay-integracao       # caminho do ensaio: log isolado + câmera sintética
make calibrar-delay-bancada DIST=150 PASSOS=5   # bancada real (trigger + câmera)
```

## Invariantes

- **Uma porta serial, um dono.** O instrumento lê o log do supervisor (passivo), nunca a serial.
- **Uma câmera, um leitor.** `LeitorCamera` é thread única e só entrega quadros **novos**.
- **Fail-closed.** Só grava `delay.json` com veredito `PASS`; ensaio reprovado não calibra nada,
  e o consumidor estoura em vez de assumir default.
- **Amostra cortada não conta.** Item tocando a borda do quadro é descartado: o centróide mediria
  só o pedaço visível e o ajuste passaria a mentir.
- **Contagem honesta.** `n_amostras` vem sempre acompanhado de `passagens_com_amostra`: quadros de
  uma rajada são correlacionados.

## Limites

- O atraso é **extrapolado** se `τ*` cair fora da janela observada; o relatório avisa.
- Se o trigger estiver **fora do campo de visão**, nenhum quadro válido sobra e o ensaio reprova
  (é diagnóstico, não bug): aproxime a câmera, abra a lente ou reduza `d`.
- Depende de câmera com exposição e foco travados (protocolo de captura do núcleo).

## Verificação (2026-09-14)

| Ensaio | Resultado |
|---|---|
| Verdade conhecida (120 amostras) | r² 0,9998; erro 0,1% em τ\* e v |
| Régua mentida (declarar 300 mm com verdade 150) | erro 99,9% → REPROVA, não aplica |
| Caminho do ensaio (log real + câmera sintética) | 2 vistas, erro 0,0%, `delay.json` acumulado |
| Caso infeasível (janela < τ\*) | REPROVA com exit 1 e nenhum delay aplicado |
| Suíte do repositório | 110 passed |
