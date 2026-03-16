"""
F4 GraphRAG — Neo4j 그래프 순회 + pgvector 의미 검색

2단계 하이브리드 검색:
1단계: Neo4j에서 고장코드 → 부품/매뉴얼/과거 정비 관계 탐색 (구조적 검색)
2단계: pgvector에서 관련 매뉴얼 섹션의 의미 유사도 검색 (정밀 검색)

현재 Phase 3 초기 버전:
- Neo4j 연동 준비 (노드/관계 미구축 시 PG 폴백)
- pgvector 임베딩 미생성 시 텍스트 기반 폴백
"""
import logging
from typing import Optional

from app.services.db import get_connection
from app.config import settings
from app.models.schemas import (
    GraphRAGResponse,
    RelatedPart,
    RelatedDocument,
    PastMaintenance,
)

logger = logging.getLogger(__name__)


def search_graphrag(
    failure_code: str,
    equipment_id: str,
) -> GraphRAGResponse:
    """F4 GraphRAG 2단계 검색

    1단계: 고장코드 → 필요 부품 + 관련 매뉴얼 + 과거 정비
    2단계: 매뉴얼 의미 검색 (pgvector, Phase 3 후반)
    """
    conn = get_connection()
    try:
        # 1단계: 구조적 검색 (현재는 PG에서 조회, Neo4j 구축 후 전환)
        parts = _search_related_parts(conn, failure_code)
        documents = _search_related_documents(conn, failure_code)
        maintenance = _search_past_maintenance(conn, failure_code, equipment_id)

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

    finally:
        conn.close()


def _search_related_parts(conn, failure_code: str) -> list[RelatedPart]:
    """고장코드 → 필요 부품 매핑 (it-data-synthesis-schema.md 기준)

    Neo4j R4 REQUIRES 관계의 PG 폴백 구현.
    고장코드별 필요 부품은 합성 스키마에서 확정됨.
    """
    # 고장코드 → 부품 매핑 (ontology-design.md + it-data-synthesis-schema.md)
    FAILURE_PART_MAP = {
        "TOOL_WEAR_001": [("P001", 1, "high")],
        "SPINDLE_OVERHEAT_001": [("P002", 1, "high")],
        "CLAMP_PRESSURE_001": [("P004", 1, "medium")],
        "COOLANT_LOW_001": [("P003", 1, "medium")],
    }

    part_specs = FAILURE_PART_MAP.get(failure_code, [])
    if not part_specs:
        return []

    results = []
    for part_id, quantity, urgency in part_specs:
        # 부품 이름은 DB에서 조회
        with conn.cursor() as cur:
            cur.execute("SELECT part_name FROM parts WHERE part_id = %s", (part_id,))
            row = cur.fetchone()
            part_name = row[0] if row else part_id

        results.append(RelatedPart(
            part_id=part_id,
            part_name=part_name,
            quantity=quantity,
            urgency=urgency,
        ))

    return results


def _search_related_documents(conn, failure_code: str) -> list[RelatedDocument]:
    """고장코드 → 관련 매뉴얼 검색

    Neo4j R5 DESCRIBED_BY 관계의 PG 폴백.
    maintenance_manuals.json에서 failure_code로 필터링.
    pgvector 임베딩 구축 후에는 의미 검색으로 전환.
    """
    # 현재는 maintenance_manuals.json 기반 정적 매핑
    # Phase 3 후반: document_embeddings 테이블에서 벡터 검색
    DOC_MAP = {
        "TOOL_WEAR_001": [
            ("DOC-001", "엔드밀 공구 교체 절차서", 0.95),
            ("DOC-002", "공구 마모 점검 체크리스트", 0.90),
            ("DOC-003", "공구 마모 트러블슈팅 가이드", 0.88),
        ],
        "SPINDLE_OVERHEAT_001": [
            ("DOC-004", "스핀들 베어링 교체 절차서", 0.95),
            ("DOC-005", "스핀들 과열 점검 체크리스트", 0.90),
            ("DOC-006", "스핀들 과열 트러블슈팅 가이드", 0.88),
        ],
        "CLAMP_PRESSURE_001": [
            ("DOC-007", "클램프 볼트 교체 절차서", 0.95),
            ("DOC-008", "클램프 압력 이상 점검 체크리스트", 0.90),
            ("DOC-009", "클램프 압력 이상 트러블슈팅 가이드", 0.88),
        ],
        "COOLANT_LOW_001": [
            ("DOC-010", "냉각수 보충 및 필터 교체 절차서", 0.95),
            ("DOC-011", "냉각수 이상 점검 체크리스트", 0.90),
            ("DOC-012", "냉각수 이상 트러블슈팅 가이드", 0.88),
        ],
    }

    docs = DOC_MAP.get(failure_code, [])
    return [
        RelatedDocument(manual_id=d[0], title=d[1], hybrid_score=d[2])
        for d in docs
    ]


def _search_past_maintenance(
    conn, failure_code: str, equipment_id: str
) -> list[PastMaintenance]:
    """해당 설비의 과거 동일 고장코드 정비 이력 조회

    Neo4j R8 RESOLVES 관계의 PG 폴백.
    설비별로 필터링하여 다른 설비의 이력이 섞이지 않도록 합니다.
    """
    sql = """
        SELECT event_id, event_type, duration_min, parts_used
        FROM maintenance_events
        WHERE failure_code = %s
          AND equipment_id = %s
        ORDER BY timestamp DESC
        LIMIT 5
    """
    with conn.cursor() as cur:
        cur.execute(sql, (failure_code, equipment_id))
        rows = cur.fetchall()

    return [
        PastMaintenance(
            event_id=r[0],
            event_type=r[1],
            duration_min=r[2],
            parts_used=r[3],
        )
        for r in rows
    ]
