# Roteiro do vídeo — Entrega 2 (Apresentação da PoC)

Alvo: **nível Avançado (1,2)**. Duração sugerida: **4 a 5 min**, um take, sem corte que esconda
etapas. Vídeo **não listado** no YouTube. Uma execução só, do gatilho ao dashboard.

Regra que a rubrica cobra: **entrada → execução → resultado na MESMA sequência acompanhável**,
com **outro elemento da arquitetura** além do núcleo, explicando o papel de cada elemento, e
**identificando o próximo passo / o que ainda não está integrado**.

## Preparação (antes de gravar)

1. Terminal na maquina de trabalho (fonte grande, tema escuro), janela do visualizador de imagens ao lado.
2. Deixe aberto: `code-workspace/` e a pasta `demo/saida/`.
3. Rode uma vez para aquecer (a primeira predição carrega o modelo): `make demo` — depois apague
   `demo/saida/` para o take ficar limpo.
4. Tenha em mãos (para mostrar, se o kit estiver por perto): ESP32-CAM + sensor E18-D80NK + a
   garrafa usada no ensaio. Se não estiver, o vídeo mostra o **firmware** (`poc01_trigger/esp/main.py`)
   e o **evento de gatilho** rodando — diga isso em voz alta, sem fingir bancada.

## Bloco 1 — Abertura (0:00–0:25)

Fala sugerida:
> "Este é o TCC PNAAT — inspeção automatizada de envase com rastreabilidade. O problema: a linha
> precisa saber, por item, se a tampa está ausente, mal rosqueada ou se o corpo está deformado, e
> guardar essa informação. Nesta entrega eu vou provar que a tecnologia central funciona: um pipeline
> de visão com pré-processamento determinístico, um modelo de anomalia treinado só com itens normais,
> e o registro com dashboard. Não é o projeto pronto — é a prova de viabilidade."

Na tela: mostrar a garrafa/frame real que será usada (abra `frame_0000.jpg`).

## Bloco 2 — Entrada (0:25–1:00)

- Mostrar **a entrada física**: a garrafa + (se houver) ESP32/E18. Diga o papel do gatilho:
  "o sensor E18-D80NK avisa que o item entrou no campo; o ESP32 faz o debounce e abre a janela de
  captura — é o que impede contar o mesmo item duas vezes".
- Mostrar rapidamente `poc01_trigger/esp/main.py` (firmware) e/ou o começo do `make demo`, onde as
  leituras lógicas do sensor aparecem (`nível=0 → PRESENTE`).

## Bloco 3 — Execução (1:00–2:20)

Rodar **uma única vez**:

```bash
cd ~/tcc-pnaat/github/code-workspace
make demo
```

Narre cada etapa conforme aparecem (os títulos `[1/7] … [7/7]` guiam a fala):

1. **ENTRADA 1/2 — gatilho**: leituras do sensor e abertura da janela multi-view.
2. **ENTRADA 2/2 — item real**: nome e `sha256` de cada frame (é o ensaio na bancada).
3. **FUNCIONAMENTO 1/3 — pré-processamento**: ROI da tampa (topo), ROI do corpo, alinhamento,
   métricas (Tenengrad = foco, cobertura especular, CNR).
4. **FUNCIONAMENTO 2/3 — modelo**: one-class (PatchCore) treinado **só com as 81 normais**;
   aparece o limiar derivado dos próprios dados (média + 3σ).
5. **FUNCIONAMENTO 3/3 — análise + decisão**: por item, `score` vs `limiar` e a decisão.
6. **RESULTADO 1/2 — registro + dashboard**: eventos gravados no registro local e o resumo.
7. **RESULTADO 2/2 — o que provou e o que falta**.

## Bloco 4 — Resultado (2:20–3:10)

Abra os arquivos gerados em `demo/saida/`:

- `frame_XXXX_anotado.png`: ROI, contorno detectado e métricas sobre a imagem.
- `frame_XXXX_controle_oclusao_mapa.png`: **mapa de anomalia** na frame com perturbação de controle.
- `dashboard.html`: a tabela com todos os itens processados.

