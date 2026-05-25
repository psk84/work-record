# work-record — 작업 정책

개인 작업 기록 저장소(설계·기술분석·이슈·자동화·AI 자산). 본 문서는 이 레포의 작업 정책이다.

## 1. 커밋 컨벤션

- 형식: `[{JIRA-KEY}] {type}: {message}` (Jira 키 + Conventional Commits).
- type: `feat`, `bug`, `fix`, `docs`, `chore`, `refactor`.
- Jira 프로젝트: **SINCE** (`https://since0523.atlassian.net`), 작업은 Epic **SINCE-9** 하위 이슈와 연결.
- 커밋/수정/푸시 시 `jira-commit` 스킬을 사용한다. 커밋·푸시는 사용자가 요청할 때만.

## 2. 디렉터리 (README 참고)

`design/ · tech-analysis/ · issues/ · automation/ · agents/ · claude/(skills·prompts·harness)`

## 3. 코드리뷰 & PR 워크플로 (상시 — 모든 코드 작업에 적용)

역할 분리: **개발자 = 메인 Claude**, **리뷰어 = `code-reviewer` 서브에이전트**(`.claude/agents/code-reviewer.md`).

1. **작성 중 협의**: 의미 있는 변경마다 커밋 **전에** `code-reviewer`를 호출한다.
   `REQUEST CHANGES`면 수정 후 재검토를 반복해 **Blocker·High가 0**이 될 때까지 수렴시킨 뒤 커밋한다.
2. **PR 게시**: 푸시하면 기존 PR이 갱신된다. 리뷰어의 최종 리뷰 결과를 **PR 리뷰 코멘트로 게시**한다.
3. **코멘트 대응**: PR 리뷰 코멘트 수신 시 개발자가 조사 → 수정 또는 반박 근거 제시 → **스레드 답변/resolve** → 푸시 → 리뷰어 재검토. 이견은 라운드로 협의해 수렴.
4. **머지**: 리뷰어 `APPROVE` + 미해결 코멘트 0건이면 **확인 없이 자동 머지**(방식: **merge commit**).
5. **자동 머지 예외(안전장치)**: 시크릿/PII 노출, 파괴적 변경, CI 실패 시 자동 머지하지 않고 사용자 확인.
