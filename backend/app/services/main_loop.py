"""
메인 폴링 루프 — F1→F2 매 5초 + 이상 시 F3→F4→F5 트리거

pipeline-design.md 기준:
- 모드 1 (상시): F1→F2→F6 매 POLL_INTERVAL_SEC(5초) 반복
- 모드 2 (이벤트): is_anomaly=true 시 F3→F4→F5→F6 비동기 실행

사용법:
  python -m app.services.main_loop
  또는 FastAPI startup에서 asyncio.create_task(run_main_loop())
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.config import settings
from app.services.db import get_connection, release_connection, insert_sensor_readings
from app.services.anomaly_detector import AnomalyDetector
from app.services.forecaster import SensorForecaster
from app.services.itot_sync import sync_itot_context
from app.services.graphrag import search_graphrag
from app.services.llm_agent import generate_action

logger = logging.getLogger(__name__)

# F2 모델 (전역 로드, 한 번만)
_detector: AnomalyDetector | None = None
_forecaster: SensorForecaster | None = None


def _get_detector() -> AnomalyDetector:
    """F2 IF 모델 싱글턴 로드"""
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
        model_path = Path(__file__).parent.parent.parent / "models" / "f2_detector.pkl"
        _detector.load(str(model_path))
    return _detector


def _get_forecaster() -> SensorForecaster | None:
    """F2 Forecasting 모델 싱글턴 로드 (없으면 None)"""
    global _forecaster
    if _forecaster is None:
        model_path = Path(__file__).parent.parent.parent / "models" / "f2_forecaster.pkl"
        if model_path.exists():
            _forecaster = SensorForecaster()
            _forecaster.load(str(model_path))
            logger.info("F2 Forecaster 모델 로드 완료")
        else:
            logger.warning("F2 Forecaster 모델 없음 — IF만 사용")
    return _forecaster


async def process_alarm(
    equipment_id: str,
    anomaly_result: dict,
):
    """이상 감지 시 F3→F4→F5 비동기 실행 (대시보드 블로킹 안 함)"""
    try:
        logger.info(f"[ALARM] {equipment_id}: F3→F4→F5 시작")

        from app.models.schemas import AnomalyResult
        f2 = AnomalyResult(
            timestamp=anomaly_result["timestamp"],
            equipment_id=equipment_id,
            anomaly_score=anomaly_result["anomaly_score"],
            is_anomaly=True,
            predicted_failure_code=anomaly_result.get("predicted_failure_code"),
            confidence=anomaly_result["anomaly_score"],
            model_version="IF-v1",
        )

        # F3: IT/OT 동기화
        f3 = sync_itot_context(
            equipment_id=equipment_id,
            timestamp=f2.timestamp,
            predicted_failure_code=f2.predicted_failure_code,
        )
        logger.info(f"  F3: 작업={'있음' if f3.latest_work_order else '없음'}, 재고={len(f3.inventory)}종")

        # F4: GraphRAG
        f4 = search_graphrag(
            failure_code=f2.predicted_failure_code or "UNKNOWN",
            equipment_id=equipment_id,
        )
        logger.info(f"  F4: 부품={len(f4.related_parts)}, 문서={len(f4.related_documents)}")

        # F5: LLM 판단 (async)
        f5 = await generate_action(f2_result=f2, f3_context=f3, f4_rag_result=f4)
        logger.info(f"  F5: {f5.recommendation} (confidence={f5.confidence})")
        logger.info(f"  조치: {f5.action_steps[:2]}...")

        # F5 결과 DB 저장
        import json as _json
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO llm_action_reports
                    (equipment_id, timestamp, recommendation, confidence, reasoning,
                     action_steps, parts_needed, predicted_failure_code, estimated_downtime_min)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    equipment_id, f2.timestamp, f5.recommendation, f5.confidence,
                    f5.reasoning, _json.dumps(f5.action_steps, ensure_ascii=False),
                    _json.dumps([p.dict() for p in f5.parts_needed], ensure_ascii=False) if f5.parts_needed else "[]",
                    f5.predicted_failure_code, f5.estimated_downtime_min,
                ))
            conn.commit()
            logger.info(f"  F5 결과 DB 저장 완료")
        finally:
            release_connection(conn)

    except Exception as e:
        logger.error(f"[ALARM] {equipment_id} 처리 실패: {e}", exc_info=True)


async def run_main_loop(data_dir: str = None):
    """메인 폴링 루프

    CSV 데이터를 5초 간격으로 DB에 넣고(F1),
    이상 감지 시(F2) F3→F4→F5를 비동기 트리거합니다.
    """
    if data_dir is None:
        data_dir = str(Path(__file__).parent.parent.parent.parent / "data" / "processed")

    from app.services.simulator import load_experiment_csv, prepare_sensor_rows
    detector = _get_detector()

    # 데이터 로드
    df = load_experiment_csv(data_dir)
    rows = prepare_sensor_rows(df)

    logger.info(f"=== 메인 폴링 루프 시작 (간격: {settings.POLL_INTERVAL_SEC}초, 총 {len(rows)}행) ===")

    equipment_ids = ["CNC-001", "CNC-002", "CNC-003"]

    for i, row in enumerate(rows):
        eq_id = row.get("equipment_id", "?")
        ts = row.get("timestamp", datetime.now())

        # F1: 센서 데이터 INSERT
        conn = get_connection()
        try:
            insert_sensor_readings(conn, [row])
        finally:
            release_connection(conn)

        # F2: 이상탐지 (최근 6행 윈도우)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM sensor_readings
                    WHERE equipment_id = %s
                    ORDER BY timestamp DESC LIMIT 6
                """, (eq_id,))
                columns = [desc[0] for desc in cur.description]
                window_rows = cur.fetchall()
        finally:
            release_connection(conn)

        if len(window_rows) >= 2:
            window_df = pd.DataFrame(window_rows, columns=columns)
            result = detector.predict(window_df)
            last = result.iloc[-1]
            if_score = float(last["anomaly_score"])
            fc = last["predicted_failure_code"]

            # F2 Forecasting (ADR-007)
            forecast_score_val = None
            forecaster = _get_forecaster()
            if forecaster is not None and len(window_df) >= 2:
                try:
                    # 최근 300행 윈도우가 필요하지만, 현재 6행만 있으면 패딩 처리됨
                    fc_result = forecaster.predict(window_df)
                    forecast_score_val = fc_result["forecast_score"]
                except Exception as e:
                    logger.debug(f"Forecaster 예측 실패 (IF만 사용): {e}")

            # 합산 (ADR-007: weighted fusion)
            w = settings.FORECAST_WEIGHT
            if forecast_score_val is not None:
                score = (1 - w) * if_score + w * forecast_score_val
            else:
                score = if_score

            is_anomaly = score > settings.ANOMALY_THRESHOLD

            # anomaly_scores INSERT (forecast_score 포함)
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO anomaly_scores
                        (timestamp, equipment_id, anomaly_score, is_anomaly, model_version,
                         predicted_failure_code, confidence, if_score, forecast_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (timestamp, equipment_id) DO UPDATE
                        SET anomaly_score = EXCLUDED.anomaly_score,
                            if_score = EXCLUDED.if_score,
                            forecast_score = EXCLUDED.forecast_score
                    """, (ts, eq_id, score, is_anomaly, "IF+CNN-v1", fc, score, if_score, forecast_score_val))
                conn.commit()
            finally:
                release_connection(conn)

            # 이상 감지 시 F3→F4→F5 비동기 트리거
            if is_anomaly:
                logger.info(f"[{i+1}] {eq_id} @ {ts} — 이상! score={score:.3f}, fc={fc}")
                asyncio.create_task(process_alarm(eq_id, {
                    "timestamp": ts,
                    "anomaly_score": score,
                    "predicted_failure_code": fc,
                }))
            else:
                if i % 100 == 0:  # 100행마다 로그
                    logger.info(f"[{i+1}/{len(rows)}] {eq_id} — 정상 (score={score:.3f})")
        else:
            if i % 100 == 0:
                logger.info(f"[{i+1}/{len(rows)}] {eq_id} — 데이터 부족 (윈도우 {len(window_rows)}행)")

        # 5초 대기 (스트림 모드)
        await asyncio.sleep(settings.POLL_INTERVAL_SEC)

    logger.info("=== 메인 폴링 루프 종료 ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    asyncio.run(run_main_loop())
