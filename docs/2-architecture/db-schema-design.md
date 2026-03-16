# DB 스키마 설계 (PostgreSQL + Neo4j)

> PostgreSQL(TimescaleDB + pgvector)에는 시계열/이벤트/벡터 데이터를,
> Neo4j에는 정적 지식 그래프를 저장한다. (ADR-003: DB 2개 제한)

---

## 1. 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Neo4j = 관계** | "무엇이 무엇과 연결되는가" (정적 지식 그래프) |
| **PostgreSQL = 시간** | "언제 어떤 값이었는가" (동적 시계열 + 이벤트) |
| **마스터 데이터 중복** | failure_code, part 등은 양쪽에 저장 (PG: FK, Neo4j: 순회) |
| **2개 DB 제한** | 1인 개발 운영 부담 최소화 (ADR-003) |

---

## 2. PostgreSQL 테이블 설계

### 2.1 센서 시계열 — `sensor_readings` (TimescaleDB Hypertable)

F1에서 수집하는 OT 센서 데이터. **와이드 테이블** 방식으로 설계.

> **와이드 vs 롱 테이블 결정:**
> 롱 테이블(sensor_id, value)은 센서 추가가 유연하지만, 42개 센서를 매번 42행으로 저장하면
> 25,286 × 42 = 100만+ 행이 되어 조인 비용이 큼. CNC 센서 구성이 고정이므로 와이드 테이블 채택.

```sql
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

-- TimescaleDB 하이퍼테이블 변환 (1일 단위 파티션)
SELECT create_hypertable('sensor_readings', 'timestamp', if_not_exists => TRUE);

-- 7일 이후 자동 압축
ALTER TABLE sensor_readings SET (timescaledb.compress = true);
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');
```

**컬럼 수:** 유효 센서 39개(X11+Y11+Z6+S11) + M1 메타 2개 + machining_process 1개 + PK 2개(timestamp, equipment_id) = **44개**
**예상 행 수:** ~25,286행 (현재), 운영 시 5초 폴링 × 설비 3대 = 하루 ~51,840행

---

### 2.2 이상탐지 결과 — `anomaly_scores` (TimescaleDB Hypertable)

F2에서 출력하는 이상 감지 및 예측 결과.

```sql
CREATE TABLE anomaly_scores (
  timestamp        TIMESTAMPTZ   NOT NULL,
  equipment_id     VARCHAR(7)    NOT NULL,
  anomaly_score    FLOAT8        NOT NULL,  -- 0.0 ~ 1.0
  is_anomaly       BOOLEAN       NOT NULL,  -- 임계치 초과 여부
  model_version    VARCHAR(20),              -- 사용된 모델 버전
  predicted_failure_code VARCHAR(30),         -- 예측된 고장코드 (nullable)
  confidence       FLOAT8,                   -- 예측 신뢰도

  PRIMARY KEY (timestamp, equipment_id)
);

SELECT create_hypertable('anomaly_scores', 'timestamp', if_not_exists => TRUE);
```

---

### 2.3 MES 작업지시 — `mes_work_orders`

```sql
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
```

**레코드:** 18건 (실험 1:1)

---

### 2.4 정비 이벤트 — `maintenance_events`

```sql
CREATE TABLE maintenance_events (
  event_id         VARCHAR(15)   PRIMARY KEY,
  equipment_id     VARCHAR(7)    NOT NULL REFERENCES equipment(equipment_id),
  event_type       VARCHAR(15)   NOT NULL CHECK (event_type IN ('corrective', 'preventive')),
  timestamp        TIMESTAMPTZ   NOT NULL,
  failure_code     VARCHAR(30)   REFERENCES failure_codes(failure_code),
  description      TEXT,
  duration_min     INT           NOT NULL,
  technician_id    VARCHAR(10)   NOT NULL,
  parts_used       VARCHAR(50),  -- 쉼표 구분 part_id 목록 (예: "P001,P005")
  work_order_id    VARCHAR(15)   REFERENCES mes_work_orders(work_order_id)
);

CREATE INDEX idx_maint_equipment ON maintenance_events(equipment_id);
CREATE INDEX idx_maint_failure ON maintenance_events(failure_code);
CREATE INDEX idx_maint_type ON maintenance_events(event_type);
```

**레코드:** 39건 (교정 12 + 예방 27)

> **parts_used를 별도 테이블로 정규화할지?**
> 현재 "P001,P005" 같은 CSV 문자열. 39건 규모에서는 정규화 비용 > 이점.
> **분리 기준:** 데이터 규모가 아니라 **쿼리 패턴**. Phase 3에서 부품별 소모량 집계 쿼리가
> 필요해지면 `maintenance_parts(event_id, part_id, quantity)` 조인 테이블로 분리.

