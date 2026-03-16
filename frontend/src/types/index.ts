// ============================================================
// 공통 타입 정의 — api-design.md의 Pydantic 모델과 대응
// ============================================================

// 설비 상태 (F6 summary 응답)
export type EquipmentStatus = 'normal' | 'warning' | 'critical' | 'offline'

export interface Equipment {
  equipment_id: string        // 예: 'CNC-001'
  status: EquipmentStatus
  anomaly_score: number       // 0.0 ~ 1.0
  last_updated: string        // ISO 8601
}

// F2 이상탐지 결과
export interface AnomalyResult {
  equipment_id: string
  timestamp: string
  anomaly_score: number
  is_anomaly: boolean
  sensor_contributions: Record<string, number>
}

// F5 LLM 판단 결과
export type ActionType = 'STOP' | 'REDUCE' | 'MONITOR' | 'NORMAL'

export interface LLMActionResponse {
  equipment_id: string
  timestamp: string
  action: ActionType
  reasoning: string
  steps: string[]
  // 판단 투명성 (섹션 10)
  input_summary?: Record<string, unknown>
  rag_documents?: string[]
  alternatives_considered?: string
  full_reasoning?: string
}

// GraphRAG 참조 문서 (F4)
export interface RelatedDocument {
  manual_id: string
  title: string
  hybrid_score: number
  bm25_score: number
  vector_score: number
  snippet?: string            // UI 표시용 최대 200자
}

// 알람
export type AlarmSeverity = 'critical' | 'warning' | 'info'

export interface Alarm {
  alarm_id: string
  equipment_id: string
  severity: AlarmSeverity
  message: string
  timestamp: string
  acknowledged: boolean
}

// 정비 이력 (섹션 9)
export interface MaintenanceRecord {
  record_id: string
  equipment_id: string
  failure_code: string
  date: string
  duration_min: number
  parts_used: string[]
  type: 'repair' | 'preventive'
}

// 부품 재고 (ERP)
export interface PartInventory {
  part_id: string             // 예: 'P001'
  name: string
  stock: number
  min_stock: number
  unit: string
}

// 작업지시 (MES)
export type WorkOrderUrgency = 'urgent' | 'normal' | 'low'

export interface WorkOrder {
  wo_id: string
  equipment_id: string
  product: string
  urgency: WorkOrderUrgency
  deadline: string
  status: string
}

// 챗봇
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  references?: string[]       // 참조 문서 ID 목록
  timestamp: string
}
