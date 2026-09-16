# TCC PNAAT - Dashboard Local de Visualização

Este diretório contém a proposta de interface (draft) para o site local de acompanhamento das capturas da Raspberry Pi.

## Estrutura de Arquivos

- `index.html`: Layout principal, sidebar, e container dos painéis. Importa o TailwindCSS via CDN (ótimo para rodar local sem build).
- `js/app.js`: Lógica principal de roteamento (troca de telas) e alternância entre Modo Claro/Escuro.
- `js/components.js`: Contém o HTML/Templates de cada painel planejado (Operação, Capturas, Investigação, etc.).
- `js/api.js`: **fonte de dados real** — conversa com a API local do hub (`src-production/api.py`, mesma origem) e preenche as globais que os templates consomem. Os mocks (`js/data.js`) foram retirados: numero inventado que sobrevive a queda da API e acreditado, e a tela agora fica vazia com aviso quando a API nao responde.

## Como Visualizar

O site é servido pela API local (`src-production/api.py`), na mesma origem: o adaptador
(`js/api.js`) busca `/api/...` por caminho relativo e não existe dado embutido para preencher a tela.

```sh
python3 api.py --db hub.db --site src-production/site
```

Abrir o `index.html` direto do disco (`file://`) NÃO funciona: sem servidor não há `/api`, e a tela
mostra o aviso de API indisponível — de propósito, porque número inventado já foi defeito aqui.

## Cores e Design (Conforme Requisito)

O design implementa a paleta solicitada nativamente no Tailwind config dentro do `index.html`:
- Vermelho: `#D61A22`
- Branco: `#F9FBFD`
- Preto: `#1E2022`
- Verde-oliva: `#5D6B42`

Possui animações simples (fade-in) e suporte completo a dark mode.

## Próximos Passos no GitHub

Como este é um novo módulo do projeto, você deve realizar as seguintes ações no seu repositório GitHub:

1. **Criar uma Branch ou Pull Request**:
   - Crie uma branch para essa feature: `git checkout -b feature/dashboard-local`
   - Faça o commit dos arquivos: `git add src-production/site/` e `git commit -m "feat: adiciona draft do site de visualização (HTML/CSS/JS)"`
   - Faça o push e abra um Pull Request (PR) para revisão, permitindo que outros membros do TCC validem o layout.

2. **Abrir Issues para as Definições Pendentes (TBD)**:
   O draft de requisitos lista vários itens `[TBD]`. Crie Issues no GitHub com labels como `discussion` ou `architecture` para debater:
   - "Qual será a API servida pela Raspberry Pi?"
   - "Como será a autenticação do operador (SITE-08)?"
   - "Topologia local de rede e serviços"

3. **Gerenciamento de Projeto (Projects)**:
   - Adicione os placeholders de requisitos (SITE-01 a SITE-10) como cards no GitHub Projects/Kanban do grupo, movendo do status "Draft" para "Em Desenvolvimento" conforme a API de comunicação for definida.

4. **GitHub Pages (Opcional)**:
   - Se quiserem mostrar o mockup para professores sem precisar rodar localmente, podem habilitar o **GitHub Pages** na pasta `/src-production/site` da branch principal, permitindo o acesso via um link público do próprio GitHub.
