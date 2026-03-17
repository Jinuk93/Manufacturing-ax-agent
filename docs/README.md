# Docs

manufacturing-ax-agent 프로젝트의 의사결정 과정과 관리 문서를 기록하는 공간입니다.

## 구성 원칙

- 애자일하게 필요한 시점에 폴더와 문서를 생성합니다.
- 각 문서는 "왜 이렇게 결정했는가(Why)"에 집중합니다.
- 기술 실험/연구 결과는 필요 시 별도 폴더로 분리합니다.

## 폴더 구조

```
docs/
├── README.md                         ← 이 파일 (폴더 구조 안내)
├── 0-project-definition/
│   ├── README.md                     ← Phase 0 색인
│   ├── prd-v1.0.md                   ← 제품 요구사항 정의서
│   ├── data-collection-strategy.md   ← 데이터 수집 전략 (v2)
│   ├── required-data-summary.md      ← F1~F6 데이터 매핑
│   └── open-items.md                 ← 미결사항 12건 (9 Decided / 1 Partial / 2 Open)
├── 1-data-exploration/
│   ├── README.md                     ← Phase 1 완료 요약
│   ├── data-gap-analysis.md          ← 데이터 갭 분석
│   ├── it-data-synthesis-schema.md   ← IT 합성 스키마 (MES/ERP/Maintenance)
│   └── outlier-analysis.md           ← 이상치 분석 (42컬럼 확정)
├── 2-architecture/
│   ├── README.md                     ← Phase 2 색인
│   ├── ontology-design.md            ← Neo4j 온톨로지 (120노드, 337관계)
│   ├── db-schema-design.md           ← PostgreSQL 11테이블 + Neo4j
│   ├── pipeline-design.md            ← F1~F6 파이프라인 데이터 흐름
│   ├── api-design.md                 ← FastAPI 16 엔드포인트
│   ├── ui-design.md                  ← F6 대시보드 초기 설계 (v1)
│   ├── ui-ux-design.md               ← F6 대시보드 최종 설계 (v4, Palantir 3-Pane)
│   └── f2-anomaly-detection-design.md ← F2 이상탐지 상세 설계 (16피처)
├── adr/
│   ├── 000-template.md               ← ADR 템플릿
│   ├── adr-006-frontend-stack.md     ← React 18 + Vite 선택
│   └── adr-007-f2-forecasting-model.md ← 1D-CNN + 4피처 + 가중합산
├── progress/
│   ├── overview.md                   ← 프로젝트 전체 현황
│   ├── adr-summary.md                ← ADR 요약 테이블 (000~007)
│   ├── constraints.md                ← 핵심 제약사항
│   └── phases/
│       ├── phase-0.md                ← Phase 0 일일 로그
│       ├── phase-1.md                ← Phase 1 일일 로그
│       ├── phase-2.md                ← Phase 2 일일 로그
│       ├── phase-3.md                ← Phase 3 일일 로그
│       ├── phase3-late-report.md     ← Phase 3 후반 개선 보고서
│       ├── chatbot-test-report.md    ← 챗봇 테스트 보고서
│       └── forecast-backfill-log.md  ← F2 Forecast backfill 작업 기록
├── future/
│   └── customer-onboarding-ontology-strategy.md ← 향후 고객 온보딩 전략
└── prompts/
    └── maintenance-manual-generation.md ← 정비 매뉴얼 v2 생성 프롬프트
```
