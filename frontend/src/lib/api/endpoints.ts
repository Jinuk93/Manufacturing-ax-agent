// ============================================================
// API 엔드포인트 함수 — 실제 백엔드 라우트와 1:1 대응
// ============================================================

import { api } from './client'
import type {
  DashboardSummary,
  Equipment,
  LLMActionResponse,
  AnomalyResult,
  AnomalyHistoryResponse,
  AlarmFeedResponse,
  SensorTimeseriesResponse,
  WorkOrderOverlayResponse,
  HealthResponse,
  GraphRAGResponse,
} from '@/types'

// F6 — 설비 요약 (DashboardSummary → equipments 배열 추출)
export const getEquipmentSummary = async (): Promise<Equipment[]> => {
  const res = await api.get<DashboardSummary>('/f6/summary')
  return res.equipments
}

// F6 — 특정 설비 현재 이상 점수
export const getEquipmentAnomaly = (equipmentId: string) =>
  api.get<AnomalyResult>(`/f6/anomaly/${equipmentId}`)

// F6 — 온디맨드 F2→F3→F4→F5 파이프라인 (LLM 조치 리포트)
export const getActionReport = (equipmentId: string) =>
  api.get<LLMActionResponse>(`/f6/action/${equipmentId}`)

// F6 — 센서 시계열
export const getSensorTimeseries = (equipmentId: string) =>
  api.get<SensorTimeseriesResponse>(`/f6/sensors/${equipmentId}`)

// F6 — 알람 피드
export const getDashboardAlarms = () =>
  api.get<AlarmFeedResponse>('/f6/alarms')

// F6 — 작업 + 재고 + 정비이력 현황
export const getWorkOrderStatus = (equipmentId: string) =>
  api.get<WorkOrderOverlayResponse>(`/f6/work-order/${equipmentId}`)

// F2 — 이상 점수 이력 (추이 차트용)
export const getAnomalyHistory = (equipmentId: string) =>
  api.get<AnomalyHistoryResponse>(`/f2/history/${equipmentId}`)

// 헬스 체크 (상태 표시용)
export const getHealth = () =>
  api.get<HealthResponse>('/health')

// F4 — GraphRAG 검색 (참조 문서용)
export const searchGraphRAG = (failureCode: string, equipmentId: string) =>
  api.post<GraphRAGResponse>('/f4/search', { failure_code: failureCode, equipment_id: equipmentId })
