# 파이프라인 설계 (F1~F6 데이터 흐름)

> CNC 예지보전 시스템의 6개 기능(F1~F6)이 어떤 순서로 데이터를 처리하고,
> 서로 어떻게 연결되는지를 정의한다.

---

## 1. 전체 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│                         5초 폴링 루프 (ADR-004)                      │
│                                                                     │
│  ┌──────────┐                                                       │
│  │ F1 수집  │ → sensor_readings (PG, hypertable)                     │
│  │ 전처리   │   44컬럼 와이드(데이터42+PK2), 5초 폴링                    │
│  └────┬─────┘                                                       │
│       ▼                                                             │
│  ┌──────────┐                                                       │
│  │ F2 이상  │ → anomaly_scores (PG, hypertable)                      │
│  │ 탐지+예측│   anomaly_score, is_anomaly, predicted_failure_code     │
│  └────┬─────┘                                                       │
│       │                                                             │
│       ├── is_anomaly = FALSE → 다음 폴링까지 대기                     │
│       │                                                             │
│       ├── is_anomaly = TRUE ──┐                                      │
│       │                      ▼                                      │
│       │              ┌──────────────┐    ┌──────────────┐           │
│       │              │ F3 IT/OT     │    │ F4 GraphRAG  │           │
│       │              │ 동기화       │    │ 지식 검색     │           │
│       │              │ (PG 조회)    │    │ (Neo4j+PG)   │           │
│       │              └──────┬───────┘    └──────┬───────┘           │
│       │                     │                   │                   │
│       │                     └───────┬───────────┘                   │
│       │                             ▼                               │
│       │                     ┌──────────────┐                        │
│       │                     │ F5 LLM      │                        │
│       │                     │ 자율 조치    │                        │
│       │                     └──────┬───────┘                        │
│       │                            │                                │
│       └────────────────────────────┼─────────────────┐              │
│                                    ▼                 ▼              │
│                            ┌──────────────────────────────┐         │
│                            │ F6 대시보드                    │        │
│                            │ 센서 + 이상탐지 + 조치 표시     │        │
│                            └──────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

**핵심 포인트:**
- F1→F2는 **매 폴링마다** 실행 (5초 주기)
- F3/F4/F5는 **이상 감지 시에만** 트리거 (이벤트 기반)
- F6는 **항상** 최신 데이터를 표시 (F2까지의 결과는 매번, F5 결과는 알람 시)

---

## 2. F1: 실시간 시계열 수집 및 전처리

### 입력

| 소스 | 데이터 | 형태 |
|------|--------|------|
| OT 센서 | 42개 유효 센서 값 | CSV / 시뮬레이터 출력 |
| 메타 | equipment_id, timestamp | 매핑 규칙 적용 |

### 처리 단계

```
1. 데이터 읽기 (5초 폴링)
   └─ 소스에서 새 행 가져오기 (마지막 읽은 timestamp 이후)

2. 전처리
   ├─ 결측값 처리: forward-fill (직전 값으로 채움)
   ├─ 제외 컬럼 필터링: Z축 전기 4개 + S1_SystemInertia + M1_sequence_number 제거
   ├─ 타입 변환: float64 통일, timestamp→TIMESTAMPTZ
   └─ 컬럼명 정규화: CamelCase → snake_case (DB 테이블 컬럼과 일치)

3. 피처 엔지니어링 (윈도우 기반)
   ├─ 이동 평균: 30초 윈도우 (sensor_value_ma_30s)
   ├─ 이동 표준편차: 30초 윈도우 (sensor_value_std_30s)
   └─ 변화율: Δvalue / Δtime

   > **Phase 3 확장 후보 (현재는 미구현):**
   > - 축 간 편차: `x1_actual_position - x1_command_position` (명령 vs 실제 → 마모 지표)
   > - FFT 주파수 특성: 진동 패턴 추출 (고급, 성능 부족 시 도입 검토)

4. 저장
   └─ sensor_readings 테이블에 INSERT (TimescaleDB hypertable)
```

### 출력

| 대상 | 테이블 | 주기 |
|------|--------|------|
| PostgreSQL | `sensor_readings` | 5초마다 배치 INSERT |

