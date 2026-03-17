# 온톨로지 설계 (Neo4j Graph Schema)

> CNC 예지보전 시스템의 지식 그래프 구조를 정의한다.
> "설비 → 고장코드 → 부품 → 매뉴얼" 관계망을 Neo4j에 구축하여, F4 GraphRAG가 정비 지식을 검색하는 기반이 된다.

---

## 1. 설계 목표

1. F4 GraphRAG가 **2~3홉 순회**로 정비 지식을 찾을 수 있는 구조
2. F2 이상탐지 결과 → 어떤 고장 → 어떤 부품 → 어떤 매뉴얼 순으로 **인과 관계를 추적** 가능
3. PostgreSQL(시계열/이벤트 저장)과 **역할 분담** 명확

---

## 2. 노드 타입 (7종)

### 2.1 Equipment (설비)

CNC 장비 마스터 데이터. 온톨로지의 중심 허브.

| 속성 | 타입 | 예시 | 비고 |
|------|------|------|------|
| `equipment_id` | String (PK) | CNC-001 | 3대 |
| `equipment_type` | String | CNC Milling Machine | |
| `status` | Enum | active / maintenance | |
| `experiment_range` | String | exp01~06 | 매핑 참고용 |

**인스턴스:** 3개 (CNC-001, CNC-002, CNC-003)

### 2.2 Sensor (센서)

설비에 부착된 개별 센서. **유효 42개만** 노드로 모델링.

| 속성 | 타입 | 예시 | 비고 |
|------|------|------|------|
| `sensor_id` | String (PK) | X1_OutputPower | 컬럼명 그대로 |
| `sensor_type` | Enum | position / velocity / acceleration / current / voltage / power | 6종 |
| `axis` | String | X / Y / Z / S / M | 축 |
| `unit` | String | A, V, W, mm, mm/s | |

**인스턴스:** 42개 (유효 센서만)

> **설계 결정: 제외된 6개는 노드로 만들지 않는다**
> Z-axis 전류 4개(all-zero) + S1_SystemInertia(상수) + M1_sequence_number(행 카운터)는
> 이상탐지에 쓸 일이 없으므로 노드 생성 불필요. 쿼리마다 is_excluded 필터링을 붙이는 불필요한 복잡성을 방지.
> 제외 사유는 Phase 1 EDA 문서([outlier-analysis.md](../1-data-exploration/outlier-analysis.md))에 기록됨.

> **설계 결정: Sensor를 노드로 모델링하는 이유**
> - 센서 → 고장코드 연결(DETECTS 관계)로 "어떤 센서가 이상이면 어떤 고장 가능성?" 표현
> - GraphRAG 질의: "S1_OutputPower 이상 시 관련 고장코드는?" → 2홉으로 부품/매뉴얼까지 도달
> - 센서 시계열 데이터 자체는 PostgreSQL에 저장 (노드에는 메타데이터만)

### 2.3 FailureCode (고장코드)

고장 유형 분류. IT 합성 스키마에서 정의된 4종.

| 속성 | 타입 | 예시 | 비고 |
|------|------|------|------|
| `failure_code` | String (PK) | TOOL_WEAR_001 | |
| `description` | String | 엔드밀 마모로 인한 가공 품질 저하 | |
| `severity` | Enum | critical / warning | |
| `failure_category` | String | tool_wear / thermal / mechanical / fluid | |
| `text_representation` | String | (BM25 검색용 텍스트) | F4용 |

**인스턴스:** 4개

| 코드 | 카테고리 | 심각도 | 관련 센서 — 초기 가설 |
|------|---------|--------|----------------------|
| TOOL_WEAR_001 | tool_wear | critical | X1/Y1 OutputPower, S1_ActualVelocity |
| SPINDLE_OVERHEAT_001 | thermal | critical | S1_OutputPower, S1_CurrentFeedback |
| CLAMP_PRESSURE_001 | mechanical | warning | Z1_ActualPosition, clamp_pressure |
| COOLANT_LOW_001 | fluid | warning | M1_CURRENT_FEEDRATE (간접) |

> **주의:** 위 센서-고장코드 매핑은 도메인 지식 기반 **초기 가설**이다.
> Phase 3에서 F2 이상탐지 모델을 실행한 후, 실제 데이터로 검증하여 DETECTS 관계를 확정/수정한다.

