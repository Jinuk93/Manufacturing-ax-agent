// ============================================================
// AiDetailPanel — AI 분석 결과 패널 (320px)
// F2 이상점수 게이지 + F5 LLM 조치 리포트 + GraphRAG 참조 문서
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getActionReport, getEquipmentAnomaly, searchGraphRAG } from '@/lib/api/endpoints'
import type { ActionType } from '@/types'

const ACTION_COLORS: Record<ActionType, string> = {
  STOP:    'var(--red5)',
  REDUCE:  'var(--yellow5)',
  MONITOR: 'var(--blue4)',
}

// 이상 점수를 색상 블록 그라디언트로 시각화
function ScoreBlocks({ score }: { score: number }) {
  const BLOCKS = 10
  const filledCount = Math.round(score * BLOCKS)
  const getColor = (i: number) => {
    if (i >= 8) return 'var(--red5)'
    if (i >= 6) return 'var(--yellow5)'
    return 'var(--green5)'
  }
  return (
    <div className="flex gap-1 mt-2">
      {Array.from({ length: BLOCKS }, (_, i) => (
        <div
          key={i}
          style={{
            flex: 1, height: '8px', borderRadius: '2px',
            background: i < filledCount ? getColor(i) : 'var(--dg4)',
            opacity: i < filledCount ? 1 : 0.3,
            transition: 'all 0.3s',
          }}
        />
      ))}
    </div>
  )
}