### 설정값 (config)

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `POLL_INTERVAL_SEC` | 5 | 폴링 주기 |
| `WINDOW_SIZE_SEC` | 30 | 이동 평균/표준편차 윈도우 |
| `FILL_METHOD` | forward | 결측값 처리 방식 |

---

## 3. F2: 사전 위험 예측 및 이상 탐지

### 입력

| 소스 | 데이터 | 비고 |
|------|--------|------|
| `sensor_readings` | 최근 N분 센서 데이터 | 슬라이딩 윈도우 |

### 처리 단계

```
1. 데이터 윈도우 추출
   └─ 최근 PREDICTION_WINDOW분의 sensor_readings 조회

2. 이상탐지 (비지도 학습)
   ├─ 모델: Isolation Forest 또는 Autoencoder (Phase 3에서 선택)
   ├─ 입력: 42개 센서 값 (정규화된 벡터)
   ├─ 출력: anomaly_score (0.0~1.0)
   └─ 판정: anomaly_score > ANOMALY_THRESHOLD → is_anomaly = TRUE

3. 시계열 예측 (지도 학습)
   ├─ 모델: LSTM 등 (Phase 3에서 선택)
   ├─ 입력: 최근 PREDICTION_WINDOW분 시계열
   ├─ 출력: 향후 FORECAST_HORIZON분 예측값
   └─ 판정: 예측값이 임계 범위 이탈 → predicted_failure_code 추론

4. 저장 + 트리거
   ├─ anomaly_scores 테이블에 INSERT
   └─ is_anomaly = TRUE → F3/F4 트리거
```

### 출력

| 대상 | 테이블 | 트리거 |
|------|--------|--------|
| PostgreSQL | `anomaly_scores` | 매 폴링 |
| F3, F4 | 알람 이벤트 | is_anomaly = TRUE 시 |

### 설정값 (config)

| 파라미터 | 기본값 | 설명 | 결정 시점 |
|---------|--------|------|-----------|
| `PREDICTION_WINDOW_MIN` | 30 | 예측 입력 윈도우 (분) | Phase 3 실험 |
| `FORECAST_HORIZON_MIN` | 30 | 예측 범위 (분) | Phase 3 실험 |
| `ANOMALY_THRESHOLD` | 0.5 | 이상 판정 임계치 | Phase 3 PR곡선 |
| `MODEL_TYPE` | isolation_forest | 모델 종류 | Phase 3 비교 |
| `MODEL_VERSION` | v0.1 | 모델 버전 추적 | 학습 시 자동 |

---

## 4. F3: IT/OT 데이터 타임라인 동기화

### 입력

| 소스 | 데이터 | 비고 |
|------|--------|------|
| F2 알람 | timestamp, equipment_id, predicted_failure_code | 트리거 |
| `mes_work_orders` | 현재 진행 중인 작업지시 | PG 조회 |
| `erp_inventory` | 최근 부품 재고 스냅샷 | PG 조회 |
| `maintenance_events` | 해당 설비의 최근 정비 이력 | PG 조회 |

### 처리 단계

```
1. 현재 작업 조회
   └─ SELECT * FROM mes_work_orders
      WHERE equipment_id = :eq_id
        AND start_time <= :alarm_time
        AND (end_time >= :alarm_time OR end_time IS NULL)

2. 부품 재고 조회
   └─ SELECT * FROM erp_inventory
      WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM erp_inventory
                             WHERE snapshot_date <= :alarm_time)

3. 최근 정비 이력 조회
   └─ SELECT * FROM maintenance_events
      WHERE equipment_id = :eq_id
      ORDER BY timestamp DESC LIMIT 5

4. 작업 조회 결과 분기
   ├─ 결과 있음 → "current_work_order"에 해당 작업 포함
   └─ 결과 0건 → "current_work_order": null + "note": "현재 진행 중인 작업 없음"
      (작업 간 빈 시간이거나 모든 작업 완료 상태)

5. 컨텍스트 JSON 병합
   └─ F5로 전달할 단일 JSON 구성
```

### 핵심 설계 과제: OT vs IT 시간 정렬

> OT(센서)는 100ms 연속 스트림, IT(MES/정비)는 비정기 이벤트.
> 두 데이터의 시간 기준이 다르므로, 정렬 규칙을 명확히 한다.

