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

## Key Decisions (ADR Summary)
- ADR-000: CNC 단일 도메인 (NASA 배제)
- ADR-001: RUL 포기, Forecasting 방식
- ADR-002: MES/ERP 합성 데이터
- ADR-003: PostgreSQL 단일 DB (TimescaleDB + pgvector) + Neo4j
- ADR-004: 5초 폴링 방식 (Kafka 미사용)
- ADR-005: 대시보드 MVP 앞당김

## File Structure
- docs/0-project-definition/ : PRD, 데이터셋 전략, 미결사항
- docs/1-data-exploration/   : KAMP 데이터 EDA
- docs/2-architecture/       : 세부 파이프라인, DB 스키마
- docs/adr/                  : Architecture Decision Records
