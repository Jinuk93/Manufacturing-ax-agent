// ============================================================
// 공통 타입 정의 — 백엔드 Pydantic 스키마와 1:1 대응
// ============================================================

// F6 — 설비 상태 요약
export type EquipmentStatus = 'normal' | 'warning' | 'critical' | 'offline'

export interface Equipment {
  equipment_id: string
  status: EquipmentStatus
  anomaly_score: number
  predicted_failure_code?: string
  last_updated: string          // ISO 8601
  if_score?: number
  forecast_score?: number
}

export interface DashboardSummary {
  equipments: Equipment[]
}

// F2 — 이상탐지 결과
export interface AnomalyResult {
  timestamp: string
  equipment_id: string
  anomaly_score: number
  is_anomaly: boolean
  predicted_failure_code?: string
  confidence?: number
  model_version?: string
  if_score?: number
  forecast_score?: number
}

// F5 — LLM 판단 결과
export type ActionType = 'STOP' | 'REDUCE' | 'MONITOR'

export interface PartNeeded {
  part_id: string
  quantity: number
  in_stock: boolean
}

export interface LLMActionResponse {
  equipment_id: string
  timestamp: string
  recommendation: ActionType
  confidence: number
  reasoning: string
  action_steps: string[]
  parts_needed: PartNeeded[]
  predicted_failure_code: string
  estimated_downtime_min?: number
}

// F4 — GraphRAG 참조 문서
export interface RelatedDocument {
  manual_id: string
  title: string
  hybrid_score: number
}

// F6 — 알람
export type AlarmSeverity = 'critical' | 'warning'

export interface AlarmEvent {
  timestamp: string
  equipment_id: string
  anomaly_score: number
  predicted_failure_code: string | null  // 백엔드 Optional → null 허용
  confidence: number
  severity: AlarmSeverity
}

export interface AlarmFeedResponse {
  alarms: AlarmEvent[]
  total: number
}

// F3 — 정비 이력
export interface MaintenanceRecord {
  event_id: string
  failure_code?: string
  event_type: string
  duration_min: number
  parts_used?: string
  event_time?: string
}

// F2 — 이상탐지 이력
export interface AnomalyHistoryResponse {
  equipment_id: string
  history: AnomalyResult[]
}

// F6 — 센서 시계열
export interface SensorPoint {
  timestamp: string
  x1_current_feedback?: number
  y1_current_feedback?: number
  s1_current_feedback?: number
  x1_output_power?: number
  s1_output_power?: number
}

export interface SensorTimeseriesResponse {
  equipment_id: string
  duration_hours: number
  series: SensorPoint[]
}

// F6 — 작업지시 / 재고
export interface WorkOrderDetail {
  work_order_id: string
  product_type: string
  due_date: string
  priority: string
  status: string
}

export interface InventoryItem {
  part_id: string
  part_name: string
  stock_quantity: number
  reorder_point: number
}

export interface WorkOrderOverlayResponse {
  equipment_id: string
  work_order?: WorkOrderDetail
  inventory: InventoryItem[]
  recent_maintenance?: MaintenanceRecord[]
}

// 헬스 체크
export interface HealthResponse {
  status: 'ok' | 'degraded'
  postgres: boolean
  neo4j: boolean
  timestamp: string
}

// F4 — GraphRAG 관련 타입
export interface RelatedPart {
  part_id: string
  part_name: string
  quantity: number
  urgency: string
}

export interface PastMaintenanceEvent {
  event_id: string
  event_type: string
  duration_min: number
  parts_used?: string
}

// F4 — GraphRAG 검색 응답 (참조 문서용)
export interface GraphRAGResponse {
  failure_code: string
  related_documents: RelatedDocument[]
  related_parts: RelatedPart[]
  past_maintenance: PastMaintenanceEvent[]
}

// 챗봇
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}
