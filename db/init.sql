-- Manufacturing AX Agent — DB 초기화
-- PostgreSQL + TimescaleDB + pgvector
-- docker-compose up 시 자동 실행

-- 확장 활성화
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. 마스터 테이블 (참조 데이터)
-- ============================================

-- 설비 마스터 (3대)
CREATE TABLE equipment (
  equipment_id   VARCHAR(7)    PRIMARY KEY,
  equipment_type VARCHAR(30)   NOT NULL DEFAULT 'CNC Milling Machine',
  status         VARCHAR(10)   NOT NULL DEFAULT 'active',
  experiment_range VARCHAR(20)
);

INSERT INTO equipment (equipment_id, experiment_range) VALUES
  ('CNC-001', 'exp01~06'),
  ('CNC-002', 'exp07~12'),
  ('CNC-003', 'exp13~18');

-- 고장코드 마스터 (4종)
CREATE TABLE failure_codes (
  failure_code     VARCHAR(30)   PRIMARY KEY,
  description      TEXT          NOT NULL,
  severity         VARCHAR(10)   NOT NULL,
  failure_category VARCHAR(20)   NOT NULL
);

INSERT INTO failure_codes VALUES
  ('TOOL_WEAR_001',        '엔드밀 마모로 인한 가공 품질 저하',      'critical', 'tool_wear'),
  ('SPINDLE_OVERHEAT_001', '주축 과열로 인한 베어링 손상 위험',      'critical', 'thermal'),
  ('CLAMP_PRESSURE_001',   '클램프 압력 저하로 공작물 고정 불량',    'warning',  'mechanical'),
  ('COOLANT_LOW_001',      '절삭유 부족으로 가공면 품질 저하 위험',  'warning',  'fluid');

-- 부품 마스터 (5종) — it-data-synthesis-schema.md 기준
CREATE TABLE parts (
  part_id        VARCHAR(10)   PRIMARY KEY,
  part_name      VARCHAR(50)   NOT NULL,
  unit_cost      INT           NOT NULL,
  lead_time_days INT           NOT NULL,
  reorder_point  INT           NOT NULL
);

INSERT INTO parts VALUES
  ('P001', 'Endmill 6mm Carbide',       45000,  3, 5),
  ('P002', 'Spindle Bearing Set',       280000, 7, 2),
  ('P003', 'Coolant (Water-Soluble, 20L)', 35000, 2, 3),
  ('P004', 'Clamp Bolt Set',            12000,  1, 4),
  ('P005', 'Air Filter',                8000,   1, 3);

-- 센서 메타 (42개 유효 센서)
CREATE TABLE sensors (
  sensor_id    VARCHAR(40)   PRIMARY KEY,
  sensor_type  VARCHAR(20)   NOT NULL,
  axis         VARCHAR(5)    NOT NULL,
  unit         VARCHAR(20)
);

-- X축 센서 (11개)
INSERT INTO sensors VALUES
  ('X1_ActualPosition',      'position',      'X1', 'mm'),
  ('X1_ActualVelocity',      'velocity',      'X1', 'mm/s'),
  ('X1_ActualAcceleration',  'acceleration',  'X1', 'mm/s²'),
  ('X1_CommandPosition',     'position',      'X1', 'mm'),
  ('X1_CommandVelocity',     'velocity',      'X1', 'mm/s'),
  ('X1_CommandAcceleration', 'acceleration',  'X1', 'mm/s²'),
  ('X1_CurrentFeedback',     'current',       'X1', 'A'),
  ('X1_DCBusVoltage',        'voltage',       'X1', 'V'),
  ('X1_OutputCurrent',       'current',       'X1', 'A'),
  ('X1_OutputVoltage',       'voltage',       'X1', 'V'),
  ('X1_OutputPower',         'power',         'X1', 'kW');

-- Y축 센서 (11개)
INSERT INTO sensors VALUES
  ('Y1_ActualPosition',      'position',      'Y1', 'mm'),
  ('Y1_ActualVelocity',      'velocity',      'Y1', 'mm/s'),
  ('Y1_ActualAcceleration',  'acceleration',  'Y1', 'mm/s²'),
  ('Y1_CommandPosition',     'position',      'Y1', 'mm'),
  ('Y1_CommandVelocity',     'velocity',      'Y1', 'mm/s'),
  ('Y1_CommandAcceleration', 'acceleration',  'Y1', 'mm/s²'),
  ('Y1_CurrentFeedback',     'current',       'Y1', 'A'),
  ('Y1_DCBusVoltage',        'voltage',       'Y1', 'V'),
  ('Y1_OutputCurrent',       'current',       'Y1', 'A'),
  ('Y1_OutputVoltage',       'voltage',       'Y1', 'V'),
  ('Y1_OutputPower',         'power',         'Y1', 'kW');

