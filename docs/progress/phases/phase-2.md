# Phase 2: Architecture Design — 계획 및 일일 로그

> Phase 2의 목표: F1~F6 전체 시스템 아키텍처를 설계하고, 구현 가능한 청사진을 만든다.

---

## 목표

Phase 1에서 확보한 데이터(OT 42컬럼 + IT 합성 3종)를 기반으로,
실제 구현에 들어가기 전에 **시스템 전체 구조를 설계**한다.

핵심 질문: "어떤 데이터가 어떤 DB에 들어가고, 어떤 순서로 흘러서, 최종적으로 대시보드에 뭘 보여주는가?"

---

## 산출물 목록

| # | 문서 | 경로 | 내용 | 상태 |
|---|------|------|------|------|
| 1 | 온톨로지 설계 | `docs/2-architecture/ontology-design.md` | Neo4j 7노드/10관계/속성 정의 | ✅ 완료 (리뷰 1회) |
| 2 | DB 스키마 설계 | `docs/2-architecture/db-schema-design.md` | PostgreSQL 10테이블 + TimescaleDB + Neo4j 매핑 | ✅ 완료 (리뷰 1회) |
| 3 | 파이프라인 설계 | `docs/2-architecture/pipeline-design.md` | F1~F6 데이터 흐름 + 에러 처리 6시나리오 | ✅ 완료 (리뷰 1회) |
| 4 | API 설계 | `docs/2-architecture/api-design.md` | FastAPI 12엔드포인트 + Pydantic 모델 | ✅ 완료 (리뷰 1회) |
| 5 | ADR (필요 시) | `docs/adr/adr-006-*.md` 등 | 설계 과정에서 결정이 필요한 사항 | 해당 없음 (기존 ADR로 충분) |

---

## 진행 순서

리뷰어 피드백을 반영한 순서:

```
① 온톨로지 설계 (Neo4j 노드/관계)
    ↓ 온톨로지가 PG 참조 테이블 설계에 영향
② DB 스키마 설계 (PostgreSQL + Neo4j 매핑)
    ↓ 데이터 저장소가 확정되어야 흐름 설계 가능
③ 파이프라인 설계 (F1~F6 데이터 흐름 + 에러 처리)
    ↓ 내부 흐름이 확정되어야 외부 인터페이스 정의 가능
④ API 설계 (FastAPI 엔드포인트)
```

**순서 변경 근거:** 온톨로지(Neo4j)의 노드/관계 구조가 PostgreSQL 참조 테이블 설계에 직접 영향을 줌.
예: `failure_code`를 PG에도 넣을지 Neo4j에만 둘지는 온톨로지를 먼저 그려봐야 결정 가능.

---

## 이미 결정된 제약사항 (Phase 0~1에서 확정)

| 제약 | 출처 | 내용 |
|------|------|------|
| CNC 단일 도메인 | ADR-000 | NASA 등 다중 도메인 배제 |
| Forecasting 방식 | ADR-001 | RUL(잔여수명) 포기, 시계열 예측 |
| 합성 IT 데이터 | ADR-002 | MES 18건, Maintenance 39건, ERP 35건 |
| 2개 DB | ADR-003 | PostgreSQL(TimescaleDB+pgvector) + Neo4j |
| 5초 폴링 | ADR-004 | Kafka/Flink 미사용 |
| 대시보드 병행 | ADR-005 | MVP를 파이프라인과 병행 개발 |
| OT 데이터 | Phase 1 | 48컬럼 중 42개 유효, 25,286행 |
| IT 합성 스키마 | Phase 1 | failure_code 4종, 부품 5종, 조인 키 확정 |
| 설비 매핑 | Phase 1 | exp01~06→CNC-001, 07~12→CNC-002, 13~18→CNC-003 |

---

## Phase 2에서 결정해야 할 미결 사항

