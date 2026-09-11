# Prompt: gerar defeito sintético em foto de garrafa (dataset) — UM por foto

Cole o texto abaixo junto com **UMA foto por vez** (a foto original, 640×480, câmera fixa do rig).

---

## Contexto

Você vai ajudar a montar um dataset de inspeção de garrafas (linha de envase).
Este dataset é **validado automaticamente**: só entram os pares cuja edição for **isolada** na
região do defeito. Regerar a cena inteira, reescalar ou reenquadrar faz o par ser **rejeitado**.

## O que entregar (nesta ordem)

**1) O PATCH do defeito (entrega principal)** — não a imagem inteira:
- Um recorte **PNG com canal alfa** contendo **somente** a região defeituosa, na **mesma escala
  1:1** da foto enviada (ex.: se a região tem 80×70 px na foto, o patch deve ser 80×70 px, mais
  uma margem de 8–16 px ao redor para mesclagem).
- Fora do defeito o patch deve ser **transparente** (alfa = 0). O defeito deve parecer fotografado
  na mesma iluminação/sombra/reflexo da foto.
- Nome: `<classe>_<nome_original_sem_ext>_patch.png`.

**2) O JSON de controle** — nome **exatamente** `<nome_da_imagem>.json`, ao lado da imagem:
```json
{
  "classe": "tampa_ausente | tampa_mal_rosqueada | deformidade",
  "regiao": [x, y, w, h],
  "arquivo_saida": "<nome exato da imagem de saída>",
  "arquivo_original": "<nome exato da foto que eu enviei>",
  "patch": "<nome exato do patch PNG>",
  "descricao": "texto curto do defeito"
}
```
- **`regiao` em coordenadas da FOTO ORIGINAL** (0..largura-1, 0..altura-1), **não** do patch.
- `w`/`h` = tamanho da região na foto original. A região cobre `x..x+w-1` e `y..y+h-1`
  (toleramos apenas **1 px** de margem na borda).

## Alternativa (somente se você faz inpainting mascarado de verdade)

Você pode entregar a **imagem completa editada** em vez do patch, **apenas** se:
- a saída tiver **exatamente** as mesmas dimensões (W×H) da foto enviada — sem upscale/downscale;
- **só** a região declarada mudar: todo o resto **bit a bit idêntico**;
- nome: `<classe>_<nome_original_sem_ext>.<mesma_extensão>`.

Se a sua ferramenta só sabe gerar/regerar a imagem inteira, **use o modo patch** (item 1).

## Proibições (motivo de rejeição automática)

- Reescalar, recortar ou reenquadrar (a saída deve ter as dimensões originais).
- Alterar cor/brilho/contraste/tom globais, fundo, foco ou posição da garrafa.
- Acrescentar objetos, logos, marcas d'água, textos ou molduras.
- Aplicar mais de um defeito por imagem (uma alteração por foto).
- Entregar JSON sem `arquivo_original`, sem `regiao`, ou com nome diferente do arquivo real.

## Como somos validados (critério objetivo)

- **Isolamento**: comparamos a sua saída com a foto original; a fração de pixels alterados
  **fora** do bbox precisa ser **≤ 0,2%** (tolerância 12 níveis por canal). Acima disso → rejeitado.
- **Dimensões**: precisam bater exatamente com a original.
- **Schema**: `classe` válida, `regiao` dentro da imagem, `arquivo_saida` conferindo, `arquivo_original` presente.

## Classes de defeito (uma por imagem)

1. `tampa_ausente` — a tampa some, restando o gargalo aberto com as roscas visíveis;
2. `tampa_mal_rosqueada` — tampa desalinhada/inclinada/frisada, sem sumir;
3. `deformidade` — amassado/entortamento localizado no corpo.

## Fluxo

Eu envio **uma** foto; você responde com o **patch PNG (1:1, fundo transparente)** + o **JSON**.
Um a um, sem lote, sem combinar garrafas. Se eu pedir a imagem completa, aplique só o modo de
inpainting mascarado descrito acima.