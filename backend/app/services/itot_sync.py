"""
F3 IT/OT 동기화 — 이상 감지 시 비즈니스 컨텍스트 조회

이상 감지된 설비의:
1. 현재/최근 작업지시 (MES)
2. 최근 정비 이력 (CMMS)
3. 관련 부품 재고 (ERP)
를 한 번에 조회하여 통합 컨텍스트를 생성합니다.

이 컨텍스트가 있어야 F5 LLM이 "즉시 정지 vs 감속 운전"을 판단할 수 있습니다.
"""
import logging
from datetime import datetime
from typing import Optional

from app.services.db import get_connection
from app.models.schemas import (
    ITOTSyncResponse,
    WorkOrderInfo,
    MaintenanceRecord,
    InventoryItem,
)

logger = logging.getLogger(__name__)


def sync_itot_context(
    equipment_id: str,
    timestamp: datetime,
    predicted_failure_code: Optional[str] = None,
) -> ITOTSyncResponse:
    """이상 감지 시 IT 데이터(MES+CMMS+ERP) 조회

    pipeline-design.md 기준 3개 SQL:
    1. MES: 해당 시각에 진행 중이던 작업 (start_time ≤ t ≤ end_time)
    2. Maintenance: 해당 설비의 최근 정비 이력 (최근 5건)
    3. ERP: 관련 부품 재고 (최신 스냅샷)
    """
    conn = get_connection()
    try:
        # ── 1. MES 작업지시 조회 ──
        work_order = _query_work_order(conn, equipment_id, timestamp)
        work_order_note = None
        if work_order is None:
            work_order_note = "해당 시각에 진행 중인 작업이 없습니다."

        # ── 2. 정비 이력 조회 (최근 5건) ──
        maintenance = _query_maintenance(conn, equipment_id, limit=5)

        # ── 3. 부품 재고 조회 ──
        inventory = _query_inventory(conn)

        logger.info(
            f"F3 동기화 완료: {equipment_id} @ {timestamp} | "
            f"작업={'있음' if work_order else '없음'}, "
            f"정비이력={len(maintenance)}건, "
            f"재고={len(inventory)}종"
        )

        return ITOTSyncResponse(
            equipment_id=equipment_id,
            timestamp=timestamp,
            latest_work_order=work_order,
            work_order_note=work_order_note,
            recent_maintenance=maintenance,
            inventory=inventory,
        )

    finally:
        conn.close()


def _query_work_order(
    conn, equipment_id: str, timestamp: datetime
) -> Optional[WorkOrderInfo]:
    """해당 시각에 진행 중이던(또는 가장 최근) 작업지시 조회"""
    sql = """
        SELECT work_order_id, product_type, due_date, priority, status
        FROM mes_work_orders
        WHERE equipment_id = %s
          AND start_time <= %s
        ORDER BY start_time DESC
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (equipment_id, timestamp))
        row = cur.fetchone()

    if row is None:
        return None

    return WorkOrderInfo(
        work_order_id=row[0],
        product_type=row[1],
        due_date=row[2],
        priority=row[3],
        status=row[4],
    )


def _query_maintenance(
    conn, equipment_id: str, limit: int = 5
) -> list[MaintenanceRecord]:
    """해당 설비의 최근 정비 이력"""
    sql = """
        SELECT event_id, failure_code, event_type, duration_min, parts_used
        FROM maintenance_events
        WHERE equipment_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (equipment_id, limit))
        rows = cur.fetchall()

    return [
        MaintenanceRecord(
            event_id=r[0],
            failure_code=r[1],
            event_type=r[2],
            duration_min=r[3],
            parts_used=r[4],
        )
        for r in rows
    ]


def _query_inventory(conn) -> list[InventoryItem]:
    """전체 부품의 최신 재고 (가장 최근 snapshot_date 기준)"""
    sql = """
        SELECT e.part_id, p.part_name, e.stock_quantity, e.reorder_point, e.lead_time_days
        FROM erp_inventory e
        JOIN parts p ON e.part_id = p.part_id
        WHERE e.snapshot_date = (SELECT MAX(snapshot_date) FROM erp_inventory)
        ORDER BY e.part_id
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    return [
        InventoryItem(
            part_id=r[0],
            part_name=r[1],
            stock_quantity=r[2],
            reorder_point=r[3],
            lead_time_days=r[4],
        )
        for r in rows
    ]