### 2.4 Part (부품)

정비에 필요한 소모품/교체 부품.

| 속성 | 타입 | 예시 | 비고 |
|------|------|------|------|
| `part_id` | String (PK) | P001 | |
| `part_name` | String | Endmill 6mm Carbide | |
| `unit_cost` | Integer | 45000 (KRW) | |
| `lead_time_days` | Integer | 2 | |
| `reorder_point` | Integer | 3 | |

**인스턴스:** 5개 (P001~P005)

| ID | 이름 | 비용 (KRW) | 리드타임 | reorder_point |
|----|------|-----------|---------|---------------|
| P001 | Endmill 6mm Carbide | 45,000 | 3일 | 5 |
| P002 | Spindle Bearing Set | 280,000 | 7일 | 2 |
| P003 | Coolant (Water-Soluble, 20L) | 35,000 | 2일 | 3 |
| P004 | Clamp Bolt Set | 12,000 | 1일 | 4 |
| P005 | Air Filter | 8,000 | 1일 | 3 |

> **출처:** [it-data-synthesis-schema.md](../1-data-exploration/it-data-synthesis-schema.md) + erp_inventory_snapshots.csv

### 2.5 Document (정비 매뉴얼)

정비 절차서, 트러블슈팅 가이드. Phase 3에서 합성/확보.

| 속성 | 타입 | 예시 | 비고 |
|------|------|------|------|
| `manual_id` | String (PK) | DOC-TOOL-001 | |
| `title` | String | 엔드밀 교체 절차서 | |
| `document_type` | Enum | technical_manual / troubleshooting_guide / sop / checklist | |
| `text_representation` | String | (BM25 검색용 전문) | F4용 |
| `embedding_ref_id` | String | → PostgreSQL pgvector FK | 벡터 검색용 |

**인스턴스:** 12개 확정 (4 고장코드 × 3 문서유형: 교체 절차서, 점검 체크리스트, 트러블슈팅 가이드)

> **참고:** Document의 실제 텍스트와 임베딩 벡터는 PostgreSQL(pgvector)에 저장.
> Neo4j에는 메타데이터 + 관계만 저장하여 그래프 순회 후 PG에서 상세 검색.
>
> **Phase 3 확장 가능성: 2계층 구조**
> ```
> Document(문서 단위) -[HAS_CHUNK]→ DocumentChunk(청크 단위)
> ```
> - GraphRAG 순회는 Document 레벨로 (어떤 매뉴얼이 관련되는지)
> - 벡터 검색은 DocumentChunk 레벨로 (pgvector에서 유사 청크 찾기)
> - 현재는 Document 1계층으로 설계하고, Phase 3에서 매뉴얼 합성 후 청킹 전략과 함께 결정

### 2.6 WorkOrder (작업지시)

MES 작업지시. 설비와 정비를 연결하는 컨텍스트 노드.

| 속성 | 타입 | 예시 | 비고 |
|------|------|------|------|
| `work_order_id` | String (PK) | WO-2024-001 | |
| `product_type` | String | WAX_BLOCK_6MM | |
| `priority` | Enum | normal / urgent / critical | |
| `status` | Enum | completed / aborted | |

**인스턴스:** 18개 (실험 1:1 대응)

### 2.7 MaintenanceAction (정비 이벤트)

실제 정비 수행 기록. 고장코드 해결 + 부품 소모를 기록.

| 속성 | 타입 | 예시 | 비고 |
|------|------|------|------|
| `event_id` | String (PK) | MT-2024-001 | |
| `event_type` | Enum | corrective / preventive | |
| `duration_min` | Integer | 45 | |
| `technician_id` | String | TECH-01 | |

**인스턴스:** 39개 (교정 12 + 예방 27)

> **참고:** timestamp 등 시간 데이터는 PostgreSQL에서 관리.
> Neo4j에는 관계 구조만 저장하여 "이 정비가 어떤 고장을 해결하고 어떤 부품을 썼는지"를 표현.

---

## 3. 관계 타입 (10종)

### 3.1 관계 정의

