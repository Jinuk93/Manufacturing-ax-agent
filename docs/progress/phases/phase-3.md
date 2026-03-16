# Phase 3: Build & Validate — 계획 및 일일 로그

> Phase 3의 목표: Phase 2 아키텍처 설계를 실제로 구현하고, 엔드-투-엔드 파이프라인이 동작함을 확인한다.

---

## 목표

Phase 2의 "청사진"을 코드로 변환하여:
1. F1~F5 백엔드 파이프라인이 실제 DB 데이터로 동작하는지 확인
2. F6 프론트엔드 대시보드가 백엔드와 연동되어 실시간 상태를 표시하는지 확인
3. OpenAI LLM 연동으로 실제 조치 권고가 생성되는지 확인

---

## 산출물 목록

| # | 항목 | 경로 | 내용 | 상태 |
|---|------|------|------|------|
| 1 | DB 초기화 스크립트 | `backend/scripts/` | PostgreSQL 10테이블 DDL + 데이터 로드 | ✅ 완료 |
| 2 | Neo4j 그래프 초기화 | `backend/scripts/load_neo4j.py` | 120+ 노드, 관계 9종, pgvector 47청크 | ✅ 완료 |
| 3 | F1 센서 수집 | `backend/app/services/` | 5초 폴링 → sensor_readings INSERT | ✅ 완료 |
| 4 | F2 이상탐지 | `backend/app/services/anomaly_detector.py` | Isolation Forest 모델 추론 | ✅ 완료 |
| 5 | F3 IT/OT 동기화 | `backend/app/services/itot_sync.py` | MES/Maintenance/ERP 통합 조회 | ✅ 완료 |
| 6 | F4 GraphRAG | `backend/app/services/graphrag.py` | Neo4j Cypher + pgvector 하이브리드 검색 | ✅ 완료 |
| 7 | F5 LLM 판단 | `backend/app/services/llm_agent.py` | OpenAI GPT-4o-mini + 규칙 기반 폴백 | ✅ 완료 |
| 8 | FastAPI 라우터 | `backend/app/api/routes.py` | 13개 엔드포인트 실제 서비스 연결 | ✅ 완료 |
| 9 | React 프론트엔드 | `frontend/src/` | React 18 + Vite + TypeScript + Tailwind v3 | ✅ 완료 |
| 10 | 프론트엔드-백엔드 연동 | `frontend/src/lib/api/` | 실제 API 연동, 타입 정합 | ✅ 완료 |
| 11 | Docker Compose | `docker-compose.yml` | PostgreSQL + Neo4j 통합 실행 환경 | ✅ 완료 |

---

## 기술 스택

### 백엔드
- FastAPI (Python) + uvicorn
- PostgreSQL 16 (TimescaleDB + pgvector 확장)
- Neo4j 5 (그래프 DB)
- Isolation Forest (이상탐지 모델)
- OpenAI GPT-4o-mini (LLM 판단)
- SentenceTransformer `paraphrase-multilingual-MiniLM-L12-v2` (임베딩)
- Docker Compose

### 프론트엔드
- React 18 + Vite 6 + TypeScript
- Tailwind CSS v3 + PostCSS
- shadcn/ui (부분)
- TanStack Query v5 (서버 상태)
- Zustand (클라이언트 상태)
- Recharts (센서 시계열 차트)
- React Router v6

---

## 최종 확인된 데이터 현황

| 테이블 | 행 수 | 비고 |
|--------|-------|------|
| sensor_readings | 25,286 | KAMP CSV CNC-001/002/003 |
| equipment | 3 | CNC-001, CNC-002, CNC-003 |
| mes_work_orders | 18 | 합성 MES 데이터 |
| maintenance_events | 39 | 합성 정비 이력 |
| erp_inventory | 35 | 합성 ERP 재고 스냅샷 |
| document_embeddings | 47 | 정비 매뉴얼 청크 임베딩 |
| Neo4j 노드 | 120+ | Equipment 3, FailureCode 4, Part 5, Sensor 39, Document 12, WorkOrder 18, MaintenanceAction 39 |

---

## 검증된 엔드포인트

| 엔드포인트 | 상태 | 비고 |
|-----------|------|------|
| GET /api/health | ✅ | `{postgres:true, neo4j:true}` |
| GET /api/f6/summary | ✅ | CNC-001/002/003 실제 anomaly_score 반환 |
| GET /api/f6/sensors/{id} | ✅ | 2024 CSV 타임스탬프 호환 (LIMIT 300) |
| GET /api/f6/anomaly/{id} | ✅ | 최신 이상탐지 결과 |
| GET /api/f6/action/{id} | ✅ | 온디맨드 F2→F3→F4→F5 파이프라인 실행 |
| GET /api/f6/alarms | ✅ | is_anomaly=true 건 목록 |
| GET /api/f6/work-order/{id} | ✅ | 작업지시 + 재고 현황 |
| POST /api/f5/generate-action | ✅ | LLM 조치 권고 생성 |

---

## 해결한 주요 이슈

