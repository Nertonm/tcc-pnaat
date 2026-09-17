# Calibração: atraso trigger → captura e casamento da velocidade

Procedimento de bancada do sistema `code-workspace/src/pocs/expansao_sincronizacao/` + `code-workspace/scripts/calibrar_delay_trigger.py`.
Status: sistema entregue e verificado em 2026-09-14 (ver seção de evidências).

## O problema, em uma linha

O sensor está a `d` mm do centro da ROI da câmera. Se a captura disparar no instante do trigger,
a garrafa ainda está `d` mm antes; se disparar tarde, ela já passou. O instante certo é
`τ* = d / v` — e nem `v` nem o mm/pixel são conhecidos a priori.

## Fase 0 — antes de medir (não pular)

| # | Item | Critério |
|---|---|---|
| 0.1 | Medir `d` com régua/paquímetro: do **plano de detecção** do E18-D80NK ao **centro da ROI** da câmera | número em mm registrado no comando |
| 0.2 | **O trigger tem de estar dentro do campo de visão da câmera** | se o item nunca aparecer inteiro no quadro, não há posição para medir |
| 0.3 | Câmera com exposição, foco e WB **travados** | sem auto-exposição variando durante a rajada |
| 0.4 | Iluminação fixa e registrada | mesma configuração entre passagens |
| 0.5 | Esteira vazia para a referência | o instrumento grava `~/poc03/referencia-esteira-vazia.jpg` |
| 0.6 | Supervisor da PoC-01 ativo (dono único da serial) | log recebendo `EV OPEN` |
| 0.7 | Nenhum outro processo com `/dev/videoN` aberto | câmera tem um leitor |

A janela da rajada deve cobrir o cruzamento: `--janela ≥ τ*` (com folga). Janela curta demais
transforma a medição em extrapolação — e o relatório avisa quando isso acontece.

## Fase 1 — rodar a calibração (uma vez por vista)

```bash
cd <TCC_HOME>
make calibrar-delay-bancada DIST=150 PASSOS=5                 # vista padrão: "principal"
# ou, com o nome da vista (cada câmera tem o seu próprio atraso):
<TCC_HOME>/.venv/bin/python code-workspace/scripts/calibrar_delay_trigger.py \
    --fonte log --vista topo --distancia-mm 150 --passagens 5 --janela 2.2 --aplicar
```

Passe 5 itens. Cada `EV OPEN` abre uma rajada de `--janela` segundos; os quadros são amostras
`(τ, offset)` e a reta sai dos quadros de todas as passagens.

## Fase 2 — ler o veredito

**PASS** exige: `n ≥ 5` amostras, `r² ≥ 0,9`, resíduo ≤ `--tolerancia-mm` e `τ* > 0`.
Só com PASS o `delay.json` é gravado. O relatório traz `τ*`, velocidade medida, escala mm/px,
resíduo, contagem de descartes e o envelope de velocidade.

Avisos que não devem ser ignorados:

- **`τ*` fora da janela observada** → número extrapolado: aumente `--janela` e recalibre.
- **`intercepto não negativo`** → sinal do offset ou distância declarada errados.
- **Ensaio reprovado com corte na borda** → suspeita de trigger fora do campo de visão.
- **`descartes: cortado_na_borda`** → normal no início da rajada (o item ainda está entrando);
  só é problema quando nenhum quadro válido sobra.

## Fase 3 — o envelope: que velocidade a esteira pode ter

O teto é o **menor** entre três limites, todos medidos:

| Limite | Fórmula | Com os números do rig |
|---|---|---|
| Orçamento de captura | `passo / (vistas × tempo_por_vista + rearme + margem)` | 80 / (3×0,077 + 0,5 + 0,02) = **107 mm/s** |
| Re-armadura do trigger | `passo / 0,5 s` (ARM_MS=500, GUARD_MS=500) | 80 / 0,5 = 160 mm/s |
| Janela de presença | `comprimento / 0,1 s` (STABLE_READS=5 × DEBOUNCE_MS=20) | 60 / 0,1 = 600 mm/s |

Com passo de 80 mm, **manda o orçamento de captura: ~107 mm/s**. Para correr mais rápido é preciso
aumentar o passo (mais espaço entre itens) ou reduzir o número de vistas — subir a velocidade sem
mexer nisso faz o trigger perder garrafas.

## Fase 4 — usar o atraso

`~/poc03/delay.json` guarda **uma entrada por vista** (`tau_s`, `distancia_mm`, velocidade medida,
escala, resíduo, contagens). O capturador lê com `carrega_delay()` + `tau_da_vista(nome)` e agenda a
captura `tau_s` após cada borda de trigger. Vista não calibrada → `KeyError` (não há default).

## Verificação sem hardware

```bash
make calibrar-delay              # física pura contra verdade injetada
make calibrar-delay-integracao   # caminho do ensaio: log isolado + câmera sintética
```

O ensaio de integração usa um log de ensaio próprio (`~/poc03/log-ensaio.log`, no formato do
supervisor) — **nunca** o log real — e cobre: duas vistas acumulando no `delay.json`, o caso
infeasível (janela menor que τ\*, que tem de reprovar) e o consumo fail-closed.

Evidências de 2026-09-14:

| Ensaio | Resultado |
|---|---|
| Verdade conhecida | r² 0,9998, resíduo 1,44 px, erro 0,1% em τ\* e v |
| Régua mentida (300 mm declarados, 150 reais) | erro 99,9% → reprova e não aplica |
| Caminho do ensaio, vista topo (d=150) | erro 0,0% contra verdade, 114 amostras em 2 passagens |
| Caminho do ensaio, vista lateral1 (d=220) | erro 0,0%, τ\*=2200 ms, sem apagar a vista topo |
| Caso infeasível (d=300, janela 1,2 s) | reprova, exit 1, nenhum delay aplicado |
| Suíte do repositório | 112 passed (estado 18/09) |
