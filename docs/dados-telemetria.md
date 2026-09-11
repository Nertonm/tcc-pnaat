# Dados e telemetria

## 1. Priorização

| Eixo | Prioridade | Impacto |
|---|---|---|
| Arquitetura e schema de dados | Alta | Alto |
| Dashboard e notificação | Alta | Alto |
| Taxonomia de defeitos | Alta | Alto |
| Sincronização de relógio | Alta | Médio-alto |
| Telemetria de saúde | Alta | Médio-alto |
| Qualidade de dados | Alta | Médio-alto |
| Genealogia e relacionamento | Média | Médio |
| Dados sintéticos leves | Alta | Médio-alto |
| Detecção simples de drift | Média | Médio |
| Aprendizado ativo com humano no ciclo | Parcial | Médio |
| Benchmark comercial para o pitch | Alta | Médio |
| Detecção one-class | Parcial | Alto, com risco |
| Re-identificação visual | Fora de escopo | Baixo |
| Câmera como nó distribuído | Fora de escopo | Baixo |

## 2. Schema do hub

Motor: SQLite, suficiente para o volume de bancada. Evolução para série temporal fica como extensão.

```sql
CREATE TABLE lote (
  lote_id TEXT PRIMARY KEY,
  data_inicio TEXT NOT NULL,
  turno TEXT,
  observacoes TEXT
);

CREATE TABLE ponto_linha (
  ponto_id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  tipo TEXT
);

CREATE TABLE taxonomia_defeito (
  codigo TEXT PRIMARY KEY,
  descricao TEXT NOT NULL,
  severidade TEXT CHECK(severidade IN ('critico','major','minor')),
  vista_esperada TEXT
);

CREATE TABLE item (
  item_id TEXT PRIMARY KEY,
  lote_id TEXT REFERENCES lote(lote_id),
  timestamp_trigger TEXT NOT NULL,
  velocidade_rig_mm_s REAL,
  fonte_trigger TEXT CHECK(fonte_trigger IN ('e18_d80nk','vl53l0x','ambos_correlacionados')),
  status_final TEXT CHECK(status_final IN ('ok','defeito','erro_processamento')),
  qualidade_registro TEXT CHECK(qualidade_registro IN ('completo','parcial_1_vista_faltante','timestamp_divergente')),
  is_golden INTEGER DEFAULT 0,
  score_consistencia REAL
);

CREATE TABLE inspecao_vista (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  vista TEXT CHECK(vista IN ('topo','lateral1','lateral2')),
  codigo_defeito TEXT REFERENCES taxonomia_defeito(codigo),
  confianca REAL,
  caminho_evidencia TEXT,
  timestamp_captura TEXT,
  latencia_ms INTEGER,
  medida_mm REAL,
  pixels_saturados_pct REAL,
  score_cutpaste REAL,
  score_ts REAL
);

CREATE TABLE evento_ambiental (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  ponto_id INTEGER REFERENCES ponto_linha(ponto_id),
  temperatura REAL,
  umidade REAL,
  qualidade_ar REAL
);

CREATE TABLE heartbeat_no (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ponto_id INTEGER REFERENCES ponto_linha(ponto_id),
  timestamp TEXT NOT NULL,
  status TEXT CHECK(status IN ('online','degradado','offline')),
  fila_pendente INTEGER,
  latencia_envio_ms INTEGER
);

CREATE TABLE correcao_operador (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  decisao_original TEXT,
  decisao_corrigida TEXT,
  corrigido_por TEXT,
  timestamp TEXT
);

CREATE TABLE evento_sinalizacao (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  notification_id TEXT NOT NULL UNIQUE,
  timestamp_criado TEXT NOT NULL,
  timestamp_enviado TEXT,
  timestamp_entregue TEXT,
  timestamp_lido TEXT,
  status TEXT CHECK(status IN ('pendente','enviada','entregue','lida','falha')),
  canal TEXT NOT NULL,
  tentativa INTEGER NOT NULL DEFAULT 1,
  evidencia_ref TEXT
);

CREATE TABLE descritor_geometrico (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  vista TEXT CHECK(vista IN ('topo','lateral1','lateral2')),
  hu1 REAL, hu2 REAL, hu3 REAL, hu4 REAL, hu5 REAL, hu6 REAL, hu7 REAL,
  compacidade REAL,
  simetria_axial REAL,
  razao_dimensao REAL,
  anomaly_score REAL
);

CREATE INDEX idx_item_lote ON item(lote_id);
CREATE INDEX idx_inspecao_item ON inspecao_vista(item_id);
CREATE INDEX idx_heartbeat_ponto_tempo ON heartbeat_no(ponto_id, timestamp);
```

