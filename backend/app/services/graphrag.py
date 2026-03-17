"""
F4 GraphRAG — Neo4j 그래프 순회 + pgvector 의미 검색

2단계 하이브리드 검색:
1단계: Neo4j Cypher로 고장코드 → 부품/매뉴얼/과거 정비 관계 탐색
2단계: pgvector cosine 유사도로 매뉴얼 섹션 정밀 검색
"""
import logging
from typing import Optional

from neo4j import GraphDatabase

from app.services.db import get_connection, release_connection
from app.config import settings
from app.models.schemas import (
    GraphRAGResponse,
    RelatedPart,
    RelatedDocument,
    PastMaintenance,
)

logger = logging.getLogger(__name__)

# 싱글턴: Neo4j 드라이버 + SentenceTransformer (한 번만 로드)
_neo4j_driver = None
_embed_model = None


def _get_neo4j_driver():
    """Neo4j 드라이버 싱글턴"""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        logger.info("Neo4j 드라이버 초기화 완료")
    return _neo4j_driver


def _get_embed_model():
    """SentenceTransformer 싱글턴 (첫 호출 시 수 초 로드, 이후 즉시)"""
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(f"sentence-transformers/{settings.EMBED_MODEL}")
        logger.info("SentenceTransformer 모델 로드 완료 (384차원)")
    return _embed_model



def search_graphrag(
    failure_code: str,
    equipment_id: str,
) -> GraphRAGResponse:
    """F4 GraphRAG 2단계 검색

    1단계: Neo4j Cypher — 고장코드에서 관계를 타고 부품/매뉴얼/과거 정비 탐색
    2단계: pgvector — 매뉴얼 섹션의 의미 유사도 검색
    """
    # 1단계: Neo4j 구조적 검색
    try:
        driver = _get_neo4j_driver()
        parts = _neo4j_search_parts(driver, failure_code)
        documents_neo = _neo4j_search_documents(driver, failure_code)
        maintenance = _neo4j_search_maintenance(driver, failure_code, equipment_id)
    except Exception as e:
        # E3 폴백: Neo4j 연결 실패 시 PG로 폴백
        logger.warning(f"Neo4j 연결 실패, PG 폴백: {e}")
        conn = get_connection()
        try:
            parts = _pg_fallback_parts(conn, failure_code)
            documents_neo = []
            maintenance = _pg_fallback_maintenance(conn, failure_code, equipment_id)
        finally:
            release_connection(conn)

    # 2단계: pgvector 의미 검색 (Neo4j에서 찾은 매뉴얼 범위 내에서)
    try:
        documents = _pgvector_search_documents(failure_code, documents_neo)
    except Exception as e:
        logger.warning(f"pgvector 검색 실패, Neo4j 결과만 사용: {e}")
        documents = [
            RelatedDocument(manual_id=d["manual_id"], title=d["title"], hybrid_score=0.9)
            for d in documents_neo
        ]

    logger.info(
        f"F4 검색 완료: {failure_code} @ {equipment_id} | "
        f"부품={len(parts)}종, 문서={len(documents)}건, 정비이력={len(maintenance)}건"
    )

    return GraphRAGResponse(
        failure_code=failure_code,
        related_parts=parts,
        related_documents=documents,
        past_maintenance=maintenance,
    )


# ============================================
# 1단계: Neo4j Cypher 검색
# ============================================

def _neo4j_search_parts(driver, failure_code: str) -> list[RelatedPart]:
    """R4 REQUIRES: FailureCode → Part"""
    with driver.session() as session:
        result = session.run("""
            MATCH (f:FailureCode {failure_code: $fc})-[r:REQUIRES]->(p:Part)
            RETURN p.part_id AS part_id, p.part_name AS part_name,
                   r.quantity AS quantity, r.urgency AS urgency
        """, fc=failure_code)
        parts = []
        for record in result:
            parts.append(RelatedPart(
                part_id=record["part_id"],
                part_name=record["part_name"],
                quantity=record["quantity"] or 1,
                urgency=record["urgency"] or "medium",
            ))
    logger.info(f"  Neo4j R4 REQUIRES: {len(parts)}종")
    return parts


def _neo4j_search_documents(driver, failure_code: str) -> list[dict]:
    """R5 DESCRIBED_BY: FailureCode → Document (메타데이터만)"""
    with driver.session() as session:
        result = session.run("""
            MATCH (f:FailureCode {failure_code: $fc})-[r:DESCRIBED_BY]->(d:Document)
            RETURN d.manual_id AS manual_id, d.title AS title,
                   d.document_type AS document_type
        """, fc=failure_code)
        docs = []
        for record in result:
            docs.append({
                "manual_id": record["manual_id"],
                "title": record["title"],
                "document_type": record["document_type"],
            })
    logger.info(f"  Neo4j R5 DESCRIBED_BY: {len(docs)}건")
    return docs


