// ============================================================
// Topbar — 상단 바
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getHealth } from '@/lib/api/endpoints'
import { useDashboardStore } from '@/stores/dashboardStore'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

function NavButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '5px 14px', fontSize: '11px', fontWeight: 600, fontFamily: sans,
        color: active ? 'var(--gray5)' : 'var(--gray4)',
        background: active ? 'linear-gradient(180deg, var(--dg3) 0%, var(--dg2) 100%)' : 'var(--dg2)',
        border: active ? '1px solid var(--border-strong)' : '1px solid var(--border-mid)',
        borderRadius: '3px', cursor: 'pointer', transition: 'all 0.15s',
        boxShadow: active ? 'inset 0 1px 0 rgba(255,255,255,0.05), 0 1px 2px rgba(0,0,0,0.3)' : '0 1px 2px rgba(0,0,0,0.2)',
      }}
      onMouseEnter={(e) => { if (!active) { e.currentTarget.style.borderColor = 'var(--border-strong)'; e.currentTarget.style.color = 'var(--gray5)' } }}
      onMouseLeave={(e) => { if (!active) { e.currentTarget.style.borderColor = 'var(--border-mid)'; e.currentTarget.style.color = 'var(--gray4)' } }}
    >
      {label}
    </button>
  )
}

export default function Topbar() {
  const { activeOverlay, toggleOverlay, selectedEquipmentId, selectedAlarm, setSelectedEquipmentId, setSelectedAlarm } = useDashboardStore()

  const { data: health, dataUpdatedAt } = useQuery({ queryKey: ['health'], queryFn: getHealth, refetchInterval: 10000, retry: false })

  const isOverview = selectedEquipmentId === null && selectedAlarm === null
  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '--:--:--'

  return (
    <div className="relative z-10">
      <div className="flex items-center gap-4 px-5" style={{
        height: 'var(--topbar-h)',
        background: 'linear-gradient(180deg, var(--dg1) 0%, rgba(10,16,28,0.95) 100%)',
        borderBottom: '1px solid var(--border-mid)',
      }}>
        {/* 로고 */}
        <div className="flex items-center gap-0 mr-2 select-none">
          <span style={{ fontFamily: sans, fontWeight: 800, fontSize: '13px', letterSpacing: '0.18em', color: 'var(--gray5)', textTransform: 'uppercase' }}>MANUFACTURING</span>
          <span style={{ fontFamily: mono, fontWeight: 700, fontSize: '13px', letterSpacing: '0.08em', color: 'var(--cyan)', marginLeft: '6px', textShadow: '0 0 12px rgba(0,212,255,0.4)' }}>AX</span>
        </div>

        <span style={{ width: '1px', height: '20px', background: 'var(--border-strong)' }} />

        {/* 좌측 버튼 그룹 */}
        <div className="flex items-center gap-2">
          <NavButton label="작업현황" active={activeOverlay === 'work'} onClick={() => toggleOverlay('work')} />
          <NavButton label="재고현황" active={activeOverlay === 'inventory'} onClick={() => toggleOverlay('inventory')} />
        </div>

        {/* 우측 — LIVE + 시간 */}
        <div className="flex items-center gap-3 ml-auto">
          <div className="flex items-center gap-1.5">
            <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--green5)', animation: 'live-blink 1.5s ease-in-out infinite' }} />
            <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--green5)', fontWeight: 600 }}>LIVE</span>
          </div>
          <span style={{ width: '1px', height: '16px', background: 'var(--border-mid)' }} />
          <span style={{ fontFamily: mono, fontSize: '10px', color: 'var(--gray3)' }}>{lastUpdated}</span>
        </div>
      </div>
    </div>
  )
}
