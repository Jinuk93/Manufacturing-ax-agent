# Phase 3: Build & Validate — 구현 및 검증 로그

> Phase 3의 목표: Phase 2에서 설계한 아키텍처를 실제 코드로 구현하고, 전체 파이프라인(F1→F2→F3→F4→F5→F6)이 끊기지 않고 동작하는지 검증한다.

---

## 목표

Phase 2의 설계 문서(온톨로지, DB 스키마, 파이프라인, API)를 기반으로:

1. **Docker 인프라 구축** — PostgreSQL(TimescaleDB+pgvector) + Neo4j
2. **F1~F5 파이프라인 구현** — 센서 수집 → 이상탐지 → IT/OT 동기화 → GraphRAG → LLM 판단
3. **Neo4j 온톨로지 구축** — 120노드 + 337관계
4. **매뉴얼 임베딩** — 12문서 47청크 → pgvector
5. **통합 테스트** — W5 Coolant 재고=0 시나리오 + Spindle 과열 시나리오
6. **F6 프론트엔드** — React 18 + Vite (ADR-006) + Palantir 디자인

---

## 산출물 목록

### 백엔드 (파이프라인)

| # | 파일 | 내용 | 상태 |
|---|------|------|------|
| 1 | `docker-compose.yml` | PG(timescaledb-ha:pg16) + Neo4j(5-community) | ✅ 완료 |
| 2 | `db/init.sql` | 10테이블 + 마스터 데이터 + hypertable + pgvector HNSW | ✅ 완료 |
| 3 | `db/init_neo4j.cypher` | Equipment, FailureCode, Part, Document 기본 노드 + R4/R5 관계 | ✅ 완료 |
| 4 | `backend/init_neo4j.py` | PG→Neo4j 동기화 (Sensor 39, WO 18, MA 39 + R1/R3/R6/R7/R8/R9) | ✅ 완료 |
| 5 | `backend/app/main.py` | FastAPI 앱 (CORS: Vite 5173) | ✅ 완료 |
| 6 | `backend/app/api/routes.py` | 13개 엔드포인트 — 실제 DB 조회 (F6 action 제외) | ✅ 완료 |
| 7 | `backend/app/models/schemas.py` | Pydantic 모델 (api-design.md 기준) | ✅ 완료 |
| 8 | `backend/app/config.py` | 설정값 11개 + DB 연결 + LLM 설정 | ✅ 완료 |
| 9 | `backend/app/services/simulator.py` | F1 CSV→DB (batch/stream), 제외 6컬럼, CamelCase→snake_case | ✅ 완료 |
| 10 | `backend/app/services/db.py` | INSERT 함수 + 테이블 화이트리스트 | ✅ 완료 |
| 11 | `backend/app/services/anomaly_detector.py` | F2 Isolation Forest (10피처, unworn fit, 고장코드 4종 분류) | ✅ 완료 |
| 12 | `backend/app/services/itot_sync.py` | F3 IT/OT 동기화 (MES+CMMS+ERP 3개 SQL, 시점 필터) | ✅ 완료 |
| 13 | `backend/app/services/graphrag.py` | F4 Neo4j Cypher + pgvector 의미 검색 + E3 폴백 | ✅ 완료 |
| 14 | `backend/app/services/llm_agent.py` | F5 OpenAI GPT-4o-mini + 환각 검증 + 규칙 폴백 + async | ✅ 완료 |
| 15 | `backend/app/services/main_loop.py` | 메인 폴링 루프 (F1→F2 매 5초 + F3→F5 비동기 트리거) | ✅ 완료 |
| 16 | `backend/load_data.py` | CLI: batch/stream 데이터 로드 | ✅ 완료 |
| 17 | `backend/train_f2.py` | CLI: F2 모델 학습 + 검증 | ✅ 완료 |
| 18 | `backend/embed_manuals.py` | CLI: 매뉴얼 임베딩 (384차원 pgvector) | ✅ 완료 |
| 19 | `backend/test_integration.py` | 통합 테스트 (W5 Coolant + Spindle 시나리오, assert) | ✅ 완료 |
| 20 | `docs/2-architecture/f2-anomaly-detection-design.md` | F2 상세 설계 (Phase 2 선결과제 해결) | ✅ 완료 |