| # | 관계 | 시작 노드 | 끝 노드 | 방향 | 카디널리티 | 관계 속성 |
|---|------|-----------|---------|------|-----------|----------|
| R1 | HAS_SENSOR | Equipment | Sensor | → | 1:N | — |
| R2 | DETECTS | Sensor | FailureCode | → | N:M | `anomaly_pattern`, `lead_time_min` (주1) |
| R3 | EXPERIENCES | Equipment | FailureCode | → | N:M | `first_occurrence` |
| R4 | REQUIRES | FailureCode | Part | → | N:M | `quantity`, `urgency` |
| R5 | DESCRIBED_BY | FailureCode | Document | → | N:M | `relevance_score` |
| R6 | EXECUTES | Equipment | WorkOrder | → | 1:N | `sequence` |
| R7 | TRIGGERS | WorkOrder | MaintenanceAction | → | 1:N | — |
| R8 | RESOLVES | MaintenanceAction | FailureCode | → | N:1 | `resolution_time_min` |
| R9 | CONSUMES | MaintenanceAction | Part | → | N:M | `quantity_used` |
| R10 | REFERENCES | MaintenanceAction | Document | → | N:M | `section_number` |

> **(주1) `lead_time_min` 정의:** 센서에서 이상 패턴이 감지된 시점부터 실제 고장이 발생하기까지 걸리는 예상 시간(분).
> 예: S1_OutputPower 이상 → SPINDLE_OVERHEAT_001 발생까지 약 30분.
> Phase 3에서 F2 모델 결과로 계산하여 채운다. 그 전까지는 null.
>
> **R2 DETECTS 관계는 구조만 확정, 구체적 인스턴스는 Phase 3에서 생성.**
> 현재 FailureCode 인스턴스 테이블의 "관련 센서"는 초기 가설이며, F2 이상탐지 모델 결과로 검증 후 확정.
>
> **(주2) R7 TRIGGERS 예외:** 예방정비(preventive) 27건은 work_order_id가 비어있음.
> 작업지시 없이 정기 일정으로 수행되는 정비이므로 WorkOrder와 연결되지 않음.
> → R7 관계는 교정정비(corrective) 12건에만 생성. 예방정비 27건은 Equipment에서 직접 연결 (R3 EXPERIENCES 경유).
>
> **(주3) R8 RESOLVES 예외:** 에어 필터 교체(preventive) 9건(MT-2024-031~039)은 failure_code가 비어있음.
> 특정 고장코드 없이 2주 주기 정기 교체로 수행되므로 FailureCode와 연결되지 않음.
> → R8 관계는 failure_code가 있는 30건에만 생성. 9건은 R9(CONSUMES → P005)만 연결.

### 3.2 관계 다이어그램

```
                          ┌──────────┐
                     R1   │  Sensor  │  R2
              ┌──────────►│ (42개)   │──────────┐
              │           └──────────┘           │
              │                                  ▼
        ┌─────────────┐   R3          ┌──────────────┐   R4    ┌────────┐
        │  Equipment  │──────────────►│ FailureCode  │────────►│  Part  │
        │   (3대)     │               │    (4종)     │         │ (5종)  │
        └──────┬──────┘               └──────┬───────┘         └────────┘
               │ R6                     R5 │ │ R8 ▲                 ▲ R9
               ▼                          ▼ │     │                 │
        ┌─────────────┐   R7    ┌──────────────────────────┐       │
        │  WorkOrder  │────────►│   MaintenanceAction      │───────┘
        │   (18건)    │         │       (39건)             │
        └─────────────┘         └──────────┬───────────────┘
                                           │ R10
                                           ▼
                                    ┌──────────┐
                                    │ Document  │
                                    │ (12건)    │
                                    └──────────┘
```

### 3.3 F4 GraphRAG 핵심 질의 경로

F2에서 이상 감지 시, F4가 Neo4j를 순회하는 대표 경로:

```
경로 1: 센서 이상 → 고장 원인 → 필요 부품 + 매뉴얼
  Sensor(S1_OutputPower) -[DETECTS]→ FailureCode(SPINDLE_OVERHEAT_001)
    -[REQUIRES]→ Part(P002: Spindle Bearing Set)
    -[DESCRIBED_BY]→ Document(스핀들 베어링 교체 절차서)

경로 2: 설비 이력 → 과거 정비 → 사용 부품
  Equipment(CNC-001) -[EXPERIENCES]→ FailureCode(TOOL_WEAR_001)
    ←[RESOLVES]- MaintenanceAction(MT-2024-005)
      -[CONSUMES]→ Part(P001: Endmill)
      -[REFERENCES]→ Document(엔드밀 교체 가이드)

경로 3: 작업 중 고장 → 정비 트리거
  Equipment(CNC-002) -[EXECUTES]→ WorkOrder(WO-2024-008)
    -[TRIGGERS]→ MaintenanceAction(MT-2024-012)
      -[RESOLVES]→ FailureCode(CLAMP_PRESSURE_001)
```

