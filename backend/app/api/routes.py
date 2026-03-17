"""
FastAPI 라우터 — 14개 엔드포인트 (실제 서비스 연결)
"""
import json
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SensorCollectRequest, SensorCollectResponse,
    AnomalyDetectRequest, AnomalyDetectResponse, AnomalyResult,
    AnomalyHistoryResponse,
    ITOTSyncRequest, ITOTSyncResponse,
    GraphRAGRequest, GraphRAGResponse,
    LLMActionRequest, LLMActionResponse,
    DashboardSummary, EquipmentStatus,
    AlarmFeedResponse, AlarmEvent,
    HealthResponse,
    ChatRequest, ChatResponse,
    WorkOrderStatusResponse,
)
from app.services.db import get_connection, release_connection
from app.services.itot_sync import sync_itot_context
from app.services.graphrag import search_graphrag as graphrag_search
from app.services.llm_agent import generate_action as llm_generate_action
from app.services.chat_agent import answer_chat
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ── F1: 센서 수집 ──
@router.post("/f1/collect", response_model=SensorCollectResponse)
async def collect_sensor(req: SensorCollectRequest):
    """센서 값 수집 → sensor_readings INSERT"""
    try:
        from app.services.db import insert_sensor_readings
        conn = get_connection()
        try:
            # sensor_data dict → DB 컬럼명 매핑
            row = {"timestamp": req.timestamp, "equipment_id": req.equipment_id}
            row.update({k.lower(): v for k, v in req.sensor_data.items()})
            count = insert_sensor_readings(conn, [row])
            return SensorCollectResponse(
                status="ok", rows_inserted=count,
                equipment_id=req.equipment_id, timestamp=req.timestamp,
            )
        finally:
            release_connection(conn)
    except Exception as e:
        logger.error(f"F1 수집 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F1 수집 실패.")


# ── F2: 이상탐지 ──
@router.post("/f2/detect", response_model=AnomalyDetectResponse)
async def detect_anomaly(req: AnomalyDetectRequest):
    """이상탐지 모델 추론 → anomaly_scores INSERT"""
    try:
        from app.services.anomaly_detector import AnomalyDetector
        import pandas as pd

        detector = AnomalyDetector()
        detector.load("models/f2_detector.pkl")

        # DB에서 최근 윈도우 데이터 조회
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM sensor_readings
                    WHERE equipment_id = %s AND timestamp <= %s
                    ORDER BY timestamp DESC LIMIT 6
                """, (req.equipment_id, req.timestamp))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
        finally:
            release_connection(conn)

        if not rows:
            return AnomalyDetectResponse(
                status="no_data",
                result=AnomalyResult(
                    timestamp=req.timestamp, equipment_id=req.equipment_id,
                    anomaly_score=0.0, is_anomaly=False, model_version="IF-v1",
                ),
            )

        df = pd.DataFrame(rows, columns=columns)
        results = detector.predict(df)
        last = results.iloc[-1]

        # anomaly_scores에 INSERT
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO anomaly_scores (timestamp, equipment_id, anomaly_score, is_anomaly, model_version, predicted_failure_code, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (timestamp, equipment_id) DO UPDATE SET anomaly_score = EXCLUDED.anomaly_score
                """, (req.timestamp, req.equipment_id, float(last["anomaly_score"]),
                      bool(last["is_anomaly"]), "IF-v1", last["predicted_failure_code"],
                      float(last["anomaly_score"])))
            conn.commit()
        finally:
            release_connection(conn)

        return AnomalyDetectResponse(
            status="ok",
            result=AnomalyResult(
                timestamp=req.timestamp, equipment_id=req.equipment_id,
                anomaly_score=float(last["anomaly_score"]),
                is_anomaly=bool(last["is_anomaly"]),
                predicted_failure_code=last["predicted_failure_code"],
                confidence=float(last["anomaly_score"]),
                model_version="IF-v1",
            ),
        )
    except Exception as e:
        logger.error(f"F2 감지 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F2 감지 실패.")


