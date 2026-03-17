// ============================================================
// ChatPanel — 우측 고정 AI 어시스턴트 (모던 챗봇 디자인)
// ============================================================

import { useState, useRef, useEffect } from 'react'
import { api } from '@/lib/api/client'
import type { ChatMessage } from '@/types'

const sans = "'IBM Plex Sans', 'Noto Sans KR', sans-serif"
const mono = "'IBM Plex Mono', monospace"

// AI 아바타 아이콘
function AiAvatar() {
  return (
    <div style={{
      width: '28px', height: '28px', borderRadius: '50%',
      background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
      boxShadow: '0 0 12px rgba(99,102,241,0.3)',
    }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round"/>
      </svg>
    </div>
  )
}

// 코드 블록 감지 및 렌더링
function MessageContent({ content }: { content: string }) {
  const parts = content.split(/(```[\s\S]*?```)/g)
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('```')) {
          const code = part.replace(/```\w*\n?/, '').replace(/```$/, '').trim()
          return (
            <pre key={i} style={{
              background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '6px', padding: '8px 10px', margin: '6px 0',
              fontSize: '10px', fontFamily: mono, color: 'var(--cyan)',
              overflowX: 'auto', whiteSpace: 'pre-wrap',
            }}>
              {code}
            </pre>
          )
        }
        return <span key={i}>{part}</span>
      })}
    </>
  )
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: '안녕하세요! CNC 관제 AI 어시스턴트입니다.\n설비 상태, 이상감지, 정비 절차, 부품 재고 등에 대해 질문해 주세요.',
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
      setMessages((prev) => [...prev, { role: 'assistant', content: res?.content ?? '응답을 받지 못했습니다.', timestamp: res?.timestamp ?? new Date().toISOString() }])
    } catch {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '답변을 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
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
      {/* 내부 카드 — 그라데이션 배경 */}
      <div style={{
        flex: 1,
        background: 'linear-gradient(180deg, #0c1529 0%, #0a0f1c 30%, #0d1225 100%)',
        border: '1px solid var(--border-mid)',
        borderRadius: '8px',
        boxShadow: '0 2px 12px rgba(0,0,0,0.3)',
        overflow: 'hidden', display: 'flex', flexDirection: 'column',
      }}>
        {/* 헤더 — 그라데이션 */}
        <div className="flex items-center gap-2.5 px-4 py-3 flex-shrink-0" style={{
          background: 'linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(6,182,212,0.08) 100%)',
          borderBottom: '1px solid rgba(99,102,241,0.15)',
        }}>
          <AiAvatar />
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--gray5)', fontFamily: sans }}>AI Assistant</div>
            <div style={{ fontSize: '9px', color: 'var(--gray3)', fontFamily: sans }}>CNC 관제 시스템</div>
          </div>
          <div className="ml-auto flex items-center gap-1">
            <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--green5)', animation: 'pulse-dot 2s ease-in-out infinite' }} />
            <span style={{ fontSize: '8px', color: 'var(--green5)', fontFamily: sans, fontWeight: 500 }}>온라인</span>
          </div>
        </div>

        {/* 메시지 영역 */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: '14px 12px',
          display: 'flex', flexDirection: 'column', gap: '12px',
        }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: 'flex',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              gap: '8px', alignItems: 'flex-start',
            }}>
              {/* AI 아바타 (assistant만) */}
              {msg.role === 'assistant' && <AiAvatar />}

              {/* 말풍선 */}
              <div style={{
                maxWidth: '82%', padding: '10px 14px',
                borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, rgba(99,102,241,0.25) 0%, rgba(6,182,212,0.15) 100%)'
                  : 'rgba(255,255,255,0.04)',
                border: msg.role === 'user'
                  ? '1px solid rgba(99,102,241,0.3)'
                  : '1px solid rgba(255,255,255,0.06)',
                color: 'var(--gray5)',
                fontSize: '11px', lineHeight: '1.7', whiteSpace: 'pre-wrap', fontFamily: sans,
              }}>
                <MessageContent content={msg.content} />
              </div>
            </div>
          ))}

          {/* 로딩 인디케이터 */}
          {loading && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
              <AiAvatar />
              <div style={{
                padding: '10px 14px', borderRadius: '14px 14px 14px 4px',
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.06)',
              }}>
                <div className="flex items-center gap-1.5">
                  {[0, 1, 2].map(j => (
                    <div key={j} style={{
                      width: '5px', height: '5px', borderRadius: '50%',
                      background: 'var(--cyan)', opacity: 0.6,
                      animation: `pulse-dot 1.2s ease-in-out ${j * 0.2}s infinite`,
                    }} />
                  ))}
                  <span style={{ fontSize: '10px', color: 'var(--gray3)', fontFamily: sans, marginLeft: '4px' }}>분석 중</span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* 입력 영역 */}
        <div style={{
          padding: '12px', flexShrink: 0,
          background: 'rgba(255,255,255,0.02)',
          borderTop: '1px solid rgba(99,102,241,0.1)',
        }}>
          <div style={{
            display: 'flex', gap: '8px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(99,102,241,0.15)',
            borderRadius: '20px',
            padding: '4px 4px 4px 14px',
            transition: 'all 0.2s',
          }}>
            <input
              style={{
                flex: 1, background: 'transparent', border: 'none',
                fontSize: '11px', color: 'var(--gray5)', outline: 'none', fontFamily: sans,
                padding: '6px 0',
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
                width: '32px', height: '32px', borderRadius: '50%',
                background: loading || !input.trim()
                  ? 'rgba(255,255,255,0.05)'
                  : 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
                border: 'none',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                flexShrink: 0,
                boxShadow: loading || !input.trim() ? 'none' : '0 0 8px rgba(99,102,241,0.3)',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
