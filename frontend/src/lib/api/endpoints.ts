// ============================================================
// API 엔드포인트 함수 — api-design.md의 엔드포인트와 1:1 대응
// ============================================================

import { api } from './client'
import type {
  Equipment,
  LLMActionResponse,
  RelatedDocument,
  Alarm,
  MaintenanceRecord,
  PartInventory,
  WorkOrder,
  ChatMessage,
} from '@/types'

// F6 — 설비 목록 + 요약 (5초 폴링)
export const getEquipmentSummary = () =>
  api.get<Equipment[]>('/f6/summary')

// F6 — 특정 설비 이상탐지 + LLM 판단 결과 (이벤트 기반)
export const getEquipmentDetail = (equipmentId: string) =>
  api.get<LLMActionResponse>(`/f6/equipment/${equipmentId}`)

// F4 — GraphRAG 참조 문서
export const getRelatedDocuments = (equipmentId: string) =>
  api.get<RelatedDocument[]>(`/f4/documents/${equipmentId}`)

// F6 — 알람 목록 (5초 폴링)
export const getAlarms = () =>
  api.get<Alarm[]>('/f6/alarms')

// F6 — 알람 확인(Acknowledge)
export const acknowledgeAlarm = (alarmId: string) =>
  api.post<void>(`/f6/alarms/${alarmId}/acknowledge`, {})

// F6 — 정비 이력 (60초 폴링)
export const getMaintenanceHistory = (equipmentId: string) =>
  api.get<MaintenanceRecord[]>(`/f6/maintenance/${equipmentId}`)

// ERP — 부품 재고 (30초 폴링)
export const getInventory = () =>
  api.get<PartInventory[]>('/erp/inventory')

// MES — 작업지시 (30초 폴링)
export const getWorkOrders = () =>
  api.get<WorkOrder[]>('/mes/workorders')

// 챗봇
export const sendChatMessage = (message: string, equipmentId?: string) =>
  api.post<ChatMessage>('/chat', { message, equipment_id: equipmentId })
