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

- **data-collection-strategy.md 크로스 리뷰** (Claude + GPT 피드백 교차 검토)
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
