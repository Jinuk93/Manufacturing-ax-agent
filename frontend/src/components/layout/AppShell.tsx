// ============================================================
// AppShell — 전체 레이아웃 골격
// [Topbar] / [Sidebar | AI Panel | Center]
// ui-ux-design.md 섹션 14-1 레이아웃 구조
// ============================================================

import Topbar from './Topbar'
import Sidebar from './Sidebar'
import AiDetailPanel from './AiDetailPanel'
import MonitoringCenter from '../dashboard/MonitoringCenter'
import ChatFab from '../dashboard/ChatFab'

export default function AppShell() {
  return (
    <div className="flex flex-col h-full bg-black overflow-hidden">
      {/* 상단 바 */}
      <Topbar />

      {/* 메인 영역: Sidebar | AI Panel | Center */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <AiDetailPanel />
        <MonitoringCenter />
      </div>

      {/* FAB 챗봇 버튼 — fixed, 레이아웃 외부 */}
      <ChatFab />
    </div>
  )
}
