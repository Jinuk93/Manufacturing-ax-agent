# API 설계 (FastAPI 엔드포인트)

> F1~F6 서비스의 REST API 인터페이스를 정의한다.
> 내부 폴링 루프(main.py)에서 직접 호출하는 구조이지만,
> 개별 테스트 및 디버깅을 위해 HTTP 엔드포인트로도 노출한다.

---

## 1. 엔드포인트 요약

| # | 경로 | 메서드 | 기능 | 호출 주기 |
|---|------|--------|------|----------|
| 1 | `/api/f1/collect` | POST | 센서 데이터 수집 + 전처리 | 5초 (매 폴링) |
| 2 | `/api/f2/detect` | POST | 이상탐지 + 예측 실행 | 5초 (매 폴링) |
| 3 | `/api/f2/history/{equipment_id}` | GET | 이상탐지 히스토리 조회 | 요청 시 |
| 4 | `/api/f3/sync` | POST | IT/OT 동기화 컨텍스트 생성 | 알람 시 |
| 5 | `/api/f4/search` | POST | GraphRAG 하이브리드 검색 | 알람 시 |
| 6 | `/api/f5/generate-action` | POST | LLM 조치 리포트 생성 | 알람 시 |
| 7 | `/api/f6/summary` | GET | 설비 상태 요약 | 대시보드 폴링 |
| 8 | `/api/f6/sensors/{equipment_id}` | GET | 실시간 센서 시계열 | 대시보드 폴링 |
| 9 | `/api/f6/anomaly/{equipment_id}` | GET | 이상탐지 현황 | 대시보드 폴링 |
| 10 | `/api/f6/work-order/{equipment_id}` | GET | 작업 + 재고 정보 | 대시보드 폴링 |
| 11 | `/api/f6/action/{equipment_id}` | GET | LLM 조치 리포트 | 알람 시 |
| 12 | `/api/health` | GET | 헬스 체크 (PG + Neo4j 상태) | 모니터링 |
| 13 | `/api/f6/alarms` | GET | 전체 설비 알람 피드 (3대 통합) | 대시보드 폴링 |

---

## 2. Pydantic 데이터 모델

### 2.1 공통

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class StatusResponse(BaseModel):
    status: str           # "success" / "error"
    message: Optional[str] = None
    timestamp: datetime
```

### 2.2 F1: 센서 수집

```python
class SensorCollectRequest(BaseModel):
    equipment_id: str                    # "CNC-001"
    timestamp: datetime
    sensor_data: Dict[str, float]        # 42개 센서 {컬럼명: 값}
    context: Optional[Dict] = None       # m1_current_program_number 등

class SensorCollectResponse(BaseModel):
    status: str
    rows_inserted: int
    equipment_id: str
    timestamp: datetime
```

### 2.3 F2: 이상탐지

```python
class AnomalyDetectRequest(BaseModel):
    equipment_id: str
    window_minutes: int = 30             # 예측 입력 윈도우
    model_version: str = "v0.1"

class AnomalyResult(BaseModel):
    timestamp: datetime
    equipment_id: str
    anomaly_score: float                 # 0.0 ~ 1.0
    is_anomaly: bool
    predicted_failure_code: Optional[str]
    confidence: Optional[float]
    model_version: str

class AnomalyDetectResponse(BaseModel):
    status: str
    anomaly_result: AnomalyResult
    trigger: bool                        # F3/F4/F5 트리거 여부

class AnomalyHistoryResponse(BaseModel):
    equipment_id: str
    records: List[AnomalyResult]
    total_count: int
```

### 2.4 F3: IT/OT 동기화

```python
class ITOTSyncRequest(BaseModel):
    timestamp: datetime
    equipment_id: str
    anomaly_score: float
    predicted_failure_code: str

class InventoryItem(BaseModel):
    part_id: str
    stock: int
    reorder_point: int
    lead_time_days: int

