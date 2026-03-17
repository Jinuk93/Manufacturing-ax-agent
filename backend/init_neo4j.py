"""
Neo4j 온톨로지 완성 — PG 데이터를 읽어 Neo4j에 노드+관계 생성

Cypher 스크립트(db/init_neo4j.cypher)로 기본 노드(Equipment, FailureCode, Part, Document)를 생성한 뒤,
이 스크립트로 Sensor(39), WorkOrder(18), MaintenanceAction(39) + 관계(R1~R10)를 완성합니다.

사용법:
  1. docker exec -i ax-neo4j cypher-shell ... < db/init_neo4j.cypher  (기본 노드)
  2. python init_neo4j.py  (나머지 노드 + 관계)
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from neo4j import GraphDatabase
from app.services.db import get_connection, release_connection
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


def get_neo4j_driver():
    return GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))


def create_sensor_nodes(driver):
    """Sensor 노드 39개 생성 + R1 HAS_SENSOR 관계"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT sensor_id, sensor_type, axis, unit FROM sensors ORDER BY sensor_id")
            sensors = cur.fetchall()
    finally:
        release_connection(conn)

    # 센서 → 설비 매핑 (모든 센서는 3대 모두에 달려있음)
    equipment_ids = ["CNC-001", "CNC-002", "CNC-003"]

    with driver.session() as session:
        for sensor_id, sensor_type, axis, unit in sensors:
            session.run(
                "MERGE (s:Sensor {sensor_id: $sid}) "
                "SET s.sensor_type = $stype, s.axis = $axis, s.unit = $unit",
                sid=sensor_id, stype=sensor_type, axis=axis, unit=unit
            )
        logger.info(f"Sensor 노드 {len(sensors)}개 생성")

        # R1 HAS_SENSOR (Equipment → Sensor)
        count = 0
        for eq_id in equipment_ids:
            for sensor_id, _, _, _ in sensors:
                session.run(
                    "MATCH (e:Equipment {equipment_id: $eid}), (s:Sensor {sensor_id: $sid}) "
                    "MERGE (e)-[:HAS_SENSOR]->(s)",
                    eid=eq_id, sid=sensor_id
                )
                count += 1
        logger.info(f"R1 HAS_SENSOR 관계 {count}개 생성")


def create_experiences_relations(driver):
    """R3 EXPERIENCES (Equipment → FailureCode) — PG 데이터 기준 자동 생성

    수동 매핑 대신 maintenance_events에서 설비별 고장코드를 집계하여 생성.
    first_occurrence = 해당 설비에서 해당 고장이 처음 발생한 날짜.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT equipment_id, failure_code, MIN(timestamp)::date AS first_date
                FROM maintenance_events
                WHERE failure_code IS NOT NULL AND failure_code != ''
                GROUP BY equipment_id, failure_code
                ORDER BY equipment_id, failure_code
            """)
            rows = cur.fetchall()
    finally:
        release_connection(conn)

    with driver.session() as session:
        # 기존 EXPERIENCES 관계 삭제 후 재생성 (수동 매핑 오류 정리)
        session.run("MATCH ()-[r:EXPERIENCES]->() DELETE r")

        for eq_id, failure_code, first_date in rows:
            session.run(
                "MATCH (e:Equipment {equipment_id: $eid}), (f:FailureCode {failure_code: $fc}) "
                "MERGE (e)-[:EXPERIENCES {first_occurrence: date($fd)}]->(f)",
                eid=eq_id, fc=failure_code, fd=str(first_date)
            )
        logger.info(f"R3 EXPERIENCES 관계 {len(rows)}개 생성 (PG 데이터 기준)")


