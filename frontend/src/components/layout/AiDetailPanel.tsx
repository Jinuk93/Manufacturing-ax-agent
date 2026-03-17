// ============================================================
// AiDetailPanel — AI 분석 결과 패널
// 모드 1: 설비 선택 → 현재 상태 분석
// 모드 2: 알람 선택 → 해당 시점 이상감지 분석
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getActionReport, getEquipmentAnomaly, searchGraphRAG, getSensorTimeseries, getWorkOrderStatus } from '@/lib/api/endpoints'
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
  const { data: ragData } = useQuery({ queryKey: ['graphrag', alarm.equipment_id, failureCode], queryFn: () => searchGraphRAG(failureCode!, alarm.equipment_id), enabled: !!failureCode, staleTime: 60_000, retry: 1 })

  const recommendation = actionReport?.recommendation ?? 'MONITOR'
  const actionColor = ACTION_COLORS[recommendation]

  const PART_NAMES: Record<string, string> = {
    P001: 'Endmill 6mm Carbide (엔드밀 초경 공구)',
    P002: 'Spindle Bearing Set (스핀들 베어링 세트)',
    P003: 'Coolant 수용성 20L (절삭유)',
    P004: 'Clamp Bolt Set (클램프 볼트 세트)',
    P005: 'Air Filter (에어 필터)',
  }
  const DOC_TITLES: Record<string, string> = {
    'DOC-001': '엔드밀 공구 교체 절차서 — 마모 시 교체 표준 절차',
    'DOC-002': '공구 마모 점검 체크리스트 — 센서 5항목 + 물리 3항목',
    'DOC-003': '공구 마모 트러블슈팅 — 증상별 원인 분석 및 조치',
    'DOC-004': '스핀들 베어링 교체 절차서 — 과열 시 교체 표준 절차',
    'DOC-005': '스핀들 과열 점검 체크리스트 — 온도/전류 기준 점검',
    'DOC-006': '스핀들 과열 트러블슈팅 — 과열 원인 분석 및 냉각 조치',
    'DOC-007': '클램프 볼트 교체 절차서 — 압력 저하 시 교체',
    'DOC-008': '클램프 압력 이상 점검 체크리스트',
    'DOC-009': '클램프 압력 이상 트러블슈팅',
    'DOC-010': '냉각수 보충 및 필터 교체 절차서',
    'DOC-011': '냉각수 이상 점검 체크리스트',
    'DOC-012': '냉각수 이상 트러블슈팅 가이드',
  }
  const cardBg = { background: 'var(--dg3)', border: '1px solid var(--border-mid)', borderRadius: '3px', boxShadow: '0 1px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.03)' }

  return (
    <div className="p-3 overflow-y-auto flex-1">
      {/* 하나의 큰 카드 */}
      <div style={{ ...cardBg, padding: '10px' }}>
        <div className="space-y-3">

          {/* 이상감지 요약 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span style={{ fontSize: '11px', fontWeight: 700, fontFamily: sans, color: 'var(--gray5)' }}>이상감지 요약</span>
              <span style={{ fontSize: '12px', fontWeight: 600, fontFamily: sans, color: 'var(--gray5)' }}>{alarm.equipment_id}</span>
              <span style={{ fontSize: '10px', fontWeight: 600, fontFamily: sans, color: alarm.severity === 'critical' ? 'var(--red5)' : 'var(--yellow5)', background: alarm.severity === 'critical' ? 'rgba(248,113,113,0.08)' : 'rgba(251,191,36,0.08)', padding: '2px 8px', borderRadius: '2px', border: `1px solid ${alarm.severity === 'critical' ? 'rgba(248,113,113,0.2)' : 'rgba(251,191,36,0.2)'}` }}>{severity}</span>
            </div>
            <span style={{ fontSize: '14px', fontWeight: 500, fontFamily: sans, color: scoreColor }}>{score.toFixed(2)}</span>
          </div>

          <ScoreBlocks score={score} />

          <div className="flex items-center justify-between">
            <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--cyan)', fontWeight: 500 }}>감지 시각: {time}</div>
            {alarm.predicted_failure_code && (
              <div style={{ fontSize: '10px', fontFamily: sans, fontWeight: 600, color: 'var(--green5)' }}>{alarm.predicted_failure_code.replace(/_/g, ' ')}</div>
            )}
          </div>

          {/* 구분선 */}
          <div style={{ height: '1px', background: 'var(--border-mid)' }} />

          {/* 원인 분석 */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--gray5)', fontFamily: sans, marginBottom: '6px' }}>원인 분석</div>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)', borderRadius: '3px', padding: '8px 10px' }}>
              {isLoading ? <div style={{ fontSize: '11px', color: 'var(--gray2)', fontFamily: sans }}>분석 중...</div> : (
                <div style={{ fontSize: '11px', lineHeight: '1.7', color: 'var(--gray5)', fontFamily: sans, fontWeight: 400 }}>{actionReport?.reasoning ?? <span style={{ color: 'var(--gray2)' }}>LLM 분석 데이터가 아직 없습니다.</span>}</div>
              )}
            </div>
          </div>

          {/* 구분선 */}
          <div style={{ height: '1px', background: 'var(--border-mid)' }} />

          {/* AI 조치 제안 */}
          {actionReport && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--gray5)', fontFamily: sans }}>AI 조치 제안</span>
                <div className="flex items-center gap-2">
                  {recommendation === 'STOP' && <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: actionColor, animation: 'pulse-dot 2s ease-in-out infinite' }} />}
                  <span style={{ fontFamily: sans, fontSize: '11px', fontWeight: 600, color: actionColor }}>{ACTION_LABELS[recommendation]}</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: 'var(--gray5)' }}>확신도</span>
                <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: 'var(--gray5)' }}>{actionReport.confidence ? `${(actionReport.confidence * 100).toFixed(0)}%` : '—'}</span>
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
            </div>
          )}

          {/* 필요 부품 */}
          {actionReport && actionReport.parts_needed.length > 0 && (
            <>
              <div style={{ height: '1px', background: 'var(--border-mid)' }} />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--gray5)', fontFamily: sans, marginBottom: '6px' }}>필요 부품</div>
                <div className="space-y-1.5">
                  {actionReport.parts_needed.map(part => (
                    <div key={part.part_id} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)', borderRadius: '2px', padding: '6px 10px' }}>
                      <div className="flex items-center justify-between mb-1">
                        <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600, fontSize: '10px' }}>{part.part_id}</span>
                        <div className="flex items-center gap-2">
                          <span style={{ fontFamily: sans, color: 'var(--gray3)', fontSize: '10px' }}>×{part.quantity}</span>
                          <span style={{ fontFamily: sans, fontWeight: 500, fontSize: '10px', color: part.in_stock ? 'var(--green5)' : 'var(--red5)' }}>{part.in_stock ? '재고 있음' : '발주 필요'}</span>
                        </div>
                      </div>
                      <div style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray4)' }}>{PART_NAMES[part.part_id] ?? part.part_id}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* 온톨로지 참조 문서 */}
          {ragData && ragData.related_documents.length > 0 && (
            <>
              <div style={{ height: '1px', background: 'var(--border-mid)' }} />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--gray5)', fontFamily: sans, marginBottom: '6px' }}>온톨로지 참조 문서</div>
                <div className="space-y-1.5">
                  {ragData.related_documents.slice(0, 3).map(doc => (
                    <div key={doc.manual_id} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)', borderRadius: '2px', padding: '6px 10px' }}>
                      <div className="flex items-center justify-between mb-1">
                        <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600, fontSize: '10px' }}>{doc.manual_id}</span>
                        <span style={{ fontFamily: sans, color: 'var(--gray3)', fontSize: '9px' }}>유사도 {doc.hybrid_score.toFixed(2)}</span>
                      </div>
                      <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray4)', lineHeight: '1.4' }}>{DOC_TITLES[doc.manual_id] ?? doc.title ?? '문서'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ── 설비 분석 모드 ──
