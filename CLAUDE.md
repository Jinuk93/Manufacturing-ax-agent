# Manufacturing-ax-agent Project Rules

## Project Context
- CNC 제조 설비의 예지보전 + 온톨로지 기반 GraphRAG + LLM 자율 조치 에이전트 관제 시스템
- CNC 단일 도메인으로 통일한 이유: 다중 도메인(NASA 등) 혼합 시 데이터 조인 키 충돌 및 LLM 환각 발생 (ADR-000)
- 핵심 파이프라인: 센서 예측(F1~F2) → IT/OT 데이터 동기화(F3) → Neo4j 온톨로지 + GraphRAG(F4) → LLM 자율 판단(F5) → 대시보드(F6)
- 온톨로지는 '설비 → 고장코드 → 부품 → 매뉴얼' 관계를 Neo4j에 구축하여 정비 지식을 구조화
- 1인 개발, 입문자 수준 - 설명은 단계별로 친절하게
- 애자일 방식, 모든 의사결정을 문서화(ADR)하며 진행

## Documentation Rules
- ADR 문서에 AI 도구 이름(클로드, 제미나이, GPT 등) 사용 금지
- ADR은 "Option A / Option B → 선택 → 근거 → 제약사항" 구조로 작성
- 기간 제약 없음, 프로젝트 내용 중심으로 진행
- 문서 변경 시 README.md의 관련 표(ADR, Phase, Open Items)도 동기화

## Code Rules (Phase 2 이후 적용)
- Python: FastAPI 백엔드, 타입 힌트 사용
- 주석은 한국어로 작성
- 커밋 메시지는 영어로, 본문에 한국어 설명 가능
- Docker Compose로 통합 실행 환경 유지

## Git Workflow Rules
- 의미 있는 작업은 기능별 브랜치로 분리하여 진행
- 브랜치 네이밍: `feature/기능명`, `docs/문서작업명`, `fix/수정내용`
  - 예시: `feature/data-collection`, `feature/eda-setup`, `feature/dashboard-mvp`, `docs/phase0-cleanup`
- `main`에는 직접 작업하지 않고, 작업 브랜치에서 커밋 후 push
- 변경사항을 반영할 때는 가능하면 PR(Pull Request)을 생성하여 검토 후 merge
- PR 생성 후 CodeRabbit 리뷰를 받아 변경 위험, 누락, 개선 포인트를 먼저 점검
- merge 완료된 브랜치는 삭제하여 브랜치 목록을 깔끔하게 유지
- 오타 수정 등 아주 작은 변경은 예외 가능하지만, 구조/기능/문서 체계 변경은 PR 흐름 우선

## Key Decisions (ADR Summary)
- ADR-000: CNC 단일 도메인 (NASA 배제)
- ADR-001: RUL 포기, Forecasting 방식
- ADR-002: MES/ERP 합성 데이터
- ADR-003: PostgreSQL 통합 (TimescaleDB + pgvector) + Neo4j 별도 = 총 2개 DB
- ADR-004: 5초 폴링 방식 (Kafka 미사용)
- ADR-005: 대시보드 MVP 앞당김

## File Structure
- docs/progress/             : 프로젝트 진행 관리 (overview, ADR 요약, constraints, Phase별 로그)
- docs/0-project-definition/ : PRD, 데이터 수집 전략, 미결사항
- docs/1-data-exploration/   : KAMP 데이터 EDA
- docs/2-architecture/       : 세부 파이프라인, DB 스키마
- docs/future/               : 향후 제품화/확장 비전
- docs/adr/                  : ADR 템플릿
