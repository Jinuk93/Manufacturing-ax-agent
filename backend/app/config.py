"""
설정값 관리 — 코드 수정 없이 동작 변경 가능
pipeline-design.md의 설정값 + DB 연결 + 모델 하이퍼파라미터
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
    POLL_INTERVAL_SEC: int = 5              # ADR-004 확정
    WINDOW_SIZE_SEC: int = 30               # 슬라이딩 윈도우

    # F2 설정
    PREDICTION_WINDOW_MIN: int = 30
    ANOMALY_THRESHOLD: float = 0.5
    MODEL_TYPE: str = "isolation_forest"
    IF_CONTAMINATION: float = 0.1           # IF 이상 비율 추정
    IF_N_ESTIMATORS: int = 200              # IF 트리 수

    # F2 고장코드 분류 임계치
    SPINDLE_CURRENT_RATIO: float = 1.3      # S1 전류 median 대비 비율
    SPINDLE_FEEDRATE_MIN: float = 15.0      # 고속 기준 feedrate
    TOOL_WEAR_RATIO: float = 0.7            # X1 전류 median 대비 비율
    CLAMP_POSITION_THRESHOLD: float = 0.5   # 위치 편차 임계치 (mm)

    # F2 Forecasting (ADR-007)
    FORECAST_WEIGHT: float = 0.4            # final = (1-w)*IF + w*forecast
    FORECAST_INPUT_STEPS: int = 300         # 30초 입력
    FORECAST_OUTPUT_STEPS: int = 300        # 30초 예측

    # F4 설정
    HYBRID_ALPHA: float = 0.5               # BM25 vs vector 비중
    TOP_K_DOCS: int = 5
    MAX_GRAPH_HOPS: int = 3
    EMBED_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # F5 설정
    TEMPERATURE: float = 0.1
    STOP_THRESHOLD: float = 0.8
    REDUCE_THRESHOLD: float = 0.6
    LLM_PROVIDER: str = "openai"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    LLM_MAX_RETRIES: int = 2               # 재시도 횟수
    LLM_TIMEOUT: int = 30                  # 타임아웃 (초)

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    class Config:
        env_file = (".env", "../.env")


settings = Settings()