---

### 2.5 ERP 재고 스냅샷 — `erp_inventory`

```sql
CREATE TABLE erp_inventory (
  snapshot_date      DATE          NOT NULL,
  part_id            VARCHAR(10)   NOT NULL REFERENCES parts(part_id),
  stock_quantity     INT           NOT NULL,
  reorder_point      INT           NOT NULL,
  lead_time_days     INT           NOT NULL,
  unit_cost          INT           NOT NULL,  -- KRW
  weekly_consumption INT           NOT NULL DEFAULT 0,
  reorder_triggered  BOOLEAN       NOT NULL DEFAULT FALSE,

  PRIMARY KEY (snapshot_date, part_id)
);
```

**레코드:** 35건 (7주 × 5부품)

> **W5 coolant stock=0:** F5 LLM 테스트 시나리오. "재고 0일 때 생산 계속할지?" 판단용.

---

### 2.6 참조 테이블 (마스터 데이터)

#### 설비 마스터 — `equipment`

```sql
CREATE TABLE equipment (
  equipment_id     VARCHAR(7)    PRIMARY KEY,
  equipment_type   VARCHAR(30)   NOT NULL DEFAULT 'CNC Milling Machine',
  status           VARCHAR(15)   NOT NULL DEFAULT 'active',
  experiment_range VARCHAR(15)   -- 참고용: 'exp01~06'
);

-- 초기 데이터
INSERT INTO equipment VALUES
  ('CNC-001', 'CNC Milling Machine', 'active', 'exp01~06'),
  ('CNC-002', 'CNC Milling Machine', 'active', 'exp07~12'),
  ('CNC-003', 'CNC Milling Machine', 'active', 'exp13~18');
```

#### 고장코드 마스터 — `failure_codes`

```sql
CREATE TABLE failure_codes (
  failure_code      VARCHAR(30)   PRIMARY KEY,
  description       TEXT          NOT NULL,
  severity          VARCHAR(10)   NOT NULL CHECK (severity IN ('critical', 'warning')),
  failure_category  VARCHAR(20)   NOT NULL
);

INSERT INTO failure_codes VALUES
  ('TOOL_WEAR_001',        '엔드밀 마모로 인한 가공 품질 저하',      'critical', 'tool_wear'),
  ('SPINDLE_OVERHEAT_001', '주축 과열로 인한 베어링 손상 위험',      'critical', 'thermal'),
  ('CLAMP_PRESSURE_001',   '클램프 압력 저하로 공작물 고정 불량',    'warning',  'mechanical'),
  ('COOLANT_LOW_001',      '절삭유 부족으로 가공면 품질 저하 위험',  'warning',  'fluid');
```

#### 부품 마스터 — `parts`

```sql
CREATE TABLE parts (
  part_id          VARCHAR(10)   PRIMARY KEY,
  part_name        VARCHAR(50)   NOT NULL,
  unit_cost        INT           NOT NULL,  -- KRW
  lead_time_days   INT           NOT NULL,
  reorder_point    INT           NOT NULL
);

-- 원본: it-data-synthesis-schema.md + erp_inventory_snapshots.csv
INSERT INTO parts VALUES
  ('P001', 'Endmill 6mm Carbide',          45000,  3, 5),
  ('P002', 'Spindle Bearing Set',          280000, 7, 2),
  ('P003', 'Coolant (Water-Soluble, 20L)', 35000,  2, 3),
  ('P004', 'Clamp Bolt Set',              12000,  1, 4),
  ('P005', 'Air Filter',                  8000,   1, 3);
```

#### 센서 메타데이터 — `sensors`

```sql
CREATE TABLE sensors (
  sensor_id        VARCHAR(30)   PRIMARY KEY,
  sensor_type      VARCHAR(15)   NOT NULL,  -- position, velocity, acceleration, current, voltage, power
  axis             VARCHAR(2)    NOT NULL,   -- X, Y, Z, S, M
  unit             VARCHAR(10)
);

-- 42개 유효 센서만 등록 (position/velocity/acceleration/current/voltage/power)
-- machining_process, m1_current_program_number, m1_current_feedrate는
-- 센서가 아닌 컨텍스트 데이터이므로 이 테이블에 포함하지 않음
-- (sensor_readings 테이블의 컬럼으로만 존재)
```

---

### 2.7 문서 임베딩 — `document_embeddings` (pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
  id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  manual_id        VARCHAR(15)   NOT NULL,   -- Neo4j Document 노드 FK
  chunk_number     INT           NOT NULL DEFAULT 0,
  title            VARCHAR(100),
  text_content     TEXT          NOT NULL,
  embedding        VECTOR(384),              -- paraphrase-multilingual-MiniLM-L12-v2 (384차원, 로컬 무료)
  created_at       TIMESTAMPTZ   DEFAULT NOW(),

  UNIQUE (manual_id, chunk_number)
);

