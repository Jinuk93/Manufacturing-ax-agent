// ============================================================
// AppShell — 전체 레이아웃 골격
// [Topbar] / [Sidebar | AI Panel | Center | ChatPanel]
// ============================================================

import Topbar from './Topbar'
import Sidebar from './Sidebar'
import AiDetailPanel from './AiDetailPanel'
import MonitoringCenter from '../dashboard/MonitoringCenter'
import ChatPanel from '../dashboard/ChatPanel'

export default function AppShell() {
  return (
    <div className="flex flex-col h-full bg-black overflow-hidden">
      <Topbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <AiDetailPanel />
        <MonitoringCenter />
        <ChatPanel />
      </div>
    </div>
  )
}