class WorkOrderInfo(BaseModel):
    work_order_id: str
    product_type: str
    due_date: datetime
    priority: str                        # normal / urgent / critical
    status: str                          # completed / aborted
    note: Optional[str] = None           # "현재 진행 중 작업 없음" 등

class MaintenanceRecord(BaseModel):
    event_id: str
    failure_code: str
    event_type: str                      # corrective / preventive
    duration_min: int

class ITOTSyncResponse(BaseModel):
    alarm: Dict
    latest_work_order: Optional[WorkOrderInfo]  # None = 현재 작업 없음
    work_order_note: str                        # "현재 진행 중인 작업 없음" 등 상태 설명
    inventory: List[InventoryItem]
    recent_maintenance: List[MaintenanceRecord]
```

### 2.5 F4: GraphRAG 검색

```python
class GraphRAGRequest(BaseModel):
    failure_code: str
    equipment_id: str

class RelatedPart(BaseModel):
    part_id: str
    part_name: str
    quantity: int
    urgency: str                         # high / medium / low

class RelatedDocument(BaseModel):
    manual_id: str
    title: str
    hybrid_score: float
    bm25_score: float
    vector_score: float
    text_preview: Optional[str] = None

class PastMaintenance(BaseModel):
    event_id: str
    event_type: str
    duration_min: int
    parts_used: str
    resolution: Optional[str] = None

class GraphRAGResponse(BaseModel):
    failure_code: str
    related_parts: List[RelatedPart]
    related_documents: List[RelatedDocument]
    past_maintenance: List[PastMaintenance]
```

### 2.6 F5: LLM 조치

```python
class LLMActionRequest(BaseModel):
    f3_context: ITOTSyncResponse
    f4_rag_result: GraphRAGResponse

class PartNeeded(BaseModel):
    part_id: str
    quantity: int
    in_stock: bool

class LLMActionResponse(BaseModel):
    recommendation: str                  # STOP / REDUCE / MONITOR
    confidence: float
    reasoning: str
    action_steps: List[str]
    estimated_downtime_min: int
    parts_needed: List[PartNeeded]
```

### 2.7 F6: 대시보드

```python
class EquipmentStatus(BaseModel):
    equipment_id: str
    status: str                          # normal / warning / critical
    last_anomaly_score: float
    last_updated: datetime

class DashboardSummary(BaseModel):
    equipment_status: List[EquipmentStatus]

class SensorTimeseriesResponse(BaseModel):
    equipment_id: str
    duration_hours: int
    series: List[Dict]                   # [{timestamp, sensor1, sensor2, ...}]
    # TODO Phase 3: List[Dict] → List[SensorDataPoint]로 타입 강화 검토

class AnomalyStatusResponse(BaseModel):
    equipment_id: str
    anomaly_score: float
    anomaly_threshold: float
    is_anomaly: bool
    predicted_failure_code: Optional[str]
    confidence: Optional[float]

class AlarmEvent(BaseModel):
    timestamp: datetime
    equipment_id: str                    # "CNC-001" / "CNC-002" / "CNC-003"
    anomaly_score: float
    predicted_failure_code: Optional[str]
    confidence: Optional[float]
    severity: str                        # "critical" (≥0.8) / "warning" (≥0.6)

class AlarmFeedResponse(BaseModel):
    alarms: List[AlarmEvent]             # 최신 순 정렬
    total_count: int
```

---

## 3. 엔드포인트 상세

### 3.1 `POST /api/f1/collect`

센서 데이터를 수신하여 전처리 후 `sensor_readings`에 저장.

```python
@app.post("/api/f1/collect", response_model=SensorCollectResponse)
async def collect_sensor_data(request: SensorCollectRequest):
    # 1. 결측값 처리 (forward-fill)
    # 2. 타입 변환 + 컬럼명 정규화
    # 3. 피처 엔지니어링 (이동 평균, 표준편차, 변화율)
    # 4. sensor_readings INSERT
    pass
