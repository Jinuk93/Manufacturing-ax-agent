"""
F2 Forecasting 모델 학습 CLI

사용법:
  cd backend
  python train_f2_forecast.py [--data-dir ../data/processed] [--epochs 50]
"""
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.forecaster import SensorForecaster, UNWORN_EXPERIMENTS, WORN_EXPERIMENTS
from app.services.simulator import load_experiment_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="F2 Forecasting 학습")
    parser.add_argument("--data-dir", default=str(Path(__file__).parent.parent / "data" / "processed"))
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--lr", type=float, default=0.001)
    args = parser.parse_args()

    data_dir = Path(args.data_dir) / "kaggle-cnc-mill"
    logger.info(f"데이터 경로: {data_dir}")

    # 실험별 DataFrame 로드
    import pandas as pd
    experiment_dfs = {}
    for csv_file in sorted(data_dir.glob("experiment_*.csv")):
        exp_no = int(csv_file.stem.split("_")[1])
        df = pd.read_csv(csv_file)
        experiment_dfs[exp_no] = df
        logger.info(f"  exp{exp_no:02d}: {len(df)}행")

    logger.info(f"총 {len(experiment_dfs)}개 실험 로드")

    # 학습
    forecaster = SensorForecaster()
    forecaster.fit(experiment_dfs, epochs=args.epochs, lr=args.lr)

    # 저장
    forecaster.save()

    # 평가
    logger.info("\n=== 실험별 Forecast Score 평가 ===")
    eval_result = forecaster.evaluate(experiment_dfs)

    logger.info(f"\n--- unworn (정상) 실험 ---")
    for r in eval_result["details"]["unworn"]:
        logger.info(f"  exp{r['experiment']:02d}: forecast_score={r['forecast_score']:.4f} "
                     f"(MAE={r['avg_mae']:.6f}, {r['n_samples']}샘플)")

    logger.info(f"\n--- worn (마모) 실험 ---")
    for r in eval_result["details"]["worn"]:
        logger.info(f"  exp{r['experiment']:02d}: forecast_score={r['forecast_score']:.4f} "
                     f"(MAE={r['avg_mae']:.6f}, {r['n_samples']}샘플)")

    logger.info(f"\n=== 요약 ===")
    logger.info(f"  unworn 평균: {eval_result['unworn_mean']:.4f}")
    logger.info(f"  worn 평균:   {eval_result['worn_mean']:.4f}")
    logger.info(f"  분리도:      {eval_result['separation']:.4f}")

    if eval_result["separation"] > 0:
        logger.info("  → worn이 unworn보다 높음 ✅ (예측 오차가 큰 것 = 비정상)")
    else:
        logger.info("  → ⚠️ 분리 안 됨. 피처/모델 개선 필요")


if __name__ == "__main__":
    main()
