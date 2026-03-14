# IT 데이터 합성 스키마

**상태:** 확정
**최종 수정일:** 2026-03-15
**근거:** ADR-002 (MES/ERP 합성), data-gap-analysis.md Phase 2 항목을 Phase 1에서 선행 처리

---

## 1. 개요

OT 데이터(센서 시계열)와 연결할 IT 데이터 3종을 합성합니다.
실제 MES/ERP가 없으므로 OT 데이터의 실험 메타데이터(train.csv)를 기반으로 현실적인 IT 데이터를 생성합니다.

**OT 데이터 범위:** 2024-01-15 ~ 2024-02-21 (약 5주, 18개 실험)

### 조인 키 다이어그램

```
OT (센서 시계열)
  │ equipment_id + timestamp
  ▼
MES (작업지시) ◄── work_order_id ──► Maintenance (정비 이벤트)
  │                                      │
  │                                      │ failure_code
  │                                      ▼
  │                                  failure_code taxonomy
  │                                      │
  │                                      │ parts_used (part_id)
  │                                      ▼
  └──────── equipment_id ──────────► ERP (부품 재고)
                                     │ part_id
                                     └── 재고 차감 반영
```

**핵심 흐름:** Maintenance 이벤트 발생 → failure_code로 원인 분류 → 사용 부품(part_id) 기록 → ERP 재고에서 차감 반영

---

## 2. failure_code 분류 체계

### 2.1 코드 정의

| failure_code | 설명 | 발생 조건 | 대응 부품 |
|---|---|---|---|
| TOOL_WEAR_001 | 점진적 엔드밀 마모 | worn + 정상 완료 실험 | P001 (엔드밀) |
| SPINDLE_OVERHEAT_001 | 스핀들 과열 | 중단 실험 중 고속(feedrate≥20) + worn | P002 (스핀들 베어링) |
| CLAMP_PRESSURE_001 | 클램프 압력 이상 | 중단 실험 중 clamp_pressure≤3 + unworn | P004 (클램프 볼트 세트) |
| COOLANT_LOW_001 | 냉각수 부족 (경미) | 예방 정비 | P003 (냉각수) |

### 2.2 실험별 매핑 (수동 확정)

조건 겹침을 방지하기 위해 중단 실험 4건은 수동으로 failure_code를 지정합니다.

| 실험 | tool_condition | finalized | feedrate | clamp_pressure | failure_code | 판정 근거 |
|---|---|---|---|---|---|---|
| 04 | unworn | no | 6 | 2.5 | CLAMP_PRESSURE_001 | unworn인데 중단 → 공구 문제 아님, 최저 clamp_pressure |
| 05 | unworn | no | 20 | 3 | CLAMP_PRESSURE_001 | unworn인데 중단 → 공구 문제 아님, 낮은 clamp_pressure |
| 07 | worn | no | 20 | 4 | SPINDLE_OVERHEAT_001 | worn + 고속 + 정상 clamp → 스핀들 과열 |
| 16 | worn | no | 20 | 3 | SPINDLE_OVERHEAT_001 | worn + 고속 → 스핀들 과열 |

정상 완료된 worn 실험 (06, 08, 09, 10, 13, 14, 15, 18): TOOL_WEAR_001 (사후 공구 교체)

---

## 3. 부품 목록 및 소비 규칙

### 3.1 부품 정의

| part_id | part_name | unit_cost | lead_time_days | reorder_point | initial_stock |
|---|---|---|---|---|---|
| P001 | Endmill 6mm Carbide | 45000 | 3 | 5 | 20 |
| P002 | Spindle Bearing Set | 280000 | 7 | 2 | 4 |
| P003 | Coolant (Water-Soluble, 20L) | 35000 | 2 | 3 | 10 |
| P004 | Clamp Bolt Set | 12000 | 1 | 4 | 15 |
| P005 | Air Filter | 8000 | 1 | 3 | 8 |

### 3.2 소비 규칙