A coluna `qualidade_registro` liga a confiabilidade do nó ao dado final. O registro `evento_sinalizacao` preserva tentativa, estado de entrega e evidência; timeout e retry são controlados pela política do canal. A definição está em `docs/requisitos/04-atuacao-seguranca.md`.

## 3. Consultas analíticas

1. Taxa de defeito por lote.
2. Defeitos mais frequentes por período e severidade.
3. Correlação entre defeito e variável ambiental em janela curta.
4. Tendência temporal da taxa de defeito por hora.
5. Itens de um lote com defeito crítico, com evidência.
6. Saúde dos nós na última hora.
7. Latência média e máxima de decisão por vista.
8. Itens com correção manual, para auditoria.
9. Notificações não entregues ou falhas de sinalização, como eventos de qualidade.
10. Taxa de disparo falso ou perda de detecção do gatilho, por fonte (E18-D80NK vs VL53L0X vs correlacionado).
11. Percentual de pixels saturados por vista, comparando capturas com e sem lente difusora.

As consultas SQL estão detalhadas junto ao schema no histórico do repositório.

## 4. Taxonomia de defeitos

Referência conceitual: lógica de nível de qualidade aceitável (AQL), sem implementar plano de amostragem completo.

| Código | Descrição | Severidade | Vista | AQL de referência |
|---|---|---|---|---|
| TAMPA_AUSENTE | Tampa completamente ausente | critico | topo | 0% |
| TAMPA_MAL_ROSQUEADA | Tampa desalinhada ou parcialmente rosqueada | major | topo | 2,5% |
| CORPO_DEFORMADO_SEVERO | Deformidade que compromete a integridade | critico | lateral | 0% |
| CORPO_DEFORMADO_LEVE | Deformidade estética sem risco de vazamento | minor | lateral | 4,0% |
| ERRO_PROCESSAMENTO | Falha de captura ou inferência, categoria técnica | - | qualquer | - |

## 5. Recomendações de implementação

1. Schema relacional, taxonomia e dashboard com notificação transformam o conjunto em sistema de dados analisável.
2. Detecção one-class como camada de anomalia desconhecida, isolada em PoC com go/no-go de latência.
3. Augmentação leve do dataset de peças 3D e detecção simples de drift.
4. Qualidade de dados e heartbeat integrados ao dashboard, para que a resiliência seja métrica.
5. Alternativas avaliadas e descartadas documentadas com justificativa.

## 6. Fora do escopo

Blockchain, gêmeo digital completo, PTP ou IEEE 1588 (relógio externo e sincronização por rede resolvem a necessidade), backbones pesados na borda, pipeline completo de MLOps, MES ou ISA-95 completo e redes sensíveis ao tempo.

## 7. Referências

- ISO 2859-1, referência conceitual para a taxonomia de defeitos.
- MVTec AD, benchmark de detecção de anomalia industrial.
- Documentação oficial do ntfy.
- PatchCore e FastFlow como referências de detecção one-class, com métricas citadas somente após verificação no dataset próprio.
- Domain randomization e sim-to-real, como referência metodológica.
