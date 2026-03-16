// ============================================================
// ChatFab — 챗봇 FAB 버튼 (우하단 fixed)
// ui-ux-design.md 섹션 14-6 패턴
// ============================================================

import { useState } from 'react'
import { useDashboardStore } from '@/stores/dashboardStore'

export default function ChatFab() {
  const { chatOpen, toggleChat, selectedEquipmentId } = useDashboardStore()
  const [input, setInput] = useState('')

  return (
    <>
      {/* FAB 버튼 */}
      <button
        onClick={toggleChat}
        className="flex items-center justify-center gap-1 font-semibold text-xs rounded-full transition-all"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 9999,
          width: '48px',
          height: '48px',
          background: 'var(--blue3)',
          color: '#fff',
          boxShadow: '0 4px 16px rgba(45,114,210,0.5)',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        {chatOpen ? '✕' : 'AI'}
      </button>

      {/* 팝업 */}
      {chatOpen && (
        <div
          className="flex flex-col"
          style={{
            position: 'fixed',
            bottom: '84px',
            right: '24px',
            zIndex: 9000,
            width: '340px',
            height: '420px',
            background: 'var(--dg1)',
            border: '1px solid var(--border-mid)',
            borderRadius: '8px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          }}
        >
          {/* 팝업 헤더 */}
          <div
            className="flex items-center px-3 py-2 text-xs font-semibold"
            style={{
              borderBottom: '1px solid var(--border-subtle)',
              color: 'var(--gray4)',
            }}
          >
            AI 어시스턴트
            {selectedEquipmentId && (
              <span
                className="ml-auto font-mono text-xs"
                style={{ color: 'var(--blue4)' }}
              >
                {selectedEquipmentId}
              </span>
            )}
          </div>

          {/* 메시지 영역 */}
          <div
            className="flex-1 p-3 overflow-y-auto text-xs"
            style={{ color: 'var(--gray4)' }}
          >
            <div
              className="p-2 rounded"
              style={{ background: 'var(--dg3)' }}
            >
              안녕하세요! 설비 이상이나 정비 절차에 대해 질문해 주세요.
            </div>
          </div>

          {/* 입력 영역 */}
          <div
            className="flex items-center gap-2 p-2"
            style={{ borderTop: '1px solid var(--border-subtle)' }}
          >
            <input
              className="flex-1 bg-transparent text-xs outline-none px-2 py-1 rounded"
              style={{
                color: 'var(--gray5)',
                background: 'var(--dg3)',
                border: '1px solid var(--border-mid)',
              }}
              placeholder="질문을 입력하세요..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  // TODO Phase 3: sendChatMessage(input, selectedEquipmentId)
                  setInput('')
                }
              }}
            />
            <button
              className="text-xs px-2 py-1 rounded"
              style={{
                background: 'var(--blue3)',
                color: '#fff',
                border: 'none',
                cursor: 'pointer',
              }}
              onClick={() => setInput('')}
            >
              전송
            </button>
          </div>
        </div>
      )}
    </>
  )
}