| # | 문제 | 원인 | 해결 |
|---|------|------|------|
| 1 | 프론트엔드 검은 화면 | `equipmentList?.map is not a function` 크래시 | TanStack Query v5: `placeholderData:[]` 무효 → `data=[]` 기본값 패턴 |
| 2 | 센서 시계열 `series:[]` | CSV 2024 타임스탬프 vs `NOW()-1hour` 필터 불일치 | 시간 필터 제거, `ORDER BY timestamp DESC LIMIT 300` |
| 3 | `/api/f6/action` null 반환 | TODO 스텁 | 온디맨드 F2→F3→F4→F5 파이프라인으로 구현 |
| 4 | `@apply border-border` CSS 오류 | shadcn/ui Tailwind v4 전용 유틸리티 | CSS 변수 직접 참조로 교체 |
| 5 | frontend `.git` 서브모듈 | npm create vite가 내부에 .git 생성 | `git rm --cached frontend && rm -rf frontend/.git` |
| 6 | SentenceTransformer 중복 로드 | 요청마다 재초기화 | 싱글턴 패턴으로 앱 기동 시 1회만 로드 |
| 7 | WorkOrderOverlay hooks 위반 | `.map()` 안에서 `useQuery` 호출 | 3개 고정 hook으로 분리 |

---

## 프론트엔드 컴포넌트 구조

```
frontend/src/
├── App.tsx                          # QueryClient + QueryClientProvider
├── index.css                        # Palantir 디자인 토큰 + keyframes
├── types/index.ts                   # 백엔드 Pydantic 스키마와 1:1 대응
├── stores/dashboardStore.ts         # Zustand: 선택 설비, 오버레이, 챗봇
├── lib/api/
│   ├── client.ts                    # fetch wrapper
│   └── endpoints.ts                 # 6개 API 함수
└── components/
    ├── layout/
    │   ├── AppShell.tsx             # [Topbar] / [Sidebar|AiDetail|Monitoring]
    │   ├── Topbar.tsx               # AX Manufacturing 로고 + STOP 배너 + 오버레이 버튼
    │   ├── Sidebar.tsx              # 설비 상태 목록 (5초 폴링)
    │   └── AiDetailPanel.tsx        # F2 게이지 + F5 LLM 리포트 + 부품 현황
    └── dashboard/
        ├── MonitoringCenter.tsx     # Recharts 센서 차트 + 파이프라인 상태
        ├── ChatFab.tsx              # 우하단 FAB 챗봇
        ├── WorkOrderOverlay.tsx     # 작업현황 슬라이드다운 (실제 API)
        └── InventoryOverlay.tsx     # 재고현황 슬라이드다운 (실제 API)
```

---

## 디자인 시스템 (Palantir 토큰)

| 토큰 | 값 | 용도 |
|------|-----|------|
| `--black` | `#090C10` | 배경 최하단 |
| `--dg1` | `#0F1318` | 사이드바/헤더 |
| `--dg2` | `#161B22` | 메인 영역 |
| `--dg3` | `#1E2530` | 카드/인풋 |
| `--blue3` | `#2D72D2` | 강조/액션 |
| `--blue4` | `#4C90F0` | 링크/선택 |
| Font 1 | Inter | 본문/레이블 |
| Font 2 | JetBrains Mono | ID/수치/코드 |

---

## 일일 로그

### Day 1 (2026-03-17)

**목표:** Phase 2 → Phase 3 전환, React 프론트엔드 세팅

- Vite 6 + React 18 + TypeScript 프로젝트 생성
- Tailwind CSS v3 + PostCSS 세팅 (shadcn/ui v4 호환 이슈 → v3 수동 설정)
- Palantir 디자인 토큰 CSS 변수 정의
- AppShell 3-Pane 레이아웃 구현 (Sidebar 200px / AiDetailPanel 320px / MonitoringCenter flex)
- Zustand 대시보드 스토어 생성
- TanStack Query v5 설정
- 기본 컴포넌트 골격 생성 (Topbar, Sidebar, AiDetailPanel, ChatFab, 오버레이)
- frontend `.git` 서브모듈 이슈 해결

**산출물:**
- `frontend/` React 프로젝트 초기 구조
- `frontend/src/index.css` — 디자인 토큰 + stop-banner keyframes
- `frontend/src/stores/dashboardStore.ts`
- `frontend/src/App.tsx`

### Day 2 (2026-03-17) — 백엔드 실제 연동 (Step A)

**목표:** 백엔드 완전 동작 확인 + 프론트엔드-백엔드 연동

**Step A — 백엔드 검증:**
- Docker `ax-postgres`, `ax-neo4j` 헬스 확인
- `/api/health` → `{postgres:true, neo4j:true}` ✅
- `/api/f6/summary` → CNC-001/002/003 실제 anomaly_score ✅
- `/api/f6/sensors` 타임스탬프 필터 버그 수정 (2024 CSV 데이터 호환)
- `/api/f6/action` TODO 스텁 → 실제 F2→F3→F4→F5 온디맨드 파이프라인 구현

**Step B — 프론트엔드 실제 연동:**
- `types/index.ts` — 백엔드 Pydantic과 1:1 정합
- `endpoints.ts` — 6개 실제 API 함수
- `Sidebar.tsx` — TanStack Query v5 `data=[]` 버그 수정
- `Topbar.tsx` — AX Manufacturing 로고 + 실제 알람 기반 STOP 배너
- `AiDetailPanel.tsx` — getActionReport 연동, 실제 LLM 리포트 표시
- `MonitoringCenter.tsx` — Recharts 센서 시계열 차트 구현
- `WorkOrderOverlay.tsx` / `InventoryOverlay.tsx` — 실제 API 연동

**브랜치:** `feature/frontend-backend-integration`

**산출물:**
- `backend/app/api/routes.py` (수정)
- `frontend/src/types/index.ts` (전면 재작성)
- `frontend/src/lib/api/endpoints.ts` (6개 실제 엔드포인트)
- `frontend/src/components/**` (실제 API 연동 완료)
