---
name: write-adr
description: 새로운 ADR(Architecture Decision Record)을 작성합니다. 사용법 - /write-adr [주제]
---

사용자가 전달한 주제에 대해 ADR을 작성합니다.

## 작성 절차

1. docs/adr/ 폴더의 기존 ADR 파일을 확인하여 다음 번호를 결정

2. docs/adr/000-template.md 의 형식에 맞춰 ADR 작성:
   - Status: Proposed (사용자 확인 후 Decided로 변경)
   - Context: 어떤 상황에서 이 결정이 필요했는가
   - Options Considered: 최소 2개 이상의 대안 제시
   - Decision: 선택한 옵션
   - Reasoning: 선택 근거
   - Consequences: 이 결정으로 인한 제약사항

3. 작성 규칙:
   - AI 도구 이름(클로드, 제미나이, GPT 등) 절대 사용 금지
   - "Option A / Option B" 형식으로 대안을 구조화
   - 파일명: [번호]-[핵심키워드].md (예: 006-llm-selection.md)

4. ADR 작성 후 사용자에게 확인을 받고:
   - README.md ADR 표에 추가
   - prd-v1.0.md §6 ADR 목록에 추가
   - 관련된 open-items.md 항목이 있으면 상태를 Decided로 변경
