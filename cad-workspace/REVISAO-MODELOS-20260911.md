# Revisão dos modelos — estado real no disco (2026-09-11)

Verificação feita abrindo os arquivos com FreeCAD headless (não pelos relatórios).

## Veredito por conjunto

| conjunto | STEP | sólidos | veredito | por quê |
|---|---|---|---|---|
| **R05 — mount de câmera** | `camera-mount-din-v6.step` | **1 válido**, 8 787 mm³ | **VÁLIDO** (0,0434 mm³ de interferência com o CM3 completo) | o único mount de câmera verificado |
| R05 — optical block / colunas | `column-modules-v2/v3`, `column-draft` | 11–17 sólidos | **CONCEITO** não verificado | montagens antigas, sem gates |
| **R06 — estrutura** | **sem STEP** (só STL) | — | **REPROVADO** | cantoneira com 2 sólidos; M6 mal orientado |
| **R07 — estrutura** | **sem STEP** (só STL) | — | **REPROVADO** pelo auditor | Redux perpendicular ao plano de engate; "mordida de mola" não provada |
| AUDIT — correção topológica | `cantoneira-topology-only.step` | **1 válido**, 10 192 mm³ | **CUPOM** (não montagem) | corrigiu a continuidade do canto; não é conjunto |
| **BASE v2** | `base-v2.step` | 10 válidos | **VÁLIDO** | gates passaram: colisões 0, M6 encaixa (gap 0, 0 / insert 5,5 mm) |
| **PEÇA OFICIAL** | `peca-dupla-plataformas.step` | **1 válido**, 22 763 mm³ | **VÁLIDO** | assentamento 0; trilho 0; duas plataformas verificadas |

## O que está sólido (pode ser usado como base)

1. **`peca-dupla-plataformas`** — a peça oficial: 1 sólido, duas plataformas, encaixe do trilho integrado,
   furos nos dois sentidos do clamp, STEP+STL+FCStd+manifest com SHA-256.
2. **`base-v2`** — o conjunto base com todos os contatos em 0,000 e o encaixe M6↔trilho comprovado.
3. **`camera-mount-din-v6`** — o mount da CM3 Wide, validado contra o modelo completo (631 sólidos).

## Dívidas e inconsistências encontradas

| # | problema | efeito |
|---|---|---|
| 1 | **R06 e R07 não têm STEP** — só STL | não há CAD editável dos modelos reprovados; se alguém quiser retomar, terá de refazer |
| 2 | **R07 carrega claims retratados** no próprio RELATORIO (mordida de mola 182 mm³, orientação do Redux) | quem ler o arquivo sem o contexto acredita em coisa errada |
| 3 | **Não existe índice da sequência** R01→R07 + candidatos | os nomes são `optical-rig-rNN` para coisas diferentes (mount vs estrutura) |
| 4 | **R05 não tem relatório na pasta** (está em `reports/`) | difícil ligar o STEP validado ao seu laudo |
| 5 | **Artefatos de teste convivem com oficiais** em `structural-candidate/` (`base-candidate` junto de `base-v2`) | risco de confundir qual é o bom |
| 6 | **`camera-mount-din-v1-interferencia.step` tem 174 sólidos** | é lixo de diagnóstico guardado como se fosse CAD |
| 7 | **Diretórios por timestamp** (`stage0-…T032253Z`, `candidate-audit-…T052357Z`) | não se sabe o que é cada um sem abrir |

## Claims que foram corrigidos durante a sessão (para não voltarem)

- ❌ "o bracket M6 nunca encaixa" → **ele encaixa**: `gap 0,000 / inserção 5,5 mm`. O erro era meu (orientação e componentes não separados).
- ❌ "182 mm³ é a mordida elástica do Redux" → **não é prova de nada**; colisão não demonstra mola.
- ❌ "a cantoneira R07 é uma peça" → era **2 sólidos**.
- ❌ "6,45 mm no clamp é rosca 1/4-20" → **é inferência**; a malha é facetada e não prova rosca.
- ❌ "antirrotação resolvida por 2 parafusos" → só é verdade **com contato correto nas duas faces**, o que a peça oficial agora tem.

## O que continua aberto (não é dívida de arquivo, é de projeto)

1. **Medir a esteira** — decide CFG1 (plataforma superior) ou CFG2 (lateral). Sem isso, ambas ficam no papel.
2. **Montantes + travessa** — o pórtico não existe.
3. **Fixadores reais** — nenhum parafuso escolhido, sem rosca, sem torque.
4. **Cargas, vibração, rigidez, fadiga** — nada calculado.
5. **Ensaio físico** — nada foi impresso.
6. **Câmeras, Pi, cabos, trigger** — não iniciados (por sequência).

## Recomendação de organização (mínima, reversível)

1. Renomear os diretórios de timestamp para função: `stage0-referencias/`, `auditoria-r07/`, `base-v2/`.
2. Mover o mount validado (R05 v6) para junto do seu laudo, com nome que diga o que é.
3. Escrever um `INDICE.md` na raiz de `cad-workspace/` listando o que cada coisa é e o veredito.
4. Marcar os reprovados com um `REPROVADO.md` no topo (para o relatório antigo não enganar).
5. Apagar/arquivar os lixos de diagnóstico (ex.: o STEP de 174 sólidos).

Nada disso foi executado — é proposta. Nenhum commit, push ou merge foi feito.
