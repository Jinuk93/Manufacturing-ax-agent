"""
F2 이상탐지 — Isolation Forest 베이스라인

설계: docs/2-architecture/f2-anomaly-detection-design.md
접근: 비지도 학습 (시점별 이상/정상 라벨 없음)
전략: unworn 실험으로 "정상 패턴" 학습 → 전체에 적용

사용법:
  detector = AnomalyDetector()
  detector.fit(df_unworn)           # unworn 실험으로 정상 패턴 학습
  results = detector.predict(df)     # 전체 데이터에 이상 점수 산출
"""
import logging
import pickle
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

from app.config import settings

logger = logging.getLogger(__name__)


def to_snake(name: str) -> str:
    """CamelCase/PascalCase → snake_case 변환 (X1_CurrentFeedback → x1_current_feedback)"""
    s1 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

# 피처셋 (기존 10개 + 확장 4개 = 14개)
FEATURE_COLUMNS = [
    # 기존 10개 (1차 피처셋)
    "X1_CurrentFeedback",      # worn -47% (핵심 지표)
    "Y1_CurrentFeedback",      # 마모 보조
    "S1_CurrentFeedback",      # 스핀들 과열
    "X1_OutputPower",          # worn +36%
    "S1_OutputPower",          # 스핀들 부하
    "X1_ActualVelocity",       # 명령 대비 편차
    "X1_CommandVelocity",      # 기준값
    "S1_ActualVelocity",       # 과열 시 속도 미달
    "M1_CURRENT_FEEDRATE",     # feedrate=50은 비절삭
    "Machining_Process",       # 공정별 정상 범위 다름
    # 확장 4개 (축 간 편차 + 추가 전력)
    "X1_ActualPosition",       # 위치 편차 계산용
    "X1_CommandPosition",      # 위치 편차 계산용
    "Y1_OutputPower",          # Y축 전력 (X축과 비교)
    "S1_OutputCurrent",        # 스핀들 출력 전류
]

# 파생 피처 (prepare_features에서 계산)
DERIVED_FEATURES = [
    "x_position_deviation",    # |ActualPosition - CommandPosition| → 클램프 이상 지표
    "x_power_ratio",           # X1_OutputPower / S1_OutputPower → 부하 비율
]

# 범주형 → 수치 매핑 (Machining_Process)
PROCESS_MAP = {
    "Starting": 0, "Prep": 1,
    "Layer 1 Up": 2, "Layer 1 Down": 3,
    "Layer 2 Up": 4, "Layer 2 Down": 5,
    "Layer 3 Up": 6, "Layer 3 Down": 7,
    "Repositioning": 8, "End": 9,
    "end": 9,  # 소문자 변형 대응
}

# unworn 실험 번호 (정상 패턴 학습용) — train.csv 기준
UNWORN_EXPERIMENTS = [1, 2, 3, 4, 5, 11, 12, 17]
# worn 실험: [6, 7, 8, 9, 10, 13, 14, 15, 16, 18]

# 중단(aborted) 실험 — unworn이지만 CLAMP_PRESSURE로 비정상 중단
ABORTED_UNWORN = [4, 5]
# 학습에서 제외하면 "순수 정상"만 학습 가능 (exclude_aborted=True)


