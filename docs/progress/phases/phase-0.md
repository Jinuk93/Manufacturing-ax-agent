# Phase 0: Project Definition — 일일 로그

> Phase 0의 목표: 프로젝트 범위 확정, 데이터 전략 수립, 핵심 기술 의사결정

---

## 2026-03-08 (Day 1)

**목표:** 프로젝트 정의 및 핵심 의사결정

### 진행 내용

- PRD v1.0 작성 (제품 요구사항 정의서)
  - Problem → Solution → 6개 Feature Pipeline 정의
  - System Pipeline 구조 확정 (상시 레이어 + 독립 모듈 + 관제 자동화 흐름)
- 데이터셋 전략 초안 작성
  - 5종 데이터셋 정의 (KAMP 센서, MES, ERP, 온톨로지, 매뉴얼)
  - 기능별 필요 데이터 분류 (필수/중요/보강)
- 핵심 기술 의사결정 5건
  - ADR-000: CNC 단일 도메인 확정
  - ADR-001: Forecasting 기반 접근 확정
  - ADR-002: MES/ERP 합성 생성 확정
  - ADR-003: PostgreSQL 통합 DB 확정
  - ADR-004: 5초 폴링 방식 확정
- 미결사항(Open Items) 11건 정리

### 산출물

- [prd-v1.0.md](../../0-project-definition/prd-v1.0.md)
- [data-collection-strategy.md](../../0-project-definition/data-collection-strategy.md) (초안)
- [open-items.md](../../0-project-definition/open-items.md)

---

## 2026-03-09 (Day 2)

**목표:** 데이터 전략 고도화 및 설계 원칙 확립

### 진행 내용

- **data-collection-strategy.md 크로스 리뷰** (AI 피드백 교차 검토)
  - 6개 품질 이슈 식별 및 수정
    - 중복 섹션 통합 (§5/§3 병합, §8/§10 병합)
    - 연결 다이어그램 개선 (그리드 구조)
    - 누락 컬럼 추가 (MES end_time, ERP snapshot_time)
  - §10 전통적 데이터 맵 추가
    - 시스템별/설비별/연동/저장/운영흐름 표 5종
    - Mermaid 아키텍처 다이어그램

- **5번째 설계 원칙 추가: 내부 표준 형식(Canonical Model)**
  - 모든 파이프라인은 원본 데이터 형식이 아니라 내부 표준 형식 기준으로 설계
  - Phase 0에서는 원칙만 확정, 실제 스키마는 Phase 1-2에서 구체화
  - 향후 고객사 확장 시 Onboarding Layer 추가만으로 대응 가능

- **향후 제품화 비전 논의**
  - Palantir 스타일 고객 온보딩 전략 검토
  - 고객 데이터 → 자동 프로파일링 → 매핑 → 온톨로지 인스턴스 생성 흐름
  - MVP 아키텍처가 전면 수정 없이 확장 가능함을 확인
  - 비전 문서는 `docs/future/`에 분리 보관

- **ADR-005: 대시보드 MVP 앞당김 결정**
  - 파이프라인 완성 전에도 시각적 결과물로 방향 검증

- **프로젝트 관리 구조 개선**
  - README.md에서 프로젝트 소개와 진행 관리 분리
  - `docs/progress/` 폴더 구조 생성

### 산출물

- [data-collection-strategy.md](../../0-project-definition/data-collection-strategy.md) (v2 - 대폭 보강)
- [customer-onboarding-ontology-strategy.md](../../future/customer-onboarding-ontology-strategy.md) (향후 비전)
- [docs/progress/](../) 폴더 구조

---

## 2026-03-10 (Day 3)

**목표:** 데이터셋 수집 완료 및 정합성 검증

### 진행 내용

- **외부 데이터셋 4종 다운로드 및 폴더 구조 정리**
  - `data/raw/kaggle-cnc-mill/` — Kaggle CNC Mill Tool Wear (48컬럼, 18실험, 100ms)
  - `data/raw/bosch-cnc/` — Bosch CNC Machining (HDF5, 진동 센서)
  - `data/raw/multi-sensor-cnc/` — Multi-Sensor CNC Tool Wear (2000행, 17컬럼)
  - `data/raw/milling-rul/` — Milling Tool Wear & RUL (1400행)
  - `data/raw/kamp/` — KAMP 제조AI 50종 카탈로그 (메타데이터)

- **.gitignore 생성** — `data/` 폴더 및 Python/IDE 임시 파일 제외

- **KAMP CSV 인코딩 수정** — CP949 → UTF-8 변환 (한국 공공데이터 인코딩 이슈)

