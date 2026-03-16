// ============================================================
// Topbar — 상단 바
// 로고 | Critical 배너 | 작업현황 / 재고현황 버튼 | 오버레이
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getDashboardAlarms } from '@/lib/api/endpoints'
import { useDashboardStore } from '@/stores/dashboardStore'
import WorkOrderOverlay from '../dashboard/WorkOrderOverlay'
import InventoryOverlay from '../dashboard/InventoryOverlay'

export default function Topbar() {
  const { activeOverlay, toggleOverlay } = useDashboardStore()

  // 알람 데이터 조회 — critical 알람 있으면 STOP 배너 표시
  const { data: alarmData } = useQuery({
    queryKey: ['alarms'],
    queryFn: getDashboardAlarms,
    refetchInterval: 5000,
    retry: false,
  })

  const criticalAlarms = alarmData?.alarms?.filter(
    (a) => a.severity === 'critical'
  ) ?? []
  const latestCritical = criticalAlarms[0] ?? null

  return (
    <div className="relative z-10">
      {/* 메인 바 */}
      <div
        className="flex items-center gap-3 px-4"
        style={{
          height: '44px',
          background: 'var(--dg1)',
          borderBottom: '1px solid var(--border-mid)',
        }}
      >
        {/* 로고 — AX Manufacturing */}
        <div className="flex items-center gap-0 mr-4 select-none">
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontWeight: 600,
              fontSize: '15px',
              letterSpacing: '-0.01em',
              color: 'var(--gray6)',
            }}
          >
            AX
          </span>
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontWeight: 300,
              fontSize: '13px',
              letterSpacing: '0.18em',
              color: 'var(--gray3)',
              marginLeft: '6px',
              textTransform: 'uppercase',
            }}
          >
            Manufacturing
          </span>
        </div>

        {/* Critical STOP 배너 — 깜빡이는 빨간 배경, 테두리 없음 */}
        {latestCritical && (
          <div
            className="stop-banner flex items-center gap-2 px-3 py-1 rounded"
            style={{ flex: '0 1 auto' }}
          >
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 700,
                fontSize: '11px',
                letterSpacing: '0.1em',
                color: 'rgba(255,255,255,0.95)',
              }}
            >
              {latestCritical.equipment_id}
            </span>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 600,
                fontSize: '11px',
                color: 'rgba(255,200,200,0.9)',
              }}
            >
              STOP
            </span>
          </div>
        )}

        {/* 오버레이 토글 버튼 */}
        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={() => toggleOverlay('work')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{
              background:
                activeOverlay === 'work'
                  ? 'var(--dg3)'
                  : 'transparent',
              color: activeOverlay === 'work' ? 'var(--gray5)' : 'var(--gray4)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M2 4h12v1.5H2V4zm0 3.5h12V9H2V7.5zm0 3.5h8V12H2v-1z"/>
            </svg>
            작업현황
          </button>

          <button
            onClick={() => toggleOverlay('inventory')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{
              background:
                activeOverlay === 'inventory'
                  ? 'var(--dg3)'
                  : 'transparent',
              color:
                activeOverlay === 'inventory' ? 'var(--gray5)' : 'var(--gray4)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M2 2h12v3H2V2zm0 4h4v8H2V6zm5 0h4v8H7V6zm5 0h2v8h-2V6z"/>
            </svg>
            재고현황
          </button>
        </div>
      </div>

      {/* 슬라이드다운 오버레이 */}
      <WorkOrderOverlay open={activeOverlay === 'work'} />
      <InventoryOverlay open={activeOverlay === 'inventory'} />
    </div>
  )
}
