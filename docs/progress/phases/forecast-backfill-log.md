# F2 Forecasting Backfill 작업 기록

**작업일:** 2026-03-17
**작업자:** 리뷰어 Claude (forecast backfill + 프론트 jitter 제거)

---

## 배경

Phase 3 후반에서 F2 Forecasting(1D-CNN)이 구현됐지만, 기존 anomaly_scores 테이블의 29,036행에 `forecast_score`와 `if_score`가 NULL인 상태였다. main_loop은 forecaster와 연동되어 있지만, batch 로드 시점에는 forecaster 없이 IF만 실행된 데이터였다.

## 수행 작업

### 1. Backfill 스크립트 작성 + 실행

**파일:** `backend/backfill_forecast.py`

- 설비별로 sensor_readings를 읽어 forecaster.predict() 호출
- 기존 anomaly_scores의 if_score를 보존하면서 forecast_score를 채움
- 가중 합산: `combined = 0.6 * if_score + 0.4 * forecast_score` (ADR-007)
- INPUT_STEPS(300) + OUTPUT_STEPS(300) = 600행 윈도우를 보내야 실제 오차 계산 가능

**핵심 이슈 해결:**
- 1차 시도: predict()에 INPUT_STEPS만 보내서 mae=0 → forecast_score 전부 0
- 2차 시도: INPUT_STEPS + OUTPUT_STEPS 윈도우를 보내서 예측 vs 실제 비교 성공

**결과:**

| 설비 | 총 행 | forecast 채움 | avg_if | avg_forecast | avg_combined |
|------|-------|--------------|--------|-------------|-------------|
| CNC-001 | 7,785 | 7,185 (92%) | 0.115 | 0.624 | 0.306 |
| CNC-002 | 9,052 | 8,452 (93%) | 0.114 | 0.695 | 0.334 |
| CNC-003 | 12,202 | 11,602 (95%) | 0.113 | 0.537 | 0.276 |

- forecast_score 범위: 0.260 ~ 1.000 (포화 없이 분포 정상)
- CNC-002가 가장 높음 (worn 실험 + 고속 가공 포함)

### 2. 프론트엔드 forecast null fallback 수정

**파일:** `frontend/src/components/dashboard/MonitoringCenter.tsx`

**수정 전:**
```ts
// forecast_score가 null이면 가짜 jitter로 mock 데이터 생성
const jitter = [0.08, -0.03, 0.05][idx] ?? 0
return Math.max(0, Math.min(1, ifScore + jitter))
```

**수정 후:**
```ts
// null이면 null 반환 → 차트에 "—" 표시, 라인 안 그림
if (anomalyData?.forecast_score != null) return anomalyData.forecast_score
return null
```

**변경 사항:**
- `getForecastScore()`: jitter 제거, null 반환
- 테이블: null이면 "—" 표시
- 융합 점수: null이면 if_score만 사용
- 차트: forecast가 undefined면 Recharts가 자동으로 라인 생략

## 검증

- DB: 29,036행 중 27,239행(93.8%)에 forecast_score 채워짐
- 나머지 6.2%: 실험 시작/끝 경계에서 600행 윈도우를 만들 수 없는 구간
- 프론트엔드: HMR 즉시 반영, 가짜 데이터 제거 확인
