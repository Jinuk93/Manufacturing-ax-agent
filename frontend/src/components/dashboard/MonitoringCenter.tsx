// ============================================================
// MonitoringCenter — 중앙 모니터링 영역
// 디폴트: 전체 설비 3대 동시 모니터링
// ============================================================

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { useDashboardStore } from '@/stores/dashboardStore'
import {
  getSensorTimeseries, getEquipmentAnomaly,
  getAnomalyHistory, getEquipmentSummary,
} from '@/lib/api/endpoints'
import type { SensorPoint, Equipment } from '@/types'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

const PANEL_STYLE = {
  background: 'var(--dg3)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '3px',
}

function PanelHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between px-3 py-1.5" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
      <span style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--gray3)', fontFamily: sans }}>{title}</span>
      {sub && <span style={{ fontSize: '8px', color: 'var(--gray2)', fontFamily: sans }}>{sub}</span>}
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
      <PanelHeader title="실시간 센서" sub="S1 전류" />
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
      <PanelHeader title="이상 추이" />
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

// ── 설비 카드 (전체 모니터링용) ───────────────────────────
function EquipmentMonitorCard({ eq }: { eq: Equipment }) {
  const { setSelectedEquipmentId } = useDashboardStore()
  const { data: anomaly } = useQuery({ queryKey: ['anomaly', eq.equipment_id], queryFn: () => getEquipmentAnomaly(eq.equipment_id), refetchInterval: 5000, retry: false })

  const score = anomaly?.anomaly_score ?? eq.anomaly_score
  const scoreColor = score >= 0.8 ? 'var(--red5)' : score >= 0.6 ? 'var(--yellow5)' : 'var(--cyan)'
  const statusLabel = eq.status === 'critical' ? '위험' : eq.status === 'warning' ? '경고' : '정상'
  const statusColor = eq.status === 'critical' ? 'var(--red5)' : eq.status === 'warning' ? 'var(--yellow5)' : 'var(--green5)'
  const failureCode = anomaly?.predicted_failure_code ?? eq.predicted_failure_code

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between px-3 py-2 cursor-pointer transition-all" style={{ ...PANEL_STYLE }}
        onClick={() => setSelectedEquipmentId(eq.equipment_id)}
        onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(0,212,255,0.3)' }}
        onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-subtle)' }}
      >
        <div className="flex items-center gap-2">
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: statusColor, animation: 'pulse-dot 2.5s ease-in-out infinite' }} />
          <span style={{ fontSize: '13px', fontFamily: sans, fontWeight: 700, color: 'var(--gray5)' }}>{eq.equipment_id}</span>
          <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: statusColor }}>{statusLabel}</span>
        </div>
        <div className="flex items-center gap-3">
          {failureCode && <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)', background: 'var(--dg4)', padding: '1px 6px', borderRadius: '2px' }}>{failureCode.replace(/_/g, ' ')}</span>}
          <span style={{ fontSize: '20px', fontFamily: mono, fontWeight: 700, color: scoreColor }}>{score.toFixed(2)}</span>
        </div>
      </div>
      <MiniSensorChart equipmentId={eq.equipment_id} />
      <MiniAnomalyChart equipmentId={eq.equipment_id} />
    </div>
  )
}

