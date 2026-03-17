// ============================================================
// AiDetailPanel — AI 분석 결과 패널
// 모드 1: 설비 선택 → 현재 상태 분석
// 모드 2: 알람 선택 → 해당 시점 이상감지 분석
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getActionReport, getEquipmentAnomaly, searchGraphRAG } from '@/lib/api/endpoints'
import type { ActionType, AlarmEvent } from '@/types'

const ACTION_COLORS: Record<ActionType, string> = { STOP: 'var(--red5)', REDUCE: 'var(--yellow5)', MONITOR: 'var(--cyan)' }
const ACTION_LABELS: Record<ActionType, string> = { STOP: '즉시 정지', REDUCE: '속도 감소', MONITOR: '모니터링 유지' }
const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

function ScoreBlocks({ score }: { score: number }) {
  const BLOCKS = 10; const filledCount = Math.round(score * BLOCKS)
  const getColor = (i: number) => i >= 8 ? 'var(--red5)' : i >= 6 ? 'var(--yellow5)' : 'var(--cyan)'
  return (
    <div className="flex gap-0.5 mt-2">
      {Array.from({ length: BLOCKS }, (_, i) => (
        <div key={i} style={{ flex: 1, height: '4px', borderRadius: '1px', background: i < filledCount ? getColor(i) : 'var(--dg4)', opacity: i < filledCount ? 1 : 0.2, transition: 'all 0.3s' }} />
      ))}
    </div>
  )
}

function PanelSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border-subtle)', borderRadius: '3px', overflow: 'hidden' }}>
      <div style={{ padding: '6px 12px', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
        <span style={{ fontSize: '10px', fontWeight: 600, fontFamily: sans, color: 'var(--gray4)' }}>{title}</span>
      </div>
      <div style={{ padding: '10px 12px' }}>{children}</div>
    </div>
  )
}

