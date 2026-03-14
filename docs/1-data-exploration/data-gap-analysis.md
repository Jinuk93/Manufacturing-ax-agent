# 데이터 갭 분석: 보유 현황 vs 실제 필요

**상태:** 확정
**최종 수정일:** 2026-03-15
**근거:** ADR-001 (RUL 포기 → Forecasting), ADR-002 (MES/ERP 합성)

Phase 1 진입 시점에서 "실제로 갖고 있는 것", "필요한데 없는 것", "갖고 있지만 필요 없는 것"을
정리한 갭 분석 문서입니다.

---

## 1. 보유 데이터 판정

| 데이터 | 위치 | 판정 | 사유 |
|--------|------|------|------|
| Kaggle CNC Mill (18실험 CSV) | `data/raw/kaggle-cnc-mill/` | **유지 — 핵심** | F1, F2의 핵심 입력. 42유효컬럼, 100ms 샘플링. ⚠ experiment_12 raw는 CR-only 줄바꿈(wc -l이 0으로 오인), 실제 2,276행 존재 |
| Bosch CNC (1,702 H5) | `data/raw/bosch-cnc/` | **유지 — 보조** | 3축 가속도(2kHz), good/bad 라벨. Kaggle과 조인 불가(별도 독립 데이터셋). 보관 근거: F1 멀티 소스 테스트 또는 Bosch 단독 진동 이상 탐지 모델용. Phase 2+에서 활용 여부 판단 |
| Multi-Sensor CNC | `data/raw/multi-sensor-cnc/` | **삭제** | 합성 데이터 의심, Kaggle+Bosch로 충분 |
| Milling Tool Wear & RUL | `data/raw/milling-rul/` | **삭제** | ADR-001로 RUL 포기. RUL 라벨이 핵심인 데이터셋이라 용도 없음 |
| KAMP 50종 카탈로그 | `data/raw/kamp/` | **삭제** | 메타데이터(목록)만 보유. 실제 센서 데이터 아님 |

---

## 2. 기능별 필요 데이터와 현재 상태

### 2.1. OT (현장/센서) — F1, F2