export default function AiDetailPanel() {
  const { selectedEquipmentId } = useDashboardStore()

  const { data: anomaly } = useQuery({
    queryKey: ['anomaly', selectedEquipmentId],
    queryFn: () => getEquipmentAnomaly(selectedEquipmentId!),
    enabled: !!selectedEquipmentId,
    refetchInterval: 5000,
    retry: false,
  })

  const { data: actionReport, isLoading: actionLoading } = useQuery({
    queryKey: ['action', selectedEquipmentId],
    queryFn: () => getActionReport(selectedEquipmentId!),
    enabled: !!selectedEquipmentId,
    retry: false,
    staleTime: 30_000,
  })

  // GraphRAG 참조 문서 — predicted_failure_code가 있을 때만 조회
  const failureCode = actionReport?.predicted_failure_code ?? anomaly?.predicted_failure_code
  const { data: ragData } = useQuery({
    queryKey: ['graphrag', selectedEquipmentId, failureCode],
    queryFn: () => searchGraphRAG(failureCode!, selectedEquipmentId!),
    enabled: !!selectedEquipmentId && !!failureCode,
    staleTime: 60_000,
    retry: false,
  })

  if (!selectedEquipmentId) {
    return (
      <div
        className="flex flex-col items-center justify-center flex-shrink-0"
        style={{
          width: 'var(--ai-panel-w)',
          background: 'var(--dg1)',
          borderRight: '2px solid var(--border-mid)',
          color: 'var(--gray3)',
          fontSize: '12px',
        }}
      >
        좌측에서 설비를 선택하세요
      </div>
    )
  }

  const recommendation = actionReport?.recommendation ?? 'MONITOR'
  const actionColor = ACTION_COLORS[recommendation]
  const score = anomaly?.anomaly_score ?? 0

  // 임계값 정보
  const thresholdLabel = score >= 0.8 ? 'STOP 임계치 (0.80) 초과' :
                         score >= 0.6 ? 'REDUCE 임계치 (0.60) 초과' : '정상 범위'
  const confidencePct = actionReport ? `확신도 ${(actionReport.confidence * 100).toFixed(0)}%` : ''

  return (
    <div
      className="flex flex-col flex-shrink-0 overflow-y-auto"
      style={{
        width: 'var(--ai-panel-w)',
        background: 'var(--dg1)',
        borderRight: '2px solid var(--border-mid)',
      }}
    >
      {/* 헤더 */}
      <div
        className="flex items-center gap-2 px-3 py-2 text-xs font-semibold uppercase tracking-wider flex-shrink-0"
        style={{ color: 'var(--gray3)', borderBottom: '1px solid var(--border-subtle)' }}
      >
        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--blue3)' }} />
        AI 분석 결과
      </div>

      <div className="p-3 space-y-4">
        {/* 이상 점수 + 블록 시각화 */}
        <div>
          <div className="flex justify-between items-baseline mb-1">
            <span className="text-xs" style={{ color: 'var(--gray4)' }}>이상 점수</span>
            <span style={{ fontSize: '10px', color: 'var(--gray3)', fontFamily: "'JetBrains Mono', monospace" }}>
              5초
            </span>
          </div>
          <div className="flex items-end gap-2">
            <span className="font-mono font-bold" style={{ fontSize: '40px', lineHeight: 1, color: actionColor }}>
              {score.toFixed(2)}
            </span>
          </div>
          <ScoreBlocks score={score} />
          <div className="mt-1.5 text-xs" style={{ color: actionColor }}>{thresholdLabel}</div>
          {actionReport?.predicted_failure_code && (
            <div className="text-xs mt-0.5" style={{ color: 'var(--gray4)' }}>
              {actionReport.predicted_failure_code}
            </div>
          )}
          {confidencePct && (
            <div className="text-xs mt-0.5" style={{ color: 'var(--gray3)' }}>{confidencePct}</div>
          )}
        </div>

        {/* 구분선 */}
        <div style={{ height: '1px', background: 'var(--border-subtle)' }} />

        {/* AI 조치 판단 */}
        {actionLoading ? (
          <div className="text-xs" style={{ color: 'var(--gray3)' }}>LLM 분석 중...</div>
        ) : actionReport && (
          <>
            <div>
              <div className="text-xs font-semibold mb-1.5" style={{ color: 'var(--gray4)' }}>AI 조치 판단</div>
              <div
                className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-bold mb-2"
                style={{
                  background: `${actionColor}20`,
                  color: actionColor,
                  border: `1px solid ${actionColor}40`,
                  letterSpacing: '0.08em',
                }}
              >
                {actionReport.recommendation === 'STOP' && (
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: actionColor }} />
                )}
                즉시 정지 ({actionReport.recommendation})
              </div>
              <p className="text-xs leading-relaxed" style={{ color: 'var(--gray4)' }}>
                {actionReport.reasoning}
              </p>
            </div>

            {/* 조치 단계 */}
            {actionReport.action_steps.length > 0 && (
              <div>
                <div className="text-xs font-semibold mb-1.5" style={{ color: 'var(--gray4)' }}>조치 단계</div>
                <ol className="space-y-1.5">
                  {actionReport.action_steps.map((step, i) => {
                    // DOC-xxx 또는 P0xx 패턴 추출해서 배지로 표시
                    const docMatch = step.match(/DOC-\d+/g)
                    const partMatch = step.match(/P\d{3}/g)
                    return (
                      <li key={i} className="flex gap-2 text-xs" style={{ color: 'var(--gray4)' }}>
                        <span className="font-mono flex-shrink-0" style={{ color: 'var(--blue3)', minWidth: '14px' }}>
                          {i + 1}.
                        </span>
                        <span className="flex-1">
                          {step}
                          {docMatch?.map((d) => (
                            <span key={d} className="ml-1 px-1 rounded font-mono"
                              style={{ background: 'rgba(45,114,210,0.2)', color: 'var(--blue4)', fontSize: '10px' }}>
                              {d}
                            </span>
                          ))}
                          {partMatch?.map((p) => (
                            <span key={p} className="ml-1 px-1 rounded font-mono"
                              style={{ background: 'rgba(114,202,155,0.15)', color: 'var(--green5)', fontSize: '10px' }}>
                              {p}
                            </span>
                          ))}
                        </span>
                      </li>
                    )
                  })}
                </ol>
              </div>
            )}

            {/* 필요 부품 */}
            {actionReport.parts_needed.length > 0 && (
              <div>
                <div className="text-xs font-semibold mb-1.5" style={{ color: 'var(--gray4)' }}>필요 부품</div>
                <div className="space-y-1">
                  {actionReport.parts_needed.map((part) => (
                    <div
                      key={part.part_id}
                      className="flex items-center justify-between text-xs px-2 py-1 rounded"
                      style={{ background: 'var(--dg3)' }}
                    >
                      <span className="font-mono" style={{ color: 'var(--blue4)' }}>{part.part_id}</span>
                      <span style={{ color: 'var(--gray4)' }}>×{part.quantity}</span>
                      <span style={{ color: part.in_stock ? 'var(--green5)' : 'var(--red5)' }}>
                        {part.in_stock ? '재고 있음' : '발주 필요'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* GraphRAG 참조 문서 */}
        {ragData && ragData.related_documents.length > 0 && (
          <>
            <div style={{ height: '1px', background: 'var(--border-subtle)' }} />
            <div>
              <div className="flex items-center gap-1.5 text-xs font-semibold mb-2" style={{ color: 'var(--gray3)' }}>
                <span>GRAPHRAG 참조 문서</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", color: 'var(--blue4)', fontSize: '10px' }}>F4</span>
              </div>
              <div className="space-y-1">
                {ragData.related_documents.slice(0, 3).map((doc) => (
                  <div
                    key={doc.manual_id}
                    className="flex items-center justify-between text-xs px-2 py-1.5 rounded"
                    style={{ background: 'var(--dg3)', border: '1px solid var(--border-subtle)' }}
                  >
                    <span className="font-mono font-semibold" style={{ color: 'var(--blue4)' }}>
                      {doc.manual_id}
                    </span>
                    <span
                      className="font-mono text-xs"
                      style={{ color: 'var(--gray3)' }}
                    >
                      hybrid: {doc.hybrid_score.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
