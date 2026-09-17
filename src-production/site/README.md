# TCC PNAAT - Dashboard Local de Visualização

Este diretório contém o frontend em uso: o site local de acompanhamento das capturas da Raspberry Pi.

## Estrutura de Arquivos

- `index.html`: Layout principal, sidebar, e container dos painéis. Importa o TailwindCSS via CDN (ótimo para rodar local sem build).
- `js/app.js`: Lógica principal de roteamento (troca de telas) e alternância entre Modo Claro/Escuro.
- `js/components.js`: Contém o HTML/Templates de cada painel servido (Operação, Capturas, Investigação, etc.).
- `js/api.js`: **fonte de dados real** — conversa com a API local do hub (`src-production/api.py`, mesma origem) e preenche as globais que os templates consomem. Os mocks (`js/data.js`) foram retirados: numero inventado que sobrevive a queda da API e acreditado, e a tela agora fica vazia com aviso quando a API nao responde.

## Como Visualizar

O site é servido pela API local (`src-production/api.py`), na mesma origem: o adaptador
(`js/api.js`) busca `/api/...` por caminho relativo e não existe dado embutido para preencher a tela.

```sh
# da RAIZ do clone (o site e servido pela API, na mesma origem)
.venv/bin/python src-production/api.py --db hub.db --porta 8080 --host 127.0.0.1
```

Abrir o `index.html` direto do disco (`file://`) NÃO funciona: sem servidor não há `/api`, e a tela
mostra o aviso de API indisponível, o que é intencional: número inventado já foi defeito aqui.

## Cores e Design (Conforme Requisito)

A paleta pedida está no Tailwind config dentro do `index.html`:
- Vermelho: `#D61A22`
- Branco: `#F9FBFD`
- Preto: `#1E2022`
- Verde-oliva: `#5D6B42`

Tem animações simples de fade-in e suporte a dark mode.

## Estado deste diretório

O site é o frontend em uso. A API o serve na mesma origem, e ele lê tudo de `/api/...` (`js/api.js`).
Sem servidor não há dado: abrir o `index.html` por `file://` mostra o aviso de API indisponível, que
existe justamente porque número inventado já foi defeito aqui.

Há duas dependências de rede. As folhas de estilo e os ícones vêm de CDN, Tailwind e Lucide, então
uma máquina sem internet abre a página com os dados e sem estilo nem ícones. Não existe build: os
arquivos são servidos como estão.

O manual de replicação na raiz, `README.md` seção 6, e `docs/operacao-pipeline.md` são a referência
para rodar o sistema. Não há alvo de demonstração; para uma operação local sem hardware, suba a API
com `--db hub.db --porta 8080` e abra o site na mesma origem.