| 데이터 | 시간 해상도 | 정렬 방식 |
|--------|-----------|----------|
| sensor_readings | ~100ms (원본), 5초 (폴링) | 정확한 timestamp 매칭 |
| mes_work_orders | 실험 단위 (분~시간) | 범위 포함 (`start_time ≤ t ≤ end_time`) |
| erp_inventory | 주간 스냅샷 | 가장 최근 스냅샷 (`MAX(snapshot_date) ≤ t`) |
| maintenance_events | 이벤트 단위 (비정기) | 최근 N건 조회 |

### 출력

```json
{
  "alarm": {
    "timestamp": "2024-01-22T09:15:00Z",
    "equipment_id": "CNC-002",
    "anomaly_score": 0.82,
    "predicted_failure_code": "SPINDLE_OVERHEAT_001"
  },
  "latest_work_order": {
    "work_order_id": "WO-2024-008",
    "product_type": "WAX_BLOCK_6MM",
    "due_date": "2024-01-22T13:00:00Z",
    "priority": "urgent",
    "status": "completed"
  },
  "work_order_note": "가장 최근 작업 (이미 완료됨, 현재 진행 중 작업 없음)",
  "inventory": [
    {"part_id": "P001", "stock": 18, "reorder_point": 5, "lead_time_days": 3},
    {"part_id": "P002", "stock": 3,  "reorder_point": 2, "lead_time_days": 7},
    {"part_id": "P003", "stock": 7,  "reorder_point": 3, "lead_time_days": 2},
    {"part_id": "P004", "stock": 13, "reorder_point": 4, "lead_time_days": 1},
    {"part_id": "P005", "stock": 7,  "reorder_point": 3, "lead_time_days": 1}
  ],
  "recent_maintenance": [
    {"event_id": "MT-2024-005", "failure_code": "TOOL_WEAR_001", "duration_min": 45}
  ]
}
```

> **`latest_work_order` = null 케이스:**
> 작업 간 빈 시간이거나 모든 작업이 완료된 상태에서 알람이 발생한 경우.
> 이때 `work_order_note`는 `"현재 진행 중인 작업 없음"` 으로 설정되며,
> F5 LLM에게 작업 컨텍스트 없이 센서+정비 이력만으로 판단하도록 안내합니다.
> ```json
> "latest_work_order": null,
> "work_order_note": "현재 진행 중인 작업 없음"
> ```

---

## 5. F4: 지식그래프 연동 하이브리드 검색

### 입력

| 소스 | 데이터 | 비고 |
|------|--------|------|
| F2 | predicted_failure_code | 고장코드 후보 |
| Neo4j | 온톨로지 그래프 (131노드, 200+관계) | 그래프 순회 |
| PostgreSQL | document_embeddings (pgvector) | 벡터 유사도 |

### 처리 단계

```
1. Neo4j 그래프 순회 (2~3홉)
   ├─ 경로 A: FailureCode → REQUIRES → Part (필요 부품 확인)
   ├─ 경로 B: FailureCode → DESCRIBED_BY → Document (관련 매뉴얼)
   └─ 경로 C: Equipment → EXPERIENCES → FailureCode (과거 이력)

2. BM25 키워드 검색 (Neo4j Full-Text Index)
   └─ CALL db.index.fulltext.queryNodes('document_search', :failure_description)
      YIELD node, score

3. Vector 유사도 검색 (PostgreSQL pgvector)
   └─ SELECT manual_id, 1 - (embedding <=> :query_vector) AS similarity
      FROM document_embeddings
      WHERE manual_id IN (:candidate_doc_ids)  -- Neo4j 결과로 필터링
      ORDER BY similarity DESC LIMIT 5

4. 하이브리드 점수 결합
   └─ hybrid_score = α × bm25_score + (1-α) × vector_similarity
      α = HYBRID_ALPHA (Phase 3에서 튜닝, 기본값 0.5)

5. 결과 정렬 및 반환
   └─ 부품 목록 + 매뉴얼 Top-K + 과거 정비 이력
```

### 검색 전략: 2단계 필터링

```
Step 1: Neo4j 순회 → 후보 Document 목록 추출 (구조적 관련성)
Step 2: pgvector 검색 → 후보 내에서 의미적 유사도 정렬 (내용적 관련성)
```

