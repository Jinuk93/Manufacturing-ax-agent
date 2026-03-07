# Manufacturing-ax-agent

**예측 기반 자율 조치 에이전트 관제 시스템**

### Problem

제조 현장에서 설비 이상이 발생하면, 작업자는 **3~4개의 분산된 시스템**을 직접 순회해야 합니다.

```
SCADA (센서 수치 확인) → MES (현재 작업/납기 확인) → ERP (부품 재고 확인) → 매뉴얼 (조치 방법 탐색)
```

이 수동 프로세스로 인해 **의사결정이 지연**되고,<br> 설비의 평균 수리 시간(MTTR)과 비가동 시간(Downtime)이 증가하여 생산 원가 손실이 발생합니다.

### Solution

분절된 IT/OT 데이터를 통합하고,<br> 
AI가 **사람 대신 자동으로 순회 → 판단 → 보고**하는 에이전트 시스템을 구축합니다.

| 기존 (수동) | 이 시스템 (자동화) |
|------------|-------------------|
| 작업자가 센서 수치를 보고 이상 감지 | **시계열 예측(Forecasting)** 이 설비 이상을 선제적으로 감지 |
| 작업자가 MES/ERP를 수동 조회 | **알람 시점 기준으로 납기/재고를 자동 조회** |
| 작업자가 매뉴얼을 찾아 대조 | **Neo4j 온톨로지 + GraphRAG**로 정비 지식을 자동 검색 |
| 작업자가 경험에 의존해 판단 | **LLM이 비즈니스 맥락 + 정비 지식을 종합**하여 조치 리포트 자동 생성 |

### Expected Impact

- **MTTR (평균 수리 시간) 단축**<br>
  : 이상 감지 → 조치 지시까지의 시간을 수동 대비 대폭 단축
- **선제적 대응**<br>
  : 고장 발생 전 예측 알람으로 계획 정비 가능
- **판단 품질 향상**<br>
  : 납기 긴급도, 부품 재고, 정비 이력을 종합한 근거 기반 의사결정
- **지식 표준화**<br>
  : 숙련자 경험에 의존하던 정비 판단을 온톨로지 + LLM으로 체계화

## AX (AI Transformation) Vision

이 시스템이 지향하는 제조 AX는 단순한 모니터링 자동화가 아닙니다.

> **"설비가 고장나기 전에, AI가 알아서 상황을 파악하고,<br> 최적의 조치를 제안하는"**
> 예측 → 판단 → 지시의 전 과정을 자율화하는 것입니다.

---

## System Pipeline

### 1. 상시 동작 레이어

```
[KAMP CNC 센서] ──> [F1: 센서 수집/전처리] ──> [F2: 이상탐지 + 예측]
                                                        |
                                                  Anomaly Score
                                                        |
                                               [F6: 관제 대시보드] <── 센서 실시간 모니터링
```

> F1, F2, F6는 알람 여부와 관계없이 **항상 동작**합니다.

### 2. 독립 기능 모듈

```
[F3: MES/ERP 조회]          [F4: GraphRAG 검색]          [F5: LLM 리포트]
 - 납기, 재고 상태            - Neo4j 온톨로지 순회        - F3 + F4 결과 종합
 - 운영자 수동 조회 가능       - 운영자 수동 검색 가능       - 자율 판단 생성
```

> F3, F4는 **독립적으로 호출 가능**한 모듈입니다. F5는 F3+F4 결과가 있으면 동작합니다.

### 3. 관제 자동화 흐름 (이 시스템의 핵심 가치)

```
사람이 3~4개 시스템을 수동 순회하던 것을 자동화:

[F2: 임계치 돌파] ──> 알람 발생
                        |
          +-------------+-------------+
          |                           |
    [F3: 자동 조회]            [F4: 자동 검색]
    MES 납기/작업 상태          정비 매뉴얼
    ERP 부품 재고               고장코드 → 부품 → 조치
          |                           |
          +-------------+-------------+
                        |
               [F5: LLM 자동 생성]
               조치 리포트
                        |
               [F6: 대시보드에 즉시 표시]
```

