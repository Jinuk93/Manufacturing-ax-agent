// ============================================================
// Topbar — 상단 바 + 예지보전 경고 배너
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { getHealth, getEquipmentAnomaly, getAnomalyHistory } from '@/lib/api/endpoints'
import { useDashboardStore } from '@/stores/dashboardStore'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

function NavButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '5px 14px', fontSize: '11px', fontWeight: 600, fontFamily: sans,
        color: active ? 'var(--gray5)' : 'var(--gray4)',
        background: active ? 'linear-gradient(180deg, var(--dg3) 0%, var(--dg2) 100%)' : 'var(--dg2)',
        border: active ? '1px solid var(--border-strong)' : '1px solid var(--border-mid)',
        borderRadius: '3px', cursor: 'pointer', transition: 'all 0.15s',
        boxShadow: active ? 'inset 0 1px 0 rgba(255,255,255,0.05), 0 1px 2px rgba(0,0,0,0.3)' : '0 1px 2px rgba(0,0,0,0.2)',
      }}
      onMouseEnter={(e) => { if (!active) { e.currentTarget.style.borderColor = 'var(--border-strong)'; e.currentTarget.style.color = 'var(--gray5)' } }}
      onMouseLeave={(e) => { if (!active) { e.currentTarget.style.borderColor = 'var(--border-mid)'; e.currentTarget.style.color = 'var(--gray4)' } }}
    >
      {label}
    </button>
  )
}

// 예지보전 경고 계산
function usePredictiveWarnings() {
  const EQ_IDS = ['CNC-001', 'CNC-002', 'CNC-003']
  const a1 = useQuery({ queryKey: ['anomaly', 'CNC-001'], queryFn: () => getEquipmentAnomaly('CNC-001'), refetchInterval: 5000, retry: false })
  const a2 = useQuery({ queryKey: ['anomaly', 'CNC-002'], queryFn: () => getEquipmentAnomaly('CNC-002'), refetchInterval: 5000, retry: false })
  const a3 = useQuery({ queryKey: ['anomaly', 'CNC-003'], queryFn: () => getEquipmentAnomaly('CNC-003'), refetchInterval: 5000, retry: false })
  const h1 = useQuery({ queryKey: ['anomaly-history', 'CNC-001'], queryFn: () => getAnomalyHistory('CNC-001'), refetchInterval: 5000, retry: false })
  const h2 = useQuery({ queryKey: ['anomaly-history', 'CNC-002'], queryFn: () => getAnomalyHistory('CNC-002'), refetchInterval: 5000, retry: false })
  const h3 = useQuery({ queryKey: ['anomaly-history', 'CNC-003'], queryFn: () => getAnomalyHistory('CNC-003'), refetchInterval: 5000, retry: false })

  const anomalies = [a1.data, a2.data, a3.data]
  const histories = [h1.data, h2.data, h3.data]

  const warnings: { eq: string; type: 'stop_imminent' | 'trend_up' | 'forecast_high'; msg: string; color: string }[] = []

  EQ_IDS.forEach((id, i) => {
    const score = anomalies[i]?.anomaly_score ?? 0
    const fc = anomalies[i]?.predicted_failure_code
    const history = histories[i]?.history ?? []

    // 이미 STOP 초과 → 이건 "이상 감지"이므로 예지보전 경고에서 제외
    if (score >= 0.8) return

    // 예지보전: 아직 정상이지만 상승 추세로 STOP 도달 예상
    if (history.length >= 5 && score >= 0.1) {
      const recent = history.slice(0, 20).map(h => h.anomaly_score)
      const rate = recent.length > 1 ? (recent[0] - recent[recent.length - 1]) / recent.length : 0
      if (rate > 0) {
        const minToStop = ((0.8 - score) / rate * 5) / 60
        if (minToStop <= 120) {
          warnings.push({ eq: id, type: 'trend_up', msg: `${id} 약 ${Math.round(minToStop)}분 후 STOP 도달 예상 — 사전 점검 권고 (현재 ${score.toFixed(2)})`, color: 'var(--yellow5)' })
        }
      }
    }

    // forecast_score가 IF보다 높으면 → 아직 정상이지만 곧 이상해질 징후
    const forecastScore = (anomalies[i] as { forecast_score?: number } | undefined)?.forecast_score
    if (forecastScore != null && forecastScore > score + 0.1 && score < 0.8) {
      warnings.push({ eq: id, type: 'forecast_high', msg: `${id} CNN 예측 상승 (현재 ${score.toFixed(2)} → 예측 ${forecastScore.toFixed(2)}) — 고장 징후 사전 감지`, color: 'var(--orange5)' })
    }
  })

  return warnings
}

