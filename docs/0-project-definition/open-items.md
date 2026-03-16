# 미결 사항 (Open Items)

**상태:** 관리 중
**최종 수정일:** 2026-03-15

PRD v1.0 시점에서 아직 결정되지 않은 항목들을 추적합니다.
각 항목은 해당 Phase 진입 시 ADR로 기록하며 확정합니다.

---

## A. 데이터 관련 (Phase 1에서 결정)

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 1 | ~~KAMP 데이터 실체 확인~~ → **timestamp/equipment_id 합성 설계** | timestamp: sequence×100ms→datetime (seed=42). equipment_id: exp01~06→CNC-001, 07~12→CNC-002, 13~18→CNC-003. `data/processed/kaggle-cnc-mill/`에 반영 완료 | Phase 1 Day 5 | **Decided** |
| 2 | 정비 매뉴얼 데이터 확보 방안 | 방향 결정: failure_code 4종 × 부품 5종 기준으로 **합성 매뉴얼 작성** (Phase 3). CNC 제조사 공개 문서로 보강 가능. IT 합성에서 failure_code 체계가 확정되어 범위 명확 | Phase 3 진입 시 구현 | **Partial** |
| 3 | 온톨로지 스키마 설계 방향 | 방향 결정: failure_code→부품→조치 관계가 IT 합성 스키마에서 초안 확정 ([it-data-synthesis-schema.md](../1-data-exploration/it-data-synthesis-schema.md)). Neo4j 노드/관계 설계는 Phase 3 | Phase 3 진입 시 구현 | **Partial** |
| 4 | 합성 데이터 시나리오 확정 | IT 합성 스키마 확정: failure_code 4종, 부품 5종, MES 18건, Maintenance 39건, ERP 35건. 조인 키 다이어그램 포함. 상세: [it-data-synthesis-schema.md](../1-data-exploration/it-data-synthesis-schema.md) | Phase 1 Day 5 | **Decided** |

## A-1. 내부 표준 형식 관련 (Phase 1~2에서 구체화)

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 5 | 내부 표준 형식(Canonical Model) 초안 | OT: 42유효컬럼 + timestamp + equipment_id 확정. IT: MES/ERP/Maintenance 컬럼 확정 ([it-data-synthesis-schema.md](../1-data-exploration/it-data-synthesis-schema.md)). DB 스키마는 Phase 2에서 구체화 | Phase 1 일부 해결, Phase 2 계속 | **Partial** |

## B. 모델링 관련 (Phase 1~2에서 결정)

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 6 | 이상 탐지 모델 선택 | IF vs AE vs 기타, 데이터 봐야 판단 | EDA 후 | Open |
| 7 | LSTM 예측 윈도우 크기 | "30분"은 가설, 데이터 패턴 봐야 검증 | 모델 실험 시 | Open |
| 8 | Anomaly Score 임계치 기준 | 몇 점 이상을 "이상"으로 판정할지 | 모델 실험 시 | Open |

## C. 시스템/인프라 관련 (Phase 2에서 결정)

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 9 | LLM 선택 (API vs 로컬) | 비용/성능 트레이드오프 미검토 | 아키텍처 설계 시 | Open |
| 10 | 하이브리드 검색 점수 결합 방식 | BM25 + Vector 비율/방식 미정 | GraphRAG 구현 시 | Open |
| 11 | ~~프론트엔드 MVP 전략~~ → **React 18 + Vite SPA** | SSR/SEO 불필요한 내부 관제 시스템. 페이지 2개 → Next.js 과함. React Router v6으로 충분 | Phase 2 완료 | **Decided (ADR-006)** |

## D. 프로젝트 관리

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 12 | Phase 3 이후 세부 마일스톤 | Phase 2 확정 후에야 이후 단계 정의 가능 | Phase 2 완료 후 | Open |

---

> **운영 규칙:**
> - 결정되면 상태를 `Decided`로 변경하고, 해당 ADR 번호를 기재
> - 불필요해지면 `Dropped`으로 변경하고 사유 기재
