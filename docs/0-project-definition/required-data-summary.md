# 필요한 데이터 정리표

**상태:** Draft (검토 중)
**최종 수정일:** 2026-03-09

이 문서는 현재 프로젝트에서 필요한 데이터를
"실제로 수집할 것", "합성으로 만들 것", "미정 또는 혼합 방식으로 갈 것"으로 나누어 정리합니다.

핵심 목적은 아래 2가지입니다.

1. 지금 당장 무엇을 확보해야 하는지 빠르게 판단하기
2. 예지보전이 단일 데이터가 아니라 여러 데이터를 연결해서 만들어지는 구조라는 점을 명확히 이해하기

이 문서는 [data-collection-strategy.md](data-collection-strategy.md)를 보조하는 요약/설명 문서입니다.

---

## 1. 먼저 이해해야 할 핵심

이 프로젝트에서 **예지보전 데이터**라는 단일 테이블이 따로 있는 것은 아닙니다.

예지보전은 아래 데이터가 합쳐져서 만들어집니다.

- SCADA / 센서 시계열
- 알람 / 정비 / 고장 이벤트 로그
- MES 작업지시 및 운영 맥락
- ERP 재고 및 부품 정보
- 온톨로지와 정비 문서

즉,

**예지보전 = 센서 신호 + 이벤트 근거 + 운영 맥락 + 자원 맥락 + 정비 지식**

입니다.

그래서 지금 해야 할 일은
"예지보전 데이터셋 하나를 찾는 것"이 아니라,
어떤 데이터를 어떻게 연결해서 예지보전 판단을 만들지 정리하는 것입니다.

---

## 2. 한눈에 보는 정리표

| 구분 | 데이터 종류 | 현재 방식 | 왜 필요한가 | 대표 키 / 컬럼 |
|------|-------------|----------|-------------|----------------|
| 실제 수집 | SCADA / CNC 센서 시계열 | KAMP 공공 데이터 수집 | F1 전처리, F2 이상탐지, forecasting 핵심 입력 | equipment_id, timestamp, vibration, current, temperature, spindle_speed |
| 실제 수집 가능 | 공개 정비 매뉴얼 / 기술 문서 | 공개 자료 수집 | F4 GraphRAG, 정비 지식 근거 확보 | manual_id, equipment_type, part_id, symptom_keyword |
| 합성 생성 | MES 작업지시 데이터 | Python 합성 | 알람 시점의 작업 상태, 납기, 생산 맥락 판단 | work_order_id, equipment_id, start_time, end_time, due_date, priority |
| 합성 생성 | ERP 부품 재고 데이터 | Python 합성 | 부품 재고, 리드타임, 즉시 정지 가능 여부 판단 | part_id, equipment_id, stock_quantity, lead_time_days, snapshot_time |
| 합성 생성 | 운영 / 정비 이벤트 로그 | 최소 버전 합성 | 센서 패턴과 실제 조치/고장 이벤트 연결 | equipment_id, part_id, maintenance_time, action_type, failure_code |
| 미정 또는 혼합 | 온톨로지 관계 데이터 | 공개 자료 + 직접 설계 혼합 가능성 | 설비-고장-부품-매뉴얼 관계 정의 | equipment_type, failure_code, part_id, manual_id |
| 미정 또는 혼합 | 정비 매뉴얼 텍스트 | 공개 수집 + 합성 보강 가능성 | GraphRAG 검색 대상 문서 | manual_id, title, section, text_chunk |
| EDA 후 구체화 | 내부 표준 형식(Canonical Model) | 원칙만 확정 | raw 데이터를 F1~F6 공통 입력 형식으로 정규화 | equipment_id, timestamp, sensor_type, value 등 |

### 기능별 데이터 확보 방식 요약