export default function Topbar() {
  const { activeOverlay, toggleOverlay, selectedEquipmentId, selectedAlarm, setSelectedEquipmentId, setSelectedAlarm, setPredictiveMode } = useDashboardStore()

  const { data: health, dataUpdatedAt } = useQuery({ queryKey: ['health'], queryFn: getHealth, refetchInterval: 10000, retry: false })
  const warnings = usePredictiveWarnings()

  const isOverview = selectedEquipmentId === null && selectedAlarm === null
  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '--:--:--'

  // 가장 심각한 경고 1개
  const topWarning = warnings.find(w => w.type === 'stop_imminent') ?? warnings.find(w => w.type === 'trend_up') ?? warnings[0] ?? null

  return (
    <div className="relative z-10">
      <div className="flex items-center gap-4 px-5" style={{
        height: 'var(--topbar-h)',
        background: 'linear-gradient(180deg, var(--dg1) 0%, rgba(10,16,28,0.95) 100%)',
        borderBottom: '1px solid var(--border-mid)',
      }}>
        {/* 로고 */}
        <div className="flex items-center gap-0 mr-2 select-none">
          <span style={{ fontFamily: sans, fontWeight: 800, fontSize: '13px', letterSpacing: '0.18em', color: 'var(--gray5)', textTransform: 'uppercase' }}>MANUFACTURING</span>
          <span style={{ fontFamily: mono, fontWeight: 700, fontSize: '13px', letterSpacing: '0.08em', color: 'var(--cyan)', marginLeft: '6px', textShadow: '0 0 12px rgba(0,212,255,0.4)' }}>AX</span>
        </div>

        <span style={{ width: '1px', height: '20px', background: 'var(--border-strong)' }} />

        {/* 좌측 버튼 그룹 */}
        <div className="flex items-center gap-2">
          <NavButton label="작업현황" active={activeOverlay === 'work'} onClick={() => toggleOverlay('work')} />
          <NavButton label="재고현황" active={activeOverlay === 'inventory'} onClick={() => toggleOverlay('inventory')} />
        </div>

        {/* 예지보전 경고 배너 */}
        {topWarning && (
          <button
            onClick={() => setPredictiveMode(true)}
            className="flex items-center gap-2 px-3 py-1 transition-all"
            style={{
              background: topWarning.type === 'stop_imminent' ? 'rgba(248,113,113,0.08)' : 'rgba(251,191,36,0.06)',
              border: `1px solid ${topWarning.type === 'stop_imminent' ? 'rgba(248,113,113,0.2)' : 'rgba(251,191,36,0.15)'}`,
              borderRadius: '3px', cursor: 'pointer',
              maxWidth: '400px',
            }}
          >
            <div style={{
              width: '5px', height: '5px', borderRadius: '50%',
              background: topWarning.color,
              animation: 'pulse-dot 1.5s ease-in-out infinite',
              flexShrink: 0,
            }} />
            <span style={{
              fontSize: '10px', fontFamily: sans, fontWeight: 500,
              color: topWarning.color,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {topWarning.msg}
            </span>
            {warnings.length > 1 && (
              <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)', flexShrink: 0 }}>+{warnings.length - 1}</span>
            )}
          </button>
        )}

        {/* 우측 — LIVE + 시간 */}
        <div className="flex items-center gap-3 ml-auto">
          <div className="flex items-center gap-1.5">
            <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--green5)', animation: 'live-blink 1.5s ease-in-out infinite' }} />
            <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--green5)', fontWeight: 600 }}>LIVE</span>
          </div>
          <span style={{ width: '1px', height: '16px', background: 'var(--border-mid)' }} />
          <span style={{ fontFamily: mono, fontSize: '10px', color: 'var(--gray3)' }}>{lastUpdated}</span>
        </div>
      </div>
    </div>
  )
}
