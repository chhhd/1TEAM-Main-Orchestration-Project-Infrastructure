# 1TEAM-Main-Orchestration-Project-Infrastructure

팀원1(이동건) — 메인 오케스트레이션 & 프로젝트 인프라 담당 산출물.

## 이 저장소에 있는 것

| 산출물 | 위치 | 내용 |
|---|---|---|
| 프로젝트 규칙 / Agent 라우팅 | `CLAUDE.md` | `/search?q=` → injection-agent 등 라우팅 표, 종료 조건, 중복 방지 규칙 |
| 권한 모드 설계 | `.claude/settings.json` | `python`/`curl(loopback)`/`git status` 등은 자동 승인, `git push`/`git commit`/`rm`/외부 `curl`은 확인 요청, 파괴적 명령은 거부 |
| Local Vulnerable Web App | `vulnapp/app.py` | `/search`(SQLi), `/lookup`(음성 대조군), `/user?id=`(IDOR), `/admin`(무인증), `/upload`(무검증 업로드), `/fetch?url=`(SSRF) — 127.0.0.1:5000 전용 |
| 오케스트레이션 흐름 실측 검증 | `docs/orchestration-flow-verification.md` | recon → 라우팅 → injection-agent/access-control-agent 병렬 호출 → 결과 수렴까지, 실제 subagent 호출 + 실제 HTTP 요청으로 재현한 로그 (시뮬레이션 아님) |

## 다른 저장소와의 관계

이 저장소는 팀 전체 프로젝트의 **인프라 슬라이스만** 담는다. `CLAUDE.md`의
라우팅 표가 가리키는 `.claude/agents/recon-agent.md`, `injection-agent.md`,
`access-control-agent.md` 등 실제 agent 정의 파일은 여기 없고, 통합 저장소
[`SECURITY-1TEAM-Orchestrator-chain`](https://github.com/chhhd/SECURITY-1TEAM-Orchestrator-chain)에
있다. 이 저장소의 경로 구조는 그 통합본과 그대로 맞아떨어지도록 맞춰뒀다
(`.claude/agents/` 아래에 두면 그대로 합쳐짐).

## 실행

```bash
python3 vulnapp/app.py &     # 127.0.0.1:5000
```

`docs/orchestration-flow-verification.md`의 재현 커맨드로 SQLi/IDOR/무인증
취약점을 직접 확인할 수 있다.

## 알아둘 것

- `.claude/settings.json`에는 hooks 설정이 없다 — 로깅/hooks는 팀원5(박정근)
  담당이며 통합 저장소에만 있다. 이 저장소만 단독으로 열면 `SubagentStop`
  자동 기록은 동작하지 않는다.
- `vulnapp/`은 의도적으로 취약하게 만든 연습용 앱이다. `127.0.0.1` 바인딩을
  벗어나거나 실제 배포 환경에 올리지 않는다.
