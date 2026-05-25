# MCP ↔ Slack 브릿지 설계

기존 커넥터(Jira·Confluence·GitHub)의 작업 흐름을 Slack으로 흘려보내는 자동화 설계.
"이벤트 → 가공 → Slack 게시" 의 단방향 알림이 1차 목표이고, 양방향(Slack 명령 → 작업)은 Phase 2.

## 1. 트리거 소스와 알림 매핑

| 소스 | 이벤트 | Slack 알림 내용 |
| --- | --- | --- |
| Jira (SINCE) | 이슈 생성/상태 전환/기한 임박 | `[SINCE-N] 제목` + 상태 + 담당 + 링크 |
| Confluence | 프로젝트 폴더 하위 페이지 신규/갱신 | 페이지 제목 + 분류(설계/조사/코드…) + 링크 |
| GitHub | PR open/merge, CI 결과 | repo + PR 제목 + 상태 + 링크 |
| generate-outputs | 산출물 생성 완료 (Phase 1+) | output 종류 + job id + 발행 링크 |

## 2. 구현 옵션 (택1, 단계적)

### A. Claude 세션 기반 (지금 당장, 추가 인프라 0)
- Slack MCP가 연결된 세션에서 Claude가 직접:
  `Jira MCP로 SINCE-9 하위 오픈이슈 조회 → 요약 → Slack MCP로 #dev-notify 게시`.
- `/loop` 스킬로 주기 실행(예: `/loop 30m`) 하거나, GitHub PR 이벤트 구독(`subscribe_pr_activity`)에 묶어 게시.
- 장점: 코드 없음, LLM이 요약/판단. 단점: 세션 비용·상시 실행은 부적합 → **요약/데일리 리포트**에 적합.

### B. 스크립트 기반 (가벼운 상시 알림)
- `notify.py` + 각 소스 폴링 스크립트(Jira REST / GitHub API / Confluence REST).
- cron 또는 GitHub Actions 스케줄로 실행. 상태는 last-seen 타임스탬프 파일로 dedupe.
- 장점: 저비용·결정적. 단점: 요약 품질은 단순(템플릿).

### C. 하이브리드 (권장 최종형)
- 실시간 단순 알림(PR/CI)은 **B(스크립트/Actions)**.
- 데일리/위클리 요약·하이라이트는 **A(Claude 세션)** 로 생성해 게시.

## 3. 1차 구현 권장 순서
1. `#dev-notify` 채널 + 봇 초대, `SLACK_DEFAULT_CHANNEL` 설정.
2. **GitHub PR/CI → Slack**: 가장 자주 보는 신호. Actions에서 `notify.py` 호출 또는 세션 PR 구독.
3. **Jira 데일리 요약**: 하루 1회 SINCE-9 하위 오픈이슈 상태를 Claude 세션이 요약 게시.
4. Confluence 페이지 변경 알림은 후순위(변경 빈도 낮음).

## 4. Phase 2 — 양방향
- Slack 슬래시 커맨드/멘션 → 작업 트리거 (예: `/since status`, `@bot SINCE-13 진행상황`).
- Slack Bolt 앱 또는 Events API 수신 엔드포인트 필요(상시 서버) → 인프라는 aws_infra와 연계 검토.

## 5. 보안·운영
- 토큰은 환경 시크릿만 (README 1절). 알림 본문에 PII/시크릿 미포함.
- 채널은 최소 권한(필요 채널에만 봇 초대). 실패 시 재시도/조용한 실패 후 로그.