def create_workorder_nodes(driver):
    """WorkOrder 노드 18개 생성 + R6 EXECUTES 관계"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT work_order_id, equipment_id, product_type, priority, status "
                "FROM mes_work_orders ORDER BY work_order_id"
            )
            work_orders = cur.fetchall()
    finally:
        release_connection(conn)

    with driver.session() as session:
        for wo_id, eq_id, product_type, priority, status in work_orders:
            # WorkOrder 노드
            session.run(
                "MERGE (w:WorkOrder {work_order_id: $wid}) "
                "SET w.product_type = $pt, w.priority = $pri, w.status = $st",
                wid=wo_id, pt=product_type, pri=priority, st=status
            )
            # R6 EXECUTES (Equipment → WorkOrder)
            session.run(
                "MATCH (e:Equipment {equipment_id: $eid}), (w:WorkOrder {work_order_id: $wid}) "
                "MERGE (e)-[:EXECUTES]->(w)",
                eid=eq_id, wid=wo_id
            )
        logger.info(f"WorkOrder 노드 {len(work_orders)}개 + R6 EXECUTES 관계 생성")


def create_maintenance_nodes(driver):
    """MaintenanceAction 노드 39개 + R7/R8/R9/R10 관계"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT event_id, equipment_id, event_type, failure_code, "
                "duration_min, technician_id, parts_used, work_order_id "
                "FROM maintenance_events ORDER BY event_id"
            )
            events = cur.fetchall()
    finally:
        release_connection(conn)

    with driver.session() as session:
        r7_count = 0
        r8_count = 0
        r9_count = 0

        for event_id, eq_id, event_type, failure_code, duration_min, tech_id, parts_used, wo_id in events:
            # MaintenanceAction 노드
            session.run(
                "MERGE (m:MaintenanceAction {event_id: $eid}) "
                "SET m.event_type = $et, m.duration_min = $dur, m.technician_id = $tid",
                eid=event_id, et=event_type, dur=duration_min, tid=tech_id
            )

            # R7 TRIGGERS (WorkOrder → MaintenanceAction)
            # 예외: 예방정비 27건은 work_order_id가 없음
            if wo_id and str(wo_id).strip():
                session.run(
                    "MATCH (w:WorkOrder {work_order_id: $wid}), (m:MaintenanceAction {event_id: $eid}) "
                    "MERGE (w)-[:TRIGGERS]->(m)",
                    wid=wo_id, eid=event_id
                )
                r7_count += 1

            # R8 RESOLVES (MaintenanceAction → FailureCode)
            # 예외: 에어필터 교체 9건은 failure_code가 없음
            if failure_code and str(failure_code).strip():
                session.run(
                    "MATCH (m:MaintenanceAction {event_id: $eid}), (f:FailureCode {failure_code: $fc}) "
                    "MERGE (m)-[:RESOLVES {resolution_time_min: $dur}]->(f)",
                    eid=event_id, fc=failure_code, dur=duration_min
                )
                r8_count += 1

            # R9 CONSUMES (MaintenanceAction → Part)
            if parts_used and str(parts_used).strip():
                for part_id in str(parts_used).split(","):
                    part_id = part_id.strip()
                    if part_id:
                        session.run(
                            "MATCH (m:MaintenanceAction {event_id: $eid}), (p:Part {part_id: $pid}) "
                            "MERGE (m)-[:CONSUMES {quantity_used: 1}]->(p)",
                            eid=event_id, pid=part_id
                        )
                        r9_count += 1

        logger.info(f"MaintenanceAction 노드 {len(events)}개 생성")
        logger.info(f"R7 TRIGGERS: {r7_count}개 (교정정비만, 예방정비 제외)")
        logger.info(f"R8 RESOLVES: {r8_count}개 (에어필터 교체 제외)")
        logger.info(f"R9 CONSUMES: {r9_count}개")


