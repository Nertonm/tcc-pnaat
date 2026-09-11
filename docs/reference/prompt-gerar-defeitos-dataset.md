# Prompt: gerar defeito sintético em foto de garrafa (dataset instr.) — um a um

Cole o texto abaixo junto com **UMA foto de cada vez** numa ferramenta de edição de imagem IA
(ex.: o modelo de edição/inpainting do seu provedor). O objetivo é construir o dataset com
defeitos isolados, mantendo a mesma perspectiva.

---

Você vai me ajudar a montar um dataset de inspeção de garrafas (linha de envase).
Eu vou te enviar **UMA foto por vez**, capturada por uma câmera fixa no nosso rig.

**Tarefa**: a partir da foto recebida, gere **uma imagem de saída** com EXATAMENTE o mesmo
enquadramento, perspectiva, iluminação, fundo, tamanho e qualidade. **NÃO re-renderize a cena
do zero.** Apenas modifique, de forma **ISOLADA e LOCALIZADA**, uma pequena região da foto
para criar **UM defeito sintético realista**, de uma destas classes (escolha uma que eu passar):

1. `tampa_ausente` — a tampa some, restando só o gargalo aberto;
2. `tampa_mal_rosqueada` — a tampa fica desalinhada/inclinada/frisada, sem sumir;
3. `deformidade` — amassado/entortamento localizado no corpo da garrafa.

**Restrições rígidas:**
- Preserve **pixel por pixel** tudo que está fora da região do defeito.
- Não acrescente objetos, não troque o fundo, não mude cor/brilho globais, não mova a garrafa.
- O defeito deve parecer fotografado na MESMA iluminação (sombras/reflexos coerentes) e no
  mesmo plano de foco.
- Aplique **UMA alteração por imagem**; nada de trocar a garrafa inteira nem adicionar itens.
- Formato/tipo de arquivo da saída igual ao da entrada, com nome diferente (ex.:
  `<classe>_<nome_original>`).

**Saída (nesta ordem):**
1. Um JSON de controle começando por:
   `{"classe": "tampa_ausente"|"tampa_mal_rosqueada"|"deformidade", "regiao": [x, y, w, h], "arquivo_saida": "<nome exato da imagem editada>", "arquivo_original": "<nome exato da foto enviada>", "descricao": "..."}`
   (`regiao` = caixa em px da área editada; nada fora dela pode mudar).
2. A **imagem editada**.
3. **Opcional**: máscara PNG da região editada (região em branco, resto preto), para treino de
   segmentação.

**Contrato de fluxo:** eu envio a original; você responde com o JSON + a imagem editada (+
máscara, se houver). Processe **um a um**, sem lote e sem combinar garrafas.

---

Nota: definir `regiao` e guardar original/editada/máscara permite validar depois que a edição
foi isolada (nada fora da caixa mudou) — bake no gate do dataset.