class AnomalyDetector:
    """Isolation Forest 기반 이상탐지기"""

    def __init__(
        self,
        contamination: float = None,
        n_estimators: int = None,
        random_state: int = 42,
    ):
        from app.config import settings as _s
        _cont = contamination if contamination is not None else _s.IF_CONTAMINATION
        _nest = n_estimators if n_estimators is not None else _s.IF_N_ESTIMATORS
        self.model = IsolationForest(
            contamination=_cont,
            n_estimators=_nest,
            random_state=random_state,
            n_jobs=-1,
        )
        self.scaler = MinMaxScaler()
        self.is_fitted = False
        self.feature_columns = [c for c in FEATURE_COLUMNS if c != "Machining_Process"]
        # stream 모드용: fit 시 score 범위 저장
        self.score_min: float = 0.0
        self.score_max: float = 1.0

    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """DataFrame → 모델 입력 배열로 변환

        1. 피처 선택 (10개)
        2. Machining_Process 수치 변환
        3. MinMaxScaler 정규화
        """
        df_feat = df.copy()

        # Machining_Process → 수치 변환
        if "Machining_Process" in df_feat.columns:
            df_feat["machining_process_num"] = df_feat["Machining_Process"].map(PROCESS_MAP).fillna(0)
        elif "machining_process" in df_feat.columns:
            df_feat["machining_process_num"] = df_feat["machining_process"].map(PROCESS_MAP).fillna(0)
        else:
            df_feat["machining_process_num"] = 0

        # 피처 선택 (CSV 원본 CamelCase / DB snake_case 모두 대응)
        use_cols = []
        for col in self.feature_columns:
            if col in df_feat.columns:
                use_cols.append(col)
            elif col.lower() in df_feat.columns:
                df_feat[col] = df_feat[col.lower()]
                use_cols.append(col)
            elif to_snake(col) in df_feat.columns:
                # PascalCase → snake_case 변환 (DB 컬럼명 대응)
                df_feat[col] = df_feat[to_snake(col)]
                use_cols.append(col)

        use_cols.append("machining_process_num")

        # 파생 피처 계산
        def _get(name):
            if name in df_feat.columns: return df_feat[name]
            if name.lower() in df_feat.columns: return df_feat[name.lower()]
            if to_snake(name) in df_feat.columns: return df_feat[to_snake(name)]
            return None

        x_pos = _get("X1_ActualPosition")
        x_cmd = _get("X1_CommandPosition")
        if x_pos is not None and x_cmd is not None:
            df_feat["x_position_deviation"] = (x_pos - x_cmd).abs()
            use_cols.append("x_position_deviation")

        x_pow = _get("X1_OutputPower")
        s_pow = _get("S1_OutputPower")
        if x_pow is not None and s_pow is not None:
            df_feat["x_power_ratio"] = x_pow / (s_pow + 1e-8)
            use_cols.append("x_power_ratio")

        X = df_feat[use_cols].values.astype(np.float64)

        # NaN 처리 (forward fill → 0)
        X = pd.DataFrame(X).ffill().fillna(0).values

        return X

    def fit(self, df: pd.DataFrame):
        """unworn 실험 데이터로 정상 패턴 학습

        Args:
            df: unworn 실험 DataFrame (원본 컬럼명)
        """
        logger.info(f"=== F2 학습 시작 ({len(df)}행) ===")

        X = self._prepare_features(df)

        # 정규화 (unworn 기준으로 fit)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        # Isolation Forest 학습
        self.model.fit(X_scaled)
        self.is_fitted = True

        # 학습 데이터의 score 범위 저장 (stream 모드에서 정규화 기준으로 사용)
        train_scores = self.model.score_samples(X_scaled)
        self.score_min = float(train_scores.min())
        self.score_max = float(train_scores.max())

        logger.info(f"학습 완료: {X_scaled.shape[0]}행 × {X_scaled.shape[1]}피처")
        logger.info(f"학습 score 범위: [{self.score_min:.4f}, {self.score_max:.4f}]")

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """전체 데이터에 이상 점수 산출

        Returns:
            DataFrame with columns: anomaly_score, is_anomaly, predicted_failure_code
        """
        if not self.is_fitted:
            raise RuntimeError("모델이 학습되지 않았습니다. fit()을 먼저 호출하세요.")

        X = self._prepare_features(df)
        X_scaled = self.scaler.transform(X)

        # IF의 score_samples: 값이 낮을수록 이상 (음수)
        raw_scores = self.model.score_samples(X_scaled)

        # 0~1 범위로 변환 (낮은 점수 = 이상 → 높은 anomaly_score)
        # fit 시점의 score 범위를 기준으로 정규화 (stream 1행에서도 안정적)
        score_range = self.score_max - self.score_min
        if score_range > 0:
            anomaly_scores = 1 - (raw_scores - self.score_min) / score_range
            # 범위 밖 값 클리핑 (0~1)
            anomaly_scores = np.clip(anomaly_scores, 0.0, 1.0)
        else:
            anomaly_scores = np.zeros_like(raw_scores)

        # 임계치 적용
        threshold = settings.ANOMALY_THRESHOLD
        is_anomaly = anomaly_scores >= threshold

        # 고장코드 예측 (규칙 기반)
        failure_codes = self._classify_failure(df, anomaly_scores, is_anomaly)

        result = pd.DataFrame({
            "anomaly_score": np.round(anomaly_scores, 4),
            "is_anomaly": is_anomaly,
            "predicted_failure_code": failure_codes,
        })

        n_anomaly = is_anomaly.sum()
        logger.info(f"예측 완료: {len(df)}행 중 {n_anomaly}건 이상 ({n_anomaly/len(df)*100:.1f}%)")

        return result

    def _classify_failure(
        self,
        df: pd.DataFrame,
        scores: np.ndarray,
        is_anomaly: np.ndarray,
    ) -> list[Optional[str]]:
        """이상 감지된 행의 고장코드 분류 (규칙 기반)

        EDA 패턴 기반:
        - S1 전류 상승 + 고속 → SPINDLE_OVERHEAT_001
        - X1 전류 하락 → TOOL_WEAR_001
        - 위치 편차 급변 → CLAMP_PRESSURE_001
        - 기타 → COOLANT_LOW_001 (기본)
        """
        codes: list[Optional[str]] = [None] * len(df)

        # 컬럼명 대소문자 대응
        def get_col(name):
            if name in df.columns:
                return df[name]
            if name.lower() in df.columns:
                return df[name.lower()]
            return None

        x1_current = get_col("X1_CurrentFeedback")
        s1_current = get_col("S1_CurrentFeedback")
        feedrate = get_col("M1_CURRENT_FEEDRATE")
        x1_actual_pos = get_col("X1_ActualPosition")
        x1_command_pos = get_col("X1_CommandPosition")

        for i in range(len(df)):
            if not is_anomaly[i]:
                continue

            # 규칙 1: S1 전류 높고 고속 → 스핀들 과열
            if (s1_current is not None and feedrate is not None
                    and s1_current.iloc[i] > s1_current.median() * settings.SPINDLE_CURRENT_RATIO
                    and feedrate.iloc[i] >= settings.SPINDLE_FEEDRATE_MIN):
                codes[i] = "SPINDLE_OVERHEAT_001"

            # 규칙 2: X1 전류 낮음 → 공구 마모
            elif (x1_current is not None
                    and x1_current.iloc[i] < x1_current.median() * settings.TOOL_WEAR_RATIO):
                codes[i] = "TOOL_WEAR_001"

            # 규칙 3: 위치 편차 급변 → 클램프 압력 이상
            elif (x1_actual_pos is not None and x1_command_pos is not None
                    and abs(x1_actual_pos.iloc[i] - x1_command_pos.iloc[i]) > settings.CLAMP_POSITION_THRESHOLD):
                codes[i] = "CLAMP_PRESSURE_001"

            # 규칙 4: 기본 → 냉각수 부족 (간접 감지)
            else:
                codes[i] = "COOLANT_LOW_001"

        return codes

    def save(self, path: str = "models/f2_detector.pkl"):
        """학습된 모델 저장 (모델 + 스케일러 + score 범위)"""
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "scaler": self.scaler,
                "score_min": self.score_min,
                "score_max": self.score_max,
            }, f)
        logger.info(f"모델 저장: {save_path}")

    def load(self, path: str = "models/f2_detector.pkl"):
        """저장된 모델 로드"""
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.score_min = data.get("score_min", 0.0)
        self.score_max = data.get("score_max", 1.0)
        self.is_fitted = True
        logger.info(f"모델 로드: {path} (score 범위: [{self.score_min:.4f}, {self.score_max:.4f}])")