@router.get("/f2/history/{equipment_id}", response_model=AnomalyHistoryResponse)
async def anomaly_history(equipment_id: str, limit: int = 100):
    """특정 설비의 이상 점수 이력"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, equipment_id, anomaly_score, is_anomaly,
                           model_version, predicted_failure_code, confidence
                    FROM anomaly_scores
                    WHERE equipment_id = %s
                    ORDER BY timestamp DESC LIMIT %s
                """, (equipment_id, limit))
                rows = cur.fetchall()
        finally:
            release_connection(conn)
        history = [
            AnomalyResult(
                timestamp=r[0], equipment_id=r[1], anomaly_score=r[2],
                is_anomaly=r[3], model_version=r[4],
                predicted_failure_code=r[5], confidence=r[6],
            ) for r in rows
        ]
        return AnomalyHistoryResponse(equipment_id=equipment_id, history=history)
    except Exception as e:
        logger.error(f"F2 이력 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F2 이력 조회 실패.")


# ── F3: IT/OT 동기화 (실제 서비스) ──
@router.post("/f3/sync", response_model=ITOTSyncResponse)
async def sync_itot(req: ITOTSyncRequest):
    """이상 감지 시 IT 데이터 조회"""
    try:
        return sync_itot_context(
            equipment_id=req.equipment_id, timestamp=req.timestamp,
            predicted_failure_code=req.predicted_failure_code,
        )
    except Exception as e:
        logger.error(f"F3 동기화 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F3 동기화 실패.")


# ── F4: GraphRAG (실제 Neo4j + pgvector) ──
@router.post("/f4/search", response_model=GraphRAGResponse)
async def search_rag(req: GraphRAGRequest):
    """Neo4j 그래프 순회 + pgvector 의미 검색"""
    try:
        return graphrag_search(failure_code=req.failure_code, equipment_id=req.equipment_id)
    except Exception as e:
        logger.error(f"F4 검색 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F4 검색 실패.")


# ── F5: LLM 판단 (실제 OpenAI) ──
@router.post("/f5/generate-action", response_model=LLMActionResponse)
async def gen_action(req: LLMActionRequest):
    """F2+F3+F4 결과를 종합하여 조치 권고"""
    try:
        logger.info(f"F5 판단 요청: {req.equipment_id}")
        return await llm_generate_action(
            f2_result=req.f2_result, f3_context=req.f3_context,
            f4_rag_result=req.f4_rag_result,
        )
    except Exception as e:
        logger.error(f"F5 판단 실패 ({req.equipment_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F5 판단 실패.")


# ── F6: 대시보드 (실제 DB) ──
@router.get("/f6/summary", response_model=DashboardSummary)
async def dashboard_summary():
    """CNC 3대 상태 요약 (최신 anomaly_scores 기반)"""
    try:
        conn = get_connection()
        try:
            equipments = []
            for eq_id in ["CNC-001", "CNC-002", "CNC-003"]:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT anomaly_score, is_anomaly, predicted_failure_code, timestamp
                        FROM anomaly_scores
                        WHERE equipment_id = %s
                        ORDER BY timestamp DESC LIMIT 1
                    """, (eq_id,))
                    row = cur.fetchone()
                if row:
                    score = float(row[0])
                    status = "critical" if score >= 0.8 else ("warning" if score >= 0.6 else "normal")
                    equipments.append(EquipmentStatus(
                        equipment_id=eq_id, status=status, anomaly_score=score,
                        predicted_failure_code=row[2], last_updated=row[3],
                    ))
                else:
                    equipments.append(EquipmentStatus(
                        equipment_id=eq_id, status="normal", anomaly_score=0.0,
                        last_updated=datetime.now(),
                    ))
        finally:
            release_connection(conn)
        return DashboardSummary(equipments=equipments)
    except Exception as e:
        logger.error(f"F6 summary 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F6 summary 실패.")


@router.get("/f6/sensors/{equipment_id}")
async def sensor_timeseries(equipment_id: str, duration_hours: int = 1):
    """특정 설비의 센서 시계열"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # CSV 데이터는 과거 타임스탬프이므로 NOW() 필터 대신
                # 최신 N행을 내림차순 조회 후 역정렬하여 시계열 반환
                cur.execute("""
                    SELECT timestamp, x1_current_feedback, y1_current_feedback,
                           s1_current_feedback, x1_output_power, s1_output_power
                    FROM sensor_readings
                    WHERE equipment_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 300
                """, (equipment_id,))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
        finally:
            release_connection(conn)
        series = [dict(zip(columns, [str(v) if isinstance(v, datetime) else v for v in row])) for row in rows]
        return {"equipment_id": equipment_id, "duration_hours": duration_hours, "series": series}
    except Exception as e:
        logger.error(f"F6 sensors 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F6 sensors 실패.")