// ── 알람 분석 모드 ──
function AlarmAnalysisView({ alarm }: { alarm: AlarmEvent }) {
  const score = alarm.anomaly_score
  const scoreColor = score >= 0.8 ? 'var(--red5)' : score >= 0.6 ? 'var(--yellow5)' : 'var(--cyan)'
  const severity = alarm.severity === 'critical' ? '긴급' : '경고'
  const time = new Date(alarm.timestamp).toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })

  const { data: actionReport, isLoading } = useQuery({ queryKey: ['action', alarm.equipment_id], queryFn: () => getActionReport(alarm.equipment_id), retry: false, staleTime: 30_000 })
  const failureCode = alarm.predicted_failure_code ?? actionReport?.predicted_failure_code
  const { data: ragData } = useQuery({ queryKey: ['graphrag', alarm.equipment_id, failureCode], queryFn: () => searchGraphRAG(failureCode!, alarm.equipment_id), enabled: !!failureCode, staleTime: 60_000, retry: false })

  const recommendation = actionReport?.recommendation ?? 'MONITOR'
  const actionColor = ACTION_COLORS[recommendation]

  return (
    <div className="p-3 space-y-3 overflow-y-auto flex-1">
      <PanelSection title="이상감지 요약">
        <div className="flex items-center justify-between mb-3">
          <span style={{ fontSize: '12px', fontWeight: 600, fontFamily: sans, color: 'var(--gray5)' }}>{alarm.equipment_id}</span>
          <span style={{ fontSize: '10px', fontWeight: 600, fontFamily: sans, color: alarm.severity === 'critical' ? 'var(--red5)' : 'var(--yellow5)', background: alarm.severity === 'critical' ? 'rgba(248,113,113,0.08)' : 'rgba(251,191,36,0.08)', padding: '2px 8px', borderRadius: '2px', border: `1px solid ${alarm.severity === 'critical' ? 'rgba(248,113,113,0.2)' : 'rgba(251,191,36,0.2)'}` }}>{severity}</span>
        </div>
        <div className="flex items-end gap-2 mb-2">
          <span style={{ fontSize: '36px', lineHeight: 1, fontWeight: 700, fontFamily: mono, color: scoreColor }}>{score.toFixed(2)}</span>
        </div>
        <ScoreBlocks score={score} />
        <div style={{ marginTop: '8px', fontSize: '10px', color: 'var(--gray3)', fontFamily: sans }}>감지 시각: {time}</div>
        {alarm.predicted_failure_code && <div style={{ fontSize: '10px', color: 'var(--gray4)', fontFamily: sans, marginTop: '2px' }}>고장코드: <span style={{ fontWeight: 600, color: 'var(--gray5)' }}>{alarm.predicted_failure_code.replace(/_/g, ' ')}</span></div>}
      </PanelSection>

      <PanelSection title="원인 분석">
        {isLoading ? <div style={{ fontSize: '11px', color: 'var(--gray2)', fontFamily: sans }}>분석 중...</div> : (
          <div style={{ fontSize: '11px', lineHeight: '1.7', color: 'var(--gray4)', fontFamily: sans }}>{actionReport?.reasoning ?? <span style={{ color: 'var(--gray2)' }}>LLM 분석 데이터가 아직 없습니다.</span>}</div>
        )}
      </PanelSection>

      {actionReport && (
        <PanelSection title="AI 조치 제안">
          <div className="flex items-center gap-2 px-3 py-2 mb-3" style={{ background: `${actionColor}08`, border: `1px solid ${actionColor}25`, borderRadius: '2px' }}>
            {recommendation === 'STOP' && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: actionColor, animation: 'pulse-dot 2s ease-in-out infinite' }} />}
            <span style={{ fontFamily: sans, fontSize: '12px', fontWeight: 700, color: actionColor }}>{ACTION_LABELS[recommendation]}</span>
            {actionReport.confidence && <span style={{ marginLeft: 'auto', fontFamily: mono, fontSize: '10px', color: 'var(--gray3)' }}>확신도 {(actionReport.confidence * 100).toFixed(0)}%</span>}
          </div>
          {actionReport.action_steps.length > 0 && (
            <ol className="space-y-2">
              {actionReport.action_steps.map((step, i) => {
                const docMatch = step.match(/DOC-\d+/g); const partMatch = step.match(/P\d{3}/g)
                return (
                  <li key={i} className="flex gap-2" style={{ fontSize: '11px', color: 'var(--gray4)', fontFamily: sans }}>
                    <span style={{ fontFamily: mono, color: 'var(--cyan)', minWidth: '16px', fontWeight: 600, flexShrink: 0 }}>{String(i + 1).padStart(2, '0')}</span>
                    <span className="flex-1">{step}{docMatch?.map(d => <span key={d} className="ml-1 px-1" style={{ background: 'rgba(0,212,255,0.08)', color: 'var(--cyan)', fontSize: '9px', fontFamily: mono, border: '1px solid rgba(0,212,255,0.15)', borderRadius: '1px' }}>{d}</span>)}{partMatch?.map(p => <span key={p} className="ml-1 px-1" style={{ background: 'rgba(52,211,153,0.08)', color: 'var(--green5)', fontSize: '9px', fontFamily: mono, border: '1px solid rgba(52,211,153,0.15)', borderRadius: '1px' }}>{p}</span>)}</span>
                  </li>
                )
              })}
            </ol>
          )}
        </PanelSection>
      )}

      {actionReport && actionReport.parts_needed.length > 0 && (
        <PanelSection title="필요 부품">
          <div className="space-y-1">
            {actionReport.parts_needed.map(part => (
              <div key={part.part_id} className="flex items-center justify-between px-3 py-1.5" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)', borderRadius: '2px', fontSize: '10px' }}>
                <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600 }}>{part.part_id}</span>
                <span style={{ fontFamily: mono, color: 'var(--gray3)' }}>×{part.quantity}</span>
                <span style={{ fontFamily: sans, fontWeight: 600, fontSize: '10px', color: part.in_stock ? 'var(--green5)' : 'var(--red5)' }}>{part.in_stock ? '재고 있음' : '발주 필요'}</span>
              </div>
            ))}
          </div>
        </PanelSection>
      )}

      {ragData && ragData.related_documents.length > 0 && (
        <PanelSection title="온톨로지 참조 문서">
          <div className="space-y-1">
            {ragData.related_documents.slice(0, 3).map(doc => (
              <div key={doc.manual_id} className="flex items-center justify-between px-3 py-1.5" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)', borderRadius: '2px', fontSize: '10px' }}>
                <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600 }}>{doc.manual_id}</span>
                <span style={{ fontFamily: mono, color: 'var(--gray3)' }}>유사도 {doc.hybrid_score.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </PanelSection>
      )}
    </div>
  )
}