> **왜 2단계인가?**
> 전체 문서를 벡터 검색하면 구조적으로 무관한 문서가 상위에 올 수 있음.
> Neo4j로 먼저 "이 고장과 관련된 문서"를 좁힌 뒤, 그 안에서 벡터 검색.

### 출력

```json
{
  "failure_code": "SPINDLE_OVERHEAT_001",
  "related_parts": [
    {"part_id": "P002", "part_name": "Spindle Bearing Set", "quantity": 1, "urgency": "high"}
  ],
  "related_documents": [
    {"manual_id": "DOC-SPINDLE-001", "title": "스핀들 베어링 교체 절차서",
     "hybrid_score": 0.92, "bm25_score": 0.88, "vector_score": 0.95}
  ],
  "past_maintenance": [
    {"event_id": "MT-2024-012", "event_type": "corrective", "duration_min": 90,
     "parts_used": "P002", "resolution": "베어링 교체 완료"}
  ]
}
```

### 설정값 (config)

| 파라미터 | 기본값 | 설명 | 결정 시점 |
|---------|--------|------|-----------|
| `HYBRID_ALPHA` | 0.5 | BM25 가중치 (1-α = vector 가중치) | Phase 3 튜닝 |
| `TOP_K_DOCS` | 5 | 반환할 문서 수 | 필요에 따라 조정 |
| `MAX_GRAPH_HOPS` | 3 | Neo4j 순회 깊이 | 고정 |

---

## 6. F5: 컨텍스트 기반 LLM 자율 조치 리포트

### 입력

| 소스 | 데이터 | 비고 |
|------|--------|------|
| F3 | IT/OT 동기화 JSON | 작업 상태, 재고, 정비 이력 |
| F4 | GraphRAG 검색 결과 | 부품, 매뉴얼, 과거 사례 |

### 프롬프트 구조

```
┌─────────────────────────────────────────────────────┐
│ System Prompt (고정)                                 │
│ ─ 역할: CNC 설비 정비 판단 어시스턴트                  │
│ ─ 규칙: 제공된 컨텍스트만 사용, 환각 금지              │
│ ─ 출력: 즉시정지 / 감속운전 / 모니터링 중 선택         │
│ ─ 반드시 근거와 조치 단계 포함                         │
└─────────────────────────────────────────────────────┘
                        +
┌─────────────────────────────────────────────────────┐
│ User Prompt (동적, F3+F4 결과 주입)                   │
│                                                     │
│ [이상 감지 정보]                                     │
│  - 설비: CNC-002                                    │
│  - 고장코드: SPINDLE_OVERHEAT_001 (신뢰도: 87%)      │
│  - 이상 점수: 0.82                                   │
│                                                     │
│ [현재 작업]                                          │
│  - 작업지시: WO-2024-008                             │
│  - 납기: 4시간 후 (priority: urgent)                  │
│                                                     │
│ [부품 재고]                                          │
│  - P002 (Spindle Bearing Set): 재고 3, 최소 2        │
│  - 리드타임: 7일                                     │
│                                                     │
│ [관련 매뉴얼]                                        │
│  - DOC-SPINDLE-001: 스핀들 베어링 교체 절차서          │
│    (관련도: 92%)                                     │
│                                                     │
│ [과거 정비]                                          │
│  - MT-2024-012: 교정 정비, 90분, P002 사용            │
│                                                     │
│ → 판단과 조치 단계를 생성하세요.                       │
└─────────────────────────────────────────────────────┘
```

### 판단 기준 (LLM에게 제공)

| 조건 | 권장 판단 |
|------|----------|
| 신뢰도 ≥ 0.8 + severity=critical | **즉시 정지** (STOP) |
| 신뢰도 ≥ 0.6 + severity=warning | **감속 운전** (REDUCE) |
| 신뢰도 < 0.6 | **모니터링 계속** (MONITOR) |
| 필요 부품 재고 = 0 | 긴급 발주 안내 추가 |
| 납기 임박 (≤ 2시간) | 생산 영향 평가 포함 |

### 출력

