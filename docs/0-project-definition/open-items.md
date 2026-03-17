# 미결 사항 (Open Items)

**상태:** 관리 중
**최종 수정일:** 2026-03-17

PRD v1.0 시점에서 아직 결정되지 않은 항목들을 추적합니다.
각 항목은 해당 Phase 진입 시 ADR로 기록하며 확정합니다.

---

## A. 데이터 관련 (Phase 1에서 결정)

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 1 | ~~KAMP 데이터 실체 확인~~ → **timestamp/equipment_id 합성 설계** | timestamp: sequence×100ms→datetime (seed=42). equipment_id: exp01~06→CNC-001, 07~12→CNC-002, 13~18→CNC-003. `data/processed/kaggle-cnc-mill/`에 반영 완료 | Phase 1 Day 5 | **Decided** |
| 2 | 정비 매뉴얼 데이터 확보 방안 | 4종 고장코드 × 3종 문서유형 = 12건 합성 완료 (`maintenance_manuals.json`). 47청크 → pgvector(384차원) 임베딩 완료 | Phase 3 | **Decided** |
| 3 | 온톨로지 스키마 설계 방향 | Neo4j 120노드 + 337관계 구축 완료. 7종 노드(Equipment, Sensor, FailureCode, Part, Document, WorkOrder, MaintenanceAction) + **10종 관계 전부 완성** (R2 DETECTS 7건 + R10 REFERENCES 90건 포함) | Phase 3 | **Decided** |
| 4 | 합성 데이터 시나리오 확정 | IT 합성 스키마 확정: failure_code 4종, 부품 5종, MES 18건, Maintenance 39건, ERP 35건. 조인 키 다이어그램 포함 | Phase 1 Day 5 | **Decided** |

## A-1. 내부 표준 형식 관련

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 5 | 내부 표준 형식(Canonical Model) | PostgreSQL **11테이블** + init.sql 완성 (llm_action_reports 추가). sensor_readings 44컬럼(와이드), anomaly_scores 7컬럼. Docker Compose로 실행 가능 | Phase 3 | **Decided** |

## B. 모델링 관련

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 6 | 이상 탐지 모델 선택 | Isolation Forest 선택 (f2-anomaly-detection-design.md). **16개 피처** (14 base + 2 파생: x_position_deviation, x_power_ratio), unworn fit, worn 검증. Autoencoder 비교는 후속 과제 | Phase 3 | **Decided** |
| 7 | LSTM 예측 윈도우 크기 | WINDOW_SIZE_SEC=30 (config 파라미터). Phase 3 후반 실험으로 조정 예정 | 모델 실험 시 | Open |
| 8 | Anomaly Score 임계치 기준 | ANOMALY_THRESHOLD=0.5 (config). STOP=0.8, REDUCE=0.6. Phase 3 후반 PR곡선으로 최적화 예정 | 모델 실험 시 | Open |

## C. 시스템/인프라 관련

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 9 | LLM 선택 (API vs 로컬) | OpenAI GPT-4o-mini 선택. JSON mode + 환각 검증 + 지수 백오프 재시도 구현 완료 | Phase 3 | **Decided** |
| 10 | 하이브리드 검색 점수 결합 방식 | HYBRID_ALPHA=0.5 (config). F4 Neo4j 순회 + pgvector 의미검색 2단계 실제 연동 완료. 점수 결합 가중치 최적화는 후속 과제 | Phase 3 후반 | **Partial** |
| 11 | ~~프론트엔드 MVP 전략~~ → **React 18 + Vite SPA** | SSR/SEO 불필요한 내부 관제 시스템. ADR-006 확정 | Phase 2 완료 | **Decided (ADR-006)** |

## D. 프로젝트 관리

| # | 항목 | 왜 미결인가 | 결정 시점 | 상태 |
|---|------|------------|-----------|------|
| 12 | Phase 3 이후 세부 마일스톤 | F4 Neo4j/pgvector 실제 연동, F2 개선, 메인 폴링 루프, 챗봇 등 | Phase 3 후반 | Open |

---

> **요약:** 12건 중 **8건 Decided** / **1건 Partial** (#10) / **3건 Open** (#7, #8, #12)
>
> **운영 규칙:**
> - 결정되면 상태를 `Decided`로 변경하고, 해당 ADR 번호를 기재
> - 불필요해지면 `Dropped`으로 변경하고 사유 기재
