// ============================================================
// Sidebar — 설비 현황 + 이상감지 로그 + 시스템 상태
// ============================================================

import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getEquipmentSummary, getDashboardAlarms, getHealth } from '@/lib/api/endpoints'
import { useDashboardStore } from '@/stores/dashboardStore'
import type { Equipment, EquipmentStatus, AlarmEvent } from '@/types'

const STATUS_COLORS: Record<EquipmentStatus, string> = {
  normal: 'var(--green5)', warning: 'var(--yellow5)', critical: 'var(--red5)', offline: 'var(--gray2)',
}
const STATUS_LABELS: Record<EquipmentStatus, string> = {
  normal: '정상', warning: '경고', critical: '위험', offline: '오프라인',
}
const SELECTED_BG = 'var(--dg1-5)'
const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

function Section({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      margin: '6px 8px', background: 'var(--dg2)', border: '1px solid var(--border-mid)',
      borderRadius: '3px', overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.02)',
    }}>{children}</div>
  )
}

function SectionTitle({ title, right }: { title: string; right?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-3 py-2" style={{
      background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-subtle)',
    }}>
      <span style={{ fontSize: '11px', fontWeight: 600, fontFamily: sans, color: 'var(--gray4)' }}>{title}</span>
      {right}
    </div>
  )
}

function EquipmentRow({ eq, isLast }: { eq: Equipment; isLast: boolean }) {
  const { selectedEquipmentId, setSelectedEquipmentId } = useDashboardStore()
  const selected = selectedEquipmentId === eq.equipment_id
  return (
    <button
      className="w-full text-left flex items-center transition-all"
      style={{
        padding: '8px 12px', background: selected ? SELECTED_BG : 'transparent',
        borderBottom: isLast ? 'none' : '1px solid var(--border-subtle)',
        borderLeft: selected ? '3px solid var(--cyan)' : '3px solid transparent',
        borderRight: selected ? '3px solid var(--cyan)' : '3px solid transparent',
      }}
      onClick={() => setSelectedEquipmentId(eq.equipment_id)}
      onMouseEnter={(e) => { if (!selected) e.currentTarget.style.background = 'rgba(255,255,255,0.015)' }}
      onMouseLeave={(e) => { if (!selected) e.currentTarget.style.background = 'transparent' }}
    >
      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: STATUS_COLORS[eq.status], flexShrink: 0, marginRight: '10px', animation: 'pulse-dot 2.5s ease-in-out infinite' }} />
      <span style={{ fontSize: '12px', fontFamily: sans, fontWeight: 600, color: selected ? 'var(--cyan)' : 'var(--gray5)', minWidth: '68px' }}>{eq.equipment_id}</span>
      <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: STATUS_COLORS[eq.status], flex: 1 }}>{STATUS_LABELS[eq.status]}</span>
      <span style={{ fontFamily: mono, fontSize: '13px', fontWeight: 600, color: eq.anomaly_score >= 0.8 ? 'var(--red5)' : eq.anomaly_score >= 0.6 ? 'var(--yellow5)' : 'var(--gray4)', minWidth: '28px', textAlign: 'right' }}>
        {eq.anomaly_score >= 0.6 ? eq.anomaly_score.toFixed(2) : (eq.anomaly_score * 100).toFixed(0)}
      </span>
    </button>
  )
}

function AlarmRow({ alarm, isLast, isNew }: { alarm: AlarmEvent; isLast: boolean; isNew: boolean }) {
  const { selectedAlarm, setSelectedAlarm } = useDashboardStore()
  const isCritical = alarm.severity === 'critical'
  const accentColor = isCritical ? 'var(--red5)' : 'var(--yellow5)'
  const time = new Date(alarm.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const isSelected = selectedAlarm?.timestamp === alarm.timestamp && selectedAlarm?.equipment_id === alarm.equipment_id && selectedAlarm?.anomaly_score === alarm.anomaly_score

  // 배경색: 새 알람(1분) → 빨간, 선택 → 진한 네이비, 기본 → 연한 노랑
  const bg = isSelected ? 'var(--dg1-5)'
    : isNew ? 'rgba(248,113,113,0.08)'
    : 'rgba(251,191,36,0.03)'

  return (
    <button
      className="w-full text-left transition-all"
      style={{
        padding: '7px 12px', background: bg,
        borderBottom: isLast ? 'none' : '1px solid var(--border-subtle)',
        borderLeft: isSelected ? '3px solid var(--cyan)' : '3px solid transparent',
        borderRight: isSelected ? '3px solid var(--cyan)' : '3px solid transparent',
        animation: isNew && !isSelected ? 'alarm-new-pulse 2s ease-in-out' : 'none',
      }}
      onClick={() => setSelectedAlarm(alarm)}
      onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = 'rgba(255,255,255,0.03)' }}
      onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = bg }}
    >
      <div className="flex items-center">
        <span style={{ fontSize: '10px', fontWeight: 600, fontFamily: sans, color: isSelected ? 'var(--cyan)' : accentColor, minWidth: '56px', flexShrink: 0 }}>{alarm.equipment_id}</span>
        <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 400, color: 'var(--gray4)', flex: 1, textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', padding: '0 4px' }}>
          {alarm.predicted_failure_code?.replace(/_/g, ' ') ?? '—'}
        </span>
        <span style={{ fontFamily: mono, fontSize: '11px', fontWeight: 600, color: isSelected ? 'var(--cyan)' : accentColor, minWidth: '34px', textAlign: 'right', flexShrink: 0 }}>{alarm.anomaly_score.toFixed(2)}</span>
      </div>
      <div style={{ fontSize: '9px', fontFamily: sans, fontWeight: 400, color: 'var(--gray3)', marginTop: '2px' }}>{time}</div>
    </button>
  )
}

