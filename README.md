# work-record

개인 작업 기록 저장소 — 설계, 기술분석, 이슈, 자동화, AI 자산을 카테고리별로 관리한다.

## 구조

```
work-record/
├── design/          # 아키텍처, UML, user flow, DB 스키마 등 설계 문서
├── tech-analysis/   # 기술 분석 및 조사 기록
├── issues/          # 이슈 분석 / 개발 고민사항 딥다이브
├── automation/      # 자동화 방안 및 스크립트 설계
├── agents/          # AI agent 구성 방안
└── claude/          # Claude / AI 관련 자산
    ├── skills/      # Claude Code 커스텀 스킬
    ├── prompts/     # 재사용 프롬프트
    └── harness/     # 하네스 엔지니어링 정리
```

## 파일 컨벤션

- 각 폴더 안에 topic별 `.md` 파일로 평탄하게 관리
- 파일명: `{topic-kebab-case}.md` (예: `auth-flow.md`, `cache-invalidation.md`)
- 내용이 커질 경우 동명의 폴더로 분리 후 `overview.md` + 하위 파일로 확장
