// ============================================================
// Sidebar — 설비 목록 + 상태 + 알람
// 200px 고정, 5초 폴링
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getEquipmentSummary } from '@/lib/api/endpoints'
import { useDashboardStore } from '@/stores/dashboardStore'
import type { Equipment, EquipmentStatus } from '@/types'

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

function EquipmentRow({ eq }: { eq: Equipment }) {
  const { selectedEquipmentId, setSelectedEquipmentId } = useDashboardStore()
  const selected = selectedEquipmentId === eq.equipment_id

  return (
    <button
      className="w-full text-left px-3 py-2.5 flex items-center gap-2.5 transition-colors"
      style={{
        background: selected ? 'var(--dg3)' : 'transparent',
        borderLeft: selected
          ? `2px solid var(--blue3)`
          : '2px solid transparent',
      }}
      onClick={() => setSelectedEquipmentId(eq.equipment_id)}
    >
      {/* 상태 도트 */}
      <div
        className="rounded-full flex-shrink-0"
        style={{
          width: '8px',
          height: '8px',
          background: STATUS_COLORS[eq.status],
          boxShadow:
            eq.status === 'critical'
              ? `0 0 6px ${STATUS_COLORS[eq.status]}`
              : 'none',
        }}
      />

      {/* 설비명 + 상태 */}
      <div className="flex-1 min-w-0">
        <div
          className="text-xs font-medium truncate"
          style={{ color: 'var(--gray5)' }}
        >
          {eq.equipment_id}
        </div>
        <div className="text-xs" style={{ color: STATUS_COLORS[eq.status] }}>
          {STATUS_LABELS[eq.status]}
        </div>
      </div>

      {/* 이상 점수 */}
      <div
        className="font-mono text-xs flex-shrink-0"
        style={{ color: 'var(--gray4)' }}
      >
        {(eq.anomaly_score * 100).toFixed(0)}
      </div>
    </button>
  )
}

export default function Sidebar() {
  const { data: equipmentList } = useQuery({
    queryKey: ['equipment-summary'],
    queryFn: getEquipmentSummary,
    refetchInterval: 5000,   // 5초 폴링
    placeholderData: [],
  })

  return (
    <div
      className="flex flex-col flex-shrink-0 overflow-hidden"
      style={{
        width: 'var(--sidebar-w)',
        background: 'var(--dg1)',
        borderRight: '2px solid var(--border-mid)',
      }}
    >
      {/* 헤더 */}
      <div
        className="px-3 py-2 text-xs font-semibold uppercase tracking-wider flex-shrink-0"
        style={{
          color: 'var(--gray3)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        설비 상태
      </div>

      {/* 설비 목록 */}
      <div className="flex-1 overflow-y-auto">
        {equipmentList?.map((eq) => (
          <EquipmentRow key={eq.equipment_id} eq={eq} />
        ))}
      </div>
    </div>
  )
}
