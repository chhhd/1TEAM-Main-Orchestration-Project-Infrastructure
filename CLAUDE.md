# CJ PROJECT — Security Subagent Harness

5인 팀이 만드는 Claude Code 기반 웹 취약점 진단 하네스. Claude Code 자체가
오케스트레이터(메인 세션) 역할을 하고, 전문 영역별 subagent가 실제 진단을 수행한다.
공용 실행 계약(`AgentFinding`/`Evidence`/`Probe`, `AgentHttpClient`, safety 경계)은
`dast-harness/`(git submodule, pull-only)가 정의하며 **여기 있는 규칙과 상충하면
`dast-harness/AGENT_GUIDE.md`·`dast-harness/CLAUDE.md`가 우선한다.**

> 이 저장소는 팀원1(오케스트레이션/인프라) 담당 산출물만 담는다. 라우팅 표가
> 가리키는 `.claude/agents/recon-agent.md` 등은 다른 팀원의 저장소
> (`SECURITY-1TEAM-Orchestrator-chain` — 통합본)에 있다. 경로는 통합 시
> 그대로 맞아떨어지도록 맞춰뒀다.

## 폴더 맵

```
CLAUDE.md                 이 문서 — 라우팅/종료/중복방지 규칙
.claude/
  settings.json            권한 모드 (allow/ask/deny)
  skills/evidence-logging/  5명 전원 공용 증적 기록 스키마·절차 (모든 agent가 로드)
evidence/                  evidence.csv — 5명 전원 공통 스키마 시도 로그 (append-only)
scripts/                   append_evidence.py, confirmed_summary.py — CSV 안전하게 쓰고 읽는 도구
vulnapp/                   팀원1 소유 로컬 취약 앱 — 오케스트레이션 흐름 검증용
                          (/search, /lookup, /user?id=, /upload, /admin, /fetch?url=)
docs/orchestration-flow-verification.md   recon→routing→후속 subagent 호출 체인 실측 로그
```

## Agent 라우팅 규칙

오케스트레이터(메인 세션)는 대상/작업 성격에 따라 아래 순서로 subagent를 호출한다.
**recon이 항상 먼저다** — 다른 agent는 recon이 만든 엔드포인트 인벤토리
(`RequestSeed`)를 입력으로 받는 게 기본 전제다. recon 없이 특정 엔드포인트 하나만
검사해달라는 요청이면 바로 해당 agent로 가도 된다.

| 신호 | 라우팅 | 정의 |
|---|---|---|
| 새 타겟, "뭐가 있는지 파악해줘", URL만 주어짐 | `recon-agent` | `.claude/agents/recon-agent.md` |
| `?q=`, `?search=` 등 값이 쿼리/바디로 들어가는 파라미터, SQL/커맨드/템플릿 주입 의심 | `injection-agent` | `.claude/agents/injection-agent.md` |
| `/id/<num>`, `?id=` 등 경로·객체 참조, `/admin` 류 role-gated 엔드포인트, 다단계 워크플로 | `access-control-agent` | `.claude/agents/access-control-agent.md` |
| 탐지된 라이브러리/프레임워크 버전에 대한 알려진 CVE 확인 | 담당 agent가 GitHub MCP 도구를 **직접** 호출 (전용 agent 없음) | `.mcp.json` |

같은 엔드포인트가 여러 클래스에 걸릴 수 있다(예: `/search?q=`가 injection이면서
동시에 인가 없이 열려 있을 수 있음) — 이 경우 각 agent에게 **자기 클래스만** 보게
하고, 오케스트레이터가 결과를 합친다. 한 agent가 스코프 밖 취약점을 "겸사겸사"
보고하지 않도록 각 agent 정의에 명시돼 있다.

## 종료 조건

다음 중 하나면 그 타겟에 대한 추가 subagent 호출을 멈춘다.

- recon이 이전 호출과 동일한 `request_seeds`를 반환함 (새로 발견한 표면 없음)
- 라우팅 표의 모든 카테고리에 대해 최소 1회씩 agent를 호출했고, 각 agent가
  `finish()`에서 `skipped=0`으로 보고함 (더 볼 게 없다고 스스로 판단)
- 사용자가 명시적으로 중단 요청
- 동일 대상에 대해 같은 agent를 3회 넘게 재호출하려는 시점 (아래 중복 방지 규칙 참고)

## 중복 방지 규칙

- 같은 (엔드포인트, 파라미터, identity) 조합을 이미 테스트했는지 실행 로그를 먼저
  확인하고 재검사하지 않는다 (로그 자동 기록은 팀원5의 hooks 담당 — 이 저장소에는
  훅 스크립트 자체는 없다).
- recon을 반복 호출할 땐 이전 `request_seeds`와 diff해서 **새로 생긴 것만** 하위
  agent에 넘긴다. 전체 재검사를 기본값으로 하지 않는다.
