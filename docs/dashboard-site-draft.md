# Draft — site de visualização do TCC PNAAT

Status: DRAFT — ideia e requisitos em aberto. Este documento não contém implementação.

## Ideia

Criar um site local de operação para acompanhar as capturas produzidas pela Raspberry Pi na bancada de inspeção. O site deve tornar cada captura auditável: item, lote, vista, horário, resultado, confiança, latência, qualidade do registro e evidência associada.

Grafana fica reservado para séries operacionais agregadas. O site próprio concentra histórico por item, evidências e investigação humana. Nenhum controle físico da esteira ou atuador entra nesta primeira versão.

## Fluxo futuro

Raspberry Pi captura → evento identificado → registro local → exportação/snapshot → site consulta → operador investiga e registra correção.

A integração deve preservar o registro original. Ausência de imagem, vista faltante ou timestamp divergente devem aparecer como estado explícito, nunca como sucesso implícito.

## Requisitos funcionais — placeholders

| ID | Requisito | Definição pendente |
|---|---|---|
| SITE-01 | Exibir histórico de capturas | [TBD: retenção e paginação] |
| SITE-02 | Filtrar por lote, item, vista e estado | [TBD: filtros obrigatórios] |
| SITE-03 | Abrir detalhe do item | [TBD: campos e navegação] |
| SITE-04 | Exibir evidência da captura | [TBD: formato, origem e política de ausência] |
| SITE-05 | Exibir qualidade do registro | [TBD: estados finais e cores] |
| SITE-06 | Exibir saúde da Pi e dos nós | [TBD: sinais e limiares] |
| SITE-07 | Atualizar dados sem recarregar a página | [TBD: polling ou evento] |
| SITE-08 | Registrar correção do operador | [TBD: autenticação e autorização] |
| SITE-09 | Exportar ou abrir relatório de lote | [TBD: formato e escopo] |
| SITE-10 | Integrar com Grafana | [TBD: links e responsabilidades] |

## Requisitos não funcionais — placeholders

| ID | Requisito | Definição pendente |
|---|---|---|
| SITE-NF-01 | Não alterar o banco de captura por leitura | [TBD: usuário e permissões] |
| SITE-NF-02 | Não perder a decisão original | [TBD: modelo de auditoria] |
| SITE-NF-03 | Identificar dados stale ou ausentes | [TBD: idade máxima aceitável] |
| SITE-NF-04 | Operar localmente sem serviço externo | [TBD: topologia final] |
| SITE-NF-05 | Ser utilizável em notebook e tela da bancada | [TBD: resoluções alvo] |
| SITE-NF-06 | Evidência deve ser recuperável | [TBD: armazenamento e hash] |
| SITE-NF-07 | Responder dentro do limite da demonstração | [TBD: latência e volume] |

## Painéis planejados

1. **Operação** — estado da linha, último evento, taxa de defeito e alerta ativo.
2. **Capturas** — histórico paginado por item e vista.
3. **Investigação** — detalhe, evidências, timestamps e divergências.
4. **Qualidade** — defeitos por código/severidade, registros parciais e correções.
5. **Saúde** — heartbeat, fila, latência e conectividade da Pi.
6. **Lote** — resumo, tendência e exportação do relatório.

## Fora do primeiro recorte

- comando de atuador;
- parada ou partida da esteira;
- alteração automática de decisão;
- treinamento ou retreinamento de modelo;
- banco paralelo ao registro da Pi;
- afirmação de acurácia sem ground truth e ensaio documentado.

## Decisões em aberto

- [TBD] A Pi servirá uma API ou exportará snapshots?
- [TBD] O site rodará na Pi, no notebook ou em outro host local?
- [TBD] Como as imagens serão transferidas e retidas?
- [TBD] Qual mecanismo de autenticação será usado para correção do operador?
- [TBD] Quais sinais serão Prometheus e quais permanecerão no registro SQLite?
- [TBD] Qual conjunto mínimo fecha a demonstração?

## Critério de aceite futuro

O draft só deve virar implementação quando cada requisito tiver fonte, produtor, consumidor, teste, evidência e responsável definidos. Até lá, qualquer tela ou dado deve ser identificado como proposta, fixture ou medição real.
