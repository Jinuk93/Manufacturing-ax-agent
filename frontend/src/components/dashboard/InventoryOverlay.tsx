// ============================================================
// InventoryOverlay — 재고현황 오버레이 (AI패널 영역에서 내려옴)
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getWorkOrderStatus } from '@/lib/api/endpoints'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

export default function InventoryOverlay({ open }: { open: boolean }) {
  const { data } = useQuery({ queryKey: ['inventory'], queryFn: () => getWorkOrderStatus('CNC-001'), enabled: open, retry: false, staleTime: 60_000, refetchInterval: open ? 60_000 : false })
  const inventory = data?.inventory ?? []

  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, width: '320px',
      overflow: 'hidden',
      maxHeight: open ? '260px' : '0',
      transition: 'max-height 0.3s ease',
      background: 'var(--dg1-5)',
      borderBottom: open ? '1px solid var(--border-mid)' : 'none',
      borderRadius: '0 0 3px 3px',
      boxShadow: open ? '0 4px 12px rgba(0,0,0,0.4)' : 'none',
      zIndex: 50,
    }}>
      <div className="p-4">
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray4)', fontFamily: sans, marginBottom: '10px' }}>부품 재고 현황</div>
        <div className="space-y-2">
          {inventory.map((part) => {
            const ratio = part.stock_quantity / Math.max(part.reorder_point * 3, 1)
            const low = part.stock_quantity <= part.reorder_point
            const barColor = low ? 'var(--red5)' : 'var(--cyan)'
            return (
              <div key={part.part_id} className="flex items-center gap-3">
                <span style={{ fontFamily: mono, fontSize: '10px', width: '36px', flexShrink: 0, color: 'var(--cyan)', fontWeight: 600 }}>{part.part_id}</span>
                <span style={{ fontSize: '10px', flex: 1, color: 'var(--gray5)', fontFamily: sans, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{part.part_name}</span>
                <div style={{ width: '50px', height: '3px', flexShrink: 0, background: 'var(--dg4)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${Math.min(ratio * 100, 100).toFixed(0)}%`, background: barColor, transition: 'width 0.3s' }} />
                </div>
                <span style={{ fontFamily: mono, fontSize: '10px', width: '36px', textAlign: 'right', flexShrink: 0, fontWeight: 600, color: low ? 'var(--red5)' : 'var(--gray4)' }}>{part.stock_quantity}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
