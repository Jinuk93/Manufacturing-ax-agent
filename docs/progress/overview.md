# Project Overview

> 프로젝트 전체 현황을 한눈에 보는 문서입니다.

---

## Phases

| Phase | 이름 | 상태 | 기간 | 핵심 산출물 |
|-------|------|------|------|------------|
| 0 | [Project Definition](../0-project-definition/) | **진행중** | 2026-03-08 ~ | PRD, 데이터셋 전략, 미결사항 정리 |
| 1 | [Data Exploration](../1-data-exploration/) | 대기 | - | KAMP 데이터 EDA, 센서 분석 |
| 2 | [Architecture](../2-architecture/) | 대기 | - | 세부 파이프라인, DB 스키마 설계 |
| 3+ | *Phase 2 완료 후 정의* | - | - | - |

**Phase별 상세 로그:** [phases/](phases/)

---

## ADR Summary (의사결정 요약)

> 상세 표는 [adr-summary.md](adr-summary.md) 참조

| # | 날짜 | 주제 | 결정 내용 |
|---|------|------|----------|
| ADR-000 | 2026-03-08 | 데이터 도메인 | CNC 단일 도메인으로 통일 |
| ADR-001 | 2026-03-08 | 예측 방식 | Forecasting 기반 접근으로 전환 |
| ADR-002 | 2026-03-08 | MES/ERP 확보 | Python으로 합성 생성 |
| ADR-003 | 2026-03-08 | DB 아키텍처 | PostgreSQL 통합 (시계열+관계형+벡터) + Neo4j 별도, 총 2개 DB |
| ADR-004 | 2026-03-08 | 실시간 처리 | 5초 폴링으로 실시간성 모사 |
| ADR-005 | 2026-03-09 | 대시보드 우선순위 | 시각적 결과물(대시보드 MVP) 앞당김 |

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
│       └── phase-0.md             #     Phase 0 진행 기록
├── 0-project-definition/          # Phase 0: 프로젝트 정의
│   ├── prd-v1.0.md                #   PRD (제품 요구사항 정의서)
│   ├── data-collection-strategy.md #   데이터 수집 전략 기준 문서
│   └── open-items.md              #   미결 사항 추적
├── future/                        # 향후 제품화/확장 비전
│   └── customer-onboarding-ontology-strategy.md
├── 1-data-exploration/            # Phase 1: 데이터 탐색 (EDA)
├── 2-architecture/                # Phase 2: 아키텍처 설계
└── adr/                           # ADR 템플릿
    └── 000-template.md
```
