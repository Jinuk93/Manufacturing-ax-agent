"""
EDA 대시보드용 JSON 요약 데이터 생성
CSV 원본 → 차트에 필요한 최소 데이터만 추출
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
data_dir = project_root / "data" / "raw" / "kaggle-cnc-mill"
out_path = project_root / "dashboards" / "eda_data.json"

# ─── 데이터 로딩 ───
train_df = pd.read_csv(data_dir / "train.csv")
train_df = train_df.rename(columns={"No": "experiment_no"})
train_df["experiment_id"] = train_df["experiment_no"].map(lambda v: f"experiment_{v:02d}")
train_df["equipment_id"] = train_df["experiment_no"].map(lambda v: f"CNC-{v:03d}")

all_experiments = []
for path in sorted(data_dir.glob("experiment_*.csv")):
    exp_id = path.stem
    exp_no = int(exp_id.split("_")[-1])
    df = pd.read_csv(path)
    df["experiment_id"] = exp_id
    df["experiment_no"] = exp_no
    df["sequence"] = range(len(df))
    row = train_df[train_df["experiment_no"] == exp_no]
    if not row.empty:
        df["tool_condition"] = row.iloc[0]["tool_condition"]
        df["Machining_Process"] = df.get("Machining_Process", "unknown")
    all_experiments.append(df)

full_df = pd.concat(all_experiments, ignore_index=True)

meta_cols = ["experiment_id", "experiment_no", "sequence",
             "Machining_Process", "tool_condition", "material",
             "feedrate", "clamp_pressure"]

constant_cols = [
    c for c in full_df.columns
    if full_df[c].nunique(dropna=False) == 1
    and c not in meta_cols
]
zero_cols = [
    c for c in full_df.select_dtypes(include=[np.number]).columns
    if full_df[c].fillna(0).eq(0).all()
]
sensor_cols = [c for c in full_df.columns if c not in meta_cols and c not in constant_cols]

# ─── 센서 그룹 ───
sensor_groups = {}
for col in sensor_cols:
    if col.startswith("X1_"): sensor_groups.setdefault("X축", []).append(col)
    elif col.startswith("Y1_"): sensor_groups.setdefault("Y축", []).append(col)
    elif col.startswith("Z1_"): sensor_groups.setdefault("Z축", []).append(col)
    elif col.startswith("S1_"): sensor_groups.setdefault("S축", []).append(col)
    elif col.startswith("M1_"): sensor_groups.setdefault("M1", []).append(col)

result = {}

# ─── 1. 데이터 개요 KPI ───
result["kpi"] = {
    "total_experiments": int(train_df.shape[0]),
    "total_rows": int(full_df.shape[0]),
    "total_columns": int(full_df.shape[1] - len(meta_cols)),
    "valid_sensors": len(sensor_cols),
    "removed_columns": len(constant_cols),
}

# 실험 메타 테이블
result["experiments"] = []
for _, r in train_df.iterrows():
    exp_data = full_df[full_df["experiment_id"] == r["experiment_id"]]
    result["experiments"].append({
        "id": r["experiment_id"],
        "equipment": r["equipment_id"],
        "material": r["material"],
        "feedrate": float(r["feedrate"]),
        "clamp_pressure": float(r["clamp_pressure"]),
        "tool_condition": r["tool_condition"],
        "rows": int(len(exp_data)),
        "finalized": r.get("machining_finalized", "yes"),
        "visual_inspection": str(r.get("passed_visual_inspection", "N/A")),
    })

# 공구 상태 분포
result["label_dist"] = {
    "worn": int((train_df["tool_condition"] == "worn").sum()),
    "unworn": int((train_df["tool_condition"] == "unworn").sum()),
}

# 센서 그룹 정보
result["sensor_groups"] = sensor_groups

# 제거 대상 컬럼
result["removed_cols"] = []
for c in constant_cols:
    val = full_df[c].iloc[0] if len(full_df) > 0 else None
    result["removed_cols"].append({
        "col": c,
        "reason": "전체 0값" if c in zero_cols else f"상수 ({val})",
    })

# ─── 2. 센서 분포 통계 ───
result["sensor_stats"] = {}
for group, cols in sensor_groups.items():
    group_stats = []
    for col in cols:
        s = full_df[col].describe()
        skew = float(full_df[col].skew())
        group_stats.append({
            "col": col,
            "mean": round(float(s["mean"]), 4),
            "std": round(float(s["std"]), 4),
            "min": round(float(s["min"]), 4),
            "q25": round(float(s["25%"]), 4),
            "median": round(float(s["50%"]), 4),
            "q75": round(float(s["75%"]), 4),
            "max": round(float(s["max"]), 4),
            "skew": round(skew, 3),
            "missing": int(full_df[col].isnull().sum()),
        })
    result["sensor_stats"][group] = group_stats

# Box plot 데이터 (5-number summary per sensor per group)
result["box_data"] = {}
for group, cols in sensor_groups.items():
    box_list = []
    for col in cols:
        s = full_df[col].dropna()
        q1, med, q3 = float(s.quantile(0.25)), float(s.quantile(0.5)), float(s.quantile(0.75))
        iqr = q3 - q1
        lower = float(max(s.min(), q1 - 1.5 * iqr))
        upper = float(min(s.max(), q3 + 1.5 * iqr))
        box_list.append({"col": col, "min": lower, "q1": q1, "median": med, "q3": q3, "max": upper})
    result["box_data"][group] = box_list

# ─── 3. 시계열 패턴 (샘플링) ───
# 각 실험에서 대표 센서 4개의 시계열을 100포인트로 다운샘플
representative_sensors = ["X1_ActualPosition", "X1_CurrentFeedback", "S1_OutputPower", "Z1_ActualPosition"]
representative_sensors = [s for s in representative_sensors if s in sensor_cols]

result["timeseries"] = {}
for exp_id in sorted(full_df["experiment_id"].unique()):
    exp_data = full_df[full_df["experiment_id"] == exp_id]
    n = len(exp_data)
    # 최대 200포인트로 다운샘플
    step = max(1, n // 200)
    sampled = exp_data.iloc[::step]
    ts = {"sequence": sampled["sequence"].tolist()}
    for sensor in representative_sensors:
        ts[sensor] = [round(float(v), 4) if pd.notna(v) else None for v in sampled[sensor]]
    if "Machining_Process" in sampled.columns:
        ts["process"] = sampled["Machining_Process"].tolist()
    result["timeseries"][exp_id] = ts

# ─── 4. Worn vs Unworn 비교 ───
worn_df = full_df[full_df["tool_condition"] == "worn"]
unworn_df = full_df[full_df["tool_condition"] == "unworn"]

result["worn_comparison"] = {}
for group, cols in sensor_groups.items():
    comp_list = []
    for col in cols:
        w_mean = float(worn_df[col].mean())
        u_mean = float(unworn_df[col].mean())
        diff_pct = (w_mean - u_mean) / (abs(u_mean) + 1e-10) * 100
        w_std = float(worn_df[col].std())
        u_std = float(unworn_df[col].std())

        # Box data per condition
        worn_s = worn_df[col].dropna()
        unworn_s = unworn_df[col].dropna()
        def box5(s):
            q1, med, q3 = float(s.quantile(0.25)), float(s.quantile(0.5)), float(s.quantile(0.75))
            iqr = q3 - q1
            return {"min": round(max(float(s.min()), q1-1.5*iqr), 4), "q1": round(q1, 4),
                    "median": round(med, 4), "q3": round(q3, 4), "max": round(min(float(s.max()), q3+1.5*iqr), 4)}

        comp_list.append({
            "col": col,
            "unworn_mean": round(u_mean, 4), "worn_mean": round(w_mean, 4),
            "diff_pct": round(diff_pct, 2),
            "unworn_std": round(u_std, 4), "worn_std": round(w_std, 4),
            "std_ratio": round(w_std / (u_std + 1e-10), 3),
            "worn_box": box5(worn_s), "unworn_box": box5(unworn_s),
        })
    result["worn_comparison"][group] = comp_list

# Worn vs Unworn 시계열 오버레이 (가장 긴 worn/unworn 실험)
worn_exp = full_df[full_df["tool_condition"]=="worn"].groupby("experiment_id").size().idxmax()
unworn_exp = full_df[full_df["tool_condition"]=="unworn"].groupby("experiment_id").size().idxmax()
result["worn_overlay"] = {"worn_exp": worn_exp, "unworn_exp": unworn_exp}

# ─── 5. 상관관계 ───
# 축 그룹별 상관행렬
result["correlations"] = {}
for group, cols in sensor_groups.items():
    if len(cols) < 2:
        continue
    corr = full_df[cols].corr()
    # 강한 상관 (|r| > 0.8) 쌍 추출
    strong = []
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            r = float(corr.iloc[i, j])
            if abs(r) > 0.8:
                strong.append({"a": cols[i], "b": cols[j], "r": round(r, 3)})
    # 히트맵 데이터
    result["correlations"][group] = {
        "cols": cols,
        "matrix": [[round(float(corr.iloc[i, j]), 3) for j in range(len(cols))] for i in range(len(cols))],
        "strong_pairs": sorted(strong, key=lambda x: abs(x["r"]), reverse=True),
    }

# ─── 6. 공정 단계 ───
process_counts = full_df["Machining_Process"].value_counts()
result["process"] = {
    "counts": {k: int(v) for k, v in process_counts.items()},
    "total": int(len(full_df)),
}

# 공정별 대표 센서 평균
proc_sensor = "S1_OutputPower"  # 스핀들 전력이 가장 직관적
if proc_sensor in sensor_cols:
    proc_stats = full_df.groupby("Machining_Process")[proc_sensor].agg(["mean", "std"]).reset_index()
    result["process"]["sensor_by_process"] = {
        "sensor": proc_sensor,
        "data": [{"process": r["Machining_Process"], "mean": round(float(r["mean"]), 4), "std": round(float(r["std"]), 4)}
                 for _, r in proc_stats.iterrows()],
    }

    # 공정별 worn/unworn 비교
    proc_cond = full_df.groupby(["Machining_Process", "tool_condition"])[proc_sensor].mean().reset_index()
    result["process"]["worn_by_process"] = [
        {"process": r["Machining_Process"], "condition": r["tool_condition"], "mean": round(float(r[proc_sensor]), 4)}
        for _, r in proc_cond.iterrows()
    ]

# ─── JSON 저장 ───
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=None)

print(f"JSON 생성 완료: {out_path}")
print(f"파일 크기: {out_path.stat().st_size / 1024:.1f} KB")
print(f"실험 수: {len(result['experiments'])}")
print(f"유효 센서: {result['kpi']['valid_sensors']}")
print(f"시계열 실험: {len(result['timeseries'])}")