def train_and_evaluate(data_dir: str):
    """학습 + 검증 한 번에 실행 (CLI용)

    1. unworn 실험으로 학습
    2. 전체 18실험에 예측
    3. worn vs unworn 분포 비교
    4. 중단 실험 감지율 확인
    """
    from app.services.simulator import load_experiment_csv

    logger.info("=== F2 이상탐지 학습 + 검증 시작 ===")

    # 데이터 로드
    df = load_experiment_csv(data_dir)

    # 실험 번호 추출 (equipment_id + 순서로 유추)
    # CSV에 experiment_id가 없으므로, 파일별로 로드해야 정확
    data_path = Path(data_dir) / "kaggle-cnc-mill"
    unworn_dfs = []
    all_dfs = []
    exp_labels = []

    exclude_aborted = True  # 중단 실험(exp04, 05)을 학습에서 제외
    for i in range(1, 19):
        csv_file = data_path / f"experiment_{i:02d}.csv"
        if not csv_file.exists():
            continue
        exp_df = pd.read_csv(csv_file)
        exp_df["experiment_id"] = i
        all_dfs.append(exp_df)
        if i in UNWORN_EXPERIMENTS:
            if exclude_aborted and i in ABORTED_UNWORN:
                logger.info(f"  exp{i:02d} (unworn+중단) — 학습에서 제외")
                continue
            unworn_dfs.append(exp_df)

    df_unworn = pd.concat(unworn_dfs, ignore_index=True)
    df_all = pd.concat(all_dfs, ignore_index=True)

    logger.info(f"unworn: {len(df_unworn)}행 ({len(unworn_dfs)}실험)")
    logger.info(f"전체: {len(df_all)}행 (18실험)")

    # 학습
    detector = AnomalyDetector()
    detector.fit(df_unworn)

    # 예측
    results = detector.predict(df_all)
    df_all["anomaly_score"] = results["anomaly_score"].values
    df_all["is_anomaly"] = results["is_anomaly"].values
    df_all["predicted_failure_code"] = results["predicted_failure_code"].values

    # 검증: 실험별 평균 이상 점수
    logger.info("\n=== 실험별 평균 이상 점수 ===")
    exp_summary = df_all.groupby("experiment_id").agg(
        mean_score=("anomaly_score", "mean"),
        max_score=("anomaly_score", "max"),
        anomaly_pct=("is_anomaly", "mean"),
        rows=("anomaly_score", "count"),
    ).round(3)

    # worn/unworn 라벨 (train.csv 기준)
    worn_exps = [6, 7, 8, 9, 10, 13, 14, 15, 16, 18]
    exp_summary["label"] = ["worn" if i in worn_exps else "unworn" for i in exp_summary.index]

    # 중단 실험
    aborted_exps = [4, 5, 7, 16]
    exp_summary["aborted"] = [i in aborted_exps for i in exp_summary.index]

    for idx, row in exp_summary.iterrows():
        marker = "🔴" if row["label"] == "worn" else "🟢"
        abort = " [중단]" if row["aborted"] else ""
        logger.info(
            f"  {marker} exp{idx:02d} ({row['label']}{abort}): "
            f"mean={row['mean_score']:.3f}, max={row['max_score']:.3f}, "
            f"이상비율={row['anomaly_pct']*100:.1f}%"
        )

    # 분포 분리도
    worn_scores = exp_summary[exp_summary["label"] == "worn"]["mean_score"]
    unworn_scores = exp_summary[exp_summary["label"] == "unworn"]["mean_score"]
    logger.info(f"\n=== 분포 분리도 ===")
    logger.info(f"  worn 평균:   {worn_scores.mean():.3f}")
    logger.info(f"  unworn 평균: {unworn_scores.mean():.3f}")
    logger.info(f"  차이:        {worn_scores.mean() - unworn_scores.mean():.3f}")

    # 중단 실험 감지율
    aborted_anomaly = exp_summary[exp_summary["aborted"]]["anomaly_pct"]
    logger.info(f"\n=== 중단 실험 감지율 ===")
    for idx in aborted_exps:
        if idx in exp_summary.index:
            row = exp_summary.loc[idx]
            logger.info(f"  exp{idx:02d}: 이상비율 {row['anomaly_pct']*100:.1f}%")

    # 모델 저장
    detector.save()
    logger.info("\n=== F2 학습 + 검증 완료 ===")

    return detector, exp_summary
