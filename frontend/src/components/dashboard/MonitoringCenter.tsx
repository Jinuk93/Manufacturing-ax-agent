// ============================================================
// MonitoringCenter — 중앙 모니터링 영역
// 긴급 배너 | KPI 카드 | 센서 차트 | 이상점수 추이 | 정비 이력 | 파이프라인
// ============================================================

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts'
import { useDashboardStore } from '@/stores/dashboardStore'
import {
  getSensorTimeseries, getEquipmentAnomaly,
  getActionReport, getAnomalyHistory, getWorkOrderStatus,
} from '@/lib/api/endpoints'
import type { SensorPoint } from '@/types'

// ── 긴급 배너 ─────────────────────────────────────────────
function CriticalBanner({ equipmentId }: { equipmentId: string }) {
  const { data: anomaly } = useQuery({
    queryKey: ['anomaly', equipmentId],
    queryFn: () => getEquipmentAnomaly(equipmentId),
    refetchInterval: 5000,
    retry: false,
  })
  const { data: action } = useQuery({
    queryKey: ['action', equipmentId],
    queryFn: () => getActionReport(equipmentId),
    staleTime: 30000,
    retry: false,
  })

  if (!anomaly || !anomaly.is_anomaly || action?.recommendation !== 'STOP') return null

  const detectedTime = new Date(anomaly.timestamp).toLocaleTimeString('ko-KR', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })

  return (
    <div
      className="flex items-center justify-between px-4 py-2 flex-shrink-0"
      style={{
        background: 'rgba(241,116,116,0.12)',
        borderBottom: '1px solid rgba(241,116,116,0.3)',
      }}
    >
      <div className="flex items-center gap-3">
        {/* 깜빡이는 점 */}
        <span
          style={{
            width: '8px', height: '8px', borderRadius: '50%',
            background: 'var(--red5)',
            boxShadow: '0 0 8px rgba(241,116,116,0.8)',
            animation: 'pulse-dot 1.2s ease-in-out infinite',
            flexShrink: 0,
          }}
        />
        <span
          className="font-mono font-bold text-sm"
          style={{ color: 'var(--red5)', letterSpacing: '0.05em' }}
        >
          {equipmentId} — IMMEDIATE STOP REQUIRED
        </span>
        <span style={{ fontSize: '11px', color: 'rgba(241,116,116,0.7)', letterSpacing: '0.08em' }}>
          · SCORE {anomaly.anomaly_score.toFixed(2)} ≥ STOP 0.80
        </span>
        <span style={{ fontSize: '11px', color: 'var(--gray4)' }}>
          · {anomaly.predicted_failure_code} predicted
        </span>
        <span style={{ fontSize: '11px', color: 'var(--gray4)' }}>
          · detected {detectedTime}
        </span>
      </div>
      <button
        className="text-xs font-semibold px-3 py-1 rounded"
        style={{
          border: '1px solid rgba(241,116,116,0.4)',
          color: 'var(--red5)',
          background: 'rgba(241,116,116,0.1)',
          letterSpacing: '0.08em',
        }}
      >
        ACKNOWLEDGE
      </button>
    </div>
  )
}