// ── 설비 분석 모드 ──
function EquipmentAnalysisView({ equipmentId }: { equipmentId: string }) {
  const { data: anomaly } = useQuery({ queryKey: ['anomaly', equipmentId], queryFn: () => getEquipmentAnomaly(equipmentId), refetchInterval: 5000, retry: false })
  const { data: actionReport, isLoading: actionLoading } = useQuery({ queryKey: ['action', equipmentId], queryFn: () => getActionReport(equipmentId), retry: false, staleTime: 30_000 })
  const failureCode = actionReport?.predicted_failure_code ?? anomaly?.predicted_failure_code
  const { data: ragData } = useQuery({ queryKey: ['graphrag', equipmentId, failureCode], queryFn: () => searchGraphRAG(failureCode!, equipmentId), enabled: !!failureCode, staleTime: 60_000, retry: false })

  const recommendation = actionReport?.recommendation ?? 'MONITOR'
  const actionColor = ACTION_COLORS[recommendation]
  const score = anomaly?.anomaly_score ?? 0
  const thresholdLabel = score >= 0.8 ? 'STOP 임계치(0.80) 초과' : score >= 0.6 ? 'REDUCE 임계치(0.60) 초과' : '정상 범위'
  const confidencePct = actionReport ? `${(actionReport.confidence * 100).toFixed(0)}%` : ''

  return (
    <div className="p-3 space-y-3 overflow-y-auto flex-1">
      <PanelSection title="이상 점수">
        <div className="flex items-end gap-2">
          <span style={{ fontSize: '40px', lineHeight: 1, fontWeight: 700, fontFamily: mono, color: actionColor }}>{score.toFixed(2)}</span>
          {confidencePct && <span style={{ fontSize: '12px', fontFamily: mono, color: 'var(--gray3)', marginBottom: '6px' }}>/ {confidencePct}</span>}
        </div>
        <ScoreBlocks score={score} />
        <div style={{ fontSize: '10px', marginTop: '6px', color: actionColor, fontFamily: sans, fontWeight: 500 }}>{thresholdLabel}</div>
        {actionReport?.predicted_failure_code && <div style={{ fontSize: '10px', marginTop: '2px', color: 'var(--gray3)', fontFamily: sans }}>예측 고장코드: {actionReport.predicted_failure_code}</div>}
      </PanelSection>

      {actionLoading ? (
        <PanelSection title="LLM 조치 판단"><div style={{ fontSize: '11px', color: 'var(--gray2)', fontFamily: sans }}>분석 중...</div></PanelSection>
      ) : actionReport && (
        <>
          <PanelSection title="LLM 조치 판단">
            <div className="flex items-center gap-2 px-3 py-2 mb-3" style={{ background: `${actionColor}08`, border: `1px solid ${actionColor}25`, borderRadius: '2px' }}>
              {recommendation === 'STOP' && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: actionColor, animation: 'pulse-dot 2s ease-in-out infinite' }} />}
              <span style={{ fontFamily: sans, fontSize: '12px', fontWeight: 700, color: actionColor }}>{ACTION_LABELS[recommendation]}</span>
            </div>
            <p style={{ fontSize: '11px', lineHeight: '1.6', color: 'var(--gray4)', fontFamily: sans }}>{actionReport.reasoning}</p>
          </PanelSection>

          {actionReport.action_steps.length > 0 && (
            <PanelSection title="조치 단계">
              <ol className="space-y-2">
                {actionReport.action_steps.map((step, i) => {
                  const docMatch = step.match(/DOC-\d+/g); const partMatch = step.match(/P\d{3}/g)
                  return (
                    <li key={i} className="flex gap-2" style={{ fontSize: '11px', color: 'var(--gray4)', fontFamily: sans }}>
                      <span style={{ fontFamily: mono, color: 'var(--cyan)', minWidth: '16px', fontWeight: 600, flexShrink: 0 }}>{String(i + 1).padStart(2, '0')}</span>
                      <span className="flex-1">{step}{docMatch?.map(d => <span key={d} className="ml-1 px-1" style={{ background: 'rgba(0,212,255,0.08)', color: 'var(--cyan)', fontSize: '9px', fontFamily: mono, border: '1px solid rgba(0,212,255,0.15)', borderRadius: '1px' }}>{d}</span>)}{partMatch?.map(p => <span key={p} className="ml-1 px-1" style={{ background: 'rgba(52,211,153,0.08)', color: 'var(--green5)', fontSize: '9px', fontFamily: mono, border: '1px solid rgba(52,211,153,0.15)', borderRadius: '1px' }}>{p}</span>)}</span>
                    </li>
                  )
                })}
              </ol>
            </PanelSection>
          )}

          {actionReport.parts_needed.length > 0 && (
            <PanelSection title="필요 부품">
              <div className="space-y-1">
                {actionReport.parts_needed.map(part => (
                  <div key={part.part_id} className="flex items-center justify-between px-3 py-1.5" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)', borderRadius: '2px', fontSize: '10px' }}>
                    <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600 }}>{part.part_id}</span>
                    <span style={{ fontFamily: mono, color: 'var(--gray3)' }}>×{part.quantity}</span>
                    <span style={{ fontFamily: sans, color: part.in_stock ? 'var(--green5)' : 'var(--red5)', fontWeight: 600, fontSize: '10px' }}>{part.in_stock ? '재고 있음' : '발주 필요'}</span>
                  </div>
                ))}
              </div>
            </PanelSection>
          )}
        </>
      )}

      {ragData && ragData.related_documents.length > 0 && (
        <PanelSection title="온톨로지 참조 문서">
          <div className="space-y-1">
            {ragData.related_documents.slice(0, 3).map(doc => (
              <div key={doc.manual_id} className="flex items-center justify-between px-3 py-1.5" style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)', borderRadius: '2px', fontSize: '10px' }}>
                <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600 }}>{doc.manual_id}</span>
                <span style={{ fontFamily: mono, color: 'var(--gray3)' }}>유사도 {doc.hybrid_score.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </PanelSection>
      )}
    </div>
  )
}

