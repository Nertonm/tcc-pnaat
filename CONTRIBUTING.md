# Contribuição

## Escopo do projeto

Trabalho de conclusão sobre inspeção multi-view e rastreabilidade em linha de envase. O produto (`src-production/`) é a entrega: firmware de trigger e de visão, ponte serial, serviço de rig, API, registro SQLite, dashboard, cadeia de treino e a documentação de replicação. As PoCs da geração anterior foram removidas deste checkout; os READMEs em `docs/pocs/` são histórico.

## Convenções de commit

- `feat:` nova funcionalidade com teste.
- `fix:` correção com teste de regressão.
- `docs:` documentação sem mudança de comportamento.
- `test:` teste novo ou ajuste de teste.
- `decision:` registro de decisão em `docs/DECISIONS.md`.

Uma mensagem de commit descreve o que o diff realmente faz. Não declarar implementação inexistente.

## Desenvolvimento

1. Ler o requisito e a ficha correspondente em `docs/requisitos/`.
2. Escrever um teste que reprova o comportamento ausente.
3. Implementar a menor mudança que faz o teste passar.
4. Rodar a suíte completa e o `git diff --check`.
5. Registrar a evidência e a decisão no commit.

## Prova de conceito

Cada PoC segue `docs/pocs/README.md`: pergunta binária, hipótese, setup, métrica, limiar e go/no-go definidos antes do ensaio. Uma PoC aprovada libera a próxima dependência declarada; não transforma o sistema inteiro em concluído.

## Limites de conteúdo

- Não incluir credenciais, tokens, dados pessoais ou caminhos de máquina.
- Não incluir dataset bruto, imagens ou binários no histórico; registrar caminho, hash e proveniência em manifesto.
- Referência bibliográfica de paper, norma ou dataset é bem-vinda; referência a anotações internas não pertence a este repositório.

## Revisão

Qualquer mudança relevante passa por revisão do diff antes do merge. Critérios: requisito rastreável, teste que pode falhar, evidência reproduzível e nenhuma afirmação sem medição.