> 번호는 [open-items.md](../../0-project-definition/open-items.md)의 번호 체계를 따릅니다. (#1~4는 Phase 1에서 해결됨)

| # | 항목 | 현재 상태 | Phase 2 접근 방식 |
|---|------|-----------|-------------------|
| 5 | Canonical Model (내부 표준 형식) | Partial — 컬럼 확정, DB 미정 | DB 스키마 설계에서 구체화 |
| 6 | 이상탐지 모델 (IF vs AE) | Open | ADR로 후보 비교만. 실제 선택은 Phase 3에서 데이터로 검증 |
| 7 | LSTM 예측 윈도우 (30분 가설) | Open | 설계에서는 윈도우 크기를 **설정값**으로 두는 구조만 잡음 |
| 8 | Anomaly Score 임계치 | Open | 7번과 동일. 파라미터화하여 실험 가능하게 설계 |
| 9 | LLM 선택 (API vs 로컬) | Open | **API 우선 거의 확정** (1인 개발 + 입문자, 로컬 LLM 인프라 부담) |
| 10 | 하이브리드 검색 점수 결합 | Open | 파이프라인 설계에서 구조만 잡고, 가중치는 Phase 3 튜닝 |
| 11 | 프론트엔드 MVP 전략 | Open | 3가지 선택지: ① Streamlit 프로토타입 ② 현 HTML+Plotly.js 확장 ③ Next.js. 1인 개발 부담 고려 |

**원칙:** Phase 2는 "구조 설계"이지 "최적값 확정"이 아님.
모델 하이퍼파라미터, 임계치 등은 설정값(config)으로 두고, Phase 3 구현에서 실험으로 결정.

---

## 각 산출물의 핵심 설계 포인트

### ① 온톨로지 설계 (`ontology-design.md`)

- **노드 타입:** Equipment, FailureCode, Part, Procedure, Manual, + **Sensor 여부 결정 필요**
- **Sensor 모델링 결정:** 42개 센서 컬럼을 Neo4j 노드로 모델링할지, Equipment의 속성으로 처리할지가 핵심 설계 포인트
  - 노드로 모델링 → 센서 간 관계, 센서→고장 연결 표현 가능 (풍부하지만 복잡)
  - 속성으로 처리 → 단순하지만 센서 단위 질의 어려움
- **관계:** Equipment -[HAS_FAILURE]→ FailureCode -[REQUIRES_PART]→ Part, FailureCode -[HAS_PROCEDURE]→ Procedure
- **속성:** 각 노드/관계에 어떤 속성을 붙일지
- **데이터 소스:** IT 합성 스키마 (`it-data-synthesis-schema.md`)의 failure_code 4종, 부품 5종 기반
- **핵심 결정:** PG와 Neo4j 간 데이터 중복/분담 경계

### ② DB 스키마 설계 (`db-schema-design.md`)

- **PostgreSQL (TimescaleDB)**
  - 센서 시계열 테이블 (hypertable)
  - MES/ERP/Maintenance 참조 테이블
  - pgvector 임베딩 테이블 (F4용)
- **Neo4j**
  - 온톨로지 그래프 (①에서 정의한 구조)
- **핵심 결정:** 어떤 데이터가 PG에, 어떤 데이터가 Neo4j에 들어가는가

### ③ 파이프라인 설계 (`pipeline-design.md`)

- **F1 (센서 전처리):** 윈도잉, 정규화, 피처 엔지니어링
- **F2 (이상탐지 + 예측):** 모델 구조 (IF/AE 후보), 입출력 형태
- **F3 (IT/OT 동기화):** 5초 폴링 로직, timestamp 정렬
  - **핵심 난이도:** OT(센서)는 100ms 연속 스트림, IT(MES/정비)는 비정기 이벤트 데이터 → 이질적인 두 데이터를 어떤 시간 기준으로 조인/정렬하는지가 F3의 본질적 설계 과제
- **F4 (GraphRAG):** Neo4j 순회 + BM25 + Vector 검색 흐름
- **F5 (LLM 판단):** 프롬프트 구조, 컨텍스트 주입 방식
- **F6 (대시보드):** 실시간 표시 항목, 알림 기준
- **에러 처리:** 센서 데이터 미수신, LLM API 실패, DB 연결 끊김 시 대응

### ④ API 설계 (`api-design.md`)

- **FastAPI 엔드포인트 목록** (F1~F6 각각)
- **요청/응답 스키마** (Pydantic 모델)
- **인증:** MVP에서는 생략 가능, 추후 확장 지점만 표시

---

## 리뷰 피드백 기록

### 2026-03-15 — 리뷰어 피드백 #1 (Phase 2 계획 수립 시)

1. **순서 변경:** 온톨로지 → DB 스키마 순서로 변경 (Neo4j가 PG 참조 테이블에 영향) ✅ 반영
2. **미결 사항 접근:** 모델 선택(#6)과 윈도우(#7)는 ADR 비교만, Phase 3에서 데이터 검증 ✅ 반영
3. **LLM:** 1인 개발 + 입문자 → API 우선 거의 확정 ✅ 반영
4. **에러 처리:** 파이프라인 설계에 에러/장애 대응 흐름 포함 필요 ✅ 반영

### 2026-03-15 — 리뷰어 피드백 #2 (Phase 2 계획 초안 리뷰)

1. **미결 번호 안내:** 5번부터 시작하는 이유 설명 메모 추가 ✅ 반영
2. **Sensor 노드 누락:** 42개 센서 컬럼을 노드로 모델링할지 속성으로 처리할지가 온톨로지 핵심 결정 포인트 ✅ 반영
3. **F3 설명 보강:** OT(연속 스트림) vs IT(비정기 이벤트) 조인 기준이 F3의 본질적 과제 ✅ 반영
4. **프론트엔드 선택지 추가:** 현 HTML+Plotly.js 확장도 현실적 옵션 (1인 개발 부담 최소) ✅ 반영

---

## 일일 로그

> 아래에 Phase 2 진행 시 일일 로그를 기록합니다.

### Day 1 (2026-03-16)

**목표:** Phase 2 아키텍처 설계 4개 문서 작성 + 리뷰 반영

- 온톨로지 설계 초안 작성 → 리뷰어 피드백 6건 반영 (Sensor 42개만, Document 1계층, DETECTS 가설 명시 등)
- DB 스키마 설계 초안 작성 → 리뷰어 피드백 7건 반영 (S축 11개, Parts 원본 통일, sensors 42개만 등)
- 파이프라인 설계 초안 작성 → 리뷰어 피드백 8건 반영 (F5 임계치 config, F3 작업 0건 분기, 컬럼 수 47개 등)
- API 설계 초안 작성 → 리뷰어 피드백 2건 반영 (F5 비동기 주석, series 타입 메모)
- 종합 리뷰 피드백 6건 반영 (상태 갱신, 메인 루프 동기화, note 위치, 컬럼 수 오타 등)

**산출물:**
- `docs/2-architecture/ontology-design.md`
- `docs/2-architecture/db-schema-design.md`
- `docs/2-architecture/pipeline-design.md`
- `docs/2-architecture/api-design.md`
- `docs/progress/phases/phase-2.md` (이 파일)

---

## Phase 3 진입 전 선결 과제

> Phase 2 설계는 "구현 가능한 청사진"으로 합격. 다만 Phase 3에서 바로 코딩에 들어가기 전, 아래 3가지를 먼저 정리해야 함.

### 1. F2 상세 설계 (피처 선택 + 라벨링 전략)

F2는 파이프라인의 핵심인데 설계가 가장 얇음. Phase 3 초반에 별도 상세 설계 필요:

- **피처 선택:** 42개 센서를 전부 넣을지, 상관관계 높은 것만 골라 넣을지?
- **라벨링 전략:** EDA에서 발견한 "worn 상태 CurrentFeedback -47%" 같은 패턴을 어떻게 활용?
- **비지도 vs 준지도:** 현재 데이터에 이상/정상 라벨이 없음 (worn/unworn만 있음). 비지도 모델만으로 충분한지?
- **Why:** F2 설계 없이 Phase 3 구현에 들어가면 피처/모델 선택에서 시행착오가 커짐

### 2. 정비 매뉴얼 합성 계획

F4 GraphRAG 설계는 잘 되어 있지만, 실제 검색할 정비 매뉴얼 문서가 **0건**:

- 매뉴얼 품질이 F4+F5 성능을 직접 좌우
- 합성 작업이 예상보다 시간이 걸릴 수 있음
- **의존성:** open-items #2 (정비 매뉴얼 합성 방향)

### 3. CSV → 실시간 시뮬레이터 구조

파이프라인은 "5초 폴링 실시간 수집"을 전제로 설계됐지만, 실제 데이터는 KAMP CSV(과거 실험):

- CSV 행을 순차적으로 5초 간격으로 흘려보내는 시뮬레이터 필요
- 시뮬레이터 설계가 현재 어디에도 없음
- **Phase 3 구현 초기에 F1 시뮬레이터부터 만들어야 파이프라인 테스트 가능**
