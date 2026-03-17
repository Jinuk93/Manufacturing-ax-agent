"""
챗봇 에이전트 — F3(DB 조회) + F4(GraphRAG) + Neo4j + OpenAI 통합

사용자가 설비 이상, 정비 절차, 부품 재고, 고장 이력 등을 자연어로 질문하면:
1. 질문 의도를 분류 (데이터 조회 / 지식 검색 / 일반 대화)
2. 필요한 데이터 소스에서 정보 수집 (DB + Neo4j + pgvector)
3. LLM이 모든 컨텍스트를 종합하여 답변 생성
"""
import json
import logging
from datetime import datetime

try:
    import openai
except ImportError:
    openai = None

from app.config import settings
from app.models.schemas import ChatResponse
from app.services.graphrag import _get_embed_model
from app.services.db import get_connection, release_connection

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """당신은 CNC 밀링 머신 공장의 예지보전 AI 어시스턴트입니다.
현장 기술자와 관리자가 설비 이상, 정비 절차, 부품 재고, 고장 원인에 대해 질문합니다.

중요: 아래에 제공되는 [DB 실시간 데이터], [Neo4j 온톨로지], [정비 매뉴얼 검색 결과]는
실제 시스템에서 조회한 실시간 데이터입니다. 반드시 이 데이터를 기반으로 답변하세요.
데이터가 없다고 하지 마세요 — 아래 데이터에 답이 있습니다.

답변 원칙:
1. 제공된 데이터의 구체적 수치(anomaly_score, IF점수, 예측점수 등)를 인용하며 답변하세요.
2. "매뉴얼이 없다", "정보를 제공할 수 없다" 같은 답변은 하지 마세요.
3. 설비별 상태(정상/주의/위험), 고장 예측 코드, 권고 조치를 명확히 안내하세요.
4. 짧고 명확하게 답변하세요 (3~7문장).
5. 부품 교체, 점검 절차 등은 번호 목록으로 정리하세요.

반드시 한국어로 답변하세요."""


async def answer_chat(message: str, equipment_id: str | None = None) -> ChatResponse:
    """사용자 질문에 대한 AI 답변 생성

    1단계: 질문 의도 분류 → 필요한 데이터 소스 결정
    2단계: DB 조회 + Neo4j 순회 + pgvector 검색
    3단계: 모든 컨텍스트를 LLM에 전달 → 답변 생성
    """
    # 1단계: 필요한 데이터 수집
    context_parts = []
    doc_ids = []

    # DB 데이터 조회 (설비 상태, 재고, 작업, 정비이력)
    db_context = _query_db_context(message, equipment_id)
    if db_context:
        context_parts.append(db_context)

    # Neo4j 온톨로지 순회 (고장→부품, 고장→매뉴얼, 설비→고장이력)
    neo4j_context, neo4j_refs = _query_neo4j_context(message, equipment_id)
    if neo4j_context:
        context_parts.append(neo4j_context)
        doc_ids.extend(neo4j_refs)

    # pgvector 매뉴얼 검색
    docs, pgvec_ids = _search_relevant_docs(message)
    if docs:
        manual_text = "\n\n".join(
            f"[{d['manual_id']}] {d['title']}\n{d['content'][:400]}"
            for d in docs
        )
        context_parts.append(f"[정비 매뉴얼 검색 결과]\n{manual_text}")
        doc_ids.extend(pgvec_ids)

    # 중복 제거
    doc_ids = list(dict.fromkeys(doc_ids))

    # 2단계: LLM 답변 생성
    full_context = "\n\n===\n\n".join(context_parts) if context_parts else "관련 정보 없음"

    if settings.LLM_PROVIDER == "openai" and openai is not None:
        content = await _call_chat_llm(message, full_context, equipment_id)
    else:
        content = _rule_based_chat(message, context_parts, equipment_id)

    return ChatResponse(
        content=content,
        timestamp=datetime.now(),
        references=doc_ids,
    )


