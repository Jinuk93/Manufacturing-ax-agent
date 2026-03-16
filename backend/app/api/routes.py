"""
FastAPI 라우터 — 13개 엔드포인트 (mock 응답)
Phase 3에서 실제 로직으로 교체 예정
"""
from datetime import datetime
from fastapi import APIRouter

from app.models.schemas import (
    SensorCollectRequest, SensorCollectResponse,
    AnomalyDetectRequest, AnomalyDetectResponse, AnomalyResult,
    AnomalyHistoryResponse,
    ITOTSyncResponse, WorkOrderInfo, InventoryItem, MaintenanceRecord,
    GraphRAGRequest, GraphRAGResponse, RelatedPart, RelatedDocument, PastMaintenance,
    LLMActionResponse, PartNeeded,
    DashboardSummary, EquipmentStatus,
    AlarmFeedResponse, AlarmEvent,
    HealthResponse,
)

router = APIRouter(prefix="/api")


# ── F1: 센서 수집 ──
@router.post("/f1/collect", response_model=SensorCollectResponse)
async def collect_sensor(req: SensorCollectRequest):
    """센서 값 수집 + 전처리 → sensor_readings INSERT"""
    # TODO: 실제 DB INSERT + 전처리 로직
    return SensorCollectResponse(
        status="ok",
        rows_inserted=1,
        equipment_id=req.equipment_id,
        timestamp=req.timestamp,
    )


# ── F2: 이상탐지 ──
@router.post("/f2/detect", response_model=AnomalyDetectResponse)
async def detect_anomaly(req: AnomalyDetectRequest):
    """이상탐지 모델 추론 → anomaly_scores INSERT"""
    # TODO: 실제 모델 추론 로직
    return AnomalyDetectResponse(
        status="ok",
        result=AnomalyResult(
            timestamp=req.timestamp,
            equipment_id=req.equipment_id,
            anomaly_score=0.23,
            is_anomaly=False,
            predicted_failure_code=None,
            confidence=None,
            model_version="mock-v0",
        ),
    )


@router.get("/f2/history/{equipment_id}", response_model=AnomalyHistoryResponse)
async def anomaly_history(equipment_id: str):
    """특정 설비의 이상 점수 이력"""
    # TODO: DB에서 최근 N건 조회
    return AnomalyHistoryResponse(
        equipment_id=equipment_id,
        history=[],
    )


# ── F3: IT/OT 동기화 ──
@router.post("/f3/sync", response_model=ITOTSyncResponse)
async def sync_itot(equipment_id: str, timestamp: datetime):
    """이상 감지 시 IT 데이터(MES+CMMS+ERP) 조회"""
    # TODO: 실제 3개 SQL 쿼리
    return ITOTSyncResponse(
        equipment_id=equipment_id,
        timestamp=timestamp,
        latest_work_order=WorkOrderInfo(
            work_order_id="WO-2024-008",
            product_type="WAX_BLOCK_6MM",
            due_date=datetime(2024, 1, 22, 10, 30),
            priority="urgent",
            status="completed",
        ),
        work_order_note=None,
        recent_maintenance=[
            MaintenanceRecord(
                event_id="MT-2024-007",
                failure_code="SPINDLE_OVERHEAT_001",
                event_type="corrective",
                duration_min=75,
                parts_used="P002",
            )
        ],
        inventory=[
            InventoryItem(part_id="P001", part_name="Endmill 6mm Carbide", stock_quantity=12, reorder_point=5, lead_time_days=3),
            InventoryItem(part_id="P002", part_name="Spindle Bearing Set", stock_quantity=2, reorder_point=2, lead_time_days=7),
            InventoryItem(part_id="P003", part_name="Coolant 20L", stock_quantity=8, reorder_point=3, lead_time_days=2),
            InventoryItem(part_id="P004", part_name="Clamp Bolt Set", stock_quantity=9, reorder_point=4, lead_time_days=1),
            InventoryItem(part_id="P005", part_name="Air Filter", stock_quantity=5, reorder_point=3, lead_time_days=1),
        ],
    )