function EquipmentAnalysisView({ equipmentId }: { equipmentId: string }) {
  const { data: anomaly } = useQuery({ queryKey: ['anomaly', equipmentId], queryFn: () => getEquipmentAnomaly(equipmentId), refetchInterval: 5000, retry: false })
  const { data: actionReport, isLoading: actionLoading } = useQuery({ queryKey: ['action', equipmentId], queryFn: () => getActionReport(equipmentId), retry: false, staleTime: 30_000 })
  const failureCode = actionReport?.predicted_failure_code ?? anomaly?.predicted_failure_code
  const { data: ragData } = useQuery({ queryKey: ['graphrag', equipmentId, failureCode], queryFn: () => searchGraphRAG(failureCode!, equipmentId), enabled: !!failureCode, staleTime: 60_000, retry: 1 })

  const recommendation = actionReport?.recommendation ?? 'MONITOR'
  const actionColor = ACTION_COLORS[recommendation]
  const score = anomaly?.anomaly_score ?? 0
  const thresholdLabel = score >= 0.8 ? 'STOP 임계치(0.80) 초과' : score >= 0.6 ? 'REDUCE 임계치(0.60) 초과' : '정상 범위'
  const confidencePct = actionReport ? `${(actionReport.confidence * 100).toFixed(0)}%` : ''

  // 문서 제목 매핑
  const DOC_TITLES: Record<string, string> = {
    'DOC-001': '엔드밀 공구 교체 절차서',
    'DOC-002': '공구 마모 점검 체크리스트',
    'DOC-003': '공구 마모 트러블슈팅 가이드',
    'DOC-004': '스핀들 베어링 교체 절차서',
    'DOC-005': '스핀들 과열 점검 체크리스트',
    'DOC-006': '스핀들 과열 트러블슈팅 가이드',
    'DOC-007': '클램프 볼트 교체 절차서',
    'DOC-008': '클램프 압력 이상 점검 체크리스트',
    'DOC-009': '클램프 압력 이상 트러블슈팅 가이드',
    'DOC-010': '냉각수 보충 및 필터 교체 절차서',
    'DOC-011': '냉각수 이상 점검 체크리스트',
    'DOC-012': '냉각수 이상 트러블슈팅 가이드',
  }

  const cardBg = { background: 'var(--dg3)', border: '1px solid var(--border-mid)', borderRadius: '3px', boxShadow: '0 1px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.03)' }

  return (
    <div className="p-3 space-y-3 overflow-y-auto flex-1">
      {/* 하나의 큰 카드로 묶기 */}
      <div style={{ ...cardBg, padding: '10px' }}>
        <div className="space-y-3">

          {/* 이상 점수 — 컴팩트 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray5)', fontFamily: sans }}>이상 점수</span>
              <span style={{ fontSize: '14px', fontWeight: 500, fontFamily: sans, color: actionColor }}>{score.toFixed(2)}</span>
              {confidencePct && <span style={{ fontSize: '14px', fontFamily: sans, fontWeight: 500, color: 'var(--gray3)' }}>/ {confidencePct}</span>}
            </div>
            <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: actionColor }}>{thresholdLabel}</span>
          </div>

          {/* 예측 고장코드 */}
          {failureCode && (
            <div style={{ fontSize: '11px', fontFamily: sans, fontWeight: 600, color: 'var(--green5)' }}>
              예측 고장코드: {failureCode.replace(/_/g, ' ')}
            </div>
          )}

          <ScoreBlocks score={score} />

          {/* 구분선 */}
          <div style={{ height: '1px', background: 'var(--border-mid)' }} />

          {/* LLM 조치 판단 */}
          {actionLoading ? (
            <div style={{ fontSize: '11px', color: 'var(--gray2)', fontFamily: sans }}>분석 중...</div>
          ) : actionReport && (
            <>
              <div className="flex items-center justify-between">
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray5)', fontFamily: sans }}>LLM 조치 판단</span>
                <div className="flex items-center gap-2">
                  {recommendation === 'STOP' && <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: actionColor, animation: 'pulse-dot 2s ease-in-out infinite' }} />}
                  <span style={{ fontFamily: sans, fontSize: '11px', fontWeight: 600, color: actionColor }}>{ACTION_LABELS[recommendation]}</span>
                </div>
              </div>
              <p style={{ fontSize: '11px', lineHeight: '1.6', color: 'var(--gray4)', fontFamily: sans }}>{actionReport.reasoning}</p>

              {/* 구분선 */}
              <div style={{ height: '1px', background: 'var(--border-mid)' }} />

              {/* 조치 단계 */}
              {actionReport.action_steps.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray5)', fontFamily: sans, marginBottom: '6px' }}>조치 단계</div>
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
                </div>
              )}

              {/* 필요 부품 */}
              {actionReport.parts_needed.length > 0 && (
                <>
                  <div style={{ height: '1px', background: 'var(--border-mid)' }} />
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray5)', fontFamily: sans, marginBottom: '6px' }}>필요 부품</div>
                    <div className="space-y-1">
                      {actionReport.parts_needed.map(part => (
                        <div key={part.part_id} className="flex items-center justify-between px-3 py-1.5" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)', borderRadius: '2px', fontSize: '10px' }}>
                          <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600 }}>{part.part_id}</span>
                          <span style={{ fontFamily: sans, color: 'var(--gray3)' }}>×{part.quantity}</span>
                          <span style={{ fontFamily: sans, color: part.in_stock ? 'var(--green5)' : 'var(--red5)', fontWeight: 500, fontSize: '10px' }}>{part.in_stock ? '재고 있음' : '발주 필요'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </>
          )}

          {/* 온톨로지 참조 문서 */}
          {ragData && ragData.related_documents.length > 0 && (
            <>
              <div style={{ height: '1px', background: 'var(--border-mid)' }} />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray5)', fontFamily: sans, marginBottom: '6px' }}>온톨로지 참조 문서</div>
                <div className="space-y-1.5">
                  {ragData.related_documents.slice(0, 3).map(doc => (
                    <div key={doc.manual_id} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)', borderRadius: '2px', padding: '6px 10px' }}>
                      <div className="flex items-center justify-between mb-1">
                        <span style={{ fontFamily: mono, color: 'var(--cyan)', fontWeight: 600, fontSize: '10px' }}>{doc.manual_id}</span>
                        <span style={{ fontFamily: sans, color: 'var(--gray3)', fontSize: '9px' }}>유사도 {doc.hybrid_score.toFixed(2)}</span>
                      </div>
                      <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray4)' }}>
                        {DOC_TITLES[doc.manual_id] ?? doc.title ?? '문서'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ── 전체 설비 종합 분석 ──
function OverviewAnalysisView() {
  const EQ_IDS = ['CNC-001', 'CNC-002', 'CNC-003']
  const a1 = useQuery({ queryKey: ['anomaly', 'CNC-001'], queryFn: () => getEquipmentAnomaly('CNC-001'), refetchInterval: 5000, retry: false })
  const a2 = useQuery({ queryKey: ['anomaly', 'CNC-002'], queryFn: () => getEquipmentAnomaly('CNC-002'), refetchInterval: 5000, retry: false })
  const a3 = useQuery({ queryKey: ['anomaly', 'CNC-003'], queryFn: () => getEquipmentAnomaly('CNC-003'), refetchInterval: 5000, retry: false })
  const r1 = useQuery({ queryKey: ['action', 'CNC-001'], queryFn: () => getActionReport('CNC-001'), retry: false, staleTime: 30_000 })
  const r2 = useQuery({ queryKey: ['action', 'CNC-002'], queryFn: () => getActionReport('CNC-002'), retry: false, staleTime: 30_000 })
  const r3 = useQuery({ queryKey: ['action', 'CNC-003'], queryFn: () => getActionReport('CNC-003'), retry: false, staleTime: 30_000 })
  const s1 = useQuery({ queryKey: ['sensors', 'CNC-001'], queryFn: () => getSensorTimeseries('CNC-001'), refetchInterval: 5000, retry: false })
  const s2 = useQuery({ queryKey: ['sensors', 'CNC-002'], queryFn: () => getSensorTimeseries('CNC-002'), refetchInterval: 5000, retry: false })
  const s3 = useQuery({ queryKey: ['sensors', 'CNC-003'], queryFn: () => getSensorTimeseries('CNC-003'), refetchInterval: 5000, retry: false })

  const anomalies = [a1.data, a2.data, a3.data]
  const actions = [r1.data, r2.data, r3.data]
  const sensors = [s1.data, s2.data, s3.data]

  const statusColor = (score: number) => score >= 0.8 ? 'var(--red5)' : score >= 0.6 ? 'var(--yellow5)' : 'var(--green5)'
  const statusLabel = (score: number) => score >= 0.8 ? '위험' : score >= 0.6 ? '경고' : '정상'

  // 센서 평균 계산
  function calcAvg(series: { s1_current_feedback?: number; x1_current_feedback?: number; x1_output_power?: number; s1_output_power?: number }[] | undefined, key: string) {
    if (!series || series.length === 0) return '—'
    const vals = series.slice(0, 30).map((s: Record<string, unknown>) => Number(s[key] ?? 0)).filter(v => v !== 0)
    if (vals.length === 0) return '—'
    return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)
  }

  const cardStyle = {
    background: 'var(--dg3)', border: '1px solid var(--border-mid)', borderRadius: '3px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.03)',
  }
  const labelStyle = { fontSize: '10px', fontFamily: sans, color: 'var(--gray3)', fontWeight: 500 as const }
  const valueStyle = { fontSize: '11px', fontFamily: sans, fontWeight: 500 as const, color: 'var(--gray4)' }

  // AI 종합 제안 생성
  const suggestions: string[] = []
  EQ_IDS.forEach((id, i) => {
    const score = anomalies[i]?.anomaly_score ?? 0
    const rec = actions[i]?.recommendation
    const fc = anomalies[i]?.predicted_failure_code
    const s1Avg = calcAvg(sensors[i]?.series, 's1_current_feedback')
    if (rec === 'STOP') {
      suggestions.push(`${id}: 즉시 점검 필요 — ${fc?.replace(/_/g, ' ') ?? '이상 감지'}, 스핀들 전류 ${s1Avg}A`)
    } else if (rec === 'REDUCE') {
      suggestions.push(`${id}: 속도 감소 운전 권고 — 이상점수 ${score.toFixed(2)}`)
    } else if (score >= 0.4) {
      suggestions.push(`${id}: 모니터링 강화 — 이상점수 상승 추세`)
    }
  })
  if (suggestions.length === 0) suggestions.push('전체 설비 정상 운전 중 — 특이사항 없음')

  return (
    <div className="p-3 space-y-3 overflow-y-auto flex-1">
      {/* 종합 현황 — 외부 감싸는 카드 */}
      <div>
        <div style={{ fontSize: '13px', fontWeight: 700, fontFamily: sans, color: 'var(--gray5)', marginBottom: '6px' }}>종합 현황</div>
        <div style={{
          ...cardStyle, padding: '8px',
        }}>
          <div className="space-y-2">
            {EQ_IDS.map((id, i) => {
              const score = anomalies[i]?.anomaly_score ?? 0
              const color = statusColor(score)
              const rec = actions[i]?.recommendation
              const fc = anomalies[i]?.predicted_failure_code
              const isCritical = score >= 0.8
              const s1Avg = calcAvg(sensors[i]?.series, 's1_current_feedback')
              const x1Avg = calcAvg(sensors[i]?.series, 'x1_current_feedback')
              const x1Pow = calcAvg(sensors[i]?.series, 'x1_output_power')
              const s1Pow = calcAvg(sensors[i]?.series, 's1_output_power')

              return (
                <div key={id} style={{
                  background: isCritical ? 'rgba(248,113,113,0.04)' : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${isCritical ? 'rgba(248,113,113,0.15)' : 'var(--border-subtle)'}`,
                  borderRadius: '3px', overflow: 'hidden',
                }}>
                  {/* 헤더 */}
                  <div className="flex items-center justify-between px-3 py-1.5" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.015)' }}>
                    <div className="flex items-center gap-2">
                      <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: color }} />
                      <span style={{ fontSize: '12px', fontWeight: 700, fontFamily: sans, color: 'var(--gray5)' }}>{id}</span>
                      <span style={{ fontSize: '11px', fontWeight: 500, fontFamily: sans, color }}>{statusLabel(score)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span style={{ fontSize: '11px', fontFamily: sans, fontWeight: 500, color }}>{score.toFixed(2)}</span>
                      {rec && <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: rec === 'STOP' ? 'var(--red5)' : rec === 'REDUCE' ? 'var(--yellow5)' : 'var(--gray3)' }}>{rec}</span>}
                    </div>
                  </div>

                  {/* 센서 지표 */}
                  <div className="grid grid-cols-4 gap-1 px-3 py-1.5">
                    <div><div style={labelStyle}>S1 전류</div><div style={valueStyle}>{s1Avg} A</div></div>
                    <div><div style={labelStyle}>X1 전류</div><div style={valueStyle}>{x1Avg} A</div></div>
                    <div><div style={labelStyle}>X1 출력</div><div style={valueStyle}>{x1Pow} %</div></div>
                    <div><div style={labelStyle}>S1 출력</div><div style={valueStyle}>{s1Pow} %</div></div>
                  </div>

                  {/* 고장 분석 — 전체 표시 (자르지 않음) */}
                  {(isCritical || rec === 'STOP' || rec === 'REDUCE') && (
                    <div className="px-3 py-1.5" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                      {fc && <div style={{ fontSize: '11px', fontFamily: sans, color: 'var(--orange5)', marginBottom: '2px', fontWeight: 500 }}>{fc.replace(/_/g, ' ')}</div>}
                      <div style={{ fontSize: '11px', fontFamily: sans, color: 'var(--gray4)', lineHeight: '1.5' }}>
                        {actions[i]?.reasoning ?? '분석 대기 중'}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* 구분선 */}
      <div style={{ height: '1px', background: 'linear-gradient(90deg, var(--border-mid), transparent)' }} />

      {/* 예지보전 예측 — 아직 정상이지만 위험 예상되는 설비만 */}
      {(() => {
        const predEqs = EQ_IDS.map((id, i) => {
          const score = anomalies[i]?.anomaly_score ?? 0
          const fc = anomalies[i]?.predicted_failure_code
          // 0.3~0.8 사이만 = 아직 정상이지만 주의 필요
          if (score >= 0.1 && score < 0.8) return { id, score, fc }
          return null
        }).filter(Boolean)
        if (predEqs.length === 0) return null
        return (
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, fontFamily: sans, color: 'var(--yellow5)', marginBottom: '6px' }}>예지보전 예측</div>
            <div style={{ ...cardStyle, padding: '10px 12px', background: 'rgba(251,191,36,0.04)', border: '1px solid rgba(251,191,36,0.12)' }}>
              <div style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)', marginBottom: '6px' }}>아직 정상 범위이지만, 추세 분석 결과 주의가 필요한 설비입니다.</div>
              {predEqs.map((eq) => eq && (
                <div key={eq.id} className="flex items-center justify-between py-1.5" style={{ borderBottom: '1px solid rgba(251,191,36,0.06)' }}>
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 600, color: 'var(--gray5)' }}>{eq.id}</span>
                    <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--yellow5)' }}>
                      현재 {eq.score.toFixed(2)} — 상승 추세
                    </span>
                  </div>
                  <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--orange5)' }}>사전 점검 권고</span>
                </div>
              ))}
            </div>
          </div>
        )
      })()}

      {/* 구분선 */}
      <div style={{ height: '1px', background: 'linear-gradient(90deg, var(--border-mid), transparent)' }} />

      {/* AI 종합 제안 */}
      <div>
        <div style={{ fontSize: '13px', fontWeight: 700, fontFamily: sans, color: 'var(--gray5)', marginBottom: '6px' }}>AI 종합 제안</div>
        <div style={{ ...cardStyle, padding: '10px 12px' }}>
          <ol className="space-y-2">
            {suggestions.map((s, i) => (
              <li key={i} className="flex gap-2" style={{ fontSize: '11px', fontFamily: sans, color: 'var(--gray4)', lineHeight: '1.5' }}>
                <span style={{ color: 'var(--cyan)', fontWeight: 600, flexShrink: 0 }}>{i + 1}.</span>
                <span style={{ fontWeight: 400 }}>{s}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  )
}

// ── 작업현황 AI 분석 ──
function WorkOrderAnalysisView() {
  const EQ_IDS = ['CNC-001', 'CNC-002', 'CNC-003']
  const w1 = useQuery({ queryKey: ['work-order', 'CNC-001'], queryFn: () => getWorkOrderStatus('CNC-001'), retry: false, staleTime: 30_000 })
  const w2 = useQuery({ queryKey: ['work-order', 'CNC-002'], queryFn: () => getWorkOrderStatus('CNC-002'), retry: false, staleTime: 30_000 })
  const w3 = useQuery({ queryKey: ['work-order', 'CNC-003'], queryFn: () => getWorkOrderStatus('CNC-003'), retry: false, staleTime: 30_000 })
  const r1 = useQuery({ queryKey: ['action', 'CNC-001'], queryFn: () => getActionReport('CNC-001'), retry: false, staleTime: 30_000 })
  const r2 = useQuery({ queryKey: ['action', 'CNC-002'], queryFn: () => getActionReport('CNC-002'), retry: false, staleTime: 30_000 })
  const r3 = useQuery({ queryKey: ['action', 'CNC-003'], queryFn: () => getActionReport('CNC-003'), retry: false, staleTime: 30_000 })

  const workOrders = [w1.data, w2.data, w3.data]
  const actions = [r1.data, r2.data, r3.data]
  const cardStyle = { background: 'var(--dg3)', border: '1px solid var(--border-mid)', borderRadius: '3px', boxShadow: '0 1px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.03)' }

  // 분석 데이터
  const activeWOs = workOrders.filter(w => w?.work_order).length
  const completedWOs = workOrders.filter(w => w?.work_order?.status === 'completed').length
  const urgentWOs = workOrders.filter(w => w?.work_order?.priority === 'urgent' || w?.work_order?.priority === 'critical').length
  const stopEquipments = actions.filter(r => r?.recommendation === 'STOP')
  const totalMaint = workOrders.reduce((sum, w) => sum + (w?.recent_maintenance?.length ?? 0), 0)

  // 리스크 분석
  const riskItems: { level: string; color: string; text: string }[] = []
  EQ_IDS.forEach((id, i) => {
    const wo = workOrders[i]?.work_order
    const rec = actions[i]?.recommendation
    const fc = actions[i]?.predicted_failure_code
    if (rec === 'STOP' && wo) {
      riskItems.push({ level: '높음', color: 'var(--red5)', text: `${id}: 설비 이상(${fc?.replace(/_/g,' ') ?? '감지'}) 발생 중 — ${wo.work_order_id} 작업 영향. 즉시 작업 중단 후 점검 필요.` })
    } else if (rec === 'STOP') {
      riskItems.push({ level: '높음', color: 'var(--red5)', text: `${id}: 설비 이상 감지 — 신규 작업 배정 보류 필요. 점검 완료 전 가동 불가.` })
    } else if (wo?.priority === 'urgent') {
      riskItems.push({ level: '주의', color: 'var(--yellow5)', text: `${id}: ${wo.work_order_id} 긴급 작업 수행 중. 설비 이상 발생 시 납기 지연 위험.` })
    }
  })
  if (riskItems.length === 0) riskItems.push({ level: '양호', color: 'var(--green5)', text: '전체 설비 정상 가동 중. 작업 일정에 영향을 줄 리스크 없음.' })

  return (
    <div className="p-3 space-y-3 overflow-y-auto flex-1">
      <div style={{ fontSize: '13px', fontWeight: 700, fontFamily: sans, color: 'var(--gray5)' }}>작업현황 분석</div>

      {/* 현황 요약 */}
      <PanelSection title="현황 요약">
        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
          <div><span style={{ fontSize: '10px', color: 'var(--gray3)', fontFamily: sans }}>배정 작업</span><div style={{ fontSize: '11px', fontWeight: 500, color: 'var(--gray5)', fontFamily: sans }}>{activeWOs}건</div></div>
          <div><span style={{ fontSize: '10px', color: 'var(--gray3)', fontFamily: sans }}>완료 작업</span><div style={{ fontSize: '11px', fontWeight: 500, color: 'var(--green5)', fontFamily: sans }}>{completedWOs}건</div></div>
          <div><span style={{ fontSize: '10px', color: 'var(--gray3)', fontFamily: sans }}>긴급 작업</span><div style={{ fontSize: '11px', fontWeight: 500, color: urgentWOs > 0 ? 'var(--red5)' : 'var(--gray4)', fontFamily: sans }}>{urgentWOs}건</div></div>
          <div><span style={{ fontSize: '10px', color: 'var(--gray3)', fontFamily: sans }}>정비 이력</span><div style={{ fontSize: '11px', fontWeight: 500, color: 'var(--gray4)', fontFamily: sans }}>{totalMaint}건</div></div>
        </div>
      </PanelSection>

      {/* 설비별 작업 */}
      <PanelSection title="설비별 작업 상세">
        <div className="space-y-2">
          {EQ_IDS.map((id, i) => {
            const wo = workOrders[i]?.work_order
            const rec = actions[i]?.recommendation
            const maint = workOrders[i]?.recent_maintenance ?? []
            const isStop = rec === 'STOP'
            const lastMaint = maint[0]
            return (
              <div key={id} style={{ background: isStop ? 'rgba(248,113,113,0.04)' : 'rgba(255,255,255,0.02)', border: `1px solid ${isStop ? 'rgba(248,113,113,0.15)' : 'var(--border-subtle)'}`, borderRadius: '3px', padding: '8px 10px' }}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: '11px', fontWeight: 700, fontFamily: sans, color: 'var(--gray5)' }}>{id}</span>
                    {isStop && <span style={{ fontSize: '9px', fontFamily: sans, color: 'var(--red5)', fontWeight: 500 }}>이상 감지</span>}
                  </div>
                  {wo && <span style={{ fontSize: '10px', fontFamily: mono, color: 'var(--cyan)' }}>{wo.work_order_id}</span>}
                </div>
                {wo ? (
                  <>
                    <div style={{ fontSize: '10px', color: 'var(--gray4)', fontFamily: sans, marginBottom: '2px' }}>
                      {wo.product_type} · {wo.status} · <span style={{ color: wo.priority === 'urgent' ? 'var(--red5)' : 'var(--gray3)' }}>{wo.priority}</span> · 납기 {wo.due_date?.slice(0, 10)}
                    </div>
                  </>
                ) : (
                  <div style={{ fontSize: '10px', color: 'var(--gray2)', fontFamily: sans }}>배정 작업 없음</div>
                )}
                {lastMaint && (
                  <div style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans, marginTop: '3px', borderTop: '1px solid var(--border-subtle)', paddingTop: '3px' }}>
                    최근 정비: {lastMaint.event_type} ({lastMaint.duration_min}분) {lastMaint.failure_code ? `· ${lastMaint.failure_code.replace(/_/g,' ')}` : ''}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </PanelSection>

      <div style={{ height: '1px', background: 'linear-gradient(90deg, var(--border-mid), transparent)' }} />

      {/* 리스크 분석 */}
      <PanelSection title="생산 리스크 분석">
        <div className="space-y-2">
          {riskItems.map((item, i) => (
            <div key={i} className="flex gap-2" style={{ fontSize: '11px', fontFamily: sans, color: 'var(--gray4)', lineHeight: '1.6' }}>
              <span style={{ fontSize: '9px', fontWeight: 600, color: item.color, flexShrink: 0, minWidth: '28px', paddingTop: '2px' }}>{item.level}</span>
              <span>{item.text}</span>
            </div>
          ))}
        </div>
      </PanelSection>
    </div>
  )
}

// ── 재고현황 AI 분석 ──
function InventoryAnalysisView() {
  const { data } = useQuery({ queryKey: ['inventory'], queryFn: () => getWorkOrderStatus('CNC-001'), retry: false, staleTime: 60_000 })
  const a1 = useQuery({ queryKey: ['anomaly', 'CNC-002'], queryFn: () => getEquipmentAnomaly('CNC-002'), retry: false, staleTime: 30_000 })
  const inventory = data?.inventory ?? []
  const fc002 = a1.data?.predicted_failure_code

  const lowStock = inventory.filter(p => p.stock_quantity <= p.reorder_point)
  const cautionStock = inventory.filter(p => p.stock_quantity > p.reorder_point && p.stock_quantity <= p.reorder_point * 2)
  const healthyStock = inventory.filter(p => p.stock_quantity > p.reorder_point * 2)

  // 고장코드와 부품 연관 분석
  const fcPartMap: Record<string, string[]> = {
    SPINDLE_OVERHEAT_001: ['P002', 'P003'],
    TOOL_WEAR_001: ['P001', 'P005'],
    COOLANT_LOW_001: ['P003', 'P005'],
    CLAMP_PRESSURE_001: ['P004'],
  }
  const neededParts = fc002 ? (fcPartMap[fc002] ?? []) : []
  const neededPartsInfo = inventory.filter(p => neededParts.includes(p.part_id))

  return (
    <div className="p-3 space-y-3 overflow-y-auto flex-1">
      <div style={{ fontSize: '13px', fontWeight: 700, fontFamily: sans, color: 'var(--gray5)' }}>재고현황 분석</div>

      {/* 재고 건강도 */}
      <PanelSection title="재고 건강도">
        <div className="flex gap-3 mb-2">
          <div style={{ flex: 1, textAlign: 'center', padding: '6px', background: 'rgba(248,113,113,0.06)', borderRadius: '3px', border: '1px solid rgba(248,113,113,0.12)' }}>
            <div style={{ fontSize: '16px', fontWeight: 600, color: lowStock.length > 0 ? 'var(--red5)' : 'var(--gray2)', fontFamily: sans }}>{lowStock.length}</div>
            <div style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans }}>부족</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center', padding: '6px', background: 'rgba(251,191,36,0.06)', borderRadius: '3px', border: '1px solid rgba(251,191,36,0.12)' }}>
            <div style={{ fontSize: '16px', fontWeight: 600, color: cautionStock.length > 0 ? 'var(--yellow5)' : 'var(--gray2)', fontFamily: sans }}>{cautionStock.length}</div>
            <div style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans }}>주의</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center', padding: '6px', background: 'rgba(52,211,153,0.06)', borderRadius: '3px', border: '1px solid rgba(52,211,153,0.12)' }}>
            <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--green5)', fontFamily: sans }}>{healthyStock.length}</div>
            <div style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans }}>충분</div>
          </div>
        </div>
      </PanelSection>

      {/* 부품별 상세 */}
      <PanelSection title="부품별 재고 상세">
        <div className="space-y-1.5">
          {inventory.map(part => {
            const low = part.stock_quantity <= part.reorder_point
            const caution = !low && part.stock_quantity <= part.reorder_point * 2
            const ratio = part.stock_quantity / Math.max(part.reorder_point * 3, 1)
            const statusLabel = low ? '부족' : caution ? '주의' : '충분'
            const statusColor = low ? 'var(--red5)' : caution ? 'var(--yellow5)' : 'var(--green5)'
            const isNeeded = neededParts.includes(part.part_id)
            return (
              <div key={part.part_id} style={{ background: low ? 'rgba(248,113,113,0.04)' : 'rgba(255,255,255,0.02)', border: `1px solid ${low ? 'rgba(248,113,113,0.15)' : 'var(--border-subtle)'}`, borderRadius: '3px', padding: '6px 10px' }}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: '10px', fontFamily: mono, fontWeight: 600, color: 'var(--cyan)' }}>{part.part_id}</span>
                    {isNeeded && <span style={{ fontSize: '8px', fontFamily: sans, color: 'var(--orange5)', background: 'rgba(251,146,60,0.1)', padding: '1px 4px', borderRadius: '2px', border: '1px solid rgba(251,146,60,0.15)' }}>수리 필요</span>}
                  </div>
                  <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: statusColor }}>{part.stock_quantity}개 · {statusLabel}</span>
                </div>
                <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray4)', marginBottom: '3px' }}>{part.part_name}</div>
                <div style={{ width: '100%', height: '3px', background: 'var(--dg4)', borderRadius: '1px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${Math.min(ratio * 100, 100)}%`, background: statusColor, transition: 'width 0.3s' }} />
                </div>
                <div style={{ fontSize: '9px', fontFamily: sans, color: 'var(--gray3)', marginTop: '2px' }}>안전재고: {part.reorder_point}개</div>
              </div>
            )
          })}
        </div>
      </PanelSection>

      {/* 고장 연관 부품 분석 */}
      {fc002 && neededPartsInfo.length > 0 && (
        <>
          <div style={{ height: '1px', background: 'linear-gradient(90deg, var(--border-mid), transparent)' }} />
          <PanelSection title="고장 연관 부품 분석">
            <div style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray4)', marginBottom: '6px', lineHeight: '1.5' }}>
              현재 CNC-002에서 <span style={{ color: 'var(--orange5)', fontWeight: 500 }}>{fc002.replace(/_/g, ' ')}</span> 감지. 수리 시 다음 부품이 필요합니다.
            </div>
            {neededPartsInfo.map(p => {
              const low = p.stock_quantity <= p.reorder_point
              return (
                <div key={p.part_id} className="flex items-center justify-between py-1" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '10px', fontFamily: sans, color: 'var(--gray5)' }}>{p.part_id} {p.part_name}</span>
                  <span style={{ fontSize: '10px', fontFamily: sans, fontWeight: 500, color: low ? 'var(--red5)' : 'var(--green5)' }}>{low ? '발주 필요' : '재고 확보'}</span>
                </div>
              )
            })}
          </PanelSection>
        </>
      )}
    </div>
  )
}

