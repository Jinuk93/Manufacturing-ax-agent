"""
F2 Forecasting — 1D-CNN 기반 시계열 예측

ADR-007: 1D-CNN + 4피처 + 30초 입력 → 30초 예측
학습: unworn 정상 패턴으로 "다음 30초를 맞춰라" (자기지도)
검증: worn 실험에서 예측 오차 급증 확인
점수: forecast_error → 0~1 정규화 → IF score와 가중 합산
"""
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

from app.config import settings

logger = logging.getLogger(__name__)

# ADR-007: 핵심 4피처
FORECAST_FEATURES = [
    "X1_CurrentFeedback",   # 마모 핵심
    "S1_CurrentFeedback",   # 과열 핵심
    "S1_OutputPower",       # 과열 보조
    "M1_CURRENT_FEEDRATE",  # 가공 조건
]

# 윈도우 설정 (100ms 샘플링 기준)
INPUT_STEPS = 300   # 30초 (300 × 100ms)
OUTPUT_STEPS = 300  # 30초 예측

# unworn 실험 (exclude_aborted: exp04, 05 제외)
UNWORN_EXPERIMENTS = [1, 2, 3, 11, 12, 17]
WORN_EXPERIMENTS = [6, 7, 8, 9, 10, 13, 14, 15, 16, 18]

# 모델 저장 경로
MODEL_DIR = Path(__file__).parent.parent.parent / "models"


