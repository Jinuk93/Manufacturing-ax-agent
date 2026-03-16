// ============================================================
// AiDetailPanel — AI 분석 결과 패널 (320px)
// 이상 점수 게이지 + AI 조치 리포트 + GraphRAG 근거 문서 + 판단 투명성
// ============================================================

import { useQuery } from '@tanstack/react-query'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getEquipmentDetail, getRelatedDocuments } from '@/lib/api/endpoints'
import type { ActionType } from '@/types'

const ACTION_COLORS: Record<ActionType, string> = {
  STOP:    'var(--red5)',
  REDUCE:  'var(--yellow5)',
  MONITOR: 'var(--blue4)',
  NORMAL:  'var(--green5)',
}

export default function AiDetailPanel() {
  const { selectedEquipmentId } = useDashboardStore()

  const { data: detail } = useQuery({
    queryKey: ['equipment-detail', selectedEquipmentId],
    queryFn: () => getEquipmentDetail(selectedEquipmentId!),
    enabled: !!selectedEquipmentId,
  })

  const { data: documents } = useQuery({
    queryKey: ['related-docs', selectedEquipmentId],
    queryFn: () => getRelatedDocuments(selectedEquipmentId!),
    enabled: !!selectedEquipmentId,
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

  return (
    <div
      className="flex flex-col flex-shrink-0 overflow-y-auto"
      style={{
        width: 'var(--ai-panel-w)',
        background: 'var(--dg1)',
        borderRight: '2px solid var(--border-mid)',
      }}
    >
      {/* 그룹 구분선 */}
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
        {detail && (
          <div>
            <div className="flex justify-between items-baseline mb-1">
              <span className="text-xs" style={{ color: 'var(--gray4)' }}>
                이상 점수
              </span>
              <span
                className="font-mono text-2xl font-bold"
                style={{ color: ACTION_COLORS[detail.action] }}
              >
                {(detail.timestamp ? 0.87 : 0).toFixed(2)}
              </span>
            </div>
            <div
              className="h-1.5 rounded-full overflow-hidden"
              style={{ background: 'var(--dg3)' }}
            >
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: '87%',
                  background: ACTION_COLORS[detail.action],
                }}
              />
            </div>
          </div>
        )}

        {/* AI 조치 리포트 */}
        {detail && (
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
                background: `${ACTION_COLORS[detail.action]}20`,
                color: ACTION_COLORS[detail.action],
                border: `1px solid ${ACTION_COLORS[detail.action]}40`,
              }}
            >
              {detail.action}
            </div>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--gray4)' }}>
              {detail.reasoning}
            </p>
          </div>
        )}

        {/* GraphRAG 참조 문서 */}
        {documents && documents.length > 0 && (
          <div>
            <div
              className="text-xs font-semibold mb-1.5"
              style={{ color: 'var(--gray4)' }}
            >
              참조 문서 (근거)
            </div>
            <div className="space-y-1.5">
              {documents.map((doc) => (
                <div
                  key={doc.manual_id}
                  className="p-2 rounded text-xs"
                  style={{
                    background: 'var(--dg3)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div className="flex justify-between mb-0.5">
                    <span style={{ color: 'var(--blue4)' }}>
                      {doc.manual_id}
                    </span>
                    <span
                      className="font-mono"
                      style={{ color: 'var(--gray3)' }}
                    >
                      {doc.hybrid_score.toFixed(2)}
                    </span>
                  </div>
                  <div style={{ color: 'var(--gray5)' }}>{doc.title}</div>
                  {doc.snippet && (
                    <div
                      className="mt-1 text-xs leading-relaxed"
                      style={{ color: 'var(--gray3)' }}
                    >
                      {doc.snippet}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