-- 벡터 유사도 검색 인덱스 (HNSW: 정확도↑, IVFFlat: 속도↑)
CREATE INDEX idx_doc_embedding ON document_embeddings
  USING hnsw (embedding vector_cosine_ops);
```

**Phase 3 구현 시 생성.** 현재는 테이블 정의만.

---

## 3. Neo4j 스키마

온톨로지 설계(`ontology-design.md`)에서 정의한 7종 노드 + 10종 관계를 그대로 사용.
상세 노드/관계 정의는 [ontology-design.md](ontology-design.md) 참조.

### 3.1 제약조건 및 인덱스

```cypher
// PK 유니크 제약
CREATE CONSTRAINT FOR (e:Equipment) REQUIRE e.equipment_id IS UNIQUE;
CREATE CONSTRAINT FOR (s:Sensor) REQUIRE s.sensor_id IS UNIQUE;
CREATE CONSTRAINT FOR (f:FailureCode) REQUIRE f.failure_code IS UNIQUE;
CREATE CONSTRAINT FOR (p:Part) REQUIRE p.part_id IS UNIQUE;
CREATE CONSTRAINT FOR (d:Document) REQUIRE d.manual_id IS UNIQUE;
CREATE CONSTRAINT FOR (w:WorkOrder) REQUIRE w.work_order_id IS UNIQUE;
CREATE CONSTRAINT FOR (m:MaintenanceAction) REQUIRE m.event_id IS UNIQUE;

// 속성 인덱스
CREATE INDEX FOR (s:Sensor) ON (s.axis);
CREATE INDEX FOR (s:Sensor) ON (s.sensor_type);
CREATE INDEX FOR (f:FailureCode) ON (f.severity);
CREATE INDEX FOR (m:MaintenanceAction) ON (m.event_type);

// BM25 전문 검색 인덱스
CREATE FULLTEXT INDEX failure_search FOR (f:FailureCode) ON EACH [f.text_representation];
CREATE FULLTEXT INDEX document_search FOR (d:Document) ON EACH [d.text_representation];
```

---

## 4. PG ↔ Neo4j 조인 키 매핑

두 DB 간 데이터를 연결하는 공유 키:

```
PostgreSQL Table              Key                    Neo4j Node
─────────────────────────────────────────────────────────────────
sensor_readings            equipment_id          Equipment.equipment_id
mes_work_orders            equipment_id          Equipment.equipment_id
mes_work_orders            work_order_id         WorkOrder.work_order_id
maintenance_events         equipment_id          Equipment.equipment_id
maintenance_events         failure_code          FailureCode.failure_code
maintenance_events         work_order_id         WorkOrder.work_order_id
erp_inventory              part_id               Part.part_id
document_embeddings        manual_id             Document.manual_id
```

**애플리케이션 레벨 조인:** PG와 Neo4j는 직접 조인 불가.
F4 서비스에서 Neo4j 순회 결과 → PG 쿼리 순서로 2단계 조회.

```
예시: F4 GraphRAG 검색 흐름
1. Neo4j: Equipment(CNC-001) → FailureCode → Part → Document
   → 결과: [manual_id: DOC-TOOL-001, DOC-TOOL-002]
2. PostgreSQL: SELECT * FROM document_embeddings
   WHERE manual_id IN ('DOC-TOOL-001', 'DOC-TOOL-002')
   ORDER BY embedding <=> query_vector LIMIT 5;
```

---

## 5. 테이블 요약

| # | 테이블 | 유형 | 레코드 수 | 확장 | 비고 |
|---|--------|------|----------|------|------|
| 1 | sensor_readings | TimescaleDB hypertable | ~25,286 (현재) | 하루 ~51,840 | 와이드 44컬럼 |
| 2 | anomaly_scores | TimescaleDB hypertable | F2 출력 | sensor_readings와 동일 | Phase 3 |
| 3 | mes_work_orders | 이벤트 | 18 | 운영 시 증가 | 작업지시 |
| 4 | maintenance_events | 이벤트 | 39 | 운영 시 증가 | 정비 기록 |
| 5 | erp_inventory | 시계열 스냅샷 | 35 | 주간 5건씩 | 재고 변동 |
| 6 | equipment | 참조 (마스터) | 3 | 거의 고정 | 설비 |
| 7 | failure_codes | 참조 (마스터) | 4 | 거의 고정 | 고장코드 |
| 8 | parts | 참조 (마스터) | 5 | 거의 고정 | 부품 |
| 9 | sensors | 참조 (메타) | 42+ | 고정 | 센서 정의 |
| 10 | document_embeddings | pgvector | ~20 (Phase 3) | 청크 시 증가 | 매뉴얼 벡터 |

**PostgreSQL 총 10개 테이블 + Neo4j 7종 노드/10종 관계**

---

## 6. Docker Compose 서비스 구성 (참고)

```yaml
services:
  postgres:
    image: timescale/timescaledb-ha:pg16  # pgvector 포함
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: cnc_maintenance
      POSTGRES_USER: cnc_user
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  neo4j:
    image: neo4j:5-community
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data

