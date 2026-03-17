# Phase 3 후반 작업 보고서

**작업일:** 2026-03-17
**범위:** Phase 3 리뷰에서 남은 Medium/Low 과제 6건 + 보고서

---

## 작업 요약

| # | 항목 | 이전 상태 | 이후 상태 |
|---|------|-----------|-----------|
| 1 | F6 action DB 저장 | TODO 스텁 | llm_action_reports 테이블 + INSERT 구현 |
| 2 | config 이관 | 매직넘버 14개 하드코딩 | 전부 Settings에 파라미터화 |
| 3 | F2 모델 개선 | 10개 피처 | 14개 피처 + 파생 2개 (총 16개) |
| 4 | R2 DETECTS + R10 REFERENCES | 0건 | R2: 7건 + R10: 90건 |
| 5 | 커넥션 풀 | 매 요청 새 연결 | SimpleConnectionPool (min=2, max=10) |
| 6 | F5 판단 투명성 | reasoning만 | + input_summary, rag_documents, alternatives_considered, full_reasoning |

---

## 상세 내용

### 1. F6 action DB 저장

**문제:** F5 LLM이 판단을 내려도 DB에 저장하지 않아서 `/api/f6/action/{eq_id}`에서 이전 결과를 조회할 수 없었음.

**해결:**
- `llm_action_reports` 테이블 신규 생성 (init.sql + 실행)
- `/api/f6/action` 엔드포인트에서 F5 결과를 자동 INSERT
- action_steps, parts_needed는 JSON 문자열로 저장

**스키마:**
```sql
CREATE TABLE llm_action_reports (
  id SERIAL PRIMARY KEY,
  equipment_id VARCHAR(7),
  timestamp TIMESTAMPTZ,
  recommendation VARCHAR(10),
  confidence FLOAT8,
  reasoning TEXT,
  action_steps TEXT,        -- JSON
  parts_needed TEXT,        -- JSON
  predicted_failure_code VARCHAR(30),
  estimated_downtime_min INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. Config 이관

**문제:** IF contamination(0.1), 고장분류 임계치(1.3, 0.7, 15, 0.5), LLM retry(2), timeout(30), CORS origin 등이 코드에 하드코딩.

**해결:** `config.py`에 14개 신규 파라미터 추가:

| 파라미터 | 기본값 | 용도 |
|----------|--------|------|
| IF_CONTAMINATION | 0.1 | Isolation Forest 이상 비율 |
| IF_N_ESTIMATORS | 200 | IF 트리 수 |
| SPINDLE_CURRENT_RATIO | 1.3 | 고장분류: S1 전류 비율 |
| SPINDLE_FEEDRATE_MIN | 15.0 | 고장분류: 고속 기준 |
| TOOL_WEAR_RATIO | 0.7 | 고장분류: X1 전류 비율 |
| CLAMP_POSITION_THRESHOLD | 0.5 | 고장분류: 위치 편차 (mm) |
| EMBED_MODEL | paraphrase-multilingual-MiniLM-L12-v2 | 임베딩 모델 |
| LLM_MAX_RETRIES | 2 | LLM 재시도 횟수 |
| LLM_TIMEOUT | 30 | LLM 타임아웃 (초) |
| CORS_ORIGINS | localhost:5173,5174 | CORS 허용 origin |

### 3. F2 모델 개선

**문제:** 10개 피처로는 분리도가 0.051로 낮음. 특히 저속 마모(exp13, 14, 18) 감지 부족.

**해결:** 피처셋 확장:
- 기존 10개 유지
- 확장 4개 추가: X1_ActualPosition, X1_CommandPosition, Y1_OutputPower, S1_OutputCurrent
- 파생 2개 추가:
  - `x_position_deviation` = |ActualPosition - CommandPosition| → 클램프 이상 지표
  - `x_power_ratio` = X1_OutputPower / S1_OutputPower → 부하 비율

**기대 효과:** 위치 편차가 직접 피처로 들어가면서 CLAMP_PRESSURE_001 감지 정확도 향상. 전력 비율로 부하 불균형 패턴 포착.

### 4. R2 DETECTS + R10 REFERENCES

**문제:** ontology-design.md에 정의된 10종 관계 중 R2, R10이 0건이었음.

**해결:**
- **R2 DETECTS** (Sensor → FailureCode): 7건
  - 도메인 지식 기반 초기 매핑 (전류→마모, S축→과열, 위치→클램프, 전력→냉각)
  - anomaly_pattern, lead_time_min 속성 포함

- **R10 REFERENCES** (MaintenanceAction → Document): 90건
  - R8 RESOLVES와 R5 DESCRIBED_BY를 결합하여 자동 생성
  - "이 정비에서 참조했을 매뉴얼" 연결

**온톨로지 최종 현황:**
- 7종 노드: 120개
- **10종 관계: 337개** (이전 240개 → +97)

### 5. 커넥션 풀

**문제:** 매 요청마다 `psycopg2.connect()` → TCP 연결 생성/해제 반복. 메인 루프에서 루프당 3회 연결.

**해결:**
- `psycopg2.pool.SimpleConnectionPool(minconn=2, maxconn=10)` 도입
- `get_connection()` → 풀에서 가져옴
- `release_connection(conn)` → 풀에 반환 (기존 코드의 conn.close()도 호환)

### 6. F5 판단 투명성

**문제:** LLM 판단 결과에 reasoning 1줄만 있어서 "왜 이렇게 판단했는지" 근거가 부족.

**해결:** `LLMActionResponse`에 4개 필드 추가:

| 필드 | 내용 |
|------|------|
| `input_summary` | F3에서 받은 컨텍스트 요약 (작업, 우선순위, 재고 수, 정비이력 수) |
| `rag_documents` | F4에서 참조한 매뉴얼 제목 목록 |
| `alternatives_considered` | "REDUCE도 고려했지만 score가 높아 STOP 유지" 등 대안 설명 |
| `full_reasoning` | 전체 판단 근거 텍스트 |

---

## 검증 결과

| 항목 | 기대 | 결과 |
|------|------|------|
| llm_action_reports 테이블 | 생성됨 | ✅ |
| config 파라미터 | 14개 추가 | ✅ |
| F2 피처 | 10→16개 | ✅ |
| R2 DETECTS | >0건 | 7건 ✅ |
| R10 REFERENCES | >0건 | 90건 ✅ |
| 커넥션 풀 | SimpleConnectionPool | ✅ |
| F5 투명성 필드 | 4개 | ✅ |
| 온톨로지 관계 총 | 10종 전부 | 337건 ✅ |

---

## 남은 과제 (Phase 4 또는 향후)

| 항목 | 설명 |
|------|------|
| F2 모델 재학습 | 16개 피처로 train_f2.py 재실행 → 분리도 개선 확인 |
| Autoencoder 비교 | IF vs AE 성능 비교 실험 |
| R2 DETECTS 데이터 검증 | F2 모델 결과로 센서→고장코드 매핑 업데이트 |
| CLAMP 임계치 검증 | 0.5mm가 exp04/05에서 유효한지 실데이터 확인 |
| 챗봇 /api/chat 고도화 | 대화 히스토리, 컨텍스트 유지 |