def _query_db_context(query: str, equipment_id: str | None) -> str | None:
    """DB에서 관련 데이터 조회 — 질문 키워드 기반"""
    results = []
    query_lower = query.lower()

    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # 설비 상태 (anomaly_score)
                if any(kw in query_lower for kw in [
                    "상태", "status", "anomaly", "이상", "점수", "score",
                    "현재", "current", "cnc", "로그", "log", "감지",
                    "detect", "알람", "alarm", "데이터", "data", "모니터",
                    "monitor", "위험", "경고", "warning", "critical",
                    "예지", "예측", "predict", "forecast", "보전",
                    "리스트", "list", "목록", "현황", "전체",
                ]):
                    eq_ids = [equipment_id] if equipment_id else ["CNC-001", "CNC-002", "CNC-003"]
                    for eq in eq_ids:
                        cur.execute("""
                            SELECT anomaly_score, is_anomaly, predicted_failure_code,
                                   if_score, forecast_score, timestamp
                            FROM anomaly_scores
                            WHERE equipment_id = %s
                            ORDER BY timestamp DESC LIMIT 1
                        """, (eq,))
                        row = cur.fetchone()
                        if row:
                            score = float(row[0]) if row[0] else 0
                            status = "위험" if score >= 0.8 else ("주의" if score >= 0.6 else "정상")
                            if_val = f"{float(row[3]):.2f}" if row[3] is not None else "N/A"
                            fc_val = f"{float(row[4]):.2f}" if row[4] is not None else "N/A"
                            results.append(
                                f"  {eq}: 합산점수={score:.2f}({status}), "
                                f"IF={if_val}, 예측={fc_val}, "
                                f"고장예측={row[2] or '없음'}, "
                                f"시각={row[5]}"
                            )

                # 예지보전 전용: 추세 분석 + 예측 경고
                if any(kw in query_lower for kw in [
                    "예지", "예측", "predict", "forecast", "보전",
                    "추세", "trend", "도달", "사전", "선제",
                ]):
                    eq_ids = [equipment_id] if equipment_id else ["CNC-001", "CNC-002", "CNC-003"]
                    pred_results = []
                    for eq in eq_ids:
                        cur.execute("""
                            SELECT anomaly_score, if_score, forecast_score,
                                   predicted_failure_code, timestamp
                            FROM anomaly_scores
                            WHERE equipment_id = %s
                            ORDER BY timestamp DESC LIMIT 20
                        """, (eq,))
                        rows = cur.fetchall()
                        if rows:
                            latest = rows[0]
                            score = float(latest[0]) if latest[0] else 0
                            if_s = float(latest[1]) if latest[1] is not None else score
                            fc_s = float(latest[2]) if latest[2] is not None else None
                            fc_code = latest[3] or "없음"

                            # 추세 계산
                            scores = [float(r[0]) for r in rows if r[0] is not None]
                            if len(scores) >= 5:
                                half = len(scores) // 2
                                avg_recent = sum(scores[:half]) / half
                                avg_old = sum(scores[half:]) / (len(scores) - half)
                                trend = "상승" if avg_recent - avg_old > 0.02 else ("하강" if avg_old - avg_recent > 0.02 else "안정")
                            else:
                                trend = "데이터 부족"

                            # STOP 도달 예상
                            if len(scores) >= 5 and score < 0.8:
                                rate = (scores[0] - scores[-1]) / len(scores)
                                if rate > 0:
                                    eta_min = ((0.8 - score) / rate * 5) / 60
                                    eta_str = f"약 {int(eta_min)}분" if eta_min <= 60 else f"약 {int(eta_min/60)}시간"
                                else:
                                    eta_str = "도달 예상 없음"
                            elif score >= 0.8:
                                eta_str = "이미 초과"
                            else:
                                eta_str = "데이터 부족"

                            status = "위험" if score >= 0.8 else ("예지보전 대상" if score >= 0.1 else "정상")
                            fc_info = f", CNN예측={fc_s:.2f}" if fc_s is not None else ""
                            pred_results.append(
                                f"  {eq}: 점수={score:.2f}({status}), IF={if_s:.2f}{fc_info}, "
                                f"추세={trend}, STOP도달={eta_str}, "
                                f"고장예측={fc_code}"
                            )
                    if pred_results:
                        results.append("[예지보전 분석 결과]\n" + "\n".join(pred_results))

                # 재고 조회
                if any(kw in query_lower for kw in [
                    "재고", "stock", "inventory", "부품", "part", "p00",
                    "coolant", "endmill", "bearing", "filter", "bolt",
                    "냉각", "엔드밀", "베어링", "필터", "볼트", "수량",
                    "남은", "잔량", "발주", "reorder"
                ]):
                    cur.execute("""
                        SELECT p.part_id, p.part_name, e.stock_quantity, e.reorder_point,
                               e.snapshot_date
                        FROM erp_inventory e
                        JOIN parts p ON e.part_id = p.part_id
                        WHERE e.snapshot_date = (SELECT MAX(snapshot_date) FROM erp_inventory)
                        ORDER BY p.part_id
                    """)
                    for row in cur.fetchall():
                        warning = " ⚠️ 재고 부족!" if row[2] <= row[3] else ""
                        results.append(
                            f"  {row[0]} {row[1]}: 재고={row[2]}개, "
                            f"안전재고={row[3]}개{warning} (기준일: {row[4]})"
                        )

                # 작업지시 조회
                if any(kw in query_lower for kw in [
                    "작업", "work", "order", "납기", "due", "진행",
                    "생산", "가공", "production", "schedule", "일정"
                ]):
                    eq_filter = "WHERE equipment_id = %s" if equipment_id else ""
                    params = (equipment_id,) if equipment_id else ()
                    cur.execute(f"""
                        SELECT work_order_id, equipment_id, priority, status,
                               start_time, end_time
                        FROM mes_work_orders
                        {eq_filter}
                        ORDER BY start_time DESC LIMIT 5
                    """, params)
                    for row in cur.fetchall():
                        results.append(
                            f"  {row[0]} ({row[1]}): 우선순위={row[2]}, "
                            f"상태={row[3]}, 시작={row[4]}, 종료={row[5]}"
                        )

                # 정비이력 조회
                if any(kw in query_lower for kw in [
                    "정비", "maintenance", "이력", "history", "수리",
                    "고장", "failure", "과거", "교체", "점검", "repair",
                    "교정", "preventive", "corrective"
                ]):
                    eq_filter = "WHERE equipment_id = %s" if equipment_id else ""
                    params = (equipment_id,) if equipment_id else ()
                    cur.execute(f"""
                        SELECT event_id, equipment_id, event_type, failure_code,
                               description, duration_min, timestamp
                        FROM maintenance_events
                        {eq_filter}
                        ORDER BY timestamp DESC LIMIT 5
                    """, params)
                    for row in cur.fetchall():
                        results.append(
                            f"  {row[0]} ({row[1]}): {row[2]}, "
                            f"고장={row[3] or '없음'}, {row[4][:50]}, "
                            f"{row[5]}분, {row[6]}"
                        )

                # 센서 원본값 조회
                if any(kw in query_lower for kw in [
                    "센서", "sensor", "전류", "current", "전압", "voltage",
                    "전력", "power", "속도", "velocity", "위치", "position",
                    "가속도", "acceleration", "feedrate", "피드", "값",
                    "x1", "y1", "z1", "s1", "m1"
                ]):
                    eq_ids = [equipment_id] if equipment_id else ["CNC-001", "CNC-002", "CNC-003"]
                    for eq in eq_ids:
                        cur.execute("""
                            SELECT timestamp,
                                   x1_current_feedback, y1_current_feedback,
                                   s1_current_feedback, s1_output_power,
                                   x1_actual_position, x1_command_position,
                                   m1_current_feedrate, machining_process
                            FROM sensor_readings
                            WHERE equipment_id = %s
                            ORDER BY timestamp DESC LIMIT 1
                        """, (eq,))
                        row = cur.fetchone()
                        if row:
                            results.append(
                                f"  {eq} 최신 센서 (시각={row[0]}):\n"
                                f"    X1전류={row[1]:.4f}, Y1전류={row[2]:.4f}, "
                                f"S1전류={row[3]:.4f}\n"
                                f"    S1출력={row[4]:.4f}, X1위치={row[5]:.2f}, "
                                f"X1명령위치={row[6]:.2f}\n"
                                f"    Feedrate={row[7]:.1f}, 공정={row[8]}"
                            )

        finally:
            release_connection(conn)

    except Exception as e:
        logger.warning(f"챗봇 DB 조회 실패: {e}")

    if results:
        return f"[DB 실시간 데이터]\n" + "\n".join(results)
    return None


