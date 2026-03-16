"""
FastAPI 라우터 — 13개 엔드포인트
F3/F4/F5는 실제 서비스 호출, 나머지는 mock (순차 교체 예정)
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SensorCollectRequest, SensorCollectResponse,
    AnomalyDetectRequest, AnomalyDetectResponse, AnomalyResult,
    AnomalyHistoryResponse,
    ITOTSyncRequest, ITOTSyncResponse,
    GraphRAGRequest, GraphRAGResponse,
    LLMActionRequest, LLMActionResponse,
    DashboardSummary, EquipmentStatus,
    AlarmFeedResponse, AlarmEvent,
    HealthResponse,
)
from app.services.itot_sync import sync_itot_context
from app.services.graphrag import search_graphrag
from app.services.llm_agent import generate_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ── F1: 센서 수집 ──
@router.post("/f1/collect", response_model=SensorCollectResponse)
async def collect_sensor(req: SensorCollectRequest):
    """센서 값 수집 + 전처리 → sensor_readings INSERT"""
    # TODO: simulator.py의 insert_sensor_readings 연결
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
    # TODO: anomaly_detector.py 연결 (모델 로드 + predict)
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


# ── F3: IT/OT 동기화 (실제 서비스 연결) ──
@router.post("/f3/sync", response_model=ITOTSyncResponse)
async def sync_itot(req: ITOTSyncRequest):
    """이상 감지 시 IT 데이터(MES+CMMS+ERP) 조회"""
    try:
        result = sync_itot_context(
            equipment_id=req.equipment_id,
            timestamp=req.timestamp,
            predicted_failure_code=req.predicted_failure_code,
        )
        return result
    except Exception as e:
        logger.error(f"F3 동기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"F3 sync error: {e}")


# ── F4: GraphRAG (실제 서비스 연결) ──
@router.post("/f4/search", response_model=GraphRAGResponse)
async def search_rag(req: GraphRAGRequest):
    """Neo4j 그래프 순회 + pgvector 의미 검색"""
    try:
        result = search_graphrag(
            failure_code=req.failure_code,
            equipment_id=req.equipment_id,
        )
        return result
    except Exception as e:
        logger.error(f"F4 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=f"F4 search error: {e}")


# ── F5: LLM 판단 (실제 서비스 연결) ──
@router.post("/f5/generate-action", response_model=LLMActionResponse)
async def gen_action(req: LLMActionRequest):
    """F2+F3+F4 결과를 종합하여 조치 권고"""
    try:
        result = generate_action(
            f2_result=req.f2_result,
            f3_context=req.f3_context,
            f4_rag_result=req.f4_rag_result,
        )
        return result
    except Exception as e:
        logger.error(f"F5 판단 실패: {e}")
        raise HTTPException(status_code=500, detail=f"F5 action error: {e}")


# ── F6: 대시보드 ──
@router.get("/f6/summary", response_model=DashboardSummary)
async def dashboard_summary():
    """CNC 3대 상태 요약"""
    # TODO: 실제 DB 조회 (anomaly_scores 최신값)
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
    # TODO: anomaly_scores에서 is_anomaly=true 조회
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
