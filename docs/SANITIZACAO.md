# Política de sanitização do repositório

Objetivo: o repositório pode ser público sem expor mídia do experimento, credenciais,
dados de terceiros ou infraestrutura privada. A verificação automatizada é o
`sanitizar_repo.py`, alvo `make sanitizar` dentro do `code-workspace`.

## Nunca entra no repositório

| Categoria | Por quê | Onde fica |
|---|---|---|
| Fotos e vídeos do experimento (garrafas, bancada, rig) | política do projeto e privacidade do laboratório | `datasets/pnaat/`, fora do git; evidências locais |
| Credenciais: tokens, chaves de API, `.env`, arquivo de credenciais | segurança | máquina de trabalho, fora do repo |
| Dados de infraestrutura: IPs privados, hostnames, usuário de sistema, caminhos pessoais | reduz superfície e ruído; o repo é acadêmico | usar placeholder: `<host>`, `(host interno)`, `$HOME`, `<TCC_HOME>` |
| CAD de terceiro (STL ou STEP de fornecedor) | licença de terceiro | área de referências do projeto, fora do git |
| Artefatos grandes (ckpt, h5, resultado de notebook) | peso do repositório | fora do git, cache local |
| Nomes completos de terceiros em dados de contato | privacidade | só no documento entregue |

## Exceções declaradas

Toda exceção de mídia mora em um único lugar:
`code-workspace/scripts/politica_midia.py`. O sanitizador importa a regra, e o
`commit_gate.sh` chama o módulo em vez de repetir a expressão.

| Exceção | Extensões | Teto por arquivo | Manifest exigido |
|---|---|---|---|
| Imagem de método em `dataset/**` | jpg, jpeg, png, bmp, webp, heic, gif | 2 MiB | `dataset/MANIFEST.sha256` |
| CAD do entregável em `cad-produto/**` | stl, step, stp, 3mf, png, pdf, svg | 8 MiB | `cad-produto/SHA256SUMS` |

Fora dessas duas exceções, mídia continua proibida, e arquivo rastreado acima de
300 KB também é achado.

A exceção de `cad-produto/**` existe porque o STL é o produto que se quer imprimir, e
não sobra de build. O teto de 8 MiB acomoda a maior peça de hoje, que tem 3,82 MB, e
barra qualquer coisa que fuja da escala de uma peça de impressora de mesa. O CAD de
terceiro continua fora, inclusive o que estiver guardado sob `cad-produto/`.

## Isenções de detecção

Hostname usado como rótulo de câmera é convenção de nomeação de dado, não vazamento de
infraestrutura. `acerola-csi.jpg`, `acerola-usb.jpg` e o rótulo `Acerola USB` na interface
são nomes de arquivo e de etiqueta produzidos pela captura. O detector de hostname tem
exceção para esse sufixo, com contraprova no `--selftest`: o rótulo passa, e o hostname
solto continua sendo achado.

## Permitido e esperado

- texto técnico, código, scripts, relatórios e documentos `.md` e `.tex`;
- o PDF do entregável, que contém a identificação exigida pelo documento;
- os templates e a documentação do entregável de CAD em `cad-produto/**`;
- notebooks do projeto sem saídas embutidas.

## Regra do receipt

Arquivo coberto por `.sha256` ou manifest é evidência de quem o produziu. O sanitizador
não reescreve esses arquivos: ele os reporta para que o produtor regenere o receipt.
Sanear um arquivo com receipt válido quebra a verificação.

## Como verificar

```bash
cd code-workspace
make sanitizar                                  # sai != 0 se houver achado
make sanitizar-apply                            # sanitiza texto e notebooks
python3 scripts/sanitizar_repo.py --selftest     # prova que os detectores detectam
python3 scripts/politica_midia.py --selftest     # prova a regra unica de mídia
code-workspace/scripts/commit_gate.sh            # gate completo; exit 0 = liberado
```

O `commit_gate.sh` roda a suíte de testes, a suíte do firmware, o sanitizador e a
checagem de mídia no staging. Ele bloqueia por padrão. O escape é consciente e
auditável, por `PNAAT_HOOK_BYPASS=1`, e o motivo precisa ir no corpo do commit.

O `pre-commit` está instalado por `core.hooksPath`, apontando para
`code-workspace/scripts/git-hooks/pre-commit`, que executa o gate. Ele bloqueia por
padrão, e o escape consciente é `PNAAT_HOOK_BYPASS=1 git commit`, com o motivo no
corpo do commit.

## Correções de portabilidade

Caminhos pessoais em código foram trocados por defaults de ambiente, mantendo o mesmo
comportamento na máquina de trabalho:

```python
TCC_HOME = os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat"))
```

Na máquina de trabalho isso resolve para o mesmo diretório de antes. Scripts do
entregável de CAD resolvem a própria raiz por `__file__`, e as referências externas
por variável de ambiente.
