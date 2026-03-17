"""
DB 연결 관리 — PostgreSQL (psycopg2 동기 + 커넥션 풀)
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values

from app.config import settings

# 커넥션 풀 (최소 2, 최대 10 연결)
_pool = None


def _get_pool():
    """커넥션 풀 싱글턴"""
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=2, maxconn=10,
            dsn=settings.DATABASE_URL_SYNC,
        )
    return _pool


def get_connection():
    """커넥션 풀에서 연결 반환 (사용 후 반드시 release_connection() 호출)"""
    return _get_pool().getconn()


def release_connection(conn):
    """커넥션을 풀에 반환 (close 대신 사용 권장)"""
    _get_pool().putconn(conn)


def insert_sensor_readings(conn, rows: list[dict]):
    """센서 데이터 배치 INSERT
    rows: [{timestamp, equipment_id, x1_actual_position, ...}, ...]
    """
    if not rows:
        return 0

    # 컬럼 순서 (init.sql과 동일)
    columns = [
        "timestamp", "equipment_id",
        # X축 (11)
        "x1_actual_position", "x1_actual_velocity", "x1_actual_acceleration",
        "x1_command_position", "x1_command_velocity", "x1_command_acceleration",
        "x1_current_feedback", "x1_dc_bus_voltage", "x1_output_current",
        "x1_output_voltage", "x1_output_power",
        # Y축 (11)
        "y1_actual_position", "y1_actual_velocity", "y1_actual_acceleration",
        "y1_command_position", "y1_command_velocity", "y1_command_acceleration",
        "y1_current_feedback", "y1_dc_bus_voltage", "y1_output_current",
        "y1_output_voltage", "y1_output_power",
        # Z축 (6)
        "z1_actual_position", "z1_actual_velocity", "z1_actual_acceleration",
        "z1_command_position", "z1_command_velocity", "z1_command_acceleration",
        # S축 (11)
        "s1_actual_position", "s1_actual_velocity", "s1_actual_acceleration",
        "s1_command_position", "s1_command_velocity", "s1_command_acceleration",
        "s1_current_feedback", "s1_dc_bus_voltage", "s1_output_current",
        "s1_output_voltage", "s1_output_power",
        # M1 + 가공 (3)
        "m1_current_program_number", "m1_current_feedrate", "machining_process",
    ]

    values = []
    for row in rows:
        values.append(tuple(row.get(col) for col in columns))

    sql = f"""
        INSERT INTO sensor_readings ({', '.join(columns)})
        VALUES %s
        ON CONFLICT (timestamp, equipment_id) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()
    return len(values)


ALLOWED_TABLES = {"mes_work_orders", "maintenance_events", "erp_inventory"}


def insert_it_data(conn, table: str, rows: list[dict]):
    """IT 데이터(MES/Maintenance/ERP) INSERT"""
    if not rows:
        return 0
    if table not in ALLOWED_TABLES:
        raise ValueError(f"허용되지 않은 테이블: {table}")

    columns = list(rows[0].keys())
    values = [tuple(row[col] for col in columns) for row in rows]

    # ON CONFLICT DO NOTHING으로 중복 방지
    sql = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()
    return len(values)
