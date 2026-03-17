// ============================================================
// ChatPanel — 우측 고정 AI 어시스턴트 사이드바
// 전체 관제 시스템을 관장하는 종합 챗봇
// ============================================================

import { useState, useRef, useEffect } from 'react'
import { api } from '@/lib/api/client'
import type { ChatMessage } from '@/types'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: '설비 상태, 이상감지 현황, 정비 절차, 부품 재고 등 전체 관제에 대해 질문해 주세요.',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', content: text, timestamp: new Date().toISOString() }])
    setInput('')
    setLoading(true)

    try {
      const res = await api.post<{ content: string; timestamp: string; references: string[] }>(
        '/chat', { message: text }
      )
      setMessages((prev) => [...prev, { role: 'assistant', content: res.content, timestamp: res.timestamp }])
    } catch {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '답변을 가져오는 중 오류가 발생했습니다.',
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col flex-shrink-0 overflow-hidden" style={{
      width: '300px', background: 'var(--dg1)',
      borderLeft: '1px solid var(--border-mid)',
      padding: '6px 8px 12px 4px',
    }}>
      {/* 내부 카드 */}
      <div style={{
        flex: 1, background: 'var(--dg2)', border: '1px solid var(--border-mid)',
        borderRadius: '3px', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        overflow: 'hidden', display: 'flex', flexDirection: 'column',
      }}>
        {/* 헤더 */}
        <div className="flex items-center gap-2 px-4 py-2 flex-shrink-0" style={{
          borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)',
        }}>
          <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--cyan)' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--gray4)', fontFamily: sans }}>
            AI 어시스턴트
          </span>
        </div>

        {/* 메시지 영역 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {messages.map((msg, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{
                maxWidth: '88%', padding: '8px 12px',
                borderRadius: msg.role === 'user' ? '3px 3px 0 3px' : '3px 3px 3px 0',
                background: msg.role === 'user' ? 'rgba(0,212,255,0.08)' : 'var(--dg3)',
                border: msg.role === 'user' ? '1px solid rgba(0,212,255,0.15)' : '1px solid var(--border-subtle)',
                color: msg.role === 'user' ? 'var(--gray5)' : 'var(--gray4)',
                fontSize: '11px', lineHeight: '1.6', whiteSpace: 'pre-wrap', fontFamily: sans,
              }}>
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ padding: '8px 12px', borderRadius: '3px', background: 'var(--dg3)', border: '1px solid var(--border-subtle)', color: 'var(--gray2)', fontSize: '10px', fontFamily: sans }}>
                분석 중...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* 입력 영역 */}
        <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border-mid)', display: 'flex', gap: '8px', flexShrink: 0, background: 'rgba(255,255,255,0.01)' }}>
          <input
            style={{
              flex: 1, background: 'var(--dg3)', border: '1px solid var(--border-mid)',
              borderRadius: '2px', padding: '8px 10px', fontSize: '11px',
              color: 'var(--gray5)', outline: 'none', fontFamily: sans,
            }}
            placeholder="질문을 입력하세요..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void sendMessage() } }}
            disabled={loading}
          />
          <button
            onClick={() => void sendMessage()}
            disabled={loading || !input.trim()}
            style={{
              background: loading || !input.trim() ? 'var(--dg3)' : 'rgba(0,212,255,0.08)',
              border: loading || !input.trim() ? '1px solid var(--border-subtle)' : '1px solid rgba(0,212,255,0.25)',
              borderRadius: '2px', padding: '8px 14px',
              color: loading || !input.trim() ? 'var(--gray2)' : 'var(--cyan)',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              fontSize: '10px', fontWeight: 600, fontFamily: sans,
              transition: 'all 0.15s', flexShrink: 0,
            }}
          >
            전송
          </button>
        </div>
      </div>
    </div>
  )
}
