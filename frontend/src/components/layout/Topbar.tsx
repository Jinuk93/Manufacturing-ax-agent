// ============================================================
// Topbar — 상단 바
// 로고 | Critical 배너 | 작업현황 / 재고현황 버튼 | 상태 표시 | 오버레이
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getDashboardAlarms, getHealth } from '@/lib/api/endpoints'
import { useDashboardStore } from '@/stores/dashboardStore'
import WorkOrderOverlay from '../dashboard/WorkOrderOverlay'
import InventoryOverlay from '../dashboard/InventoryOverlay'

function StatusDot({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        style={{
          width: '7px',
          height: '7px',
          borderRadius: '50%',
          background: ok ? 'var(--green5)' : 'var(--red5)',
          boxShadow: ok ? '0 0 5px rgba(114,202,155,0.5)' : '0 0 5px rgba(241,116,116,0.5)',
          flexShrink: 0,
        }}
      />
      <span style={{ fontSize: '11px', color: 'var(--gray4)', fontFamily: "'Inter', sans-serif" }}>
        {label}
      </span>
    </div>
  )
}

export default function Topbar() {
  const { activeOverlay, toggleOverlay } = useDashboardStore()

  // 알람 데이터 조회 — critical 알람 있으면 STOP 배너 표시
  const { data: alarmData } = useQuery({
    queryKey: ['alarms'],
    queryFn: getDashboardAlarms,
    refetchInterval: 5000,
    retry: false,
  })

  // 헬스 체크 — 상태 표시 dots
  const { data: health, dataUpdatedAt } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 10000,
    retry: false,
  })

  const criticalAlarms = alarmData?.alarms?.filter((a) => a.severity === 'critical') ?? []
  const latestCritical = criticalAlarms[0] ?? null

  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '--:--:--'

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
        {/* 로고 — MANUFACTURING AX | CNC 관제 시스템 */}
        <div className="flex items-center gap-0 mr-2 select-none">
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontWeight: 700,
              fontSize: '13px',
              letterSpacing: '0.12em',
              color: 'var(--gray5)',
              textTransform: 'uppercase',
            }}
          >
            Manufacturing
          </span>
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontWeight: 700,
              fontSize: '13px',
              letterSpacing: '0.06em',
              color: 'var(--blue4)',
              marginLeft: '5px',
            }}
          >
            AX
          </span>
          <span
            style={{
              width: '1px',
              height: '14px',
              background: 'var(--border-strong)',
              margin: '0 10px',
            }}
          />
          <span style={{ fontSize: '11px', color: 'var(--gray3)', letterSpacing: '0.05em' }}>
            CNC 관제 시스템
          </span>
        </div>

        {/* Critical STOP 배너 */}
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

        {/* 우측: 오버레이 버튼 + 상태 표시 */}
        <div className="flex items-center gap-3 ml-auto">
          {/* 오버레이 토글 버튼 */}
          <button
            onClick={() => toggleOverlay('work')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{
              background: activeOverlay === 'work' ? 'var(--dg3)' : 'transparent',
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
              background: activeOverlay === 'inventory' ? 'var(--dg3)' : 'transparent',
              color: activeOverlay === 'inventory' ? 'var(--gray5)' : 'var(--gray4)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M2 2h12v3H2V2zm0 4h4v8H2V6zm5 0h4v8H7V6zm5 0h2v8h-2V6z"/>
            </svg>
            재고현황
          </button>

          {/* 구분선 */}
          <span style={{ width: '1px', height: '16px', background: 'var(--border-mid)' }} />

          {/* 연결 상태 dots */}
          <div className="flex items-center gap-3">
            <StatusDot label="PostgreSQL" ok={health?.postgres ?? false} />
            <StatusDot label="Neo4j" ok={health?.neo4j ?? false} />
            <StatusDot label="LLM API" ok={health?.status === 'ok'} />
          </div>

          {/* 구분선 */}
          <span style={{ width: '1px', height: '16px', background: 'var(--border-mid)' }} />

          {/* 마지막 갱신 시간 */}
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11px',
              color: 'var(--gray3)',
            }}
          >
            마지막 갱신 {lastUpdated}
          </span>
        </div>
      </div>

      {/* 슬라이드다운 오버레이 */}
      <WorkOrderOverlay open={activeOverlay === 'work'} />
      <InventoryOverlay open={activeOverlay === 'inventory'} />
    </div>
  )
}
