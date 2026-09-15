-- Esquema do hub (docs/dados-telemetria.md §2) com as duas mudancas aprovadas:
--   1) taxonomia_defeito ganha classe/dominio/aql_ref: o catalogo passa a ser DADO de referencia
--      ligado ao vocabulario por dominio (D-28), em vez de um segundo sistema de nomes;
--   2) inspecao_vista ganha `papel` (D-30) e o dominio passa a aceitar NULL, porque o check
--      dimensional do topo nao pertence a dominio nenhum.
-- Invariantes que valem no banco, nao so no codigo:
--   * papel='decide' exige dominio (nao se decide sem dizer em que dominio);
--   * vista='topo' NUNCA decide (D-23/D-30).
-- O restante do DDL segue a fonte normativa sem alteracao.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS lote (
  lote_id TEXT PRIMARY KEY,
  data_inicio TEXT NOT NULL,
  turno TEXT,
  observacoes TEXT
);

CREATE TABLE IF NOT EXISTS ponto_linha (
  ponto_id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  tipo TEXT
);

CREATE TABLE IF NOT EXISTS taxonomia_defeito (
  codigo TEXT PRIMARY KEY,
  descricao TEXT NOT NULL,
  classe TEXT CHECK(classe IS NULL OR classe IN
    ('normal','tampa_ausente','defeito_tampa','deformidade','inconclusivo')),
  dominio TEXT CHECK(dominio IS NULL OR dominio IN ('tampa','corpo')),
  severidade TEXT CHECK(severidade IN ('critico','major','minor')),
  vista_esperada TEXT,
  aql_ref TEXT
);

CREATE TABLE IF NOT EXISTS item (
  item_id TEXT PRIMARY KEY,
  lote_id TEXT REFERENCES lote(lote_id),
  timestamp_trigger TEXT NOT NULL,
  velocidade_rig_mm_s REAL,
  fonte_trigger TEXT CHECK(fonte_trigger IN ('e18_d80nk','vl53l0x','ambos_correlacionados')),
  status_tampa TEXT CHECK(status_tampa IN ('ok','defeito','inconclusivo','erro_processamento')),
  status_corpo TEXT CHECK(status_corpo IN ('ok','defeito','inconclusivo','erro_processamento')),
  discordancia_lateral INTEGER DEFAULT 0 CHECK(discordancia_lateral IN (0,1)),
  status_final TEXT CHECK(status_final IN ('ok','defeito','inconclusivo','erro_processamento')),
  motivo_inconclusivo TEXT,
  qualidade_registro TEXT CHECK(qualidade_registro IN
    ('completo','parcial_1_vista_faltante','timestamp_divergente','evidencia_insuficiente','invalido')),
  is_golden INTEGER DEFAULT 0 CHECK(is_golden IN (0,1)),
  score_consistencia REAL,
  -- contrato do evento (docs/arquitetura.md): origem, localizacao e versao do contrato
  equipamento TEXT,
  localizacao TEXT,
  versao_contrato TEXT NOT NULL DEFAULT '1'
);

CREATE TABLE IF NOT EXISTS inspecao_vista (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  vista TEXT CHECK(vista IN ('topo','lateral1','lateral2')),
  dominio TEXT CHECK(dominio IS NULL OR dominio IN ('tampa','corpo')),
  papel TEXT NOT NULL DEFAULT 'decide' CHECK(papel IN ('decide','auxiliar','fallback')),
  vista_disponivel INTEGER DEFAULT 1 CHECK(vista_disponivel IN (0,1)),
  qualidade_imagem TEXT CHECK(qualidade_imagem IN ('adequada','baixa','invalida','nao_avaliada')),
  status_vista TEXT CHECK(status_vista IN ('ok','defeito','inconclusivo','erro_processamento')),
  codigo_defeito TEXT REFERENCES taxonomia_defeito(codigo),
  confianca REAL,
  caminho_evidencia TEXT,
  timestamp_captura TEXT,
  latencia_ms INTEGER,
  medida_mm REAL,
  pixels_saturados_pct REAL,
  score_cutpaste REAL,
  score_ts REAL,
  -- referencia da evidencia (caminho ja existe em caminho_evidencia): o hash fecha a cadeia
  sha256_evidencia TEXT,
  CHECK (papel <> 'decide' OR dominio IS NOT NULL),
  CHECK (NOT (papel = 'decide' AND vista = 'topo'))
);

-- Eventos de gatilho (RF-01.1). Existe separado do item porque o disparo que NAO virou item e
-- justamente o que precisa ser registrado: falso disparo e duplicata sao observaveis aqui, e a
-- perda de deteccao (item passou sem gatilho) NAO e — ela exige referencia externa (encoder).
CREATE TABLE IF NOT EXISTS evento_gatilho (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  ponto_id INTEGER REFERENCES ponto_linha(ponto_id),
  fonte TEXT CHECK(fonte IN ('e18_d80nk','vl53l0x','ambos_correlacionados','nao_declarada')),
  estado TEXT NOT NULL CHECK(estado IN ('aceito','duplicado','falso','invalido')),
  item_id TEXT REFERENCES item(item_id),
  motivo TEXT,
  debounce_ms INTEGER
);

