"""
F1 시뮬레이터 — CSV를 읽어 실시간처럼 DB에 INSERT

두 가지 모드:
1. batch: 전체 CSV를 한 번에 DB에 넣음 (초기 데이터 로드)
2. stream: 5초 간격으로 한 행씩 넣음 (실시간 시뮬레이션)

실제 현장에서는 이 시뮬레이터 자리에 SCADA API 연동이 들어감.
"""
import time
import logging
from pathlib import Path

import pandas as pd

from app.services.db import get_connection, insert_sensor_readings, insert_it_data

logger = logging.getLogger(__name__)

# CSV에서 제외할 컬럼 (분석에 쓸모없는 6개)
EXCLUDE_COLUMNS = [
    "Z1_CurrentFeedback",
    "Z1_DCBusVoltage",
    "Z1_OutputCurrent",
    "Z1_OutputVoltage",
    "S1_SystemInertia",
    "M1_sequence_number",
]

# DB 컬럼 매핑 (CSV 컬럼명 → DB 컬럼명, 소문자 변환)
def csv_to_db_column(col: str) -> str:
    """CSV 컬럼명을 DB 컬럼명으로 변환 (소문자화)"""
    return col.lower()


def load_experiment_csv(data_dir: str) -> pd.DataFrame:
    """18개 실험 CSV를 하나의 DataFrame으로 합침"""
    data_path = Path(data_dir) / "kaggle-cnc-mill"
    all_dfs = []

    for i in range(1, 19):
        csv_file = data_path / f"experiment_{i:02d}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            all_dfs.append(df)
            logger.info(f"로드 완료: {csv_file.name} ({len(df)}행)")
        else:
            logger.warning(f"파일 없음: {csv_file}")

    if not all_dfs:
        raise FileNotFoundError(f"실험 CSV가 없습니다: {data_path}")

    combined = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"전체 합산: {len(combined)}행, {len(combined.columns)}컬럼")
    return combined


def prepare_sensor_rows(df: pd.DataFrame) -> list[dict]:
    """DataFrame → DB INSERT용 dict 리스트로 변환 (제외 컬럼 제거)"""
    # 제외 컬럼 드롭
    df_clean = df.drop(columns=EXCLUDE_COLUMNS, errors="ignore")

    # 컬럼명 소문자 변환
    df_clean.columns = [csv_to_db_column(c) for c in df_clean.columns]

    return df_clean.to_dict(orient="records")


def load_it_csv(data_dir: str) -> dict:
    """IT 데이터 3종 CSV 로드"""
    it_path = Path(data_dir) / "it-data"
    result = {}

    # MES 작업지시
    mes_file = it_path / "mes_work_orders.csv"
    if mes_file.exists():
        result["mes"] = pd.read_csv(mes_file).to_dict(orient="records")
        logger.info(f"MES 로드: {len(result['mes'])}건")

    # 정비 이벤트
    maint_file = it_path / "maintenance_events.csv"
    if maint_file.exists():
        result["maintenance"] = pd.read_csv(maint_file).to_dict(orient="records")
        logger.info(f"Maintenance 로드: {len(result['maintenance'])}건")

    # ERP 재고
    erp_file = it_path / "erp_inventory_snapshots.csv"
    if erp_file.exists():
        result["erp"] = pd.read_csv(erp_file).to_dict(orient="records")
        logger.info(f"ERP 로드: {len(result['erp'])}건")

    return result


def batch_load(data_dir: str):
    """배치 모드 — 전체 데이터를 한 번에 DB에 넣음

    사용 시점: 최초 DB 세팅, 또는 전체 리로드
    """
    conn = get_connection()
    try:
        # 1. 센서 데이터
        logger.info("=== 센서 데이터 배치 로드 시작 ===")
        df = load_experiment_csv(data_dir)
        rows = prepare_sensor_rows(df)
        count = insert_sensor_readings(conn, rows)
        logger.info(f"센서 데이터 INSERT 완료: {count}행")

        # 2. IT 데이터
        logger.info("=== IT 데이터 배치 로드 시작 ===")
        it_data = load_it_csv(data_dir)

        if "mes" in it_data:
            cnt = insert_it_data(conn, "mes_work_orders", it_data["mes"])
            logger.info(f"MES INSERT 완료: {cnt}건")

        if "maintenance" in it_data:
            cnt = insert_it_data(conn, "maintenance_events", it_data["maintenance"])
            logger.info(f"Maintenance INSERT 완료: {cnt}건")

        if "erp" in it_data:
            cnt = insert_it_data(conn, "erp_inventory", it_data["erp"])
            logger.info(f"ERP INSERT 완료: {cnt}건")

        logger.info("=== 배치 로드 전체 완료 ===")

    finally:
        conn.close()


def stream_load(data_dir: str, poll_interval: int = 5):
    """스트림 모드 — 5초 간격으로 한 행씩 DB에 넣음

    실제 현장의 SCADA 5초 폴링을 시뮬레이션.
    Ctrl+C로 중단 가능.
    """
    conn = get_connection()
    try:
        df = load_experiment_csv(data_dir)
        rows = prepare_sensor_rows(df)

        logger.info(f"=== 스트림 시뮬레이션 시작 (간격: {poll_interval}초, 총 {len(rows)}행) ===")

        for i, row in enumerate(rows):
            insert_sensor_readings(conn, [row])

            eq_id = row.get("equipment_id", "?")
            ts = row.get("timestamp", "?")
            logger.info(f"[{i+1}/{len(rows)}] {eq_id} @ {ts}")

            if i < len(rows) - 1:
                time.sleep(poll_interval)

        logger.info("=== 스트림 시뮬레이션 완료 ===")

    except KeyboardInterrupt:
        logger.info(f"\n스트림 중단 (Ctrl+C). {i+1}행까지 완료.")
    finally:
        conn.close()
