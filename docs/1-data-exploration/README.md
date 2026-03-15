# Phase 1: Data Exploration — ✅ 완료

**기간:** 2026-03-10 ~ 2026-03-15
**상세 로그:** [phases/phase-1.md](../progress/phases/phase-1.md)

Kaggle CNC Mill을 주력으로, Bosch CNC를 보조로 탐색(EDA)하여 "우리가 실제로 무엇을 갖고 있는가"를 파악하는 단계입니다.

---

## 핵심 질문과 답변

| 질문 | 답변 | 근거 |
|------|------|------|
| 실제 유효 분석 컬럼은? | 42개 (원본 48 - Z축 전기 4 - 상수 1 - 행 순서번호 1) | [outlier-analysis.md](outlier-analysis.md) |
| `sequence`를 어떻게 `timestamp`로 바꾸나? | sequence × 100ms → datetime, 기준일 2024-01-15 | `scripts/synthesize_timestamp.py` |
| `experiment`를 어떻게 `equipment_id`에 매핑하나? | exp01~06→CNC-001, 07~12→CNC-002, 13~18→CNC-003 | `scripts/synthesize_equipment_id.py` |
| Canonical Model 최소 입력 컬럼은? | 42유효 센서 + timestamp + equipment_id | [data-gap-analysis.md](data-gap-analysis.md) |
| IT 데이터(MES/ERP)는 어떻게 확보하나? | OT 메타데이터 기반 합성 (18+39+35건) | [it-data-synthesis-schema.md](it-data-synthesis-schema.md) |

---

## 이 폴더의 문서

| 문서 | 설명 |
|------|------|
| [data-gap-analysis.md](data-gap-analysis.md) | 보유 데이터 vs 필요 데이터 갭 분석. 데이터셋 2종 확정, Phase별 해결 계획 |
| [outlier-analysis.md](outlier-analysis.md) | README 경고 조건 전수 조사. FR=50, X1≈198, Prog≠0 판정. 42컬럼 확정 |
| [it-data-synthesis-schema.md](it-data-synthesis-schema.md) | IT 합성 스키마: failure_code 4종, 부품 5종, MES/Maintenance/ERP 스키마 |

---

## Phase 1 완료 체크리스트

- [x] 불필요 데이터 삭제 (multi-sensor-cnc, milling-rul, kamp → 총 ~848KB)
- [x] EDA 이상치 분석 — 42유효컬럼 확정 ([outlier-analysis.md](outlier-analysis.md))
- [x] `timestamp` 합성 — 100ms 샘플링, 2024-01-15 ~ 2024-02-21 (`data/processed/`)
- [x] `equipment_id` 매핑 — 3대 분산 (CNC-001~003)
- [x] Bosch CNC 데이터 탐색 — 3축 가속도(2kHz), 1,702 H5 파일, Kaggle과 조인 불가
- [x] IT 데이터 합성: MES 작업지시 (18건)
- [x] IT 데이터 합성: Maintenance 정비 이벤트 (39건)
- [x] IT 데이터 합성: ERP 부품 재고 스냅샷 (35건)
- [x] IT 합성 스키마 문서화 ([it-data-synthesis-schema.md](it-data-synthesis-schema.md))

---

## 생성된 데이터

| 경로 | 내용 | 건수 |
|------|------|------|
| `data/processed/kaggle-cnc-mill/` | timestamp + equipment_id 추가된 18개 실험 CSV + train.csv | 25,286행 |
| `data/processed/it-data/mes_work_orders.csv` | MES 작업지시 | 18건 |
| `data/processed/it-data/maintenance_events.csv` | 정비 이벤트 (corrective 12 + preventive 27) | 39건 |
| `data/processed/it-data/erp_inventory_snapshots.csv` | ERP 재고 스냅샷 (7주 × 5부품) | 35건 |

---

## Phase 2 인수 사항

Phase 2(Architecture)로 넘기는 핵심 정보:

1. **OT 데이터**: 42컬럼, 100ms 샘플링, 3대 설비 × 18실험
2. **IT 데이터**: MES/ERP/Maintenance 합성 완료, 조인 키 확정 (equipment_id + timestamp)
3. **미결 사항**: 이상탐지 모델 선택(#6), LSTM 윈도우(#7), 임계치(#8), LLM 선택(#9) → [open-items.md](../0-project-definition/open-items.md)
4. **알려진 시나리오**: W5 냉각수 재고 0 → Phase 2 F5 LLM 테스트 케이스
