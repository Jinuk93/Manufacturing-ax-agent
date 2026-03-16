"""
Pydantic 모델 — api-design.md 기준 13개 엔드포인트의 요청/응답 타입
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── F1 센서 수집 ──
class SensorCollectRequest(BaseModel):
    equipment_id: str
    timestamp: datetime
    sensor_data: dict  # 42개 센서 값


class SensorCollectResponse(BaseModel):
    status: str
    rows_inserted: int
    equipment_id: str
    timestamp: datetime


# ── F2 이상탐지 ──
class AnomalyDetectRequest(BaseModel):
    equipment_id: str
    timestamp: datetime


class AnomalyResult(BaseModel):
    timestamp: datetime
    equipment_id: str
    anomaly_score: float
    is_anomaly: bool
    predicted_failure_code: Optional[str] = None
    confidence: Optional[float] = None
    model_version: Optional[str] = None


class AnomalyDetectResponse(BaseModel):
    status: str
    result: AnomalyResult


class AnomalyHistoryResponse(BaseModel):
    equipment_id: str
    history: list[AnomalyResult]


# ── F3 IT/OT 동기화 ──
class WorkOrderInfo(BaseModel):
    work_order_id: str
    product_type: str
    due_date: datetime
    priority: str
    status: str


class InventoryItem(BaseModel):
    part_id: str
    part_name: str
    stock_quantity: int
    reorder_point: int
    lead_time_days: int


class MaintenanceRecord(BaseModel):
    event_id: str
    failure_code: Optional[str]
    event_type: str
    duration_min: int
    parts_used: Optional[str]


class ITOTSyncResponse(BaseModel):
    equipment_id: str
    timestamp: datetime
    latest_work_order: Optional[WorkOrderInfo] = None
    work_order_note: Optional[str] = None
    recent_maintenance: list[MaintenanceRecord]
    inventory: list[InventoryItem]


# ── F3 IT/OT 동기화 요청 ──
class ITOTSyncRequest(BaseModel):
    timestamp: datetime
    equipment_id: str
    anomaly_score: float
    predicted_failure_code: str


# ── F4 GraphRAG ──
class GraphRAGRequest(BaseModel):
    failure_code: str
    equipment_id: str


class RelatedPart(BaseModel):
    part_id: str
    part_name: str
    quantity: int
    urgency: str


class RelatedDocument(BaseModel):
    manual_id: str
    title: str
    hybrid_score: float


class PastMaintenance(BaseModel):
    event_id: str
    event_type: str
    duration_min: int
    parts_used: Optional[str]


class GraphRAGResponse(BaseModel):
    failure_code: str
    related_parts: list[RelatedPart]
    related_documents: list[RelatedDocument]
    past_maintenance: list[PastMaintenance]


# ── F5 LLM 판단 ──
class PartNeeded(BaseModel):
    part_id: str
    quantity: int
    in_stock: bool


# ── F5 LLM 판단 요청 ──
class LLMActionRequest(BaseModel):
    equipment_id: str
    timestamp: datetime
    f2_result: AnomalyResult
    f3_context: ITOTSyncResponse
    f4_rag_result: GraphRAGResponse


class LLMActionResponse(BaseModel):
    equipment_id: str
    timestamp: datetime
    recommendation: str  # STOP / REDUCE / MONITOR
    confidence: float
    reasoning: str
    action_steps: list[str]
    parts_needed: list[PartNeeded]
    predicted_failure_code: str
    estimated_downtime_min: Optional[int] = None


# ── F6 대시보드 ──
class EquipmentStatus(BaseModel):
    equipment_id: str
    status: str  # normal / warning / critical
    anomaly_score: float
    predicted_failure_code: Optional[str] = None
    last_updated: datetime


class DashboardSummary(BaseModel):
    equipments: list[EquipmentStatus]


class AlarmEvent(BaseModel):
    timestamp: datetime
    equipment_id: str
    anomaly_score: float
    predicted_failure_code: str
    confidence: float
    severity: str  # critical / warning (프론트엔드 색상 구분용)


class AlarmFeedResponse(BaseModel):
    alarms: list[AlarmEvent]
    total: int


# ── 헬스 체크 ──
class HealthResponse(BaseModel):
    status: str
    postgres: bool
    neo4j: bool
    timestamp: datetime


# ── 에러 ──
class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    timestamp: datetime
