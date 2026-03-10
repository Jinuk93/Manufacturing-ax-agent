# Phase 1: Data Exploration

Kaggle CNC Mill을 주력으로, Bosch CNC를 보조로 탐색(EDA)하여 "우리가 실제로 무엇을 갖고 있는가"를 파악하는 단계입니다.

## 이 단계의 핵심 질문

- 현재 확보 데이터에서 실제 유효 센서는 무엇인가?
- `sequence`를 어떤 규칙으로 `timestamp`로 바꿀 것인가?
- `experiment`를 어떤 기준으로 `equipment_id`에 매핑할 것인가?
- 어떤 컬럼을 Canonical Model의 최소 입력으로 삼을 것인가?

## 이 폴더에 들어갈 문서

- Kaggle CNC Mill EDA 결과
- Bosch CNC 보조 데이터 검토 메모
- 센서 컬럼 정의 및 분포 분석
- 결측치/이상치 현황
- `timestamp`/`equipment_id` 합성 규칙
- 합성 데이터(MES/ERP) 설계 기준