// ── 전체 모니터링 (디폴트) ────────────────────────────────
function OverviewMonitoring() {
  const { data: equipments, isLoading } = useQuery({ queryKey: ['equipment-summary'], queryFn: getEquipmentSummary, refetchInterval: 5000 })
  if (isLoading) return <div className="h-full flex items-center justify-center" style={{ color: 'var(--gray2)', fontSize: '11px', fontFamily: sans }}>설비 데이터 로딩 중...</div>
  const eqs = equipments ?? []

  return (
    <div style={{ animation: 'fade-in 0.3s ease-out' }}>
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Math.min(eqs.length, 3)}, 1fr)` }}>
        {eqs.map((eq) => <EquipmentMonitorCard key={eq.equipment_id} eq={eq} />)}
      </div>
    </div>
  )
}

// ── 개별 설비 상세 ────────────────────────────────────────
const SENSOR_GROUPS = [
  { id: 'X축', sensors: [{ key: 'x1_current_feedback', label: 'X1 전류', color: 'var(--yellow5)' }, { key: 'x1_output_power', label: 'X1 출력', color: 'var(--green5)' }] },
  { id: '스핀들', sensors: [{ key: 's1_current_feedback', label: 'S1 전류', color: 'var(--cyan)' }, { key: 's1_output_power', label: 'S1 속도', color: 'var(--blue4)' }] },
]
const ALL_SENSORS = [
  { key: 'x1_current_feedback', label: 'X1 전류', color: 'var(--yellow5)' },
  { key: 's1_current_feedback', label: 'S1 전류', color: 'var(--cyan)' },
  { key: 'x1_output_power', label: 'X1 출력', color: 'var(--green5)' },
  { key: 's1_output_power', label: 'S1 출력', color: '#a78bfa' },
  { key: 'y1_current_feedback', label: 'Y1 전류', color: 'var(--orange5)' },
]

function DetailSensorChart({ equipmentId }: { equipmentId: string }) {
  const [groupIdx, setGroupIdx] = useState(1)
  const [sensorIdx, setSensorIdx] = useState(0)
  const { data, isLoading } = useQuery({ queryKey: ['sensors', equipmentId], queryFn: () => getSensorTimeseries(equipmentId), refetchInterval: 5000, retry: false })
  const series: SensorPoint[] = [...(data?.series ?? [])].reverse()
  const chartData = series.map((p) => ({ ...p, t: p.timestamp.slice(11, 19) }))
  const selectedGroup = SENSOR_GROUPS[groupIdx]
  const activeSensor = ALL_SENSORS.find((s) => s.label === selectedGroup?.sensors[sensorIdx]?.label) ?? selectedGroup?.sensors[0] ?? ALL_SENSORS[0]
  const selectStyle = { background: 'var(--dg4)', border: '1px solid var(--border-mid)', color: 'var(--gray5)', fontSize: '9px', borderRadius: '2px', padding: '3px 8px', fontFamily: mono }

  return (
    <div style={PANEL_STYLE}>
      <div className="flex items-center justify-between px-3 py-1.5" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
        <span style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans }}>실시간 센서</span>
        <div className="flex items-center gap-2">
          <select value={groupIdx} onChange={(e) => { setGroupIdx(Number(e.target.value)); setSensorIdx(0) }} style={selectStyle}>{SENSOR_GROUPS.map((g, i) => <option key={g.id} value={i}>{g.id}</option>)}</select>
          <select value={sensorIdx} onChange={(e) => setSensorIdx(Number(e.target.value))} style={selectStyle}>{selectedGroup?.sensors.map((s, i) => <option key={s.key} value={i}>{s.label}</option>)}</select>
        </div>
      </div>
      {isLoading || chartData.length === 0 ? (
        <div className="flex items-center justify-center" style={{ height: '160px', color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>{isLoading ? '로딩...' : '데이터 없음'}</div>
      ) : (
        <div className="px-2 pb-2 pt-2">
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 2, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
              <XAxis dataKey="t" tick={{ fontSize: 8, fill: '#64748b' }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 8, fill: '#64748b' }} />
              <Tooltip contentStyle={{ background: 'var(--dg1)', border: '1px solid var(--border-mid)', fontSize: '9px', color: 'var(--gray5)', fontFamily: mono, borderRadius: '2px' }} />
              <Line type="monotone" dataKey={activeSensor.key} stroke={activeSensor.color} dot={false} name={activeSensor.label} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

function DetailAnomalyChart({ equipmentId }: { equipmentId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ['anomaly-history', equipmentId], queryFn: () => getAnomalyHistory(equipmentId), refetchInterval: 5000, retry: false })
  const chartData = [...(data?.history ?? [])].reverse().slice(-60).map((h) => ({ t: new Date(h.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }), score: Number(h.anomaly_score.toFixed(3)) }))

  return (
    <div style={PANEL_STYLE}>
      <div className="flex items-center justify-between px-3 py-1.5" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
        <span style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans }}>이상 점수 추이</span>
        <div className="flex items-center gap-3">
          <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--red5)' }}>— STOP 0.8</span>
          <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--yellow5)' }}>— REDUCE 0.6</span>
        </div>
      </div>
      {isLoading || chartData.length === 0 ? (
        <div className="flex items-center justify-center" style={{ height: '130px', color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>{isLoading ? '로딩...' : '데이터 없음'}</div>
      ) : (
        <div className="px-2 pb-2 pt-2">
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 2, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,200,255,0.04)" />
              <XAxis dataKey="t" tick={{ fontSize: 8, fill: '#64748b' }} interval="preserveStartEnd" />
              <YAxis domain={[0, 1]} tick={{ fontSize: 8, fill: '#64748b' }} />
              <Tooltip contentStyle={{ background: 'var(--dg1)', border: '1px solid var(--border-mid)', fontSize: '9px', color: 'var(--gray5)', fontFamily: mono, borderRadius: '2px' }} formatter={(v: number) => [v.toFixed(3), '이상점수']} />
              <ReferenceLine y={0.8} stroke="var(--red5)" strokeDasharray="4 2" strokeOpacity={0.5} />
              <ReferenceLine y={0.6} stroke="var(--yellow5)" strokeDasharray="4 2" strokeOpacity={0.5} />
              <Line type="monotone" dataKey="score" stroke="var(--cyan)" dot={false} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

function DetailKpiCards({ equipmentId }: { equipmentId: string }) {
  const { data: anomaly } = useQuery({ queryKey: ['anomaly', equipmentId], queryFn: () => getEquipmentAnomaly(equipmentId), refetchInterval: 5000, retry: false })
  if (!anomaly) return null
  const score = anomaly.anomaly_score
  const scoreColor = score >= 0.8 ? 'var(--red5)' : score >= 0.6 ? 'var(--yellow5)' : 'var(--cyan)'

  return (
    <div className="grid grid-cols-3 gap-2">
      <div style={{ ...PANEL_STYLE, padding: '10px 12px' }}>
        <div style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans, marginBottom: '4px' }}>이상 점수</div>
        <div style={{ fontFamily: mono, fontSize: '24px', fontWeight: 700, color: scoreColor, lineHeight: 1 }}>{score.toFixed(2)}</div>
      </div>
      <div style={{ ...PANEL_STYLE, padding: '10px 12px' }}>
        <div style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans, marginBottom: '4px' }}>고장코드</div>
        <div style={{ fontFamily: sans, fontSize: '12px', fontWeight: 600, color: 'var(--gray5)', lineHeight: 1.2 }}>{anomaly.predicted_failure_code?.replace(/_/g, ' ') ?? '—'}</div>
      </div>
      <div style={{ ...PANEL_STYLE, padding: '10px 12px' }}>
        <div style={{ fontSize: '9px', fontWeight: 600, color: 'var(--gray3)', fontFamily: sans, marginBottom: '4px' }}>상태</div>
        <div style={{ fontFamily: sans, fontSize: '12px', fontWeight: 600, color: scoreColor, lineHeight: 1 }}>{score >= 0.8 ? 'STOP 초과' : score >= 0.6 ? 'REDUCE 초과' : '정상 범위'}</div>
      </div>
    </div>
  )
}

// ── 메인 ──────────────────────────────────────────────────
export default function MonitoringCenter() {
  const { selectedEquipmentId, selectedAlarm } = useDashboardStore()
  const monitorId = selectedEquipmentId ?? selectedAlarm?.equipment_id ?? null

  return (
    <div className="flex-1 flex flex-col overflow-hidden" style={{ background: 'var(--dg1)', padding: '6px 4px 12px 4px' }}>
      {/* 내부 카드 */}
      <div style={{
        flex: 1, background: 'var(--dg2)', border: '1px solid var(--border-mid)',
        borderRadius: '3px', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        overflow: 'hidden', display: 'flex', flexDirection: 'column',
      }}>
        {/* 헤더 */}
        <div className="flex items-center justify-between px-4 flex-shrink-0" style={{ height: '36px', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
          <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--gray4)', fontFamily: sans }}>
            {monitorId ? `${monitorId} — 상세 모니터링` : '전체 설비 모니터링'}
          </span>
          {monitorId && (
            <button
              onClick={() => { useDashboardStore.getState().setSelectedEquipmentId(null); useDashboardStore.getState().setSelectedAlarm(null) }}
              style={{ fontSize: '10px', padding: '2px 10px', fontFamily: sans, fontWeight: 600, color: 'var(--cyan)', border: '1px solid rgba(0,212,255,0.25)', background: 'rgba(0,212,255,0.06)', cursor: 'pointer', borderRadius: '2px' }}
            >
              ← 전체 보기
            </button>
          )}
        </div>

        {/* 콘텐츠 */}
        <div className="flex-1 overflow-y-auto p-3">
          {!monitorId ? <OverviewMonitoring /> : (
            <div className="space-y-3" style={{ animation: 'fade-in 0.3s ease-out' }}>
              <DetailKpiCards equipmentId={monitorId} />
              <DetailSensorChart equipmentId={monitorId} />
              <DetailAnomalyChart equipmentId={monitorId} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