### 프론트엔드 (F6 대시보드)

| # | 파일 | 내용 | 상태 |
|---|------|------|------|
| 21 | `frontend/` | React 18 + Vite + TypeScript + Tailwind + shadcn/ui | ✅ 스캐폴드 완료 |
| 22 | `frontend/src/components/layout/` | AppShell, Sidebar, Topbar | ✅ 구현 중 |
| 23 | `frontend/src/components/dashboard/` | MonitoringCenter, ChatFab, InventoryOverlay, WorkOrderOverlay | ✅ 구현 중 |
| 24 | `frontend/src/lib/api/` | API 클라이언트 + 엔드포인트 정의 | ✅ 완료 |
| 25 | `frontend/src/stores/` | Zustand 전역 상태 | ✅ 완료 |

---

## 실행 방법

```bash
# 1. Docker 실행
docker-compose up -d

# 2. 데이터 로드
cd backend
pip install -r requirements.txt
python load_data.py batch

# 3. Neo4j 온톨로지 구축
cat ../db/init_neo4j.cypher | docker exec -i ax-neo4j cypher-shell -u neo4j -p ax_password
python init_neo4j.py

# 4. F2 모델 학습
python train_f2.py

# 5. 매뉴얼 임베딩
python embed_manuals.py

# 6. 통합 테스트
echo "OPENAI_API_KEY=sk-..." > .env
python test_integration.py

# 7. API 서버 실행
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI)

# 8. 프론트엔드 실행
cd ../frontend
npm install && npm run dev
# → http://localhost:5173
```

---

## 검증 결과

### 데이터 정합성

| 항목 | 기대값 | 실제값 | 판정 |
|------|--------|--------|------|
| sensor_readings | 25,286행 | 25,286행 | ✅ |
| mes_work_orders | 18건 | 18건 | ✅ |
| maintenance_events | 39건 | 39건 | ✅ |
| erp_inventory | 35건 | 35건 | ✅ |
| Neo4j 노드 | ~120개 | 120개 | ✅ |
| Neo4j 관계 | ~240개 | 337개 | ✅ |
| document_embeddings | 47청크 | 47청크 | ✅ |
| W5 P003 재고 | 0 | 0 | ✅ |

### F2 이상탐지 결과

| 지표 | 값 |
|------|-----|
| worn 평균 anomaly_score | 0.284 |
| unworn 평균 anomaly_score | 0.233 |
| 분리도 | 0.051 |
| 중단 실험 감지율 (exp04,05,07,16) | 7.9% ~ 35.0% |
| exp07 (고속+마모+중단) | 35.0% — 가장 강한 감지 |

### 통합 테스트 (2 시나리오)

**시나리오 1: W5 Coolant 재고=0**
- F3: P003 stock=0 정확 조회 ✅
- F4: DOC-010~012 + P003 검색 ✅
- F5 (LLM): REDUCE + "긴급 발주 필요" + P003 in_stock=False ✅

**시나리오 2: Spindle 과열 + critical 작업**
- F3: WO-2024-007 (critical) 작업 중 ✅
- F4: P002 + DOC-004~006 (실제 pgvector 유사도) ✅
- F5 (LLM): STOP + "즉시 정지, 베어링 교체" ✅

---

## 일일 로그

### Day 1 (2026-03-17) — 백엔드 파이프라인

**목표:** Phase 3 인프라 + F1~F5 구현 + 통합 테스트

작업 내용:
- **인프라 구축:**
  - docker-compose.yml (PG timescaledb-ha + Neo4j 5-community)
  - db/init.sql (10테이블, 마스터 데이터, hypertable, pgvector HNSW)
  - FastAPI 스켈레톤 13개 엔드포인트 + Pydantic 모델 + config 11개 설정값
  - 리뷰 피드백 8건 반영 (F3/F5 시그니처, erp_inventory PK, equipment_type, CORS, pydantic-settings 등)