> **이 자동화 흐름이 PRD §1.1의 비즈니스 문제를 해결하는 핵심입니다.**

---

## Tech Stack

| 영역 | 기술 |
|------|------|
| Database | PostgreSQL (TimescaleDB + pgvector) |
| Graph DB | Neo4j |
| Backend | Python, FastAPI |
| Frontend | Next.js + Tailwind CSS + Tremor |
| Infra | Docker Compose |

---


## Project Progress (Agile)

> 이 프로젝트는 애자일 방식으로, 각 단계의 의사결정 과정(ADR)과 고민을 모두 문서화하며 진행합니다.

### Phases

| Phase | 이름 | 상태 | 핵심 산출물 |
|-------|------|------|------------|
| 0 | [Project Definition](docs/0-project-definition/) | **진행중** | PRD, 데이터셋 전략, 미결사항 정리 |
| 1 | [Data Exploration](docs/1-data-exploration/) | 대기 | KAMP 데이터 EDA, 센서 분석 |
| 2 | [Architecture](docs/2-architecture/) | 대기 | 세부 파이프라인, DB 스키마 설계 |
| 3+ | *Phase 2 완료 후 정의* | - | - |

### Architecture Decision Records (ADR)

프로젝트의 모든 기술적 의사결정은 ADR로 기록합니다.<br>
각 결정의 배경, 고려한 대안, 선택 근거, 그로 인한 제약사항을 추적합니다.

| Phase | ADR | 결정 사항 | 상태 |
|-------|-----|----------|------|
| 0 | [ADR-000](docs/adr/) | 데이터 도메인을 CNC 단일로 통일 (NASA 데이터 배제) | Decided |
| 0 | [ADR-001](docs/adr/) | RUL 예측 포기, Forecasting 방식으로 전환 | Decided |
| 0 | [ADR-002](docs/adr/) | MES/ERP 데이터 Python 합성 생성 | Decided |
| 0 | [ADR-003](docs/adr/) | PostgreSQL 단일 DB 통합 (TimescaleDB + pgvector) | Decided |
| 0 | [ADR-004](docs/adr/) | 실시간 처리를 폴링 방식으로 대체 | Decided |
| 0 | [ADR-005](docs/adr/) | 시각적 결과물(대시보드 MVP) 앞당김 | Decided |

### Key Constraints

| 제약 | 결정 근거 |
|------|----------|
| CNC 단일 도메인 | 도메인 혼합 시 데이터 조인 키 충돌 및 LLM 환각 방지 (ADR-000) |
| RUL 대신 Forecasting | 합성 타겟 변수로는 모델 신뢰성 평가 불가 (ADR-001) |
| 합성 MES/ERP | 기업 데이터 비공개, KAMP 타임라인에 맞춰 합성 (ADR-002) |
| DB 2개로 제한 | 1인 개발, PostgreSQL 확장으로 3역할 통합 (ADR-003) |
| 폴링 방식 | Kafka/Flink 없이 5초 주기 조회로 실시간 모사 (ADR-004) |

### Open Items(미결 사항)

현재 **11개** 미결 사항이 있으며, 대부분 Phase 1(EDA) 이후 결정됩니다.<br>
상세 내용은 [open-items.md](docs/0-project-definition/open-items.md)를 참조하세요.

---

## Docs Structure(문서 구조)

```
docs/
├── README.md                      # docs 전체 안내
├── 0-project-definition/          # Phase 0: 프로젝트 정의
│   ├── prd-v1.0.md                #   PRD (제품 요구사항 정의서)
│   ├── dataset-strategy.md        #   데이터셋 확보 전략
│   └── open-items.md              #   미결 사항 추적
├── 1-data-exploration/            # Phase 1: 데이터 탐색 (EDA)
├── 2-architecture/                # Phase 2: 아키텍처 설계
└── adr/                           # ADR (의사결정 기록)
    └── 000-template.md            #   ADR 작성 템플릿
```

> 이 프로젝트는 애자일 원칙에 따라, Phase 3 이후의 폴더는 Phase 2 완료 후 필요 시 생성합니다.
