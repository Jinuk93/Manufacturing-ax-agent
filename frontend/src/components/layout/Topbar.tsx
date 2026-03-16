// ============================================================
// Topbar — 상단 바
// 로고 | Critical 배너 | 작업현황 / 재고현황 버튼 | 오버레이
// ============================================================

import { useDashboardStore } from '@/stores/dashboardStore'
import WorkOrderOverlay from '../dashboard/WorkOrderOverlay'
import InventoryOverlay from '../dashboard/InventoryOverlay'

export default function Topbar() {
  const { activeOverlay, toggleOverlay } = useDashboardStore()

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
        {/* 로고 (Palantir ring 스타일) */}
        <div className="flex items-center gap-2 mr-4">
          <div
            className="relative flex items-center justify-center"
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              border: '2px solid var(--blue4)',
              boxShadow:
                '0 0 0 1px rgba(76,144,240,0.15), 0 0 12px rgba(45,114,210,0.25)',
            }}
          >
            <span
              className="font-mono font-bold text-xs"
              style={{ color: 'var(--blue4)' }}
            >
              AX
            </span>
          </div>
          <span
            className="font-semibold text-xs tracking-widest uppercase"
            style={{ color: 'var(--gray4)' }}
          >
            Manufacturing
          </span>
        </div>

        {/* Critical 배너 (임시 — 실제로는 알람 상태에 따라 조건부 렌더) */}
        <div
          className="flex-1 flex items-center gap-2 px-3 py-1 rounded"
          style={{
            background:
              'linear-gradient(90deg, rgba(197,48,48,0.18) 0%, rgba(197,48,48,0.06) 60%, transparent 100%)',
            borderLeft: '3px solid var(--red3)',
          }}
        >
          <div
            className="rounded-full animate-pulse"
            style={{
              width: '10px',
              height: '10px',
              background: 'var(--red5)',
            }}
          />
          <span className="text-xs font-medium" style={{ color: 'var(--red5)' }}>
            CNC-002 이상 감지 — STOP 권고
          </span>
        </div>

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
            {/* 작업현황 아이콘 */}
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
            {/* 재고현황 아이콘 */}
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