CREATE TABLE IF NOT EXISTS evento_ambiental (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  ponto_id INTEGER REFERENCES ponto_linha(ponto_id),
  temperatura REAL,
  umidade REAL,
  qualidade_ar REAL
);

CREATE TABLE IF NOT EXISTS heartbeat_no (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ponto_id INTEGER REFERENCES ponto_linha(ponto_id),
  timestamp TEXT NOT NULL,
  status TEXT CHECK(status IN ('online','degradado','offline')),
  fila_pendente INTEGER,
  latencia_envio_ms INTEGER
);

CREATE TABLE IF NOT EXISTS correcao_operador (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  decisao_original TEXT,
  decisao_corrigida TEXT,
  corrigido_por TEXT,
  timestamp TEXT
);

CREATE TABLE IF NOT EXISTS evento_rejeicao (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  tentativa INTEGER DEFAULT 1,
  timestamp_ordenado TEXT NOT NULL,
  timestamp_confirmado TEXT,
  timestamp_timeout TEXT,
  status_ordem TEXT CHECK(status_ordem IN ('pendente','emitida','falha')),
  status TEXT CHECK(status IN ('pendente','confirmada','falha','timeout')),
  via_sensor TEXT
);

CREATE TABLE IF NOT EXISTS descritor_geometrico (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES item(item_id),
  vista TEXT CHECK(vista IN ('topo','lateral1','lateral2')),
  hu1 REAL, hu2 REAL, hu3 REAL, hu4 REAL, hu5 REAL, hu6 REAL, hu7 REAL,
  compacidade REAL,
  simetria_axial REAL,
  razao_dimensao REAL,
  anomaly_score REAL
);

-- Evidencia do que sustentou a decisao (D-30). Uma linha por grandeza medida, ligada a linha de
-- inspecao que ela explica: e o rastro, nao o voto. Sem esta tabela, a medicao geometrica vira
-- numero em memoria que morre com o processo.
--
-- Por que a MESMA medicao aparece em mais de uma linha: a medicao geometrica e da VISTA (um recorte),
-- e cada vista tem uma linha de inspecao por dominio. Se a mesma medida sustenta a decisao da tampa
-- e a do corpo, ela aparece nas duas linhas — isso e o rastro de duas decisoes, nao duplicacao de
-- dado. O calculo, esse sim, e feito uma unica vez por vista (orquestracao).
CREATE TABLE IF NOT EXISTS evidencia (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  inspecao_vista_id INTEGER REFERENCES inspecao_vista(id),
  grandeza TEXT NOT NULL,
  valor REAL,
  unidade TEXT NOT NULL,
  origem TEXT NOT NULL CHECK(origem IN ('classificador','geometria')),
  papel TEXT NOT NULL CHECK(papel IN ('decide','auxiliar','fallback')),
  metodo TEXT NOT NULL,
  fonte TEXT
);

CREATE INDEX IF NOT EXISTS idx_evidencia_inspecao ON evidencia(inspecao_vista_id);
CREATE INDEX IF NOT EXISTS idx_item_lote ON item(lote_id);
CREATE INDEX IF NOT EXISTS idx_inspecao_item ON inspecao_vista(item_id);
CREATE INDEX IF NOT EXISTS idx_heartbeat_ponto_tempo ON heartbeat_no(ponto_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_gatilho_tempo ON evento_gatilho(timestamp);

-- Catalogo de referencia (dados-telemetria §4). Os codigos de tampa apontam para as LATERAIS:
-- o topo nao decide a tampa (D-23/D-30). ERRO_PROCESSAMENTO nao tem classe: e categoria tecnica.
INSERT OR IGNORE INTO taxonomia_defeito (codigo, descricao, classe, dominio, severidade, vista_esperada, aql_ref) VALUES
 ('TAMPA_AUSENTE','Tampa completamente ausente','tampa_ausente','tampa','critico','lateral1,lateral2','0%'),
 ('TAMPA_DEFEITO','Defeito de tampa (mal rosqueada, danificada ou aberta)','defeito_tampa','tampa','major','lateral1,lateral2','2,5%'),
 ('TAMPA_MAL_ROSQUEADA','Tampa desalinhada ou parcialmente rosqueada','defeito_tampa','tampa','major','lateral1,lateral2','2,5%'),
 ('TAMPA_DANIFICADA','Tampa fisicamente danificada','defeito_tampa','tampa','major','lateral1,lateral2','2,5%'),
 ('TAMPA_ABERTA','Tampa presente porem nao selada','defeito_tampa','tampa','major','lateral1,lateral2','2,5%'),
 ('CORPO_DEFORMADO_SEVERO','Deformidade que compromete a integridade','deformidade','corpo','critico','lateral1,lateral2','0%'),
 ('CORPO_DEFORMADO_LEVE','Deformidade estetica sem risco de vazamento','deformidade','corpo','minor','lateral1,lateral2','4,0%'),
 ('ERRO_PROCESSAMENTO','Falha de captura ou inferencia (categoria tecnica)',NULL,NULL,NULL,'qualquer',NULL);

-- consulta de correcoes por item (detalhe da Investigacao): sem indice, cada /api/item/<id> le a
-- tabela inteira de correcoes
CREATE INDEX IF NOT EXISTS idx_correcao_item ON correcao_operador(item_id);
