---
name: frontend-code-review
description: 프론트엔드 전체 코드 점검 결과 및 수정 이력 (2026-03-17)
type: project
---

## 프론트엔드 코드 점검 (2026-03-17)

### 검토 범위
13개 파일, 22개 이슈 발견 (Critical 7 / High 7 / Medium 6 / Low 2)

### 수정 완료 (Critical)

| # | 문제 | 파일 | 해결 |
|---|---|---|---|
| 1 | 검정화면 크래시 — ErrorBoundary 없음 | AppShell.tsx | ErrorBoundary 6개 영역 독립 감싸기 |
| 2 | 40+ 동시 요청 — 커넥션 풀 고갈 | App.tsx | staleTime: 5s, refetchOnWindowFocus: false |
| 3 | sortedAlarms[0] 접근 크래시 | Sidebar.tsx | optional chaining ?.timestamp |
| 4 | ChatPanel 응답 undefined | ChatPanel.tsx | res?.content ?? fallback |
| 5 | retry: false 즉사 | AiDetailPanel.tsx | retry: 1 (1회 재시도) |
| 6 | 쿼리 중복 | useEquipmentData.ts | 공통 훅 + POLL_5S/POLL_10S/LAZY 전략 |
| 7 | 메모리 누수 — useEffect timeout | Sidebar.tsx | clearTimeout 보장 |

### 미수정 (향후)

| # | 심각도 | 문제 | 해결 방향 |
|---|---|---|---|
| 8 | HIGH | 인라인 스타일 객체 → 불필요한 리렌더 | 상수로 추출 (일부 완료) |
| 9 | HIGH | 하드코딩 EQ_IDS 4곳 | 백엔드 equipment 목록 API에서 동적 로드 |
| 10 | MEDIUM | 에러 UI 없음 (로딩만 표시) | isError 상태 + 에러 메시지 표시 |
| 11 | MEDIUM | 타입 불일치 (predicted_failure_code) | null 가드 강화 |
| 12 | MEDIUM | 접근성 (aria-label 없음) | 버튼/인터랙션 요소에 추가 |
| 13 | MEDIUM | 일관성 없는 retry/staleTime | useEquipmentData.ts 훅으로 통일 중 |
| 14 | LOW | Mock fallback (jitter) | API forecast_score 연결 후 제거 |

### 커넥션 풀 고갈 근본 원인
- 프론트 5초 폴링 × 3설비 × 6종 API = 18+ 동시 요청
- staleTime: 0 → 탭 전환마다 전체 재요청
- health 체크 conn.close() → 풀 커넥션 파괴 (백엔드 수정 완료)
- SimpleConnectionPool → ThreadedConnectionPool (백엔드 수정 완료)

**Why:** 초기 설계에서 쿼리 최적화 없이 컴포넌트마다 독립 쿼리를 사용
**How to apply:** 새 쿼리 추가 시 useEquipmentData.ts 훅 활용, retry: 1 + staleTime 필수 설정
