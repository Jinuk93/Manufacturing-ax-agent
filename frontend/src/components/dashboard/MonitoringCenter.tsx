// ============================================================
// MonitoringCenter — 중앙 모니터링 영역
// 디폴트: 전체 설비 3대 동시 모니터링
// ============================================================

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend, ReferenceArea,
} from 'recharts'
import { useDashboardStore } from '@/stores/dashboardStore'
import {
  getSensorTimeseries, getEquipmentAnomaly,
  getAnomalyHistory, getEquipmentSummary,
  getActionReport, getWorkOrderStatus,
} from '@/lib/api/endpoints'
import type { SensorPoint, Equipment } from '@/types'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

const PANEL_STYLE = {
  background: 'var(--dg3)',
  border: '1px solid var(--border-mid)',
  borderRadius: '3px',
  boxShadow: '0 2px 6px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.03)',
}

function LiveDot() {
  return (
    <div className="flex items-center gap-1">
      <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--green5)', animation: 'live-blink 1.5s ease-in-out infinite' }} />
      <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--green5)', fontWeight: 600 }}>LIVE</span>
    </div>
  )
}

function PanelHeader({ title, sub, live }: { title: string; sub?: string; live?: boolean }) {
  return (
    <div className="flex items-center justify-between px-3 py-1.5" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
      <div className="flex items-center gap-2">
        <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--gray4)', fontFamily: sans }}>{title}</span>
        {sub && <span style={{ fontSize: '8px', color: 'var(--gray2)', fontFamily: sans }}>{sub}</span>}
      </div>
      {live && <div style={{ marginRight: '2px' }}><LiveDot /></div>}
    </div>
  )
}