```json
{
  "recommendation": "STOP",
  "confidence": 0.92,
  "reasoning": "주축 과열 위험 감지 (신뢰도 87%). 베어링 손상 시 수리 7일 소요. 현재 재고 충분(3개). 즉시 교체로 장기 다운타임 방지.",
  "action_steps": [
    "1. CNC-002 주축 즉시 정지",
    "2. DOC-SPINDLE-001 절차서 3~5장 참고하여 베어링 상태 점검",
    "3. P002 (Spindle Bearing Set) 1개 출고 요청",
    "4. TECH-01 배정, 예상 소요 90분 (과거 MT-2024-012 참고)",
    "5. 교체 후 WO-2024-008 재개, 납기 내 완료 가능 여부 확인"
  ],
  "estimated_downtime_min": 90,
  "parts_needed": [{"part_id": "P002", "quantity": 1, "in_stock": true}]
}
```

### 설정값 (config)

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `LLM_PROVIDER` | (미정) | API 제공자 — OpenAI / Anthropic 등 Phase 3에서 확정 |
| `LLM_MODEL` | (미정) | 모델명 — Phase 3에서 비용/성능 비교 후 선택 |
| `MAX_TOKENS` | 1000 | 응답 최대 토큰 |
| `TEMPERATURE` | 0.1 | 낮은 온도 = 일관된 판단 |
| `STOP_THRESHOLD` | 0.8 | 즉시 정지 판단 기준 (Phase 3 검증) |
| `REDUCE_THRESHOLD` | 0.6 | 감속 운전 판단 기준 (Phase 3 검증) |

---

## 7. F6: 운영자 관제 대시보드

### 입력

| 소스 | 데이터 | 갱신 주기 |
|------|--------|----------|
| F1 | sensor_readings (최근 1시간) | 5초 |
| F2 | anomaly_scores | 5초 |
| F3 | IT 동기화 정보 | 알람 시 |
| F5 | LLM 조치 리포트 | 알람 시 |

### 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│ [상단] 설비 상태 요약                                         │
│  CNC-001: ● 정상    CNC-002: ● 경고    CNC-003: ● 정상     │
├───────────────────────────┬─────────────────────────────────┤
│ [좌측] 실시간 센서 차트     │ [우측] 이상탐지 상태             │
│                           │                                 │
│ ── X1 OutputPower ──      │ 이상 점수: ████████░░ 0.82       │
│ ── S1 Velocity ──         │ 임계치:    ─────── 0.50          │
│ ── Y1 Current ──          │                                 │
│                           │ 예측 고장: SPINDLE_OVERHEAT_001  │
│ [시간축: 최근 1시간]        │ 신뢰도: 87%                     │
├───────────────────────────┼─────────────────────────────────┤
│ [좌하] 작업/재고 정보       │ [우하] LLM 조치 리포트           │
│                           │                                 │
│ 작업: WO-2024-008         │ 권고: 즉시 정지 (STOP)           │
│ 납기: 4시간 후 (urgent)    │                                 │
│                           │ 조치 1: 주축 정지                │
│ P002 재고: 3 (최소 2) ✅   │ 조치 2: DOC-SPINDLE-001 참고    │
│ P003 재고: 0 (최소 3) ⚠️   │ 조치 3: P002 출고 요청          │
│                           │ 예상 소요: 90분                  │
└───────────────────────────┴─────────────────────────────────┘
```

### 프론트엔드 선택지 (open-items #11)

| 옵션 | 장점 | 단점 | 적합도 |
|------|------|------|--------|
| **Streamlit** | Python만으로 구현, 빠른 프로토타입 | 커스텀 UI 제한, 실시간 제약 | MVP 적합 |
| **HTML + Plotly.js** | 이미 data-review.html 경험 있음, 자유도 높음 | 백엔드 연동 직접 구현 필요 | 확장 적합 |
| **Next.js** | 프로덕션 수준, 컴포넌트 재사용 | React 학습 필요, 1인 개발 부담 | 장기 적합 |

> Phase 3에서 결정. 현재는 3가지 선택지를 열어둔다.

---

## 8. 에러 처리 및 장애 대응

### 8.1 에러 시나리오별 대응

| # | 에러 시나리오 | 영향 범위 | 감지 방법 | 대응 전략 | Fallback |
|---|-------------|----------|----------|----------|----------|
| E1 | 센서 데이터 미수신 (5초 이상) | F1→F2 | 타임아웃 체크 | 마지막 정상값 forward-fill | 3회 연속 미수신 시 설비 점검 알림 |
| E2 | F2 모델 추론 실패 (OOM 등) | F2 | try-except | 배치 크기 축소 후 재시도 | 직전 anomaly_score 유지 |
| E3 | Neo4j 연결 끊김 | F4 | 연결 상태 체크 | 재연결 (exponential backoff) | BM25만으로 검색 (pgvector) |
| E4 | LLM API 실패 (타임아웃/429) | F5 | HTTP status | 재시도 (최대 3회, backoff) | "기술자 수동 판단 필요" 메시지 |
| E5 | PostgreSQL 다운 | 전체 | 연결 상태 체크 | 재연결 (exponential backoff) | 대시보드에 "DB 연결 끊김" 표시 |
| E6 | LLM 환각 (컨텍스트 외 응답) | F5 | 출력 검증 | 응답에 failure_code/part_id 존재 여부 체크 | 검증 실패 시 재시도 또는 수동 안내 |

### 8.2 재시도 정책

```python
# Exponential Backoff 공통 패턴
MAX_RETRIES = 3
BASE_DELAY_SEC = 1