---

## 4. PostgreSQL vs Neo4j 역할 분담

| 데이터 | PostgreSQL | Neo4j | 이유 |
|--------|-----------|-------|------|
| 센서 시계열 (25,286행 × 42컬럼) | ✅ TimescaleDB | ❌ | 시계열 집계/윈도잉은 PG 강점 |
| 센서 메타데이터 (이름, 축, 단위) | 참조 테이블 | ✅ Sensor 노드 | 관계 순회에 필요 |
| 고장코드 마스터 (4종) | 참조 테이블 | ✅ FailureCode 노드 | 양쪽 모두 필요 (PG: FK, Neo4j: 순회) |
| 부품 마스터 (5종) | 참조 테이블 | ✅ Part 노드 | 양쪽 모두 필요 |
| 재고 스냅샷 (35건, 시계열) | ✅ | ❌ | 시간별 재고 변동은 PG |
| MES 작업지시 (18건) | ✅ 이벤트 테이블 | ✅ WorkOrder 노드 | PG: 상세 조회, Neo4j: 관계 |
| 정비 이벤트 (39건) | ✅ 이벤트 테이블 | ✅ MaintenanceAction 노드 | PG: 이력 조회, Neo4j: 관계 |
| 매뉴얼 텍스트 + 임베딩 | ✅ pgvector | ❌ | 벡터 검색은 PG |
| 매뉴얼 메타데이터 + 관계 | ❌ | ✅ Document 노드 | 그래프 순회 후 PG에서 상세 검색 |
| 이상탐지 결과/예측값 | ✅ | ❌ | 시계열 출력값 |

**원칙:**
- **Neo4j** = 관계 구조 (정적 지식 그래프, "무엇이 무엇과 연결되는가")
- **PostgreSQL** = 시계열 + 이벤트 + 벡터 (동적 데이터, "언제 어떤 값이었는가")
- 고장코드, 부품 등 **마스터 데이터는 양쪽에 중복** 저장 (PG: FK 참조, Neo4j: 그래프 순회)

---

## 5. 조인 키 매핑

Neo4j 노드와 PostgreSQL 테이블을 연결하는 키:

```
Neo4j Node              Join Key              PostgreSQL Table
─────────────────────────────────────────────────────────────
Equipment.equipment_id  ← equipment_id →      sensor_readings.equipment_id
                                              mes_work_orders.equipment_id
                                              maintenance_events.equipment_id

FailureCode.failure_code ← failure_code →     maintenance_events.failure_code

Part.part_id            ← part_id →           erp_inventory.part_id
                                              maintenance_events.parts_used

WorkOrder.work_order_id ← work_order_id →     mes_work_orders.work_order_id
                                              maintenance_events.work_order_id

Document.embedding_ref_id ← ref_id →         document_embeddings.id (pgvector)
```

---

## 6. Cypher 스키마 정의 (구현 참고)

```cypher
// 제약조건 (PK 보장)
CREATE CONSTRAINT FOR (e:Equipment) REQUIRE e.equipment_id IS UNIQUE;
CREATE CONSTRAINT FOR (s:Sensor) REQUIRE s.sensor_id IS UNIQUE;
CREATE CONSTRAINT FOR (f:FailureCode) REQUIRE f.failure_code IS UNIQUE;
CREATE CONSTRAINT FOR (p:Part) REQUIRE p.part_id IS UNIQUE;
CREATE CONSTRAINT FOR (d:Document) REQUIRE d.manual_id IS UNIQUE;
CREATE CONSTRAINT FOR (w:WorkOrder) REQUIRE w.work_order_id IS UNIQUE;
CREATE CONSTRAINT FOR (m:MaintenanceAction) REQUIRE m.event_id IS UNIQUE;

// 인덱스 (검색 성능)
CREATE INDEX FOR (s:Sensor) ON (s.axis);
CREATE INDEX FOR (s:Sensor) ON (s.sensor_type);
CREATE INDEX FOR (f:FailureCode) ON (f.severity);
CREATE INDEX FOR (m:MaintenanceAction) ON (m.event_type);

// BM25 전문 검색 인덱스 (Neo4j 5.x Full-Text Index)
CREATE FULLTEXT INDEX failure_search FOR (f:FailureCode) ON EACH [f.text_representation];
CREATE FULLTEXT INDEX document_search FOR (d:Document) ON EACH [d.text_representation];
```

