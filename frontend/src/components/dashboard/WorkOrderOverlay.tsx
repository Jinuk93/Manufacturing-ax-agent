// ============================================================
// WorkOrderOverlay — 작업현황 슬라이드다운 오버레이
// /api/f6/work-order/{equipment_id} 에서 실제 데이터 조회
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getWorkOrderStatus } from '@/lib/api/endpoints'

interface Props { open: boolean }

const PRIORITY_COLORS: Record<string, string> = {
  urgent:   'var(--red5)',
  critical: 'var(--red5)',
  normal:   'var(--yellow5)',
  low:      'var(--gray4)',
}

export default function WorkOrderOverlay({ open }: Props) {
  // 3개 설비 각각 고정 hook (hooks 규칙: 조건부/반복 불가)
  const q1 = useQuery({ queryKey: ['work-order', 'CNC-001'], queryFn: () => getWorkOrderStatus('CNC-001'), enabled: open, retry: false, staleTime: 30_000, refetchInterval: open ? 30_000 : false })
  const q2 = useQuery({ queryKey: ['work-order', 'CNC-002'], queryFn: () => getWorkOrderStatus('CNC-002'), enabled: open, retry: false, staleTime: 30_000, refetchInterval: open ? 30_000 : false })
  const q3 = useQuery({ queryKey: ['work-order', 'CNC-003'], queryFn: () => getWorkOrderStatus('CNC-003'), enabled: open, retry: false, staleTime: 30_000, refetchInterval: open ? 30_000 : false })

  const rows = [
    { id: 'CNC-001', data: q1.data },
    { id: 'CNC-002', data: q2.data },
    { id: 'CNC-003', data: q3.data },
  ].flatMap(({ id, data }) => {
    const wo = data?.work_order
    if (!wo) return []
    return [{
      wo_id: wo.work_order_id,
      equipment_id: id,
      product: wo.product_type,
      priority: wo.priority,
      due_date: wo.due_date.slice(0, 10),
      status: wo.status,
    }]
  })

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '520px',
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
          style={{ color: 'var(--gray3)' }}
        >
          작업지시 현황
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr style={{ color: 'var(--gray3)' }}>
              <th className="text-left pb-1.5 font-medium">WO ID</th>
              <th className="text-left pb-1.5 font-medium">설비</th>
              <th className="text-left pb-1.5 font-medium">제품</th>
              <th className="text-left pb-1.5 font-medium">우선순위</th>
              <th className="text-left pb-1.5 font-medium">납기</th>
              <th className="text-left pb-1.5 font-medium">상태</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-2 text-center" style={{ color: 'var(--gray3)' }}>
                  작업지시 없음
                </td>
              </tr>
            ) : rows.map((wo) => (
              <tr key={wo.wo_id} style={{ color: 'var(--gray5)' }}>
                <td className="py-1" style={{ fontFamily: "'JetBrains Mono', monospace", color: 'var(--blue4)' }}>
                  {wo.wo_id}
                </td>
                <td className="py-1">{wo.equipment_id}</td>
                <td className="py-1">{wo.product}</td>
                <td className="py-1" style={{ color: PRIORITY_COLORS[wo.priority] ?? 'var(--gray4)' }}>
                  {wo.priority}
                </td>
                <td className="py-1" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                  {wo.due_date}
                </td>
                <td className="py-1" style={{ color: 'var(--gray4)' }}>{wo.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
