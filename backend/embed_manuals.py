"""
매뉴얼 임베딩 — maintenance_manuals.json → pgvector INSERT

1. JSON에서 12건 × N섹션 = 청크 추출
2. sentence-transformers로 벡터 변환 (768차원)
3. PostgreSQL document_embeddings 테이블에 INSERT

사용법:
  python embed_manuals.py

사전 조건:
  - docker-compose up -d (PG 실행)
  - pip install sentence-transformers
"""
import sys
import json
import logging
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from app.services.db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
MANUALS_PATH = PROJECT_ROOT / "data" / "processed" / "it-data" / "maintenance_manuals.json"

# 임베딩 모델 (768차원, 다국어 지원, 로컬 무료)
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_manuals() -> list[dict]:
    """maintenance_manuals.json에서 청크 추출"""
    with open(MANUALS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    for doc in data["documents"]:
        manual_id = doc["manual_id"]
        title = doc["title"]

        for i, section in enumerate(doc["sections"]):
            chunk_id = f"{manual_id}-{i+1}"
            heading = section["heading"]
            content = section["content"]

            # 제목 + 본문을 합쳐서 임베딩 (검색 정확도 향상)
            text = f"{title} — {heading}\n{content}"

            chunks.append({
                "chunk_id": chunk_id,
                "manual_id": manual_id,
                "chunk_number": i + 1,
                "title": f"{title} — {heading}",
                "text_content": content,
                "embed_text": text,  # 임베딩용 (제목 포함)
            })

    logger.info(f"청크 추출: {len(data['documents'])}문서 → {len(chunks)}청크")
    return chunks


def generate_embeddings(chunks: list[dict]) -> np.ndarray:
    """sentence-transformers로 벡터 생성 (768차원)"""
    from sentence_transformers import SentenceTransformer

    logger.info(f"모델 로드 중: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    texts = [c["embed_text"] for c in chunks]
    logger.info(f"임베딩 생성 중: {len(texts)}청크...")

    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    logger.info(f"임베딩 완료: shape={embeddings.shape}")

    return embeddings


def insert_embeddings(chunks: list[dict], embeddings: np.ndarray):
    """document_embeddings 테이블에 INSERT"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 기존 데이터 삭제 (재실행 시 중복 방지)
            cur.execute("DELETE FROM document_embeddings")
            logger.info("기존 임베딩 데이터 삭제")

            for i, chunk in enumerate(chunks):
                vec = embeddings[i].tolist()
                vec_str = "[" + ",".join(str(v) for v in vec) + "]"

                cur.execute(
                    """
                    INSERT INTO document_embeddings
                    (chunk_id, manual_id, chunk_number, title, text_content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
                    """,
                    (
                        chunk["chunk_id"],
                        chunk["manual_id"],
                        chunk["chunk_number"],
                        chunk["title"],
                        chunk["text_content"],
                        vec_str,
                    ),
                )

        conn.commit()
        logger.info(f"INSERT 완료: {len(chunks)}청크")
    finally:
        conn.close()


def verify():
    """삽입 결과 확인 + 유사도 검색 테스트"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 총 청크 수
            cur.execute("SELECT count(*) FROM document_embeddings")
            count = cur.fetchone()[0]
            logger.info(f"총 임베딩 청크: {count}개")

            # 문서별 청크 수
            cur.execute("""
                SELECT manual_id, count(*) as chunks
                FROM document_embeddings
                GROUP BY manual_id
                ORDER BY manual_id
            """)
            for row in cur.fetchall():
                logger.info(f"  {row[0]}: {row[1]}청크")

            # 유사도 검색 테스트: "스핀들 과열 시 베어링 교체 방법"
            logger.info("\n=== 유사도 검색 테스트 ===")
            logger.info('쿼리: "스핀들 과열 시 베어링 교체 방법"')

            # 쿼리 벡터 생성
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(MODEL_NAME)
            query_vec = model.encode("스핀들 과열 시 베어링 교체 방법", normalize_embeddings=True)
            vec_str = "[" + ",".join(str(v) for v in query_vec.tolist()) + "]"

            cur.execute(f"""
                SELECT chunk_id, title, 1 - (embedding <=> '{vec_str}'::vector) AS similarity
                FROM document_embeddings
                ORDER BY embedding <=> '{vec_str}'::vector
                LIMIT 5
            """)
            for row in cur.fetchall():
                logger.info(f"  {row[0]} (sim={row[2]:.3f}): {row[1]}")

    finally:
        conn.close()


def main():
    logger.info("=== 매뉴얼 임베딩 시작 ===")

    # 1. 청크 추출
    chunks = load_manuals()

    # 2. 벡터 생성
    embeddings = generate_embeddings(chunks)

    # 3. DB 저장
    insert_embeddings(chunks, embeddings)

    # 4. 검증
    verify()

    logger.info("\n=== 매뉴얼 임베딩 완료 ===")


if __name__ == "__main__":
    main()
