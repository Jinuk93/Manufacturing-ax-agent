# Docs

manufacturing-ax-agent 프로젝트의 의사결정 과정과 관리 문서를 기록하는 공간입니다.

## 구성 원칙

- 애자일하게 필요한 시점에 폴더와 문서를 생성합니다.
- 각 문서는 "왜 이렇게 결정했는가(Why)"에 집중합니다.
- 기술 실험/연구 결과는 필요 시 별도 폴더로 분리합니다.

## 폴더 구조

```
docs/
├── progress/                      # 프로젝트 진행 관리
│   ├── overview.md                #   전체 현황 요약
│   ├── adr-summary.md             #   ADR 의사결정 요약 표
│   ├── constraints.md             #   Key Constraints + 설계 원칙
│   └── phases/                    #   Phase별 날짜별 로그
│       └── phase-0.md             #     Phase 0 진행 기록
├── 0-project-definition/          # Phase 0: 프로젝트 정의
│   ├── prd-v1.0.md                #   PRD (제품 요구사항 정의서)
│   ├── data-collection-strategy.md #   데이터 수집 전략 기준 문서
│   ├── required-data-summary.md   #   실수집/합성/미정 데이터 요약표
│   └── open-items.md              #   미결 사항 추적
├── future/                        # 향후 제품화/확장 비전
│   └── customer-onboarding-ontology-strategy.md
├── 1-data-exploration/            # Phase 1: Kaggle/Bosch 기반 데이터 탐색 (EDA)
├── 2-architecture/                # Phase 2: 아키텍처 설계
└── adr/                           # ADR 템플릿
    └── 000-template.md
```

> 이 프로젝트는 애자일 원칙에 따라, Phase 3 이후의 폴더는 Phase 2 완료 후 필요 시 생성합니다.
