# F6 대시보드 UI 설계서

> **기술 스택:** Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui + Recharts
> **대상:** F6 관제 대시보드 — CNC 3대의 실시간 상태 + LLM 조치 리포트
> **갱신 주기:** 5초 폴링 (TanStack Query)

> ⚠️ **기술 스택 결정 주의 (open-items #11 연결)**
> Next.js 15 + TypeScript + Tailwind + shadcn/ui + Recharts + TanStack Query + Zustand 조합은
> 1인 개발 입문자에게 학습 곡선이 높을 수 있습니다.
> 현재 `data-review.html` 처럼 순수 HTML + Plotly.js 방식도 F6 MVP로는 충분히 구현 가능한 대안입니다.
> **Phase 3 착수 전 ADR-006(프론트엔드 전략)으로 최종 확정 필요.**
> (open-items #11 참조)

---

## 1. 페이지 구조 (라우팅)

```
app/
├── layout.tsx          ← 공통 레이아웃 (헤더 포함)
├── page.tsx            ← / : 전체 설비 개요 (메인)
└── equipment/
    └── [id]/
        └── page.tsx    ← /equipment/CNC-001 : 설비 상세
```

**이동 흐름:**
```
/ (전체 개요)
  └─ 설비 카드 클릭
      └─ /equipment/CNC-001 (상세 페이지)
          └─ 뒤로가기 → 전체 개요
```

---

## 2. 전체 레이아웃

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER                                                          │
│  [로고] CNC 관제 시스템          ● PG  ● Neo4j    08:23:15 갱신  │
├──────────────────────────────────────────────────────────────────┤
│  MAIN CONTENT                                                    │
│                                                                  │
│  ─── 설비 상태 요약 ───────────────────────────────────────────  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   CNC-001    │  │   CNC-002    │  │   CNC-003    │          │
│  │   🟢 정상    │  │   🟡 경고    │  │   🟢 정상    │          │
│  │  score: 0.21 │  │  score: 0.74 │  │  score: 0.18 │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ─── 이상 알람 피드 ────────────────────────────────────────────  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🔴 08:23:01  CNC-002  SPINDLE_OVERHEAT_001  score: 0.87 │   │
│  │ 🟡 07:45:30  CNC-001  TOOL_WEAR_001  score: 0.63         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 컴포넌트 상세 설계

### 3-1. Header

```
components/layout/Header.tsx
```

| 요소 | 내용 | API |
|------|------|-----|
| 시스템명 | "CNC 관제 시스템" | 정적 |
| DB 상태 뱃지 | `● PG` `● Neo4j` (초록/빨강) | `GET /api/health` (10초) |
| 마지막 갱신 | "08:23:15 갱신" | 클라이언트 시각 |

---

### 3-2. 설비 상태 카드 (메인 페이지)

```
components/equipment/EquipmentCard.tsx
```

**레이아웃 (카드 1개):**
```
┌─────────────────────────────┐
│  CNC-002              🟡 경고 │
│                              │
│   anomaly score              │
│   ████████░░  0.74           │
│                              │
│  SPINDLE_OVERHEAT_001        │
│  확신도: 87%                  │
│                              │
│  마지막 갱신: 08:23:01        │
│  [상세 보기 →]               │
└─────────────────────────────┘
```

| 요소 | 내용 | 색상 규칙 |
|------|------|-----------|
| 상태 뱃지 | 정상 / 경고 / 위험 | 초록 / 노랑 / 빨강 |
| 프로그레스 바 | anomaly_score 시각화 | score < 0.6 초록, 0.6~0.8 노랑, ≥ 0.8 빨강 |
| 예측 고장코드 | `predicted_failure_code` | 이상 시에만 표시 |

**API:** `GET /api/f6/summary` (5초 폴링)

---

### 3-3. 이상 알람 피드

```
components/alarm/AlarmFeed.tsx
```

```
┌──────────────────────────────────────────────────────────────────┐
│ 이상 알람 피드                                          최근 20건 │
├──────────────────────────────────────────────────────────────────┤
│ 🔴 08:23:01  CNC-002  SPINDLE_OVERHEAT_001  0.87  [리포트 보기]  │
│ 🟡 07:45:30  CNC-001  TOOL_WEAR_001         0.63  [리포트 보기]  │
│ 🟡 06:12:15  CNC-003  CLAMP_PRESSURE_001    0.61  [리포트 보기]  │
└──────────────────────────────────────────────────────────────────┘
```

- 클릭 시 해당 설비 상세 페이지로 이동 + 해당 알람의 LLM 리포트 표시
- **API:** `GET /api/f6/alarms?limit=20` (5초 폴링, 3대 통합)
  - 기존 `/api/f2/history/{equipment_id}` × 3 호출 → 단일 알람 전용 엔드포인트로 통합
  - `api-design.md` #13 `/api/f6/alarms` 신규 추가 필요 (반영 완료)

---

### 3-4. 설비 상세 페이지 `/equipment/[id]`

```
app/equipment/[id]/page.tsx
```

**전체 레이아웃:**
```
┌────────────────────────────────────────────────────────────────┐
│  ← 전체 개요     CNC-002  🟡 경고  score: 0.74               │
├──────────────────────────────┬─────────────────────────────────┤
│  [센서 차트 패널]             │  [이상 점수 패널]               │
│  (좌 2/3)                    │  (우 1/3)                       │
├──────────────────────────────┴─────────────────────────────────┤
│  [작업 + 재고 패널]  (좌 1/2)  │  [LLM 조치 리포트]  (우 1/2)  │
└────────────────────────────────────────────────────────────────┘
```

---

### 3-5. 센서 차트 패널

```
components/sensor/SensorChart.tsx
```

```
┌──────────────────────────────────────────────────────────────┐
│ 실시간 센서   [X축 ▼]  [X1_CurrentFeedback ▼]  최근 1시간    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ^                                        ← 이상 구간        │
│  │         ╭──╮                    ╭──╮  ████              │
│  │    ╭────╯  ╰────────────────────╯  ╰──░░░░──            │
│  │────╯                                                     │
│  └──────────────────────────────────────────────────────→   │
│  08:00      08:10      08:20     08:23                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

| 요소 | 내용 |
|------|------|
| 축 선택 드롭다운 | X축 / Y축 / Z축 / S축 / M1 |
| 센서 선택 드롭다운 | 선택된 축의 센서 목록 |
| 이상 구간 하이라이트 | `is_anomaly=true` 구간을 배경 빨강 처리 |
| 차트 라이브러리 | Recharts `LineChart` |

**API:** `GET /api/f6/sensors/{equipment_id}` (5초 폴링)

---

### 3-6. 이상 점수 패널

```
components/anomaly/AnomalyPanel.tsx
```

```
┌─────────────────────────────┐
│ 이상 점수                    │
│                              │
│        ╭───────╮             │
│      ╭─╯  0.74 ╰─╮          │
│   ╭──╯   🟡 경고  ╰──╮      │  ← RadialBar (반원 게이지)
│   └────────────────┘         │
│                              │
│   예측 고장코드               │
│   SPINDLE_OVERHEAT_001       │
│   확신도 87%                  │
│                              │
│  ── 최근 1시간 추이 ─────────  │
│  ▂▂▂▄▄▆▆▇███                │  ← 미니 바 차트
│                              │
└─────────────────────────────┘
```

**API:** `GET /api/f6/anomaly/{equipment_id}` (5초 폴링)

---

### 3-7. 작업 + 재고 패널

```
components/work/WorkOrderPanel.tsx
```

```
┌───────────────────────────────────────────────┐
│ 작업 현황                                       │
├───────────────────────────────────────────────┤
│ WO-2024-007    우선순위: 🔴 urgent             │
│ 납기: 2024-01-22 10:30  (2시간 16분 남음)       │
│ 상태: completed                                │
├───────────────────────────────────────────────┤
│ 부품 재고                              W6 기준  │
├───────────────────────────────────────────────┤
│ P001  Endmill 6mm        ████████░░  12개      │
│ P002  Spindle Bearing    ████░░░░░░   2개  ⚠️  │  ← 재주문점 이하
│ P003  Coolant 20L        ██████████  10개      │
│ P004  Clamp Bolt Set     ███████░░░   9개      │
│ P005  Air Filter         ████████░░   5개      │
└───────────────────────────────────────────────┘
```

| 요소 | 내용 |
|------|------|
| 우선순위 색상 | normal 회색 / urgent 주황 / critical 빨강 |
| 재고 프로그레스 바 | (현재 재고 / 초기 재고) 비율 |
| ⚠️ 표시 | `stock_quantity ≤ reorder_point` 시 |
| 납기 카운트다운 | 클라이언트 타이머 |
| 작업 상태 | `completed` / `aborted` (합성 데이터 기준) |

> ⚠️ **`in_progress` 상태 없음 — Phase 3 주의 사항**
> 현재 MES 합성 CSV(`maintenance_events.csv`)의 status 값은 `completed` / `aborted` 두 가지만 존재합니다.
> UI에서 `in_progress` 표시가 필요하다면 Phase 3 시뮬레이터에서 이 상태를 생성하는 로직을 추가해야 합니다.
> MVP에서는 `completed` / `aborted` 만 처리하는 것으로 구현합니다.

**API:** `GET /api/f6/work-order/{equipment_id}` (30초 폴링)

---

### 3-8. LLM 조치 리포트 패널

```
components/llm/ActionReport.tsx
```

```
┌──────────────────────────────────────────────────────┐
│ AI 조치 리포트          08:23:05 생성   신뢰도: 85%  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  🔴  즉시 정지                               │   │  ← STOP 빨강
│  │      score ≥ 0.8 — 즉각 조치 필요            │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  조치 단계                                            │
│  ① feedrate 즉시 0으로 감속                           │
│  ② 현재 가공 중단 (안전 정지)                          │
│  ③ DOC-004 스핀들 점검 절차 실행                      │
│  ④ P002 베어링 교체 (재고 2세트 확인)                  │
│                                                      │
│  판단 근거                                            │
│  "anomaly_score 0.87, 과거 동일 고장 평균 75분 소요.  │
│   현재 urgent 작업이나 납기까지 2시간 여유 있어          │
│   즉시 정지 후 정비 권장."                             │
│                                                      │
│  필요 부품                                            │
│  P002  Spindle Bearing  1세트  [재고 있음 ✅]         │
│                                                      │
│  예상 다운타임: 75분                                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

| 요소 | 내용 | 색상 규칙 |
|------|------|-----------|
| recommendation 배너 | STOP / REDUCE / MONITOR | 빨강 / 주황 / 초록 |
| action_steps | 번호 리스트 | — |
| reasoning | 텍스트 박스 | — |
| parts_needed | in_stock true/false | ✅ / ❌ |

**API:** `GET /api/f6/action/{equipment_id}` (알람 시 갱신)

---

## 4. 전역 상태 (Zustand)

```typescript
// store/dashboardStore.ts

interface DashboardStore {
  selectedEquipmentId: string | null       // 현재 선택된 설비
  alarmList: AlarmEvent[]                  // 전체 알람 피드
  lastUpdated: Date | null                 // 마지막 갱신 시각
  dbStatus: { pg: boolean; neo4j: boolean } // 헬스 상태

  setSelectedEquipment: (id: string) => void
  addAlarm: (alarm: AlarmEvent) => void
  setDbStatus: (status: DbStatus) => void
}
```

---

## 5. 데이터 폴링 전략 (TanStack Query)

```typescript
// 폴링 주기 정의
const POLL = {
  FAST:   5_000,   // 센서, 이상탐지, 설비 요약
  MEDIUM: 30_000,  // 작업/재고
  SLOW:   10_000,  // 헬스 체크
  EVENT:  0,       // 알람 시에만 갱신 (LLM 리포트)
} as const
```

| 컴포넌트 | 엔드포인트 | 주기 |
|----------|-----------|------|
| EquipmentCard × 3 | `/api/f6/summary` | 5초 |
| AlarmFeed | `/api/f6/alarms?limit=20` | 5초 |
| SensorChart | `/api/f6/sensors/{id}` | 5초 |
| AnomalyPanel | `/api/f6/anomaly/{id}` | 5초 |
| WorkOrderPanel | `/api/f6/work-order/{id}` | 30초 |
| ActionReport | `/api/f6/action/{id}` | 이벤트 갱신 |
| Header (DB 상태) | `/api/health` | 10초 |

---

## 6. 파일 구조

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                       ← 전체 개요
│   └── equipment/
│       └── [id]/
│           └── page.tsx               ← 설비 상세
│
├── components/
│   ├── layout/
│   │   └── Header.tsx
│   ├── equipment/
│   │   ├── EquipmentCard.tsx
│   │   └── EquipmentGrid.tsx
│   ├── alarm/
│   │   └── AlarmFeed.tsx
│   ├── sensor/
│   │   └── SensorChart.tsx
│   ├── anomaly/
│   │   └── AnomalyPanel.tsx
│   ├── work/
│   │   └── WorkOrderPanel.tsx
│   └── llm/
│       └── ActionReport.tsx
│
├── lib/
│   ├── api.ts                         ← fetch 래퍼 함수
│   └── utils.ts                       ← score → status 변환 등
│
├── store/
│   └── dashboardStore.ts              ← Zustand 전역 상태
│
├── types/
│   └── api.ts                         ← API 응답 TypeScript 타입
│
└── hooks/
    ├── useEquipmentSummary.ts         ← TanStack Query 훅
    ├── useSensorData.ts
    ├── useAnomalyData.ts
    └── useWorkOrder.ts
```

---

## 7. 색상 / 디자인 시스템

| 상태 | 색상 (Tailwind) | 사용 위치 |
|------|----------------|-----------|
| 정상 | `green-500` | 상태 뱃지, score < 0.6 |
| 경고 | `yellow-400` | 상태 뱃지, 0.6 ≤ score < 0.8 |
| 위험 | `red-500` | 상태 뱃지, score ≥ 0.8 |
| 배경 | `gray-950` | 전체 배경 (다크 테마) |
| 카드 | `gray-900` | 카드 배경 |
| 테두리 | `gray-800` | 카드/구분선 |
| 텍스트 주 | `gray-100` | 주요 텍스트 |
| 텍스트 보조 | `gray-400` | 부가 설명 |

**테마:** 다크 모드 단일 (현장 관제 환경 특성상)

---

## 8. 미결 / Phase 3 결정 사항

| # | 항목 | 현재 상태 |
|---|------|-----------|
| UI-1 | LLM 리포트 실시간 스트리밍 (SSE) vs 완료 후 표시 | Phase 3 결정 |
| UI-2 | 알람 사운드 / 브라우저 알림 추가 여부 | Phase 3 결정 |
| UI-3 | 이상 이력 차트 기간 선택 (1h / 6h / 24h) | Phase 3 구현 |
| UI-4 | 모바일 반응형 대응 여부 | MVP 이후 |
| UI-5 | **프론트엔드 기술 스택 확정** — Next.js vs HTML+Plotly.js (open-items #11, ADR-006 필요) | Phase 3 착수 전 확정 |
| UI-6 | **`in_progress` 작업 상태** — Phase 3 시뮬레이터에서 합성 데이터 확장 여부 | Phase 3 결정 |

---

## 리뷰 피드백 기록

### 리뷰 #1 (2026-03-16)

1. **기술 스택 과함 (High):** Next.js 15 스택 전체가 1인 입문자에게 학습 곡선이 높음. open-items #11 + ADR-006으로 최종 확정 필요. ✅ 상단 경고 주석 추가
2. **`in_progress` 상태 없음 (Medium):** MES CSV에 completed/aborted만 있음. UI 예시를 `completed`로 수정, Phase 3 주의 사항 추가. ✅ 반영
3. **AlarmFeed API 비효율 (Medium):** `/api/f2/history` × 3 → `/api/f6/alarms` 단일 엔드포인트로 교체. api-design.md #13 추가. ✅ 반영
