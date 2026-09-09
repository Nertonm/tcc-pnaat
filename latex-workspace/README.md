# Template LaTeX: Entrega 1 PNAAT

Formulário técnico para o Levantamento de Requisitos. O arquivo não contém uma solução pronta: o grupo preenche os campos azuis, remove as orientações e mantém apenas decisões, metas e evidências próprias.

## Estado

- Documento: PNAAT-TCC-REQ-001
- Estado: template em revisão
- Classe: KOMA-Script `scrreprt`
- Compilador: LuaLaTeX + Biber + latexmk
- Objetivo: organizar problema, escopo, requisitos, PoCs, integração, reprodutibilidade e aceite

## Build

```bash
make all
```

Para limpar artefatos:

```bash
make clean
```

Para conferir se o documento ainda tem campos de formulário:

```bash
make check-final
```

Esse comando deve falhar enquanto houver campos azuis ou instruções. Isso é esperado no template e impede exportar um PDF incompleto.

## Estados

Use os estados de evidência de forma consistente:

- `ABERTO`: decisão ou dado ainda não definido;
- `PROPOSTO`: solução registrada, sem ensaio suficiente;
- `EM TESTE`: ensaio em execução ou aguardando resultado;
- `VALIDADO`: critério atendido com evidência reproduzível;
- `REJEITADO`: critério não atendido ou alternativa descartada;
- `BLOQUEADO`: falta acesso, dependência, dado ou permissão.

`META` é um alvo mensurável, não um estado. `RESULTADO OBSERVADO` é o valor medido. `ACEITE` é a decisão tomada contra o critério.

- campos azuis (`\placeholder`, `\field`, `\campoGrande`) são obrigatórios ou orientações;
- substituir placeholders por fatos, decisões ou hipóteses identificadas;
- remover as linhas de `\instruction` antes da entrega;
- não deixar `PREENCHER`, `TODO`, `???` ou campos azuis no PDF final;
- usar verbos observáveis e métricas com unidade, população, condição e método;
- distinguir proposta, meta, resultado medido e resultado não alcançado;
- não inserir hardware, modelo, protocolo ou número só porque aparece em um exemplo externo.

## Arquitetura de arquivos

- `main.tex`: composição.
- `preamble.tex`: classe, pacotes e macros de preenchimento.
- `texto/`: seções preenchíveis.
- `tabelas/`: tabelas que crescerem além do corpo.
- `figuras/`: fontes editáveis dos diagramas.
- `referencias.bib`: fontes verificadas.

## Gate antes da entrega

1. Tema oficial, grupo, integrantes e data preenchidos.
2. Dor descrita com situação, afetados, consequência e evidência.
3. Dentro/fora do escopo e premissas separados.
4. RF/RNF rastreáveis a PoC, evidência e aceite.
5. Software, IoT, captura e processamento descritos por função.
6. Nenhuma meta apresentada como resultado.
7. Nenhum placeholder ou instrução no PDF final.
8. Build limpo e revisão visual do PDF.
