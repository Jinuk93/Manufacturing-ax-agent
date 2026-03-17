# Manufacturing-ax-agent

**CNC 예지보전 + 온톨로지 기반 GraphRAG + LLM 자율 조치 에이전트 관제 시스템**

<p align="center">
  <img src="docs/assets/dashboard-preview.png" alt="Dashboard Preview" width="800" />
</p>

---

## Problem

제조 현장에서 설비 이상이 발생하면, 작업자는 **3~4개의 분산된 시스템**을 직접 순회해야 합니다.

```
SCADA (센서 수치 확인) → MES (현재 작업/납기 확인) → ERP (부품 재고 확인) → 매뉴얼 (조치 방법 탐색)
```

이 수동 프로세스로 인해 **의사결정이 지연**되고, 설비의 평균 수리 시간(MTTR)과 비가동 시간(Downtime)이 증가하여 생산 원가 손실이 발생합니다.

## Solution

분절된 IT/OT 데이터를 통합하고, AI가 **자동으로 순회 → 분석 → 조치를 제안**하는 에이전트 시스템을 구축합니다.

| 기능 | 기존 (수동) | 이 시스템 (AI 지원) |
|------|------------|-------------------|
| **이상탐지** | 작업자가 센서 수치를 보고 이상 감지 | Isolation Forest + 1D-CNN이 **자동 판별** |
| **예지보전** | 고장 발생 후 사후 대응 | 시계열 예측(1D-CNN)으로 **고장 전 선제 알람** |
| **운영 맥락 조회** | 작업자가 MES/ERP를 수동 조회 | 알람 시점 기준으로 **자동 조회** |
| **정비 지식 검색** | 작업자가 매뉴얼을 찾아 대조 | Neo4j 온톨로지 + GraphRAG로 **자동 검색** |
| **조치 제안** | 작업자가 경험에 의존해 판단 | LLM이 비즈니스 맥락 + 정비 지식을 종합하여 **자동 생성** |
| **AI 챗봇** | — | 실시간 DB 데이터 기반 질의응답 (GraphRAG + pgvector) |

## Expected Impact

- **MTTR 단축** — 이상 감지 → 조치 지시까지의 시간을 수동 대비 대폭 단축
- **선제적 대응** — 1D-CNN이 30초 후 센서값을 예측하여 고장 전 알람
- **판단 품질 향상** — 납기 긴급도, 부품 재고, 정비 이력을 종합한 근거 기반 의사결정
- **지식 표준화** — 숙련자 경험에 의존하던 정비 판단을 온톨로지 + LLM으로 체계화

---

## System Architecture

### 핵심 파이프라인 (F1 → F6)

```
[센서 데이터] ──→ [F1: 수집/전처리] ──→ [F2: 이상탐지 + 예측]
                                              │
                            ┌─────────────────┤ Anomaly Score
                            │                 │
                    ┌───────▼───────┐  ┌──────▼──────┐
                    │ F3: IT/OT 동기 │  │ F4: GraphRAG│
                    │ MES 납기/작업  │  │ Neo4j 온톨로지│
                    │ ERP 부품 재고  │  │ 정비 매뉴얼   │
                    └───────┬───────┘  └──────┬──────┘
                            │                 │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │ F5: LLM 자율 판단 │
                            │ STOP/REDUCE/     │
                            │ MONITOR 조치 생성 │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │ F6: 관제 대시보드  │
                            │ + AI 챗봇         │
                            └─────────────────┘
```

### F2: 이상탐지 + 예지보전 (ADR-007)

```
                ┌──────────────────┐
센서 300행 ───→ │ Isolation Forest  │──→ IF 점수 (현재 이상 여부)
(30초 윈도우)   │ (비지도 학습)      │
                └──────────────────┘
                ┌──────────────────┐
센서 300행 ───→ │ 1D-CNN Forecaster │──→ Forecast 점수 (미래 예측)
(30초 입력)     │ (자기지도 학습)    │
                └──────────────────┘
                         │
              융합 점수 = 0.6×IF + 0.4×Forecast

성능: unworn/worn 분리도 0.051(IF) → 0.384(IF+CNN) — 7.5배 향상
```

### 온톨로지 구조 (Neo4j)

