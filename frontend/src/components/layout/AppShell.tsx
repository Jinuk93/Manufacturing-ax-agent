// ============================================================
// AppShell — 전체 레이아웃 골격 (ErrorBoundary 적용)
// ============================================================

import Topbar from './Topbar'
import Sidebar from './Sidebar'
import AiDetailPanel from './AiDetailPanel'
import MonitoringCenter from '../dashboard/MonitoringCenter'
import ChatPanel from '../dashboard/ChatPanel'
import WorkOrderOverlay from '../dashboard/WorkOrderOverlay'
import InventoryOverlay from '../dashboard/InventoryOverlay'
import ErrorBoundary from '../ErrorBoundary'
import { useDashboardStore } from '@/stores/dashboardStore'

export default function AppShell() {
  const { activeOverlay } = useDashboardStore()

  return (
    <ErrorBoundary name="App">
      <div className="flex flex-col h-full bg-black overflow-hidden">
        <ErrorBoundary name="Topbar">
          <Topbar />
        </ErrorBoundary>
        <div className="flex flex-1 overflow-hidden">
          <ErrorBoundary name="Sidebar">
            <Sidebar />
          </ErrorBoundary>
          <div className="relative flex-shrink-0" style={{ width: 'var(--ai-panel-w)' }}>
            <ErrorBoundary name="AiDetailPanel">
              <AiDetailPanel />
            </ErrorBoundary>
          </div>
          <div className="relative flex-1 flex flex-col overflow-hidden">
            <WorkOrderOverlay open={activeOverlay === 'work'} />
            <InventoryOverlay open={activeOverlay === 'inventory'} />
            <ErrorBoundary name="MonitoringCenter">
              <MonitoringCenter />
            </ErrorBoundary>
          </div>
          <ErrorBoundary name="ChatPanel">
            <ChatPanel />
          </ErrorBoundary>
        </div>
      </div>
    </ErrorBoundary>
  )
}