def _query_neo4j_context(query: str, equipment_id: str | None) -> tuple[str | None, list[str]]:
    """Neo4j 온톨로지 순회 — 고장→부품, 고장→매뉴얼, 설비→고장이력"""
    results = []
    doc_refs = []
    query_lower = query.lower()

    # 고장코드 추출 (영문 코드 + 한국어 키워드 모두 지원)
    _FC_KEYWORDS = {
        "TOOL_WEAR_001": ["tool", "wear", "마모", "공구", "엔드밀", "endmill"],
        "SPINDLE_OVERHEAT_001": ["spindle", "overheat", "과열", "스핀들", "베어링", "bearing"],
        "CLAMP_PRESSURE_001": ["clamp", "pressure", "클램프", "고정", "압력"],
        "COOLANT_LOW_001": ["coolant", "냉각", "절삭유", "냉각수", "low"],
    }
    failure_codes = []
    for fc, keywords in _FC_KEYWORDS.items():
        if fc.lower() in query_lower or any(kw in query_lower for kw in keywords):
            failure_codes.append(fc)

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

        with driver.session() as session:
            # 고장코드 → 필요 부품 + 관련 매뉴얼
            for fc in failure_codes:
                # 부품
                r = session.run(
                    "MATCH (f:FailureCode {failure_code:$fc})-[:REQUIRES]->(p:Part) "
                    "RETURN p.part_id, p.part_name",
                    fc=fc,
                )
                parts = [f"  {rec['p.part_id']} {rec['p.part_name']}" for rec in r]
                if parts:
                    results.append(f"  {fc} 필요 부품:\n" + "\n".join(parts))

                # 매뉴얼
                r = session.run(
                    "MATCH (f:FailureCode {failure_code:$fc})-[:DESCRIBED_BY]->(d:Document) "
                    "RETURN d.manual_id, d.title",
                    fc=fc,
                )
                docs = [(rec["d.manual_id"], rec["d.title"]) for rec in r]
                if docs:
                    results.append(f"  {fc} 관련 매뉴얼:\n" +
                                   "\n".join(f"  {mid} {title}" for mid, title in docs))
                    doc_refs.extend([mid for mid, _ in docs])

            # 설비 → 과거 고장 이력
            if equipment_id and any(kw in query_lower for kw in [
                "고장", "failure", "이력", "과거", "경험", "experience"
            ]):
                r = session.run(
                    "MATCH (e:Equipment {equipment_id:$eq})-[:EXPERIENCES]->(fc:FailureCode) "
                    "RETURN fc.failure_code, fc.description",
                    eq=equipment_id,
                )
                fcs = [f"  {rec['fc.failure_code']}: {rec['fc.description']}" for rec in r]
                if fcs:
                    results.append(f"  {equipment_id} 경험한 고장 유형:\n" + "\n".join(fcs))

                # 과거 정비 이력 (Neo4j)
                r = session.run(
                    "MATCH (e:Equipment {equipment_id:$eq})-[:EXPERIENCES]->(fc:FailureCode)"
                    "<-[:RESOLVES]-(ma:MaintenanceAction) "
                    "RETURN ma.event_id, fc.failure_code, ma.duration_min "
                    "ORDER BY ma.event_id DESC LIMIT 5",
                    eq=equipment_id,
                )
                maint = [f"  {rec['ma.event_id']}: {rec['fc.failure_code']} ({rec['ma.duration_min']}분)"
                         for rec in r]
                if maint:
                    results.append(f"  {equipment_id} 과거 정비:\n" + "\n".join(maint))

        driver.close()

    except Exception as e:
        logger.warning(f"챗봇 Neo4j 조회 실패: {e}")

    if results:
        return f"[Neo4j 온톨로지 데이터]\n" + "\n".join(results), doc_refs
    return None, []


