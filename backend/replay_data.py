"""
데이터 리플레이 — 기존 DB 데이터를 현재 시각으로 재생
5초마다 센서 + 이상탐지 데이터를 현재 timestamp로 갱신하여
대시보드에서 실시간 데이터 흐름처럼 보이게 합니다.

사용법: cd backend && python replay_data.py
"""
import time
import logging
from datetime import datetime, timezone

from app.services.db import get_connection, release_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

EQUIPMENT_IDS = ["CNC-001", "CNC-002", "CNC-003"]
POLL_INTERVAL = 5  # 초


def get_sensor_rows(conn, equipment_id: str, limit: int = 300):
    """기존 센서 데이터 조회"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM sensor_readings
            WHERE equipment_id = %s
            ORDER BY timestamp ASC LIMIT %s
        """, (equipment_id, limit))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return columns, rows


def replay_loop():
    """메인 리플레이 루프"""
    # 각 설비별 기존 데이터 로드
    conn = get_connection()
    all_data = {}
    for eq_id in EQUIPMENT_IDS:
        columns, rows = get_sensor_rows(conn, eq_id)
        all_data[eq_id] = {"columns": columns, "rows": rows, "idx": 0}
        logger.info(f"{eq_id}: {len(rows)}행 로드됨")
    release_connection(conn)

    if all(len(d["rows"]) == 0 for d in all_data.values()):
        logger.error("센서 데이터가 없습니다. load_data.py를 먼저 실행하세요.")
        return

    logger.info(f"=== 리플레이 시작 (간격: {POLL_INTERVAL}초) ===")

    while True:
        now = datetime.now(timezone.utc)
        conn = get_connection()

        for eq_id, data in all_data.items():
            if len(data["rows"]) == 0:
                continue

            # 순환 인덱스
            idx = data["idx"] % len(data["rows"])
            row = data["rows"][idx]
            columns = data["columns"]
            row_dict = dict(zip(columns, row))

            # 현재 시각으로 덮어쓰기
            row_dict["timestamp"] = now

            # sensor_readings에 INSERT (최신 데이터로)
            cols_to_insert = [c for c in columns if c not in ("id",)]
            vals = [row_dict.get(c) for c in cols_to_insert]

            try:
                with conn.cursor() as cur:
                    placeholders = ", ".join(["%s"] * len(cols_to_insert))
                    col_names = ", ".join(cols_to_insert)
                    cur.execute(
                        f"INSERT INTO sensor_readings ({col_names}) VALUES ({placeholders})",
                        vals
                    )

                    # anomaly_scores도 현재 시각으로 갱신
                    # 기존 이상 점수 데이터에서 같은 인덱스의 점수 사용
                    cur.execute("""
                        SELECT anomaly_score, is_anomaly, predicted_failure_code, confidence
                        FROM anomaly_scores
                        WHERE equipment_id = %s
                        ORDER BY timestamp DESC LIMIT 1
                    """, (eq_id,))
                    score_row = cur.fetchone()

                    if score_row:
                        # 약간의 변동을 줘서 차트가 움직이게
                        import random
                        base_score = float(score_row[0])
                        jitter = random.uniform(-0.02, 0.02)
                        new_score = max(0, min(1, base_score + jitter))
                        is_anomaly = new_score >= 0.5

                        cur.execute("""
                            INSERT INTO anomaly_scores
                            (timestamp, equipment_id, anomaly_score, is_anomaly, model_version, predicted_failure_code, confidence)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (timestamp, equipment_id) DO UPDATE SET anomaly_score = EXCLUDED.anomaly_score
                        """, (now, eq_id, new_score, is_anomaly, "IF-v1", score_row[2], new_score))

                conn.commit()
            except Exception as e:
                logger.warning(f"{eq_id} 리플레이 실패: {e}")
                conn.rollback()

            data["idx"] = idx + 1

        release_connection(conn)

        # 3개 설비 중 첫번째만 로그
        d0 = all_data[EQUIPMENT_IDS[0]]
        logger.info(f"[{d0['idx']}] 리플레이 완료 — {now.strftime('%H:%M:%S')}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    replay_loop()