| 데이터 | 용도 | 상태 | 비고 |
|--------|------|------|------|
| 센서 시계열 (전류, 전력, 속도, 위치, 가속도) | F1 전처리 입력 | **확보** | Kaggle CNC Mill 42유효컬럼 |
| 가공 단계 (Machining_Process) | 정상 패턴을 단계별로 분리 | **확보** | 10단계 |
| 진동 센서 | 핵심에 없는 센서 보완 | **확보** | Bosch CNC (보조) |
| 공구 라벨 (worn/unworn) | F2 모델 성능 검증용 정답지 | **확보** | 이상탐지 입력이 아닌 검증용 |
| 육안검사 결과 (passed_visual_inspection) | 마모 vs 품질 관계 분석 | **확보** | yes/no/NaN. worn이지만 통과한 실험(#13,#14,#15,#18) 존재 — F2 검증 시 중요 |
| `timestamp` | 시계열 정렬 기준 | **확보 (합성 완료)** | sequence × 100ms → datetime (`data/processed/`) |
| `equipment_id` | 설비 단위 구분 키 | **확보 (합성 완료)** | experiment_01~06 → CNC-001, 07~12 → CNC-002, 13~18 → CNC-003 |
| 온도 센서 | 과열 감지 | **없음** | Phase 1 EDA에서 전류/전력의 간접 대체 가능성 검증 예정 |

**참고: 공구 라벨의 역할**

이상탐지는 "평소와 다른 패턴"을 찾는 것이므로, 공구 라벨은 입력이 아닙니다.
다만 Forecasting 모델이 예측한 결과가 실제 마모 상태와 맞는지 **검증**할 때 사용됩니다.

### 2.2. IT (업무 시스템) — F3

F3의 역할은 OT(센서)와 IT(업무 시스템)를 시간 기준으로 동기화하는 것입니다.

```
센서(OT): "X축 전류 급상승!" (언제? 14:30:05)
    +
MES(IT):  "지금 긴급 납기 작업 중" (14:00~16:00)
ERP(IT):  "베어링 재고 0개, 리드타임 5일"
    ↓
F3 출력:  "14:30에 이상 발생, 긴급 작업 중, 부품 없음"
    ↓
F5(LLM):  "감속 운전 + 긴급 발주 권고"
```

| 데이터 | 용도 | 상태 | 비고 |
|--------|------|------|------|
| MES 작업지시 (work_order, due_date, priority) | 알람 시점의 업무 맥락 | **확보** | Phase 1에서 합성 완료 (`data/processed/it-data/`) |
| ERP 부품 재고 (part_id, stock, lead_time) | 즉시 교체 가능 여부 판단 | **확보** | Phase 1에서 합성 완료 (`data/processed/it-data/`) |
| 정비/고장 이벤트 로그 (failure_code, maintenance_time) | 이상 신호와 실제 고장 연결 | **확보** | Phase 1에서 합성 완료 (`data/processed/it-data/`) |

### 2.3. 지식 (온톨로지) — F4

| 데이터 | 용도 | 상태 | 비고 |
|--------|------|------|------|
| 설비→고장코드→부품→매뉴얼 관계 | Neo4j 지식그래프 뼈대 | **없음** | Phase 3 설계 |
| 고장 코드 체계 (E-001 = 스핀들 과열 등) | 온톨로지 핵심 노드 | **없음** | Phase 3 설계 |
| 정비 매뉴얼 텍스트 | GraphRAG 검색 대상 | **없음** | Phase 3 수집/합성 |

### 2.4. 조합 — F5, F6

| 기능 | 입력 | 상태 |
|------|------|------|
| F5 LLM 자율 판단 | F2 + F3 + F4 출력 조합 | 앞 기능 완성 대기 (별도 데이터 수집 불필요) |
| F6 대시보드 | F1~F5 전체 출력 시각화 | 점진 구축 |

---

## 3. 갭 요약: Phase별 해결 계획

### Phase 1 (지금)

- [x] 불필요 데이터 삭제: `multi-sensor-cnc/`, `milling-rul/`, `kamp/`
- [x] `timestamp` 합성: sequence × 100ms → datetime (`data/processed/`)
- [x] EDA로 유효 42컬럼 검증 및 확정 (이상치 분석 완료, [outlier-analysis.md](outlier-analysis.md) 참고)
- [x] `equipment_id` 매핑: 순번 기반 3대 분산 (CNC-001~003, 편중 문서화)

### Phase 1에서 선행 완료 (원래 Phase 2 계획)

- [x] MES 작업지시 합성 (18건, `data/processed/it-data/mes_work_orders.csv`)
- [x] ERP 부품 재고 스냅샷 합성 (7주 × 5부품, `data/processed/it-data/erp_inventory_snapshots.csv`)
- [x] 정비/고장 이벤트 로그 합성 (39건, `data/processed/it-data/maintenance_events.csv`)
- [x] IT/OT 합성 시나리오 설계 ([it-data-synthesis-schema.md](it-data-synthesis-schema.md) 참고)

### Phase 3 (온톨로지 구축)

- [ ] 설비→고장→부품→매뉴얼 관계 스키마 설계
- [ ] 고장 코드 체계 정의
- [ ] 정비 매뉴얼 텍스트 수집/합성

---

## 4. 핵심 데이터셋 정리 (확정)

이 프로젝트에서 사용하는 데이터셋은 **2종**입니다.

| # | 데이터셋 | 역할 | 매핑 기능 | 출처 |
|---|---------|------|----------|------|
| 1 | Kaggle CNC Mill Tool Wear | 핵심 | F1, F2 | [Kaggle](https://www.kaggle.com/datasets/shasun/tool-wear-detection-in-cnc-mill) |
| 2 | Bosch CNC Machining | 보조 (진동) | F1 보조 | [GitHub](https://github.com/boschresearch/CNC_Machining) |

나머지 데이터(MES, ERP, 이벤트 로그, 온톨로지)는 전부 **합성하거나 직접 설계**합니다.

### 제외된 데이터셋

| 데이터셋 | 제외 사유 |
|---------|----------|
| Multi-Sensor CNC Tool Wear | 합성 데이터 의심 (센서값 분포 불자연), Kaggle+Bosch로 충분 |
| Milling Tool Wear & RUL | ADR-001에서 RUL 포기. 이 데이터셋의 핵심인 RUL 라벨을 사용하지 않음 |
| KAMP 50종 카탈로그 | 메타데이터(목록)만 보유. 실제 센서 데이터 아님. Kaggle CNC Mill로 대체 |

---

## 5. 관련 문서

- [data-collection-strategy.md](../0-project-definition/data-collection-strategy.md) — 데이터 수집 전략 (Phase 0 기준)
- [required-data-summary.md](../0-project-definition/required-data-summary.md) — 필요 데이터 정리표 (Phase 0 기준)
- [open-items.md](../0-project-definition/open-items.md) — 미결 사항
- ADR-001 — RUL 포기, Forecasting 방식
- ADR-002 — MES/ERP 합성 데이터
