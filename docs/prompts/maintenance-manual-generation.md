# CNC 정비 매뉴얼 합성 데이터 생성 프롬프트

## 1. 프로젝트 배경

CNC 제조 설비의 **예지보전 + 온톨로지 기반 GraphRAG + LLM 자율 조치** 에이전트 관제 시스템을 만들고 있습니다.
실제 PDF 매뉴얼이 없어서, LLM이 참조할 수 있는 **실제 정비 매뉴얼처럼 보이는 합성 문서**가 필요합니다.

이 문서들은:
- Neo4j 온톨로지에 노드로 등록됨 (`Document` 노드)
- PostgreSQL에 섹션별로 청킹 + 임베딩 저장됨 (384차원 벡터)
- GraphRAG 검색으로 LLM에게 컨텍스트로 전달됨
- 대시보드에서 "온톨로지 참조 문서"로 표시됨

---

## 2. 현재 보유 데이터 구조

### 설비 (3대)
| ID | 유형 | 비고 |
|---|---|---|
| CNC-001 | CNC 밀링 | KAMP 데이터셋 기반 |
| CNC-002 | CNC 밀링 | 동일 |
| CNC-003 | CNC 밀링 | 동일 |

### 고장코드 (4종)
| 코드 | 설명 | 심각도 | 분류 기준 |
|---|---|---|---|
| TOOL_WEAR_001 | 엔드밀 마모 → 가공 품질 저하 | critical | X1 전류가 median의 70% 이하 |
| SPINDLE_OVERHEAT_001 | 주축 과열 → 베어링 손상 위험 | critical | S1 전류가 median의 130% 이상 + feedrate 15 이상 |
| CLAMP_PRESSURE_001 | 클램프 압력 저하 → 공작물 고정 불량 | warning | X1 위치 편차(ActualPosition - CommandPosition) > 0.5mm |
| COOLANT_LOW_001 | 절삭유 부족 → 가공면 품질 저하 | warning | 위 3개에 해당 안 되는 이상 |

### 부품 (5종)
| ID | 품명 | 단가 | 리드타임 | 안전재고 |
|---|---|---|---|---|
| P001 | Endmill 6mm Carbide | 45,000원 | 3일 | 5개 |
| P002 | Spindle Bearing Set | 280,000원 | 7일 | 2개 |
| P003 | Coolant (수용성, 20L) | 35,000원 | 2일 | 3개 |
| P004 | Clamp Bolt Set | 12,000원 | 1일 | 4개 |
| P005 | Air Filter | 8,000원 | 1일 | 3개 |

### 센서 데이터 (F2 이상탐지 16개 피처)

**기본 피처 (14개)**
| 센서 | 의미 | 단위 | 관련 고장코드 |
|---|---|---|---|
| X1_CurrentFeedback | X축 서보모터 전류 피드백 | A | TOOL_WEAR_001 |
| S1_CurrentFeedback | 스핀들 전류 피드백 | A | SPINDLE_OVERHEAT_001 |
| Y1_CurrentFeedback | Y축 서보모터 전류 피드백 | A | - |
| X1_OutputPower | X축 출력 파워 | % | TOOL_WEAR_001 |
| S1_OutputPower | 스핀들 출력 파워 | % | SPINDLE_OVERHEAT_001 |
| X1_ActualVelocity | X축 실제 속도 | mm/s | - |
| Y1_ActualVelocity | Y축 실제 속도 | mm/s | - |
| S1_ActualVelocity | 스핀들 실제 속도 | RPM | SPINDLE_OVERHEAT_001 |
| X1_ActualPosition | X축 실제 위치 | mm | CLAMP_PRESSURE_001 |
| X1_CommandPosition | X축 명령 위치 | mm | CLAMP_PRESSURE_001 |
| Y1_ActualPosition | Y축 실제 위치 | mm | - |
| Y1_CommandPosition | Y축 명령 위치 | mm | - |
| M1_CURRENT_FEEDRATE | 현재 이송 속도 | mm/s | SPINDLE_OVERHEAT_001 |
| Machining_Process | 가공 단계 (Layer 1~9) | enum | - |

**파생 피처 (2개)**
| 피처 | 계산식 | 관련 고장코드 |
|---|---|---|
| x_position_deviation | abs(X1_ActualPosition - X1_CommandPosition) | CLAMP_PRESSURE_001 |
| power_ratio | S1_OutputPower / (X1_OutputPower + 0.001) | SPINDLE_OVERHEAT_001 |

### 온톨로지 관계
```
설비(Equipment) --[HAS_SENSOR]--> 센서(Sensor)
센서(Sensor) --[DETECTS]--> 고장코드(FailureCode)
설비(Equipment) --[EXPERIENCES]--> 고장코드(FailureCode)
고장코드(FailureCode) --[REQUIRES]--> 부품(Part)
고장코드(FailureCode) --[DESCRIBED_BY]--> 문서(Document)  ← 이 문서를 만들어야 함
정비이력(MaintenanceAction) --[RESOLVES]--> 고장코드(FailureCode)
정비이력(MaintenanceAction) --[REFERENCES]--> 문서(Document)
```

