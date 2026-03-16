// ============================================================
// MonitoringCenter — 중앙 모니터링 영역 (flex, 나머지 공간)
// 센서 차트 + 파이프라인 상태 + 정비 이력 타임라인
// Phase 3에서 순차적으로 채워나갈 메인 영역
// ============================================================

import { useDashboardStore } from '@/stores/dashboardStore'

export default function MonitoringCenter() {
  const { selectedEquipmentId } = useDashboardStore()

  return (
    <div
      className="flex-1 flex flex-col overflow-hidden"
      style={{ background: 'var(--dg2)' }}
    >
      {/* 센터 헤더 */}
      <div
        className="flex items-center px-4 text-xs font-semibold uppercase tracking-wider flex-shrink-0"
        style={{
          height: '36px',
          borderBottom: '1px solid var(--border-subtle)',
          color: 'var(--gray3)',
        }}
      >
        {selectedEquipmentId
          ? `${selectedEquipmentId} — 모니터링`
          : '모니터링 센터'}
      </div>

      {/* 콘텐츠 영역 — Phase 3에서 차트/타임라인 컴포넌트로 채울 공간 */}
      <div className="flex-1 overflow-y-auto p-4">
        {!selectedEquipmentId ? (
          <div
            className="h-full flex items-center justify-center text-sm"
            style={{ color: 'var(--gray3)' }}
          >
            좌측 사이드바에서 설비를 선택하면 센서 차트와 분석 결과가 표시됩니다.
          </div>
        ) : (
          <div className="space-y-4">
            {/* TODO Phase 3: SensorChart 컴포넌트 */}
            <Placeholder label="센서 시계열 차트 (Recharts)" height="200px" />
            {/* TODO Phase 3: PipelineStatus 컴포넌트 */}
            <Placeholder label="파이프라인 상태 (F1~F5)" height="80px" />
            {/* TODO Phase 3: MaintenanceTimeline 컴포넌트 */}
            <Placeholder label="정비 이력 타임라인" height="160px" />
          </div>
        )}
      </div>
    </div>
  )
}

// 개발 중 플레이스홀더
function Placeholder({ label, height }: { label: string; height: string }) {
  return (
    <div
      className="rounded flex items-center justify-center text-xs"
      style={{
        height,
        background: 'var(--dg3)',
        border: '1px dashed var(--border-mid)',
        color: 'var(--gray3)',
      }}
    >
      {label}
    </div>
  )
}