// ── 설비별 미니 센서 차트 ─────────────────────────────────
function MiniSensorChart({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ['sensors', equipmentId], queryFn: () => getSensorTimeseries(equipmentId), refetchInterval: 5000, retry: false })
  const series: SensorPoint[] = [...(data?.series ?? [])].reverse()
  const chartData = series.map((p) => ({ ...p, t: p.timestamp.slice(11, 19) }))

  return (
    <div style={PANEL_STYLE}>
      <PanelHeader title="실시간 센서" sub="S1 전류" live />
      {isLoading || chartData.length === 0 ? (
        <div className="flex items-center justify-center" style={{ height: '100px', color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>{isLoading ? '로딩...' : '데이터 없음'}</div>
      ) : (
        <div className="px-1 pb-1 pt-1">
          <ResponsiveContainer width="100%" height={90}>
            <LineChart data={chartData} margin={{ top: 2, right: 4, bottom: 2, left: -24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
              <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#64748b' }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 7, fill: '#64748b' }} />
              <Tooltip contentStyle={{ background: 'var(--dg1)', border: '1px solid var(--border-mid)', fontSize: '9px', color: 'var(--gray5)', fontFamily: mono, borderRadius: '2px' }} />
              <Line type="monotone" dataKey="s1_current_feedback" stroke="var(--cyan)" dot={false} strokeWidth={1.2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

// ── 설비별 미니 이상추이 차트 ─────────────────────────────
function MiniAnomalyChart({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ['anomaly-history', equipmentId], queryFn: () => getAnomalyHistory(equipmentId), refetchInterval: 5000, retry: false })
  const chartData = [...(data?.history ?? [])].reverse().slice(-40).map((h) => ({
    t: new Date(h.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
    score: Number(h.anomaly_score.toFixed(3)),
  }))

  return (
    <div style={PANEL_STYLE}>
      <PanelHeader title="이상 추이" live />
      {isLoading || chartData.length === 0 ? (
        <div className="flex items-center justify-center" style={{ height: '80px', color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>{isLoading ? '로딩...' : '데이터 없음'}</div>
      ) : (
        <div className="px-1 pb-1 pt-1">
          <ResponsiveContainer width="100%" height={70}>
            <LineChart data={chartData} margin={{ top: 2, right: 4, bottom: 2, left: -24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
              <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#64748b' }} interval="preserveStartEnd" />
              <YAxis domain={[0, 1]} tick={{ fontSize: 7, fill: '#64748b' }} />
              <ReferenceLine y={0.8} stroke="var(--red5)" strokeDasharray="3 2" strokeOpacity={0.4} />
              <ReferenceLine y={0.6} stroke="var(--yellow5)" strokeDasharray="3 2" strokeOpacity={0.4} />
              <Line type="monotone" dataKey="score" stroke="var(--cyan)" dot={false} strokeWidth={1.2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

// ── 종합 상태 테이블 ──────────────────────────────────────
function SummaryTable({ eqs }: { eqs: Equipment[] }) {
  // 각 설비별 추가 데이터 조회
  const a1 = useQuery({ queryKey: ['anomaly', 'CNC-001'], queryFn: () => getEquipmentAnomaly('CNC-001'), refetchInterval: 5000, retry: false })
  const a2 = useQuery({ queryKey: ['anomaly', 'CNC-002'], queryFn: () => getEquipmentAnomaly('CNC-002'), refetchInterval: 5000, retry: false })
  const a3 = useQuery({ queryKey: ['anomaly', 'CNC-003'], queryFn: () => getEquipmentAnomaly('CNC-003'), refetchInterval: 5000, retry: false })
  const r1 = useQuery({ queryKey: ['action', 'CNC-001'], queryFn: () => getActionReport('CNC-001'), retry: false, staleTime: 30_000 })
  const r2 = useQuery({ queryKey: ['action', 'CNC-002'], queryFn: () => getActionReport('CNC-002'), retry: false, staleTime: 30_000 })
  const r3 = useQuery({ queryKey: ['action', 'CNC-003'], queryFn: () => getActionReport('CNC-003'), retry: false, staleTime: 30_000 })
  const w1 = useQuery({ queryKey: ['work-order', 'CNC-001'], queryFn: () => getWorkOrderStatus('CNC-001'), retry: false, staleTime: 60_000 })
  const w2 = useQuery({ queryKey: ['work-order', 'CNC-002'], queryFn: () => getWorkOrderStatus('CNC-002'), retry: false, staleTime: 60_000 })
  const w3 = useQuery({ queryKey: ['work-order', 'CNC-003'], queryFn: () => getWorkOrderStatus('CNC-003'), retry: false, staleTime: 60_000 })

  const anomalies = [a1.data, a2.data, a3.data]
  const actions = [r1.data, r2.data, r3.data]
  const workOrders = [w1.data, w2.data, w3.data]

  const statusColor = (s: string) => s === 'critical' ? 'var(--red5)' : s === 'warning' ? 'var(--yellow5)' : 'var(--green5)'
  const statusLabel = (s: string) => s === 'critical' ? '위험' : s === 'warning' ? '경고' : '정상'
  const recColor = (r?: string) => r === 'STOP' ? 'var(--red5)' : r === 'REDUCE' ? 'var(--yellow5)' : 'var(--cyan)'

  const cellFont = { fontSize: '10px', fontFamily: sans, fontWeight: 400 as const }
  const thStyle = { fontSize: '10px', fontWeight: 700 as const, color: 'var(--gray4)', fontFamily: sans, padding: '6px 8px', textAlign: 'left' as const, borderBottom: '1px solid var(--border-mid)' }
  const tdStyle = { ...cellFont, padding: '5px 8px', borderBottom: '1px solid var(--border-mid)', color: 'var(--gray4)', textAlign: 'center' as const, background: 'transparent' }

  const rows = [
    {
      label: '상태',
      cells: eqs.map((eq, i) => (
        <span key={i} style={{ ...cellFont, color: statusColor(eq.status) }}>
          <span style={{ display: 'inline-block', width: '5px', height: '5px', borderRadius: '50%', background: statusColor(eq.status), marginRight: '4px', animation: 'pulse-dot 2.5s ease-in-out infinite' }} />
          {statusLabel(eq.status)}
        </span>
      )),
    },
    {
      label: '이상 점수',
      cells: eqs.map((eq, i) => {
        const score = anomalies[i]?.anomaly_score ?? eq.anomaly_score
        const color = score >= 0.8 ? 'var(--red5)' : score >= 0.6 ? 'var(--yellow5)' : 'var(--gray4)'
        return <span key={i} style={{ ...cellFont, color }}>{score.toFixed(2)}</span>
      }),
    },
    {
      label: '고장코드',
      cells: eqs.map((eq, i) => {
        const fc = anomalies[i]?.predicted_failure_code ?? eq.predicted_failure_code
        return <span key={i} style={{ ...cellFont, fontSize: '10px', color: fc ? 'var(--orange5)' : 'var(--gray2)' }}>{fc?.replace(/_/g, ' ') ?? '—'}</span>
      }),
    },
    {
      label: 'LLM 판단',
      cells: eqs.map((_, i) => {
        const rec = actions[i]?.recommendation
        return <span key={i} style={{ ...cellFont, color: rec === 'STOP' ? 'var(--red5)' : rec === 'REDUCE' ? 'var(--yellow-dim)' : 'var(--gray4)' }}>{rec ?? '—'}</span>
      }),
    },
    {
      label: '확신도',
      cells: eqs.map((_, i) => {
        const conf = actions[i]?.confidence
        return <span key={i} style={{ ...cellFont, color: 'var(--gray4)' }}>{conf ? `${(conf * 100).toFixed(0)}%` : '—'}</span>
      }),
    },
    {
      label: '현재 작업',
      cells: eqs.map((_, i) => {
        const wo = workOrders[i]?.work_order
        return <span key={i} style={{ ...cellFont, fontSize: '10px', color: wo ? 'var(--cyan)' : 'var(--gray2)' }}>{wo?.work_order_id ?? '—'}</span>
      }),
    },
    {
      label: '우선순위',
      cells: eqs.map((_, i) => {
        const wo = workOrders[i]?.work_order
        const pColor = wo?.priority === 'urgent' || wo?.priority === 'critical' ? 'var(--red5)' : wo?.priority === 'normal' ? 'var(--yellow5)' : 'var(--gray3)'
        return <span key={i} style={{ ...cellFont, fontSize: '10px', color: pColor }}>{wo?.priority ?? '—'}</span>
      }),
    },
    {
      label: '최근 정비',
      cells: eqs.map((_, i) => {
        const maint = workOrders[i]?.recent_maintenance?.[0]
        const time = maint?.event_time ? new Date(maint.event_time).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) : '—'
        return <span key={i} style={{ ...cellFont, fontSize: '10px', color: 'var(--gray4)' }}>{time}</span>
      }),
    },
  ]

  return (
    <div style={PANEL_STYLE}>
      <table className="w-full" style={{ borderCollapse: 'collapse', tableLayout: 'fixed' }}>
        <thead>
          <tr>
            <th style={{ ...thStyle, width: '80px', borderRight: '1px solid var(--border-mid)' }}></th>
            {eqs.map((eq, i) => (
              <th key={eq.equipment_id} style={{ ...thStyle, textAlign: 'center', fontSize: '11px', fontWeight: 700, color: 'var(--gray5)', borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>
                {eq.equipment_id}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr key={row.label} style={{ background: rowIdx % 2 === 0 ? 'rgba(255,255,255,0.015)' : 'transparent' }}>
              <td style={{ ...tdStyle, color: 'var(--gray3)', fontWeight: 600, fontSize: '9px', textAlign: 'left', borderRight: '1px solid var(--border-mid)' }}>{row.label}</td>
              {row.cells.map((cell, i) => (
                <td key={i} style={{ ...tdStyle, textAlign: 'center', borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── 전체 모니터링 (디폴트) — 테이블 + 차트 3행 ──
function OverviewMonitoring() {
  const { data: equipments, isLoading } = useQuery({ queryKey: ['equipment-summary'], queryFn: getEquipmentSummary, refetchInterval: 5000 })
  if (isLoading) return <div className="h-full flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '11px', fontFamily: sans }}>설비 데이터 로딩 중...</div>
  const eqs = equipments ?? []
  const cols = Math.min(eqs.length, 3)

  return (
    <div className="h-full flex flex-col gap-2" style={{ animation: 'fade-in 0.3s ease-out' }}>
      {/* 1행: 종합 상태 테이블 */}
      <div className="flex-shrink-0">
        <SummaryTable eqs={eqs} />
      </div>

      {/* 2행: S1 스핀들 전류 차트 */}
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)`, flex: '1 1 35%', minHeight: 0 }}>
        {eqs.map((eq) => (
          <div key={eq.equipment_id} style={{ ...PANEL_STYLE, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <PanelHeader title={`${eq.equipment_id} S1 스핀들 전류`} live />
            <MiniSensorContent equipmentId={eq.equipment_id} />
          </div>
        ))}
      </div>

      {/* 3행: X1 서보 전류 차트 */}
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)`, flex: '1 1 35%', minHeight: 0 }}>
        {eqs.map((eq) => (
          <div key={eq.equipment_id} style={{ ...PANEL_STYLE, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <PanelHeader title={`${eq.equipment_id} X1 서보 전류`} live />
            <MiniX1Content equipmentId={eq.equipment_id} />
          </div>
        ))}
      </div>

      {/* 4행: 이상 점수 추이 */}
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)`, flex: '1 1 30%', minHeight: 0 }}>
        {eqs.map((eq) => (
          <div key={eq.equipment_id} style={{ ...PANEL_STYLE, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <PanelHeader title={`${eq.equipment_id} 이상 점수`} live />
            <MiniAnomalyContent equipmentId={eq.equipment_id} />
          </div>
        ))}
      </div>
    </div>
  )
}

// ── 위험 센서 매핑 ──
const FAULT_SENSOR_MAP: Record<string, { sensor: string; desc: string; level: string }> = {
  SPINDLE_OVERHEAT_001: { sensor: 'S1 전류', desc: '스핀들 전류 상승 — 과열 징후 감지', level: '위험' },
  TOOL_WEAR_001: { sensor: 'X1 전류', desc: 'X축 전류 하락 — 공구 마모 진행 중', level: '위험' },
  CLAMP_PRESSURE_001: { sensor: 'Y1 위치', desc: '위치 편차 증가 — 클램프 이상 감지', level: '주의' },
  COOLANT_LOW_001: { sensor: '간접 징후', desc: '복합 센서 패턴 — 냉각수 점검 필요', level: '주의' },
}

// ── 예지보전 뷰 ───────────────────────────────────────────
function PredictiveMaintenanceView() {
  const EQ_IDS = ['CNC-001', 'CNC-002', 'CNC-003']
  const a1 = useQuery({ queryKey: ['anomaly', 'CNC-001'], queryFn: () => getEquipmentAnomaly('CNC-001'), refetchInterval: 5000, retry: false })
  const a2 = useQuery({ queryKey: ['anomaly', 'CNC-002'], queryFn: () => getEquipmentAnomaly('CNC-002'), refetchInterval: 5000, retry: false })
  const a3 = useQuery({ queryKey: ['anomaly', 'CNC-003'], queryFn: () => getEquipmentAnomaly('CNC-003'), refetchInterval: 5000, retry: false })
  const r1 = useQuery({ queryKey: ['action', 'CNC-001'], queryFn: () => getActionReport('CNC-001'), retry: false, staleTime: 30_000 })
  const r2 = useQuery({ queryKey: ['action', 'CNC-002'], queryFn: () => getActionReport('CNC-002'), retry: false, staleTime: 30_000 })
  const r3 = useQuery({ queryKey: ['action', 'CNC-003'], queryFn: () => getActionReport('CNC-003'), retry: false, staleTime: 30_000 })
  const h1 = useQuery({ queryKey: ['anomaly-history', 'CNC-001'], queryFn: () => getAnomalyHistory('CNC-001'), refetchInterval: 5000, retry: false })
  const h2 = useQuery({ queryKey: ['anomaly-history', 'CNC-002'], queryFn: () => getAnomalyHistory('CNC-002'), refetchInterval: 5000, retry: false })
  const h3 = useQuery({ queryKey: ['anomaly-history', 'CNC-003'], queryFn: () => getAnomalyHistory('CNC-003'), refetchInterval: 5000, retry: false })

  const anomalies = [a1.data, a2.data, a3.data]
  const actions = [r1.data, r2.data, r3.data]
  const histories = [h1.data, h2.data, h3.data]

  const statusColor = (s: number) => s >= 0.8 ? 'var(--red5)' : s >= 0.6 ? 'var(--yellow5)' : 'var(--green5)'
  const DETAIL_CARD_PM = { ...PANEL_STYLE, boxShadow: '0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04)' }

  function calcTrend(history: { anomaly_score: number }[]) {
    if (!history || history.length < 5) return { direction: '—', label: '데이터 부족', color: 'var(--gray2)' }
    const recent = history.slice(0, 10).map(h => h.anomaly_score)
    const half = Math.floor(recent.length / 2)
    const diff = recent.slice(0, half).reduce((a, b) => a + b, 0) / half - recent.slice(half).reduce((a, b) => a + b, 0) / (recent.length - half)
    if (diff > 0.03) return { direction: '↗', label: '상승', color: 'var(--red5)' }
    if (diff < -0.03) return { direction: '↘', label: '하강', color: 'var(--green5)' }
    return { direction: '→', label: '안정', color: 'var(--gray4)' }
  }

  function calcETA(score: number, history: { anomaly_score: number }[]) {
    if (score >= 0.8) return '이미 초과'
    if (!history || history.length < 5) return '—'
    const recent = history.slice(0, 20).map(h => h.anomaly_score)
    const rate = recent.length > 1 ? (recent[0] - recent[recent.length - 1]) / recent.length : 0
    if (rate <= 0) return '도달 예상 없음'
    const min = ((0.8 - score) / rate * 5) / 60
    if (min > 480) return '48시간 이상'
    if (min > 60) return `약 ${Math.round(min / 60)}시간`
    return `약 ${Math.round(min)}분`
  }

  // 실제 API에서 forecast_score 가져오기 (없으면 fallback)
  function getForecastScore(anomalyData: { anomaly_score: number; forecast_score?: number; if_score?: number } | undefined, idx: number) {
    if (anomalyData?.forecast_score != null) return anomalyData.forecast_score
    // API에 아직 없으면 mock fallback
    const jitter = [0.08, -0.03, 0.05][idx] ?? 0
    return Math.max(0, Math.min(1, (anomalyData?.anomaly_score ?? 0) + jitter))
  }
  function getIfScore(anomalyData: { anomaly_score: number; if_score?: number } | undefined) {
    return anomalyData?.if_score ?? anomalyData?.anomaly_score ?? 0
  }

  const thStyle = { fontSize: '10px', fontWeight: 700 as const, color: 'var(--gray4)', fontFamily: sans, padding: '6px 8px', textAlign: 'left' as const, borderBottom: '1px solid var(--border-mid)' }
  const tdStyle = { fontSize: '10px', fontFamily: sans, fontWeight: 400 as const, padding: '5px 8px', borderBottom: '1px solid var(--border-mid)', color: 'var(--gray4)', textAlign: 'center' as const }

  return (
    <div className="h-full flex flex-col gap-2" style={{ animation: 'fade-in 0.3s ease-out' }}>

      {/* 예측 현황 테이블 — IF / Forecast / 융합 분리 */}
      <div className="flex-shrink-0" style={DETAIL_CARD_PM}>
        <PanelHeader title="예지보전 예측 현황" live />
        <table className="w-full" style={{ borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <thead>
            <tr>
              <th style={{ ...thStyle, width: '90px', borderRight: '1px solid var(--border-mid)' }}></th>
              {EQ_IDS.map((id, i) => <th key={id} style={{ ...thStyle, textAlign: 'center', fontWeight: 700, color: 'var(--gray5)', borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{id}</th>)}
            </tr>
          </thead>
          <tbody>
            <tr style={{ background: 'rgba(255,255,255,0.015)' }}>
              <td style={{ ...tdStyle, textAlign: 'left', fontWeight: 600, color: 'var(--gray3)', borderRight: '1px solid var(--border-mid)' }}>IF 탐지 점수</td>
              {anomalies.map((a, i) => { const s = a?.anomaly_score ?? 0; return <td key={i} style={{ ...tdStyle, color: statusColor(s), fontWeight: 500, borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{s.toFixed(2)}</td> })}
            </tr>
            <tr>
              <td style={{ ...tdStyle, textAlign: 'left', fontWeight: 600, color: 'var(--gray3)', borderRight: '1px solid var(--border-mid)' }}>CNN 예측 점수</td>
              {anomalies.map((a, i) => { const fs = getForecastScore(a, i); return <td key={i} style={{ ...tdStyle, color: 'var(--orange5)', fontWeight: 500, borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{fs.toFixed(2)}</td> })}
            </tr>
            <tr style={{ background: 'rgba(255,255,255,0.015)' }}>
              <td style={{ ...tdStyle, textAlign: 'left', fontWeight: 600, color: 'var(--gray3)', borderRight: '1px solid var(--border-mid)' }}>융합 점수</td>
              {anomalies.map((a, i) => { const s = a?.anomaly_score ?? 0; const fs = getForecastScore(a, i); const fused = 0.6 * s + 0.4 * fs; return <td key={i} style={{ ...tdStyle, color: statusColor(fused), fontWeight: 500, borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{fused.toFixed(2)}</td> })}
            </tr>
            <tr style={{ background: 'rgba(251,191,36,0.06)' }}>
              <td style={{ ...tdStyle, textAlign: 'left', fontWeight: 600, color: 'var(--gray3)', borderRight: '1px solid var(--border-mid)' }}>추세</td>
              {histories.map((h, i) => { const t = calcTrend(h?.history ?? []); return <td key={i} style={{ ...tdStyle, color: t.color, fontWeight: 500, borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{t.direction} {t.label}</td> })}
            </tr>
            <tr style={{ background: 'rgba(251,191,36,0.06)' }}>
              <td style={{ ...tdStyle, textAlign: 'left', fontWeight: 600, color: 'var(--gray3)', borderRight: '1px solid var(--border-mid)' }}>STOP 도달</td>
              {anomalies.map((a, i) => { const eta = calcETA(a?.anomaly_score ?? 0, histories[i]?.history ?? []); const c = eta === '이미 초과' ? 'var(--red5)' : eta.includes('분') ? 'var(--yellow5)' : 'var(--gray4)'; return <td key={i} style={{ ...tdStyle, color: c, fontWeight: 500, borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{eta}</td> })}
            </tr>
            <tr style={{ background: 'rgba(251,191,36,0.06)' }}>
              <td style={{ ...tdStyle, textAlign: 'left', fontWeight: 600, color: 'var(--gray3)', borderRight: '1px solid var(--border-mid)' }}>위험 센서</td>
              {anomalies.map((a, i) => { const fc = a?.predicted_failure_code; const info = fc ? FAULT_SENSOR_MAP[fc] : null; return <td key={i} style={{ ...tdStyle, color: info ? (info.level === '위험' ? 'var(--red5)' : 'var(--yellow5)') : 'var(--gray2)', fontWeight: 500, fontSize: '9px', borderLeft: i > 0 ? '1px solid var(--border-mid)' : 'none' }}>{info?.sensor ?? '—'}</td> })}
            </tr>
          </tbody>
        </table>
      </div>

      {/* IF vs Forecast 비교 차트 — 3대 나란히 */}
      <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(3, 1fr)', flex: '1 1 38%', minHeight: 0 }}>
        {EQ_IDS.map((eqId, idx) => {
          const history = histories[idx]?.history ?? []
          const reversed = [...history].reverse().slice(-60)
          const chartData = reversed.map((h) => {
            const ifScore = h.anomaly_score ?? 0
            const jitter = [0.08, -0.03, 0.05][idx] ?? 0
            const fs = (h as { forecast_score?: number }).forecast_score
            const forecastScore = fs != null ? fs : Math.max(0, Math.min(1, ifScore + jitter))
            return {
              t: new Date(h.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
              if_score: Number(ifScore.toFixed(3)),
              forecast: Number(forecastScore.toFixed(3)),
            }
          })

          // 현재 상태 판정
          const latestIf = chartData.length > 0 ? chartData[chartData.length - 1].if_score : 0
          const latestFc = chartData.length > 0 ? chartData[chartData.length - 1].forecast : 0
          const statusText = latestIf >= 0.8 ? '위험' : latestIf >= 0.6 ? '주의' : '정상'
          const statusClr = latestIf >= 0.8 ? 'var(--red5)' : latestIf >= 0.6 ? 'var(--yellow5)' : 'var(--green5)'
          const predictWarn = latestFc > latestIf + 0.05

          return (
            <div key={eqId} style={{ ...DETAIL_CARD_PM, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* 헤더: 설비명 + 상태 + 설명 */}
              <div className="flex items-center justify-between px-3 py-1.5 flex-shrink-0" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
                <div className="flex items-center gap-2">
                  <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--gray4)', fontFamily: sans }}>{eqId}</span>
                  <span style={{ fontSize: '9px', fontWeight: 600, color: statusClr, fontFamily: sans }}>{statusText}</span>
                  {predictWarn && <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--orange5)', background: 'rgba(251,146,60,0.1)', padding: '1px 4px', borderRadius: '2px', border: '1px solid rgba(251,146,60,0.15)' }}>예측 상승</span>}
                </div>
                <LiveDot />
              </div>
              {/* 범례 설명 */}
              <div className="flex items-center justify-center gap-4 py-1 flex-shrink-0" style={{ background: 'rgba(255,255,255,0.01)', borderBottom: '1px solid var(--border-subtle)' }}>
                <div className="flex items-center gap-1">
                  <div style={{ width: '16px', height: '2px', background: 'var(--cyan)' }} />
                  <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--gray3)' }}>현재 탐지 (IF)</span>
                </div>
                <div className="flex items-center gap-1">
                  <div style={{ width: '16px', height: '2px', background: 'var(--orange5)', borderTop: '1px dashed var(--orange5)' }} />
                  <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--gray3)' }}>미래 예측 (CNN)</span>
                </div>
              </div>
              {chartData.length === 0 ? (
                <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>데이터 없음</div>
              ) : (
                <div className="flex-1 px-1 pb-0" style={{ minHeight: 0 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={CHART_MARGIN}>
                      {/* 위험/주의 영역 색칠 */}
                      <ReferenceArea y1={0.8} y2={1} fill="rgba(248,113,113,0.06)" />
                      <ReferenceArea y1={0.6} y2={0.8} fill="rgba(251,191,36,0.04)" />
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
                      <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#475569' }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
                      <YAxis domain={[0, 1]} tick={{ fontSize: 7, fill: '#475569' }} tickLine={false} axisLine={false} />
                      <ReferenceLine y={0.8} stroke="var(--red5)" strokeDasharray="3 2" strokeOpacity={0.3} label={{ value: 'STOP', position: 'right', fill: '#f87171', fontSize: 7, fontFamily: sans }} />
                      <ReferenceLine y={0.6} stroke="var(--yellow5)" strokeDasharray="3 2" strokeOpacity={0.3} label={{ value: 'REDUCE', position: 'right', fill: '#fbbf24', fontSize: 7, fontFamily: sans }} />
                      <Tooltip contentStyle={CHART_TOOLTIP} />
                      <Line type="monotone" dataKey="if_score" stroke="var(--cyan)" dot={false} strokeWidth={1.5} name="현재 탐지" />
                      <Line type="monotone" dataKey="forecast" stroke="var(--orange5)" dot={false} strokeWidth={1.5} strokeDasharray="4 3" name="미래 예측" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* 위험 센서 + 예지보전 이력 — 2열, flex 확장 */}
      <div className="grid gap-2" style={{ gridTemplateColumns: '1fr 1fr', flex: '1 1 30%', minHeight: 0 }}>
        {/* 위험 센서 분석 — 표 */}
        <div style={{ ...DETAIL_CARD_PM, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader title="위험 센서 분석" />
          <div className="flex-1 overflow-y-auto">
            <table className="w-full" style={{ borderCollapse: 'collapse', tableLayout: 'fixed' }}>
              <thead>
                <tr>
                  <th style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans, padding: '5px 8px', textAlign: 'left', borderBottom: '1px solid var(--border-mid)', width: '60px' }}>설비</th>
                  <th style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans, padding: '5px 8px', textAlign: 'center', borderBottom: '1px solid var(--border-mid)' }}>수준</th>
                  <th style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans, padding: '5px 8px', textAlign: 'center', borderBottom: '1px solid var(--border-mid)' }}>센서</th>
                  <th style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans, padding: '5px 8px', textAlign: 'left', borderBottom: '1px solid var(--border-mid)' }}>설명</th>
                </tr>
              </thead>
              <tbody>
                {EQ_IDS.map((id, i) => {
                  const fc = anomalies[i]?.predicted_failure_code
                  const info = fc ? FAULT_SENSOR_MAP[fc] : null
                  const levelColor = info ? (info.level === '위험' ? 'var(--red5)' : 'var(--yellow5)') : 'var(--green5)'
                  return (
                    <tr key={id} style={{ background: info ? (info.level === '위험' ? 'rgba(248,113,113,0.04)' : 'rgba(251,191,36,0.03)') : 'transparent', borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ fontSize: '10px', fontFamily: sans, fontWeight: 600, color: 'var(--gray5)', padding: '6px 8px' }}>{id}</td>
                      <td style={{ fontSize: '9px', fontFamily: sans, fontWeight: 500, color: levelColor, padding: '6px 8px', textAlign: 'center' }}>{info?.level ?? '정상'}</td>
                      <td style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray4)', padding: '6px 8px', textAlign: 'center' }}>{info?.sensor ?? '—'}</td>
                      <td style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray4)', padding: '6px 8px', lineHeight: '1.4' }}>{info?.desc ?? '이상 없음'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* 예지보전 이력 */}
        <div style={{ ...DETAIL_CARD_PM, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader title="예지보전 이력" />
          <div className="px-3 py-2">
            {[
              { date: '3/16 14:21', eq: 'CNC-002', code: 'SPINDLE OVERHEAT', action: 'STOP → 베어링 교체', color: 'var(--red5)' },
              { date: '3/15 09:47', eq: 'CNC-003', code: 'COOLANT LOW', action: 'REDUCE → 냉각수 보충', color: 'var(--yellow5)' },
              { date: '3/14 16:33', eq: 'CNC-001', code: 'TOOL WEAR', action: '모니터링 → 엔드밀 교체', color: 'var(--green5)' },
            ].map((log, i) => (
              <div key={i} className="flex items-center gap-2 py-1.5" style={{ borderBottom: i < 2 ? '1px solid var(--border-subtle)' : 'none' }}>
                <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)', minWidth: '60px' }}>{log.date}</span>
                <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 600, color: 'var(--gray5)', minWidth: '50px' }}>{log.eq}</span>
                <span style={{ fontSize: '9px', fontFamily: sans, color: log.color, flex: 1 }}>{log.code} — {log.action}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// 공통 차트 마진 — 좌우 여백 최소화, 그래프 영역 최대화
const CHART_MARGIN = { top: 4, right: 4, bottom: 0, left: -28 }
const CHART_TOOLTIP = { background: 'var(--dg1)', border: '1px solid var(--border-mid)', fontSize: '9px', color: 'var(--gray5)', fontFamily: mono, borderRadius: '2px' }

function MiniSensorContent({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ['sensors', equipmentId], queryFn: () => getSensorTimeseries(equipmentId), refetchInterval: 5000, retry: false })
  const series: SensorPoint[] = [...(data?.series ?? [])].reverse()
  const chartData = series.map((p) => ({ ...p, t: p.timestamp.slice(11, 19) }))

  if (isLoading || chartData.length === 0) {
    return <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>{isLoading ? '로딩...' : '데이터 없음'}</div>
  }
  return (
    <div className="flex-1 px-1 pb-0" style={{ minHeight: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
          <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#475569' }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
          <YAxis tick={{ fontSize: 7, fill: '#475569' }} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={CHART_TOOLTIP} />
          <Line type="monotone" dataKey="s1_current_feedback" stroke="var(--cyan)" dot={false} strokeWidth={1.2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function MiniX1Content({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ['sensors', equipmentId], queryFn: () => getSensorTimeseries(equipmentId), refetchInterval: 5000, retry: false })
  const series: SensorPoint[] = [...(data?.series ?? [])].reverse()
  const chartData = series.map((p) => ({ ...p, t: p.timestamp.slice(11, 19) }))

  if (isLoading || chartData.length === 0) {
    return <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>{isLoading ? '로딩...' : '데이터 없음'}</div>
  }
  return (
    <div className="flex-1 px-1 pb-0" style={{ minHeight: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
          <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#475569' }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
          <YAxis tick={{ fontSize: 7, fill: '#475569' }} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={CHART_TOOLTIP} />
          <Line type="monotone" dataKey="x1_current_feedback" stroke="var(--yellow5)" dot={false} strokeWidth={1.2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function MiniAnomalyContent({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ['anomaly-history', equipmentId], queryFn: () => getAnomalyHistory(equipmentId), refetchInterval: 5000, retry: false })
  const chartData = [...(data?.history ?? [])].reverse().slice(-40).map((h) => ({
    t: new Date(h.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
    score: Number(h.anomaly_score.toFixed(3)),
  }))

  if (isLoading || chartData.length === 0) {
    return <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>{isLoading ? '로딩...' : '데이터 없음'}</div>
  }
  return (
    <div className="flex-1 px-1 pb-0" style={{ minHeight: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
          <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#475569' }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 7, fill: '#475569' }} tickLine={false} axisLine={false} />
          <ReferenceLine y={0.8} stroke="var(--red5)" strokeDasharray="3 2" strokeOpacity={0.4} />
          <ReferenceLine y={0.6} stroke="var(--yellow5)" strokeDasharray="3 2" strokeOpacity={0.4} />
          <Tooltip contentStyle={CHART_TOOLTIP} />
          <Line type="monotone" dataKey="score" stroke="var(--cyan)" dot={false} strokeWidth={1.2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── 개별 설비 상세 (Tier 1~3) ─────────────────────────────
function DetailView({ equipmentId }: { equipmentId: string }) {
  const { data: sensorData, isLoading: sensorLoading } = useQuery({ queryKey: ['sensors', equipmentId], queryFn: () => getSensorTimeseries(equipmentId), refetchInterval: 5000, retry: false })
  const { data: anomaly } = useQuery({ queryKey: ['anomaly', equipmentId], queryFn: () => getEquipmentAnomaly(equipmentId), refetchInterval: 5000, retry: false })
  const { data: historyData } = useQuery({ queryKey: ['anomaly-history', equipmentId], queryFn: () => getAnomalyHistory(equipmentId), refetchInterval: 5000, retry: false })
  const { data: action } = useQuery({ queryKey: ['action', equipmentId], queryFn: () => getActionReport(equipmentId), retry: false, staleTime: 30_000 })
  const { data: woData } = useQuery({ queryKey: ['work-order', equipmentId], queryFn: () => getWorkOrderStatus(equipmentId), retry: false, staleTime: 60_000 })

  const series: SensorPoint[] = [...(sensorData?.series ?? [])].reverse()
  const chartData = series.map((p) => ({ ...p, t: p.timestamp.slice(11, 19) }))
  const anomalyChart = [...(historyData?.history ?? [])].reverse().slice(-60).map((h) => ({ t: new Date(h.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }), score: Number(h.anomaly_score.toFixed(3)) }))

  const score = anomaly?.anomaly_score ?? 0
  const scoreColor = score >= 0.8 ? 'var(--red5)' : score >= 0.6 ? 'var(--yellow5)' : 'var(--cyan)'
  const wo = woData?.work_order
  const maint = woData?.recent_maintenance ?? []
  const rec = action?.recommendation

  const chartM = { top: 4, right: 4, bottom: 0, left: -28 }
  const DETAIL_CARD = { ...PANEL_STYLE, background: 'var(--dg3)', boxShadow: '0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04)' }

  return (
    <div className="flex flex-col gap-2 h-full" style={{ animation: 'fade-in 0.3s ease-out' }}>
      {/* KPI 카드 — 5개 (라벨 좌측 상단, 값 좌측 하단, 동일 크기) */}
      <div className="grid grid-cols-5 gap-2 flex-shrink-0">
        {[
          { label: '이상 점수', value: score.toFixed(2), color: scoreColor },
          { label: '고장코드', value: anomaly?.predicted_failure_code?.replace(/_/g, ' ') ?? '—', color: anomaly?.predicted_failure_code ? 'var(--orange5)' : 'var(--gray2)' },
          { label: 'LLM 판단', value: rec ?? '—', color: rec === 'STOP' ? 'var(--red5)' : rec === 'REDUCE' ? 'var(--yellow5)' : 'var(--gray4)' },
          { label: '현재 작업', value: wo?.work_order_id ?? '—', color: wo ? 'var(--cyan)' : 'var(--gray2)' },
          { label: '확신도', value: action?.confidence ? `${(action.confidence * 100).toFixed(0)}%` : '—', color: 'var(--gray4)' },
        ].map(kpi => (
          <div key={kpi.label} style={{ ...DETAIL_CARD, padding: '8px 10px' }}>
            <div style={{ fontSize: '9px', fontWeight: 500, color: 'var(--gray3)', fontFamily: sans, marginBottom: '4px' }}>{kpi.label}</div>
            <div style={{ fontFamily: sans, fontSize: '11px', fontWeight: 500, color: kpi.color, lineHeight: 1 }}>{kpi.value}</div>
          </div>
        ))}
      </div>

      {/* Tier 1: 센서 차트 — 2열, flex 확장 */}
      <div className="grid grid-cols-2 gap-2" style={{ flex: '1 1 40%', minHeight: 0 }}>
        <div style={{ ...DETAIL_CARD, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader title="4축 전류 비교 (A)" live />
          {sensorLoading || chartData.length === 0 ? (
            <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>로딩...</div>
          ) : (
            <div className="flex-1 px-1 pb-0" style={{ minHeight: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={chartM}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
                  <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#475569' }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
                  <YAxis tick={{ fontSize: 7, fill: '#475569' }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={CHART_TOOLTIP} />
                  <Legend layout="vertical" verticalAlign="top" align="right" wrapperStyle={{ fontSize: '8px', fontFamily: sans, color: 'var(--gray3)', lineHeight: '14px', right: '-1%', top: '40%' }} iconSize={8} />
                  <Line type="monotone" dataKey="x1_current_feedback" stroke="var(--yellow5)" dot={false} strokeWidth={1} name="X1 서보" />
                  <Line type="monotone" dataKey="y1_current_feedback" stroke="var(--orange5)" dot={false} strokeWidth={1} name="Y1 서보" />
                  <Line type="monotone" dataKey="s1_current_feedback" stroke="var(--cyan)" dot={false} strokeWidth={1} name="S1 스핀들" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div style={{ ...DETAIL_CARD, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader title="출력 파워 (%)" live />
          {sensorLoading || chartData.length === 0 ? (
            <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>로딩...</div>
          ) : (
            <div className="flex-1 px-1 pb-0" style={{ minHeight: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={chartM}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
                  <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#475569' }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
                  <YAxis tick={{ fontSize: 7, fill: '#475569' }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={CHART_TOOLTIP} />
                  <Legend layout="vertical" verticalAlign="top" align="right" wrapperStyle={{ fontSize: '8px', fontFamily: sans, color: 'var(--gray3)', lineHeight: '14px', right: '-1%', top: '40%' }} iconSize={8} />
                  <Line type="monotone" dataKey="x1_output_power" stroke="var(--green5)" dot={false} strokeWidth={1} name="X1 서보 출력" />
                  <Line type="monotone" dataKey="s1_output_power" stroke="#a78bfa" dot={false} strokeWidth={1} name="S1 스핀들 출력" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* 이상 점수 추이 — flex 확장 */}
      <div style={{ ...DETAIL_CARD, display: 'flex', flexDirection: 'column', overflow: 'hidden', flex: '1 1 30%', minHeight: 0 }}>
        <div className="flex items-center justify-between px-3 py-1.5 flex-shrink-0" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--gray4)', fontFamily: sans }}>이상 점수 추이</span>
            <LiveDot />
          </div>
          <div className="flex items-center gap-3">
            <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--red5)' }}>— STOP 0.8</span>
            <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--yellow5)' }}>— REDUCE 0.6</span>
          </div>
        </div>
        {anomalyChart.length === 0 ? (
          <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>데이터 없음</div>
        ) : (
          <div className="flex-1 px-1 pb-0" style={{ minHeight: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={anomalyChart} margin={chartM}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
                <XAxis dataKey="t" tick={{ fontSize: 7, fill: '#475569' }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 7, fill: '#475569' }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={CHART_TOOLTIP} formatter={(v: number) => [v.toFixed(3), '이상점수']} />
                <ReferenceLine y={0.8} stroke="var(--red5)" strokeDasharray="4 2" strokeOpacity={0.5} />
                <ReferenceLine y={0.6} stroke="var(--yellow5)" strokeDasharray="4 2" strokeOpacity={0.5} />
                <Line type="monotone" dataKey="score" stroke="var(--cyan)" dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Tier 2: 비즈니스 컨텍스트 — 3열, flex 확장 */}
      <div className="grid grid-cols-3 gap-2" style={{ flex: '1 1 30%', minHeight: 0 }}>
        {/* 정비 이력 */}
        <div style={{ ...DETAIL_CARD, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader title={`정비 이력 (${maint.length}건)`} sub="" />
          <div className="flex-1 overflow-y-auto">
            {maint.length === 0 ? (
              <div className="px-3 py-2" style={{ fontSize: '10px', color: 'var(--gray2)', fontFamily: sans }}>이력 없음</div>
            ) : maint.map((m, i) => {
              const isFail = m.event_type?.toLowerCase().includes('fail') || !!m.failure_code
              return (
                <div key={m.event_id} className="px-3 py-1.5" style={{ borderBottom: i < maint.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                  <div className="flex items-center justify-between">
                    <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: isFail ? 'var(--red5)' : 'var(--green5)' }}>{m.event_type}</span>
                    <span style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray3)' }}>{m.duration_min}분</span>
                  </div>
                  {m.failure_code && <div style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)' }}>{m.failure_code.replace(/_/g, ' ')}</div>}
                </div>
              )
            })}
          </div>
        </div>

        {/* 작업지시 */}
        <div style={{ ...DETAIL_CARD, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader title="작업지시" />
          <div className="flex-1 flex items-center justify-center px-3 py-2">
            {wo ? (
              <div className="space-y-1 text-center">
                <div style={{ fontSize: '11px', fontFamily: sans, color: 'var(--cyan)', fontWeight: 600 }}>{wo.work_order_id}</div>
                <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray4)' }}>{wo.product_type}</div>
                <div style={{ fontSize: '10px', fontFamily: sans, color: wo.priority === 'urgent' ? 'var(--red5)' : 'var(--gray3)' }}>{wo.priority} · {wo.status}</div>
                <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray3)' }}>납기: {wo.due_date?.slice(0, 10)}</div>
              </div>
            ) : (
              <div style={{ fontSize: '10px', color: 'var(--gray2)', fontFamily: sans }}>배정 작업 없음</div>
            )}
          </div>
        </div>

        {/* LLM 판단 이력 */}
        <div style={{ ...DETAIL_CARD, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader title="LLM 판단" />
          <div className="flex-1 flex items-center justify-center px-3 py-2">
            {action ? (
              <div className="space-y-1 text-center">
                <div style={{ fontSize: '12px', fontFamily: sans, fontWeight: 600, color: rec === 'STOP' ? 'var(--red5)' : rec === 'REDUCE' ? 'var(--yellow5)' : 'var(--gray4)' }}>{rec}</div>
                <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray4)', lineHeight: '1.5' }}>
                  {action.reasoning}
                </div>
                {action.parts_needed?.length > 0 && (
                  <div style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)', marginTop: '3px' }}>
                    필요 부품: {action.parts_needed.map(p => p.part_id).join(', ')}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '10px', color: 'var(--gray2)', fontFamily: sans }}>분석 대기 중</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── 탭 북마크 ─────────────────────────────────────────────
const TABS = [
  { id: null as string | null, label: '전체 설비' },
  { id: 'CNC-001', label: 'CNC-001' },
  { id: 'CNC-002', label: 'CNC-002' },
  { id: 'CNC-003', label: 'CNC-003' },
  { id: '__predictive__', label: '예지보전' },
]

function MonitorTab({ tab, active, onClick }: { tab: typeof TABS[0]; active: boolean; onClick: () => void }) {
  const isPredictive = tab.id === '__predictive__'
  return (
    <button
      onClick={onClick}
      style={{
        padding: '6px 16px',
        fontSize: '11px',
        fontWeight: active ? 700 : 500,
        fontFamily: sans,
        color: active
          ? (isPredictive ? '#1c2a3a' : 'var(--gray5)')
          : (isPredictive ? 'var(--yellow5)' : 'var(--gray3)'),
        background: active
          ? (isPredictive ? 'rgba(251,191,36,0.7)' : 'var(--dg2)')
          : (isPredictive ? 'rgba(251,191,36,0.08)' : 'var(--dg3)'),
        border: isPredictive && active
          ? '1px solid rgba(251,191,36,0.7)'
          : '1px solid var(--border-mid)',
        borderBottom: active ? (isPredictive ? '1px solid var(--dg2)' : '1px solid var(--dg2)') : '1px solid var(--border-mid)',
        borderRadius: '4px 4px 0 0',
        cursor: 'pointer',
        transition: 'all 0.15s',
        marginBottom: '-1px',
        position: 'relative',
        zIndex: active ? 2 : 1,
      }}
      onMouseEnter={(e) => { if (!active) e.currentTarget.style.color = 'var(--gray4)' }}
      onMouseLeave={(e) => { if (!active) e.currentTarget.style.color = 'var(--gray3)' }}
    >
      {tab.label}
    </button>
  )
}

// ── 메인 ──────────────────────────────────────────────────
export default function MonitoringCenter() {
  const { selectedEquipmentId, selectedAlarm, setSelectedEquipmentId, setSelectedAlarm, predictiveMode, setPredictiveMode } = useDashboardStore()
  const monitorId = selectedEquipmentId ?? selectedAlarm?.equipment_id ?? null

  const handleTabClick = (id: string | null) => {
    if (id === '__predictive__') {
      setPredictiveMode(true)
    } else if (id === null) {
      setSelectedEquipmentId(null)
      setSelectedAlarm(null)
    } else {
      setSelectedEquipmentId(id)
    }
  }

  const activeTabId = predictiveMode ? '__predictive__' : monitorId

  return (
    <div className="flex flex-col overflow-hidden" style={{ background: 'var(--dg1)', padding: '6px 4px 12px 4px', flex: 1, minHeight: 0 }}>
      {/* 탭 북마크 바 */}
      <div className="flex items-end flex-shrink-0" style={{ paddingLeft: '4px' }}>
        {TABS.map((tab) => (
          <MonitorTab
            key={tab.id ?? 'all'}
            tab={tab}
            active={activeTabId === tab.id}
            onClick={() => handleTabClick(tab.id)}
          />
        ))}
      </div>

      {/* 내부 카드 — 탭과 이어지는 구조 */}
      <div style={{
        flex: 1, background: 'var(--dg2)', border: '1px solid var(--border-mid)',
        borderRadius: '0 3px 3px 3px', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        overflow: 'hidden', display: 'flex', flexDirection: 'column',
      }}>
        {/* 콘텐츠 */}
        <div className="flex-1 overflow-y-auto p-3">
          {predictiveMode ? <PredictiveMaintenanceView />
            : !monitorId ? <OverviewMonitoring />
            : (
            <DetailView equipmentId={monitorId} />
          )}
        </div>
      </div>
    </div>
  )
}