def create_detects_relations(driver):
    """R2 DETECTS (Sensor → FailureCode) — 도메인 지식 기반 초기 매핑

    f2-anomaly-detection-design.md 기준:
    - 전류 센서 → TOOL_WEAR_001 (마모 시 전류 하락)
    - S축 센서 → SPINDLE_OVERHEAT_001 (과열 시 전류/전력 상승)
    - 위치 센서 → CLAMP_PRESSURE_001 (고정 불량 시 위치 편차)
    - 전력 센서 → COOLANT_LOW_001 (냉각 부족 시 전력 변화)
    """
    SENSOR_FAILURE_MAP = [
        # (sensor_id, failure_code, anomaly_pattern, lead_time_min)
        ("X1_CurrentFeedback", "TOOL_WEAR_001", "전류 지속 하락 (-47%)", 30),
        ("Y1_CurrentFeedback", "TOOL_WEAR_001", "전류 변동 증가", 30),
        ("S1_CurrentFeedback", "SPINDLE_OVERHEAT_001", "전류 지속 상승", 20),
        ("S1_OutputPower", "SPINDLE_OVERHEAT_001", "전력 급증", 20),
        ("S1_OutputCurrent", "SPINDLE_OVERHEAT_001", "출력 전류 상승", 20),
        ("X1_ActualPosition", "CLAMP_PRESSURE_001", "위치 편차 급변 (>0.5mm)", 10),
        ("X1_OutputPower", "COOLANT_LOW_001", "전력 패턴 변화 (간접)", None),
    ]

    with driver.session() as session:
        session.run("MATCH ()-[r:DETECTS]->() DELETE r")
        count = 0
        for sensor_id, fc, pattern, lead_time in SENSOR_FAILURE_MAP:
            props = {"anomaly_pattern": pattern}
            if lead_time is not None:
                props["lead_time_min"] = lead_time
            session.run(
                "MATCH (s:Sensor {sensor_id: $sid}), (f:FailureCode {failure_code: $fc}) "
                "MERGE (s)-[r:DETECTS]->(f) SET r += $props",
                sid=sensor_id, fc=fc, props=props,
            )
            count += 1
        logger.info(f"R2 DETECTS 관계 {count}개 생성 (도메인 지식 기반 초기 매핑)")


def create_references_relations(driver):
    """R10 REFERENCES (MaintenanceAction → Document)

    정비 이벤트의 failure_code와 Document의 failure_code를 매칭하여
    "이 정비에서 참조했을 매뉴얼"을 연결합니다.
    """
    with driver.session() as session:
        session.run("MATCH ()-[r:REFERENCES]->() DELETE r")
        result = session.run("""
            MATCH (m:MaintenanceAction)-[:RESOLVES]->(f:FailureCode)-[:DESCRIBED_BY]->(d:Document)
            MERGE (m)-[:REFERENCES {section_number: 'all'}]->(d)
            RETURN count(*) AS cnt
        """)
        count = result.single()["cnt"]
        logger.info(f"R10 REFERENCES 관계 {count}개 생성 (정비→매뉴얼 자동 매칭)")


def verify(driver):
    """전체 노드/관계 수 확인"""
    with driver.session() as session:
        # 노드 수
        result = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY label")
        logger.info("\n=== 노드 수 ===")
        total_nodes = 0
        for record in result:
            logger.info(f"  {record['label']}: {record['count']}")
            total_nodes += record['count']
        logger.info(f"  총: {total_nodes}")

        # 관계 수
        result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS count ORDER BY rel")
        logger.info("\n=== 관계 수 ===")
        total_rels = 0
        for record in result:
            logger.info(f"  {record['rel']}: {record['count']}")
            total_rels += record['count']
        logger.info(f"  총: {total_rels}")


def main():
    logger.info("=== Neo4j 온톨로지 완성 시작 ===")
    driver = get_neo4j_driver()
    try:
        create_sensor_nodes(driver)
        create_detects_relations(driver)
        create_experiences_relations(driver)
        create_workorder_nodes(driver)
        create_maintenance_nodes(driver)
        create_references_relations(driver)
        verify(driver)
        logger.info("\n=== Neo4j 온톨로지 완성 완료 ===")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
