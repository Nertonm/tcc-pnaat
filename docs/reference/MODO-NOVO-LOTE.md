# Modo de execução — lote novo

Preparado em 2026-09-15. **Nada aqui foi executado nem iniciado**: é o modo pronto para o
próximo lote de anotações da equipe.

## Quando usar

Quando a equipe fechar um lote novo no Label Studio (mais fotos classificadas). Um lote é
"novo" se o export mudou — se não mudou, treinar produz um número novo para o mesmo modelo,
o que é pior que não treinar: parece progresso e não é.

## Comando

```
cd <raiz do repo>
bash dataset/TRABALHO/filas/novo_lote.sh <TAG> [--kfold]
# exemplo:
bash dataset/TRABALHO/filas/novo_lote.sh v10 --kfold
```

`<TAG>` vira o nome dos artefatos (`v10-lateral-detector-roi`, `ENTREGA/v10-lateral/`).

## O que ele faz, e a trava de cada passo

| # | Passo | Trava que impede resultado enganoso |
|---|-------|-------------------------------------|
| 1 | export do Label Studio | **frescor**: aborta se nenhum export tem menos de `LOTE_HZ` (padrão 2h) |
| 2 | monta dataset | rótulos **no espaço do recorte** (o bug de hoje valia ~0,19 de mAP50) |
| 3 | aumenta 3x o treino | blur calibrado na nitidez medida das câmeras (rig 14,7 · usb 155,1 · espcam 377,6) |
| 4 | treina | guardião: temperatura de GPU, RAM, swap, durabilidade em disco |
| 5 | limiares | calibrados na **validação**; F1 por classe reportado no **teste** |
| 6 | k-fold | barra de erro por item (sem ele não há como comparar lotes) |
| 7 | pacote | peso + SHA256SUMS em `ENTREGA/<TAG>-lateral/` |

## Depois do lote: produção é passo de operador

O runner **não** sobe inferência. Para um lote virar produção:

```
scp ENTREGA/<TAG>-lateral/<TAG>-lateral.pt <alvo>:$ACEROLA_MODELOS/
# no host de inferencia: trocar o MODEL_NAME da unit pnaat-v0-yolo.service e reiniciar
```

Decisão humana, com o número do lote na mão — não automática.

## Sinais de que o lote não serve (e o certo é dizer isso, não forçar)

- k-fold pior que o lote anterior → o dado novo não ajudou; investigar antes de promover
- F1 de `defeito_tampa` caiu → checar se a equipe anotou com o mesmo critério
- contagem de itens quase igual à do lote anterior → provavelmente é o mesmo lote