- **F1 시뮬레이터:**
  - batch/stream 2가지 모드 (CSV→DB INSERT)
  - CamelCase→snake_case 변환 (regex), 제외 6컬럼 자동 제거
  - IT 데이터 컬럼 화이트리스트, SQL 인젝션 방지, 1000행 청크
  - 리뷰 피드백 5건 반영

- **F2 이상탐지:**
  - Isolation Forest (10피처, n_estimators=200, contamination=0.1)
  - unworn 6실험으로 fit (exp04/05 중단 제외), worn 10실험으로 검증
  - 고장코드 4종 규칙 기반 분류 (SPINDLE/TOOL_WEAR/CLAMP/COOLANT)
  - fit 시점 score 범위 저장 (stream 모드 안정 정규화)
  - 리뷰 피드백 5건 반영 (UNWORN 리스트 수정, CLAMP 규칙 추가 등)

- **F3 IT/OT 동기화:**
  - 3개 SQL 쿼리 (MES 범위 매칭, Maintenance 최근 5건, ERP 시점 필터)
  - end_time 조건 + alarm_time 재고 필터 (W5 시나리오 지원)
  - 리뷰 피드백 3건 반영

- **F4 GraphRAG:**
  - Neo4j Cypher 실제 연동 (R4/R5/R8/R9 + E3 폴백)
  - pgvector 의미 검색 (failure_code 설명 → cosine 유사도)
  - SentenceTransformer + Neo4j 드라이버 싱글턴 최적화
  - 리뷰 피드백 2건 반영

- **F5 LLM 자율 판단:**
  - OpenAI GPT-4o-mini (JSON mode, temperature=0.1)
  - SYSTEM_PROMPT + USER_PROMPT_TEMPLATE (F2+F3+F4 컨텍스트)
  - 환각 검증 (failure_code/part_id 화이트리스트)
  - E4/E6 지수 백오프 재시도 (asyncio.sleep)
  - 실패 시 규칙 기반 폴백
  - 리뷰 피드백 3건 반영

- **Neo4j 온톨로지:**
  - 120노드 + 337관계 (Cypher 스크립트 + Python PG→Neo4j 동기화)
  - R3 EXPERIENCES를 PG 데이터 기준 자동 생성 (수동 매핑 오류 수정)
  - 리뷰 피드백 3건 반영

- **매뉴얼 임베딩:**
  - sentence-transformers (384차원, 로컬 무료)
  - 12문서 → 47청크 → pgvector INSERT
  - 유사도 검색 테스트: "스핀들 과열" → DOC-004 1위 ✅
  - VECTOR(768)→VECTOR(384) 전체 동기화

- **통합 테스트:**
  - W5 Coolant 재고=0 시나리오: 4/4 검증 통과
  - Spindle 과열 + critical 작업 시나리오: 2/2 검증 통과
  - assert 추가 (CI 실패 감지)

- **메인 폴링 루프:**
  - F1→F2 매 5초 + is_anomaly=true → asyncio.create_task(F3→F4→F5)
  - F2 모델 싱글턴 로드, 100행마다 정상 로그

- **mock → 실제 DB 연결:**
  - 13개 엔드포인트 중 12개 실제 DB 조회로 교체
  - /f6/action만 F5 결과 저장 테이블 미구현 (TODO)

- **문서 동기화:**
  - README + overview.md Phase 테이블 업데이트
  - open-items.md 8건 Decided (매뉴얼, 온톨로지, DB, IF, GPT-4o-mini 등)
  - db-schema-design.md VECTOR 384차원 동기화

**리뷰 반영 총계:** 인프라 8건 + F1 5건 + F2 5건 + F3~F5 5건 + Neo4j 3건 + 임베딩 2건 + LLM 3건 + 종합 8건 + H1~H4 4건 + 싱글턴 2건 = **45건+**

---

## 미해결 과제 (후속)

### 기능 완성

