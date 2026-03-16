"""
F2 이상탐지 모델 학습 + 검증 CLI

사용법:
  python train_f2.py

결과:
  - 실험별 이상 점수 출력
  - worn vs unworn 분포 비교
  - 중단 실험 감지율
  - models/f2_detector.pkl 저장
"""
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = str(PROJECT_ROOT / "data" / "processed")

sys.path.insert(0, str(Path(__file__).parent))

from app.services.anomaly_detector import train_and_evaluate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


if __name__ == "__main__":
    detector, summary = train_and_evaluate(DATA_DIR)
    print("\n학습된 모델: models/f2_detector.pkl")
    print("다음 단계: FastAPI 엔드포인트(/api/f2/detect)에 연결")
