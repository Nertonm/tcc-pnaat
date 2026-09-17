# Entrega 6 — documentação e reprodutibilidade

Esta página é a conferência objetiva dos artefatos exigidos para a entrega final. Ela não substitui
o README da raiz: aponta a evidência e registra o que ainda não pode ser afirmado.

## Matriz dos critérios

| Critério | Evidência no repositório | Veredito |
|---|---|---|
| Código-fonte desenvolvido | `src-production/` (produto), `code-workspace/` (PoCs) e `src-production/firmware/` | Atendido |
| Esquemáticos elétricos | `docs/hardware/esp32s3-trigger/` e contrato de pinos em `src-production/firmware/README.md` | Parcial: o Wokwi é simulação; interface do E18 real requer validação |
| Diagramas finais de arquitetura | diagrama no README raiz e `docs/arquitetura.md` | Atendido |
| Manual no README | pré-requisitos, dependências, instalação, configuração, montagem, execução e confirmação no README raiz | Atendido |
| Organização e legibilidade | módulos e responsabilidades em `src-production/README.md`; testes em `src-production/tests/` | Atendido |
| Reprodutibilidade sem ambiguidades | suíte e demo são locais; inferência real depende de dados/pesos externos identificados por hash | Parcial por dependência dos artefatos externos |

## Checklist antes de publicar

- [ ] substituir `<URL-DESTE-REPOSITORIO>` no README pela URL definitiva;
- [ ] executar `make -C src-production verificar` em Python 3.11;
- [ ] executar `.venv/bin/python -m ruff check --select F src-production`;
- [ ] executar a política de sanitização documentada em `docs/SANITIZACAO.md`;
- [ ] conferir que o pacote do modelo usado na apresentação corresponde ao SHA-256 em
      `models/INDEX.csv`;
- [ ] guardar dataset, peso e contrato juntos no meio de entrega autorizado, pois os binários não
      estão no Git;
- [ ] validar no hardware real a interface elétrica do sensor antes de energizar;
- [ ] apresentar o classificador de corpo e a integração do trigger como pendências, não como
      resultado final.

## Como interpretar o resultado

O repositório é reproduzível, sem hardware ou modelo externo, para instalação, suíte automatizada,
persistência, API e dashboard demonstrativo. A reprodução da classificação real exige o pacote de
modelo calibrado e as capturas externas. A reprodução eletromecânica completa exige ainda a
validação elétrica indicada na documentação de hardware.

Essa distinção evita que “código presente”, “teste automatizado”, “resultado medido” e “meta futura”
sejam tratados como equivalentes.
