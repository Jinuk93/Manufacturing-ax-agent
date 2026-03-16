// ============================================================
// Sidebar — 설비 상태 + 이상 알람 피드 + 파이프라인 상태
// 200px 고정, 5초 폴링
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getEquipmentSummary, getDashboardAlarms } from '@/lib/api/endpoints'
import { useDashboardStore } from '@/stores/dashboardStore'
import type { Equipment, EquipmentStatus, AlarmEvent } from '@/types'

const STATUS_COLORS: Record<EquipmentStatus, string> = {
  normal:   'var(--green5)',
  warning:  'var(--yellow5)',
  critical: 'var(--red5)',
  offline:  'var(--gray3)',
}

const STATUS_LABELS: Record<EquipmentStatus, string> = {
  normal:   '정상',
  warning:  '경고',
  critical: '위험',
  offline:  '오프라인',
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div
      className="px-3 py-2 text-xs font-semibold uppercase tracking-wider flex-shrink-0"
      style={{ color: 'var(--gray3)', borderBottom: '1px solid var(--border-subtle)' }}
    >
      {label}
    </div>
  )
}

function EquipmentRow({ eq }: { eq: Equipment }) {
  const { selectedEquipmentId, setSelectedEquipmentId } = useDashboardStore()
  const selected = selectedEquipmentId === eq.equipment_id

  return (
    <button
      className="w-full text-left px-3 py-2.5 flex items-center gap-2.5 transition-colors"
      style={{
        background: selected ? 'var(--dg3)' : 'transparent',
        borderLeft: selected ? `2px solid var(--blue3)` : '2px solid transparent',
      }}
      onClick={() => setSelectedEquipmentId(eq.equipment_id)}
    >
      <div
        className="rounded-full flex-shrink-0"
        style={{
          width: '8px', height: '8px',
          background: STATUS_COLORS[eq.status],
          boxShadow: eq.status === 'critical' ? `0 0 6px ${STATUS_COLORS[eq.status]}` : 'none',
        }}
      />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium truncate" style={{ color: 'var(--gray5)' }}>
          {eq.equipment_id}
        </div>
        <div className="text-xs" style={{ color: STATUS_COLORS[eq.status] }}>
          {STATUS_LABELS[eq.status]}
        </div>
      </div>
      <div className="font-mono text-xs flex-shrink-0" style={{ color: 'var(--gray4)' }}>
        {(eq.anomaly_score * 100).toFixed(0)}
      </div>
    </button>
  )
}

function AlarmRow({ alarm }: { alarm: AlarmEvent }) {
  const { setSelectedEquipmentId } = useDashboardStore()
  const isCritical = alarm.severity === 'critical'
  const time = new Date(alarm.timestamp).toLocaleTimeString('ko-KR', {
    hour: '2-digit', minute: '2-digit',
  })

  return (
    <button
      className="w-full text-left px-3 py-2 transition-colors"
      style={{ borderLeft: `2px solid ${isCritical ? 'var(--red5)' : 'var(--yellow5)'}` }}
      onClick={() => setSelectedEquipmentId(alarm.equipment_id)}
    >
      <div className="flex items-center justify-between gap-1">
        <span
          className="font-mono text-xs font-semibold"
          style={{ color: isCritical ? 'var(--red5)' : 'var(--yellow5)' }}
        >
          {alarm.equipment_id}
        </span>
        <span
          className="font-mono text-xs"
          style={{ color: isCritical ? 'var(--red5)' : 'var(--yellow5)' }}
        >
          {alarm.anomaly_score.toFixed(2)}
        </span>
      </div>
      <div className="text-xs truncate mt-0.5" style={{ color: 'var(--gray4)', maxWidth: '100%' }}>
        {alarm.predicted_failure_code?.replace(/_/g, ' ')}
      </div>
      <div className="text-xs mt-0.5" style={{ color: 'var(--gray3)' }}>
        {time}
      </div>
    </button>
  )
}

// 파이프라인 단계 표시
const PIPELINE_STEPS = [
  { key: 'F1', label: 'F1 수집' },
  { key: 'F2', label: 'F2 탐지' },
  { key: 'F3', label: 'F3 동기' },
  { key: 'F4', label: 'F4 RAG' },
  { key: 'F5', label: 'F5 LLM' },
  { key: 'F6', label: 'F6 UI' },
]

export default function Sidebar() {
  const { data: equipmentList = [] } = useQuery({
    queryKey: ['equipment-summary'],
    queryFn: getEquipmentSummary,
    refetchInterval: 5000,
    retry: false,
  })

  const { data: alarmData } = useQuery({
    queryKey: ['alarms'],
    queryFn: getDashboardAlarms,
    refetchInterval: 5000,
    retry: false,
  })

  const alarms = alarmData?.alarms ?? []
  const criticalCount = alarms.filter((a) => a.severity === 'critical').length
  const hasAnomaly = equipmentList.some((e) => e.status !== 'normal')

  return (
    <div
      className="flex flex-col flex-shrink-0 overflow-hidden"
      style={{
        width: 'var(--sidebar-w)',
        background: 'var(--dg1)',
        borderRight: '2px solid var(--border-mid)',
      }}
    >
      {/* 설비 상태 */}
      <SectionHeader label="설비 상태" />
      <div className="flex-shrink-0">
        {Array.isArray(equipmentList) && equipmentList.map((eq) => (
          <EquipmentRow key={eq.equipment_id} eq={eq} />
        ))}
      </div>

      {/* 이상 알람 */}
      <SectionHeader label="이상 알람" />
      <div className="overflow-y-auto" style={{ maxHeight: '180px' }}>
        {alarms.length === 0 ? (
          <div className="px-3 py-2 text-xs" style={{ color: 'var(--gray3)' }}>
            알람 없음
          </div>
        ) : (
          alarms.map((alarm, i) => (
            <AlarmRow key={`${alarm.equipment_id}-${alarm.timestamp}-${i}`} alarm={alarm} />
          ))
        )}
      </div>

      {/* 파이프라인 상태 */}
      <div className="mt-auto flex-shrink-0">
        <SectionHeader label="파이프라인 상태" />
        <div className="px-3 py-2.5" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {PIPELINE_STEPS.map((step) => {
            // F1~F3는 항상 active, F4~F6는 이상 있을 때만
            const active = ['F1', 'F2', 'F3'].includes(step.key) || hasAnomaly
            return (
              <div
                key={step.key}
                style={{
                  display: 'flex', alignItems: 'center', gap: '4px',
                  padding: '2px 0',
                }}
              >
                <span
                  style={{
                    width: '7px', height: '7px', borderRadius: '50%', flexShrink: 0,
                    background: active ? 'var(--green5)' : 'var(--gray3)',
                    boxShadow: active ? '0 0 4px rgba(114,202,155,0.5)' : 'none',
                  }}
                />
                <span style={{ fontSize: '10px', color: active ? 'var(--gray4)' : 'var(--gray3)' }}>
                  {step.label}
                </span>
              </div>
            )
          })}
        </div>
        {/* 폴링 주기 표시 */}
        <div className="px-3 pb-2" style={{ fontSize: '10px', color: 'var(--gray3)' }}>
          폴링 주기: 5초 / 알람 {criticalCount}건
        </div>
      </div>
    </div>
  )
}