for attempt in range(MAX_RETRIES):
    try:
        result = execute_operation()
        break
    except ConnectionError:
        delay = BASE_DELAY_SEC * (2 ** attempt)  # 1s, 2s, 4s
        log.warning(f"Retry {attempt+1}/{MAX_RETRIES}, waiting {delay}s")
        sleep(delay)
else:
    activate_fallback()
```

### 8.3 로깅 전략

| 레벨 | 사용처 | 예시 |
|------|--------|------|
| INFO | 정상 폴링 | "F1: 50 rows inserted, equipment=CNC-001" |
| WARNING | Fallback 활성화 | "F4: Neo4j disconnected, using BM25 only" |
| ERROR | 재시도 실패 | "F5: LLM API failed after 3 retries" |
| CRITICAL | 전체 파이프라인 정지 | "E5: PostgreSQL unreachable" |

---

## 9. 서비스 구조

### 9.1 단일 프로세스 구조 (MVP)

```
cnc-maintenance-agent/
├── main.py                 # 5초 폴링 루프 (메인 엔트리)
├── config.py               # 설정값 관리 (환경변수 / .env)
├── services/
│   ├── f1_collector.py     # 센서 수집 + 전처리
│   ├── f2_detector.py      # 이상탐지 + 예측
│   ├── f3_sync.py          # IT/OT 동기화
│   ├── f4_graphrag.py      # Neo4j 순회 + 하이브리드 검색
│   ├── f5_llm.py           # LLM 조치 생성
│   └── f6_dashboard.py     # 대시보드 서빙
├── models/                 # 학습된 모델 파일
│   ├── anomaly_model.pkl
│   └── forecast_model.h5
├── db/
│   ├── postgres.py         # PG 연결 + 쿼리
│   └── neo4j_client.py     # Neo4j 연결 + Cypher
└── docker-compose.yml      # PG + Neo4j + App
```

### 9.2 메인 루프 구조

```python
# main.py (의사코드)
async def main_loop():
    pg = PostgresClient()
    neo4j = Neo4jClient()

    while True:
        for eq_id in EQUIPMENT_IDS:  # ["CNC-001", "CNC-002", "CNC-003"]
            # F1: 수집 + 전처리
            sensor_data = f1_collector.poll_and_preprocess(eq_id)
            pg.insert_sensor_readings(sensor_data)

            # F2: 이상탐지
            anomaly_result = f2_detector.detect(eq_id, sensor_data)
            pg.insert_anomaly_scores(anomaly_result)

            # F3~F5: 알람 시에만 실행
            if anomaly_result.is_anomaly:
                # F5는 LLM API 호출(2~10초)로 병목 → 비동기 분리
                # 대시보드 갱신을 블로킹하지 않도록 create_task로 처리
                asyncio.create_task(
                    process_alarm(eq_id, anomaly_result, pg, neo4j)
                    # 내부: F3→F4→F5→push_alert 순차 실행
                )

            # F6: 항상 최신 데이터 갱신 (매 폴링)
            f6_dashboard.update(eq_id, sensor_data, anomaly_result)

        await asyncio.sleep(POLL_INTERVAL_SEC)