```
Equipment ──[HAS_SENSOR]──→ Sensor ──[DETECTS]──→ FailureCode
    │                                                  │
    ├──[EXPERIENCES]──→ FailureCode ──[REQUIRES]──→ Part
    │                       │
    ├──[EXECUTES]──→ WorkOrder   FailureCode ──[DESCRIBED_BY]──→ Document
    │                                                              │
    └──[triggers]──→ MaintenanceAction ──[REFERENCES]──→ Document
                          │
                          ├──[RESOLVES]──→ FailureCode
                          └──[CONSUMES]──→ Part
```

- **120 노드** (설비 3 + 센서 39 + 고장코드 4 + 부품 5 + 문서 12 + 작업 18 + 정비 39)
- **337 관계** (R1~R10, 10종 관계 유형)

---

## Tech Stack

| 영역 | 기술 | 비고 |
|------|------|------|
| Backend | Python, FastAPI | 타입 힌트, 한국어 주석 |
| Database | PostgreSQL (TimescaleDB + pgvector) | 시계열 + 벡터 검색 통합 |
| Graph DB | Neo4j 5 Community | 온톨로지 + GraphRAG |
| ML | Isolation Forest + 1D-CNN (PyTorch) | ADR-001, ADR-007 |
| LLM | OpenAI GPT-4o-mini | JSON mode, 비용 효율 |
| Frontend | React 18 + Vite + TanStack Query v5 + Recharts | ADR-006 |
| Infra | Docker Compose | PostgreSQL + Neo4j |
| Font | IBM Plex Sans/Mono + Noto Sans KR | 기업용 단정한 서체 |

---

## Dashboard

### 메인 화면 — 전체 설비 모니터링

4패널 레이아웃: **설비 현황 | AI 분석 | 모니터링 센터 | AI 챗봇**

- **설비 현황** — CNC-001/002/003 상태, 이상감지 로그 (실시간), 시스템 상태 (F1~F6)
- **AI 분석** — 설비별/알람별 분석, 전체 종합 분석, 작업현황/재고현황 AI 분석
- **모니터링** — 전체 설비 테이블 + 4축 전류/출력 파워/이상 추이 차트
- **AI 챗봇** — 실시간 DB 데이터 기반 질의응답 (GraphRAG + pgvector + Neo4j)

### 설비별 상세 모니터링

탭 전환: `전체 설비 | CNC-001 | CNC-002 | CNC-003 | 예지보전`

- KPI 5개 (이상점수, 고장코드, LLM판단, 현재작업, 확신도)
- 4축 전류 비교 차트 (X1/Y1/S1 서보 + 스핀들)
- 출력 파워 차트 (X1/S1)
- 이상 점수 추이 (STOP/REDUCE 기준선)
- 정비 이력 + 작업지시 + LLM 판단 내역

### 예지보전 탭

- IF 탐지 점수 vs CNN 예측 점수 비교 차트
- 추세 분석 + STOP 도달 예상 시점
- 위험 센서 분석 (고장코드 → 센서 매핑)
- 상단바/사이드바 예지보전 경고 알림

---

## Data

### KAMP CNC 밀링 데이터셋

| 항목 | 값 |
|------|-----|
| 실험 | 18개 (unworn 8 + worn 10) |
| 센서 | 42컬럼 (4축 × 11센서 + feedrate + process) |
| 총 행 | 25,286행 |
| 샘플링 | 100ms |
| 설비 | CNC-001, CNC-002, CNC-003 (합성 분배) |

### 합성 데이터 (MES/ERP/CMMS)

| 테이블 | 건수 | 용도 |
|--------|------|------|
| mes_work_orders | 18건 | 작업지시 (6건/설비) |
| maintenance_events | 39건 | 정비 이력 |
| erp_inventory | 35건 | 부품 재고 (5종) |
| maintenance_manuals | 12건 | 정비 매뉴얼 (4고장코드 × 3유형) |
| document_embeddings | 47청크 | pgvector 임베딩 (384차원) |

### 고장코드 (4종)

| 코드 | 설명 | 심각도 | 감지 기준 |
|------|------|--------|----------|
| TOOL_WEAR_001 | 엔드밀 마모 | Critical | X1 전류 < median × 0.7 |
| SPINDLE_OVERHEAT_001 | 스핀들 과열 | Critical | S1 전류 > median × 1.3 |
| CLAMP_PRESSURE_001 | 클램프 압력 저하 | Warning | Y1 위치 편차 > 0.5mm |
| COOLANT_LOW_001 | 냉각수 부족 | Warning | 나머지 이상 |

---

## Project Progress