-- Z축 센서 (6개, 전기 피드백 4개 제외)
INSERT INTO sensors VALUES
  ('Z1_ActualPosition',      'position',      'Z1', 'mm'),
  ('Z1_ActualVelocity',      'velocity',      'Z1', 'mm/s'),
  ('Z1_ActualAcceleration',  'acceleration',  'Z1', 'mm/s²'),
  ('Z1_CommandPosition',     'position',      'Z1', 'mm'),
  ('Z1_CommandVelocity',     'velocity',      'Z1', 'mm/s'),
  ('Z1_CommandAcceleration', 'acceleration',  'Z1', 'mm/s²');

-- S축/주축 센서 (11개, SystemInertia 제외)
INSERT INTO sensors VALUES
  ('S1_ActualPosition',      'position',      'S1', 'mm'),
  ('S1_ActualVelocity',      'velocity',      'S1', 'rpm'),
  ('S1_ActualAcceleration',  'acceleration',  'S1', 'rpm/s'),
  ('S1_CommandPosition',     'position',      'S1', 'mm'),
  ('S1_CommandVelocity',     'velocity',      'S1', 'rpm'),
  ('S1_CommandAcceleration', 'acceleration',  'S1', 'rpm/s'),
  ('S1_CurrentFeedback',     'current',       'S1', 'A'),
  ('S1_DCBusVoltage',        'voltage',       'S1', 'V'),
  ('S1_OutputCurrent',       'current',       'S1', 'A'),
  ('S1_OutputVoltage',       'voltage',       'S1', 'V'),
  ('S1_OutputPower',         'power',         'S1', 'kW');

-- ============================================
-- 2. 시계열 테이블 (TimescaleDB Hypertable)
-- ============================================

-- 센서 시계열 (와이드 44컬럼)
CREATE TABLE sensor_readings (
  timestamp        TIMESTAMPTZ   NOT NULL,
  equipment_id     VARCHAR(7)    NOT NULL,

  -- X축 (11개)
  x1_actual_position       FLOAT8,
  x1_actual_velocity       FLOAT8,
  x1_actual_acceleration   FLOAT8,
  x1_command_position      FLOAT8,
  x1_command_velocity      FLOAT8,
  x1_command_acceleration  FLOAT8,
  x1_current_feedback      FLOAT8,
  x1_dc_bus_voltage        FLOAT8,
  x1_output_current        FLOAT8,
  x1_output_voltage        FLOAT8,
  x1_output_power          FLOAT8,

  -- Y축 (11개)
  y1_actual_position       FLOAT8,
  y1_actual_velocity       FLOAT8,
  y1_actual_acceleration   FLOAT8,
  y1_command_position      FLOAT8,
  y1_command_velocity      FLOAT8,
  y1_command_acceleration  FLOAT8,
  y1_current_feedback      FLOAT8,
  y1_dc_bus_voltage        FLOAT8,
  y1_output_current        FLOAT8,
  y1_output_voltage        FLOAT8,
  y1_output_power          FLOAT8,

  -- Z축 (6개, 전기 피드백 4개 제외)
  z1_actual_position       FLOAT8,
  z1_actual_velocity       FLOAT8,
  z1_actual_acceleration   FLOAT8,
  z1_command_position      FLOAT8,
  z1_command_velocity      FLOAT8,
  z1_command_acceleration  FLOAT8,

  -- S축/주축 (11개, SystemInertia 제외)
  s1_actual_position       FLOAT8,
  s1_actual_velocity       FLOAT8,
  s1_actual_acceleration   FLOAT8,
  s1_command_position      FLOAT8,
  s1_command_velocity      FLOAT8,
  s1_command_acceleration  FLOAT8,
  s1_current_feedback      FLOAT8,
  s1_dc_bus_voltage        FLOAT8,
  s1_output_current        FLOAT8,
  s1_output_voltage        FLOAT8,
  s1_output_power          FLOAT8,

  -- M1 메타 (2개, sequence_number 제외)
  m1_current_program_number INT,
  m1_current_feedrate       FLOAT8,

  -- 가공 공정
  machining_process  VARCHAR(20),

  PRIMARY KEY (timestamp, equipment_id)
);

-- TimescaleDB 하이퍼테이블 변환
SELECT create_hypertable('sensor_readings', 'timestamp', if_not_exists => TRUE);

-- 7일 자동 압축 정책
ALTER TABLE sensor_readings SET (timescaledb.compress = true);
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');

-- 이상탐지 결과 (F2 출력)
CREATE TABLE anomaly_scores (
  timestamp        TIMESTAMPTZ   NOT NULL,
  equipment_id     VARCHAR(7)    NOT NULL,
  anomaly_score    FLOAT8        NOT NULL,
  is_anomaly       BOOLEAN       NOT NULL,
  model_version    VARCHAR(20),
  predicted_failure_code VARCHAR(30) REFERENCES failure_codes(failure_code),
  confidence       FLOAT8,
  if_score         FLOAT8,                             -- Isolation Forest 단독 점수 (0~1)
  forecast_score   FLOAT8,                             -- ADR-007: 1D-CNN 예측 점수 (0~1)

  PRIMARY KEY (timestamp, equipment_id)
);

SELECT create_hypertable('anomaly_scores', 'timestamp', if_not_exists => TRUE);

