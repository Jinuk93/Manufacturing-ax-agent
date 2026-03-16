# ADR-006: 프론트엔드 기술 스택 선택

## Status
Decided

## Context

F6 대시보드(관제 UI) 구현을 위해 프론트엔드 기술 스택을 결정해야 한다.
Phase 2 UI 설계(ui-design.md)에서 Next.js 15를 초안으로 작성했으나,
리뷰 과정에서 1인 개발 입문자에게 학습 곡선이 과하다는 피드백이 제기되었다.
(open-items #11)

대시보드의 특성:
- 페이지 2개 (전체 개요 `/`, 설비 상세 `/equipment/:id`)
- 내부 관제 시스템 — SEO 불필요
- API에서 데이터를 받아 클라이언트에서 렌더링 — SSR 불필요
- 5초 폴링 기반 실시간 갱신

## Options Considered

1. **Option A — Next.js 15 + TypeScript + Tailwind + shadcn/ui**
   - 장점: 파일 기반 라우팅, SSR/ISR, 실무 경험 측면에서 학습 가치 높음
   - 단점: SSR·SEO가 불필요한 내부 시스템에서 핵심 기능을 사용하지 않음. Node.js 환경 별도 구성 필요. 1인 입문자 학습 부담 큼
   - 결과물 수준: 실제 제품 수준

2. **Option B — React 18 + Vite + TypeScript + Tailwind + shadcn/ui**
   - 장점: SPA로 충분한 요구사항에 딱 맞음. Next.js 대비 설정 단순. shadcn/ui·TanStack Query·Zustand 동일하게 사용 가능
   - 단점: 라우팅을 React Router로 직접 구성해야 함 (2페이지라 복잡도 낮음)
   - 결과물 수준: 실제 제품 수준

3. **Option C — HTML + Plotly.js (현재 data-review.html 방식)**
   - 장점: 학습 비용 없음, 즉시 시작 가능
   - 단점: 컴포넌트 재사용 불가, 규모 커지면 유지보수 어려움, 실시간 폴링 관리 복잡
   - 결과물 수준: 프로토타입 수준

## Decision

**Option B — React 18 + Vite** 를 선택한다.

확정 스택:

| 항목 | 선택 |
|------|------|
| 프레임워크 | React 18 + Vite |
| 언어 | TypeScript |
| 스타일 | Tailwind CSS |
| 컴포넌트 | shadcn/ui |
| 차트 | Recharts |
| 데이터 폴링 | TanStack Query (React Query) |
| 전역 상태 | Zustand |
| 라우팅 | React Router v6 |

## Reasoning

- **SSR/SEO 불필요:** 내부 관제 시스템이므로 Next.js의 핵심 강점(SSR, ISR, SEO)이 무의미함
- **페이지 2개:** 파일 기반 라우팅의 이점이 없음. React Router로 충분
- **동일한 컴포넌트 생태계:** shadcn/ui, TanStack Query, Zustand, Recharts는 Next.js 없이도 동일하게 사용 가능 — ui-design.md 설계를 그대로 구현 가능
- **학습 효율:** React + Vite는 내부 대시보드·관제 UI에서 업계 표준. 1인 입문자가 핵심(React 상태관리·폴링·컴포넌트 설계)에 집중할 수 있음
- **속도:** Vite의 빠른 HMR로 개발 생산성 향상

## Consequences

- ui-design.md의 `app/` 디렉토리 구조를 `src/` 기반 Vite 구조로 수정 필요
  - `app/page.tsx` → `src/pages/Overview.tsx`
  - `app/equipment/[id]/page.tsx` → `src/pages/EquipmentDetail.tsx`
  - 라우팅: `<Routes>` / `<Route>` (React Router v6)
- Next.js 전용 기능(`useRouter`, `next/image`, `server actions` 등) 사용 불가 — 해당 없음
- Phase 3 구현 시 `frontend/` 디렉토리에 Vite 프로젝트 초기화 필요 (`npm create vite@latest`)