volumes:
  pg_data:
  neo4j_data:
```

> **Docker 이미지 결정: `timescale/timescaledb-ha` 사용.**
> 기본 timescaledb 이미지에는 pgvector가 포함되지 않을 수 있으므로,
> pgvector가 기본 포함된 `timescale/timescaledb-ha` 이미지를 사용한다.

---

## 7. ER 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL (TimescaleDB)                  │
│                                                             │
│  ┌──────────────┐     ┌─────────────────┐                  │
│  │  equipment    │◄────│ sensor_readings │ (hypertable)     │
│  │  (3)         │     │ (25,286+)       │                  │
│  └──────┬───────┘     └─────────────────┘                  │
│         │                                                   │
│         ├──────────────┐                                    │
│         │              │                                    │
│  ┌──────▼───────┐  ┌──▼──────────────┐                     │
│  │ mes_work_    │  │ maintenance_    │                      │
│  │ orders (18)  │◄─│ events (39)    │                      │
│  └──────────────┘  └──────┬─────────┘                      │
│                           │                                 │
│  ┌──────────────┐  ┌──────▼─────────┐  ┌─────────────────┐│
│  │ failure_     │  │ erp_inventory  │  │ document_       ││
│  │ codes (4)    │  │ (35)           │  │ embeddings      ││
│  └──────────────┘  └────────────────┘  │ (pgvector)      ││
│                                        └─────────────────┘│
│  ┌──────────────┐  ┌────────────────┐                     │
│  │ parts (5)    │  │ sensors (42)   │                     │
│  └──────────────┘  └────────────────┘                     │
│  ┌──────────────────────────────────┐                     │
│  │ anomaly_scores (hypertable)     │                      │
│  └──────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘

                    ▲ 애플리케이션 레벨 조인 (equipment_id, failure_code, part_id, manual_id)
                    ▼

┌─────────────────────────────────────────────────────────────┐
│                      Neo4j (Graph)                          │
│                                                             │
│   Equipment ──HAS_SENSOR──► Sensor ──DETECTS──► FailureCode │
│       │                                    │        │       │
│       ├──EXECUTES──► WorkOrder             │ REQUIRES│      │
│       │                  │                 ▼        ▼       │
│       └──EXPERIENCES──►  ├──TRIGGERS──► MaintenanceAction   │
│                          │                 │        │       │
│                          │          RESOLVES│ CONSUMES│     │
│                          │                 ▼        ▼       │
│                          │            FailureCode  Part     │
│                          │                                  │
│                          └──────────► Document               │
│                                      (DESCRIBED_BY,         │
│                                       REFERENCES)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 리뷰 결정 사항

| # | 질문 | 결정 | 근거 |
|---|------|------|------|
| 1 | 와이드 vs 롱 테이블 | **와이드** | CNC 센서 42개 고정, 행 수 1/42로 절감 |
| 2 | parts_used 정규화 | **현재 CSV, 쿼리 패턴 기준 분리** | 39건 규모에서 정규화 불필요, 부품별 집계 필요 시 분리 |
| 3 | anomaly_scores 위치 | **별도 테이블** | 생성 주기 다름, 모델 버전별 비교 용이 |
| 4 | Docker 이미지 | **timescaledb-ha** | pgvector 기본 포함 |

---

## 리뷰 피드백 이력

### 리뷰 #1 (2026-03-15)

1. **와이드 테이블 — OK** ✅ 확인
2. **parts_used 분리 기준:** "데이터 규모"가 아닌 "쿼리 패턴"이 기준 ✅ 반영
3. **anomaly_scores 별도 — OK** ✅ 확인
4. **Docker timescaledb-ha 확정** ✅ 반영
5. **S축 센서 주석:** 10개 → 11개 수정 ✅ 반영
6. **Parts 데이터 불일치:** 온톨로지 문서를 원본(it-data-synthesis-schema.md) 기준으로 통일 ✅ 반영
7. **sensors 테이블:** 45개 → 42개 센서만, 나머지는 컨텍스트 데이터로 분리 ✅ 반영