- **required-data-summary.md에 F1~F6 데이터 매핑표 추가**
  - 기능별 데이터 확보 방식 요약
  - 기능별 필요 데이터셋 상세 매핑
  - 외부 데이터셋 출처 목록 (Kaggle, KAMP, Bosch 링크)

- **constraints.md에 프로젝트 범위 섹션 추가**
  - 데이터 수집 레이어(IoT/센서/프로토콜)는 범위 밖으로 명시
  - 분석/판단/관제 레이어(F1~F6)에 집중하는 이유 문서화

- **크로스 리뷰 반영 (4건 이슈)**
  - ZIP 파일 4개 삭제 (압축 해제 후 원본 정리)
  - KAMP: 카탈로그만 보유, 실제 센서 데이터는 Kaggle로 대체 — 문서 반영
  - Bosch: HDF5 포맷 확인 — EDA 시 h5py 필요 (메모)
  - milling-rul: RUL 컬럼은 ADR-001에 의해 미사용, 센서 패턴만 참고 — 문서 반영

### 산출물

- [.gitignore](../../../.gitignore)
- [required-data-summary.md](../../0-project-definition/required-data-summary.md) (F1~F6 매핑표 추가)
- [constraints.md](../constraints.md) (범위 섹션 추가)
- `data/raw/` 5개 폴더 (외부 데이터셋 4종 + KAMP 카탈로그)

- **데이터 갭 분석 + 크로스 검증 (3회 리뷰)**
  - 설계 원칙 1번(equipment_id + timestamp 기준 연결) vs 실제 데이터 대조
  - **발견:** 4개 데이터셋 모두 timestamp·equipment_id 없음 → Phase 1에서 합성 필요
  - **발견:** 주력 데이터셋(Kaggle Mill)에 진동·온도 센서 없음 → 전류·전력·속도 중심으로 F1/F2 설계
  - **발견:** Z축 전기 피드백 4컬럼 전 실험 0값, 상수 컬럼 2개 → 실질 유효 42컬럼
  - **발견:** Multi-Sensor, Milling-RUL은 합성 데이터 (균등/정규분포, 음수 마모량)
  - **발견:** 미완료 실험 4건은 "비정상 중단"이 아닌 "의도적으로 짧게 종료된 실험" (전부 End로 정상 종료)
  - open-items #1을 "KAMP 실체 확인" → "timestamp/equipment_id 합성 설계"로 업데이트
  - data-collection-strategy §2 표: "KAMP 공공 데이터" → "Kaggle CNC Mill" 수정
  - required-data-summary §3.1: 필수 센서 목록을 실제 확보 데이터 기준으로 전면 수정

### 다음 단계

- Phase 1(EDA) 진입: Kaggle CNC Mill 데이터 탐색적 분석 시작
- EDA 첫 번째 과제: timestamp 합성 규칙 + equipment_id 매핑 설계
- EDA 환경 세팅 (Python venv, Jupyter, pandas, h5py 등)

---

## Phase 0 완료 (2026-03-10)

Phase 0의 목표였던 **프로젝트 범위 확정, 데이터 전략 수립, 핵심 기술 의사결정**이 모두 완료되었습니다.

### 완료 산출물

| 산출물 | 문서 |
|--------|------|
| PRD v1.0 | [prd-v1.0.md](../../0-project-definition/prd-v1.0.md) |
| 데이터 수집 전략 | [data-collection-strategy.md](../../0-project-definition/data-collection-strategy.md) |
| 필요 데이터 정리표 | [required-data-summary.md](../../0-project-definition/required-data-summary.md) |
| 미결 사항 추적 (12건) | [open-items.md](../../0-project-definition/open-items.md) |
| ADR 6건 (ADR-000 ~ 005) | [adr-summary.md](../adr-summary.md) |
| 핵심 제약사항 + 범위 정의 | [constraints.md](../constraints.md) |
| 향후 제품화 비전 | [customer-onboarding-ontology-strategy.md](../../future/customer-onboarding-ontology-strategy.md) |
| 외부 데이터셋 4종 확보 | `data/raw/` (kaggle-cnc-mill, bosch-cnc, multi-sensor-cnc, milling-rul) |

### 핵심 의사결정 요약

- ADR-000: CNC 단일 도메인
- ADR-001: Forecasting 기반 (RUL 포기)
- ADR-002: MES/ERP 합성 생성
- ADR-003: PostgreSQL 통합 + Neo4j = 2개 DB
- ADR-004: 5초 폴링 방식
- ADR-005: 대시보드 MVP 앞당김

> Phase 1(Data Exploration)으로 이동합니다.
