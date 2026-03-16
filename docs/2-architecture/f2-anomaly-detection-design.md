# F2 이상탐지 상세 설계

**상태:** Phase 3 선결 과제 → 확정
**최종 수정일:** 2026-03-16

---

## 1. 접근 방식: 비지도 학습

### 왜 비지도인가
- 센서별 "이상/정상" **시점 라벨이 없음**
- worn/unworn 라벨은 실험 단위(공구 전체)이지, 5초 단위가 아님
- "이 구간이 이상이다"라는 ground truth 없음
- → **정상 패턴을 학습하고, 거기서 벗어나면 이상**으로 판단

### 모델 실험 순서
1. **Isolation Forest (IF)** — 베이스라인 (먼저)
2. **Autoencoder (AE)** — IF 성능이 부족할 때 시도

| | Isolation Forest | Autoencoder |
|--|-----------------|-------------|
| 구현 | scikit-learn 3줄 | PyTorch 모델 설계 |
| 학습 시간 | 수 초 | 수 분~시간 |
| 해석 가능성 | 피처 중요도 바로 확인 | 블랙박스 |
| 베이스라인 | ✅ 빠르게 "이 정도 나온다" 확인 | IF 결과와 비교 |

---

## 2. 1차 피처셋 (EDA 기반)

Phase 1 EDA에서 발견한 핵심 패턴을 기반으로 선정.

### 핵심 피처 (10개)

| # | 피처 | EDA 근거 | 역할 |
|---|------|----------|------|
| 1 | X1_CurrentFeedback | worn -47% 감소 | **공구 마모 핵심 지표** |
| 2 | Y1_CurrentFeedback | worn 시 변동 | 마모 보조 지표 |
| 3 | S1_CurrentFeedback | 스핀들 전류 | 과열 지표 |
| 4 | X1_OutputPower | worn +36% 증가 | 절삭 부하 |
| 5 | S1_OutputPower | 스핀들 전력 | 과열 부하 |
| 6 | X1_ActualVelocity | 명령 대비 편차 | 마모 시 속도 미달 |
| 7 | X1_CommandVelocity | 기준값 | 편차 계산용 |
| 8 | S1_ActualVelocity | 스핀들 실제 속도 | 과열 시 속도 미달 |
| 9 | M1_CURRENT_FEEDRATE | 이송속도 | feedrate=50은 비절삭 구간 |
| 10 | Machining_Process | 가공 단계 | 공정별 정상 범위가 다름 |

### 확장 후보 (Phase 3 후반)
- 축 간 편차: `X1_ActualPosition - X1_CommandPosition`
- 이동표준편차: 최근 30초 변동성
- FFT 주파수 특성 (고급)

---

## 3. 전처리 파이프라인

```
원본 센서값 (42컬럼)
    ↓
피처 선택 (10개)
    ↓
정규화 (MinMaxScaler, 0~1)
    ↓
슬라이딩 윈도우 (WINDOW_SIZE_SEC=30, 6행)
    ↓
파생 변수 (이동평균, 이동표준편차, 변화율)
    ↓
모델 입력 텐서
```

### 정규화 방식
- **MinMaxScaler**: 센서마다 단위가 다르므로 0~1 범위로 통일
- 학습 데이터(unworn 실험)의 min/max로 fit → 전체에 transform
- unworn 기준으로 fit하는 이유: "정상 범위"를 정의해야 이상을 감지할 수 있음

### 슬라이딩 윈도우
- 30초 = 6행 (5초 폴링 기준)
- 한 시점만 보면 정상인데, 30초간 계속 오르고 있으면 이상
- Phase 3에서 WINDOW_SIZE_SEC 조정 실험

---

## 4. 검증 전략

### 준지도 검증 (worn/unworn 라벨 활용)
- 학습: unworn 실험(8개)으로 "정상 패턴" 학습
- 검증: worn 실험(10개)에서 이상 점수가 높게 나오는지 확인
- 기대: worn 실험의 평균 anomaly_score > unworn 실험의 평균 anomaly_score

### 고장코드 매핑 검증
- exp07, exp16 (중단 + worn + 고속) → SPINDLE_OVERHEAT_001 패턴 나오는지
- exp04, exp05 (중단 + unworn + 저압) → CLAMP_PRESSURE_001 패턴 나오는지

### 평가 지표
- **분포 분리도**: worn vs unworn의 anomaly_score 분포가 얼마나 분리되는가
- **중단 실험 감지율**: 4건의 중단 실험(04, 05, 07, 16)에서 이상 감지 비율
- **오탐률**: unworn 정상 실험에서 이상으로 잘못 판단하는 비율

---

## 5. 실행 계획

```
Step 1: IF로 전체 데이터 이상점수 산출
  - unworn 8개 실험으로 fit
  - 전체 18개 실험에 predict
  - anomaly_score 분포 시각화

Step 2: 검증
  - worn vs unworn 분포 비교
  - 중단 실험 4건 감지 여부
  - 피처 중요도 확인

Step 3: 임계치 튜닝
  - ANOMALY_THRESHOLD 조정 (기본 0.5)
  - Precision-Recall 곡선으로 최적값 탐색

Step 4: (필요 시) Autoencoder 시도
  - IF 성능이 부족할 때만
  - 동일 피처셋으로 비교
```

---

## 6. 고장코드 분류 전략

이상 감지(anomaly detection)와 고장코드 분류(classification)는 별개:

1. **이상 감지**: "정상이 아니다" (IF/AE로 점수 산출)
2. **고장코드 분류**: "어떤 고장인가" (별도 로직)

### 고장코드 분류 방법 (Phase 3 실험)
- **규칙 기반 (먼저)**: EDA 패턴 활용
  - S1_CurrentFeedback 상승 + 고속 → SPINDLE_OVERHEAT_001
  - X1_CurrentFeedback 하락 → TOOL_WEAR_001
  - 위치 편차 급변 → CLAMP_PRESSURE_001
  - 주기적 (예방정비 주기) → COOLANT_LOW_001
- **모델 기반 (나중)**: 규칙 성능이 부족하면 분류 모델 추가
