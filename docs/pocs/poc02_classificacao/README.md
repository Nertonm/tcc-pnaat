# PoC-02: Classificacao de tampa (isolada)

- **Unidade**: esta PoC, isolada. Trigger, esteira e Pi pertencem a outras PoCs e **nao** sao pre-requisito.
- **Ideia** (`docs/pocs/README.md`): classificacao de tampa ausente e mal rosqueada.
- **Criterio de passagem**: metas do RNF-02 por classe (ausente >=95%, mal rosqueada >=90%, com intervalo
  de confianca) **e** RNF-03 (FP <=2% ausente, <=5% demais).
- **Evidencia esperada**: matriz de confusao **por classe**, com `n` declarado e IC, mais a imagem
  anotada de cada item (o que discriminou).
- **Casos**: `normal`, `tampa_ausente`, `tampa_mal_rosqueada`, `fronteira` (rosca parcial/alinhamento
  limitrofe) e `inconclusivo` (classe propria na matriz, D-26).

## Decisoes vigentes

| Decisao | Conteudo |
|---|---|
| **D-04 (emenda)** + **D-23** | a tampa e decidida nas **duas vistas laterais**; a vista de topo e check dimensional independente (so escala, nunca aprova sozinha) |
| **D-24** | nenhum limiar vale como criterio sem fonte primaria (`arquivo:linha`) ou validacao empirica registrada |
| **D-25** | recall por classe com IC (Wilson/Clopper-Pearson), FP separado de FN, inconclusivo proprio, e **imagem anotada por item** |
| **D-26** | fronteira entra no conjunto; inconclusivo > 10% = nao decidivel |
| **D-27** | composicao de fontes (proprio + publico + referencias) com **procedencia por numero**, nunca agregada |
| **D-28** | classes: `normal`, `tampa_ausente`, `tampa_mal_rosqueada`, `inconclusivo` |

## O que precisa e o que NAO precisa

```
precisa                                     NAO precisa
imagens das classes (proprias + publicas)   gatilho E18 (PoC-01)
manifest com item_id e rotulo por item      esteira / controle de velocidade (PoC-01/03)
duas vistas laterais + uma de topo          Pi 5 (RNF-01 e outra metrica)
harness de avaliacao (scripts/avaliar_poc02.py)  modelo destilado / aluno (expansao)
```

## Protocolo minimo

1. **Congelar antes de coletar**: bloco de limiares versionado (D-24) e definicao operacional de
   `fronteira`. Nenhum limiar provisorio vira criterio.
2. **Conjunto proprio**: 20-50 itens por classe, produzidos a mao (tampa removida; rosqueada parcial em
   3 severidades), com `item_id`, `fonte=proprio`, verdade anotada **antes** de ver a saida do pipeline,
   split por item (nunca por frame).
3. **Composicao (D-27)**: somar o corpus publico com `fonte=publico:<dataset>` e as referencias
   bibliograficas como comparacao externa. Cada bloco e reportado separado.
4. **Avaliar**: `python scripts/avaliar_poc02.py --manifest ... --predicoes ... --anotar saida/ [--limiares limiares.json]`.
5. **Julgar**: GO somente se o **limite inferior** do IC95 do recall >= alvo e a taxa de FP <= limite;
   caso contrario NO_GO ou NAO_DECIDIVEL (inconclusivo > 10%).

## Pendencias declaradas

- `tilt_incerto=2,0` / `tilt_reprova=4,0` / `altura_ausente_px=3,0`: **provisorios** ate fonte ou
  calibracao empirica (D-24).
- Definicao operacional de "dimensao violada" pelo topo (D-23), a calibrar.
- Quantidade de itens por classe: dimensionar pelo IC desejado (com 0 erro, n=73 da LB95 >= 0,95 para
  ausente; n=35 para mal rosqueada) e pelo teto de FP do IC.
