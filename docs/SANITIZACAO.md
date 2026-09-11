# Política de sanitização do repositório

Objetivo: o repositório pode ser público (GitHub) **sem** expor mídia do experimento, credenciais,
dados de terceiros ou infraestrutura privada. Verificação automatizada no fluxo F4
(`code-workspace/scripts/sanitizar_repo.py`, alvo `make sanitizar`).

## Nunca entra no repositório

| Categoria | Por quê | Onde fica |
|---|---|---|
| Fotos/vídeos do experimento (garrafas, bancada, rig) | política do projeto ("não suba as fotos") + privacidade do laboratório | `datasets/pnaat/` (fora do git), evidências locais |
| Credenciais: tokens, arquivo de credenciais da ferramenta, chaves de API, `.env` | segurança | host de trabalho (fora do repo) |
| Chatices de infraestrutura: IPs privados, hostnames, usuário de SO, caminhos pessoais | reduz superfície e ruído; o repo é acadêmico | usar placeholder (`<host>`, `(host interno)`, `$HOME`, `<TCC_HOME>`) |
| Binários de CAD de terceiros (STL/STEP de fornecedor) | licença de terceiro | `cad-workspace/references/vendor/**` (ignorado) |
| Artefatos grandes (ckpt, h5, resultados de notebook) | peso do repositório | fora do git / cache local |
| Nomes completos de terceiros em dados de contato | privacidade | só no documento entregue |

## Permitido e esperado

- texto técnico, código, scripts, relatórios e documentos `.md`/`.tex`;
- o PDF do entregue (`latex-workspace/PNAAT-TCC-REQ-001-*.pdf`) — ele contém a identificação exigida
  pelo documento entregue (tema, grupo, integrantes);
- `cad-workspace/data/g0/**` (templates G0) explicitamente liberados no `.gitignore`;
- notebooks do projeto (`code-workspace/notebooks/*.ipynb`) **sem saídas embutidas**.

## Regra do receipt (importante)

Arquivo coberto por `.sha256`/manifest é **evidência** de quem o produziu. O sanitizador **não**
reescreve esses arquivos: ele os reporta para que o produtor regenere o receipt. Sanear um arquivo
com receipt quebra a verificação — foi o que aconteceu com `cad-workspace/reports/OPTICAL-RIG-3CAM-R01.md`
(restaurado do HEAD depois, receipt válido de novo).

## Como verificar

```bash
cd code-workspace
make sanitizar          # --check: sai != 0 se houver achado
make sanitizar-apply    # sanitiza texto/notebooks (não reescreve código nem receipts)
python3 scripts/sanitizar_repo.py --selftest   # prova que os detectores detectam
```

O hook `pre-commit` roda o sanitizador em modo aviso (não bloqueia colegas) junto do `doctor`.

## Correções de portabilidade (sem quebrar execução)

Caminhos pessoais em código foram trocados por defaults de ambiente, mantendo o mesmo comportamento
na máquina de trabalho:

```python
TCC_HOME = os.environ.get("TCC_HOME", str(Path.home() / "tcc-pnaat"))
```

Na máquina de trabalho, `Path.home()` resolve para o mesmo diretório de antes — nada muda na
execução; só deixa de publicar o caminho absoluto.
