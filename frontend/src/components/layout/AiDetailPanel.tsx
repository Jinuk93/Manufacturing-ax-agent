// ============================================================
// AiDetailPanel — AI 분석 결과 패널 (320px)
// F2 이상점수 게이지 + F5 LLM 조치 리포트 + 부품 재고 현황
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getActionReport, getEquipmentAnomaly } from '@/lib/api/endpoints'
import type { ActionType } from '@/types'

const ACTION_COLORS: Record<ActionType, string> = {
  STOP:    'var(--red5)',
  REDUCE:  'var(--yellow5)',
  MONITOR: 'var(--blue4)',
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
    queryKey: ['action-report', selectedEquipmentId],
    queryFn: () => getActionReport(selectedEquipmentId!),
    enabled: !!selectedEquipmentId,
    retry: false,
    staleTime: 30_000,     // 30초 캐시 — LLM 호출 비용 절감
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
        className="flex items-center gap-2 px-3 py-2 text-xs font-semibold uppercase tracking-wider"
        style={{
          color: 'var(--gray3)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div
          className="rounded-full"
          style={{ width: '6px', height: '6px', background: 'var(--blue3)' }}
        />
        AI 분석 결과
      </div>

      <div className="p-3 space-y-4">
        {/* 이상 점수 게이지 */}
        <div>
          <div className="flex justify-between items-baseline mb-1">
            <span className="text-xs" style={{ color: 'var(--gray4)' }}>
              이상 점수
            </span>
            <span
              className="font-mono text-2xl font-bold"
              style={{ color: actionColor }}
            >
              {score.toFixed(2)}
            </span>
          </div>
          <div
            className="h-1.5 rounded-full overflow-hidden"
            style={{ background: 'var(--dg3)' }}
          >
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${(score * 100).toFixed(0)}%`,
                background: actionColor,
              }}
            />
          </div>
        </div>

        {/* AI 조치 판단 */}
        {actionLoading ? (
          <div className="text-xs" style={{ color: 'var(--gray3)' }}>
            LLM 분석 중...
          </div>
        ) : actionReport && (
          <>
            <div>
              <div
                className="text-xs font-semibold mb-1.5"
                style={{ color: 'var(--gray4)' }}
              >
                AI 조치 판단
              </div>
              <div
                className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-bold mb-2"
                style={{
                  background: `${actionColor}20`,
                  color: actionColor,
                  border: `1px solid ${actionColor}40`,
                }}
              >
                {actionReport.recommendation}
              </div>
              <p className="text-xs leading-relaxed" style={{ color: 'var(--gray4)' }}>
                {actionReport.reasoning}
              </p>
            </div>

            {/* 조치 단계 */}
            {actionReport.action_steps.length > 0 && (
              <div>
                <div
                  className="text-xs font-semibold mb-1.5"
                  style={{ color: 'var(--gray4)' }}
                >
                  조치 단계
                </div>
                <ol className="space-y-1">
                  {actionReport.action_steps.map((step, i) => (
                    <li key={i} className="flex gap-2 text-xs" style={{ color: 'var(--gray4)' }}>
                      <span
                        className="font-mono flex-shrink-0"
                        style={{ color: 'var(--blue3)' }}
                      >
                        {i + 1}.
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* 필요 부품 */}
            {actionReport.parts_needed.length > 0 && (
              <div>
                <div
                  className="text-xs font-semibold mb-1.5"
                  style={{ color: 'var(--gray4)' }}
                >
                  필요 부품
                </div>
                <div className="space-y-1">
                  {actionReport.parts_needed.map((part) => (
                    <div
                      key={part.part_id}
                      className="flex items-center justify-between text-xs px-2 py-1 rounded"
                      style={{ background: 'var(--dg3)' }}
                    >
                      <span
                        className="font-mono"
                        style={{ color: 'var(--blue4)' }}
                      >
                        {part.part_id}
                      </span>
                      <span style={{ color: 'var(--gray4)' }}>×{part.quantity}</span>
                      <span
                        style={{
                          color: part.in_stock ? 'var(--green5)' : 'var(--red5)',
                        }}
                      >
                        {part.in_stock ? '재고 있음' : '발주 필요'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