```

| 항목 | 값 |
|------|-----|
| 성공 응답 | 200 + `SensorCollectResponse` |
| 실패 응답 | 422 (데이터 검증 실패), 500 (DB 오류) |
| 에러 처리 | E1: 센서 미수신 시 forward-fill, 3회 연속 미수신 → 알림 |

### 3.2 `POST /api/f2/detect`

최근 센서 데이터로 이상탐지 + 예측 실행.

```python
@app.post("/api/f2/detect", response_model=AnomalyDetectResponse)
async def detect_anomaly(request: AnomalyDetectRequest):
    # 1. 최근 window_minutes 분의 sensor_readings 조회
    # 2. 이상탐지 모델 추론 → anomaly_score
    # 3. 시계열 예측 → predicted_failure_code
    # 4. anomaly_scores INSERT
    # 5. is_anomaly = TRUE → trigger = True 반환
    pass
```

| 항목 | 값 |
|------|-----|
| 성공 응답 | 200 + `AnomalyDetectResponse` |
| 실패 응답 | 500 (모델 추론 실패) |
| 에러 처리 | E2: 배치 크기 축소 재시도, 실패 시 직전 점수 유지 |

### 3.3 `GET /api/f2/history/{equipment_id}`

특정 설비의 이상탐지 히스토리 조회.

```python
@app.get("/api/f2/history/{equipment_id}", response_model=AnomalyHistoryResponse)
async def get_anomaly_history(
    equipment_id: str,
    hours: int = 24,          # 최근 N시간
    limit: int = 100          # 최대 건수
):
    pass
```

### 3.4 `POST /api/f3/sync`

알람 시점의 IT/OT 비즈니스 컨텍스트 조회.

```python
@app.post("/api/f3/sync", response_model=ITOTSyncResponse)
async def sync_it_ot(request: ITOTSyncRequest):
    # 1. MES: 현재/최근 작업지시 조회
    #    결과 0건 → latest_work_order = None
    # 2. ERP: 가장 최근 재고 스냅샷
    # 3. Maintenance: 최근 정비 5건
    # 4. JSON 병합
    pass
```

| 항목 | 값 |
|------|-----|
| 성공 응답 | 200 + `ITOTSyncResponse` |
| `latest_work_order` = None | 현재 진행 중인 작업 없음 (정상 케이스) |

### 3.5 `POST /api/f4/search`

Neo4j 그래프 순회 + pgvector 벡터 검색 실행.

```python
@app.post("/api/f4/search", response_model=GraphRAGResponse)
async def search_graphrag(request: GraphRAGRequest):
    # 1. Neo4j 2~3홉 순회
    #    FailureCode → Part, Document, past MaintenanceAction
    # 2. pgvector 벡터 검색 (Neo4j 결과로 필터링)
    # 3. 하이브리드 점수 결합 (α × BM25 + (1-α) × vector)
    # 4. Top-K 정렬 반환
    pass
```

| 항목 | 값 |
|------|-----|
| 성공 응답 | 200 + `GraphRAGResponse` |
| Neo4j 끊김 | E3: BM25만으로 검색 (Fallback) |

### 3.6 `POST /api/f5/generate-action`

F3 + F4 결과로 LLM 조치 리포트 생성.

```python
@app.post("/api/f5/generate-action", response_model=LLMActionResponse)
async def generate_action(request: LLMActionRequest):
    # 1. 시스템 프롬프트 구성 (역할 + 규칙 + 판단 기준)
    # 2. 사용자 프롬프트 구성 (F3 + F4 컨텍스트 주입)
    # 3. LLM API 호출
    # 4. 응답 파싱 + 검증 (환각 체크)
    pass
