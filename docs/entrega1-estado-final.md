# Entrega 1: Levantamento de Requisitos — Estado final da sessão

Documento de encerramento da sessão de 2026-09-09. Repositório canônico: `github/` (HEAD `9a9eb23`, github remoto). Workspace LaTeX em `latex-workspace/`; compilação via distrobox `trabalho` no gaspar.

## Entregável

- PDF: `latex-workspace/PNAAT-TCC-REQ-001-template.pdf`, 12 páginas.
- Build: LuaLaTeX via distrobox `trabalho`; `make check-final` e `git diff --check` limpos; `Overfull=0`; zero placeholders.
- Estrutura: `main.tex`, `preamble.tex` e `texto/{capa,contexto,escopo,arquitetura,requisitos,validacao}.tex`; referências locais via `\pocref`/`\hypertarget`; tabelas com zebra (corpo) e cabeçalho `\tblhdr`; expansões em cinza `pnaatgray`; paleta `pnaatblue` + `bodytext`.

## Avaliação contra a rubrica (Definição e Requisitos, 0–1.5)

Veredito: Nível Avançado, 1.5 pontos.

- Identificação: capa p.1 (título, grupo; 4 integrantes).
- Escolha do tema: capa, "Cenário 1: Inspeção de envase".
- Escopo: s1.3 situação; s1.5 resultado; s2.1/s2.2 limites dentro/fora.
- Levantamento de requisitos: s3.1 sensores/placas + função; s3.2 conectividade/captura/processamento/software; IoT/visão/integração; viabilidade e aderência (estado planejado + PoCs).
- Aprofundamento (diferencial Avançado): s1.2 análise; s2.4/s5.4 visão crítica; s5.6 justificativas (8 escolhas, com necessidade, porquê, alternativa e critério).

Cobertura de requisitos no PDF: RF-01..RF-30 (30) e RNF-01..RNF-21 (21), todos presentes por conjunto (núcleo, expansão e processo), sem IDs ausentes.

## Pendências registradas (não aplicadas nesta sessão)

Não afetam a avaliação da rubrica, mas violam regra editorial ou o padrão de apresentação:

- `pixel--milímetro` renderiza en-dash no PDF; trocar para "pixel a milímetro" ou hífen simples.
- Resíduo "hub" em `contexto.tex` (premissa de conectividade) contradiz o núcleo de nó único/registro local.
- Referências órfãs `DAT-*` e `IF-*` em `arquitetura.tex` (sem âncora no documento); `RNF-06` citado na comunicação local é de expansão.
- Cabeçalho da tabela 4.1 (Classes e saídas) sem `\tblhdr`.
- Figura 3.1 usa "fusão por votação"; alinhar ao léxico "regra determinística".
- Hifenização em colunas estreitas (expansão `p{0.18\textwidth}`, "dashboard" em escopo.tex) e espaço residual no rodapé por `\raggedbottom`.

## Constraints

- Nenhum commit realizado nesta sessão; `git status` do repositório mantém as alterações pendentes de aprovação.
- Nenhum push: remoto exige credenciais e autorização nominal.