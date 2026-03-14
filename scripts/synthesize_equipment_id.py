"""
equipment_id 합성 스크립트

기존 data/processed/kaggle-cnc-mill/ 파일에 equipment_id 컬럼을 추가합니다.

분배 규칙 (단순 순번, 편중 문서화):
  CNC-001: experiment 01~06 (unworn 5, worn 1) — 새 공구 위주
  CNC-002: experiment 07~12 (unworn 2, worn 4) — 마모 빈번
  CNC-003: experiment 13~18 (unworn 1, worn 5) — 오래된 공구 위주

설계 근거:
  - 실제 공장에서도 설비마다 공구 교체 주기가 다름
  - 편중 자체가 현실적 시나리오 (완벽 균등이 오히려 비현실적)
  - 과한 셔플링은 합성 데이터를 더 인공적으로 만듦
"""

import csv
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
processed_dir = project_root / "data" / "processed" / "kaggle-cnc-mill"

# 설비 매핑
EQUIPMENT_MAP = {
    1: "CNC-001", 2: "CNC-001", 3: "CNC-001",
    4: "CNC-001", 5: "CNC-001", 6: "CNC-001",
    7: "CNC-002", 8: "CNC-002", 9: "CNC-002",
    10: "CNC-002", 11: "CNC-002", 12: "CNC-002",
    13: "CNC-003", 14: "CNC-003", 15: "CNC-003",
    16: "CNC-003", 17: "CNC-003", 18: "CNC-003",
}

print("=" * 60)
print("equipment_id 합성 시작")
print("=" * 60)

# 각 실험 CSV에 equipment_id 추가
for i in range(1, 19):
    fp = processed_dir / ("experiment_%02d.csv" % i)
    eq_id = EQUIPMENT_MAP[i]

    with open(fp, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    header = reader[0]
    data_rows = reader[1:]

    # timestamp 다음(두 번째 컬럼)에 equipment_id 삽입
    new_header = [header[0], "equipment_id"] + header[1:]
    new_rows = [[row[0], eq_id] + row[1:] for row in data_rows]

    with open(fp, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(new_header)
        writer.writerows(new_rows)

    print("  experiment_%02d: %s (%d rows)" % (i, eq_id, len(data_rows)))

# train.csv에도 equipment_id 추가
train_fp = processed_dir / "train.csv"
with open(train_fp, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))

train_header = reader[0]
train_rows = reader[1:]

# No 다음(두 번째 컬럼)에 equipment_id 삽입
new_train_header = [train_header[0], "equipment_id"] + train_header[1:]
new_train_rows = []
for row in train_rows:
    exp_no = int(row[0])
    eq_id = EQUIPMENT_MAP[exp_no]
    new_train_rows.append([row[0], eq_id] + row[1:])

with open(train_fp, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(new_train_header)
    writer.writerows(new_train_rows)

# 결과 요약
print("\n" + "=" * 60)
print("완료!")
print("  CNC-001 (exp 01~06): unworn 5, worn 1")
print("  CNC-002 (exp 07~12): unworn 2, worn 4")
print("  CNC-003 (exp 13~18): unworn 1, worn 5")
print("=" * 60)
