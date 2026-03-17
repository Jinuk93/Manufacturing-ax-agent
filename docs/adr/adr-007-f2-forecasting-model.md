# ADR-007: F2 Forecasting 모델 선택

## Status
Decided

## Context

PRD에서 F2의 핵심 기능을 **"시계열 예측으로 30분 뒤 위험 임계치 돌파를 선제 감지"**로 정의했다 (ADR-001: RUL 대신 Forecasting).

Phase 3에서 이상탐지(Isolation Forest)는 구현됐으나, **시계열 예측(Forecasting)**은 미구현 상태다. "지금 이상한가"는 판단 가능하지만, "앞으로 이상해질까"는 판단 불가.

구현에 앞서 3가지 결정이 필요하다:
1. **모델 아키텍처**: LSTM vs 1D-CNN
2. **입력 피처 수**: 16개 전부 vs 핵심 4~5개
3. **기존 IF 점수와의 합산 방식**: 독립 vs 가중 합산

### 데이터 제약

| 항목 | 값 | 영향 |
|------|------|------|
| 총 데이터 | 25,286행 (42분) | 딥러닝 학습에 적은 양 |
| 샘플링 | 100ms | 고빈도 → 시퀀스가 짧아도 정보 풍부 |
| 실험당 길이 | 46초 ~ 231초 | PRD "30분 윈도우" 불가능 |
| 실험 수 | 18개 (unworn 8, worn 10) | 교차 검증 한계 |

---

## Options Considered

### 1. 모델 아키텍처

**Option A: LSTM (Long Short-Term Memory)**
- 시계열 예측의 전통적 선택
- 긴 시퀀스(수천 행)에서 장기 의존성 포착 가능
- 학습 느림, 하이퍼파라미터 튜닝 복잡

**Option B: 1D-CNN (1차원 합성곱 신경망)**
- 짧은 시퀀스(수백 행)에서 국소 패턴 추출에 강점
- 학습 빠름, 구조 단순
- 매우 긴 의존성 포착은 약함 (우리 데이터에서는 해당 없음)

### 2. 입력 피처 수

**Option A: 16개 전부 (기존 IF 피처셋)**
- IF와 동일 입력 → 일관성
- 25,286행으로 16차원 시계열 학습 → 과적합 위험 높음

**Option B: 핵심 4개만**
- X1_CurrentFeedback (마모 핵심), S1_CurrentFeedback (과열 핵심), S1_OutputPower (과열 보조), M1_CURRENT_FEEDRATE (가공 조건)
- EDA에서 worn/unworn 분리에 가장 기여한 센서들
- 적은 파라미터 → 25,286행으로도 안정적 학습

### 3. IF anomaly_score와 합산 방식

**Option A: max(if_score, forecast_score)** — 둘 중 높은 값
- 단순, 하나만 높아도 알람
- 한쪽이 노이즈에 민감하면 오경보 증가

**Option B: alpha * if_score + (1-alpha) * forecast_score** — 가중 평균
- FORECAST_WEIGHT config로 실험 가능
- 두 신호를 부드럽게 결합

**Option C: 별도 forecast_score 컬럼** — 독립 관리
- anomaly_scores 테이블에 컬럼 추가
- 합산 안 하고 각각 표시
- 프론트엔드에서 두 차트를 별도 표시 가능

---

## Decision

1. **1D-CNN** 베이스라인으로 시작 (Option B). 성능 부족 시 LSTM으로 교체.
2. **핵심 4피처**로 시작 (Option B). 실험적으로 추가.
3. **가중 합산 (Option B)** + forecast_score 별도 저장 (Option C 일부 채택).
   - `FORECAST_WEIGHT = 0.4` (기본값, config)
   - `final_score = (1 - weight) * if_score + weight * forecast_score`
   - anomaly_scores 테이블에 `forecast_score` 컬럼 추가 (독립 조회도 가능)

### 윈도우 조정

| PRD 원안 | 조정값 | 이유 |
|----------|--------|------|
| 30분 입력 | **30초 입력** (300행) | 실험당 1~4분, 30분 데이터 없음 |
| 30분 예측 | **30초 예측** (300행) | 최소 60초 실험에서 30+30 가능 |

---

## Reasoning

1. **1D-CNN 선택**: 입력 시퀀스가 300행(30초)으로 짧다. LSTM의 장기 의존성 포착 능력이 불필요하고, 1D-CNN이 국소 패턴(전류 급변, 진동 증가)을 빠르게 학습한다. 학습 속도도 5~10배 빠르다.

2. **4피처 선택**: 25,286행 × 16차원은 딥러닝에 적은 데이터다. Phase 1 EDA에서 worn/unworn 분리에 가장 기여한 4개 센서만 사용하면 과적합 위험을 줄이고, 해석 가능성도 높아진다.

3. **가중 합산 + 별도 저장**: IF는 "현재 패턴이 정상과 얼마나 다른가", Forecasting은 "미래에 위험해질 가능성이 얼마나 높은가"를 측정한다. 두 관점을 결합하되, 각각의 원본 점수도 보존하여 디버깅과 프론트엔드 표시에 활용한다.

4. **30초/30초 윈도우**: exp04(46초)와 exp05(52초)는 30+30=60초 미만이라 학습 샘플 생성이 불가하지만, 이 2개는 이미 `exclude_aborted=True`로 IF 학습에서도 제외 중이므로 실질적 영향 없음. 나머지 16개 실험(60초 이상)에서는 충분한 샘플 생성 가능.

---

## Consequences

- **긍정**: PRD의 "예지보전" 약속을 이행. "30초 후 전류 급증 예상" 선제 알람 가능.
- **제약**: 1D-CNN은 매우 긴 주기의 패턴(수 시간)을 감지하지 못함. 실제 현장 데이터가 있으면 LSTM/Transformer 재검토 필요.
- **제약**: 4피처만 사용하므로, 나머지 12피처에만 나타나는 이상 패턴은 Forecasting으로 감지 불가 (IF가 보완).
- **운영**: anomaly_scores 테이블에 forecast_score 컬럼 추가 → init.sql 수정 + 마이그레이션 필요.
- **실험**: FORECAST_WEIGHT 기본값 0.4는 가설. Phase 4 실험으로 최적값 결정.
