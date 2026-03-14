"""
IT 데이터 합성 스크립트

OT 데이터(train.csv)를 기반으로 IT 데이터 3종을 합성합니다:
  1. MES 작업지시 (mes_work_orders.csv)
  2. Maintenance 정비 이벤트 (maintenance_events.csv)
  3. ERP 부품 재고 스냅샷 (erp_inventory_snapshots.csv)

설계 근거: docs/1-data-exploration/it-data-synthesis-schema.md
ADR-002: MES/ERP 합성 데이터
"""

import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

project_root = Path(__file__).resolve().parent.parent
processed_dir = project_root / "data" / "processed" / "kaggle-cnc-mill"
output_dir = project_root / "data" / "processed" / "it-data"
output_dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# train.csv 읽기
# ============================================================
train_fp = processed_dir / "train.csv"
with open(train_fp, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    experiments = list(reader)

print("=" * 60)
print("IT data synthesis start")
print("=" * 60)
print("  Experiments loaded: %d" % len(experiments))

# ============================================================
# failure_code 매핑 (수동 확정)
# ============================================================
# 중단 실험 → 수동 매핑 (조건 겹침 방지)
ABORT_FAILURE = {
    4: "CLAMP_PRESSURE_001",   # unworn, clamp_pressure=2.5
    5: "CLAMP_PRESSURE_001",   # unworn, clamp_pressure=3
    7: "SPINDLE_OVERHEAT_001", # worn, feedrate=20
    16: "SPINDLE_OVERHEAT_001", # worn, feedrate=20
}

# 정상 완료 worn 실험 → TOOL_WEAR_001
WORN_COMPLETED = {6, 8, 9, 10, 13, 14, 15, 18}

def get_failure_code(exp_no, tool_condition, finalized):
    """실험별 failure_code 결정"""
    if finalized == "no":
        return ABORT_FAILURE.get(exp_no)
    if tool_condition == "worn":
        return "TOOL_WEAR_001"
    return None  # unworn + 정상 완료 → 정비 불필요

# ============================================================
# 부품 정의
# ============================================================
PARTS = {
    "P001": {"name": "Endmill 6mm Carbide", "cost": 45000, "lead_time": 3,
             "reorder_point": 5, "initial_stock": 20},
    "P002": {"name": "Spindle Bearing Set", "cost": 280000, "lead_time": 7,
             "reorder_point": 2, "initial_stock": 4},
    "P003": {"name": "Coolant Water-Soluble 20L", "cost": 35000, "lead_time": 2,
             "reorder_point": 3, "initial_stock": 10},
    "P004": {"name": "Clamp Bolt Set", "cost": 12000, "lead_time": 1,
             "reorder_point": 4, "initial_stock": 15},
    "P005": {"name": "Air Filter", "cost": 8000, "lead_time": 1,
             "reorder_point": 3, "initial_stock": 8},
}

# failure_code → 소비 부품
FAILURE_PARTS = {
    "TOOL_WEAR_001": ["P001"],
    "SPINDLE_OVERHEAT_001": ["P002"],
    "CLAMP_PRESSURE_001": ["P004"],
    "COOLANT_LOW_001": ["P003"],
}

# ============================================================
# 1. MES 작업지시 생성
# ============================================================
print("\n--- MES Work Orders ---")

mes_rows = []
for exp in experiments:
    exp_no = int(exp["No"])
    eq_id = exp["equipment_id"]
    start_time = datetime.fromisoformat(exp["experiment_start"])
    duration = float(exp["experiment_duration_sec"])
    end_time = start_time + timedelta(seconds=duration)
    finalized = exp["machining_finalized"]
    tool_cond = exp["tool_condition"]
    feedrate = int(exp["feedrate"])

    # 우선순위 결정
    if finalized == "no":
        priority = "critical"
        due_delta = timedelta(hours=2)
    elif tool_cond == "worn" and feedrate >= 15:
        priority = "urgent"
        due_delta = timedelta(hours=4)
    else:
        priority = "normal"
        due_delta = timedelta(hours=8)

    status = "completed" if finalized == "yes" else "aborted"
    due_date = start_time + due_delta

    mes_rows.append({
        "work_order_id": "WO-2024-%03d" % exp_no,
        "equipment_id": eq_id,
        "experiment_id": exp_no,
        "product_type": "WAX_BLOCK_6MM",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "due_date": due_date.isoformat(),
        "priority": priority,
        "status": status,
    })
    print("  WO-2024-%03d: %s %s %s" % (exp_no, eq_id, priority, status))

mes_fp = output_dir / "mes_work_orders.csv"
with open(mes_fp, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=mes_rows[0].keys())
    writer.writeheader()
    writer.writerows(mes_rows)

print("  -> %s (%d rows)" % (mes_fp.name, len(mes_rows)))

# ============================================================
# 2. Maintenance 정비 이벤트 생성
# ============================================================
print("\n--- Maintenance Events ---")

mt_rows = []
mt_counter = 1
technicians = ["TECH-01", "TECH-02", "TECH-03"]

# 각 부품의 소비 이력 추적 (ERP 재고 계산용)
parts_consumption = []  # (date, part_id, quantity)

# 2a. 실험 기반 정비 이벤트
for exp in experiments:
    exp_no = int(exp["No"])
    eq_id = exp["equipment_id"]
    start_time = datetime.fromisoformat(exp["experiment_start"])
    duration = float(exp["experiment_duration_sec"])
    end_time = start_time + timedelta(seconds=duration)
    finalized = exp["machining_finalized"]
    tool_cond = exp["tool_condition"]

    failure_code = get_failure_code(exp_no, tool_cond, finalized)
    if failure_code is None:
        # unworn 정상 완료 → 냉각수만 소비 기록
        parts_consumption.append((end_time.date(), "P003", 0.5))
        continue

    # 정비 시작: 실험 종료 후 30분~2시간
    mt_start = end_time + timedelta(minutes=random.randint(30, 120))

    if finalized == "no":
        event_type = "corrective"
        duration_min = random.randint(60, 120)
    else:
        event_type = "corrective"
        duration_min = random.randint(30, 60)

    used_parts = FAILURE_PARTS.get(failure_code, [])

    # 스핀들 베어링: 5주간 1건만 교체 (exp07에서 교체, exp16은 점검만)
    if failure_code == "SPINDLE_OVERHEAT_001" and exp_no == 16:
        used_parts = []  # 점검만, 부품 교체 없음
        desc = "Spindle overheat inspection, no bearing replacement needed"
    elif failure_code == "SPINDLE_OVERHEAT_001":
        desc = "Spindle bearing replacement due to overheat"
    elif failure_code == "TOOL_WEAR_001":
        desc = "Worn endmill replacement after machining"
    elif failure_code == "CLAMP_PRESSURE_001":
        desc = "Clamp bolt replacement due to pressure loss"
    else:
        desc = "Maintenance event"

    # 냉각수는 모든 실험에서 소비 (중단 포함)
    parts_consumption.append((end_time.date(), "P003", 0.5))

    # 사용 부품 소비 기록
    for pid in used_parts:
        parts_consumption.append((mt_start.date(), pid, 1))

    mt_rows.append({
        "event_id": "MT-2024-%03d" % mt_counter,
        "equipment_id": eq_id,
        "event_type": event_type,
        "timestamp": mt_start.isoformat(),
        "failure_code": failure_code,
        "description": desc,
        "duration_min": duration_min,
        "technician_id": random.choice(technicians),
        "parts_used": ",".join(used_parts) if used_parts else "",
        "work_order_id": "WO-2024-%03d" % exp_no,
    })
    mt_counter += 1

# 2b. 예방 정비: 냉각수 보충 (매주 금요일)
# OT 범위: 2024-01-15 ~ 2024-02-21
# 금요일: 1/19, 1/26, 2/2, 2/9, 2/16, 2/23
fridays = []
d = datetime(2024, 1, 19)  # 첫 금요일
while d <= datetime(2024, 2, 23):
    fridays.append(d)
    d += timedelta(weeks=1)

for friday in fridays:
    mt_time = friday.replace(hour=16, minute=0)
    for eq_id in ["CNC-001", "CNC-002", "CNC-003"]:
        mt_rows.append({
            "event_id": "MT-2024-%03d" % mt_counter,
            "equipment_id": eq_id,
            "event_type": "preventive",
            "timestamp": mt_time.isoformat(),
            "failure_code": "COOLANT_LOW_001",
            "description": "Weekly coolant refill",
            "duration_min": 15,
            "technician_id": "TECH-01",
            "parts_used": "P003",
            "work_order_id": "",
        })
        parts_consumption.append((friday.date(), "P003", 1))
        mt_counter += 1

# 2c. 예방 정비: 에어 필터 교체 (2주 주기)
# 1/26, 2/9, 2/23
filter_dates = [datetime(2024, 1, 26), datetime(2024, 2, 9), datetime(2024, 2, 23)]
for fd in filter_dates:
    mt_time = fd.replace(hour=17, minute=0)
    for eq_id in ["CNC-001", "CNC-002", "CNC-003"]:
        mt_rows.append({
            "event_id": "MT-2024-%03d" % mt_counter,
            "equipment_id": eq_id,
            "event_type": "preventive",
            "timestamp": mt_time.isoformat(),
            "failure_code": "",
            "description": "Bi-weekly air filter replacement",
            "duration_min": 20,
            "technician_id": "TECH-02",
            "parts_used": "P005",
            "work_order_id": "",
        })
        parts_consumption.append((fd.date(), "P005", 1))
        mt_counter += 1

# 시간순 정렬
mt_rows.sort(key=lambda x: x["timestamp"])

mt_fp = output_dir / "maintenance_events.csv"
with open(mt_fp, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=mt_rows[0].keys())
    writer.writeheader()
    writer.writerows(mt_rows)

print("  -> %s (%d rows)" % (mt_fp.name, len(mt_rows)))

# ============================================================
# 3. ERP 부품 재고 스냅샷 생성
# ============================================================
print("\n--- ERP Inventory Snapshots ---")

# 월요일 스냅샷 날짜
mondays = []
d = datetime(2024, 1, 15)
while d <= datetime(2024, 2, 26):
    mondays.append(d.date())
    d += timedelta(weeks=1)

# 주차별 소비량 집계
from collections import defaultdict
weekly_consumption = defaultdict(lambda: defaultdict(float))

for cons_date, part_id, qty in parts_consumption:
    # 해당 소비가 어느 주차에 속하는지 결정
    for i, monday in enumerate(mondays[:-1]):
        next_monday = mondays[i + 1]
        if monday <= cons_date < next_monday:
            weekly_consumption[monday][part_id] += qty
            break
    else:
        # 마지막 주
        if cons_date >= mondays[-1]:
            weekly_consumption[mondays[-1]][part_id] += qty

erp_rows = []
stock = {pid: info["initial_stock"] for pid, info in PARTS.items()}

for monday in mondays:
    week_cons = weekly_consumption.get(monday, {})

    for pid, info in PARTS.items():
        consumed = int(week_cons.get(pid, 0))
        stock[pid] = max(0, stock[pid] - consumed)
        reorder = stock[pid] <= info["reorder_point"]

        erp_rows.append({
            "snapshot_date": monday.isoformat(),
            "part_id": pid,
            "part_name": info["name"],
            "stock_quantity": stock[pid],
            "reorder_point": info["reorder_point"],
            "lead_time_days": info["lead_time"],
            "unit_cost": info["cost"],
            "weekly_consumption": consumed,
            "reorder_triggered": reorder,
        })

        # 재주문 발생 시 리드타임 후 재고 보충 (단순화: 다음 스냅샷에 반영)
        if reorder:
            stock[pid] += info["initial_stock"] // 2  # 초기 재고의 절반 보충

erp_fp = output_dir / "erp_inventory_snapshots.csv"
with open(erp_fp, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=erp_rows[0].keys())
    writer.writeheader()
    writer.writerows(erp_rows)

print("  -> %s (%d rows)" % (erp_fp.name, len(erp_rows)))

# ============================================================
# 결과 요약
# ============================================================
print("\n" + "=" * 60)
print("IT data synthesis complete!")
print("  MES work orders:        %d rows" % len(mes_rows))
print("  Maintenance events:     %d rows" % len(mt_rows))
print("  ERP inventory snapshots: %d rows" % len(erp_rows))
print("  Output: %s" % output_dir)
print("=" * 60)

# 검증: failure_code 분포
from collections import Counter
fc_counts = Counter(r["failure_code"] for r in mt_rows if r["failure_code"])
print("\nfailure_code distribution:")
for code, cnt in fc_counts.most_common():
    print("  %s: %d" % (code, cnt))

# 검증: 부품 최종 재고
print("\nFinal stock levels:")
for pid, info in PARTS.items():
    print("  %s (%s): %d" % (pid, info["name"], stock[pid]))
