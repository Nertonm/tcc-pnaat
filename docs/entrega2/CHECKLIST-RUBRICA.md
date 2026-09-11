# Checklist da Entrega 2 (rubrica) — o que o vídeo precisa provar

Rubrica: Ausente 0 · Insuficiente 0,3 · Básico 0,6 · **Adequado 0,9** · **Avançado 1,2**.

## Mapa critério → evidência no nosso vídeo

| Critério da rubrica | Como aparece no vídeo | Onde está no material |
|---|---|---|
| **Entrada utilizada ou início da execução** | garrafa real + frames do ensaio; leituras do sensor E18-D80NK abrindo a janela de captura | `make demo` passos `[1/7]` e `[2/7]`; `poc01_trigger/esp/main.py` |
| **Funcionamento da tecnologia principal** | pré-processamento determinístico (ROI, alinhamento, métricas), modelo one-class treinado só com normais, decisão por domínio com gate de qualidade | passos `[3/7]` a `[5/7]`; `poc08_preproc`, `treinar_dataset.py` |
| **Resultado produzido** | decisão por item (normal / suspeita / inconclusivo) + registro local + dashboard com todos os itens | passos `[6/7]` e `[7/7]`; `demo/saida/dashboard.html`, `registro.json` |
| **Corresponde à parte central da solução** | visão computacional (o cenário é inspeção de envase): entrada de imagem → processamento → resultado | `docs/escopo.md`, `latex-workspace` (Entrega 1) |
| **Avançado: mesma sequência acompanhável** | **uma** execução de `make demo`, sem corte, do gatilho ao dashboard | roteiro, blocos 2–4 |
| **Avançado: núcleo + outro elemento da arquitetura** | gatilho (ESP32/E18) + câmera + registro/dashboard junto do núcleo de visão | passos `[1/7]`, `[6/7]` |
| **Avançado: explica entrada, funcionamento, resultado e função dos elementos** | bloco 5 do roteiro (tabela falada elemento → papel) | roteiro, bloco 5 |
| **Avançado: identifica o próximo passo / o não integrado** | bloco 6: medição da tampa em validação, pares de defeito pendentes, integração no Pi 5 | roteiro, bloco 6 |

## Armadilhas que derrubam o nível (evitar)

- **Intervenção manual no meio** (Básico): rode uma vez; se algo falhar, corrija antes de gravar.
- **Resultado que não aparece** (Insuficiente/Básico): o vídeo precisa **mostrar** a decisão e o
  registro — não só o terminal rolando.
- **Prometer o que não roda**: não chamar a geometria da tampa de "medição pronta" nem apresentar a
  perturbação de controle como defeito real. Dizer o status é o que fecha o nível Avançado.
- **Vídeo público por engano**: subir como **não listado** e conferir na entrega.

## Estado real do material (conferido no ensaio)

| Item | Estado |
|---|---|
| Frames reais | 81 normais (ensaio na bancada) |
| Modelo one-class | treinado apenas com normais; limiar derivado dos dados (média + 3σ) |
| Perturbações de controle | 2 (oclusão e risco) com máscara e bbox registrados |
| Geometria da tampa | contorno detectado; **medição em validação** (rig v0 sem backlight) |
| Defeito real | **não existe** no dataset → acurácia com defeito fica como próximo passo |
| Hardware no ensaio | Pi 5/ESP32 não plugados na bancada atual → gatilho demonstrado por firmware + evento |

## Medições desta rodada (evidência para a banca)

| Medida | Valor |
|---|---|
| Itens processados no demo | 5 (3 normais + 2 controles) |
| Normais (81) — max(mapa) | média 0,1254 · máx 0,5636 · p99 0,4800 |
| Limiar bruto derivado | **0,4820** |
| Controle de risco | 1,0000 → suspeita (2,07× o limiar) |
| Controle de oclusão suave | 0,1574 → não detectado (limitação declarada) |
| Qualidade de captura | Tenengrad ≈ 105 · especular ≈ 0,005% · CNR tampa/corpo ≈ 0,59 |
| Geometria da tampa | contorno detectado; medição **em validação** |
