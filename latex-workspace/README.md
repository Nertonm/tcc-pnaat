# Documento LaTeX: Entrega 1 PNAAT

Documento final do Levantamento de Requisitos do TCC PNAAT. O PDF formaliza o Cenário 1, o contexto, o escopo, os requisitos técnicos e as PoCs propostas para validar cada ideia e a conjectura integrada.

## Estado do artefato

- PDF publicado: `PNAAT-TCC-REQ-001-template.pdf`
- Compilador: LuaLaTeX + latexmk
- Estrutura: contexto, escopo, arquitetura, requisitos, PoCs, visão crítica e próximos passos
- Estado das decisões: `Proposto` até que a PoC correspondente produza evidência
- Escopo: observação, classificação, rastreabilidade e dashboard; sem controle da velocidade da esteira ou atuação física

## Build

```bash
make all
```

Para limpar artefatos de compilação:

```bash
make clean
```

Para verificar campos vazios e marcadores antes da entrega:

```bash
make check-final
```

O gate deve terminar sem placeholders, instruções ou marcadores de trabalho.

## Organização

- `main.tex`: composição do documento.
- `preamble.tex`: pacotes, estilos, colunas e macros de links PoC.
- `texto/capa.tex`: identificação e integrantes.
- `texto/contexto.tex`: Cenário 1, dor, resultado pretendido e operação.
- `texto/escopo.tex`: dentro/fora do escopo, premissas e restrições.
- `texto/arquitetura.tex`: papéis, interfaces e expansão multi-nó.
- `texto/requisitos.tex`: RF, RNF, critérios e rastreabilidade.
- `texto/validacao.tex`: PoCs, riscos, integração e justificativas.
- `texto/aceite.tex`: próximos passos de execução.
- `figuras/`: documentação dos diagramas autocontidos.

A Entrega 1 não apresenta desempenho medido. Cada PoC define a métrica, o critério e a evidência que serão usados na etapa de validação.
