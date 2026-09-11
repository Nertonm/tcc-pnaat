# Rubrica oficial da Entrega 1 (recuperada) + conferência do entregue

Fonte: texto da disciplina colado pelo usuário em 2026-09-08 (`paste_3_230225.txt`, 70 linhas) —
estava **fora do repositório**; recuperado aqui para não se perder.

## O que a Entrega 1 exige

**Artefato:** documento em PDF contendo **obrigatoriamente**:

1. **Identificação** — título do projeto; nome do grupo; nome completo dos integrantes.
2. **Escolha do tema** — indicação, por **nome ou número**, de qual dos **oito temas industriais** foi selecionado.
3. **Escopo do problema** — situação tratada; resultado que a solução pretende produzir; limites
   (o que será e o que **não** será contemplado).
4. **Levantamento de requisitos técnicos** — sensores e placas previstos; recursos de conectividade,
   captura, processamento ou software; necessidades de **IoT, visão computacional ou integração**;
   função prevista dos principais recursos. Os requisitos devem ser **tecnicamente viáveis** e
   **aderentes** à tecnologia escolhida.
5. **Aprofundamento (para nível máximo)** — análise aprofundada do problema relacionando situação,
   necessidades, resultado e limites; visão crítica do cenário (condições/restrições); justificativa
   das principais escolhas tecnológicas (qual necessidade cada uma atende e por quê).

## Níveis da rubrica

| Nível | Pontos | Critério (resumo fiel) |
|---|---|---|
| Ausente | 0 | não permite verificar formalização do desafio nem mapeamento das necessidades |
| Insuficiente | 0,375 | há informação do tema/problema/tecnologia, mas escolha do tema, escopo ou requisitos está ausente/desconectado |
| Básico | 0,75 | parte verificável: tema, escopo e requisitos identificáveis, mas um ou mais conteúdos ausentes, incompletos ou não correspondentes |
| Adequado | 1,125 | tudo integralmente verificável: tema, problema com situação/resultado/limites e levantamento preliminar com funções e viabilidade |
| Avançado | 1,5 | Adequado **+** análise aprofundada, visão crítica e justificativa das escolhas tecnológicas |

## Conferência do nosso entregue (`latex-workspace/PNAAT-TCC-REQ-001-template.pdf`, v1.0, 09/09/2026)

| Exigência | Estado | Evidência (verificada no PDF) |
|---|---|---|
| Título do projeto | **atendido** | "Inspeção Automatizada Multi-View com Rastreabilidade de Anomalias em Linha de Produção" |
| Nome do grupo | **atendido** | "Soldadinhos do Araripe" |
| Integrantes (nome completo) | **atendido** | 4 nomes na capa (Luana, Thiago, Paulo Victor, Miguel) |
| Tema por nome/número | **atendido** | "Tema: Cenário 1: Inspeção de envase" |
| Escopo (situação/resultado/limites) | **atendido** | seção de escopo + limites explícitos (atuar na esteira fora do núcleo) |
| Sensores e placas | **atendido** | E18-D80NK, ESP32, câmeras, Pi 5 (RF/RNF + arquitetura) |
| Conectividade/captura/processamento/software | **atendido** | arquitetura + justificativas de tecnologia |
| Função prevista dos recursos | **atendido** | tabela de arquitetura (função por bloco) |
| Viabilidade/aderência (IoT, VC ou integração) | **atendido** | fronteira núcleo × expansão (D-22) declara o que é viável no prazo |
| Análise aprofundada + visão crítica + justificativas | **atendido** | contexto/visão crítica + tabela de justificativas tecnológicas |

**Risco cosmético identificado:** o arquivo entregue chama-se `PNAAT-TCC-REQ-001-template.pdf`
("template" no nome). Renomear antes da submissão final evita passar impressão de rascunho.

**Lacuna declarada:** a rubrica fala dos "oito temas industriais apresentados"; não temos em mãos a
lista dos oito. Nosso entregue indica "Cenário 1: Inspeção de envase" (nome **e** número), o que
satisfaz a exigência, mas confirmar a nomenclatura oficial é ação do usuário (material da disciplina).