---

## 7. 노드/관계 수량 요약

| 항목 | 수량 | 출처 |
|------|------|------|
| Equipment 노드 | 3 | OT 데이터 (설비 매핑) |
| Sensor 노드 | 42 | OT 데이터 (유효 컬럼만) |
| FailureCode 노드 | 4 | IT 합성 스키마 |
| Part 노드 | 5 | IT 합성 ERP |
| WorkOrder 노드 | 18 | IT 합성 MES |
| MaintenanceAction 노드 | 39 | IT 합성 Maintenance |
| Document 노드 | 12 | 합성 완료 (4 고장코드 × 3 문서유형) |
| **총 노드** | **120** | Phase 3 확정 |
| **총 관계** | **337** | 10종 전부 완성 (R2 DETECTS 7 + R10 REFERENCES 90 포함) |

> 소규모 그래프이지만, F4 GraphRAG의 핵심은 크기가 아니라 **관계의 정확성**과 **질의 경로의 명확성**이다.

---

## 8. Phase 3 구현 시 필요한 작업

| 작업 | 설명 | 의존성 |
|------|------|--------|
| 매뉴얼 합성 | failure_code 4종 × 부품 5종 기준 정비 절차서 작성 | open-items #2 (정비 매뉴얼 데이터 확보 방안) |
| 매뉴얼 청킹 | 문서를 검색 가능한 섹션으로 분할 | 매뉴얼 합성 후 |
| 벡터 임베딩 | 청크별 임베딩 생성 → PostgreSQL pgvector 저장 | LLM 선택 (#9) |
| BM25 인덱스 | text_representation 필드에 전문 검색 인덱스 | Neo4j 구축 후 |
| Sensor-FailureCode 매핑 | 어떤 센서 이상이 어떤 고장과 연관되는지 (DETECTS 관계) | 도메인 지식 + EDA 결과 |

---

## 리뷰 결정 사항

리뷰어 피드백을 거쳐 확정된 설계 결정:

| # | 질문 | 결정 | 근거 |
|---|------|------|------|
| 1 | Sensor 노드 48개 vs 42개? | **42개만** | 제외 6개는 이상탐지에 불필요. 필터링 복잡성 방지 |
| 2 | WorkOrder/MaintenanceAction Neo4j 중복? | **유지** | F4 질의 경로 2, 3에 필수. 57개 노드는 부담 없는 규모 |
| 3 | DETECTS 관계 구체성? | **구조만 확정, 인스턴스는 Phase 3** | 현재 매핑은 초기 가설. F2 모델 결과로 검증 필요 |
| 4 | Document 노드 구조? | **현재 1계층, Phase 3에서 2계층 확장 가능** | 매뉴얼 합성 후 청킹 전략과 함께 결정 |

---

## 리뷰 피드백 이력

### 리뷰 #1 (2026-03-15)

1. **Sensor 42개만:** 제외 6개는 all-zero/상수, is_excluded 필터링은 불필요한 복잡성 ✅ 반영
2. **WorkOrder/MaintenanceAction 유지:** F4 질의 경로에 필수, 57개 노드 부담 없음 ✅ 반영
3. **DETECTS 구조만 확정:** 현재 센서-고장코드 매핑은 "초기 가설" 명시, Phase 3에서 데이터 검증 ✅ 반영
4. **Document 2계층 가능성:** Document→DocumentChunk 확장 가능성 메모, 현재는 1계층 ✅ 반영
5. **lead_time_min 정의 추가:** "센서 이상 감지 ~ 실제 고장까지 예상 시간(분)" 설명 추가 ✅ 반영
6. **open-items #2 확인:** "정비 매뉴얼 데이터 확보 방안" 맞음, 참조 명확화 ✅ 반영