---

## 3. 생성해야 할 문서 목록

고장코드 4종 × 문서유형 3종 = **총 12개 문서**

| ID | 제목 | 유형 | 관련 고장코드 | 관련 부품 |
|---|---|---|---|---|
| DOC-001 | 엔드밀 공구 교체 절차서 | 교체 절차서 | TOOL_WEAR_001 | P001 |
| DOC-002 | 공구 마모 점검 체크리스트 | 점검 체크리스트 | TOOL_WEAR_001 | P001 |
| DOC-003 | 공구 마모 트러블슈팅 가이드 | 트러블슈팅 가이드 | TOOL_WEAR_001 | P001, P005 |
| DOC-004 | 스핀들 베어링 교체 절차서 | 교체 절차서 | SPINDLE_OVERHEAT_001 | P002 |
| DOC-005 | 스핀들 과열 점검 체크리스트 | 점검 체크리스트 | SPINDLE_OVERHEAT_001 | P002 |
| DOC-006 | 스핀들 과열 트러블슈팅 가이드 | 트러블슈팅 가이드 | SPINDLE_OVERHEAT_001 | P002, P003 |
| DOC-007 | 클램프 볼트 교체 절차서 | 교체 절차서 | CLAMP_PRESSURE_001 | P004 |
| DOC-008 | 클램프 압력 이상 점검 체크리스트 | 점검 체크리스트 | CLAMP_PRESSURE_001 | P004 |
| DOC-009 | 클램프 압력 이상 트러블슈팅 가이드 | 트러블슈팅 가이드 | CLAMP_PRESSURE_001 | P004 |
| DOC-010 | 냉각수 보충 및 필터 교체 절차서 | 교체 절차서 | COOLANT_LOW_001 | P003, P005 |
| DOC-011 | 냉각수 이상 점검 체크리스트 | 점검 체크리스트 | COOLANT_LOW_001 | P003 |
| DOC-012 | 냉각수 이상 트러블슈팅 가이드 | 트러블슈팅 가이드 | COOLANT_LOW_001 | P003, P005 |

---

## 4. 각 문서 유형별 작성 가이드

### 4-1. 교체 절차서 (Replacement Procedure)
실제 제조 현장의 SOP(Standard Operating Procedure) 느낌으로 작성.

**필수 포함 섹션:**
1. **문서 정보** — 문서번호, 개정이력, 작성일, 승인자 (합성)
2. **개요** — 본 절차서의 목적, 적용 범위, 관련 고장코드
3. **사전 준비** — 필요 부품(부품번호 P00x 명시), 공구, 예상 소요시간, 안전장비
4. **교체 절차** — Step 1~7 수준의 상세 단계. 각 단계에 구체적 수치 포함 (토크값, RPM, 온도, 대기시간 등)
5. **교체 후 검증** — 시운전 조건, 센서값 정상 범위, 품질 확인 방법
6. **주의사항** — 안전 경고, 흔한 실수, 재사용 불가 부품
7. **관련 문서** — 다른 DOC-xxx 참조 (예: "상세 점검은 DOC-002를 참조")

### 4-2. 점검 체크리스트 (Inspection Checklist)
현장 작업자가 태블릿으로 체크하는 느낌.

**필수 포함 섹션:**
1. **적용 범위** — 언제 이 체크리스트를 사용하는지
2. **센서 데이터 확인** — 5~6개 항목, 각 항목에 구체적 센서명(X1_CurrentFeedback 등)과 판정 기준값
3. **물리적 확인** — 3~4개 항목, 육안/청각/촉각 검사 항목
4. **판정 기준** — "센서 N개 이상 해당 시 → 즉시 교체" 같은 의사결정 트리
5. **조치 연계** — 판정 결과별 다음 행동 (어떤 DOC 참조할지)

### 4-3. 트러블슈팅 가이드 (Troubleshooting Guide)
엔지니어가 원인 분석할 때 참조하는 기술 문서 느낌.

**필수 포함 섹션:**
1. **증상-원인 매핑** — 증상 A/B/C 각각에 원인, 센서 패턴, 심각도 기술
2. **조치 방법** — 증상별 단계적 대응 (경미 → 중간 → 심각)
3. **재발 방지** — 예방 정비 주기, 센서 모니터링 기준값
4. **과거 사례** — "2026년 1월 CNC-002에서 유사 증상 발생, P002 교체로 해결" 같은 합성 사례
5. **관련 고장코드 연관** — 이 고장이 다른 고장을 유발할 수 있는 경우 (예: 냉각수 부족 → 스핀들 과열)

---

## 5. 작성 시 반드시 지킬 규칙

