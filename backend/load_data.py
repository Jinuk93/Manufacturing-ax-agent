"""
데이터 로드 CLI — CSV를 DB에 넣는 진입점

사용법:
  # 배치 모드 (전체 데이터 한 번에)
  python load_data.py batch

  # 스트림 모드 (5초 간격 시뮬레이션)
  python load_data.py stream

  # 스트림 모드 (1초 간격, 빠른 테스트)
  python load_data.py stream --interval 1

사전 조건:
  1. docker-compose up -d (PG + Neo4j 실행)
  2. init.sql이 자동 실행되어 테이블 생성 완료
"""
import sys
import logging
import argparse
from pathlib import Path

# 프로젝트 루트 기준 경로
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = str(PROJECT_ROOT / "data" / "processed")

# 모듈 임포트를 위해 backend를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.simulator import batch_load, stream_load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(description="CSV → DB 데이터 로드")
    parser.add_argument("mode", choices=["batch", "stream"],
                        help="batch: 전체 한 번에 / stream: 5초 간격 시뮬레이션")
    parser.add_argument("--interval", type=int, default=5,
                        help="스트림 모드의 폴링 간격(초). 기본 5초")
    parser.add_argument("--data-dir", type=str, default=DATA_DIR,
                        help=f"데이터 디렉토리 경로. 기본: {DATA_DIR}")

    args = parser.parse_args()

    print(f"데이터 경로: {args.data_dir}")
    print(f"모드: {args.mode}")

    if args.mode == "batch":
        batch_load(args.data_dir)
    else:
        print(f"폴링 간격: {args.interval}초")
        print("Ctrl+C로 중단 가능")
        stream_load(args.data_dir, poll_interval=args.interval)


if __name__ == "__main__":
    main()