def _search_relevant_docs(query: str, top_k: int = 3) -> tuple[list[dict], list[str]]:
    """pgvector 의미 검색으로 관련 매뉴얼 청크 조회"""
    try:
        model = _get_embed_model()
        query_vec = model.encode(query, normalize_embeddings=True)
        vec_str = "[" + ",".join(str(v) for v in query_vec.tolist()) + "]"

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT manual_id, title, text_content,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM document_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (vec_str, vec_str, top_k))
                rows = cur.fetchall()
        finally:
            release_connection(conn)

        docs = [
            {"manual_id": r[0], "title": r[1], "content": r[2], "similarity": float(r[3])}
            for r in rows
        ]
        doc_ids = [d["manual_id"] for d in docs]
        logger.info(f"챗봇 검색: '{query[:30]}...' → {len(docs)}건 (상위: {doc_ids})")
        return docs, doc_ids

    except Exception as e:
        logger.warning(f"챗봇 문서 검색 실패: {e}")
        return [], []


async def _call_chat_llm(
    message: str,
    context: str,
    equipment_id: str | None,
) -> str:
    """OpenAI GPT-4o-mini 호출 — DB + Neo4j + 매뉴얼 컨텍스트 포함"""
    eq_info = f"\n현재 질문 설비: {equipment_id}" if equipment_id else ""
    user_content = f"""아래 데이터를 참고하여 질문에 답변하세요.{eq_info}

{context}

===

질문: {message}"""

    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=20,
        )
        return response.choices[0].message.content or "답변을 생성할 수 없습니다."
    except Exception as e:
        logger.error(f"챗봇 LLM 호출 실패: {e}")
        return _rule_based_chat(message, [context], equipment_id)


def _rule_based_chat(
    message: str,
    context_parts: list[str],
    equipment_id: str | None,
) -> str:
    """LLM 없이 수집된 데이터만으로 답변 (폴백)"""
    if not context_parts:
        return "관련 정보를 찾을 수 없습니다. 더 구체적인 질문을 입력해 주세요."

    eq_prefix = f"[{equipment_id}] " if equipment_id else ""
    return f"{eq_prefix}수집된 정보:\n\n" + "\n\n".join(context_parts[:3])