### 데이터 일관성
- 부품번호는 반드시 **P001~P005** 사용 (위 표 참조)
- 고장코드는 반드시 **4개만** 사용 (TOOL_WEAR_001, SPINDLE_OVERHEAT_001, CLAMP_PRESSURE_001, COOLANT_LOW_001)
- 문서번호는 반드시 **DOC-001~DOC-012** 사용
- 설비번호는 **CNC-001, CNC-002, CNC-003** 사용
- 센서명은 위 16개 피처 이름을 정확히 사용 (X1_CurrentFeedback, x_position_deviation 등)

### 수치의 현실감
- 토크값, RPM, 온도, 전류값 등은 실제 CNC 밀링 머신 기준으로 현실적인 수치 사용
- 예) 스핀들 RPM: 500~12,000, 엔드밀 토크: 20~30Nm, 냉각수 온도: 15~25°C
- 교체 소요시간: 15분~2시간 (부품 난이도에 따라)
- 점검 주기: 일/주/월 단위

### 문서 간 교차 참조
- 각 문서에서 관련된 다른 DOC 번호를 반드시 언급
- 예: DOC-001(교체 절차) → "상세 점검은 DOC-002를 참조하십시오"
- 예: DOC-003(트러블슈팅) → "교체가 필요한 경우 DOC-001을 따르십시오"

### 톤앤매너
- **공식 기술 문서** 톤: "~합니다", "~하십시오" 체
- 현장 작업자 + 정비 엔지니어가 읽는 문서
- 불필요한 수식어 없이 간결하고 정확하게
- 안전 관련 내용은 반드시 강조

---

## 6. 출력 형식

JSON 형식으로 작성해 주세요. 아래 구조를 따릅니다:

```json
{
  "schema": {
    "version": "2.0",
    "created": "2026-03-17",
    "description": "CNC 정비 매뉴얼 합성 데이터 v2. 고장코드 4종 × 문서유형 3종 = 12건. 실제 현장 매뉴얼 수준의 상세도.",
    "document_types": ["교체 절차서", "점검 체크리스트", "트러블슈팅 가이드"],
    "chunk_strategy": "섹션 단위 (heading 기준). 임베딩 모델: paraphrase-multilingual-MiniLM-L12-v2 (384차원). 섹션별 청킹 후 pgvector HNSW cosine 인덱스 저장."
  },
  "documents": [
    {
      "manual_id": "DOC-001",
      "title": "엔드밀 공구 교체 절차서",
      "document_type": "교체 절차서",
      "failure_code": "TOOL_WEAR_001",
      "related_parts": ["P001"],          // 참조용 메타데이터 (임베딩에는 미사용, Neo4j R4 REQUIRES와 대응)
      "revision": "Rev.3",
      "effective_date": "2026-01-15",
      "approved_by": "정비팀장 김OO",
      "sections": [
        {
          "heading": "1. 문서 정보",
          "content": "문서번호: DOC-001 ..."
        },
        {
          "heading": "2. 개요",
          "content": "본 절차서는 ..."
        }
        // ... 각 섹션
      ]
    }
    // ... DOC-002 ~ DOC-012
  ]
}
```

### 섹션 content 작성 기준
- 각 섹션의 content는 **최소 200자, 최대 500자** 수준 (200자 미만은 임베딩 검색 품질이 떨어짐)
- 한 문서당 **5~7개 섹션**
- 구체적 수치, 부품번호, 센서명을 반드시 포함
- 과거 사례(합성)를 트러블슈팅 가이드에 포함

---

## 7. 현재 버전(v1)의 개선 포인트

현재 `maintenance_manuals.json`에 v1이 있는데, 다음을 보강해 주세요:

1. **문서 정보 섹션 추가** — 개정번호, 시행일, 승인자 (실제 문서 느낌)
2. **과거 사례 추가** — 트러블슈팅 가이드에 합성 사례 2~3건씩
3. **교차 참조 강화** — 문서 간 "DOC-xxx를 참조하십시오" 연결
4. **수치 보강** — 센서 임계값, 토크값, RPM, 온도 등 더 구체적으로
5. **안전 경고 강화** — 위험 표시 (⚠️), 금지사항 명시
6. **예방 정비 주기** — 각 고장코드별 권장 점검/교체 주기 명시
7. **고장 간 연관 관계** — 냉각수 부족 → 스핀들 과열 유발 같은 cascade 관계 설명

---

## 8. 참고 자료

이 프로젝트의 센서 데이터는 **KAMP(한국 AI 제조 플랫폼) CNC 밀링 데이터셋**을 기반으로 합니다.

- 실험 조건: unworn/worn 공구, 다양한 feedrate(5~25mm/s)
- 주요 발견: worn 상태에서 X1_CurrentFeedback이 unworn 대비 평균 47% 감소
- 센서 샘플링: 100ms 주기 → 5초 윈도우로 집계

이 정보를 매뉴얼 내용에 자연스럽게 녹여주세요 (EDA 분석 결과 참조, 센서 임계치 기준 등).