| # | 항목 | 설명 | 우선순위 |
|---|------|------|----------|
| 1 | F6 action 엔드포인트 | F5 결과를 DB에 저장하고 /f6/action에서 조회 | 중간 |
| 2 | F4 R2 DETECTS 관계 | F2 모델 결과 기반 센서→고장코드 매핑 | 중간 |
| 3 | F4 R10 REFERENCES 관계 | 정비 → 매뉴얼 참조 이력 | 낮음 |
| 4 | 챗봇 (/api/chat) | F4+F5 재사용, 사용자 대화형 질의 | 중간 |
| 5 | F5 판단 투명성 | full_reasoning, alternatives_considered 확장 | 중간 |

### 코드 품질 개선

| # | 항목 | 설명 | 우선순위 |
|---|------|------|----------|
| 6 | config 이관 | IF contamination, 고장코드 임계치, LLM retry 등 하드코딩 → config | 중간 |
| 7 | 커넥션 풀 | 매 요청 get_connection() → psycopg2.pool | 중간 |
| 8 | CORS 환경변수화 | localhost:5173 하드코딩 → 설정 | 낮음 |
| 9 | init.sql 센서 주석 | "42개" → "39개 (M1 3개는 컨텍스트)" | 낮음 |
| 10 | DB 이름 문서 통일 | ax_agent vs cnc_maintenance | 낮음 |

### 모델 개선

| # | 항목 | 설명 | 우선순위 |
|---|------|------|----------|
| 11 | F2 분리도 개선 | 현재 0.051 → 피처 추가 (축 간 편차, 이동표준편차) | 중간 |
| 12 | Autoencoder 비교 | IF vs AE 성능 비교 실험 | 중간 |
| 13 | 공정별 분리 학습 | Machining_Process별 정상 범위 차별화 | 낮음 |
| 14 | CLAMP 임계치 검증 | 위치 편차 0.5mm가 실제 exp04/05에서 유효한지 | 중간 |

---

## Phase 2 선결 과제 해결 현황

| # | 과제 | Phase 2 상태 | Phase 3 결과 |
|---|------|-------------|-------------|
| 1 | F2 상세 설계 | 미착수 | ✅ f2-anomaly-detection-design.md 작성 + IF 구현 |
| 2 | 정비 매뉴얼 합성 | 0건 | ✅ 12건 합성 + 47청크 임베딩 |
| 3 | CSV→실시간 시뮬레이터 | 미설계 | ✅ batch/stream 2모드 + 메인 폴링 루프 |

---

## Day N (2026-03-17) — 프론트엔드-백엔드 실제 연동

**목표:** 코드로 작성된 프론트엔드를 실제 백엔드 API와 완전히 연결

### 백엔드 수정
- `/api/f6/action/{equipment_id}` — TODO 스텁 제거, 온디맨드 F2→F3→F4→F5 파이프라인 구현
- `/api/f6/sensors/{equipment_id}` — `NOW()-interval` 시간 필터 제거 (CSV 2024 타임스탬프 호환)

### 프론트엔드 수정
| 파일 | 변경 내용 |
|------|-----------|
| `types/index.ts` | 백엔드 Pydantic 스키마와 1:1 정합 (전면 재작성) |
| `endpoints.ts` | 실제 백엔드 6개 엔드포인트로 교체 |
| `Sidebar.tsx` | TanStack Query v5 버그 수정 (`placeholderData:[]` → `data=[]`) |
| `Topbar.tsx` | AX Manufacturing 로고 + 실제 알람 데이터 기반 STOP 배너 |
| `AiDetailPanel.tsx` | `getActionReport` 연동, recommendation/action_steps/parts_needed 표시 |
| `MonitoringCenter.tsx` | Recharts 센서 시계열 차트 + F1~F5 파이프라인 상태 구현 |
| `WorkOrderOverlay.tsx` | 실제 `/f6/work-order` API 연동 (3개 설비 고정 hook) |
| `InventoryOverlay.tsx` | 실제 `/f6/work-order` inventory 연동 |

### 미해결 (후속)
- ChatFab `/api/chat` 엔드포인트 미구현 (현재 더미 상태)
- 브라우저 실제 동작 테스트 필요