// ── 메인 ──
export default function AiDetailPanel() {
  const { selectedEquipmentId, selectedAlarm, activeOverlay } = useDashboardStore()
  const hasSelection = !!selectedEquipmentId || !!selectedAlarm
  const headerRight = selectedAlarm?.equipment_id ?? selectedEquipmentId ?? ''

  // 오버레이 활성화 시 해당 분석 표시
  const isOverlay = activeOverlay === 'work' || activeOverlay === 'inventory'
  const headerLabel = isOverlay
    ? (activeOverlay === 'work' ? 'AI 작업현황 분석' : 'AI 재고현황 분석')
    : selectedAlarm ? '이상감지 분석'
    : hasSelection ? 'AI 분석 결과'
    : 'AI 전체 설비 종합 분석'
  const headerDot = selectedAlarm ? 'var(--yellow5)' : 'var(--cyan)'

  // 현재 보여줄 뷰 결정
  const renderContent = () => {
    if (isOverlay) {
      return activeOverlay === 'work' ? <WorkOrderAnalysisView /> : <InventoryAnalysisView />
    }
    if (selectedAlarm) return <AlarmAnalysisView alarm={selectedAlarm} />
    if (selectedEquipmentId) return <EquipmentAnalysisView equipmentId={selectedEquipmentId} />
    return <OverviewAnalysisView />
  }

  return (
    <div className="flex flex-col flex-shrink-0" style={{ width: '100%', height: '100%', background: 'var(--dg1)', borderRight: '1px solid var(--border-mid)', padding: '6px 8px 12px 0' }}>
      <div style={{ flex: 1, background: 'var(--dg1-5)', border: '1px solid var(--border-mid)', borderRadius: '3px', boxShadow: '0 1px 3px rgba(0,0,0,0.2)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div className="flex items-center gap-2 px-4 py-2 flex-shrink-0" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: headerDot }} />
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--gray5)', fontFamily: sans }}>{headerLabel}</span>
          {headerRight && !isOverlay && <span style={{ marginLeft: 'auto', fontSize: '11px', fontFamily: sans, fontWeight: 600, color: headerDot }}>{headerRight}</span>}
        </div>
        {renderContent()}
      </div>
    </div>
  )
}