// ── 메인 ──
export default function AiDetailPanel() {
  const { selectedEquipmentId, selectedAlarm } = useDashboardStore()
  const hasSelection = !!selectedEquipmentId || !!selectedAlarm
  const headerLabel = selectedAlarm ? '이상감지 분석' : 'AI 분석 결과'
  const headerRight = selectedAlarm?.equipment_id ?? selectedEquipmentId ?? ''

  if (!hasSelection) {
    return (
      <div className="flex flex-col flex-shrink-0" style={{ width: 'var(--ai-panel-w)', background: 'var(--dg1)', borderRight: '1px solid var(--border-mid)', padding: '6px 8px 12px 0' }}>
        <div className="flex-1 flex items-center justify-center" style={{ background: 'var(--dg1-5)', border: '1px solid var(--border-mid)', borderRadius: '3px', boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }}>
          <div style={{ color: 'var(--gray2)', fontSize: '11px', fontFamily: sans }}>설비 또는 알람을 선택하세요</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-shrink-0" style={{ width: 'var(--ai-panel-w)', background: 'var(--dg1)', borderRight: '1px solid var(--border-mid)', padding: '6px 8px 12px 0' }}>
      <div style={{ flex: 1, background: 'var(--dg1-5)', border: '1px solid var(--border-mid)', borderRadius: '3px', boxShadow: '0 1px 3px rgba(0,0,0,0.2)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div className="flex items-center gap-2 px-4 py-2 flex-shrink-0" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: selectedAlarm ? 'var(--yellow5)' : 'var(--cyan)' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray4)', fontFamily: sans }}>{headerLabel}</span>
          <span style={{ marginLeft: 'auto', fontSize: '11px', fontFamily: sans, fontWeight: 600, color: selectedAlarm ? 'var(--yellow5)' : 'var(--cyan)' }}>{headerRight}</span>
        </div>
        {selectedAlarm ? <AlarmAnalysisView alarm={selectedAlarm} /> : selectedEquipmentId ? <EquipmentAnalysisView equipmentId={selectedEquipmentId} /> : null}
      </div>
    </div>
  )
}