const SYSTEM_MODULES = [
  { key: 'F1', name: '센서 수집', alwaysOn: true },
  { key: 'F2', name: '이상 탐지', alwaysOn: true },
  { key: 'F3', name: 'IT/OT 동기', alwaysOn: true },
  { key: 'F4', name: 'GraphRAG', alwaysOn: false },
  { key: 'F5', name: 'LLM 판단', alwaysOn: false },
  { key: 'F6', name: '대시보드', alwaysOn: true },
]

function SystemStatusSection({ hasAnomaly }: { hasAnomaly: boolean }) {
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: getHealth, refetchInterval: 10000, retry: false })
  const infra = [
    { label: 'PostgreSQL', ok: health?.postgres ?? false },
    { label: 'Neo4j', ok: health?.neo4j ?? false },
    { label: 'Backend', ok: health?.status === 'ok' },
  ]

  return (
    <div className="flex-shrink-0" style={{ paddingBottom: '12px' }}>
      <Section>
        <SectionTitle title="시스템 상태" right={<span style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans, fontWeight: 500 }}>폴링 5초</span>} />

        {/* 인프라 연결 상태 */}
        <div className="flex items-center gap-3 px-3 py-2" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
          {infra.map((s) => (
            <div key={s.label} className="flex items-center gap-1">
              <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: s.ok ? 'var(--green5)' : 'var(--red5)', flexShrink: 0 }} />
              <span style={{ fontSize: '9px', fontFamily: sans, fontWeight: 500, color: s.ok ? 'var(--gray4)' : 'var(--red5)' }}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* 파이프라인 모듈 */}
        <div className="px-3 py-2">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px' }}>
            {SYSTEM_MODULES.map((mod) => {
              const active = mod.alwaysOn || hasAnomaly
              return (
                <div key={mod.key} className="flex items-center gap-1">
                  <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: active ? 'var(--green5)' : 'var(--gray2)', flexShrink: 0 }} />
                  <span style={{ fontSize: '9px', fontFamily: mono, fontWeight: 600, color: active ? 'var(--gray5)' : 'var(--gray2)' }}>{mod.key}</span>
                  <span style={{ fontSize: '8px', fontFamily: sans, color: active ? 'var(--gray3)' : 'var(--gray2)' }}>{mod.name}</span>
                </div>
              )
            })}
          </div>
        </div>
      </Section>
    </div>
  )
}