| 기능 | 실제 수집 | 합성 생성 | 직접 설계 | 앞 기능 출력 |
|------|:---------:|:---------:|:---------:|:----------:|
| **F1** 센서 전처리 | ✅ | | | |
| **F2** 이상탐지/Forecasting | ✅ | ✅ | | ✅ F1 |
| **F3** IT/OT 동기화 | | ✅ | | ✅ F1 |
| **F4** GraphRAG | ✅ | ✅ | ✅ | |
| **F5** LLM 조치 제안 | | | | ✅ F2+F3+F4 |
| **F6** 대시보드 | | | | ✅ F1~F5 |

### 기능별 필요 데이터셋 상세 매핑

| 기능 | 기능명 | 필요한 데이터 | 확보 방식 | 데이터셋 출처 |
|------|--------|--------------|-----------|--------------|
| F1 | 센서 전처리 | CNC 센서 시계열 (위치, 속도, 전류, 전력 등) | 실제 수집 | [Kaggle CNC Mill Tool Wear](https://www.kaggle.com/datasets/shasun/tool-wear-detection-in-cnc-mill) (48컬럼, 18실험) |
| F1 | 센서 전처리 | 보조 CNC 센서 (진동, 전류) | 실제 수집 | [KAMP 공공데이터](https://www.data.go.kr/data/15089213/fileData.do) / [Bosch CNC](https://github.com/boschresearch/CNC_Machining) |
| F2 | 이상탐지 + Forecasting | F1 전처리 결과 (정규화된 센서 시계열) | F1 출력 | ← F1에서 전처리된 데이터 |
| F2 | 이상탐지 + Forecasting | 공구 상태 라벨 (unworn/worn) | 실제 수집 | [Kaggle CNC Mill Tool Wear](https://www.kaggle.com/datasets/shasun/tool-wear-detection-in-cnc-mill) (tool_condition) |
| F2 | 이상탐지 + Forecasting | 정비/고장 이벤트 로그 | 합성 생성 | Python 합성 (equipment_id, failure_code, maintenance_time) |
| F3 | IT/OT 동기화 | MES 작업지시 데이터 | 합성 생성 | Python 합성 (work_order_id, due_date, priority, status) |
| F3 | IT/OT 동기화 | ERP 부품 재고 데이터 | 합성 생성 | Python 합성 (part_id, stock_quantity, lead_time_days) |
| F3 | IT/OT 동기화 | 센서 데이터 (OT 측) | F1 출력 | ← F1에서 전처리된 데이터 |
| F4 | GraphRAG 검색 | 온톨로지 관계 데이터 (설비→고장→부품→매뉴얼) | 직접 설계 | Neo4j에 수동 구축 |
| F4 | GraphRAG 검색 | 정비 매뉴얼 텍스트 | 공개 수집 + 합성 | CNC 제조사 공개 문서 + 합성 보강 |
| F5 | LLM 조치 제안 | F2 이상탐지 결과 + F3 운영 맥락 + F4 검색 결과 | 앞 기능 출력 | ← F2 + F3 + F4 출력 조합 |
| F6 | 대시보드 | F1~F5 전체 출력 | 앞 기능 출력 | ← 모든 기능의 결과를 시각화 |

### 외부 데이터셋 출처 목록

| 데이터셋 | 출처 | 용도 | 비고 |
|----------|------|------|------|
| CNC Mill Tool Wear | [Kaggle](https://www.kaggle.com/datasets/shasun/tool-wear-detection-in-cnc-mill) | F1, F2 핵심 입력 | 48컬럼, 18실험, 100ms 샘플링, tool_condition 라벨 |
| KAMP 제조 AI 데이터셋 | [공공데이터포털](https://www.data.go.kr/data/15089213/fileData.do) | F1 보조 데이터 | CNC 포함 50종, 가이드북 포함 |
| Bosch CNC Machining | [GitHub](https://github.com/boschresearch/CNC_Machining) | F1 보조 데이터 | 실제 산업 진동 데이터 |
| Milling Tool Wear & RUL | [Kaggle](https://www.kaggle.com/datasets/programmer3/milling-tool-wear-and-rul-dataset) | F2 참고 | 공구 수명 예측용, 진동+전류 |
| Multi-Sensor CNC Tool Wear | [Kaggle](https://www.kaggle.com/datasets/ziya07/multi-sensor-cnc-tool-wear-dataset/data) | F2 참고 | 다중 센서 데이터 |

> **핵심:** 직접 확보해야 하는 것은 딱 2가지입니다.
> 1. **Kaggle CNC Mill Tool Wear** → F1, F2의 핵심 입력
> 2. **공개 정비 매뉴얼** → F4 GraphRAG의 텍스트 근거
>
> 나머지는 전부 합성하거나(F3 MES/ERP, F2 이벤트 로그), 직접 설계하거나(F4 온톨로지), 앞 기능의 출력을 이어받는 구조(F5, F6)입니다.

---

## 3. 실제로 수집해야 할 것

### 3.1. SCADA / CNC 센서 데이터

이건 지금 프로젝트에서 가장 먼저 확보해야 하는 실데이터입니다.

왜 필요한가:

- F1 전처리의 출발점
- F2 이상탐지와 forecasting의 핵심 입력
- 전체 시스템의 시간축 기준

우선 확인할 항목:

- `timestamp`
- `equipment_id`
- 진동
- 전류
- 온도
- 주축 속도

현재 확보 방식:

- KAMP 공공 데이터 다운로드
- Phase 1 EDA에서 실제 컬럼과 주기 확인

### 3.2. 공개 정비 문서 / 기술 자료

가능하면 실제로 수집하는 것이 좋은 데이터입니다.

왜 필요한가:

- GraphRAG의 텍스트 근거
- 온톨로지 관계를 검증하거나 보강하는 문서 근거
- LLM이 출처 기반으로 답변하도록 만들기 위함

예시 자료:

- CNC 제조사 공개 매뉴얼
- 공개 기술 문서
- 정비 체크리스트
- CNC 정비 관련 기술 블로그, 논문

---

## 4. 우리가 합성해서 만들어야 할 것

### 4.1. MES 작업지시 데이터

이 데이터는 현재 프로젝트에서 합성 생성이 사실상 확정된 영역입니다. (ADR-002)

왜 필요한가:

- 알람 시점에 어떤 작업이 진행 중인지 보기 위해
- 납기 긴급도와 생산 잔량을 판단하기 위해
- 설비를 멈출지, 감속할지, 계획 정비로 넘길지 판단하기 위해

대표 컬럼:

- `work_order_id`
- `equipment_id`
- `product_name`
- `order_quantity`
- `completed_quantity`
- `due_date`
- `priority`
- `status`
- `start_time`
- `end_time`

### 4.2. ERP 부품 재고 데이터

이 데이터도 현재 프로젝트에서는 합성 생성이 기본입니다. (ADR-002)

왜 필요한가:

- 필요한 부품이 실제로 있는지 보기 위해
- 재고 부족 시 감속 운전 또는 긴급 발주 판단을 위해
- 최근 교체 이력과 재고 상태를 함께 보기 위해

대표 컬럼:

- `part_id`
- `part_name`
- `equipment_id`
- `stock_quantity`
- `min_stock`
- `lead_time_days`
- `unit_price`
- `last_replaced`
- `snapshot_time`

### 4.3. 운영 / 정비 이벤트 로그

이 부분은 자주 빠뜨리기 쉬운데,
예지보전 해석력을 높이려면 최소 버전이라도 합성하는 것이 좋습니다.

왜 필요한가:

- 센서 이상 패턴이 실제 정비/고장 이벤트와 어떻게 연결되는지 보기 위해
- 단순 노이즈와 실제 전조를 구분하는 근거로 쓰기 위해

대표 컬럼:

- `equipment_id`
- `part_id`
- `maintenance_time`
- `action_type`
- `failure_code`

---

## 5. 미정이거나 혼합 방식으로 갈 것

### 5.1. 온톨로지 관계 데이터

현재 가장 현실적인 방향은 완전 자동 수집보다,
**최소 스키마를 직접 설계하고 공개 자료로 근거를 보강하는 혼합 방식**입니다.

왜 필요한가:

- 설비와 고장, 부품, 조치, 매뉴얼을 구조적으로 연결하기 위해
- F4 GraphRAG가 단순 문서 검색이 아니라 관계 탐색을 할 수 있게 하기 위해

핵심 관계 예시:

- 설비 -> 고장 코드
- 고장 코드 -> 필요 부품
- 고장 코드 -> 조치 절차
- 조치 절차 -> 매뉴얼 문서

### 5.2. 정비 매뉴얼 텍스트

정비 매뉴얼은 GraphRAG 검색 대상 텍스트이므로,
공개 수집과 합성 보강을 섞는 방식이 현실적입니다.

왜 필요한가:

- 유사 증상, 조치 절차, 주의사항을 텍스트로 검색하기 위해
- LLM이 근거 있는 조치 리포트를 작성하게 하기 위해

---

## 6. 예지보전 데이터는 어떻게 구성되는가

이 부분이 프로젝트의 핵심입니다.

예지보전은 아래 조합으로 만들어집니다.

### 6.1. 센서 신호

- 진동
- 전류
- 온도
- 회전수

역할:

- 이상탐지
- forecasting
- 위험 신호 포착

### 6.2. 이벤트 근거

- 알람 발생 시점
- 정비 시점
- 부품 교체 시점
- 고장 시점

역할:

- 센서 패턴의 의미 해석
- 전조와 실제 이벤트 연결

### 6.3. 운영 맥락

- 현재 작업지시
- 납기 긴급도
- 생산 잔량
- 작업 상태

역할:

- 지금 멈출지, 감속할지, 계획 정비로 넘길지 판단

### 6.4. 자원 맥락

- 부품 재고
- 리드타임
- 최근 교체 이력

역할:

- 실제 조치 가능성 판단
- 부품 부족 시 대안 판단

### 6.5. 정비 지식

- 고장 코드
- 조치 절차
- 점검 항목
- 매뉴얼 문서

역할:

- GraphRAG 검색
- LLM 조치 리포트의 근거 제공

즉,

**예지보전은 센서만으로 끝나는 문제가 아니라,
센서 + 이벤트 + 운영 + 자원 + 지식을 연결해야 완성됩니다.**

---

## 7. 지금 기준의 현실적인 우선순위

아래 순서로 가는 것이 가장 현실적입니다.

1. KAMP 센서 데이터를 실제로 확보한다.
2. EDA를 통해 실제 컬럼, 주기, 결측 현황을 확인한다.
3. 그 결과에 맞춰 MES/ERP 합성 스키마를 고정한다.
4. 예지보전 해석용 이벤트 로그 최소 버전을 설계한다.
5. 온톨로지와 정비 매뉴얼은 작은 범위로 혼합 구축한다.

---

## 8. 향후 고객사 확장 시 실제로 받고 싶은 데이터

현재 개인 프로젝트에서는 없지만,
향후 고객사 확장 관점에서는 아래 데이터가 실제로 들어오면 예지보전 품질이 크게 올라갑니다.

- 실제 정비 로그
- 실제 고장 이벤트 로그
- 실제 알람 이력
- 실제 MES 마스터 데이터
- 실제 ERP 마스터 데이터
- 실제 설비/부품 코드 체계

이 데이터들은 향후 [customer-onboarding-ontology-strategy.md](../future/customer-onboarding-ontology-strategy.md)에서 다룬
고객 온보딩과 Canonical Model 설계로 이어질 수 있습니다.

---

## 9. 결론

지금 프로젝트에서 실제로 꼭 수집해야 하는 핵심은 SCADA / 센서 데이터입니다.
MES와 ERP는 합성으로 가는 것이 현실적이고,
예지보전 해석력을 위해 운영/정비 이벤트 로그도 최소 버전 합성이 필요합니다.

그리고 가장 중요한 관점은 아래 한 줄입니다.

**예지보전은 하나의 데이터셋을 찾는 문제가 아니라,
여러 데이터를 연결해서 만드는 문제입니다.**