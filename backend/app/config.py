"""
설정값 관리 — 코드 수정 없이 동작 변경 가능
pipeline-design.md의 설정값 11개 + DB 연결 정보
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB 연결
    DATABASE_URL: str = "postgresql+asyncpg://ax_user:ax_password@localhost:5432/ax_agent"
    DATABASE_URL_SYNC: str = "postgresql://ax_user:ax_password@localhost:5432/ax_agent"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "ax_password"

    # F1 설정
    POLL_INTERVAL_SEC: int = 5          # ADR-004 확정
    WINDOW_SIZE_SEC: int = 30           # Phase 3 조정

    # F2 설정
    PREDICTION_WINDOW_MIN: int = 30     # Phase 3 실험
    ANOMALY_THRESHOLD: float = 0.5      # Phase 3 PR곡선
    MODEL_TYPE: str = "isolation_forest" # Phase 3 비교

    # F4 설정
    HYBRID_ALPHA: float = 0.5           # Phase 3 조정
    TOP_K_DOCS: int = 5
    MAX_GRAPH_HOPS: int = 3             # 확정

    # F5 설정
    TEMPERATURE: float = 0.1            # 확정 (일관성)
    STOP_THRESHOLD: float = 0.8         # Phase 3 검증
    REDUCE_THRESHOLD: float = 0.6       # Phase 3 검증
    LLM_PROVIDER: str = "openai"         # OpenAI GPT-4o-mini
    OPENAI_MODEL: str = "gpt-4o-mini"    # 비용 효율적 + JSON mode 지원

    class Config:
        env_file = ".env"


settings = Settings()