| 규칙 | 내용 |
|---|---|
| P001 엔드밀 | TOOL_WEAR_001 이벤트에서만 소비 (점진 마모 후 교체). SPINDLE_OVERHEAT, CLAMP_PRESSURE에서는 소비하지 않음 |
| P002 스핀들 베어링 | SPINDLE_OVERHEAT_001에서 소비. 5주간 0~1회 교체가 현실적 (고가 부품). 실제로 2건(exp07, exp16) 중 1건만 교체 |
| P003 냉각수 | 모든 실험에서 소비 (중단 실험 포함). 주 1회 보충 이벤트 추가. **보충 = 창고 재고에서 기계 탱크로 이동이므로 ERP 관점에서는 "소비"** |
| P004 클램프 볼트 | CLAMP_PRESSURE_001에서만 소비 |
| P005 에어 필터 | 2주 주기 예방 정비에서 교체 |

---

## 4. MES 작업지시 스키마

**파일:** `data/processed/it-data/mes_work_orders.csv`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| work_order_id | string | WO-2024-001 ~ WO-2024-018 |
| equipment_id | string | CNC-001 ~ CNC-003 |
| experiment_id | int | 1~18 (OT 조인 키) |
| product_type | string | WAX_BLOCK_6MM |
| start_time | datetime | experiment_start (train.csv) |
| end_time | datetime | start_time + duration_sec |
| due_date | datetime | start_time + 작업 여유 시간 |
| priority | string | normal / urgent / critical |
| status | string | completed / aborted |

### 우선순위 규칙

| priority | 조건 | due_date 여유 |
|---|---|---|
| normal | 기본 | start_time + 8시간 |
| urgent | worn + feedrate ≥ 15 | start_time + 4시간 |
| critical | 중단 실험 (finalized=no) | start_time + 2시간 |

---

## 5. Maintenance 정비 이벤트 스키마

**파일:** `data/processed/it-data/maintenance_events.csv`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| event_id | string | MT-2024-001 ~ |
| equipment_id | string | CNC-001 ~ CNC-003 |
| event_type | string | corrective / preventive |
| timestamp | datetime | 실험 종료 후 30분~2시간 |
| failure_code | string | 섹션 2 참고 |
| description | string | 정비 내용 |
| duration_min | int | 정비 소요 시간 |
| technician_id | string | TECH-01 ~ TECH-03 |
| parts_used | string | part_id (쉼표 구분) |
| work_order_id | string | 연결된 작업지시 (있는 경우) |

### 이벤트 생성 규칙

| 이벤트 유형 | 트리거 | duration_min | parts_used |
|---|---|---|---|
| 중단 → 긴급 정비 | finalized=no | 60~120 | failure_code에 따라 |
| 마모 → 사후 교체 | worn + finalized=yes | 30~60 | P001 |
| 냉각수 보충 | 매주 금요일 | 15 | P003 |
| 에어 필터 교체 | 2주 주기 | 20 | P005 |

---

## 6. ERP 부품 재고 스냅샷 스키마

**파일:** `data/processed/it-data/erp_inventory_snapshots.csv`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| snapshot_date | date | 매주 월요일 |
| part_id | string | P001 ~ P005 |
| part_name | string | 부품명 |
| stock_quantity | int | 현재 재고 |
| reorder_point | int | 재주문 기준점 |
| lead_time_days | int | 조달 리드타임 |
| unit_cost | int | 단가 (원) |
| weekly_consumption | int | 해당 주 소비량 |
| reorder_triggered | bool | 재주문 발생 여부 |

### 스냅샷 날짜 (월요일 기준, OT 범위에 맞춤)

| 주차 | snapshot_date | OT 실험 범위 |
|---|---|---|
| W1 | 2024-01-15 (월) | exp 01~03 |
| W2 | 2024-01-22 (월) | exp 04~05 |
| W3 | 2024-01-29 (월) | exp 06~08 |
| W4 | 2024-02-05 (월) | exp 09~10 |
| W5 | 2024-02-12 (월) | exp 11~14 |
| W6 | 2024-02-19 (월) | exp 15~18 |
| W7 | 2024-02-26 (월) | (마감 스냅샷) |

**참고:** 2024-01-15이 월요일이므로 OT 시작일과 자연스럽게 정렬됩니다.

---

## 7. 관련 문서

- [data-gap-analysis.md](data-gap-analysis.md) — 데이터 갭 분석 (IT 데이터 항목)
- [ADR-002](../adr/adr-002-mes-erp-synthetic.md) — MES/ERP 합성 데이터 결정
- [outlier-analysis.md](outlier-analysis.md) — OT 데이터 이상치 분석
