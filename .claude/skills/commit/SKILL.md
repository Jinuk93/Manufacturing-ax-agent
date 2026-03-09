---
name: commit
description: 변경사항을 확인하고 의미 있는 커밋 메시지로 커밋합니다. /commit [push] 로 push도 가능합니다.
---

## 커밋 절차

1. `git status`와 `git diff`로 변경사항 확인

2. 변경 내용을 분석하여 커밋 메시지 작성:
   - 제목: 영어, 50자 이내, 동사로 시작 (Add/Update/Fix/Remove)
   - 본문: 변경된 파일과 이유를 간결하게 나열
   - Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com> 포함

3. 커밋 메시지를 사용자에게 보여주고 확인 후 커밋

4. 인자에 "push"가 포함되어 있으면 push까지 실행

## 규칙
- .env, credentials 등 민감 파일은 커밋하지 않음
- git add -A 대신 변경된 파일을 명시적으로 staging
- 커밋 전 변경 내용을 반드시 사용자에게 보여줌
