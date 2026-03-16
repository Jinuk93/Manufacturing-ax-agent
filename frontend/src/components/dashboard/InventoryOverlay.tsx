// ============================================================
// InventoryOverlay — 재고현황 슬라이드다운 오버레이
// /api/f6/work-order/CNC-001 에서 inventory 조회 (설비 무관)
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getWorkOrderStatus } from '@/lib/api/endpoints'

interface Props { open: boolean }

export default function InventoryOverlay({ open }: Props) {
  const { data } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => getWorkOrderStatus('CNC-001'),
    enabled: open,
    retry: false,
    staleTime: 60_000,
    refetchInterval: open ? 60_000 : false,
  })

  const inventory = data?.inventory ?? []

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '420px',
        overflow: 'hidden',
        maxHeight: open ? '200px' : '0',
        transition: 'max-height 0.25s ease',
        background: 'var(--dg2)',
        borderBottom: open ? '1px solid var(--border-mid)' : 'none',
        borderLeft: open ? '1px solid var(--border-mid)' : 'none',
        zIndex: 100,
      }}
    >
      <div className="p-3">
        <div
          className="text-xs font-semibold mb-2 uppercase tracking-wider"
          style={{ color: 'var(--gray3)', fontFamily: "'Inter', sans-serif" }}
        >
          부품 재고 현황
        </div>
        <div className="space-y-1.5">
          {inventory.map((part) => {
            const ratio = part.stock_quantity / Math.max(part.reorder_point * 3, 1)
            const low = part.stock_quantity <= part.reorder_point
            const barColor = low ? 'var(--red5)' : 'var(--green5)'

            return (
              <div key={part.part_id} className="flex items-center gap-3">
                <span
                  className="text-xs w-10 flex-shrink-0"
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    color: 'var(--blue4)',
                  }}
                >
                  {part.part_id}
                </span>
                <span
                  className="text-xs flex-1 truncate"
                  style={{ color: 'var(--gray5)' }}
                >
                  {part.part_name}
                </span>
                <div
                  className="rounded-full overflow-hidden flex-shrink-0"
                  style={{ width: '60px', height: '5px', background: 'var(--dg3)' }}
                >
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(ratio * 100, 100).toFixed(0)}%`,
                      background: barColor,
                    }}
                  />
                </div>
                <span
                  className="text-xs w-12 text-right flex-shrink-0"
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    color: low ? 'var(--red5)' : 'var(--gray4)',
                  }}
                >
                  {part.stock_quantity}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
