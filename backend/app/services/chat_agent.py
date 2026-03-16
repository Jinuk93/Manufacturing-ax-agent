"""
챗봇 에이전트 — F4(GraphRAG) + OpenAI를 재사용한 대화형 질의 응답

사용자가 설비 이상, 정비 절차, 부품 재고 등을 자연어로 질문하면
GraphRAG로 관련 문서를 검색하고 LLM이 답변을 생성합니다.
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
from app.services.db import get_connection

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """당신은 CNC 밀링 머신 공장의 예지보전 AI 어시스턴트입니다.
현장 기술자와 관리자가 설비 이상, 정비 절차, 부품 재고, 고장 원인에 대해 질문합니다.

답변 원칙:
1. 검색된 정비 매뉴얼을 근거로 답변하세요.
2. 확실하지 않은 내용은 "정비 매뉴얼에서 확인 필요합니다"라고 하세요.
3. 짧고 명확하게 답변하세요 (3~5문장 이내).
4. 부품 교체, 점검 절차 등은 번호 목록으로 정리하세요.
5. 설비 ID가 제공된 경우 해당 설비에 맞게 답변을 조정하세요.

반드시 한국어로 답변하세요."""


async def answer_chat(message: str, equipment_id: str | None = None) -> ChatResponse:
    """사용자 질문에 대한 AI 답변 생성

    1단계: pgvector 의미 검색으로 관련 매뉴얼 청크 조회
    2단계: 검색 결과를 컨텍스트로 OpenAI에 답변 요청
    """
    # 1단계: 관련 매뉴얼 청크 검색
    docs, doc_ids = _search_relevant_docs(message)

    # 2단계: LLM 답변 생성
    if settings.LLM_PROVIDER == "openai" and openai is not None:
        content = await _call_chat_llm(message, docs, equipment_id)
    else:
        content = _rule_based_chat(message, docs, equipment_id)

    return ChatResponse(
        content=content,
        timestamp=datetime.now(),
        references=doc_ids,
    )


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
            conn.close()

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
    docs: list[dict],
    equipment_id: str | None,
) -> str:
    """OpenAI GPT-4o-mini 호출"""
    # 컨텍스트 구성
    context_parts = []
    for doc in docs:
        context_parts.append(
            f"[{doc['manual_id']}] {doc['title']}\n{doc['content'][:400]}"
        )
    context = "\n\n---\n\n".join(context_parts) if context_parts else "관련 매뉴얼 없음"

    eq_info = f"\n현재 질문 설비: {equipment_id}" if equipment_id else ""
    user_content = f"""참조 매뉴얼:{eq_info}

{context}

---

질문: {message}"""

    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)  # pydantic-settings에서 로드
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=400,
            timeout=20,
        )
        return response.choices[0].message.content or "답변을 생성할 수 없습니다."
    except Exception as e:
        logger.error(f"챗봇 LLM 호출 실패: {e}")
        return _rule_based_chat(message, docs, equipment_id)


def _rule_based_chat(
    message: str,
    docs: list[dict],
    equipment_id: str | None,
) -> str:
    """LLM 없이 검색 결과만으로 답변 (폴백)"""
    if not docs:
        return "관련 정비 매뉴얼을 찾을 수 없습니다. 더 구체적인 질문을 입력해 주세요."

    top = docs[0]
    eq_prefix = f"[{equipment_id}] " if equipment_id else ""
    return (
        f"{eq_prefix}관련 매뉴얼: {top['title']} ({top['manual_id']})\n\n"
        f"{top['content'][:300]}"
    )
