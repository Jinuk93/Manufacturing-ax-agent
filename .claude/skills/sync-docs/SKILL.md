---
name: sync-docs
description: 문서 변경 후 README, PRD, open-items 간의 정합성을 검사하고 동기화합니다.
---

아래 문서들을 읽고, 서로 불일치하는 부분을 찾아 수정하세요:

1. **README.md** 확인 항목:
   - Phases 표의 상태가 실제 진행 상황과 일치하는지
   - ADR 표가 docs/adr/ 폴더의 실제 파일과 일치하는지
   - Open Items 개수가 open-items.md와 일치하는지
   - Docs Structure 트리가 실제 폴더 구조와 일치하는지

2. **docs/0-project-definition/prd-v1.0.md** 확인 항목:
   - §6 ADR 목록이 README의 ADR 표와 일치하는지
   - §5 미결사항이 open-items.md와 일치하는지

3. **docs/0-project-definition/open-items.md** 확인 항목:
   - 상태(Open/Decided/Dropped)가 최신인지
   - Decided된 항목에 ADR 번호가 기재되어 있는지

불일치 발견 시:
- 어떤 문서의 어떤 부분이 다른지 명확히 보고
- 사용자에게 확인 후 수정 (자동 수정하지 말 것)