-- ============================================
-- 3. 이벤트 테이블 (IT 데이터)
-- ============================================

-- MES 작업지시
CREATE TABLE mes_work_orders (
  work_order_id    VARCHAR(15)   PRIMARY KEY,
  equipment_id     VARCHAR(7)    NOT NULL REFERENCES equipment(equipment_id),
  experiment_id    INT           NOT NULL,
  product_type     VARCHAR(20)   NOT NULL DEFAULT 'WAX_BLOCK_6MM',
  start_time       TIMESTAMPTZ   NOT NULL,
  end_time         TIMESTAMPTZ,
  due_date         TIMESTAMPTZ   NOT NULL,
  priority         VARCHAR(10)   NOT NULL CHECK (priority IN ('normal', 'urgent', 'critical')),
  status           VARCHAR(10)   NOT NULL CHECK (status IN ('completed', 'aborted'))
);

CREATE INDEX idx_wo_equipment ON mes_work_orders(equipment_id);
CREATE INDEX idx_wo_status ON mes_work_orders(status);

-- 정비 이벤트 (CMMS)
CREATE TABLE maintenance_events (
  event_id         VARCHAR(15)   PRIMARY KEY,
  equipment_id     VARCHAR(7)    NOT NULL REFERENCES equipment(equipment_id),
  event_type       VARCHAR(15)   NOT NULL CHECK (event_type IN ('corrective', 'preventive')),
  timestamp        TIMESTAMPTZ   NOT NULL,
  failure_code     VARCHAR(30)   REFERENCES failure_codes(failure_code),
  description      TEXT,
  duration_min     INT           NOT NULL,
  technician_id    VARCHAR(10)   NOT NULL,
  parts_used       VARCHAR(50),
  work_order_id    VARCHAR(15)   REFERENCES mes_work_orders(work_order_id)
);

CREATE INDEX idx_maint_equipment ON maintenance_events(equipment_id);
CREATE INDEX idx_maint_failure ON maintenance_events(failure_code);
CREATE INDEX idx_maint_type ON maintenance_events(event_type);

-- ERP 부품 재고 스냅샷
CREATE TABLE erp_inventory (
  snapshot_date      DATE          NOT NULL,
  part_id            VARCHAR(10)   NOT NULL REFERENCES parts(part_id),
  stock_quantity     INT           NOT NULL,
  reorder_point      INT           NOT NULL,
  lead_time_days     INT           NOT NULL,
  unit_cost          INT           NOT NULL,
  weekly_consumption INT           NOT NULL DEFAULT 0,
  reorder_triggered  BOOLEAN       NOT NULL DEFAULT FALSE,

  PRIMARY KEY (snapshot_date, part_id)
);

CREATE INDEX idx_inv_part ON erp_inventory(part_id);

-- ============================================
-- 4. 벡터 검색 테이블 (pgvector)
-- ============================================

-- 정비 매뉴얼 임베딩 (Phase 3에서 데이터 채움)
CREATE TABLE document_embeddings (
  chunk_id         VARCHAR(20)   PRIMARY KEY,
  manual_id        VARCHAR(10)   NOT NULL,
  chunk_number     INT           NOT NULL DEFAULT 0,
  title            VARCHAR(100),
  text_content     TEXT          NOT NULL,
  embedding        VECTOR(384),  -- paraphrase-multilingual-MiniLM-L12-v2 (384차원, 로컬 무료)
  created_at       TIMESTAMPTZ   DEFAULT NOW(),

  UNIQUE (manual_id, chunk_number)
);

-- HNSW 인덱스 (cosine 유사도)
CREATE INDEX idx_doc_embedding ON document_embeddings
  USING hnsw (embedding vector_cosine_ops);

-- ============================================
-- 5. LLM 조치 리포트 저장 (F5 결과)
-- ============================================

CREATE TABLE llm_action_reports (
  id              SERIAL        PRIMARY KEY,
  equipment_id    VARCHAR(7)    NOT NULL,
  timestamp       TIMESTAMPTZ   NOT NULL,
  recommendation  VARCHAR(10)   NOT NULL,
  confidence      FLOAT8        NOT NULL,
  reasoning       TEXT,
  action_steps    TEXT,          -- JSON 배열 문자열
  parts_needed    TEXT,          -- JSON 배열 문자열
  predicted_failure_code VARCHAR(30),
  estimated_downtime_min INT,
  created_at      TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX idx_action_equipment ON llm_action_reports(equipment_id);
CREATE INDEX idx_action_timestamp ON llm_action_reports(timestamp DESC);

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
  RAISE NOTICE '=== Manufacturing AX Agent DB 초기화 완료 ===';
  RAISE NOTICE '마스터: equipment(3), failure_codes(4), parts(5), sensors(42)';
  RAISE NOTICE '시계열: sensor_readings(hypertable), anomaly_scores(hypertable)';
  RAISE NOTICE '이벤트: mes_work_orders, maintenance_events, erp_inventory';
  RAISE NOTICE '벡터: document_embeddings (pgvector HNSW)';
END $$;
