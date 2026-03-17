// ============================================================
// 공통 설비 데이터 훅 — 중복 쿼리 방지
// React Query의 queryKey 기반 캐시 공유를 활용
// ============================================================

import { useQuery } from '@tanstack/react-query'
import {
  getEquipmentSummary, getEquipmentAnomaly,
  getActionReport, getAnomalyHistory,
  getDashboardAlarms, getWorkOrderStatus,
} from '@/lib/api/endpoints'

// 공통 쿼리 옵션 — 일관된 설정
const POLL_5S = { refetchInterval: 5000, retry: 1, staleTime: 4000 }
const POLL_10S = { refetchInterval: 10000, retry: 1, staleTime: 8000 }
const LAZY = { retry: 1, staleTime: 30000 }

// 설비 목록
export function useEquipmentSummary() {
  return useQuery({ queryKey: ['equipment-summary'], queryFn: getEquipmentSummary, ...POLL_5S })
}

// 알람 피드
export function useAlarms() {
  return useQuery({ queryKey: ['alarms'], queryFn: getDashboardAlarms, ...POLL_5S })
}

// 특정 설비 이상 점수
export function useAnomaly(equipmentId: string | null) {
  return useQuery({
    queryKey: ['anomaly', equipmentId],
    queryFn: () => getEquipmentAnomaly(equipmentId!),
    enabled: !!equipmentId,
    ...POLL_5S,
  })
}

// 특정 설비 이상 이력
export function useAnomalyHistory(equipmentId: string | null) {
  return useQuery({
    queryKey: ['anomaly-history', equipmentId],
    queryFn: () => getAnomalyHistory(equipmentId!),
    enabled: !!equipmentId,
    ...POLL_10S,
  })
}

// LLM 판단
export function useActionReport(equipmentId: string | null) {
  return useQuery({
    queryKey: ['action', equipmentId],
    queryFn: () => getActionReport(equipmentId!),
    enabled: !!equipmentId,
    ...LAZY,
  })
}

// 작업 + 재고
export function useWorkOrder(equipmentId: string | null) {
  return useQuery({
    queryKey: ['work-order', equipmentId],
    queryFn: () => getWorkOrderStatus(equipmentId!),
    enabled: !!equipmentId,
    ...LAZY,
  })
}

// 3대 설비 일괄 조회 (중복 방지 — queryKey 동일하면 캐시 공유)
export function useAllEquipmentData() {
  const EQ_IDS = ['CNC-001', 'CNC-002', 'CNC-003'] as const

  const a1 = useAnomaly(EQ_IDS[0])
  const a2 = useAnomaly(EQ_IDS[1])
  const a3 = useAnomaly(EQ_IDS[2])
  const r1 = useActionReport(EQ_IDS[0])
  const r2 = useActionReport(EQ_IDS[1])
  const r3 = useActionReport(EQ_IDS[2])
  const h1 = useAnomalyHistory(EQ_IDS[0])
  const h2 = useAnomalyHistory(EQ_IDS[1])
  const h3 = useAnomalyHistory(EQ_IDS[2])

  return {
    EQ_IDS,
    anomalies: [a1.data, a2.data, a3.data],
    actions: [r1.data, r2.data, r3.data],
    histories: [h1.data, h2.data, h3.data],
  }
}
