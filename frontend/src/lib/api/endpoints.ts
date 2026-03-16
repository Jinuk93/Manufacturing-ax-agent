// ============================================================
// API 엔드포인트 함수 — 실제 백엔드 라우트와 1:1 대응
// ============================================================

import { api } from './client'
import type {
  DashboardSummary,
  Equipment,
  LLMActionResponse,
  AnomalyResult,
  AlarmFeedResponse,
  SensorTimeseriesResponse,
  WorkOrderOverlayResponse,
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

// F6 — 작업 + 재고 현황
export const getWorkOrderStatus = (equipmentId: string) =>
  api.get<WorkOrderOverlayResponse>(`/f6/work-order/${equipmentId}`)
