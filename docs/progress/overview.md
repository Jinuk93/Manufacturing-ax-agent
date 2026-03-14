# Project Overview

> 프로젝트 전체 현황을 한눈에 보는 문서입니다.

---

## Phases

| Phase | 이름 | 상태 | 기간 | 핵심 산출물 |
|-------|------|------|------|------------|
| 0 | [Project Definition](../0-project-definition/) | ✅ 완료 | 2026-03-08 ~ 2026-03-10 | PRD, 데이터셋 전략, ADR 6건, 미결사항 정리 |
| 1 | [Data Exploration](../1-data-exploration/) | ✅ 완료 | 2026-03-10 ~ 2026-03-15 | EDA 42컬럼 확정, timestamp/equipment_id 합성, IT 데이터 합성 (MES/ERP/Maintenance), 이상치 분석 |
| 2 | [Architecture](../2-architecture/) | **다음** | - | 세부 파이프라인, DB 스키마 설계 |
| 3+ | *Phase 2 완료 후 정의* | - | - | - |

**Phase별 상세 로그:** [phases/](phases/)

---

## ADR Summary (의사결정 요약)

> 상세 표는 [adr-summary.md](adr-summary.md) 참조

| # | 날짜 | 주제 | 고민 내용 | 검토한 대안 | 결정 내용 | 결정 이유 |
|---|------|------|----------|------------|----------|----------|
| ADR-000 | 2026-03-08 | 데이터 도메인 | CNC + NASA 혼합 vs CNC 단일 | NASA: 센서 체계 상이, 조인 키 충돌 | **CNC 단일 도메인으로 통일** | 단일 도메인이어야 equipment_id 기준 조인과 LLM 맥락 일관성 유지 가능 |
| ADR-001 | 2026-03-08 | 예측 방식 | RUL vs Forecasting | RUL: 합성 타겟으로 신뢰성 검증 불가 | **Forecasting 기반 접근** | 실제 센서값의 미래 추세를 예측하면 임계치 기반 알람이 가능하고, 타겟 라벨 없이도 동작 |
| ADR-002 | 2026-03-08 | MES/ERP 확보 | 실데이터 vs 합성 | 공개 MES/ERP 데이터 존재하지 않음 | **Python으로 합성 생성** | 기준 센서 타임라인에 맞춰 비즈니스 시나리오를 직접 설계할 수 있어 LLM 판단 테스트에 유리 |
| ADR-003 | 2026-03-08 | DB 아키텍처 | 전용 DB 다수 vs 통합 | 3개 DB 운영 부담 과도 (1인 개발) | **PostgreSQL 통합 + Neo4j 별도 = 2개** | PostgreSQL 확장(TimescaleDB+pgvector)으로 시계열/관계형/벡터 3역할 충분, Neo4j는 그래프 탐색 대체 불가 |
| ADR-004 | 2026-03-08 | 실시간 처리 | Kafka/Flink vs 폴링 | 스트리밍 인프라 복잡도 과도 | **5초 폴링으로 실시간성 모사** | MVP 목적에는 5초 주기면 충분하고, 나중에 스트리밍 전환해도 파이프라인 구조는 동일 |
| ADR-005 | 2026-03-09 | 대시보드 우선순위 | 파이프라인 완성 후 vs 조기 시각화 | 중간 검증 없이 진행하면 방향 검증 어려움 | **대시보드 MVP 앞당김** | 시각적 결과물이 있어야 파이프라인 각 단계의 출력을 즉시 검증하고 방향 수정 가능 |

---

## Key Constraints

> 상세는 [constraints.md](constraints.md) 참조

| 제약 | 근거 |
|------|------|
| CNC 단일 도메인 | ADR-000 |
| Forecasting (RUL 아님) | ADR-001 |
| 합성 MES/ERP | ADR-002 |
| DB 2개 제한 | ADR-003 |
| 폴링 방식 | ADR-004 |

---

## Open Items

현재 **12개** 미결 사항 → [open-items.md](../0-project-definition/open-items.md)

---

## Docs Structure

```
docs/
├── progress/                      # 프로젝트 진행 관리
│   ├── overview.md                #   전체 현황 (이 문서)
│   ├── adr-summary.md             #   ADR 의사결정 요약 표
│   ├── constraints.md             #   Key Constraints
│   └── phases/                    #   Phase별 날짜별 로그
│       ├── phase-0.md             #     Phase 0 진행 기록
│       └── phase-1.md             #     Phase 1 진행 기록
├── 0-project-definition/          # Phase 0: 프로젝트 정의
│   ├── prd-v1.0.md                #   PRD (제품 요구사항 정의서)
│   ├── data-collection-strategy.md #   데이터 수집 전략 기준 문서
│   ├── required-data-summary.md   #   실수집/합성/미정 데이터 요약표
│   └── open-items.md              #   미결 사항 추적
├── future/                        # 향후 제품화/확장 비전
│   └── customer-onboarding-ontology-strategy.md
├── 1-data-exploration/            # Phase 1: 데이터 탐색 (EDA)
│   ├── README.md                  #   Phase 1 개요 및 완료 요약
│   ├── data-gap-analysis.md       #   데이터 갭 분석 (보유 vs 필요)
│   ├── outlier-analysis.md        #   이상치 분석 (README 경고 전수 조사)
│   └── it-data-synthesis-schema.md #   IT 데이터 합성 스키마
├── 2-architecture/                # Phase 2: 아키텍처 설계
└── adr/                           # ADR 템플릿
    └── 000-template.md
```
