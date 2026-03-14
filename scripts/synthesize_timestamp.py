"""
timestamp 합성 스크립트

원본 Kaggle CNC Mill 데이터에 timestamp 컬럼을 추가합니다.
- 샘플링 주기: 100ms (원본 명세)
- 기준일: 2024-01-15 (월요일)
- 시작 시각: 08:00~09:00 사이 랜덤
- 실험 간 간격: 1~3일 (주말 건너뜀)
- 출력: data/processed/kaggle-cnc-mill/

원본(data/raw/)은 변경하지 않습니다.
"""

import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# 재현 가능하도록 시드 고정
random.seed(42)

project_root = Path(__file__).resolve().parent.parent
raw_dir = project_root / "data" / "raw" / "kaggle-cnc-mill"
out_dir = project_root / "data" / "processed" / "kaggle-cnc-mill"
out_dir.mkdir(parents=True, exist_ok=True)

SAMPLING_MS = 100  # 100ms
NUM_EXPERIMENTS = 18
BASE_DATE = datetime(2024, 1, 15, 0, 0, 0)  # 월요일


def next_workday(dt, skip_days):
    """주말을 건너뛰며 skip_days만큼 이동"""
    current = dt
    days_added = 0
    while days_added < skip_days:
        current += timedelta(days=1)
        # 월(0)~금(4)만 카운트
        if current.weekday() < 5:
            days_added += 1
    return current


def random_start_time():
    """08:00~09:00 사이 랜덤 시각 생성"""
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    return timedelta(hours=8, minutes=minutes, seconds=seconds)


# 실험별 시작 날짜/시각 생성
experiment_starts = {}
current_date = BASE_DATE

for i in range(1, NUM_EXPERIMENTS + 1):
    start_dt = current_date + random_start_time()
    experiment_starts[i] = start_dt

    # 다음 실험까지 1~3 영업일 간격
    gap = random.randint(1, 3)
    current_date = next_workday(current_date, gap)


# 각 실험 CSV에 timestamp 추가
print("=" * 60)
print("timestamp 합성 시작")
print("=" * 60)

total_rows = 0

for i in range(1, NUM_EXPERIMENTS + 1):
    src = raw_dir / f"experiment_{i:02d}.csv"
    dst = out_dir / f"experiment_{i:02d}.csv"

    with open(src, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    if len(reader) <= 1:
        print(f"  experiment_{i:02d}: 헤더만 있거나 빈 파일 → 건너뜀")
        continue

    header = reader[0]
    data_rows = reader[1:]

    # timestamp를 첫 번째 컬럼으로 추가
    new_header = ["timestamp"] + header
    start_dt = experiment_starts[i]

    new_rows = []
    for idx, row in enumerate(data_rows):
        ts = start_dt + timedelta(milliseconds=idx * SAMPLING_MS)
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}"
        new_rows.append([ts_str] + row)

    with open(dst, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(new_header)
        writer.writerows(new_rows)

    duration = len(data_rows) * SAMPLING_MS / 1000
    end_dt = start_dt + timedelta(milliseconds=(len(data_rows) - 1) * SAMPLING_MS)
    total_rows += len(data_rows)

    print(f"  experiment_{i:02d}: {len(data_rows):>5}행 | "
          f"{start_dt.strftime('%Y-%m-%d %H:%M:%S')} ~ "
          f"{end_dt.strftime('%H:%M:%S')} | "
          f"{duration:.1f}초")

# train.csv도 복사 (실험별 시작시각 컬럼 추가)
src_train = raw_dir / "train.csv"
dst_train = out_dir / "train.csv"

with open(src_train, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))

train_header = reader[0]
train_rows = reader[1:]

new_train_header = train_header + ["experiment_start", "experiment_duration_sec"]
new_train_rows = []

for row in train_rows:
    exp_no = int(row[0])
    start_dt = experiment_starts[exp_no]

    # 해당 실험의 행 수로 duration 계산
    exp_src = raw_dir / f"experiment_{exp_no:02d}.csv"
    with open(exp_src, "r", encoding="utf-8") as f:
        exp_row_count = sum(1 for _ in f) - 1  # 헤더 제외

    duration = exp_row_count * SAMPLING_MS / 1000
    new_train_rows.append(
        row + [start_dt.strftime("%Y-%m-%dT%H:%M:%S"), f"{duration:.1f}"]
    )

with open(dst_train, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(new_train_header)
    writer.writerows(new_train_rows)

print(f"\n{'=' * 60}")
print(f"완료!")
print(f"  총 {total_rows:,}행 처리")
print(f"  기간: {experiment_starts[1].strftime('%Y-%m-%d')} ~ "
      f"{experiment_starts[NUM_EXPERIMENTS].strftime('%Y-%m-%d')}")
print(f"  출력: {out_dir}")
print(f"{'=' * 60}")
