// ============================================================
// AppShell — 전체 레이아웃 골격
// [Topbar] / [Sidebar | AI Panel | Center (+ Overlays) | ChatPanel]
// ============================================================

import Topbar from './Topbar'
import Sidebar from './Sidebar'
import AiDetailPanel from './AiDetailPanel'
import MonitoringCenter from '../dashboard/MonitoringCenter'
import ChatPanel from '../dashboard/ChatPanel'
import WorkOrderOverlay from '../dashboard/WorkOrderOverlay'
import InventoryOverlay from '../dashboard/InventoryOverlay'
import { useDashboardStore } from '@/stores/dashboardStore'

export default function AppShell() {
  const { activeOverlay } = useDashboardStore()

  return (
    <div className="flex flex-col h-full bg-black overflow-hidden">
      <Topbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        {/* AI 패널 */}
        <div className="relative flex-shrink-0" style={{ width: 'var(--ai-panel-w)' }}>
          <AiDetailPanel />
        </div>
        {/* 모니터링 + 오버레이 */}
        <div className="relative flex-1 flex flex-col overflow-hidden">
          <WorkOrderOverlay open={activeOverlay === 'work'} />
          <InventoryOverlay open={activeOverlay === 'inventory'} />
          <MonitoringCenter />
        </div>
        <ChatPanel />
      </div>
    </div>
  )
}
