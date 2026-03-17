// ============================================================
// ErrorBoundary — 컴포넌트 크래시 시 검정화면 방지
// ============================================================

import { Component } from 'react'
import type { ReactNode, ErrorInfo } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  name?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[ErrorBoundary${this.props.name ? ` - ${this.props.name}` : ''}] 크래시:`, error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div style={{
          padding: '16px',
          background: 'rgba(248,113,113,0.06)',
          border: '1px solid rgba(248,113,113,0.15)',
          borderRadius: '4px',
          margin: '8px',
        }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#f87171', marginBottom: '4px' }}>
            컴포넌트 오류 발생
          </div>
          <div style={{ fontSize: '10px', color: '#94a3b8', lineHeight: '1.4' }}>
            {this.state.error?.message ?? '알 수 없는 오류'}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              marginTop: '8px', fontSize: '10px', padding: '4px 10px',
              background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.2)',
              borderRadius: '3px', color: '#f87171', cursor: 'pointer',
            }}
          >
            다시 시도
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