```

| 항목 | 값 |
|------|-----|
| 성공 응답 | 200 + `LLMActionResponse` |
| LLM 실패 | E4: 3회 재시도, Fallback = "기술자 수동 판단 필요" |
| 환각 감지 | E6: failure_code/part_id 존재 여부 체크, 실패 시 재시도 |

### 3.7 `GET /api/f6/*` (대시보드 4종)

```python
@app.get("/api/f6/summary", response_model=DashboardSummary)
async def dashboard_summary():
    # 설비 3대의 최신 상태 요약
    pass

@app.get("/api/f6/sensors/{equipment_id}", response_model=SensorTimeseriesResponse)
async def sensor_timeseries(equipment_id: str, duration_hours: int = 1):
    # 최근 N시간 센서 시계열 (TimescaleDB time_bucket 활용)
    pass

@app.get("/api/f6/anomaly/{equipment_id}", response_model=AnomalyStatusResponse)
async def anomaly_status(equipment_id: str):
    # 최신 이상탐지 상태
    pass

@app.get("/api/f6/work-order/{equipment_id}")
async def work_order_status(equipment_id: str):
    # 현재 작업 + 부품 재고
    pass

@app.get("/api/f6/action/{equipment_id}")
async def llm_action(equipment_id: str) -> LLMActionResponse:
    # 가장 최근 LLM 조치 리포트 (알람 시에만 존재)
    # F5의 LLMActionResponse 모델을 그대로 반환 (별도 모델 불필요)
    pass
```

### 3.8 `GET /api/f6/alarms`

전체 설비(3대) 알람 피드를 단일 엔드포인트로 제공.
대시보드 AlarmFeed 컴포넌트가 설비별 × 3 호출 대신 이 엔드포인트 1회만 호출.

```python
@app.get("/api/f6/alarms", response_model=AlarmFeedResponse)
async def alarm_feed(
    limit: int = 20,                 # 최근 N건
    min_score: float = 0.5           # ANOMALY_THRESHOLD 이상만
):
    # anomaly_scores 테이블에서 is_anomaly=True 인 최근 N건 조회
    # equipment_id 무관하게 timestamp DESC 정렬
    # severity 계산: anomaly_score >= 0.8 → "critical", >= 0.6 → "warning"
    pass
```

| 항목 | 값 |
|------|-----|
| 성공 응답 | 200 + `AlarmFeedResponse` |
| 알람 없음 | 200 + `{"alarms": [], "total_count": 0}` |

### 3.10 `GET /api/health`

```python
@app.get("/api/health")
async def health_check():
    pg_ok = check_postgres_connection()
    neo4j_ok = check_neo4j_connection()
    return {
        "status": "healthy" if (pg_ok and neo4j_ok) else "degraded",
        "postgres": "connected" if pg_ok else "disconnected",
        "neo4j": "connected" if neo4j_ok else "disconnected",
        "timestamp": datetime.utcnow()
    }
```

---

## 4. 내부 호출 흐름 (main.py)

엔드포인트는 외부 HTTP용이지만, 메인 루프에서는 서비스 함수를 **직접 호출**한다.

```python
# main.py — 5초 폴링 루프 (의사코드)
async def main_loop():
    while True:
        for eq_id in ["CNC-001", "CNC-002", "CNC-003"]:
            # F1 → F2 (매번)
            sensor = f1_collector.poll_and_preprocess(eq_id)
            anomaly = f2_detector.detect(eq_id, sensor)

            # F3 → F4 → F5 (알람 시만)
            if anomaly.is_anomaly:
                # F5는 LLM API 호출(2~10초)로 병목 → 비동기 분리
                # Phase 3 구현 시 asyncio.create_task()로 분리하여
                # 대시보드 갱신을 블로킹하지 않도록 처리
                asyncio.create_task(
                    process_alarm(eq_id, anomaly)  # F3→F4→F5→push_alert
                )

            # F6 갱신 (매번)
            f6_dashboard.update(eq_id, sensor, anomaly)

        await asyncio.sleep(config.POLL_INTERVAL_SEC)
```

> **HTTP 엔드포인트 vs 직접 호출:**
> - 메인 루프: 서비스 함수 직접 호출 (성능, 오버헤드 없음)
> - HTTP 엔드포인트: 개별 테스트, 디버깅, 외부 연동용
> - 같은 서비스 로직을 공유하므로 코드 중복 없음

---

## 5. 인증 및 보안

### MVP (Phase 3)

| 항목 | 접근 방식 |
|------|----------|
| 인증 | 미적용 (내부 네트워크 전제) |
| API Key | Phase 3 후반 또는 Phase 4에서 도입 검토 |
| CORS | 대시보드 프론트엔드 도메인만 허용 |
| Rate Limit | 미적용 (5초 폴링 × 3대 = 저부하) |

> MVP에서는 Docker 내부 네트워크에서만 접근 가능하므로 인증 생략.
> 외부 노출 시 API Key 또는 JWT 도입. 확장 지점만 코드에 표시.

```python
# 확장 지점 예시
# from fastapi.security import APIKeyHeader
# api_key_header = APIKeyHeader(name="X-API-Key")
# @app.get("/api/f6/summary", dependencies=[Depends(verify_api_key)])
```

---

## 6. 에러 응답 형식

모든 에러는 동일한 JSON 형식으로 반환:

```python
class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str              # "E1", "E2", ...
    message: str                 # 사람이 읽을 수 있는 설명
    timestamp: datetime
    details: Optional[Dict] = None

# 예시
{
    "status": "error",
    "error_code": "E4",
    "message": "LLM API 호출 실패 (3회 재시도 후). 기술자 수동 판단 필요.",
    "timestamp": "2024-01-22T09:15:05Z",
    "details": {
        "provider": "openai",
        "http_status": 429,
        "retry_count": 3
    }
}
```

---

## 7. 응답 시간 예상

| 엔드포인트 | 예상 응답 시간 | 병목 |
|-----------|-------------|------|
| F1 collect | < 100ms | PG INSERT |
| F2 detect | 100ms ~ 1s | 모델 추론 |
| F3 sync | < 100ms | PG SELECT 3건 |
| F4 search | 200ms ~ 500ms | Neo4j 순회 + pgvector |
| F5 generate | 2s ~ 10s | LLM API 호출 |
| F6 summary | < 100ms | PG SELECT |
| F6 sensors | 100ms ~ 500ms | TimescaleDB 시계열 조회 |

> **F5가 병목:** LLM API 호출은 2~10초 소요.
> 메인 루프에서는 F5를 비동기로 실행하고, 대시보드는 결과가 올 때까지 이전 상태 유지.

---

## 리뷰 결정 사항

| # | 질문 | 결정 | 근거 |
|---|------|------|------|
| 1 | 엔드포인트 12개 | **적절** | 기능별 1:1 매핑, 억지로 합치면 복잡해짐 |
| 2 | F6 5개 분리 | **분리 유지** | 갱신 주기가 다름 (센서 5초 vs 작업/재고 알람 시) |
| 3 | 직접 호출 + HTTP | **적절** | 코드 공유, 디버깅 용이 |
| 4 | 인증 생략 | **MVP OK** | Docker 내부 네트워크, 확장 지점 주석 있음 |

---

## 리뷰 피드백 이력

### 리뷰 #1 (2026-03-15)

1. **엔드포인트 12개 — OK** ✅ 확인
2. **F6 분리 — OK** ✅ 확인
3. **직접 호출 + HTTP — OK** ✅ 확인
4. **인증 생략 — OK** ✅ 확인
5. **F5 비동기 처리:** 메인 루프에서 `asyncio.create_task()`로 분리 ✅ 반영
6. **series: List[Dict]:** Phase 3에서 SensorDataPoint 타입 강화 TODO 추가 ✅ 반영
7. **섹션 번호 불일치:** 인지만, 수정 불필요 ✅ 확인

### 리뷰 #2 (2026-03-16)

1. **AlarmFeed API 비효율:** `/api/f2/history/{equipment_id}` × 3대 호출 → `/api/f6/alarms` 단일 엔드포인트 신규 추가(#13) ✅ 반영
   - `AlarmEvent`, `AlarmFeedResponse` Pydantic 모델 추가
   - `severity` 필드 포함 (critical/warning)