- 정찰 결과를 전달할 때는 전체 원문이 아니라 §라우팅에 필요한 필드만 요약해서
  넘긴다 (토큰 최소화 — subagent는 독립 컨텍스트이므로 원본은 그 안에만 남는다).

## 범위 제한 (Rules of Engagement)

`1TEAM-MEMORY`(팀 통합 규정 저장소)와 동일한 규정을 이 저장소 레벨에서도 지킨다.

- `target-info.md`에 명시된 호스트/URL/IP 대역 외에는 스캔·요청하지 않는다.
- 공개 인터넷의 무관한 서비스에 대해 대량 스캔, 무차별 대입, DoS성 요청을 절대
  수행하지 않는다.
- 실제 크리덴셜, 개인정보, 플래그 원문은 커밋하지 않는다 — `evidence/evidence.csv`
  등 evidence 파일에는 해시/마스킹/요약만 남긴다.
- 대상 시스템 상태를 변경하는 행위(쓰기, 삭제, 설정 변경)는 대회/훈련 규정상
  명시적으로 허용된 경우에만 수행한다 (§안전 경계의 "파괴적/상태변경 probe" 규칙과
  같은 취지).

## 안전 경계 (오케스트레이션 레벨)

팀 공용 하네스(`dast-harness/dast_harness/safety.py`)가 강제하는 것과 같은
원칙을 오케스트레이터 레벨에서도 지킨다.

- **loopback(`127.0.0.1`/`localhost`) 또는 명시적으로 허가된 대상만** 스캔한다.
  `vulnapp/`은 기본 포트 `5000`.
- 파일 편집은 체크포인트로 되돌릴 수 있지만, **실제 공격 요청 같은 외부 부작용은
  되돌릴 수 없다.** 파괴적이거나 상태를 바꾸는 probe(파일 업로드, 쿠폰 반복 사용
  등)를 보내기 전에는 무엇을 왜 보내는지 먼저 알린다 — 각 agent 정의에도 명시.
- `.claude/settings.json`의 `permissions.allow`에 없는 명령(원격 push, 강제 삭제 등)은
  자동 승인하지 않는다.

## 기록 절차 (evidence.csv) — 5명 전원 동일

라우팅/종료/중복방지와는 별개로, **모든 테스트 시도**(finding으로 이어졌든 아니든)는
공통 스키마로 `evidence/evidence.csv`에 기록한다. 스키마와 절차 전문은
`evidence-logging` skill과 `evidence/README.md`에 있다 — 여기는 오케스트레이터
레벨에서 지켜야 할 것만 요약한다.

- **스키마**: `timestamp,target,endpoint,agent,operator,caller,hypothesis,payload,observation,new_info,status,evidence_ref` — 5개 agent(Recon/Injection/IDOR/Auth/CVE) 전원이 같은 파일, 같은 컬럼을 쓴다.
- **오케스트레이터가 subagent를 호출할 때**, 반드시 `operator`(실행한 사람 이름)와 `caller=orchestrator`를 프롬프트에 명시해서 넘긴다 — subagent는 이 두 값을 추측하지 않는다.
- **CSV는 손으로 편집하지 않는다.** `scripts/append_evidence.py`로만 행을 추가한다 (payload에 쉼표/따옴표가 섞이면 손 편집은 깨진다).
- **status 승격은 append-only.** `unconfirmed` 행을 고쳐서 `confirmed`로 바꾸지 않고, 재현 확인 후 새 행을 추가한다.
- **오케스트레이터 호출 시점에 팀원1이 `python scripts/confirmed_summary.py`로 confirmed 행만 모아서 전달한다** — unconfirmed/dead-end 행은 원본 CSV에는 남지만 오케스트레이터 컨텍스트에는 안 들어간다 (토큰 최소화 원칙, 위 §중복 방지 규칙과 같은 이유).
- **상태판(Notion) 연동은 아직 없다.** 이 저장소에는 실제 Notion 페이지/DB 연결이 설정돼 있지 않다 — `evidence/README.md`의 "상태판" 절 참고. 연동 전까지는 `evidence/evidence.csv`의 `status` 컬럼과 git 커밋 로그가 사실상의 상태판이다.
- **커밋 컨벤션**: `git commit -m "<이름>: <endpoint> <agent> 시도 N건"` — 사람 오퍼레이터가 직접 커밋한다(agent가 대신 커밋하지 않는다).

## 산출물 우선순위

이 문서는 "이론적 설계"가 아니라 실제 동작하는 `.claude/settings.json`,
`vulnapp/`, 그리고 흐름이 실제로 이어진다는 것을 보여주는 검증 로그
(`docs/orchestration-flow-verification.md`)와, 모든 시도를 빠짐없이 남기는
증적 기록(`evidence/evidence.csv` + `scripts/`)을 남기는 것을 목표로 한다.