// ── KPI 카드 4개 ───────────────────────────────────────────
function KpiCards({ equipmentId }: { equipmentId: string }) {
  const { data: anomaly } = useQuery({
    queryKey: ['anomaly', equipmentId],
    queryFn: () => getEquipmentAnomaly(equipmentId),
    refetchInterval: 5000,
    retry: false,
  })
  const { data: action } = useQuery({
    queryKey: ['action', equipmentId],
    queryFn: () => getActionReport(equipmentId),
    staleTime: 30000,
    retry: false,
  })

  if (!anomaly) return null

  const score = anomaly.anomaly_score
  const scoreColor = score >= 0.8 ? 'var(--red5)' : score >= 0.6 ? 'var(--yellow5)' : 'var(--green5)'
  const actionLabel = action?.recommendation === 'STOP' ? 'STOP 임계치 초과' :
                      action?.recommendation === 'REDUCE' ? 'REDUCE 임계치 초과' : '정상 범위'
  const recColor = action?.recommendation === 'STOP' ? 'var(--red5)' :
                   action?.recommendation === 'REDUCE' ? 'var(--yellow5)' : 'var(--green5)'

  const cards = [
    {
      label: '이상 점수',
      value: score.toFixed(2),
      sub: actionLabel,
      color: scoreColor,
      large: true,
    },
    {
      label: '예측 고장코드',
      value: anomaly.predicted_failure_code?.replace(/_\d+$/, '') ?? '—',
      sub: anomaly.predicted_failure_code ?? '',
      color: 'var(--gray5)',
      large: false,
    },
    {
      label: 'LLM 확신도',
      value: action ? `${(action.confidence * 100).toFixed(0)}%` : '—',
      sub: 'GraphRAG 기반',
      color: recColor,
      large: true,
    },
    {
      label: '예상 다운타임',
      value: action?.estimated_downtime_min ? `${action.estimated_downtime_min}분` : '—',
      sub: '과거 유사 사례 기준',
      color: 'var(--gray5)',
      large: true,
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-3 flex-shrink-0">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded p-3"
          style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}
        >
          <div className="text-xs mb-1" style={{ color: 'var(--gray3)' }}>{c.label}</div>
          <div
            className="font-mono font-bold"
            style={{ fontSize: c.large ? '28px' : '16px', color: c.color, lineHeight: 1.1 }}
          >
            {c.value}
          </div>
          {c.sub && (
            <div className="text-xs mt-1" style={{ color: 'var(--gray3)' }}>{c.sub}</div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── 센서 차트 (드롭다운 선택) ──────────────────────────────
const SENSOR_GROUPS = [
  { id: 'X축', sensors: [
    { key: 'x1_current_feedback', label: 'X1_CurrentFeedback', color: 'var(--yellow5)' },
    { key: 'x1_output_power', key2: 'x1_output_power', label: 'X1_OutputPower', color: 'var(--green5)' },
  ]},
  { id: 'S축 (스핀들)', sensors: [
    { key: 's1_current_feedback', label: 'S1_CurrentFeedback', color: 'var(--yellow5)' },
    { key: 's1_output_power', label: 'S1_ActualVelocity', color: 'var(--blue4)' },
  ]},
]

const ALL_SENSORS = [
  { key: 'x1_current_feedback', label: 'X1_CurrentFeedback', color: 'var(--yellow5)' },
  { key: 's1_current_feedback', label: 'S1_CurrentFeedback', color: 'var(--blue4)' },
  { key: 'x1_output_power', label: 'X1_OutputPower', color: 'var(--green5)' },
  { key: 's1_output_power', label: 'S1_OutputPower', color: '#c084fc' },
  { key: 'y1_current_feedback', label: 'Y1_CurrentFeedback', color: '#f97316' },
]

function SensorChart({ equipmentId }: { equipmentId: string }) {
  const [groupIdx, setGroupIdx] = useState(1)       // 기본: S축
  const [sensorIdx, setSensorIdx] = useState(0)     // 그룹 내 첫 번째

  const { data, isLoading } = useQuery({
    queryKey: ['sensors', equipmentId],
    queryFn: () => getSensorTimeseries(equipmentId),
    refetchInterval: 5000,
    retry: false,
  })

  const series: SensorPoint[] = [...(data?.series ?? [])].reverse()
  const chartData = series.map((p) => ({ ...p, t: p.timestamp.slice(11, 19) }))

  const selectedGroup = SENSOR_GROUPS[groupIdx]
  const activeSensor = ALL_SENSORS.find((s) => s.label === selectedGroup?.sensors[sensorIdx]?.label)
    ?? ALL_SENSORS[0]

  return (
    <div className="rounded" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}>
      <div className="flex items-center justify-between px-3 py-2" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--gray3)' }}>
          실시간 센서 <span style={{ color: 'var(--gray4)', fontWeight: 400 }}>5초 폴링</span>
        </span>
        <div className="flex items-center gap-2">
          <select
            value={groupIdx}
            onChange={(e) => { setGroupIdx(Number(e.target.value)); setSensorIdx(0) }}
            style={{
              background: 'var(--dg4)', border: '1px solid var(--border-mid)',
              color: 'var(--gray5)', fontSize: '11px', borderRadius: '4px', padding: '3px 6px',
            }}
          >
            {SENSOR_GROUPS.map((g, i) => (
              <option key={g.id} value={i}>{g.id}</option>
            ))}
          </select>
          <select
            value={sensorIdx}
            onChange={(e) => setSensorIdx(Number(e.target.value))}
            style={{
              background: 'var(--dg4)', border: '1px solid var(--border-mid)',
              color: 'var(--gray5)', fontSize: '11px', borderRadius: '4px', padding: '3px 6px',
            }}
          >
            {selectedGroup?.sensors.map((s, i) => (
              <option key={s.key} value={i}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center text-xs" style={{ height: '180px', color: 'var(--gray3)' }}>
          센서 데이터 로딩 중...
        </div>
      ) : chartData.length === 0 ? (
        <div className="flex items-center justify-center text-xs" style={{ height: '180px', color: 'var(--gray3)' }}>
          센서 데이터 없음
        </div>
      ) : (
        <div className="px-2 pb-2 pt-2">
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 2, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--gray3)' }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 9, fill: 'var(--gray3)' }} />
              <Tooltip
                contentStyle={{ background: 'var(--dg1)', border: '1px solid var(--border-mid)', fontSize: '11px', color: 'var(--gray5)' }}
              />
              <Legend wrapperStyle={{ fontSize: '10px', color: 'var(--gray3)' }} />
              <Line type="monotone" dataKey={activeSensor.key} stroke={activeSensor.color} dot={false} name={activeSensor.label} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

// ── 이상 점수 추이 차트 ────────────────────────────────────
function AnomalyTrendChart({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['anomaly-history', equipmentId],
    queryFn: () => getAnomalyHistory(equipmentId),
    refetchInterval: 5000,
    retry: false,
  })

  const chartData = [...(data?.history ?? [])]
    .reverse()
    .slice(-60)
    .map((h) => ({
      t: new Date(h.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      score: Number(h.anomaly_score.toFixed(3)),
    }))

  return (
    <div className="rounded" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}>
      <div className="flex items-center justify-between px-3 py-2" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--gray3)' }}>
          이상 점수 추이 <span style={{ color: 'var(--gray4)', fontWeight: 400 }}>5초 폴링</span>
        </span>
        <div className="flex items-center gap-3">
          <span style={{ fontSize: '10px', color: 'var(--red5)' }}>--- STOP 0.8</span>
          <span style={{ fontSize: '10px', color: 'var(--yellow5)' }}>--- REDUCE 0.6</span>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center text-xs" style={{ height: '140px', color: 'var(--gray3)' }}>
          이력 로딩 중...
        </div>
      ) : chartData.length === 0 ? (
        <div className="flex items-center justify-center text-xs" style={{ height: '140px', color: 'var(--gray3)' }}>
          이력 데이터 없음
        </div>
      ) : (
        <div className="px-2 pb-2 pt-2">
          <ResponsiveContainer width="100%" height={130}>
            <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 2, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--gray3)' }} interval="preserveStartEnd" />
              <YAxis domain={[0, 1]} tick={{ fontSize: 9, fill: 'var(--gray3)' }} />
              <Tooltip
                contentStyle={{ background: 'var(--dg1)', border: '1px solid var(--border-mid)', fontSize: '11px', color: 'var(--gray5)' }}
                formatter={(v: number) => [v.toFixed(3), '이상점수']}
              />
              <ReferenceLine y={0.8} stroke="var(--red5)" strokeDasharray="4 2" strokeOpacity={0.7} />
              <ReferenceLine y={0.6} stroke="var(--yellow5)" strokeDasharray="4 2" strokeOpacity={0.7} />
              <Line type="monotone" dataKey="score" stroke="var(--red5)" dot={false} name="이상점수" strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

// ── 정비 이력 타임라인 ─────────────────────────────────────
function MaintenanceTimeline({ equipmentId }: { equipmentId: string }) {
  const { data } = useQuery({
    queryKey: ['work-order', equipmentId],
    queryFn: () => getWorkOrderStatus(equipmentId),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: false,
  })

  const records = data?.recent_maintenance ?? []

  return (
    <div className="rounded" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}>
      <div className="px-3 py-2" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--gray3)' }}>
          정비 이력 타임라인 <span style={{ color: 'var(--gray4)', fontWeight: 400 }}>60초 폴링</span>
        </span>
      </div>

      {records.length === 0 ? (
        <div className="px-3 py-3 text-xs" style={{ color: 'var(--gray3)' }}>정비 이력 없음</div>
      ) : (
        <div className="px-3 py-2 flex flex-col gap-2">
          {records.map((r) => {
            const isFail = r.event_type?.toLowerCase().includes('fail') || !!r.failure_code
            const dotColor = isFail ? 'var(--red5)' : 'var(--green5)'
            const time = r.event_time
              ? new Date(r.event_time).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
              : '—'
            return (
              <div key={r.event_id} className="flex items-start gap-2">
                <span
                  style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: dotColor, flexShrink: 0, marginTop: '3px',
                  }}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium" style={{ color: 'var(--gray5)' }}>
                      {isFail ? '수리' : '점검'} {r.failure_code ?? r.event_type}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--gray3)' }}>{time}</span>
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--gray4)' }}>
                    소요 {r.duration_min}분
                    {r.parts_used ? ` · ${r.parts_used}` : ''}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
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
    <div className="rounded p-3" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}>
      <div className="text-xs font-semibold mb-2 uppercase tracking-wider" style={{ color: 'var(--gray3)' }}>
        파이프라인 상태
      </div>
      <div className="flex items-center gap-1">
        {steps.map((s, i) => (
          <div key={s.id} className="flex items-center gap-1 flex-1">
            <div className="flex flex-col items-center flex-1">
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
    <div className="flex-1 flex flex-col overflow-hidden" style={{ background: 'var(--dg2)' }}>
      {/* 헤더 */}
      <div
        className="flex items-center px-4 text-xs font-semibold uppercase tracking-wider flex-shrink-0"
        style={{ height: '36px', borderBottom: '1px solid var(--border-subtle)', color: 'var(--gray3)' }}
      >
        {selectedEquipmentId ? `${selectedEquipmentId} — 모니터링` : '모니터링 센터'}
      </div>

      {/* 긴급 배너 (critical 시에만) */}
      {selectedEquipmentId && <CriticalBanner equipmentId={selectedEquipmentId} />}

      {/* 콘텐츠 */}
      <div className="flex-1 overflow-y-auto p-4">
        {!selectedEquipmentId ? (
          <div className="h-full flex items-center justify-center text-sm" style={{ color: 'var(--gray3)' }}>
            좌측 사이드바에서 설비를 선택하면 센서 차트와 분석 결과가 표시됩니다.
          </div>
        ) : (
          <div className="space-y-4">
            <KpiCards equipmentId={selectedEquipmentId} />
            <SensorChart equipmentId={selectedEquipmentId} />
            <AnomalyTrendChart equipmentId={selectedEquipmentId} />
            <MaintenanceTimeline equipmentId={selectedEquipmentId} />
            <PipelineStatus equipmentId={selectedEquipmentId} />
          </div>
        )}
      </div>
    </div>
  )
}
