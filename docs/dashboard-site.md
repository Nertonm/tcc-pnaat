# Site e dashboard: estado implementado

Este documento substitui o rascunho original. O produto em `src-production/` já contém API HTTP, site
estático, consultas SQLite, exposição de evidências, correção de operador e leituras de rig/ponte. O
que depende da instalação física ou de serviço externo permanece identificado como dependência, não
como implementação do site.

## 1. Fluxo que existe

```text
serviço de rig e ponte -> api.py -> consultas SQLite/site -> operador
                                      |
                                      +-> POST /api/correcao -> trilha no registro
```

A ponte serial é `src-production/firmware/esp32cam-test/esp32cam_site.py`: ela recebe eventos do
sensor de trigger, envia `CMD_TRIG` ao nó da câmera, decodifica frames e publica status. O gateway
`api.py` consulta `PNAAT_RIG` e `PNAAT_PONTE` e repassa teste de trigger, captura e delay. A topologia
e os endereços são configuração da instalação.

O site consulta o SQLite local. Ele não substitui o registro, não mantém banco paralelo e não muda a
decisão original quando o operador registra uma correção.

## 2. Rotas disponíveis

| Rota | Estado no código | Fonte |
|---|---|---|
| `GET /api/health` | implementada; pode inicializar o schema quando o banco é novo | `api.py`, `tests/test_saude_banco_novo.py` |
| `GET /api/resumo` | implementada; resumo de itens e estados | `api.py`, `consultas_site.py` |
| `GET /api/capturas` | implementada; lista limitada, filtros por vista e estado | `api.py`, `consultas_site.py` |
| `GET /api/item/<id>` | implementada; detalhe, vistas, evidências e correções | `api.py`, `consultas_site.py` |
| `GET /api/evidencia` | implementada; só serve imagem dentro da raiz permitida | `api.py` |
| `GET /api/qualidade` | implementada; indicadores do registro e saúde observada | `api.py`, `painel.py` |
| `GET /api/lotes` | implementada; resumo por lote | `api.py`, `painel.py` |
| `GET /api/gatilhos` | implementada; eventos registrados | `api.py`, `painel.py` |
| `GET /api/rig/*` | implementada como gateway para rig e ponte | `api.py:1098-1250` |
| `POST /api/gatilho` | implementada; valida e persiste o evento | `api.py`, `registro.py` |
| `POST /api/correcao` | implementada; preserva original e registra read-back | `api.py`, `registro.py` |

## 3. Requisitos do site e estado

| ID | Implementação verificada | Limite real |
|---|---|---|
| SITE-01 | histórico recente de capturas | máximo por requisição; não há paginação por cursor |
| SITE-02 | filtros por vista e estado | não há filtro server-side completo por lote e item |
| SITE-03 | detalhe com item, vistas, evidências, decisão e correções | depende do item existir no SQLite |
| SITE-04 | evidência recuperável com validação de raiz e tipo | retenção e backup são externos |
| SITE-05 | qualidade, inconclusão, discordância e indicadores | não é métrica de desempenho ML ou do rig físico |
| SITE-06 | saúde local, adaptador e heartbeats registrados | limiares e cobertura dos nós dependem da instalação |
| SITE-07 | atualização por polling enquanto a página está visível | não usa WebSocket ou SSE |
| SITE-08 | correção append-only com decisão original preservada | identidade forte, usuários e papéis não existem |
| SITE-09 | resumo por lote, CSV da lista e relatório HTML por CLI | não há endpoint dedicado de relatório por lote |
| SITE-10 | não implementado | Grafana é integração externa |
| SITE-NF-01 | consultas usam SQLite read-only | `/api/health` pode criar schema em banco novo |
| SITE-NF-02 | original e correção ficam separados | — |
| SITE-NF-03 | ausência é declarada | idade máxima de stale não está definida |
| SITE-NF-04 | API, SQLite e site rodam na mesma origem | Tailwind/Lucide vêm de CDN |
| SITE-NF-05 | frontend responsivo | resolução-alvo e teste de usabilidade não estão formalizados |
| SITE-NF-06 | path traversal e arquivo ausente falham explicitamente | retenção, replicação e backup são externos |
| SITE-NF-07 | há limites defensivos de consulta e timeout | SLA e benchmark do frontend não estão definidos |

## 4. Painéis

- Operação: resumo, saúde e eventos registrados.
- Capturas: histórico recente e filtros existentes.
- Investigação: item, vistas, evidências e correções.
- Qualidade: defeitos, inconclusivos, latência, saturação, gatilhos e discordâncias do registro.
- Saúde: heartbeat e estado dos adaptadores observados.
- Lote: resumo e exportação CSV da lista carregada.

Esses painéis representam o estado persistido e as leituras disponíveis. Não afirmam que a esteira
está rodando, que todo nó físico está conectado ou que a acurácia do detector foi validada.

## 5. Operação

```bash
.venv/bin/python src-production/api.py --db hub.db --porta 8080 --host 127.0.0.1
```

Para bind fora do loopback, informe token Bearer. Os serviços do rig e da ponte são apontados por
`PNAAT_RIG` e `PNAAT_PONTE`; a API falha explicitamente quando um deles não responde. Para uma
instalação local sem esses serviços, suba a API contra um banco local novo (o `/api/health` cria o
schema) e use as rotas de consulta.

## 6. O que fica fora

Não há no site comando de atuador, partida/parada da esteira, retreinamento, Grafana, gestão de
usuários ou garantia de retenção de imagens. Esses limites são de produto, não pendências de implementação.
