// ============================================================
// MonitoringCenter — 중앙 모니터링 영역 (flex, 나머지 공간)
// 센서 차트 (Recharts) + 파이프라인 상태 + 정비 이력
// ============================================================

import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getSensorTimeseries, getEquipmentAnomaly } from '@/lib/api/endpoints'
import type { SensorPoint } from '@/types'

// ── 센서 차트 ─────────────────────────────────────────────
function SensorChart({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['sensors', equipmentId],
    queryFn: () => getSensorTimeseries(equipmentId),
    refetchInterval: 5000,
    retry: false,
  })

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center rounded text-xs"
        style={{ height: '200px', background: 'var(--dg3)', color: 'var(--gray3)' }}
      >
        센서 데이터 로딩 중...
      </div>
    )
  }

  // 시계열 역순 정렬 (오래된 것 → 최신)
  const series: SensorPoint[] = [...(data?.series ?? [])].reverse()

  // timestamp를 짧게 표시 (HH:MM:SS)
  const chartData = series.map((p) => ({
    ...p,
    t: p.timestamp.slice(11, 19),
  }))

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded text-xs"
        style={{ height: '200px', background: 'var(--dg3)', color: 'var(--gray3)' }}
      >
        센서 데이터 없음
      </div>
    )
  }

  return (
    <div
      className="rounded p-3"
      style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}
    >
      <div className="text-xs font-semibold mb-3 uppercase tracking-wider" style={{ color: 'var(--gray3)' }}>
        센서 시계열 (최근 {chartData.length}개)
      </div>
      <ResponsiveContainer width="100%" height={170}>
        <LineChart data={chartData} margin={{ top: 2, right: 8, bottom: 2, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="t"
            tick={{ fontSize: 9, fill: 'var(--gray3)' }}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 9, fill: 'var(--gray3)' }} />
          <Tooltip
            contentStyle={{
              background: 'var(--dg1)',
              border: '1px solid var(--border-mid)',
              fontSize: '11px',
              color: 'var(--gray5)',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '10px', color: 'var(--gray3)' }} />
          <Line type="monotone" dataKey="x1_current_feedback" stroke="var(--blue4)" dot={false} name="X1전류" strokeWidth={1.5} />
          <Line type="monotone" dataKey="s1_current_feedback" stroke="var(--yellow5)" dot={false} name="S1전류" strokeWidth={1.5} />
          <Line type="monotone" dataKey="x1_output_power" stroke="var(--green5)" dot={false} name="X1파워" strokeWidth={1.5} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── 파이프라인 상태 ────────────────────────────────────────
function PipelineStatus({ equipmentId }: { equipmentId: string }) {
  const { data: anomaly } = useQuery({
    queryKey: ['anomaly', equipmentId],
    queryFn: () => getEquipmentAnomaly(equipmentId),
    refetchInterval: 5000,
    retry: false,
  })

  const steps = [
    { id: 'F1', label: '센서 수집', done: true },
    { id: 'F2', label: `이상탐지 ${anomaly ? (anomaly.anomaly_score * 100).toFixed(0) + '%' : ''}`, done: !!anomaly },
    { id: 'F3', label: 'IT/OT 동기화', done: !!anomaly },
    { id: 'F4', label: 'GraphRAG', done: !!anomaly },
    { id: 'F5', label: 'LLM 판단', done: !!anomaly?.is_anomaly },
  ]

  return (
    <div
      className="rounded p-3"
      style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}
    >
      <div className="text-xs font-semibold mb-2 uppercase tracking-wider" style={{ color: 'var(--gray3)' }}>
        파이프라인 상태
      </div>
      <div className="flex items-center gap-1">
        {steps.map((s, i) => (
          <div key={s.id} className="flex items-center gap-1 flex-1">
            <div
              className="flex flex-col items-center flex-1"
            >
              <div
                className="w-full text-center text-xs py-1 px-1 rounded"
                style={{
                  background: s.done ? 'rgba(45,114,210,0.2)' : 'var(--dg2)',
                  color: s.done ? 'var(--blue4)' : 'var(--gray3)',
                  border: `1px solid ${s.done ? 'rgba(45,114,210,0.4)' : 'var(--border-subtle)'}`,
                  fontSize: '10px',
                }}
              >
                <div className="font-mono font-bold">{s.id}</div>
                <div>{s.label}</div>
              </div>
            </div>
            {i < steps.length - 1 && (
              <div style={{ color: 'var(--gray3)', fontSize: '10px' }}>›</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── 메인 ──────────────────────────────────────────────────
export default function MonitoringCenter() {
  const { selectedEquipmentId } = useDashboardStore()

  return (
    <div
      className="flex-1 flex flex-col overflow-hidden"
      style={{ background: 'var(--dg2)' }}
    >
      {/* 헤더 */}
      <div
        className="flex items-center px-4 text-xs font-semibold uppercase tracking-wider flex-shrink-0"
        style={{
          height: '36px',
          borderBottom: '1px solid var(--border-subtle)',
          color: 'var(--gray3)',
        }}
      >
        {selectedEquipmentId
          ? `${selectedEquipmentId} — 모니터링`
          : '모니터링 센터'}
      </div>

      {/* 콘텐츠 */}
      <div className="flex-1 overflow-y-auto p-4">
        {!selectedEquipmentId ? (
          <div
            className="h-full flex items-center justify-center text-sm"
            style={{ color: 'var(--gray3)' }}
          >
            좌측 사이드바에서 설비를 선택하면 센서 차트와 분석 결과가 표시됩니다.
          </div>
        ) : (
          <div className="space-y-4">
            <SensorChart equipmentId={selectedEquipmentId} />
            <PipelineStatus equipmentId={selectedEquipmentId} />
          </div>
        )}
      </div>
    </div>
  )
}
