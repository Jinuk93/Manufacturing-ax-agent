# Phase 1: Data Exploration — 일일 로그

> Phase 1의 목표: EDA를 통한 데이터 이해, 전처리 규칙 확정, 유효 컬럼 검증

---

## 2026-03-14 (Day 4)

**목표:** 대시보드 고도화 및 인터랙티브 EDA 구축

### 진행 내용

- **대시보드 구조 개편**
  - 한눈에 보기(p0)에서 애자일/Phase 페이지 분리
  - 데이터 전략 페이지에 다크 테마 적용
  - CodeRabbit 리뷰 반영 (문서 정합성, 노트북 정리)

- **인터랙티브 EDA 대시보드 구축** (`data-review.html` p11 페이지)
  - Plotly.js 기반 6개 탭: 데이터 개요, 분포, 시계열, Worn 비교, 상관관계, 공정별
  - Python CSV → JSON 요약 데이터 생성 (`scripts/generate_eda_json.py`)
  - JSON + JS 주입 스크립트 (`scripts/inject_eda_js.py`)
  - 처음 기존 페이지에 삽입 → 별도 페이지(p11 "데이터 탐색")로 분리
  - 네비게이션 data-idx 12페이지 체계로 재매핑

- **EDA 개요 탭 교육적 콘텐츠로 전면 재작성**
  - 데이터 출처 → 실험 구조 → 센서 그룹 → 축간 관계 순 Top-down 설명
  - 실험별 메타데이터 테이블 (worn/unworn, finalized, visual inspection)

- **갭 분석 및 수정**
  - `passed_visual_inspection` 누락 발견 → JSON, 테이블, 설명에 추가
  - worn이지만 육안검사 통과한 실험(#13,#14,#15,#18) 패턴 문서화
  - `M1_CURRENT_PROGRAM_NUMBER` 값(0,1,4) 상세 설명 추가
  - M1 그룹(기계 레벨) 센서 설명 추가

### 산출물

- `data-review.html` — EDA 대시보드 (p11 페이지, 6개 탭)
- `dashboards/eda_data.json` — EDA 요약 데이터 (~214KB)
- `scripts/generate_eda_json.py` — CSV → JSON 생성기
- `scripts/inject_eda_js.py` — HTML 주입 스크립트
- `scripts/update_overview.py` — 개요 탭 업데이트
- `scripts/fix_overview_gap.py` — 갭 수정 스크립트

---

## 2026-03-15 (Day 5)

**목표:** 데이터 갭 분석 확정 및 데이터 정리/합성 시작

### 진행 내용

- **data-gap-analysis.md 검토 및 보완** (5건 수정)
  - `passed_visual_inspection` 행 추가 (OT 데이터 테이블)
  - KAMP를 섹션 1 보유 데이터 판정 테이블에 추가 (일관성)
  - Bosch 확장자 HDF5 → H5 수정 (실제 파일 확인)
  - 온도 센서 "대체 설계" → "Phase 1 EDA에서 검증 예정"으로 수정
  - "비즈니스 시나리오 S1~S4" → "IT/OT 합성 시나리오 (Phase 2 초기 정의 예정)"

- **불필요 데이터셋 삭제** (3종, 총 ~848KB)
  - `data/raw/multi-sensor-cnc/` — 합성 데이터 의심
  - `data/raw/milling-rul/` — ADR-001 RUL 포기로 용도 없음
  - `data/raw/kamp/` — 메타데이터만 보유
  - 남은 데이터: Kaggle CNC Mill (핵심, 12MB) + Bosch CNC (보조, 1.8GB)

- **timestamp 합성** (`scripts/synthesize_timestamp.py`)
  - 규칙: 100ms 샘플링, 기준일 2024-01-15, 08:00~09:00 시작, 1~3영업일 간격
  - 18개 실험 전체 처리: 25,286 데이터행 (헤더 제외), 2024-01-15 ~ 2024-02-21 (약 5주간)
  - 정상 실험: 105~233초 / 중단 실험: 46~60초 (행 수에서 자연 반영)
  - 원본(`data/raw/`) 보존, `data/processed/kaggle-cnc-mill/`에 출력
  - train.csv에 `experiment_start`, `experiment_duration_sec` 컬럼 추가

- **experiment_12 줄바꿈 이슈 발견 및 문서화**
  - raw 파일이 CR-only(`\r`) 줄바꿈 → `wc -l`이 0행으로 오인
  - 실제 2,276행 정상 데이터 존재 확인
  - processed에서는 CRLF로 통일됨
  - data-gap-analysis.md에 주의사항 메모 추가

### 산출물

- [data-gap-analysis.md](../../1-data-exploration/data-gap-analysis.md) — 보완 완료
- `scripts/synthesize_timestamp.py` — timestamp 합성 스크립트
- `data/processed/kaggle-cnc-mill/` — timestamp 추가된 18개 CSV + train.csv

### Phase 1 체크리스트

- [x] 불필요 데이터 삭제 (multi-sensor-cnc, milling-rul, kamp)
- [x] `timestamp` 합성 (data/processed/)
- [x] EDA 이상치 분석 — README 경고 3조건 전수 조사, 42유효컬럼 확정 (원본 48컬럼 유지 중, 5개 제거는 F1 전처리에서)
- [x] `equipment_id` 매핑 — 순번 기반 3대 분산 완료
- [x] Bosch CNC 데이터 탐색 완료 — 3축 가속도(2kHz), 3대 기계, 1,702 H5 파일, good/bad 라벨. Kaggle과 조인 불가(별도 독립 데이터셋). 보관 유지, Phase 2+ 활용 판단

#### equipment_id 분배 특성

| 설비 | unworn | worn | 중단 | feedrate | 해석 |
|------|--------|------|------|----------|------|
| CNC-001 (exp 01~06) | 5 | 1 | 2 (04,05) | {6, 20} | 신품 공구 중심, 중저속~고속 |
| CNC-002 (exp 07~12) | 2 | 4 | 1 (07) | {3, 12, 15, 20} | 마모 빈번, feedrate 다양 |
| CNC-003 (exp 13~18) | 1 | 5 | 1 (16) | {3, 6, 20} | 오래된 공구 위주, 저속 중심 |

편중은 의도적 — 실제 공장에서도 설비별 공구 교체 주기가 다르므로 현실적 시나리오임.

---
