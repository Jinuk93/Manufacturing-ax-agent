// ============================================================
// WorkOrderOverlay — 작업현황 슬라이드다운 오버레이
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getWorkOrderStatus } from '@/lib/api/endpoints'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"
const PRIORITY_COLORS: Record<string, string> = { urgent: 'var(--red5)', critical: 'var(--red5)', normal: 'var(--yellow5)', low: 'var(--gray3)' }

export default function WorkOrderOverlay({ open }: { open: boolean }) {
  const q1 = useQuery({ queryKey: ['work-order', 'CNC-001'], queryFn: () => getWorkOrderStatus('CNC-001'), enabled: open, retry: false, staleTime: 30_000, refetchInterval: open ? 30_000 : false })
  const q2 = useQuery({ queryKey: ['work-order', 'CNC-002'], queryFn: () => getWorkOrderStatus('CNC-002'), enabled: open, retry: false, staleTime: 30_000, refetchInterval: open ? 30_000 : false })
  const q3 = useQuery({ queryKey: ['work-order', 'CNC-003'], queryFn: () => getWorkOrderStatus('CNC-003'), enabled: open, retry: false, staleTime: 30_000, refetchInterval: open ? 30_000 : false })

  const rows = [{ id: 'CNC-001', data: q1.data }, { id: 'CNC-002', data: q2.data }, { id: 'CNC-003', data: q3.data }].flatMap(({ id, data }) => {
    const wo = data?.work_order; if (!wo) return []
    return [{ wo_id: wo.work_order_id, equipment_id: id, product: wo.product_type, priority: wo.priority, due_date: wo.due_date.slice(0, 10), status: wo.status }]
  })

  return (
    <div style={{ position: 'absolute', top: 0, right: 0, width: '540px', overflow: 'hidden', maxHeight: open ? '220px' : '0', transition: 'max-height 0.25s ease', background: 'var(--dg2)', borderBottom: open ? '1px solid var(--border-mid)' : 'none', borderLeft: open ? '1px solid var(--border-mid)' : 'none', zIndex: 100 }}>
      <div className="p-4">
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray4)', fontFamily: sans, marginBottom: '10px' }}>작업지시 현황</div>
        <table className="w-full" style={{ fontSize: '10px' }}>
          <thead>
            <tr style={{ color: 'var(--gray3)', fontFamily: sans }}>
              <th className="text-left pb-2 font-medium" style={{ fontSize: '9px' }}>WO ID</th>
              <th className="text-left pb-2 font-medium" style={{ fontSize: '9px' }}>설비</th>
              <th className="text-left pb-2 font-medium" style={{ fontSize: '9px' }}>제품</th>
              <th className="text-left pb-2 font-medium" style={{ fontSize: '9px' }}>우선순위</th>
              <th className="text-left pb-2 font-medium" style={{ fontSize: '9px' }}>납기</th>
              <th className="text-left pb-2 font-medium" style={{ fontSize: '9px' }}>상태</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={6} className="py-3 text-center" style={{ color: 'var(--gray2)', fontFamily: sans }}>작업지시 없음</td></tr>
            ) : rows.map((wo) => (
              <tr key={wo.wo_id} style={{ fontFamily: sans, borderTop: '1px solid var(--border-subtle)' }}>
                <td className="py-1.5" style={{ color: 'var(--cyan)', fontWeight: 600, fontFamily: mono }}>{wo.wo_id}</td>
                <td className="py-1.5" style={{ color: 'var(--gray5)' }}>{wo.equipment_id}</td>
                <td className="py-1.5" style={{ color: 'var(--gray4)' }}>{wo.product}</td>
                <td className="py-1.5" style={{ color: PRIORITY_COLORS[wo.priority] ?? 'var(--gray3)', fontWeight: 600, textTransform: 'uppercase', fontSize: '9px' }}>{wo.priority}</td>
                <td className="py-1.5" style={{ color: 'var(--gray4)', fontFamily: mono }}>{wo.due_date}</td>
                <td className="py-1.5" style={{ color: 'var(--gray3)' }}>{wo.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
