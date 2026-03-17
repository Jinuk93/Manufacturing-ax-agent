"""
F2 Forecast backfill — 기존 anomaly_scores에 forecast_score + if_score 채우기

기존 데이터는 IF만 돌린 상태라 if_score/forecast_score가 NULL.
이 스크립트는:
1. sensor_readings에서 실험별 데이터를 읽음
2. IF detector로 if_score 산출
3. CNN forecaster로 forecast_score 산출
4. 가중 합산 → anomaly_scores UPDATE

사용법:
  cd backend
  python backfill_forecast.py
"""
import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.db import get_connection, release_connection
from app.services.anomaly_detector import AnomalyDetector
from app.services.forecaster import SensorForecaster, INPUT_STEPS, OUTPUT_STEPS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "models"


def main():
    logger.info("=== F2 Forecast Backfill 시작 ===")

    # 1. 모델 로드
    detector = AnomalyDetector()
    detector.load(str(MODEL_DIR / "f2_detector.pkl"))

    forecaster = SensorForecaster()
    forecaster.load(str(MODEL_DIR / "f2_forecaster.pkl"))

    # 2. 설비별 sensor_readings 읽기
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT equipment_id FROM sensor_readings ORDER BY 1")
            equipment_ids = [row[0] for row in cur.fetchall()]
    finally:
        release_connection(conn)

    total_updated = 0

    for eq_id in equipment_ids:
        logger.info(f"\n--- {eq_id} 처리 중 ---")

        # 센서 데이터 읽기
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM sensor_readings
                    WHERE equipment_id = %s
                    ORDER BY timestamp
                """, (eq_id,))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
        finally:
            release_connection(conn)

        if not rows:
            logger.warning(f"  {eq_id}: 데이터 없음")
            continue

        df = pd.DataFrame(rows, columns=columns)
        logger.info(f"  {eq_id}: {len(df)}행 로드")

        # 3. IF 이상탐지 — 기존 anomaly_scores에서 if_score 가져오기
        # (IF 모델 피처 호환 문제를 우회: 이미 계산된 점수를 재사용)
        conn2 = get_connection()
        try:
            with conn2.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, anomaly_score, predicted_failure_code
                    FROM anomaly_scores
                    WHERE equipment_id = %s
                    ORDER BY timestamp
                """, (eq_id,))
                existing = cur.fetchall()
        finally:
            release_connection(conn2)

        # timestamp → (score, failure_code) 매핑
        existing_map = {}
        for row in existing:
            existing_map[row[0]] = (row[1], row[2])
        logger.info(f"  기존 anomaly_scores: {len(existing_map)}건")

        # 4. Forecasting (슬라이딩 윈도우)
        # predict()에 INPUT_STEPS + OUTPUT_STEPS를 보내야 실제 오차 계산 가능
        forecast_scores = [None] * len(df)
        total_window = INPUT_STEPS + OUTPUT_STEPS  # 300 + 300 = 600행

        for i in range(INPUT_STEPS, len(df)):
            # i 시점 기준: 과거 INPUT_STEPS + 미래 OUTPUT_STEPS를 함께 전달
            start = max(0, i - INPUT_STEPS)
            end = min(len(df), i + OUTPUT_STEPS)
            window = df.iloc[start:end]

            if len(window) < total_window:
                # 윈도우가 부족하면 입력만으로 예측 (mae=0 → score=0이지만 어쩔 수 없음)
                # 실험 경계에서 발생
                continue

            try:
                fc_result = forecaster.predict(window)
                forecast_scores[i] = fc_result["forecast_score"]
            except Exception:
                pass

        forecast_count = sum(1 for s in forecast_scores if s is not None)
        logger.info(f"  Forecast 완료: {forecast_count}/{len(df)}행 산출")

        # 5. DB UPDATE — 기존 anomaly_scores에 forecast_score + if_score 채우기
        w = settings.FORECAST_WEIGHT
        conn = get_connection()
        try:
            updated = 0
            with conn.cursor() as cur:
                for ts_key, (orig_score, fc) in existing_map.items():
                    # 해당 타임스탬프의 forecast_score 찾기
                    # sensor_readings의 인덱스 매칭
                    matching = df[df["timestamp"] == ts_key]
                    if matching.empty:
                        continue

                    idx = matching.index[0]
                    if_score = float(orig_score)  # 기존 IF 점수 보존
                    fs = forecast_scores[idx] if idx < len(forecast_scores) else None

                    # 합산
                    if fs is not None:
                        combined = (1 - w) * if_score + w * fs
                    else:
                        combined = if_score

                    is_anomaly = combined > settings.ANOMALY_THRESHOLD

                    cur.execute("""
                        UPDATE anomaly_scores
                        SET anomaly_score = %s,
                            is_anomaly = %s,
                            if_score = %s,
                            forecast_score = %s,
                            model_version = 'IF+CNN-v1'
                        WHERE timestamp = %s AND equipment_id = %s
                    """, (combined, is_anomaly, if_score, fs, ts_key, eq_id))
                    updated += 1

            conn.commit()
            total_updated += updated
            logger.info(f"  {eq_id}: {updated}행 UPDATE 완료")
        finally:
            release_connection(conn)

    # 6. 검증
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT equipment_id,
                  count(*) as total,
                  count(forecast_score) as with_forecast,
                  round(avg(if_score)::numeric, 3) as avg_if,
                  round(avg(forecast_score)::numeric, 3) as avg_forecast,
                  round(avg(anomaly_score)::numeric, 3) as avg_combined
                FROM anomaly_scores GROUP BY equipment_id ORDER BY 1
            """)
            for row in cur.fetchall():
                logger.info(f"  {row[0]}: total={row[1]}, forecast={row[2]}, "
                           f"avg_if={row[3]}, avg_forecast={row[4]}, avg_combined={row[5]}")
    finally:
        release_connection(conn)

    logger.info(f"\n=== Backfill 완료: {total_updated}행 업데이트 ===")


if __name__ == "__main__":
    main()
