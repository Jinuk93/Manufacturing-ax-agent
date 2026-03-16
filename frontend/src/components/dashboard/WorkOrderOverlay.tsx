// ============================================================
// WorkOrderOverlay — 작업현황 슬라이드다운 오버레이
// ============================================================

interface Props { open: boolean }

// 임시 더미 데이터 (Phase 3에서 API 연동)
const DUMMY_ORDERS = [
  { wo_id: 'WO-2024-007', equipment_id: 'CNC-002', product: 'SHAFT-A', urgency: 'urgent', deadline: '2h', status: '진행 중' },
  { wo_id: 'WO-2024-008', equipment_id: 'CNC-001', product: 'GEAR-B', urgency: 'normal', deadline: '6h', status: '대기' },
  { wo_id: 'WO-2024-009', equipment_id: 'CNC-003', product: 'FLANGE-C', urgency: 'low', deadline: '24h', status: '대기' },
]

const URGENCY_COLORS: Record<string, string> = {
  urgent: 'var(--red5)',
  normal: 'var(--yellow5)',
  low:    'var(--gray4)',
}

export default function WorkOrderOverlay({ open }: Props) {
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
          작업지시 현황
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr style={{ color: 'var(--gray3)' }}>
              <th className="text-left pb-2 font-medium">WO ID</th>
              <th className="text-left pb-2 font-medium">설비</th>
              <th className="text-left pb-2 font-medium">제품</th>
              <th className="text-left pb-2 font-medium">긴급도</th>
              <th className="text-left pb-2 font-medium">납기</th>
              <th className="text-left pb-2 font-medium">상태</th>
            </tr>
          </thead>
          <tbody>
            {DUMMY_ORDERS.map((wo) => (
              <tr key={wo.wo_id} style={{ color: 'var(--gray5)' }}>
                <td className="py-1 font-mono" style={{ color: 'var(--blue4)' }}>{wo.wo_id}</td>
                <td className="py-1">{wo.equipment_id}</td>
                <td className="py-1">{wo.product}</td>
                <td className="py-1" style={{ color: URGENCY_COLORS[wo.urgency] }}>{wo.urgency}</td>
                <td className="py-1 font-mono">{wo.deadline}</td>
                <td className="py-1" style={{ color: 'var(--gray4)' }}>{wo.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
