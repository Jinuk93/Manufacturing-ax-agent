// ============================================================
// InventoryOverlay — 재고현황 슬라이드다운 오버레이
// ============================================================

interface Props { open: boolean }

// 임시 더미 데이터 (Phase 3에서 API 연동)
const DUMMY_PARTS = [
  { part_id: 'P001', name: 'Endmill (10mm)', stock: 8,  min_stock: 5, unit: 'EA' },
  { part_id: 'P002', name: '스핀들 베어링',   stock: 2,  min_stock: 3, unit: 'EA' },
  { part_id: 'P003', name: '냉각수 필터',     stock: 12, min_stock: 5, unit: 'EA' },
  { part_id: 'P004', name: '드라이브 벨트',   stock: 4,  min_stock: 2, unit: 'EA' },
  { part_id: 'P005', name: '절삭유 (20L)',    stock: 3,  min_stock: 2, unit: 'CAN' },
]

export default function InventoryOverlay({ open }: Props) {
  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        overflow: 'hidden',
        maxHeight: open ? '320px' : '0',
        transition: 'max-height 0.25s ease',
        background: 'var(--dg1)',
        borderBottom: open ? '1px solid var(--border-mid)' : 'none',
        zIndex: 100,
      }}
    >
      <div className="p-4">
        <div
          className="text-xs font-semibold mb-3 uppercase tracking-wider"
          style={{ color: 'var(--gray3)' }}
        >
          부품 재고 현황
        </div>
        <div className="space-y-2">
          {DUMMY_PARTS.map((part) => {
            const ratio = part.stock / (part.min_stock * 3)
            const low = part.stock < part.min_stock
            const barColor = low ? 'var(--red5)' : 'var(--green5)'

            return (
              <div key={part.part_id} className="flex items-center gap-3">
                <span
                  className="font-mono text-xs w-10 flex-shrink-0"
                  style={{ color: 'var(--blue4)' }}
                >
                  {part.part_id}
                </span>
                <span
                  className="text-xs flex-1 truncate"
                  style={{ color: 'var(--gray5)' }}
                >
                  {part.name}
                </span>
                {/* 프로그레스 바 */}
                <div
                  className="rounded-full overflow-hidden flex-shrink-0"
                  style={{ width: '80px', height: '6px', background: 'var(--dg3)' }}
                >
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(ratio * 100, 100)}%`,
                      background: barColor,
                    }}
                  />
                </div>
                <span
                  className="font-mono text-xs w-14 text-right flex-shrink-0"
                  style={{ color: low ? 'var(--red5)' : 'var(--gray4)' }}
                >
                  {part.stock} {part.unit}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