def _neo4j_search_maintenance(driver, failure_code: str, equipment_id: str) -> list[PastMaintenance]:
    """R8 RESOLVES: MaintenanceAction → FailureCode (해당 설비만)"""
    with driver.session() as session:
        result = session.run("""
            MATCH (m:MaintenanceAction)-[r:RESOLVES]->(f:FailureCode {failure_code: $fc})
            WHERE EXISTS {
                MATCH (e:Equipment {equipment_id: $eid})-[:EXECUTES]->(:WorkOrder)-[:TRIGGERS]->(m)
            } OR EXISTS {
                MATCH (m) WHERE m.event_id STARTS WITH 'MT-'
            }
            RETURN m.event_id AS event_id, m.event_type AS event_type,
                   r.resolution_time_min AS duration_min
            ORDER BY m.event_id DESC
            LIMIT 5
        """, fc=failure_code, eid=equipment_id)
        maint = []
        for record in result:
            maint.append(PastMaintenance(
                event_id=record["event_id"],
                event_type=record["event_type"],
                duration_min=record["duration_min"] or 0,
                parts_used=None,
            ))
    # parts_used는 R9 CONSUMES에서 보강
    if maint:
        _enrich_parts_used(driver, maint)
    logger.info(f"  Neo4j R8 RESOLVES: {len(maint)}건")
    return maint


def _enrich_parts_used(driver, maint_list: list[PastMaintenance]):
    """R9 CONSUMES: MaintenanceAction → Part (부품 정보 보강)"""
    with driver.session() as session:
        for m in maint_list:
            result = session.run("""
                MATCH (ma:MaintenanceAction {event_id: $eid})-[:CONSUMES]->(p:Part)
                RETURN p.part_id AS part_id
            """, eid=m.event_id)
            parts = [r["part_id"] for r in result]
            m.parts_used = ",".join(parts) if parts else None


# ============================================
# 2단계: pgvector 의미 검색
# ============================================

def _pgvector_search_documents(
    failure_code: str,
    neo4j_docs: list[dict],
) -> list[RelatedDocument]:
    """Neo4j에서 좁혀진 매뉴얼 범위 내에서 pgvector 의미 검색

    검색 쿼리: 고장코드의 설명 텍스트
    범위: Neo4j에서 찾은 manual_id 목록
    """
    conn = get_connection()
    try:
        # 고장코드 설명을 쿼리로 사용
        with conn.cursor() as cur:
            cur.execute(
                "SELECT description FROM failure_codes WHERE failure_code = %s",
                (failure_code,)
            )
            row = cur.fetchone()
            query_text = row[0] if row else failure_code

        # 쿼리 벡터 생성 (싱글턴 모델 사용)
        model = _get_embed_model()
        query_vec = model.encode(query_text, normalize_embeddings=True)
        vec_str = "[" + ",".join(str(v) for v in query_vec.tolist()) + "]"

        # Neo4j에서 찾은 manual_id 범위로 필터링
        manual_ids = [d["manual_id"] for d in neo4j_docs]
        if not manual_ids:
            return []

        placeholders = ",".join(["%s"] * len(manual_ids))
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT DISTINCT ON (manual_id)
                    manual_id, title,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM document_embeddings
                WHERE manual_id IN ({placeholders})
                ORDER BY manual_id, embedding <=> %s::vector
            """, (vec_str, *manual_ids, vec_str))
            rows = cur.fetchall()

        documents = []
        for r in rows:
            documents.append(RelatedDocument(
                manual_id=r[0],
                title=r[1],
                hybrid_score=round(float(r[2]), 3),
            ))

        # 유사도 내림차순 정렬
        documents.sort(key=lambda d: d.hybrid_score, reverse=True)
        logger.info(f"  pgvector 검색: {len(documents)}건 (범위: {len(manual_ids)} 매뉴얼)")
        return documents

    finally:
        release_connection(conn)


# ============================================
# PG 폴백 (Neo4j 연결 실패 시)
# ============================================

def _pg_fallback_parts(conn, failure_code: str) -> list[RelatedPart]:
    """PG 폴백: 고장코드 → 부품 매핑"""
    FAILURE_PART_MAP = {
        "TOOL_WEAR_001": [("P001", 1, "high")],
        "SPINDLE_OVERHEAT_001": [("P002", 1, "high")],
        "CLAMP_PRESSURE_001": [("P004", 1, "medium")],
        "COOLANT_LOW_001": [("P003", 1, "medium")],
    }
    specs = FAILURE_PART_MAP.get(failure_code, [])
    results = []
    for part_id, qty, urgency in specs:
        with conn.cursor() as cur:
            cur.execute("SELECT part_name FROM parts WHERE part_id = %s", (part_id,))
            row = cur.fetchone()
            name = row[0] if row else part_id
        results.append(RelatedPart(part_id=part_id, part_name=name, quantity=qty, urgency=urgency))
    return results


def _pg_fallback_maintenance(conn, failure_code: str, equipment_id: str) -> list[PastMaintenance]:
    """PG 폴백: 과거 정비 이력"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT event_id, event_type, duration_min, parts_used
            FROM maintenance_events
            WHERE failure_code = %s AND equipment_id = %s
            ORDER BY timestamp DESC LIMIT 5
        """, (failure_code, equipment_id))
        rows = cur.fetchall()
    return [
        PastMaintenance(event_id=r[0], event_type=r[1], duration_min=r[2], parts_used=r[3])
        for r in rows
    ]
