---
name: connection-pool-fix
description: PostgreSQL 커넥션 풀 고갈 문제 원인과 해결 기록
type: project
---

## 커넥션 풀 고갈 문제

**증상**: 대시보드 사용 중 PostgreSQL 연결이 끊기고 API가 500 에러 반환.
`psycopg2.pool.PoolError: connection pool exhausted`

**원인**:
1. `routes.py` health 체크에서 `conn.close()` 사용 → 풀 커넥션을 파괴(반환이 아닌 삭제)
2. 프론트에서 5초 폴링 × 설비 3대 × API 6종 = 18개 동시 요청 → 풀 고갈
3. `SimpleConnectionPool`은 스레드 안전하지 않음

**해결 (2026-03-17)**:
1. `conn.close()` → `release_connection(conn)` 전체 교체 (routes.py 12곳)
2. `SimpleConnectionPool` → `ThreadedConnectionPool` (스레드 안전)
3. `maxconn: 10 → 50` 확대
4. `get_db()` 컨텍스트 매니저 추가 (향후 안전한 사용 패턴)

**Why:** health 체크가 10초마다 호출되면서 매번 커넥션을 파괴하고, 프론트 폴링이 남은 커넥션을 빠르게 소진시킴
**How to apply:** routes.py에서 conn 사용 후 반드시 `release_connection(conn)` 호출. 신규 코드에서는 `with get_db() as conn:` 패턴 사용 권장