# ── F4: GraphRAG ──
@router.post("/f4/search", response_model=GraphRAGResponse)
async def search_graphrag(req: GraphRAGRequest):
    """Neo4j 그래프 순회 + pgvector 의미 검색"""
    # TODO: 실제 Neo4j + pgvector 쿼리
    return GraphRAGResponse(
        failure_code=req.failure_code,
        related_parts=[
            RelatedPart(part_id="P002", part_name="Spindle Bearing Set", quantity=1, urgency="high"),
        ],
        related_documents=[
            RelatedDocument(manual_id="DOC-004", title="스핀들 베어링 교체 절차서", hybrid_score=0.92),
            RelatedDocument(manual_id="DOC-006", title="스핀들 과열 트러블슈팅 가이드", hybrid_score=0.87),
        ],
        past_maintenance=[
            PastMaintenance(event_id="MT-2024-007", event_type="corrective", duration_min=75, parts_used="P002"),
        ],
    )


# ── F5: LLM 판단 ──
@router.post("/f5/generate-action", response_model=LLMActionResponse)
async def generate_action(equipment_id: str):
    """F2+F3+F4 결과를 LLM에게 전달 → 조치 권고"""
    # TODO: 실제 LLM API 호출
    return LLMActionResponse(
        equipment_id=equipment_id,
        timestamp=datetime.now(),
        recommendation="REDUCE",
        confidence=0.85,
        reasoning="anomaly_score 0.87, 과거 동일 고장 평균 75분 소요. 현재 urgent 작업이나 납기까지 2시간 여유 있어 감속 운전 후 정비 권장.",
        action_steps=[
            "feedrate를 50% 감속",
            "현재 작업 완료까지 감속 운전 유지",
            "작업 완료 후 DOC-004 절차에 따라 베어링 교체",
            "P002 스핀들 베어링 1세트 준비",
        ],
        parts_needed=[
            PartNeeded(part_id="P002", quantity=1, in_stock=True),
        ],
        predicted_failure_code="SPINDLE_OVERHEAT_001",
        estimated_downtime_min=75,
    )


# ── F6: 대시보드 ──
@router.get("/f6/summary", response_model=DashboardSummary)
async def dashboard_summary():
    """CNC 3대 상태 요약"""
    # TODO: 실제 DB 조회
    now = datetime.now()
    return DashboardSummary(
        equipments=[
            EquipmentStatus(equipment_id="CNC-001", status="normal", anomaly_score=0.21, last_updated=now),
            EquipmentStatus(equipment_id="CNC-002", status="warning", anomaly_score=0.74, predicted_failure_code="SPINDLE_OVERHEAT_001", last_updated=now),
            EquipmentStatus(equipment_id="CNC-003", status="normal", anomaly_score=0.18, last_updated=now),
        ]
    )


@router.get("/f6/sensors/{equipment_id}")
async def sensor_timeseries(equipment_id: str, duration_hours: int = 1):
    """특정 설비의 센서 시계열"""
    # TODO: TimescaleDB 시계열 조회
    return {"equipment_id": equipment_id, "duration_hours": duration_hours, "series": []}


@router.get("/f6/anomaly/{equipment_id}", response_model=AnomalyResult)
async def anomaly_status(equipment_id: str):
    """특정 설비의 현재 이상 점수"""
    # TODO: 최신 anomaly_scores 조회
    return AnomalyResult(
        timestamp=datetime.now(),
        equipment_id=equipment_id,
        anomaly_score=0.23,
        is_anomaly=False,
        model_version="mock-v0",
    )


@router.get("/f6/work-order/{equipment_id}")
async def work_order_status(equipment_id: str):
    """작업 + 재고 현황"""
    # TODO: MES + ERP 조회
    return {"equipment_id": equipment_id, "work_order": None, "inventory": []}


@router.get("/f6/action/{equipment_id}")
async def action_report(equipment_id: str):
    """LLM 조치 리포트 (최신)"""
    # TODO: 최신 F5 결과 조회
    return {"equipment_id": equipment_id, "report": None}


@router.get("/f6/alarms", response_model=AlarmFeedResponse)
async def alarm_feed(limit: int = 20):
    """전체 알람 피드 (최근 N건)"""
    # TODO: anomaly_scores에서 is_anomaly=true인 것 조회
    return AlarmFeedResponse(alarms=[], total=0)


# ── 헬스 체크 ──
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """PostgreSQL + Neo4j 연결 상태 확인"""
    # TODO: 실제 연결 체크
    return HealthResponse(
        status="ok",
        postgres=True,
        neo4j=True,
        timestamp=datetime.now(),
    )
