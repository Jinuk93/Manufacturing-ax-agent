"""
F1 시뮬레이터 — CSV를 읽어 실시간처럼 DB에 INSERT

두 가지 모드:
1. batch: 전체 CSV를 한 번에 DB에 넣음 (초기 데이터 로드)
2. stream: 5초 간격으로 한 행씩 넣음 (실시간 시뮬레이션)

실제 현장에서는 이 시뮬레이터 자리에 SCADA API 연동이 들어감.
"""
import re
import time
import logging
from pathlib import Path

import pandas as pd

from app.services.db import get_connection, release_connection, insert_sensor_readings, insert_it_data

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

# DB 컬럼 매핑 (CSV CamelCase → DB snake_case)
def csv_to_db_column(col: str) -> str:
    """CSV 컬럼명을 DB 컬럼명으로 변환
    예: X1_ActualPosition → x1_actual_position
        M1_CURRENT_FEEDRATE → m1_current_feedrate
        Machining_Process → machining_process
    """
    # 이미 소문자+언더스코어인 경우 (timestamp, equipment_id 등)
    if col == col.lower():
        return col
    # CamelCase 부분을 snake_case로 변환
    # ActualPosition → Actual_Position → actual_position
    result = re.sub(r'([a-z])([A-Z])', r'\1_\2', col)
    # 연속 대문자 처리: DCBus → DC_Bus
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', result)
    return result.lower()


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


# IT 테이블별 허용 컬럼 (DB 스키마 기준, CSV에만 있는 컬럼 제거용)
IT_TABLE_COLUMNS = {
    "mes_work_orders": [
        "work_order_id", "equipment_id", "experiment_id", "product_type",
        "start_time", "end_time", "due_date", "priority", "status",
    ],
    "maintenance_events": [
        "event_id", "equipment_id", "event_type", "timestamp", "failure_code",
        "description", "duration_min", "technician_id", "parts_used", "work_order_id",
    ],
    "erp_inventory": [
        "snapshot_date", "part_id", "stock_quantity", "reorder_point",
        "lead_time_days", "unit_cost", "weekly_consumption", "reorder_triggered",
    ],
}


def load_it_csv(data_dir: str) -> dict:
    """IT 데이터 3종 CSV 로드 (DB에 없는 컬럼 자동 제거)"""
    it_path = Path(data_dir) / "it-data"
    result = {}

    # MES 작업지시
    mes_file = it_path / "mes_work_orders.csv"
    if mes_file.exists():
        df = pd.read_csv(mes_file)
        df = df[[c for c in IT_TABLE_COLUMNS["mes_work_orders"] if c in df.columns]]
        result["mes"] = df.to_dict(orient="records")
        logger.info(f"MES 로드: {len(result['mes'])}건 ({len(df.columns)}컬럼)")

    # 정비 이벤트
    maint_file = it_path / "maintenance_events.csv"
    if maint_file.exists():
        df = pd.read_csv(maint_file)
        df = df[[c for c in IT_TABLE_COLUMNS["maintenance_events"] if c in df.columns]]
        # NaN → None 변환 (nullable FK 처리)
        df = df.where(df.notna(), None)
        result["maintenance"] = df.to_dict(orient="records")
        logger.info(f"Maintenance 로드: {len(result['maintenance'])}건 ({len(df.columns)}컬럼)")

    # ERP 재고 (CSV의 part_name 등 DB에 없는 컬럼 자동 제거)
    erp_file = it_path / "erp_inventory_snapshots.csv"
    if erp_file.exists():
        df = pd.read_csv(erp_file)
        df = df[[c for c in IT_TABLE_COLUMNS["erp_inventory"] if c in df.columns]]
        result["erp"] = df.to_dict(orient="records")
        logger.info(f"ERP 로드: {len(result['erp'])}건 ({len(df.columns)}컬럼)")

    return result


def batch_load(data_dir: str):
    """배치 모드 — 전체 데이터를 한 번에 DB에 넣음

    사용 시점: 최초 DB 세팅, 또는 전체 리로드
    """
    conn = get_connection()
    try:
        # 1. 센서 데이터 (1,000행 단위 청크로 INSERT)
        logger.info("=== 센서 데이터 배치 로드 시작 ===")
        df = load_experiment_csv(data_dir)
        rows = prepare_sensor_rows(df)
        CHUNK_SIZE = 1000
        total_inserted = 0
        for i in range(0, len(rows), CHUNK_SIZE):
            chunk = rows[i:i + CHUNK_SIZE]
            count = insert_sensor_readings(conn, chunk)
            total_inserted += count
            logger.info(f"  청크 {i//CHUNK_SIZE + 1}: {count}행 INSERT ({total_inserted}/{len(rows)})")
        logger.info(f"센서 데이터 INSERT 완료: {total_inserted}행")

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
        release_connection(conn)


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

        prev_eq_id = None
        for i, row in enumerate(rows):
            insert_sensor_readings(conn, [row])

            eq_id = row.get("equipment_id", "?")
            ts = row.get("timestamp", "?")

            # 실험(설비) 경계 감지 — equipment_id가 바뀌면 로그 표시
            if eq_id != prev_eq_id:
                if prev_eq_id is not None:
                    logger.info(f"──── 설비 전환: {prev_eq_id} → {eq_id} ────")
                prev_eq_id = eq_id

            logger.info(f"[{i+1}/{len(rows)}] {eq_id} @ {ts}")

            if i < len(rows) - 1:
                time.sleep(poll_interval)

        logger.info("=== 스트림 시뮬레이션 완료 ===")

    except KeyboardInterrupt:
        logger.info(f"\n스트림 중단 (Ctrl+C). {i+1}행까지 완료.")
    finally:
        release_connection(conn)