export default function Sidebar() {
  const { prevAlarmCount, setPrevAlarmCount } = useDashboardStore()
  const { data: equipmentList = [] } = useQuery({ queryKey: ['equipment-summary'], queryFn: getEquipmentSummary, refetchInterval: 3000, retry: false })
  const { data: alarmData } = useQuery({ queryKey: ['alarms'], queryFn: getDashboardAlarms, refetchInterval: 3000, retry: false })

  const alarms = alarmData?.alarms ?? []
  const sortedAlarms = [...alarms].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  const newAlarmCount = sortedAlarms.length - prevAlarmCount
  const prevCountRef = useRef(prevAlarmCount)

  useEffect(() => {
    if (sortedAlarms.length !== prevCountRef.current) {
      const timer = setTimeout(() => { setPrevAlarmCount(sortedAlarms.length); prevCountRef.current = sortedAlarms.length }, 60000)
      return () => clearTimeout(timer)
    }
  }, [sortedAlarms.length, setPrevAlarmCount])

  const hasAnomaly = equipmentList.some((e) => e.status === 'warning' || e.status === 'critical') || alarms.length > 0

  return (
    <div className="flex flex-col flex-shrink-0 overflow-hidden" style={{ width: 'var(--sidebar-w)', background: 'var(--dg1)' }}>
      {/* 설비 현황 */}
      <Section>
        <SectionTitle title="설비 현황" right={<span style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray4)', fontWeight: 500 }}>{equipmentList.length}대</span>} />
        <div className="flex items-center px-3 py-1" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.01)' }}>
          <span style={{ width: '16px' }} />
          <span style={{ flex: 0, minWidth: '68px', fontSize: '9px', color: 'var(--gray3)', fontFamily: sans, fontWeight: 500 }}>설비</span>
          <span style={{ flex: 1, fontSize: '9px', color: 'var(--gray3)', fontFamily: sans, fontWeight: 500 }}>상태</span>
          <span style={{ fontSize: '9px', color: 'var(--gray3)', minWidth: '28px', textAlign: 'right', fontFamily: sans, fontWeight: 500 }}>점수</span>
        </div>
        {Array.isArray(equipmentList) && equipmentList.map((eq, i) => <EquipmentRow key={eq.equipment_id} eq={eq} isLast={i === equipmentList.length - 1} />)}
      </Section>

      {/* 예측 경고 (예지보전) */}
      {(() => {
        const predWarnings = equipmentList.filter(eq => eq.anomaly_score >= 0.1 && eq.anomaly_score < 0.8)
        if (predWarnings.length === 0) return null
        return (
          <div style={{ margin: '6px 8px 0', background: 'rgba(251,191,36,0.04)', border: '1px solid rgba(251,191,36,0.12)', borderRadius: '3px', overflow: 'hidden', flexShrink: 0 }}>
            <div className="flex items-center justify-between px-3 py-1.5" style={{ borderBottom: '1px solid rgba(251,191,36,0.08)' }}>
              <span style={{ fontSize: '10px', fontWeight: 600, fontFamily: sans, color: 'var(--yellow5)' }}>예측 경고</span>
              <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--yellow5)' }}>{predWarnings.length}건</span>
            </div>
            {predWarnings.map(eq => (
              <button
                key={eq.equipment_id}
                className="w-full text-left px-3 py-1.5 transition-all"
                style={{ borderBottom: '1px solid rgba(251,191,36,0.06)' }}
                onClick={() => { useDashboardStore.getState().setPredictiveMode(true) }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(251,191,36,0.06)' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
              >
                <div className="flex items-center justify-between">
                  <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 600, color: 'var(--yellow5)' }}>{eq.equipment_id}</span>
                  <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: 'var(--yellow5)' }}>{eq.anomaly_score.toFixed(2)}</span>
                </div>
                <div style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)', marginTop: '1px' }}>
                  ↗ 아직 정상이나 상승 추세 — 사전 점검 권고
                </div>
              </button>
            ))}
          </div>
        )
      })()}

      {/* 이상감지 로그 */}
      <div style={{ margin: '6px 8px', background: 'var(--dg2)', border: '1px solid var(--border-mid)', borderRadius: '3px', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.02)', flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div className="flex items-center justify-between px-3 py-2 flex-shrink-0" style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '11px', fontWeight: 600, fontFamily: sans, color: 'var(--gray4)' }}>이상감지 로그</span>
            <div className="flex items-center gap-1">
              <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--green5)', animation: 'live-blink 1.5s ease-in-out infinite' }} />
              <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--green5)', fontWeight: 600 }}>LIVE</span>
            </div>
          </div>
          <span style={{ fontSize: '10px', fontFamily: sans, color: sortedAlarms.length > 0 ? 'var(--red5)' : 'var(--gray3)', fontWeight: 600 }}>{sortedAlarms.length}건</span>
        </div>
        {sortedAlarms.length > 0 && (
          <div className="flex items-center px-3 py-1 flex-shrink-0" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.01)' }}>
            <span style={{ fontSize: '9px', color: 'var(--gray3)', minWidth: '56px', fontFamily: sans, fontWeight: 500 }}>설비</span>
            <span style={{ fontSize: '9px', color: 'var(--gray3)', flex: 1, textAlign: 'center', fontFamily: sans, fontWeight: 500 }}>고장코드</span>
            <span style={{ fontSize: '9px', color: 'var(--gray3)', minWidth: '34px', textAlign: 'right', fontFamily: sans, fontWeight: 500 }}>점수</span>
          </div>
        )}
        <div className="overflow-y-auto flex-1">
          {sortedAlarms.length === 0 ? (
            <div className="px-3 py-4 text-center" style={{ fontSize: '11px', color: 'var(--gray2)', fontFamily: sans }}>이상감지 내역 없음</div>
          ) : sortedAlarms.map((alarm, i) => (
            <AlarmRow key={`${alarm.equipment_id}-${alarm.timestamp}-${i}`} alarm={alarm} isLast={i === sortedAlarms.length - 1} isNew={newAlarmCount > 0 && i < newAlarmCount} />
          ))}
        </div>
        {sortedAlarms.length > 0 && (
          <div className="flex items-center justify-between px-3 py-1.5 flex-shrink-0" style={{ borderTop: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.015)' }}>
            <span style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans, fontWeight: 500 }}>총 {sortedAlarms.length}건</span>
            <span style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans, fontWeight: 500 }}>최근 {sortedAlarms[0]?.timestamp ? new Date(sortedAlarms[0].timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '—'}</span>
          </div>
        )}
      </div>

      {/* 시스템 상태 */}
      <SystemStatusSection hasAnomaly={hasAnomaly} />
    </div>
  )
}