class CNNForecaster(nn.Module):
    """1D-CNN 시계열 예측 모델

    입력: (batch, INPUT_STEPS, 4) — 30초 × 4피처
    출력: (batch, OUTPUT_STEPS, 4) — 30초 예측 × 4피처
    """

    def __init__(self, n_features: int = 4):
        super().__init__()
        self.n_features = n_features

        # 인코더: 시계열 → 압축 표현
        self.encoder = nn.Sequential(
            nn.Conv1d(n_features, 32, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(64),  # 고정 길이로 압축
        )

        # 디코더: 압축 표현 → 미래 예측
        self.decoder = nn.Sequential(
            nn.Linear(128 * 64, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, OUTPUT_STEPS * n_features),
        )

    def forward(self, x):
        # x: (batch, seq_len, features) → (batch, features, seq_len)
        x = x.permute(0, 2, 1)
        encoded = self.encoder(x)  # (batch, 128, 64)
        flat = encoded.reshape(encoded.size(0), -1)  # (batch, 128*64)
        decoded = self.decoder(flat)  # (batch, OUTPUT_STEPS * features)
        return decoded.reshape(-1, OUTPUT_STEPS, self.n_features)


class SensorForecaster:
    """시계열 예측기 — 학습, 예측, 점수 산출"""

    def __init__(self):
        self.model: Optional[CNNForecaster] = None
        self.scaler: Optional[MinMaxScaler] = None
        self.error_max: float = 1.0  # 정규화용 최대 오차
        self.device = torch.device("cpu")

    def _get_col(self, df: pd.DataFrame, col_name: str) -> Optional[pd.Series]:
        """컬럼명 대소문자 호환"""
        if col_name in df.columns:
            return df[col_name]
        if col_name.lower() in df.columns:
            return df[col_name.lower()]
        # snake_case 변환
        import re
        snake = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', col_name)
        snake = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', snake).lower()
        if snake in df.columns:
            return df[snake]
        return None

    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """DataFrame에서 4피처 추출 → numpy array"""
        cols = []
        for feat in FORECAST_FEATURES:
            series = self._get_col(df, feat)
            if series is None:
                raise ValueError(f"피처 '{feat}'를 찾을 수 없습니다. 컬럼: {list(df.columns[:10])}...")
            cols.append(series.values)
        return np.column_stack(cols)  # (n_rows, 4)

    def _create_sequences(self, data: np.ndarray):
        """슬라이딩 윈도우로 (입력, 정답) 쌍 생성"""
        X, y = [], []
        total = INPUT_STEPS + OUTPUT_STEPS
        for i in range(len(data) - total + 1):
            X.append(data[i:i + INPUT_STEPS])
            y.append(data[i + INPUT_STEPS:i + total])
        return np.array(X), np.array(y)

    def fit(self, experiment_dfs: dict[int, pd.DataFrame], epochs: int = 50, lr: float = 0.001):
        """unworn 실험으로 학습

        experiment_dfs: {1: df_exp01, 2: df_exp02, ...}
        """
        logger.info(f"=== F2 Forecasting 학습 시작 (1D-CNN, {len(FORECAST_FEATURES)}피처) ===")

        # 1. 피처 추출 + 스케일링
        all_data = []
        for exp_no in UNWORN_EXPERIMENTS:
            if exp_no not in experiment_dfs:
                continue
            df = experiment_dfs[exp_no]
            if len(df) < INPUT_STEPS + OUTPUT_STEPS:
                logger.warning(f"  exp{exp_no:02d} 길이 부족 ({len(df)}행) — 건너뜀")
                continue
            features = self._extract_features(df)
            all_data.append(features)
            logger.info(f"  exp{exp_no:02d}: {len(df)}행 → {len(df) - INPUT_STEPS - OUTPUT_STEPS + 1}개 샘플")

        if not all_data:
            raise ValueError("학습 가능한 데이터가 없습니다")

        # 스케일러 fit (전체 unworn 데이터)
        combined = np.vstack(all_data)
        self.scaler = MinMaxScaler()
        self.scaler.fit(combined)

        # 2. 시퀀스 생성
        all_X, all_y = [], []
        for data in all_data:
            scaled = self.scaler.transform(data)
            X, y = self._create_sequences(scaled)
            all_X.append(X)
            all_y.append(y)

        X_train = np.vstack(all_X)
        y_train = np.vstack(all_y)
        logger.info(f"  총 학습 샘플: {len(X_train)}개")

        # 3. 모델 학습
        self.model = CNNForecaster(n_features=len(FORECAST_FEATURES))
        self.model.to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        X_tensor = torch.FloatTensor(X_train).to(self.device)
        y_tensor = torch.FloatTensor(y_train).to(self.device)

        # 미니배치 학습
        batch_size = 32
        n_batches = (len(X_train) + batch_size - 1) // batch_size

        self.model.train()
        for epoch in range(epochs):
            epoch_loss = 0.0
            indices = np.random.permutation(len(X_train))

            for batch_idx in range(n_batches):
                start = batch_idx * batch_size
                end = min(start + batch_size, len(X_train))
                idx = indices[start:end]

                X_batch = X_tensor[idx]
                y_batch = y_tensor[idx]

                optimizer.zero_grad()
                pred = self.model(X_batch)
                loss = criterion(pred, y_batch)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / n_batches
            if (epoch + 1) % 10 == 0 or epoch == 0:
                logger.info(f"  Epoch {epoch + 1}/{epochs} — loss: {avg_loss:.6f}")

        # 4. 정규화용 오차 범위 계산
        # unworn 99th를 "정상 상한"으로 잡고, 그 3배를 "최대"로 설정
        # → worn 실험들이 1.0으로 포화하지 않고 분포가 보임
        self.model.eval()
        with torch.no_grad():
            pred_all = self.model(X_tensor).numpy()
        errors = np.mean(np.abs(pred_all - y_train), axis=(1, 2))
        normal_upper = float(np.percentile(errors, 99))  # unworn 99th = 정상 상한
        self.error_max = normal_upper * 3.0  # 3배 확장 → worn 내 차이 보존
        logger.info(f"  정상 상한 오차 (99th): {normal_upper:.6f}")
        logger.info(f"  정규화 기준 (3배 확장): {self.error_max:.6f}")
        logger.info(f"=== 학습 완료 ===")

    def predict(self, df: pd.DataFrame) -> dict:
        """최근 30초 데이터로 예측 + forecast_score 산출

        Returns:
            {
                "forecast_score": float (0~1),
                "predicted_values": np.ndarray (OUTPUT_STEPS, 4),
                "actual_values": np.ndarray or None,
                "mae": float
            }
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("모델이 로드되지 않았습니다. fit() 또는 load()를 먼저 호출하세요.")

        features = self._extract_features(df)

        # 최근 INPUT_STEPS 행만 사용
        if len(features) < INPUT_STEPS:
            # 부족하면 패딩 (앞쪽을 첫 번째 값으로 채움)
            pad_len = INPUT_STEPS - len(features)
            padding = np.tile(features[0:1], (pad_len, 1))
            features = np.vstack([padding, features])

        recent = features[-INPUT_STEPS:]
        scaled = self.scaler.transform(recent)

        # 예측
        self.model.eval()
        with torch.no_grad():
            X = torch.FloatTensor(scaled).unsqueeze(0).to(self.device)
            pred = self.model(X).numpy()[0]  # (OUTPUT_STEPS, 4)

        # 역정규화
        predicted_values = self.scaler.inverse_transform(pred)

        # 오차 계산 (실제 미래 데이터가 있으면)
        actual_values = None
        mae = 0.0
        if len(features) >= INPUT_STEPS + OUTPUT_STEPS:
            actual = features[-OUTPUT_STEPS:]
            actual_scaled = self.scaler.transform(actual)
            mae = float(np.mean(np.abs(pred - actual_scaled)))
            actual_values = actual

        # forecast_score: 예측 오차를 0~1로 정규화
        # 오차가 클수록 "정상 패턴에서 벗어남" → 높은 점수
        forecast_score = min(mae / self.error_max, 1.0) if self.error_max > 0 else 0.0

        return {
            "forecast_score": forecast_score,
            "predicted_values": predicted_values,
            "actual_values": actual_values,
            "mae": mae,
        }

    def evaluate(self, experiment_dfs: dict[int, pd.DataFrame]) -> dict:
        """worn/unworn 실험별 forecast_score 비교"""
        results = {"unworn": [], "worn": []}

        for exp_no, df in experiment_dfs.items():
            if len(df) < INPUT_STEPS + OUTPUT_STEPS:
                continue

            features = self._extract_features(df)
            scaled = self.scaler.transform(features)
            X, y = self._create_sequences(scaled)

            if len(X) == 0:
                continue

            self.model.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X).to(self.device)
                pred = self.model(X_tensor).numpy()

            errors = np.mean(np.abs(pred - y), axis=(1, 2))
            avg_error = float(np.mean(errors))
            score = min(avg_error / self.error_max, 1.0)

            label = "unworn" if exp_no in UNWORN_EXPERIMENTS else "worn"
            results[label].append({
                "experiment": exp_no,
                "avg_mae": avg_error,
                "forecast_score": score,
                "n_samples": len(X),
            })

        # 요약
        unworn_scores = [r["forecast_score"] for r in results["unworn"]]
        worn_scores = [r["forecast_score"] for r in results["worn"]]

        summary = {
            "unworn_mean": float(np.mean(unworn_scores)) if unworn_scores else 0,
            "worn_mean": float(np.mean(worn_scores)) if worn_scores else 0,
            "separation": 0.0,
            "details": results,
        }
        summary["separation"] = summary["worn_mean"] - summary["unworn_mean"]

        return summary

    def save(self, path: str = None):
        """모델 + 스케일러 + 파라미터 저장"""
        if path is None:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            path = str(MODEL_DIR / "f2_forecaster.pkl")

        data = {
            "model_state": self.model.state_dict() if self.model else None,
            "scaler": self.scaler,
            "error_max": self.error_max,
            "features": FORECAST_FEATURES,
            "input_steps": INPUT_STEPS,
            "output_steps": OUTPUT_STEPS,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"Forecaster 저장: {path}")

    def load(self, path: str = None):
        """저장된 모델 로드"""
        if path is None:
            path = str(MODEL_DIR / "f2_forecaster.pkl")

        with open(path, "rb") as f:
            data = pickle.load(f)

        self.scaler = data["scaler"]
        self.error_max = data.get("error_max", 1.0)

        self.model = CNNForecaster(n_features=len(data.get("features", FORECAST_FEATURES)))
        self.model.load_state_dict(data["model_state"])
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Forecaster 로드: {path}")