Fala sugerida:
> "O resultado por item é uma decisão: normal, suspeita de anomalia ou inconclusivo quando a captura
> não tem qualidade suficiente — inconclusivo nunca vira aprovação silenciosa. Aqui, as frames
> normais do ensaio ficam abaixo do limiar. Esta outra imagem é uma **perturbação de controle** que eu
> gerei por script — não é defeito real — e serve para mostrar que o modelo reage a uma anomalia com
> verificação: o chão de verdade dessa região está registrado no JSON."

## Bloco 5 — Explicação dos elementos (3:10–4:00) — exigência do nível Avançado

Fale o papel de cada elemento mostrado:

| Elemento | Papel na arquitetura |
|---|---|
| Gatilho E18-D80NK + ESP32 | entrada: detecta a passagem, faz debounce e abre a janela de captura por item |
| Câmera (frame real) | entrada: evidência visual por item |
| Pré-processamento determinístico | padroniza a entrada (ROI, alinhamento, métricas de qualidade) — barato e reprodutível |
| Modelo one-class | núcleo de aparência: aprende só o normal e sinaliza desvio |
| Decisão por domínio + gate de qualidade | regra explícita; evidência insuficiente → inconclusivo |
| Registro local + dashboard | rastreabilidade e observabilidade por item (é o que a linha consome) |

## Bloco 6 — Próximo passo (4:00–4:40)

Fala sugerida:
> "O que ainda **não** está integrado: primeiro, a medição dimensional da tampa — o contorno é
> detectado, mas a medida ainda não é confiável com a óptica atual, e eu prefiro dizer isso a mostrar
> um número bonito; o passo é o rig v1 com backlight e a calibração pixel→milímetro. Segundo, os
> pares de defeito — o dataset hoje tem apenas itens normais, então o acerto ainda não é medido com
> defeito real. Terceiro, a integração final no Raspberry Pi 5 com o firmware do ESP32."

## Ficha do vídeo (YouTube, não listado)

- **Título**: `PNAAT TCC — PoC 1: inspeção de envase (visão + one-class + rastreabilidade)`
- **Descrição**: problema tratado, o que é mostrado (entrada → execução → resultado), o que ainda não
  está integrado, e o link do repositório.
- **Visibilidade**: `Não listado`. Copiar o link e colar no campo de entrega.

## Checklist de 10 segundos antes de publicar

- [ ] a entrada aparece (garrafa/gatilho) antes da execução;
- [ ] a execução corre do começo ao fim **sem intervenção manual** no meio;
- [ ] o resultado aparece (decisão por item + registro/dashboard);
- [ ] o papel dos elementos foi explicado em voz alta;
- [ ] o próximo passo / o que não está integrado foi dito;
- [ ] vídeo **não listado** e link colado na entrega.


## Resultados reais medidos (use estes números na narração)

Execução de referência (`make demo`, 5 itens = 3 normais + 2 controles):

| item | max(mapa) | decisão |
|---|---|---|
| frame_0000 (normal) | 0,1571 | normal |
| frame_0001 (normal) | 0,0621 | normal |
| frame_0002 (normal) | 0,1193 | normal |
| controle **oclusão** | 0,1574 | normal (**não** detectado) |
| controle **risco** | **1,0000** | **suspeita de anomalia** |

- Modelo: PatchCore treinado **só com as 81 normais**; limiar derivado dos próprios normais
  (p99 = 0,4800 → **limiar bruto = 0,4820**); normais medidas: média 0,1254, máx 0,5636.
- **Fala recomendada sobre o controle de oclusão**: "esta perturbação suave **não** foi detectada —
  e eu mostro isso de propósito: significa que o defeito sintético que eu gerar precisa de
  frequência espacial e contraste adequados, não basta 'parecer óbvio' para o olho humano."
- **Achado técnico a citar** (mostra rigor): o `pred_score` padrão do anomalib 2.6.1 **satura**
  (0 ou 1) por normalização com os limites do conjunto; trocamos o sinal para o **máximo do mapa
  de anomalia cru**, que é comparável entre itens — e derivamos o limiar nos normais.

---

# Captura de evidência — PoC-01 isolada (esteira + garrafas)

Objetivo deste bloco: provar, **em vídeo e com veredito automático**, que a PoC-01 funciona isolada —
cada passagem do item abre **uma** janela de captura, com vistas e timestamps, sem duplicar e sem
janela espúria (é o critério da Entrega 1 para a PoC-01).

## Preparação (antes de gravar)

