# Slack 연동 (MCP + 코드 + 브릿지)

Slack을 세 가지 경로로 연동하기 위한 설정·코드·설계 모음.

| 트랙 | 목적 | 산출물 |
| --- | --- | --- |
| ① MCP 서버 | Claude 세션이 Slack을 직접 읽고/쓰게 함 | `mcp.example.json` (+ 각 레포 루트 `.mcp.json`) |
| ② 코드 연동 | 스크립트/앱에서 Slack으로 메시지 전송 | `notify.py` |
| ③ MCP 브릿지 | Jira·Confluence·GitHub 이벤트 → Slack 알림 | `bridge-design.md` |

---

## 0. 선행: Slack App & 봇 토큰

> 이미 Bot 토큰(`xoxb-...`)을 보유한 상태 기준. 새로 만들 경우 아래 절차.

1. <https://api.slack.com/apps> → **Create New App** → *From scratch* → 워크스페이스 선택.
2. **OAuth & Permissions → Bot Token Scopes** 에 필요한 스코프 추가:
   - `chat:write` — 메시지 전송 (필수)
   - `chat:write.public` — 봇이 초대되지 않은 공개 채널에도 전송
   - `channels:read`, `groups:read` — 채널 목록 조회
   - `channels:history`, `groups:history` — 메시지 읽기 (MCP 읽기용)
   - `users:read` — 사용자 조회
   - `reactions:write` — 이모지 반응 (선택)
3. **Install to Workspace** → 발급된 **Bot User OAuth Token** (`xoxb-...` ) 확보.
4. **Team ID** 확인: 브라우저에서 Slack 접속 시 URL `app.slack.com/client/T01234ABCDE/...` 의 `T`로 시작하는 값.
5. 봇을 메시지 보낼 채널에 초대: 채널에서 `/invite @your-bot`.

### Bot 토큰의 제약 (알아둘 것)
- `xoxb-` 토큰은 **초대된 채널**에서만 동작하고, 워크스페이스 전역 **검색 불가**, DM 제한이 있다.
- 전역 검색/DM까지 필요하면 별도 사용자 토큰(`xoxc`/`xoxd`)이 필요하지만 만료가 잦아 권장하지 않는다. 알림·게시 용도엔 봇 토큰으로 충분.

---

## 1. 토큰 보관 (절대 커밋 금지)

토큰·Team ID는 **환경 변수/시크릿**으로만 주입한다. 어떤 파일에도 평문으로 커밋하지 않는다.

- **Claude Code on the web**: 환경(Environment) 설정의 **Secrets/Env**에 `SLACK_BOT_TOKEN`, `SLACK_TEAM_ID` 등록.
- **로컬**: 셸 프로파일이나 `.env`(gitignore됨)에 export.

```bash
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_TEAM_ID="T01234ABCDE"
export SLACK_DEFAULT_CHANNEL="#dev-notify"   # notify.py 기본 채널 (선택)
```

---

## 2. 트랙 ① — MCP 서버 연결

표준 레퍼런스 서버 `@modelcontextprotocol/server-slack`(stdio)를 사용한다.
설정 템플릿: [`mcp.example.json`](./mcp.example.json). 토큰은 `${VAR}`로 참조만 하고 값은 환경 시크릿에서 온다.

### Claude Code on the web
MCP 서버는 **환경 설정 레벨**에서 로드된다. 두 가지 방법:
- **권장**: 세션이 사용하는 레포 **루트에 `.mcp.json`** 을 커밋 → 자동 로드. (별도 레포인 `generate-outputs` 루트에 추가 완료 — 본 레포에는 템플릿 `mcp.example.json`만 둠)
- 또는 환경 설정 UI에서 MCP 서버를 직접 등록.

변경 후 **새 세션**부터 `slack` MCP 툴이 활성화된다 (현재 진행 중 세션엔 즉시 반영되지 않음).
참고: <https://code.claude.com/docs/en/claude-code-on-the-web>

### 로컬 CLI
```bash
claude mcp add slack \
  -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  -e SLACK_TEAM_ID=$SLACK_TEAM_ID \
  -- npx -y @modelcontextprotocol/server-slack
```

---

## 3. 트랙 ② — 코드에서 전송

의존성 없는 stdlib 스크립트: [`notify.py`](./notify.py).

```bash
# 기본
python notify.py --channel "#dev-notify" --text "배포 완료 :rocket:"

# 환경변수 기본 채널 사용 (SLACK_DEFAULT_CHANNEL)
python notify.py --text "테스트 알림"

# Block Kit JSON 전송
python notify.py --channel "#dev-notify" --blocks-file payload.json
```

`generate-outputs`(Kotlin/Spring) 스캐폴딩 시에는 산출물 발행 알림 채널로 이 패턴을 포팅한다
(`SINCE-21 발행 플랫폼` 이슈와 연계).

---

## 4. 트랙 ③ — MCP 브릿지 자동화

Jira/Confluence/GitHub 이벤트를 Slack으로 흘리는 설계는 [`bridge-design.md`](./bridge-design.md) 참고.
