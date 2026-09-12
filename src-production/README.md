# Inspeção Automatizada Multi-View com Rastreabilidade de Anomalias em Linha de Produção

**Sigla do projeto: `iamralp`** (nome do pacote no codigo).

Arvore de **codigo de producao**. As PoCs ficam onde estao (`../code-workspace/src/pocs`) como
historico congelado: nada daqui importa de la, e nada de la deve ser promovido para ca sem
reescrita tipada.

## O que ja existe
| Arquivo | Responsabilidade |
|---|---|
| `dominio.py` | Dominios, vocabulario de classes por dominio (D-28), evidencia tipada e o contrato do evento |
| `decisao.py` | Decisao por vista (D-30): o classificador decide, a geometria e auxiliar, o fallback roteia e nunca aprova |
| `conformidade.py` | Regra por dominio (D-04/D-29): defeito em qualquer vista reprova, aprovacao exige o rig completo, discordancia preservada |
| `captura.py` | Monta as vistas do mesmo `item_id`; verificacao de posicionamento fail-closed (NCC + tolerancia em px) |
| `identidade.py` | Formato e geracao do `item_id` (`<lote>-<sequencia>`), com sequencia ancorada no banco |
| `registro.py` | Persistencia idempotente por `item_id`; recusa evidencia divergente |
| `painel.py` | As 14 consultas analiticas de `docs/dados-telemetria.md` secao 3, somente leitura |
| `orquestracao.py` | Pipeline unica (captura -> decisao -> conformidade -> registro) e entry point |
| `esquema.sql` | Esquema do hub, com as invariantes no banco (o topo nunca decide; decidir exige dominio) |

## Regras desta arvore

- Contratos **tipados** (dataclass/Enum/Protocol). Nenhuma funcao devolve `dict[str, Any]`.
- **Uma** pipeline: captura -> decisao por vista -> fusao por dominio -> registro -> painel.
- Toda grandeza que decide carrega `Evidencia.fonte` (`arquivo:linha` ou protocolo); sem fonte e
  provisoria e aparece marcada como tal (D-24).
- Ausencia de evidencia e `inconclusivo`, nunca aprovacao silenciosa (D-04).

## Como rodar

```sh
make test          # a partir desta pasta
make instalacao    # instala o pacote em modo editavel no venv da raiz
```