1. **Esteira** ligada em velocidade baixa, com as garrafas passando pela frente do sensor.
2. **Garrafas**: 10 da mesma série (sugestão: 5 vazias + 5 cheias).
3. **Sensor** fixado a ~15 cm do caminho, apontado para o **corpo/tampa** da garrafa, com fundo
   **fosco escuro** atrás (parede/mesa clara reflete IR e mantém a linha disparada).
4. **Potenciômetro ajustado** — condição de partida obrigatória: a janela `SENSOR (ao vivo)` deve
   mostrar `nivel=1` em repouso e **`bordas=0.0/s`**. Se `bordas` estiver alto, o alcance está grande
   demais (é o "sensível demais") e o teste vai acusar duplicata.
5. **Três janelas abertas** (já criadas):
   - `PNAAT PoC-01 — SENSOR (ao vivo)` → escopo do 1 bit e taxa de bordas;
   - `PNAAT PoC-01 — TESTE (veredito)` → protocolo e resultado;
   - um terminal com `tail -f ~/poc01/stream.log` (timeline crua com carimbo de hora).

## Roteiro de gravação (5 blocos, ~3–4 min, um take)

1. **Bancada (15 s)** — mostre esteira, sensor e as garrafas. Uma frase de objetivo: "vou provar que
   o gatilho de presença abre uma janela por item, sem duplicar".
2. **Repouso (20 s)** — mostre o escopo com `nivel=1` e `bordas=0.0/s`: "o sensor está ajustado, não
   dispara sozinho".
3. **Início do teste (15 s)** — na janela `TESTE`, pressione **Enter**. Narre o que aparece:
   "ele está armado e vai pedir 10 passagens".
4. **As 10 passagens (90 s)** — coloque as garrafas na esteira respeitando o ritmo que a tela pede
   (`PASSAGEM k/10: aproxime agora` → `afaste e aguarde 3 s`). Alterne **vazia/cheia**. Deixe o
   escopo visível enquanto passa: dá para ver `nivel` cair para `0` e voltar a `1` a cada item.
5. **Resultado (40 s)** — pare na tabela final e leia em voz alta: passagens OK, perdidas,
   duplicatas, espúrias e o **VEREDITO: PASS**. Abra `~/poc01/evidencia-poc01.json` e o trecho do
   `stream.log` com `EV OPEN n=…`/`EV CLOSE dur_ms=…` — é a prova por item.
6. **Fechamento (20 s)** — diga o que isso prova (gatilho + contagem por item, sem duplicidade) e o
   que **ainda não** está integrado (a janela ainda não dispara câmera; a captura multi-view entra na
   etapa seguinte).

## Critério de aceite (o que o vídeo precisa mostrar)

| Condição | Como aparece |
|---|---|
| 10 passagens → 10 janelas | tabela do harness: 10 linhas `OK` |
| Sem duplicidade | coluna `janelas` = 1 em todas as linhas; `descartadas` pode ser >0 (a guarda atuou) |
| Sem janela espúria | linha `janelas fora de passagem: 0` |
| Item identificado e datado | cada linha traz `detectado` (hora) e `vistas` (topo,lateral1,lateral2) |
| Veredito automático | `VEREDITO: PASS` na tela |

Se aparecer `FAIL`, a causa provável está impressa pelo próprio harness:
`PERDIDA` → aproxime mais / reduza o alcance; `DUPLICATA` → potenciômetro no limite (veja `bordas/s`);
`espúria` → algo entrou no campo fora da passagem.

## Evidências a preservar (fora do git — política de mídia)

- `~/poc01/evidencia-poc01.json` — veredito + tabela por passagem (fonte primária do resultado);
- `~/poc01/stream.log` — timeline bruta com carimbo do host (o que a câmera não mostra);
- `code-workspace/poc01_passagens.csv` — tradução do visualizador;
- `poc01_events.csv` **no board** — log persistente do firmware (sobrevive a reset);
- vídeo bruto + link do vídeo **não listado** publicado.

## Enquadramento (para o vídeo ser "acompanhável" na rubrica)

- Film e a **esteira e a tela no mesmo quadro** (ou picture-in-picture): entrada e execução juntas.
- Sem corte entre "iniciar o teste" e a leitura do veredito — é o que separa o nível Avançado.
- Narração contínua: entrada (garrafa na esteira) → execução (escopo + stream) → resultado (tabela).