@router.get("/f6/anomaly/{equipment_id}", response_model=AnomalyResult)
async def anomaly_status(equipment_id: str):
    """특정 설비의 현재 이상 점수"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, equipment_id, anomaly_score, is_anomaly,
                           model_version, predicted_failure_code, confidence
                    FROM anomaly_scores
                    WHERE equipment_id = %s
                    ORDER BY timestamp DESC LIMIT 1
                """, (equipment_id,))
                row = cur.fetchone()
        finally:
            release_connection(conn)
        if row:
            return AnomalyResult(
                timestamp=row[0], equipment_id=row[1], anomaly_score=row[2],
                is_anomaly=row[3], model_version=row[4],
                predicted_failure_code=row[5], confidence=row[6],
            )
        return AnomalyResult(
            timestamp=datetime.now(), equipment_id=equipment_id,
            anomaly_score=0.0, is_anomaly=False, model_version="IF-v1",
        )
    except Exception as e:
        logger.error(f"F6 anomaly 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F6 anomaly 실패.")


@router.get("/f6/work-order/{equipment_id}", response_model=WorkOrderStatusResponse)
async def work_order_status(equipment_id: str):
    """작업 + 재고 현황"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # 최근 작업
                cur.execute("""
                    SELECT work_order_id, product_type, due_date, priority, status
                    FROM mes_work_orders
                    WHERE equipment_id = %s ORDER BY start_time DESC LIMIT 1
                """, (equipment_id,))
                wo = cur.fetchone()
                # 최신 재고
                cur.execute("""
                    SELECT e.part_id, p.part_name, e.stock_quantity, e.reorder_point
                    FROM erp_inventory e JOIN parts p ON e.part_id = p.part_id
                    WHERE e.snapshot_date = (SELECT MAX(snapshot_date) FROM erp_inventory)
                    ORDER BY e.part_id
                """)
                inv = cur.fetchall()
                # 최근 정비 이력 (5건)
                cur.execute("""
                    SELECT event_id, failure_code, event_type, duration_min, parts_used,
                           timestamp
                    FROM maintenance_events
                    WHERE equipment_id = %s
                    ORDER BY timestamp DESC LIMIT 5
                """, (equipment_id,))
                maint = cur.fetchall()
        finally:
            release_connection(conn)
        return {
            "equipment_id": equipment_id,
            "work_order": {"work_order_id": wo[0], "product_type": wo[1], "due_date": str(wo[2]), "priority": wo[3], "status": wo[4]} if wo else None,
            "inventory": [{"part_id": r[0], "part_name": r[1], "stock_quantity": r[2], "reorder_point": r[3]} for r in inv],
            "recent_maintenance": [
                {"event_id": r[0], "failure_code": r[1], "event_type": r[2],
                 "duration_min": r[3], "parts_used": r[4], "event_time": str(r[5])}
                for r in maint
            ],
        }
    except Exception as e:
        logger.error(f"F6 work-order 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F6 work-order 실패.")


@router.get("/f6/action/{equipment_id}", response_model=LLMActionResponse)
async def action_report(equipment_id: str):
    """온디맨드 F2→F3→F4→F5 파이프라인 실행 후 LLM 조치 리포트 반환"""
    try:
        # F2: 최신 이상 점수 조회
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, equipment_id, anomaly_score, is_anomaly,
                           model_version, predicted_failure_code, confidence
                    FROM anomaly_scores
                    WHERE equipment_id = %s
                    ORDER BY timestamp DESC LIMIT 1
                """, (equipment_id,))
                row = cur.fetchone()
        finally:
            release_connection(conn)

        if not row:
            raise HTTPException(status_code=404, detail="이상탐지 데이터 없음")

        f2_result = AnomalyResult(
            timestamp=row[0], equipment_id=row[1], anomaly_score=row[2],
            is_anomaly=row[3], model_version=row[4],
            predicted_failure_code=row[5], confidence=row[6],
        )
        failure_code = f2_result.predicted_failure_code or "TOOL_WEAR_001"

        # F3: IT/OT 동기화
        f3_context = sync_itot_context(
            equipment_id=equipment_id,
            timestamp=f2_result.timestamp,
            predicted_failure_code=failure_code,
        )

        # F4: GraphRAG 검색
        f4_rag_result = graphrag_search(
            failure_code=failure_code,
            equipment_id=equipment_id,
        )

        # F5: LLM 판단
        result = await llm_generate_action(
            f2_result=f2_result,
            f3_context=f3_context,
            f4_rag_result=f4_rag_result,
        )

        # F5 결과를 DB에 저장 (F6 대시보드 조회용)
        try:
            conn2 = get_connection()
            try:
                with conn2.cursor() as cur:
                    cur.execute("""
                        INSERT INTO llm_action_reports
                        (equipment_id, timestamp, recommendation, confidence, reasoning,
                         action_steps, parts_needed, predicted_failure_code, estimated_downtime_min)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        result.equipment_id, result.timestamp, result.recommendation,
                        result.confidence, result.reasoning,
                        json.dumps(result.action_steps, ensure_ascii=False),
                        json.dumps([p.model_dump() for p in result.parts_needed], ensure_ascii=False),
                        result.predicted_failure_code, result.estimated_downtime_min,
                    ))
                conn2.commit()
            finally:
                release_connection(conn2)
        except Exception as e:
            logger.warning(f"F5 결과 DB 저장 실패 (비치명적): {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"F6 action 실패 ({equipment_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F6 action 실패.")


@router.get("/f6/alarms", response_model=AlarmFeedResponse)
async def alarm_feed(limit: int = 20):
    """전체 알람 피드 (is_anomaly=true인 최근 N건)"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, equipment_id, anomaly_score,
                           predicted_failure_code, confidence
                    FROM anomaly_scores
                    WHERE is_anomaly = true
                    ORDER BY timestamp DESC LIMIT %s
                """, (limit,))
                rows = cur.fetchall()
        finally:
            release_connection(conn)
        alarms = [
            AlarmEvent(
                timestamp=r[0], equipment_id=r[1], anomaly_score=r[2],
                predicted_failure_code=r[3] or "UNKNOWN",
                confidence=r[4] or 0.0,
                severity="critical" if r[2] >= 0.8 else "warning",
            ) for r in rows
        ]
        return AlarmFeedResponse(alarms=alarms, total=len(alarms))
    except Exception as e:
        logger.error(f"F6 alarms 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="F6 alarms 실패.")


# ── 챗봇 ──
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """대화형 AI 질의 — pgvector 검색 + LLM 답변"""
    try:
        return await answer_chat(message=req.message, equipment_id=req.equipment_id)
    except Exception as e:
        logger.error(f"챗봇 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="챗봇 응답 실패.")


# ── 헬스 체크 ──
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """PostgreSQL + Neo4j 연결 상태 확인"""
    pg_ok = False
    neo_ok = False
    try:
        conn = get_connection()
        conn.cursor().execute("SELECT 1")
        release_connection(conn)
        pg_ok = True
    except Exception:
        pass
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
        with driver.session() as s:
            s.run("RETURN 1")
        driver.close()
        neo_ok = True
    except Exception:
        pass
    return HealthResponse(status="ok" if pg_ok and neo_ok else "degraded", postgres=pg_ok, neo4j=neo_ok, timestamp=datetime.now())
