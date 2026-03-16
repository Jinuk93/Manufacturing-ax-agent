// ============================================================
// ChatFab — 챗봇 FAB 버튼 (우하단 fixed)
// /api/chat 엔드포인트와 실제 연동
// ============================================================

import { useState, useRef, useEffect } from 'react'
import { useDashboardStore } from '@/stores/dashboardStore'
import { api } from '@/lib/api/client'
import type { ChatMessage } from '@/types'

export default function ChatFab() {
  const { chatOpen, toggleChat, selectedEquipmentId } = useDashboardStore()
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: '안녕하세요! 설비 이상, 정비 절차, 부품 재고에 대해 질문해 주세요.',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // 메시지 추가 시 스크롤 하단으로
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await api.post<{ content: string; timestamp: string; references: string[] }>(
        '/chat',
        { message: text, equipment_id: selectedEquipmentId ?? undefined }
      )
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: res.content,
        timestamp: res.timestamp,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '답변을 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* FAB 버튼 — 56px 파란 원형 */}
      <button
        onClick={toggleChat}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 9999,
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: chatOpen ? 'var(--dg3)' : 'var(--blue3)',
          border: chatOpen ? '1px solid var(--border-mid)' : 'none',
          color: '#fff',
          cursor: 'pointer',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2px',
          boxShadow: chatOpen ? 'none' : '0 4px 20px rgba(45,114,210,0.55)',
          transition: 'all 0.2s',
        }}
      >
        {chatOpen ? (
          /* 닫기 X */
          <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
            <path d="M2 2l14 14M16 2L2 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : (
          /* 챗 버블 아이콘 */
          <>
            <svg width="22" height="20" viewBox="0 0 22 20" fill="none">
              <path
                d="M2 2h18v13H2V2z"
                stroke="white" strokeWidth="1.5" strokeLinejoin="round" fill="rgba(255,255,255,0.15)"
              />
              <circle cx="7" cy="8.5" r="1.2" fill="white"/>
              <circle cx="11" cy="8.5" r="1.2" fill="white"/>
              <circle cx="15" cy="8.5" r="1.2" fill="white"/>
              <path d="M6 15l-4 3V15" fill="white"/>
            </svg>
            <span style={{ fontSize: '8px', fontWeight: 700, letterSpacing: '0.05em' }}>AI</span>
          </>
        )}
      </button>

      {/* 팝업 창 */}
      {chatOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '92px',
            right: '24px',
            zIndex: 9000,
            width: '360px',
            height: '560px',
            background: 'var(--dg1)',
            border: '1px solid var(--border-mid)',
            borderRadius: '10px',
            boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* 헤더 */}
          <div
            style={{
              padding: '12px 14px',
              borderBottom: '1px solid var(--border-subtle)',
              background: 'linear-gradient(135deg, rgba(45,114,210,0.15) 0%, transparent 100%)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: 'var(--blue4)',
                boxShadow: '0 0 6px rgba(76,144,240,0.7)',
              }}
            />
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--gray5)' }}>
              AI 어시스턴트
            </span>
            {selectedEquipmentId && (
              <span
                style={{
                  marginLeft: 'auto',
                  fontSize: '10px',
                  fontFamily: "'JetBrains Mono', monospace",
                  color: 'var(--blue4)',
                  background: 'rgba(45,114,210,0.15)',
                  padding: '2px 6px',
                  borderRadius: '4px',
                }}
              >
                {selectedEquipmentId}
              </span>
            )}
          </div>

          {/* 메시지 영역 */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '8px 12px',
                    borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                    background: msg.role === 'user' ? 'var(--blue3)' : 'var(--dg3)',
                    color: msg.role === 'user' ? '#fff' : 'var(--gray5)',
                    fontSize: '12px',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  style={{
                    padding: '8px 12px',
                    borderRadius: '12px 12px 12px 2px',
                    background: 'var(--dg3)',
                    color: 'var(--gray3)',
                    fontSize: '12px',
                  }}
                >
                  분석 중...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* 입력 영역 */}
          <div
            style={{
              padding: '10px 12px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              gap: '8px',
              flexShrink: 0,
            }}
          >
            <input
              style={{
                flex: 1,
                background: 'var(--dg3)',
                border: '1px solid var(--border-mid)',
                borderRadius: '6px',
                padding: '7px 10px',
                fontSize: '12px',
                color: 'var(--gray5)',
                outline: 'none',
              }}
              placeholder="질문을 입력하세요..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  void sendMessage()
                }
              }}
              disabled={loading}
            />
            <button
              onClick={() => void sendMessage()}
              disabled={loading || !input.trim()}
              style={{
                background: loading || !input.trim() ? 'var(--dg3)' : 'var(--blue3)',
                border: 'none',
                borderRadius: '6px',
                padding: '7px 12px',
                color: '#fff',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                fontSize: '12px',
                fontWeight: 600,
                transition: 'background 0.15s',
                flexShrink: 0,
              }}
            >
              전송
            </button>
          </div>
        </div>
      )}
    </>
  )
}