async def process_alarm(eq_id, anomaly_result, pg, neo4j):
    """알람 발생 시 F3→F4→F5 순차 처리 (비동기 태스크)"""
    # F3: IT/OT 동기화
    context = f3_sync.build_context(
        anomaly_result.timestamp, eq_id, pg
    )

    # F4: GraphRAG 검색
    rag_result = f4_graphrag.search(
        anomaly_result.predicted_failure_code, neo4j, pg
    )

    # F5: LLM 조치 생성
    action = f5_llm.generate_action(context, rag_result)

    # F6로 알림 전달
    f6_dashboard.push_alert(anomaly_result, context, rag_result, action)
```

> **api-design.md와 동일한 비동기 패턴:** F3→F4→F5를 `asyncio.create_task()`로 분리하여
> 메인 루프의 F6 갱신이 LLM 호출(2~10초)에 블로킹되지 않도록 합니다.

---

## 10. 전체 설정값 요약

| 카테고리 | 파라미터 | 기본값 | 결정 시점 |
|---------|---------|--------|-----------|
| F1 | POLL_INTERVAL_SEC | 5 | ADR-004 확정 |
| F1 | WINDOW_SIZE_SEC | 30 | Phase 3 조정 |
| F2 | PREDICTION_WINDOW_MIN | 30 | Phase 3 실험 |
| F2 | ANOMALY_THRESHOLD | 0.5 | Phase 3 PR곡선 |
| F2 | MODEL_TYPE | isolation_forest | Phase 3 비교 |
| F4 | HYBRID_ALPHA | 0.5 | Phase 3 튜닝 |
| F4 | TOP_K_DOCS | 5 | 필요에 따라 |
| F4 | MAX_GRAPH_HOPS | 3 | 고정 |
| F5 | LLM_PROVIDER | (미정) | Phase 3 확정 |
| F5 | LLM_MODEL | (미정) | Phase 3 확정 |
| F5 | TEMPERATURE | 0.1 | 고정 (일관성) |
| F5 | STOP_THRESHOLD | 0.8 | Phase 3 검증 |
| F5 | REDUCE_THRESHOLD | 0.6 | Phase 3 검증 |

> **원칙:** 모든 하이퍼파라미터는 `config.py` 또는 `.env`에서 관리.
> 코드 수정 없이 설정값만 바꿔서 실험 가능한 구조.

---

## 리뷰 결정 사항

| # | 질문 | 결정 | 근거 |
|---|------|------|------|
| 1 | F1 피처 추가 변수 | **현재 3개 유지, 확장 후보 메모** | MVP 충분. 축 간 편차, FFT는 Phase 3 성능 부족 시 |
| 2 | F3 작업 0건 edge case | **분기 처리 추가** | 작업 간 빈 시간 대응. null + "작업 없음" 전달 |
| 3 | F4 2단계 순서 | **Neo4j 먼저 유지** | 구조적 필터링 → 정밀 벡터 검색이 정확도↑ |
| 4 | F5 판단 임계치 | **config로 분리** | STOP_THRESHOLD=0.8, REDUCE_THRESHOLD=0.6 (Phase 3 검증) |
| 5 | 단일 vs 마이크로서비스 | **단일 프로세스** | 1인 개발, 하루 ~51,840행은 단일로 충분 |

---

## 리뷰 피드백 이력

### 리뷰 #1 (2026-03-15)

1. **F1 피처 확장 후보 메모:** 축 간 편차, FFT 주파수 특성 추가 ✅ 반영
2. **F3 작업 0건 분기:** 결과 없을 때 null + "현재 작업 없음" 전달 ✅ 반영
3. **F4 순서 — OK** ✅ 확인
4. **F5 임계치 config 추가:** STOP_THRESHOLD, REDUCE_THRESHOLD ✅ 반영
5. **단일 프로세스 — OK** ✅ 확인
6. **F3 출력 라벨 변경:** "current_work_order" → "latest_work_order" + 상태 note ✅ 반영
7. **sensor_readings 컬럼 수:** 44개 확정 (데이터42 + PK2) ✅ 재확인 완료
8. **LLM_PROVIDER:** openai → (미정), Phase 3에서 비교 선택 ✅ 반영