| Phase | 이름 | 기간 | 상태 |
|-------|------|------|------|
| 0 | Project Definition | 3/8~3/10 | ✅ 완료 |
| 1 | Data Exploration | 3/10~3/12 | ✅ 완료 |
| 2 | Architecture Design | 3/12~3/14 | ✅ 완료 |
| 3 | Build & Validate | 3/14~3/17 | ✅ 완료 |

### ADR (Architecture Decision Records)

| ADR | 결정 | 근거 |
|-----|------|------|
| [ADR-000](docs/adr/adr-000-single-domain.md) | CNC 단일 도메인 | 다중 도메인 조인 키 충돌 + LLM 환각 방지 |
| [ADR-001](docs/adr/adr-001-rul-vs-forecasting.md) | Forecasting 방식 (RUL 포기) | 합성 RUL 신뢰성 부족 |
| [ADR-002](docs/adr/adr-002-mes-erp-synthesis.md) | MES/ERP 합성 데이터 | 공개 데이터셋 없음 |
| [ADR-003](docs/adr/adr-003-db-architecture.md) | PostgreSQL + Neo4j (2 DB) | 1인 개발 관리 가능 범위 |
| [ADR-004](docs/adr/adr-004-polling-vs-kafka.md) | 5초 폴링 (Kafka 미사용) | MVP 복잡도 최소화 |
| [ADR-005](docs/adr/adr-005-dashboard-mvp.md) | 대시보드 MVP 앞당김 | 시각적 검증 필요 |
| [ADR-006](docs/adr/adr-006-frontend-stack.md) | React 18 + Vite SPA | SSR 불필요, 학습 비용 최소화 |
| [ADR-007](docs/adr/adr-007-f2-forecasting-model.md) | 1D-CNN + 가중 융합 | 짧은 시퀀스(300행)에 CNN 적합 |

---

## Quick Start

### 1. 인프라 실행

```bash
docker compose up -d    # PostgreSQL + Neo4j
```

### 2. 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev              # http://localhost:5173
```

### 4. 데이터 초기화 (최초 1회)

```bash
cd backend
python load_data.py       # 센서 + MES/ERP 데이터 로드
python embed_manuals.py   # 정비 매뉴얼 임베딩
python init_neo4j.py      # Neo4j 온톨로지 생성
```

### 5. 실시간 데이터 리플레이 (선택)

```bash
cd backend
python replay_data.py     # 기존 데이터를 현재 시각으로 재생
```

---

## File Structure

```
Manufacturing-ax-agent/
├── backend/
│   ├── app/
│   │   ├── api/routes.py           # 14개 API 엔드포인트
│   │   ├── config.py               # 설정값 관리
│   │   ├── models/schemas.py       # Pydantic 스키마
│   │   └── services/
│   │       ├── anomaly_detector.py  # F2: Isolation Forest
│   │       ├── forecaster.py        # F2: 1D-CNN Forecaster
│   │       ├── itot_sync.py         # F3: IT/OT 동기화
│   │       ├── graphrag.py          # F4: GraphRAG 검색
│   │       ├── llm_agent.py         # F5: LLM 자율 판단
│   │       ├── chat_agent.py        # AI 챗봇
│   │       ├── db.py                # DB 커넥션 풀
│   │       └── main_loop.py         # F1→F2 폴링 루프
│   ├── models/                      # 학습된 모델 (.pkl)
│   ├── replay_data.py               # 데이터 리플레이
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/              # AppShell, Sidebar, Topbar, AiDetailPanel
│   │   │   ├── dashboard/           # MonitoringCenter, ChatPanel, Overlays
│   │   │   └── ErrorBoundary.tsx    # 크래시 방지
│   │   ├── hooks/useEquipmentData.ts # 공통 쿼리 훅
│   │   ├── stores/dashboardStore.ts  # Zustand 전역 상태
│   │   ├── lib/api/                  # API 클라이언트
│   │   └── types/index.ts            # 타입 정의
│   └── index.html
├── db/
│   ├── init.sql                     # PostgreSQL 스키마
│   └── init_neo4j.cypher            # Neo4j 초기화
├── data/
│   └── processed/                   # 전처리된 데이터
├── docs/
│   ├── adr/                         # ADR 7건
│   ├── progress/                    # Phase 로그
│   └── prompts/                     # 매뉴얼 생성 프롬프트
├── docker-compose.yml
└── CLAUDE.md                        # 프로젝트 규칙
```

---

## License

This project is for educational and portfolio purposes.

## Author

1인 개발 프로젝트 — CNC 제조 도메인 예지보전 시스템
